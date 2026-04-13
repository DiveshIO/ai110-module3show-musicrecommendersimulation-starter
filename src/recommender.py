from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

@dataclass
class Song:
    """
    Represents a song and its attributes.
    Required by tests/test_recommender.py
    """
    id: int
    title: str
    artist: str
    genre: str
    mood: str
    energy: float
    tempo_bpm: float
    valence: float
    danceability: float
    acousticness: float

@dataclass
class UserProfile:
    """
    Represents a user's taste preferences.
    Required by tests/test_recommender.py
    """
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool

class Recommender:
    """
    OOP implementation of the recommendation logic.
    Required by tests/test_recommender.py
    """
    def __init__(self, songs: List[Song]):
        """Store the catalog of songs this recommender will score and rank."""
        self.songs = songs

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        """Return the top k songs from the catalog ranked by fit for the given user."""
        # TODO: Implement recommendation logic
        return self.songs[:k]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        """Return a human-readable string explaining why song was recommended for user."""
        # TODO: Implement explanation logic
        return "Explanation placeholder"

def load_songs(csv_path: str) -> List[Dict]:
    """Read songs.csv and return a list of dicts with numeric fields cast to int or float."""
    import csv

    int_fields   = {"id"}
    float_fields = {"energy", "tempo_bpm", "valence", "danceability", "acousticness"}

    songs = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            for field in int_fields:
                row[field] = int(row[field])
            for field in float_fields:
                row[field] = float(row[field])
            songs.append(row)
    return songs

def score_song(user_prefs: Dict, song: Dict) -> Tuple[float, List[str]]:
    """Score one song against user preferences (max 5.0) and return (score, reasons).

    Scoring weights (weight-shift experiment: genre halved, energy doubled):
      Genre match        +1.0   (exact string match)          ← was +2.0
      Mood match         +1.5   (exact string match)
      Energy proximity   +2.0   (2.0 - 2*|song_energy - target_energy|, floored at 0)  ← was +1.0
      Acousticness fit   +0.5   (song_acousticness * 0.5, only when likes_acoustic=True)
    """
    score = 0.0
    reasons = []

    # ── Genre match: +1.0 (halved from +2.0) ────────────────────────────────
    if song.get("genre") == user_prefs.get("favorite_genre"):
        score += 1.0
        reasons.append("genre match (+1.0)")

    # ── Mood match: +1.5 ────────────────────────────────────────────────────
    if song.get("mood") == user_prefs.get("favorite_mood"):
        score += 1.5
        reasons.append("mood match (+1.5)")

    # ── Energy proximity: up to +2.0 (doubled from +1.0) ────────────────────
    if "target_energy" in user_prefs and "energy" in song:
        diff = abs(song["energy"] - user_prefs["target_energy"])
        energy_points = round(max(0.0, 2.0 - 2.0 * diff), 2)
        if energy_points > 0:
            score += energy_points
            reasons.append(f"energy close (+{energy_points})")

    # ── Acousticness fit: up to +0.5 ────────────────────────────────────────
    if user_prefs.get("likes_acoustic") and "acousticness" in song:
        acoustic_points = round(song["acousticness"] * 0.5, 2)
        if acoustic_points > 0:
            score += acoustic_points
            reasons.append(f"acoustic preference (+{acoustic_points})")

    return round(score, 2), reasons

def recommend_songs(user_prefs: Dict, songs: List[Dict], k: int = 5) -> List[Tuple[Dict, float, str]]:
    """Score every song in the catalog, sort by score descending, and return the top k as (song, score, explanation)."""
    # 1. Score every song in the catalog — no skipping, no early slicing
    scored = []
    for song in songs:
        score, reasons = score_song(user_prefs, song)
        explanation = ", ".join(reasons) if reasons else "no matching preferences"
        scored.append((song, score, explanation))
    # 2. Sort the full list of songs by score, highest first
    ranked = sorted(scored, key=lambda item: item[1], reverse=True)

    # 3. Return only the top k results
    return ranked[:k]
