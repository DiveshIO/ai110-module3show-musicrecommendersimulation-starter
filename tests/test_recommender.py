import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.recommender import Song, UserProfile, Recommender, load_songs, recommend_songs, score_song

SONGS_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "songs.csv")


# ── Fixtures ──────────────────────────────────────────────────────────────────

def make_small_recommender() -> Recommender:
    songs = [
        Song(id=1, title="Test Pop Track", artist="Test Artist",
             genre="pop", mood="happy", energy=0.8, tempo_bpm=120,
             valence=0.9, danceability=0.8, acousticness=0.2),
        Song(id=2, title="Chill Lofi Loop", artist="Test Artist",
             genre="lofi", mood="chill", energy=0.4, tempo_bpm=80,
             valence=0.6, danceability=0.5, acousticness=0.9),
    ]
    return Recommender(songs)


# ── OOP interface tests ───────────────────────────────────────────────────────

def test_recommend_returns_songs_sorted_by_score():
    user = UserProfile(favorite_genre="pop", favorite_mood="happy",
                       target_energy=0.8, likes_acoustic=False)
    rec = make_small_recommender()
    results = rec.recommend(user, k=2)

    assert len(results) == 2
    assert results[0].genre == "pop"
    assert results[0].mood == "happy"


def test_explain_recommendation_returns_non_empty_string():
    user = UserProfile(favorite_genre="pop", favorite_mood="happy",
                       target_energy=0.8, likes_acoustic=False)
    rec = make_small_recommender()
    explanation = rec.explain_recommendation(user, rec.songs[0])
    assert isinstance(explanation, str)
    assert explanation.strip() != ""


def test_explain_recommendation_mentions_match_reason():
    user = UserProfile(favorite_genre="pop", favorite_mood="happy",
                       target_energy=0.8, likes_acoustic=False)
    rec = make_small_recommender()
    explanation = rec.explain_recommendation(user, rec.songs[0])
    assert "genre" in explanation or "mood" in explanation or "energy" in explanation


# ── score_song unit tests ─────────────────────────────────────────────────────

def test_score_song_genre_match_adds_points():
    song  = {"genre": "pop", "mood": "sad", "energy": 0.5, "acousticness": 0.1}
    prefs = {"favorite_genre": "pop", "favorite_mood": "happy",
             "target_energy": 0.5, "likes_acoustic": False}
    score, reasons = score_song(prefs, song)
    assert score >= 1.0
    assert any("genre" in r for r in reasons)


def test_score_song_no_genre_no_mood_match():
    song  = {"genre": "metal", "mood": "angry", "energy": 0.5, "acousticness": 0.1}
    prefs = {"favorite_genre": "pop", "favorite_mood": "happy",
             "target_energy": 0.5, "likes_acoustic": False}
    _, reasons = score_song(prefs, song)
    assert not any("genre" in r for r in reasons)
    assert not any("mood" in r for r in reasons)


def test_acoustic_bonus_only_when_likes_acoustic_true():
    song      = {"genre": "folk", "mood": "chill", "energy": 0.5, "acousticness": 0.9}
    prefs_on  = {"favorite_genre": "x", "favorite_mood": "x",
                 "target_energy": 0.5, "likes_acoustic": True}
    prefs_off = {"favorite_genre": "x", "favorite_mood": "x",
                 "target_energy": 0.5, "likes_acoustic": False}
    score_on,  _ = score_song(prefs_on, song)
    score_off, _ = score_song(prefs_off, song)
    assert score_on > score_off


def test_score_song_max_does_not_exceed_5():
    song  = {"genre": "jazz", "mood": "relaxed", "energy": 0.37, "acousticness": 1.0}
    prefs = {"favorite_genre": "jazz", "favorite_mood": "relaxed",
             "target_energy": 0.37, "likes_acoustic": True}
    score, _ = score_song(prefs, song)
    assert score <= 5.0


def test_score_song_returns_tuple():
    song  = {"genre": "pop", "mood": "happy", "energy": 0.7, "acousticness": 0.2}
    prefs = {"favorite_genre": "pop", "favorite_mood": "happy",
             "target_energy": 0.7, "likes_acoustic": False}
    result = score_song(prefs, song)
    assert isinstance(result, tuple)
    assert len(result) == 2
    assert isinstance(result[0], float)
    assert isinstance(result[1], list)


# ── recommend_songs integration tests ────────────────────────────────────────

def test_recommend_songs_returns_exactly_k():
    songs = load_songs(SONGS_PATH)
    results = recommend_songs({"favorite_genre": "pop", "favorite_mood": "happy",
                               "target_energy": 0.8, "likes_acoustic": False},
                              songs, k=4)
    assert len(results) == 4


def test_recommend_songs_sorted_descending():
    songs = load_songs(SONGS_PATH)
    results = recommend_songs({"favorite_genre": "rock", "favorite_mood": "intense",
                               "target_energy": 0.9, "likes_acoustic": False},
                              songs, k=5)
    scores = [r[1] for r in results]
    assert scores == sorted(scores, reverse=True)


def test_recommend_songs_unknown_genre_still_returns_k():
    songs = load_songs(SONGS_PATH)
    results = recommend_songs({"favorite_genre": "bossa nova", "favorite_mood": "relaxed",
                               "target_energy": 0.4, "likes_acoustic": True},
                              songs, k=5)
    assert len(results) == 5


def test_recommend_songs_result_is_triples():
    songs = load_songs(SONGS_PATH)
    results = recommend_songs({"favorite_genre": "pop", "favorite_mood": "happy",
                               "target_energy": 0.7, "likes_acoustic": False},
                              songs, k=2)
    for item in results:
        assert isinstance(item, tuple)
        assert len(item) == 3
        assert isinstance(item[0], dict)  # song
        assert isinstance(item[1], float) # score
        assert isinstance(item[2], str)   # explanation
