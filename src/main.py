"""
Command line runner for the Music Recommender Simulation.

You will implement the functions in recommender.py:
- load_songs
- score_song
- recommend_songs
"""

from src.recommender import load_songs, recommend_songs

# ── Standard user profiles ────────────────────────────────────────────────────
STANDARD_USERS = {
    "High-Energy Pop Fan": {
        "favorite_genre": "pop",
        "favorite_mood": "happy",
        "target_energy": 0.9,
        "likes_acoustic": False,
    },
    "Chill Lofi Studier": {
        "favorite_genre": "lofi",
        "favorite_mood": "chill",
        "target_energy": 0.4,
        "likes_acoustic": True,
    },
    "Deep Intense Rock Listener": {
        "favorite_genre": "rock",
        "favorite_mood": "intense",
        "target_energy": 0.95,
        "likes_acoustic": False,
    },
}

# ── Adversarial / edge-case profiles ─────────────────────────────────────────
# Each is designed to expose a specific weakness or surprising behavior.
ADVERSARIAL_USERS = {
    "Conflicting: High Energy + Melancholic Mood": {
        # Energy says "intense workout" but mood says "sad".
        # Very few songs are both high-energy AND melancholic.
        # Expect: scoring rewards energy matches but can't find the mood —
        # watch for high-energy songs from the wrong emotional category winning.
        "favorite_genre": "folk",
        "favorite_mood": "melancholic",
        "target_energy": 0.95,
        "likes_acoustic": False,
    },
    "Ghost Genre (not in catalog)": {
        # 'bossa nova' exists in the real world but not in songs.csv.
        # Expect: genre score is 0 for every song — mood + energy become
        # the only differentiators, so results feel random/unrelated.
        "favorite_genre": "bossa nova",
        "favorite_mood": "relaxed",
        "target_energy": 0.4,
        "likes_acoustic": True,
    },
    "Acoustic Lover Who Wants Maximum Energy": {
        # likes_acoustic=True pushes toward quiet, gentle songs.
        # target_energy=1.0 pushes toward loud, intense songs.
        # These two signals directly fight each other — acoustic songs in the
        # catalog are almost always low energy. Watch the scorer try to balance.
        "favorite_genre": "folk",
        "favorite_mood": "intense",
        "target_energy": 1.0,
        "likes_acoustic": True,
    },
    "Perfectly Matched (Coffee Shop Stories)": {
        # Constructed to match id=7 exactly on all four fields.
        # Expect: score very close to 5.0, all four reasons fire.
        # Useful as a sanity check that the ceiling works correctly.
        "favorite_genre": "jazz",
        "favorite_mood": "relaxed",
        "target_energy": 0.37,
        "likes_acoustic": True,
    },
    "Energy Floor (target = 0.0)": {
        # Pushes energy proximity to its extreme low end.
        # Lowest-energy song in the catalog is Spacewalk Thoughts at 0.28.
        # Expect: ambient/classical songs float up; metal/EDM sink to the bottom.
        "favorite_genre": "ambient",
        "favorite_mood": "peaceful",
        "target_energy": 0.0,
        "likes_acoustic": True,
    },
}


def _print_results(name: str, profile: dict, songs: list) -> None:
    genre  = profile["favorite_genre"]
    mood   = profile["favorite_mood"]
    energy = profile["target_energy"]
    acoustic = profile["likes_acoustic"]

    print(f"\n{'='*60}")
    print(f"  {name}")
    print(f"  genre={genre!r}  mood={mood!r}  energy={energy}  acoustic={acoustic}")
    print(f"{'='*60}")
    for song, score, explanation in recommend_songs(profile, songs, k=3):
        print(f"  {song['title']} by {song['artist']}  [{score:.2f}/5.0]")
        print(f"    {explanation}")


def main() -> None:
    songs = load_songs("data/songs.csv")
    print(f"Loaded {len(songs)} songs from the dataset.")

    print("\n\n>>> STANDARD PROFILES")
    for name, profile in STANDARD_USERS.items():
        _print_results(name, profile, songs)

    print("\n\n>>> ADVERSARIAL / EDGE-CASE PROFILES")
    for name, profile in ADVERSARIAL_USERS.items():
        _print_results(name, profile, songs)


if __name__ == "__main__":
    main()
