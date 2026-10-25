# Amar Khobor (আমার খবর)

> **"You slept. It listened. Here's what you missed."**

Amar Khobor turns a chaotic overnight WhatsApp group — dozens of voice notes in Bengali, Hindi, English, Benglish, and Hinglish — into one warm, two-minute audio briefing you can play while making morning tea. No more scrolling through 40 voice notes to find out who needs what by when.

**[▶ Listen to a sample briefing](demo/sample_briefing.mp3)** · **[Read the build story](YOUR_DEVTO_POST_URL)**

---

## The Problem

Family WhatsApp groups don't sleep. While you were asleep, someone asked for a medicine refill, someone's flight got delayed, a school form needs signing by noon, and three people argued about dinner plans — all in voice notes, half of them in Benglish that autocorrect can't parse.

Catching up means playing every note, remembering who said what, and mentally assembling a to-do list. Every morning. For every family member who doesn't have time for that.

**Amar Khobor does it for you.** Drop in the group's WhatsApp export, and get back a spoken briefing plus a visual receipt for every claim — who said it, when, and whether it needs action.

## Demo

> [**▶ Sample audio briefing**](demo/sample_briefing.mp3)  
> *Generated from a real multilingual family WhatsApp export: 4 voice notes in Bengali and Benglish, summarized by Gemma, narrated with ElevenLabs.*

The digest arrives as two things at once:

- **A spoken script** — warm and conversational, like a family member catching you up. No timestamps, no citations read aloud.
- **Show notes** — structured cards below the player, mapping every claim to its sender and timestamp: `Dadu → Telma 40 refill → health → needs action`.

## How It Works

```text
WhatsApp .zip export
      │
      ▼
┌─────────────┐   ┌──────────────┐   ┌─────────────┐
│  Extract    │──▶│  Normalize   │──▶│  VAD Filter │
│ _chat.txt   │   │ FFmpeg 16kHz │   │ skip noise  │
│ + voice     │   │ mono WAV     │   │ save credits│
└─────────────┘   └──────────────┘   └─────────────┘
                                           │
                              ┌────────────┴────────────┐
                              ▼                         ▼
                      ┌──────────────┐         ┌──────────────┐
                      │ Sarvam       │    vs   │ Groq Whisper │
                      │ Saaras       │         │ large-v3     │
                      └──────────────┘         └──────────────┘
                              │                         │
                              └────────────┬────────────┘
                                           ▼
                                 ┌──────────────────┐
                                 │  Gemma 4         │
                                 │  spoken_script + │
                                 │  show_notes      │
                                 └──────────────────┘
                                           │
                                 ┌─────────┴─────────┐
                                 ▼                   ▼
                          ┌────────────┐     ┌────────────┐
                          │ Edge-TTS   │ or  │ ElevenLabs │
                          │ (dev)      │     │ (demo)     │
                          └────────────┘     └────────────┘
```

### Design decisions worth explaining

**Why two STT engines?** Because neither is obviously right for a Bengali family group. Saaras is built for Indic languages and code-mixed speech; Whisper-large-v3 is the high-throughput open baseline. Instead of guessing, Amar Khobor treats STT as a pluggable interface and benchmarks both on real family audio — the pipeline, the database schema, and the UI all record which provider produced every transcript.

**Why filter audio before STT?** Voice notes are the expensive part. An energy-based VAD pass tags silence and background noise *before* any API call, so a forwarded chain of muted clips costs nothing. Forwarded messages are also excluded from summarization — nobody needs a briefing about a chain-forwarded good-morning graphic.

**Why one LLM call for both outputs?** The spoken script and the show notes describe the same events; generating them in a single structured Gemma call keeps them consistent — if the script says Dadu needs medicine, the show notes card for it exists too.

**Why a 202-and-poll architecture?** A real overnight export can take a minute to process. `POST /digests/run` returns `202 Accepted` immediately, FastAPI `BackgroundTasks` does the work, and the frontend polls every 2 seconds. No Celery, no Redis, no message broker — this is a family tool, not a distributed system.

## The Dual-STT Bake-Off

Rather than pick a transcription provider based on a benchmark table from someone else's dataset, Amar Khobor ships with a bake-off harness that scores Saaras and Whisper on **your own family's audio**.

| Clip type | Scoring method | Why |
|---|---|---|
| Bengali / Hindi / English | Word Error Rate (WER) | Direct comparison is valid within one script |
| Benglish / Hinglish | Gemma LLM-judge, semantic fidelity 1–5 | Providers output different scripts (native Indic vs Romanized); Levenshtein distance across scripts is meaningless |
| Noise / silence | Hallucination guard | Measures whether a provider invents speech from nothing |

Text normalization before WER: Unicode NFC, zero-width joiner/non-joiner stripping, punctuation and case folding.

**Results from a real 13-second Bengali voice note** (food order, Benglish mixed in):

| Provider | Transcript quality |
|---|---|
| **Saaras** | Coherent and complete — captured the full request including "দুটো রুটি হলে হবে" and code-mixed "চিলি চিকেন করিস, বেটার হবে" |
| **Whisper** | Repetitive and fragmented — lost sentence structure, repeated "চিকেন" three times, dropped context |


## Why Open Models Matter

This is a tool for **family voice notes** — some of the most private audio that exists. That constraint shaped every choice:

- **Gemma 4** summarizes the digest because it's an open-weight model I can swap, self-host, or point at any provider without rewriting the pipeline. The `LLM_PROVIDER` interface accepts Google AI Studio or any OpenAI-compatible endpoint (OpenRouter included) — no vendor lock-in on the brain of the system.
- **Whisper-large-v3 via Groq** is the open-weights baseline, so the STT comparison is between two models whose weights and behavior I can inspect — not a black box I have to trust.
- **Edge-TTS** keeps development free and local-first; ElevenLabs is opt-in for the final demo voice, never a hard dependency.
- **MongoDB's free tier and a fallback in-memory store** mean the whole system runs on zero infrastructure cost.

The result: a family can run this on their own terms, with their own keys, and swap any component without forking the project.

## Tech Stack

| Layer | Choice |
|---|---|
| Pipeline | Python 3.12, FFmpeg, energy-based VAD |
| STT | Sarvam Saaras · Groq Whisper-large-v3 (pluggable) |
| Summarization | Gemma 4 via Gemini API (OpenAI-compatible fallback supported) |
| TTS | Edge-TTS (dev) · ElevenLabs (demo) |
| Backend | FastAPI, Pydantic v2, Motor (MongoDB async) |
| Frontend | Next.js App Router, TypeScript, Tailwind CSS |
| Database | MongoDB Atlas M0, with in-memory fallback |

## Quick Start

```bash
# 1. Clone and set up
git clone https://github.com/Tamajit-005/Amar-Khobor.git
cd Amar-Khobor
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Configure — copy the template and add your keys
cp .env.example .env
# edit .env: add SARVAM_API_KEY, GROQ_API_KEY, GEMINI_API_KEY

# 3. Run the pipeline on a WhatsApp export
python -m pipeline.run sample_data/sample_chat.zip --provider saaras

# 4. Or run the full stack
uvicorn backend.main:app --reload --port 8000
cd frontend && npm install && npm run dev
```

### Run the bake-off yourself

```bash
python -m pipeline.eval test_data/manifest.yaml --out output/bakeoff_results.json
```

### Mock mode (zero API calls)

```bash
# In .env
MOCK_MODE=true
```

Runs the entire pipeline against local fixtures — useful for development and CI without spending credits.

## Project Structure

```text
pipeline/           Core processing pipeline
├── extract.py      WhatsApp _chat.txt parser (Android + iOS formats)
├── normalize.py    FFmpeg 16kHz mono resampler
├── vad.py          Energy-based voice activity detection
├── stt/            Pluggable STT (saaras, whisper)
├── summarize.py    Gemma dual-output digest
├── tts/            Edge-TTS and ElevenLabs adapters
├── eval.py         Bake-off harness (WER + LLM-judge + noise guard)
└── run.py          CLI runner

backend/            FastAPI server, MongoDB persistence
frontend/           Next.js single-page UI
tests/              37 tests covering parser, VAD, STT, TTS, eval, API
test_data/          Bake-off manifest + voice clips
sample_data/        Demo WhatsApp export fixture
demo/               Real sample briefing MP3, structured JSON digest, and STT bake-off comparison
```

## Honest Limitations

- **Gemma reasoning & schema wrapping:** Gemma 4 occasionally emitted internal chain-of-thought monologue before the JSON digest, and sometimes wrapped the output in an array (`[{...}]`). The pipeline hardens the prompt against preambles and employs a tolerant backward JSON extractor anchored to `"spoken_script"`, turning a flaky LLM response into a deterministic parse.
- **STT accuracy on heavy code-mixing varies.** Saaras handled my Benglish test clip well; Whisper struggled. One clip is an anecdote, not a benchmark — the bake-off harness exists precisely because more clips are needed before claiming a winner.
- **The VAD is energy-based, not neural.** It's cheap and fast, but a loud TV in the background can fool it. A neural VAD (Silero) is the obvious next upgrade.
- **No authentication on the API.** This is a single-family deployment assumption. Before multi-user use, it needs auth and per-user rate limits.
- **Benglish ground truth is manual.** There's no standard Romanized-Bengali orthography, so bake-off ground truths are typed by hand — which limits how many clips are practical to score.

## License

MIT — see [LICENSE](LICENSE).

---

*Built for the [Hacktoberfest Open-Source AI Challenge, Week 3](https://dev.to/challenges/hacktoberfest-week3-2026-10-19/). Speech-to-text by [Sarvam AI](https://sarvam.ai/) and [Groq](https://groq.com/); briefing voice by [ElevenLabs](https://elevenlabs.io/).*