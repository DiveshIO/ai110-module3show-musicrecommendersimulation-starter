"""
AI-powered agentic explanation layer using the Google Gemini API (google-genai SDK).

Two-step agentic workflow per recommendation request:
  Step 1 — Audit:   Gemini reviews top-k scored songs and flags poor fits
                    despite a high numeric score (observable intermediate step).
  Step 2 — Explain: Gemini writes a 1-2 sentence natural-language explanation
                    for each remaining song.

Get a free API key at: https://aistudio.google.com/app/apikey
Set it as: export GEMINI_API_KEY=your_key_here

Graceful degradation: if GEMINI_API_KEY is absent or the API call fails,
the function returns the original scored results unchanged so the app still works.
"""

import json
import logging
import os
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "gemini-2.0-flash"

# ── Prompt (system instruction + few-shot baked in) ───────────────────────────
_SYSTEM_INSTRUCTION = """\
You are MusicMind, a music recommendation assistant.
You receive a user taste profile and a ranked list of candidate songs that were
pre-scored by a content-based algorithm. Your job is a TWO-STEP workflow:

STEP 1 — AUDIT: Review the candidates. Identify any song that, despite its
numeric score, feels like a poor emotional or contextual fit for this user
(e.g. high energy score but totally wrong genre vibe). Output a JSON list of
song IDs to REMOVE (can be empty: []).

STEP 2 — EXPLAIN: For each remaining song write a 1-2 sentence explanation
telling the user WHY this song fits them. Be conversational and reference
concrete attributes (genre, mood, energy level, acousticness). Avoid generic
phrases like "this song matches your preferences."

Respond ONLY with valid JSON — no markdown fences, no extra text:
{
  "step1_removed_ids": [<int>, ...],
  "step1_reasoning": "<one sentence, or 'none removed'>",
  "step2_explanations": {
    "<song_id_as_string>": "<explanation>"
  }
}"""

_FEW_SHOT = """\
Example request:
User: genre=lofi, mood=chill, energy=0.4, likes_acoustic=True
Candidates:
- ID 4: Library Rain by Paper Lanterns | lofi/chill | energy=0.35 | acoustic=0.86 | score=4.83
- ID 2: Midnight Coding by LoRoom | lofi/chill | energy=0.42 | acoustic=0.71 | score=4.81
- ID 17: Signal Drop by Flux State | edm/euphoric | energy=0.95 | acoustic=0.03 | score=2.0

Example response:
{
  "step1_removed_ids": [17],
  "step1_reasoning": "Signal Drop is high-energy EDM — it would shatter a chill study session despite its score.",
  "step2_explanations": {
    "4": "Library Rain wraps you in a soft acoustic cocoon at a gentle 72 BPM — ideal for winding down or deep focus.",
    "2": "Midnight Coding sits right in your energy sweet spot with its unhurried lofi groove and warm acoustic texture."
  }
}
"""


def _candidates_text(candidates: List[Tuple[Dict, float, str]]) -> str:
    lines = []
    for song, score, _ in candidates:
        lines.append(
            f"- ID {song['id']}: {song['title']} by {song['artist']} | "
            f"{song['genre']}/{song['mood']} | energy={song['energy']} | "
            f"acoustic={song['acousticness']} | score={score:.2f}"
        )
    return "\n".join(lines)


def _clean_json(raw: str) -> str:
    """Strip markdown code fences that Gemini sometimes adds despite instructions."""
    text = raw.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        # drop first and last fence lines
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines).strip()
    return text


def ai_explain_recommendations(
    user_prefs: Dict,
    candidates: List[Tuple[Dict, float, str]],
    *,
    model: str = DEFAULT_MODEL,
    max_tokens: int = 1024,
) -> Dict:
    """
    Run the two-step agentic workflow with Gemini and return:
      {
        "final_recommendations": [(song, score, ai_explanation), ...],
        "removed":               [song_id, ...],
        "removal_reason":        str,
        "error":                 None | str,
      }

    Falls back gracefully to original candidates if GEMINI_API_KEY is missing
    or the API call fails.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        logger.warning("GEMINI_API_KEY not set — AI layer skipped.")
        return _fallback(candidates, "GEMINI_API_KEY not set. Get a free key at aistudio.google.com")

    try:
        from google import genai
        from google.genai import types
    except ImportError:
        return _fallback(candidates, "google-genai not installed — run: pip install google-genai")

    client = genai.Client(api_key=api_key)

    user_message = (
        f"{_FEW_SHOT}\n\n"
        f"Now process this real request:\n"
        f"User: genre={user_prefs.get('favorite_genre')}, "
        f"mood={user_prefs.get('favorite_mood')}, "
        f"energy={user_prefs.get('target_energy')}, "
        f"likes_acoustic={user_prefs.get('likes_acoustic')}\n"
        f"Candidates:\n{_candidates_text(candidates)}"
    )

    logger.info("Calling Gemini %s for AI recommendation audit (step 1 + 2)", model)

    try:
        response = client.models.generate_content(
            model=model,
            contents=user_message,
            config=types.GenerateContentConfig(
                system_instruction=_SYSTEM_INSTRUCTION,
                max_output_tokens=max_tokens,
                temperature=0.3,        # low temp = consistent JSON output
            ),
        )
        raw = response.text or ""
        logger.info("Gemini response: %d chars", len(raw))
        if not raw.strip():
            return _fallback(candidates, "Gemini returned an empty response")

        parsed = json.loads(_clean_json(raw))
        removed_ids = {int(x) for x in parsed.get("step1_removed_ids", [])}
        explanations = parsed.get("step2_explanations", {})
        removal_reason = parsed.get("step1_reasoning", "")

        final = []
        for song, score, original_reason in candidates:
            if song["id"] in removed_ids:
                logger.info("AI removed song %d (%s)", song["id"], song["title"])
                continue
            ai_exp = explanations.get(str(song["id"]), original_reason)
            final.append((song, score, ai_exp))

        return {
            "final_recommendations": final,
            "removed": list(removed_ids),
            "removal_reason": removal_reason,
            "error": None,
        }

    except json.JSONDecodeError as exc:
        logger.error("Failed to parse Gemini JSON: %s", exc)
        return _fallback(candidates, f"JSON parse error: {exc}")
    except Exception as exc:
        logger.error("Gemini API error: %s", exc)
        return _fallback(candidates, str(exc))


def _fallback(candidates, reason: str) -> Dict:
    return {
        "final_recommendations": candidates,
        "removed": [],
        "removal_reason": reason,
        "error": reason,
    }


def ai_rag_explain(
    query: str,
    retrieved: List[Tuple[Dict, float]],
    *,
    model: str = DEFAULT_MODEL,
    max_tokens: int = 800,
) -> Dict:
    """
    Generate AI explanations for RAG-retrieved songs.

    Takes a natural-language query and a list of (song_dict, similarity_score)
    tuples returned by the RAG retriever, and asks Gemini to explain why each
    song matches the query vibe.

    Returns:
      {
        "explanations": {song_id_str: explanation_str, ...},
        "summary":      str,
        "error":        None | str,
      }
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return {"explanations": {}, "summary": "", "error": "GEMINI_API_KEY not set"}

    try:
        from google import genai
        from google.genai import types
    except ImportError:
        return {"explanations": {}, "summary": "",
                "error": "google-genai not installed — run: pip install google-genai"}

    # Build the candidate lines
    lines = []
    for song, sim in retrieved:
        lines.append(
            f"- ID {song['id']}: {song['title']} by {song['artist']} | "
            f"{song['genre']}/{song['mood']} | energy={song['energy']} | "
            f"similarity={sim:.2f}"
        )
    candidates_text = "\n".join(lines)

    prompt = (
        f'A user searched for songs matching this vibe: "{query}"\n\n'
        f"The retrieval system found these songs from the catalog:\n"
        f"{candidates_text}\n\n"
        f"For each song, write 1 sentence explaining WHY it matches this specific vibe/query.\n"
        f"Reference the genre, mood, energy, or artist style. Be specific to the query.\n"
        f"Also write a 1-sentence summary of what kind of vibe these songs share.\n\n"
        f'Respond ONLY with valid JSON:\n'
        f'{{"summary": "<1 sentence>", "explanations": {{"<song_id_as_string>": "<explanation>"}}}}'
    )

    logger.info("Calling Gemini %s for RAG vibe explanations (query=%r)", model, query)

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                max_output_tokens=max_tokens,
                temperature=0.4,
            ),
        )
        raw = response.text or ""
        logger.info("Gemini RAG response: %d chars", len(raw))
        if not raw.strip():
            return {"explanations": {}, "summary": "", "error": "Gemini returned an empty response"}

        parsed = json.loads(_clean_json(raw))
        return {
            "explanations": parsed.get("explanations", {}),
            "summary": parsed.get("summary", ""),
            "error": None,
        }

    except Exception as exc:
        logger.error("Gemini RAG error: %s", exc)
        return {"explanations": {}, "summary": "", "error": str(exc)}
