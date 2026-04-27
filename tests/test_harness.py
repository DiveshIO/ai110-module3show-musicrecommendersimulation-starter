#!/usr/bin/env python3
"""
Music Recommender — Automated Test Harness (CodePath AI110 stretch feature).

Runs the system on predefined user profiles and prints a structured
PASS/FAIL report with per-profile confidence scores.

Usage:
    python tests/test_harness.py
    # exit code 0 = all pass, 1 = any failure
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.recommender import load_songs, recommend_songs, score_song

SONGS_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "songs.csv")

# ── Test definitions ──────────────────────────────────────────────────────────
# Each test has: name, profile, k, assertion lambda, description
# Direct tests (no profile) use a `direct_fn` key instead.

TESTS = [
    {
        "name": "pop_fan_top_result_is_pop",
        "profile": {"favorite_genre": "pop", "favorite_mood": "happy",
                    "target_energy": 0.85, "likes_acoustic": False},
        "k": 3,
        "assert": lambda r: r[0][0]["genre"] == "pop",
        "description": "Top result for pop/happy/high-energy should be a pop song",
    },
    {
        "name": "lofi_fan_top_result_is_lofi",
        "profile": {"favorite_genre": "lofi", "favorite_mood": "chill",
                    "target_energy": 0.40, "likes_acoustic": True},
        "k": 3,
        "assert": lambda r: r[0][0]["genre"] == "lofi",
        "description": "Top result for lofi/chill/acoustic user should be a lofi song",
    },
    {
        "name": "scores_sorted_descending",
        "profile": {"favorite_genre": "rock", "favorite_mood": "intense",
                    "target_energy": 0.90, "likes_acoustic": False},
        "k": 5,
        "assert": lambda r: all(r[i][1] >= r[i+1][1] for i in range(len(r)-1)),
        "description": "Results must be sorted by score descending",
    },
    {
        "name": "max_score_leq_5",
        "profile": {"favorite_genre": "jazz", "favorite_mood": "relaxed",
                    "target_energy": 0.37, "likes_acoustic": True},
        "k": 1,
        "assert": lambda r: r[0][1] <= 5.0,
        "description": "Perfect-match score must not exceed 5.0",
    },
    {
        "name": "unknown_genre_returns_k_results",
        "profile": {"favorite_genre": "bossa nova", "favorite_mood": "relaxed",
                    "target_energy": 0.40, "likes_acoustic": True},
        "k": 5,
        "assert": lambda r: len(r) == 5,
        "description": "Unknown genre should still return k results via mood+energy fallback",
    },
    {
        "name": "very_calm_user_gets_low_energy_top3",
        "profile": {"favorite_genre": "ambient", "favorite_mood": "peaceful",
                    "target_energy": 0.05, "likes_acoustic": True},
        "k": 3,
        "assert": lambda r: all(s[0]["energy"] < 0.55 for s in r),
        "description": "energy=0.05 user's top-3 should all have energy < 0.55",
    },
    {
        "name": "acoustic_bonus_increases_score",
        "profile": None,
        "k": None,
        "assert": None,
        "description": "Acoustic bonus must raise score when likes_acoustic=True",
        "direct_fn": lambda songs: (
            score_song({"favorite_genre":"x","favorite_mood":"x",
                        "target_energy":0.5,"likes_acoustic":True},
                       {"genre":"x","mood":"x","energy":0.5,"acousticness":0.9})[0]
            >
            score_song({"favorite_genre":"x","favorite_mood":"x",
                        "target_energy":0.5,"likes_acoustic":False},
                       {"genre":"x","mood":"x","energy":0.5,"acousticness":0.9})[0]
        ),
    },
    {
        "name": "recommend_songs_returns_tuple_structure",
        "profile": None,
        "k": None,
        "assert": None,
        "description": "recommend_songs result items must be (dict, float, str) triples",
        "direct_fn": lambda songs: (
            isinstance(recommend_songs(
                {"favorite_genre":"pop","favorite_mood":"happy",
                 "target_energy":0.7,"likes_acoustic":False},
                songs, k=2
            )[0], tuple)
        ),
    },
]


def confidence_score(results: list, profile: dict) -> float:
    """
    0–1 score: fraction of top-3 results matching the user's genre or mood.
    Higher = the system clearly understood the user's preferences.
    """
    if not results:
        return 0.0
    top3 = results[:min(3, len(results))]
    hits = sum(
        1 for s, _, _ in top3
        if s.get("genre") == profile.get("favorite_genre") or
           s.get("mood")  == profile.get("favorite_mood")
    )
    return round(hits / len(top3), 2)


def run_harness() -> bool:
    print("=" * 65)
    print("  MUSIC RECOMMENDER — AUTOMATED TEST HARNESS")
    print("=" * 65)

    songs = load_songs(SONGS_PATH)
    print(f"  Catalog loaded: {len(songs)} songs\n")

    passed = failed = 0

    for t in TESTS:
        name = t["name"]
        desc = t["description"]
        try:
            if "direct_fn" in t:
                ok = t["direct_fn"](songs)
                conf_str = ""
            else:
                results = recommend_songs(t["profile"], songs, k=t["k"])
                ok = t["assert"](results)
                conf = confidence_score(results, t["profile"])
                conf_str = f"  confidence={conf:.2f}"

            status = "PASS" if ok else "FAIL"
            if ok:
                passed += 1
            else:
                failed += 1

            symbol = "✅" if ok else "❌"
            print(f"  {symbol} [{status}] {name}")
            print(f"          {desc}{conf_str}")
            print()

        except Exception as exc:
            failed += 1
            print(f"  💥 [ERROR] {name}: {exc}\n")

    print("-" * 65)
    print(f"  Results: {passed} passed, {failed} failed / {passed+failed} total")
    avg_conf = None
    profile_tests = [t for t in TESTS if t.get("profile")]
    if profile_tests:
        confs = []
        for t in profile_tests:
            try:
                r = recommend_songs(t["profile"], songs, k=t["k"])
                confs.append(confidence_score(r, t["profile"]))
            except Exception:
                pass
        if confs:
            avg_conf = sum(confs) / len(confs)
            print(f"  Avg confidence score: {avg_conf:.2f}")
    print("=" * 65)
    return failed == 0


if __name__ == "__main__":
    success = run_harness()
    sys.exit(0 if success else 1)
