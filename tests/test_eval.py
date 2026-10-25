import unicodedata
import pytest
from pipeline.eval import (
    normalize_text_for_wer,
    calculate_wer,
    evaluate_clip,
    EvaluationResult,
)


def test_normalize_text_for_wer():
    # Test ZWJ / ZWNJ removal
    text_with_zwj = "দাদু‌ বললেন‍ ওষুধ!"
    normalized = normalize_text_for_wer(text_with_zwj)
    assert "‌" not in normalized
    assert "‍" not in normalized
    assert "!" not in normalized
    assert normalized == "দাদু বললেন ওষুধ"

    # Test Unicode NFC
    decomposed = unicodedata.normalize("NFD", "কালকে সকালে")
    nfc_result = normalize_text_for_wer(decomposed)
    assert unicodedata.is_normalized("NFC", nfc_result)


def test_calculate_wer():
    ref = "দাদু বললেন ওষুধ নিয়ে আসতে"
    hyp = "দাদু বললেন ওষুধ নিয়ে আসতে"
    assert calculate_wer(ref, hyp) == 0.0

    hyp_one_diff = "দাদু বললেন খাবার নিয়ে আসতে"
    wer = calculate_wer(ref, hyp_one_diff)
    assert 0.0 < wer <= 0.3


def test_evaluate_clip_monolingual():
    res = evaluate_clip(
        clip_id="test_bn_1",
        audio_path="test_data/dummy.wav",
        ground_truth="দাদু বললেন ওষুধ আনতে",
        hypothesis="দাদু বললেন ওষুধ আনতে",
        language_mode="bn-IN",
        latency_ms=300,
        provider="saaras",
    )
    assert res.eval_type == "wer"
    assert res.wer == 0.0
    assert res.score == 1.0  # 100% accuracy


def test_evaluate_clip_codemixed():
    res = evaluate_clip(
        clip_id="test_benglish_1",
        audio_path="test_data/dummy.wav",
        ground_truth="কালকে সকালে airport e পৌঁছাবো",
        hypothesis="Kalke sokale airport e pouchabo",
        language_mode="benglish",
        latency_ms=300,
        provider="saaras",
    )
    # Code-mixed must NOT compute Levenshtein WER across scripts
    assert res.eval_type == "llm_judge"
    assert res.wer is None
    assert 1.0 <= res.score <= 5.0


def test_evaluate_clip_noise_silence():
    res = evaluate_clip(
        clip_id="test_noise_clean",
        audio_path="test_data/dummy.wav",
        ground_truth="[SILENCE/NOISE]",
        hypothesis="",
        language_mode="noise",
        latency_ms=100,
        provider="saaras",
    )
    assert res.eval_type == "noise_guard"
    assert res.hallucinated is False
    assert res.score == 5.0


def test_evaluate_clip_noise_hallucination():
    res = evaluate_clip(
        clip_id="test_noise_hallucinated",
        audio_path="test_data/dummy.wav",
        ground_truth="[SILENCE/NOISE]",
        hypothesis="Thank you for watching! Subscribe for more.",
        language_mode="noise",
        latency_ms=100,
        provider="whisper",
    )
    assert res.eval_type == "noise_guard"
    assert res.hallucinated is True
    assert res.score == 0.0
