import os
import re
import pytest
from pipeline.summarize import ShowNoteItem, DigestResponse, generate_digest
from pipeline.extract import VoiceNoteItem


def test_digest_schemas():
    note = ShowNoteItem(
        claim="Dadu needs his blood pressure medicine by noon",
        sender="Dadu",
        timestamp="Yesterday 8:14 PM",
        category="health",
        urgent=True,
    )
    digest = DigestResponse(
        spoken_script="Good morning everyone! Dadu reminded us that his medicine needs to be picked up today.",
        show_notes=[note],
    )

    assert digest.spoken_script
    assert len(digest.show_notes) == 1
    assert digest.show_notes[0].category == "health"
    assert digest.show_notes[0].urgent is True


def test_mock_generate_digest(tmp_path):
    os.environ["MOCK_MODE"] = "true"

    transcripts = [
        {
            "clip_id": "clip_001",
            "sender": "Dadu",
            "timestamp_str": "23/10/2026, 08:14",
            "text": "আমার প্রেশারের ওষুধ শেষ হয়ে গেছে, দুপুরে আসার সময় একটু নিয়ে এসো।",
            "is_forwarded": False,
        },
        {
            "clip_id": "clip_002",
            "sender": "Ma",
            "timestamp_str": "23/10/2026, 08:16",
            "text": "এই ফরোয়ার্ডেড মেসেজটা সবাইকে পাঠিয়ে দাও।",
            "is_forwarded": True,  # Chain spam, must be ignored
        },
        {
            "clip_id": "clip_003",
            "sender": "Rahul",
            "timestamp_str": "23/10/2026, 09:30",
            "text": "I will reach Kolkata airport by 5 PM, please arrange a cab.",
            "is_forwarded": False,
        },
    ]

    result = generate_digest(transcripts)

    assert isinstance(result, DigestResponse)
    assert len(result.spoken_script) <= 2500
    assert len(result.spoken_script) > 50

    # Invariant Check: NO bracketed citations in spoken script
    assert not re.search(r"\[.*?\]", result.spoken_script)

    # Invariant Check: NO clock timestamps in spoken script (e.g. 08:14, 5:00 PM)
    assert not re.search(r"\b\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)?\b", result.spoken_script)

    # Invariant Check: Receipts exist in show_notes
    assert len(result.show_notes) >= 2
    claims = [n.claim for n in result.show_notes]
    senders = [n.sender for n in result.show_notes]

    assert "Dadu" in senders
    assert "Rahul" in senders
    # Ma's forwarded message was excluded
    assert "Ma" not in senders


def test_json_extraction_with_conversational_preamble():
    raw_llm_response = """Here is the family morning briefing you requested:
```json
{
  "spoken_script": "Good morning family! Hope everyone is having a peaceful morning.",
  "show_notes": [
    {
      "claim": "Family meeting scheduled for dinner",
      "sender": "Ma",
      "timestamp": "8:00 PM",
      "category": "event",
      "urgent": false
    }
  ]
}
```
Hope this is helpful! Let me know if you need any changes."""

    start_idx = raw_llm_response.find("{")
    end_idx = raw_llm_response.rfind("}")
    assert start_idx != -1 and end_idx != -1
    extracted = raw_llm_response[start_idx : end_idx + 1]

    import json
    parsed = json.loads(extracted)
    digest = DigestResponse(
        spoken_script=parsed["spoken_script"],
        show_notes=[ShowNoteItem(**item) for item in parsed["show_notes"]],
    )
    assert digest.spoken_script.startswith("Good morning")
    assert len(digest.show_notes) == 1
    assert digest.show_notes[0].category == "event"


def test_json_extraction_with_cot_rambling_and_array_wrapper():
    # Simulates Gemma dumping internal monologue with curly braces before emitting an array-wrapped JSON object
    raw_cot_response = """Let's think step by step:
1. First, we need to extract claims: { "thought": "Dadu needs medicine", "step": 1 }
2. Next, draft the spoken_script without brackets or timestamps.
3. Show notes must have verified claims.

Here is the final output:
[
  {
    "spoken_script": "Good morning everyone! Dadu reminded us that medicines must be brought home.",
    "show_notes": [
      {
        "claim": "Dadu needs medicine",
        "sender": "Dadu",
        "timestamp": "8:14 PM",
        "category": "health",
        "urgent": true
      }
    ]
  }
]
Hope this helps!"""

    idx = raw_cot_response.rfind('"spoken_script"')
    assert idx != -1
    start_idx = raw_cot_response.rfind("{", 0, idx)
    end_idx = raw_cot_response.rfind("}")
    assert start_idx != -1 and end_idx != -1 and end_idx > start_idx
    cleaned_json = raw_cot_response[start_idx : end_idx + 1]

    import json
    data = json.loads(cleaned_json)
    if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
        data = data[0]

    digest = DigestResponse(
        spoken_script=data["spoken_script"],
        show_notes=[ShowNoteItem(**item) for item in data["show_notes"]],
    )
    assert "Dadu" in digest.spoken_script
    assert len(digest.show_notes) == 1
    assert digest.show_notes[0].urgent is True
