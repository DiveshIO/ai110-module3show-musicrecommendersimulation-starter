"""
RAG Retriever — TF-IDF index over enriched song documents.

Natural-language queries like "chill background music for coding" retrieve
lofi/ambient/focused songs without the user needing to know those labels,
because each song's document is enriched with genre/mood synonym expansions.
"""

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# ── Synonym tables ─────────────────────────────────────────────────────────────

MOOD_SYNONYMS = {
    "happy": "happy joyful upbeat cheerful positive fun bright summer",
    "chill": "chill relaxed calm mellow laid-back peaceful lofi lo-fi coffee coding studying homework background",
    "melancholic": "melancholic sad emotional tearful heartbreak longing bittersweet",
    "intense": "intense powerful strong hard aggressive driving fast",
    "focused": "focused concentration study work productivity focus",
    "confident": "confident bold empowered strong attitude swagger",
    "romantic": "romantic love intimate tender sweet date night",
    "energized": "energized pumped hyped workout gym exercise run running sport training",
    "euphoric": "euphoric ecstatic excited dance party festival",
    "dreamy": "dreamy ethereal floating hazy atmospheric late night",
    "moody": "moody dark brooding mysterious introspective",
    "hopeful": "hopeful optimistic uplifting inspiring motivational sunrise",
    "groovy": "groovy funky danceable rhythm bounce soulful",
    "peaceful": "peaceful calm serene quiet tranquil sleep relax",
    "uplifting": "uplifting inspiring motivational positive feel-good",
    "nostalgic": "nostalgic memories throwback classic vintage retro",
    "powerful": "powerful anthemic epic stadium arena",
    "sentimental": "sentimental emotional heartfelt touching tender",
    "angry": "angry aggressive rage punk",
}

GENRE_SYNONYMS = {
    "pop": "pop popular mainstream charts radio hit catchy",
    "hip-hop": "hip-hop rap hiphop bars rhymes flow beats street",
    "r&b": "r&b rnb soul rhythm blues smooth vibes",
    "rock": "rock guitar band live loud electric",
    "edm": "edm electronic dance club rave drop bass house workout pump energy",
    "country": "country southern american guitars twang heartfelt",
    "jazz": "jazz improvisation swing sophisticated cool",
    "lofi": "lofi lo-fi chill study studying homework beats background coffee coding rainy focus concentration",
    "k-pop": "kpop k-pop korean pop energetic idol",
    "latin": "latin salsa reggaeton spanish dance tropical",
    "indie pop": "indie independent alternative bedroom soft dreamy",
    "classical": "classical orchestra piano symphony beethoven",
    "ambient": "ambient atmospheric background meditation calm rain sleep studying focus reading",
    "folk": "folk acoustic storytelling singer-songwriter gentle",
    "soul": "soul gospel emotional heartfelt groove",
    "blues": "blues slow emotional guitar soulful",
    "synthwave": "synthwave retro 80s neon drive night",
    "metal": "metal heavy intense loud distortion thrash",
    "reggae": "reggae island tropical jamaican positive",
    "trap": "trap beats bass dark street 808",
    "afrobeats": "afrobeats african dance upbeat vibrant",
    "alternative": "alternative indie underground grunge",
    "punk": "punk fast aggressive raw three-chord",
}

# ── Module-level cache keyed by tuple of song IDs ─────────────────────────────
_INDEX_CACHE = {}


def _energy_words(energy):
    """Return descriptive words for a numeric energy level."""
    if energy < 0.25:
        return "very calm soft gentle quiet meditation sleep"
    elif energy < 0.45:
        return "low energy mellow relaxed laid-back slow"
    elif energy < 0.65:
        return "moderate medium balanced easy going"
    elif energy < 0.80:
        return "high energy upbeat active driving"
    else:
        return "very high energy intense powerful loud fast"


def _make_document(song):
    """Build an enriched text document for a single song dict."""
    genre = str(song.get("genre", "")).lower()
    mood = str(song.get("mood", "")).lower()
    energy = float(song.get("energy", 0.5))

    parts = [
        str(song.get("title", "")),
        str(song.get("artist", "")),
        genre,
        GENRE_SYNONYMS.get(genre, genre),
        mood,
        MOOD_SYNONYMS.get(mood, mood),
        _energy_words(energy),
    ]
    return " ".join(p for p in parts if p)


def build_index(songs):
    """
    Build a TF-IDF index over the given list of song dicts.

    Results are cached by the tuple of song IDs so repeated calls with the
    same catalog are fast.

    Returns (vectorizer, matrix, songs).
    """
    cache_key = tuple(s["id"] for s in songs)
    if cache_key in _INDEX_CACHE:
        return _INDEX_CACHE[cache_key]

    documents = [_make_document(s) for s in songs]
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1, stop_words="english")
    matrix = vectorizer.fit_transform(documents)

    result = (vectorizer, matrix, songs)
    _INDEX_CACHE[cache_key] = result
    return result


def retrieve(query, songs, k=8):
    """
    Retrieve the top-k songs matching a natural-language query.

    Returns a list of (song_dict, similarity_float) tuples, ranked by
    cosine similarity, filtered to similarity > 0.01.
    """
    vectorizer, matrix, indexed_songs = build_index(songs)

    query_vec = vectorizer.transform([query])
    sims = cosine_similarity(query_vec, matrix).flatten()

    # Pair each song with its similarity score, then sort descending
    pairs = list(zip(indexed_songs, sims.tolist()))
    pairs.sort(key=lambda x: x[1], reverse=True)

    # Filter weak matches and return top k
    results = [(s, float(sim)) for s, sim in pairs[:k] if sim > 0.01]
    return results
