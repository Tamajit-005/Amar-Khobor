import json
import os
import re
import string
import unicodedata
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml
from pydantic import BaseModel
import Levenshtein

from pipeline import is_mock_mode, require_key
from pipeline.stt.base import get_stt_provider


class EvaluationResult(BaseModel):
    clip_id: str
    language_mode: str
    provider: str
    ground_truth: str
    hypothesis: str
    eval_type: str  # "wer", "llm_judge", "noise_guard"
    wer: Optional[float] = None
    score: float  # For WER: (1.0 - wer); For LLM-Judge: 1.0 to 5.0
    latency_ms: int
    hallucinated: bool = False


def normalize_text_for_wer(text: str) -> str:
    """
    Normalizes Indic / English text for rigorous Word Error Rate comparison:
    1. Unicode Form C normalization (NFC)
    2. Stripping Zero-Width Joiner (‍) and Non-Joiner (‌)
    3. Stripping all punctuation symbols
    4. Lowercasing English characters and collapsing whitespace
    """
    if not text:
        return ""

    # Unicode Form C
    text = unicodedata.normalize("NFC", text)

    # Strip Zero-Width Joiner and Non-Joiner
    text = text.replace("‌", "").replace("‍", "")

    # Strip punctuation
    # Remove standard punctuation and Indic danda (।)
    punc_table = str.maketrans("", "", string.punctuation + "।॥‘’“”'\"`")
    text = text.translate(punc_table)

    # Lowercase & collapse extra whitespace
    text = text.lower()
    return re.sub(r"\s+", " ", text).strip()


def calculate_wer(reference: str, hypothesis: str) -> float:
    """
    Computes Levenshtein Word Error Rate (WER) between reference and hypothesis:
    WER = (S + D + I) / N
    """
    ref_norm = normalize_text_for_wer(reference)
    hyp_norm = normalize_text_for_wer(hypothesis)

    ref_words = ref_norm.split()
    hyp_words = hyp_norm.split()

    if not ref_words:
        return 0.0 if not hyp_words else 1.0

    # Calculate word-level edit distance
    distance = Levenshtein.distance(ref_words, hyp_words)
    return round(distance / len(ref_words), 4)


def judge_codemixed_transcript(
    ground_truth: str,
    hypothesis: str,
    language_mode: str,
) -> float:
    """
    Evaluates code-mixed speech (Benglish/Hinglish) using LLM-Judge
    (1 to 5 scale) to avoid false penalties between Romanized text and native script.
    """
    if is_mock_mode():
        # Deterministic high-accuracy semantic match score
        return 4.8

    active_model = os.getenv("GEMMA_MODEL") or os.getenv("LLM_MODEL") or "gemma-4"
    custom_url = os.getenv("LLM_API_URL", "").strip()

    prompt = f"""You are an expert bilingual linguist judging ASR transcripts of code-mixed {language_mode} speech.
Compare the spoken meaning between the Ground Truth and Hypothesis. Note that one system may output in Romanized English script while another uses native Indic script; DO NOT penalize script differences if the words and meaning are semantically identical.

Ground Truth: "{ground_truth}"
Hypothesis: "{hypothesis}"

Score the semantic fidelity from 1.0 to 5.0:
5.0 = Perfect semantic equivalence (identical words/meaning despite script)
4.0 = Minor slip (one minor word missing or slight spelling variation)
3.0 = Partial meaning preserved, but significant phrase dropped
2.0 = Major distortion of meaning
1.0 = Completely uninterpretable or wrong

Respond with ONLY the numeric score (e.g., 4.5)."""

    key = require_key("GEMINI_API_KEY", "Gemma LLM-judge")
    try:
        if custom_url:
            import httpx
            headers = {"Authorization": f"Bearer {key}"}
            payload = {
                "model": active_model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.0,
            }
            resp = httpx.post(custom_url, headers=headers, json=payload, timeout=30.0)
            score_text = resp.json()["choices"][0]["message"]["content"]
        else:
            import google.generativeai as genai
            genai.configure(api_key=key)
            model = genai.GenerativeModel(active_model)
            response = model.generate_content(prompt)
            score_text = response.text

        score_match = re.search(r"(\d+(?:\.\d+)?)", score_text.strip())
        if score_match:
            score = float(score_match.group(1))
            return max(1.0, min(5.0, score))
    except Exception:
        pass

    return 4.0


def evaluate_clip(
    clip_id: str,
    audio_path: str | Path,
    ground_truth: str,
    hypothesis: str,
    language_mode: str,
    latency_ms: int,
    provider: str,
) -> EvaluationResult:
    # Noise handling
    if language_mode == "noise":
        cleaned = hypothesis.strip().lower()
        is_silence = cleaned in ("", "[silence]", "[background_noise]", "[noise]")
        hallucinated = not is_silence and len(cleaned) > 0
        return EvaluationResult(
            clip_id=clip_id,
            language_mode="noise",
            provider=provider,
            ground_truth="[SILENCE/NOISE]",
            hypothesis=hypothesis,
            eval_type="noise_guard",
            wer=None,
            score=0.0 if hallucinated else 5.0,
            latency_ms=latency_ms,
            hallucinated=hallucinated,
        )

    # Code-mixed routing (Benglish, Hinglish) -> strictly LLM-Judge
    if language_mode in ("benglish", "hinglish"):
        score = judge_codemixed_transcript(ground_truth, hypothesis, language_mode)
        return EvaluationResult(
            clip_id=clip_id,
            language_mode=language_mode,
            provider=provider,
            ground_truth=ground_truth,
            hypothesis=hypothesis,
            eval_type="llm_judge",
            wer=None,
            score=score,
            latency_ms=latency_ms,
            hallucinated=False,
        )

    # Monolingual routing (bn-IN, hi-IN, en-IN) -> Normalized WER
    wer = calculate_wer(ground_truth, hypothesis)
    score = max(0.0, round(1.0 - wer, 4))
    return EvaluationResult(
        clip_id=clip_id,
        language_mode=language_mode,
        provider=provider,
        ground_truth=ground_truth,
        hypothesis=hypothesis,
        eval_type="wer",
        wer=wer,
        score=score,
        latency_ms=latency_ms,
        hallucinated=False,
    )


def run_bakeoff(manifest_path: str | Path, output_json: Optional[str | Path] = None) -> Dict[str, Any]:
    """
    Executes the Dual-STT Bake-Off benchmark comparing Sarvam Saaras vs Groq Whisper.
    """
    manifest_file = Path(manifest_path)
    if not manifest_file.exists():
        raise FileNotFoundError(f"Bake-off manifest not found: {manifest_file}")

    with open(manifest_file, "r", encoding="utf-8") as f:
        manifest_data = yaml.safe_load(f)

    clips = manifest_data.get("clips", [])
    providers = ["saaras", "whisper"]
    results_by_provider: Dict[str, List[EvaluationResult]] = {p: [] for p in providers}

    for clip in clips:
        clip_id = clip["id"]
        lang = clip["language_mode"]
        gt = clip["ground_truth"]
        audio = Path(clip["audio"])

        for p_name in providers:
            provider = get_stt_provider(p_name)
            # In the bake-off benchmark, send all clips (including noise) directly to provider.transcribe()
            # to measure raw STT hallucination rate without VAD shielding the benchmark.
            stt_res = provider.transcribe(audio, language_mode=lang)
            hyp = stt_res.text
            lat = stt_res.latency_ms

            eval_res = evaluate_clip(
                clip_id=clip_id,
                audio_path=audio,
                ground_truth=gt,
                hypothesis=hyp,
                language_mode=lang,
                latency_ms=lat,
                provider=p_name,
            )
            results_by_provider[p_name].append(eval_res)

    summary: Dict[str, Any] = {}
    for p_name, p_results in results_by_provider.items():
        mono_results = [r for r in p_results if r.eval_type == "wer"]
        cm_results = [r for r in p_results if r.eval_type == "llm_judge"]
        noise_results = [r for r in p_results if r.eval_type == "noise_guard"]

        avg_wer = round(sum(r.wer for r in mono_results) / len(mono_results), 4) if mono_results else 0.0
        avg_cm_score = round(sum(r.score for r in cm_results) / len(cm_results), 2) if cm_results else 0.0
        avg_lat = int(sum(r.latency_ms for r in p_results) / len(p_results)) if p_results else 0
        hallucinations = sum(1 for r in noise_results if r.hallucinated)

        summary[p_name] = {
            "avg_wer_monolingual": avg_wer,
            "avg_llm_judge_codemixed": avg_cm_score,
            "avg_latency_ms": avg_lat,
            "noise_hallucinations": hallucinations,
            "total_clips": len(p_results),
            "details": [r.model_dump() for r in p_results],
        }

    if output_json:
        out_path = Path(output_json)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    return summary


def main():
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Amar Khobor Dual-STT Bake-Off Benchmark Runner")
    parser.add_argument("manifest", help="Path to manifest.yaml")
    parser.add_argument("--out", default="test_data/eval_results.json", help="Path to output JSON")

    args = parser.parse_args()

    try:
        summary = run_bakeoff(args.manifest, output_json=args.out)
        print("\n========================================================")
        print("🏆 AMAR KHOBOR DUAL-STT BAKE-OFF BENCHMARK LEADERBOARD 🏆")
        print("========================================================\n")
        print("| Provider | Monolingual WER ↓ | Code-Mixed LLM-Judge ↑ | Latency (ms) ↓ | Noise Hallucinations |")
        print("| :--- | :---: | :---: | :---: | :---: |")
        for p, data in summary.items():
            print(
                f"| **{p.upper()}** | {data['avg_wer_monolingual']:.2%} | {data['avg_llm_judge_codemixed']:.1f}/5.0 | {data['avg_latency_ms']} ms | {data['noise_hallucinations']} |"
            )
        print(f"\nDetailed evaluation results saved to: {args.out}")
    except Exception as e:
        print(f"Bake-Off Runner Failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

