import json
import os
import re
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

from pipeline import is_mock_mode, require_key


CategoryType = Literal["health", "money", "travel", "event", "other"]


class ShowNoteItem(BaseModel):
    claim: str
    sender: str
    timestamp: str
    category: CategoryType = "other"
    urgent: bool = False


class DigestResponse(BaseModel):
    spoken_script: str = Field(
        ...,
        description="Warm conversational narrative script without bracketed citations or clock timestamps. Max 2500 chars.",
    )
    show_notes: List[ShowNoteItem] = Field(
        ...,
        description="Structured receipts panel with claim, sender, timestamp, and category.",
    )


SUMMARIZER_PROMPT = """You are the loving, attentive voice of 'Amar Khobor' (আমার খবর) for an Indian multilingual family WhatsApp group.
Review the following transcribed overnight voice notes.

CRITICAL INVARIANTS:
1. `spoken_script`:
   - Warm, natural, caring narrative voice in Bengali/English (or English/Hindi as suitable for the family).
   - Attribute information naturally ("Dadu mentioned that...", "Rahul said he will arrive...").
   - STRICTLY FORBIDDEN: NEVER include timestamps (e.g., 'at 8:14 PM') or brackets/citations (e.g., '[Dadu, 10:20]').
   - Maximum length: 2,500 characters.
2. `show_notes`:
   - Array of objects containing:
     - `claim`: Clear, concise summary of the fact or request.
     - `sender`: Person who sent the voice note.
     - `timestamp`: Date/time formatted for display (e.g., "Yesterday 8:14 PM").
     - `category`: Exactly one of "health", "money", "travel", "event", "other".
     - `urgent`: true if time-sensitive (medicine, safety, urgent airport pickup), else false.
3. Ignore forwarded messages (marked with is_forwarded=True) as chain spam.

INPUT TRANSCRIPTS:
{transcripts_json}

OUTPUT FORMAT:
Respond with pure JSON matching the following schema:
{{
  "spoken_script": "...",
  "show_notes": [
    {{
      "claim": "...",
      "sender": "...",
      "timestamp": "...",
      "category": "health|money|travel|event|other",
      "urgent": true|false
    }}
  ]
}}
"""


def _sanitize_spoken_script(script: str) -> str:
    """Safety guard to strip any stray bracketed citations or clock timestamps."""
    # Strip bracketed citations like [Dadu] or [10:15]
    cleaned = re.sub(r"\[.*?\]", "", script)
    # Strip clock timestamps like 08:14 or 5:00 PM or 8:15 am
    cleaned = re.sub(r"\b\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)?\b", "", cleaned)
    # Clean up double spaces
    cleaned = re.sub(r" {2,}", " ", cleaned).strip()
    if len(cleaned) <= 2500:
        return cleaned
    truncated = cleaned[:2500]
    last_space = truncated.rfind(" ")
    return truncated[:last_space].rstrip() if last_space > 0 else truncated


def generate_digest(
    transcripts: List[Dict[str, Any]],
    api_key: Optional[str] = None,
    model_name: Optional[str] = None,
) -> DigestResponse:
    is_mock = is_mock_mode()

    # Filter out forwarded messages
    valid_transcripts = [t for t in transcripts if not t.get("is_forwarded", False)]

    if not valid_transcripts:
        return DigestResponse(
            spoken_script="Good morning everyone! There were no new family voice notes overnight. Have a wonderful day ahead!",
            show_notes=[],
        )

    if is_mock:
        # Generate rich deterministic mock response
        notes: List[ShowNoteItem] = []
        for t in valid_transcripts:
            sender = t.get("sender", "Family Member")
            text = t.get("text", "")
            ts = t.get("timestamp_str", "Last Night")

            category: CategoryType = "other"
            urgent = False
            lower_text = text.lower()
            if any(w in lower_text for w in ["ওষুধ", "medicine", "doctor", "হসপিটাল", "health"]):
                category = "health"
                urgent = True
                claim = f"{sender} requested medicines to be picked up"
            elif any(w in lower_text for w in ["flight", "airport", "train", "reach", "travel", "পৌঁছাবো"]):
                category = "travel"
                urgent = True
                claim = f"{sender} is arriving and needs transit/cab arranged"
            elif any(w in lower_text for w in ["টাকা", "money", "payment", "bank", "account"]):
                category = "money"
                claim = f"{sender} mentioned an important payment"
            elif any(w in lower_text for w in ["dinner", "lunch", "event", "party", "অনুষ্ঠান"]):
                category = "event"
                claim = f"{sender} updated the family meal/gathering plan"
            else:
                claim = f"{sender} shared an overnight update: {text[:60]}"

            notes.append(
                ShowNoteItem(
                    claim=claim,
                    sender=sender,
                    timestamp=ts,
                    category=category,
                    urgent=urgent,
                )
            )

        spoken_script = (
            "Good morning family! Here is your quick morning briefing. "
            "Dadu reminded everyone that his medicine needs to be brought home today. "
            "Also, Rahul will be arriving at Kolkata airport this evening, so please make sure a cab is arranged. "
            "Wishing everyone a calm and productive day ahead!"
        )

        return DigestResponse(
            spoken_script=_sanitize_spoken_script(spoken_script),
            show_notes=notes,
        )

    # Live Gemma / LLM generation
    key = api_key or require_key("GEMINI_API_KEY", "Gemma summarizer")
    active_model = model_name or os.getenv("GEMMA_MODEL") or os.getenv("LLM_MODEL") or "gemma-4"
    custom_url = os.getenv("LLM_API_URL", "").strip()

    prompt = SUMMARIZER_PROMPT.format(
        transcripts_json=json.dumps(valid_transcripts, ensure_ascii=False, indent=2)
    )

    if custom_url:
        # Custom endpoint (e.g. Groq, vLLM, or OpenAI-compatible gateway)
        import httpx
        headers = {"Authorization": f"Bearer {key}"}
        payload = {
            "model": active_model,
            "messages": [
                {"role": "system", "content": "You are Amar Khobor. Always output valid JSON strictly."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
        }
        resp = httpx.post(custom_url, headers=headers, json=payload, timeout=60.0)
        if resp.status_code != 200:
            raise RuntimeError(f"LLM API Error ({resp.status_code}): {resp.text}")
        content = resp.json()["choices"][0]["message"]["content"]
    else:
        # Standard Google Generative AI (Gemma / Google AI Studio)
        import google.generativeai as genai
        genai.configure(api_key=key)
        model = genai.GenerativeModel(active_model)
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"},
        )
        content = response.text

    # Robust extraction between first '{' and last '}' to handle preambles, chat, or code fences
    start_idx = content.find("{")
    end_idx = content.rfind("}")
    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        cleaned_json = content[start_idx : end_idx + 1]
    else:
        cleaned_json = content.strip()

    try:
        data = json.loads(cleaned_json)
        script = _sanitize_spoken_script(data.get("spoken_script", ""))
        show_notes = [ShowNoteItem(**item) for item in data.get("show_notes", [])]
        return DigestResponse(spoken_script=script, show_notes=show_notes)
    except Exception as e:
        raise ValueError(f"Failed to parse Gemma digest response: {e}\nRaw output: {content}")
