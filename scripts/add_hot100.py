#!/usr/bin/env python3
"""
Bulk-add Billboard Hot 100 (week of April 25, 2026) to data/songs.csv.
Looks up each song via the iTunes Search API to get the primary genre,
falls back to a hard-coded artist→genre map for unknowns.

Run once from the repo root:
    python scripts/add_hot100.py
"""

import csv
import os
import sys
import time
import requests

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "songs.csv")

# ── Billboard Hot 100 — week of April 25, 2026 ───────────────────────────────
HOT_100 = [
    (1,  "Choosin' Texas",                          "Ella Langley"),
    (2,  "Man I Need",                              "Olivia Dean"),
    (3,  "I Just Might",                            "Bruno Mars"),
    (4,  "Be Her",                                  "Ella Langley"),
    (5,  "Ordinary",                                "Alex Warren"),
    (6,  "So Easy (To Fall In Love)",               "Olivia Dean"),
    (7,  "Golden",                                  "HUNTR/X"),
    (8,  "Stateside",                               "PinkPantheress"),
    (9,  "Folded",                                  "Kehlani"),
    (10, "Swim",                                    "BTS"),
    (11, "The Fate Of Ophelia",                     "Taylor Swift"),
    (12, "Risk It All",                             "Bruno Mars"),
    (13, "Yukon",                                   "Justin Bieber"),
    (14, "Where Is My Husband!",                    "RAYE"),
    (15, "Dracula",                                 "Tame Impala"),
    (16, "Sleepless In A Hotel Room",               "Luke Combs"),
    (17, "Opalite",                                 "Taylor Swift"),
    (18, "Daisies",                                 "Justin Bieber"),
    (19, "Babydoll",                                "Dominic Fike"),
    (20, "Bottom Of Your Boots",                    "Ella Langley"),
    (21, "Loving Life Again",                       "Ella Langley"),
    (22, "Iloveitiloveitiloveit",                   "Bella Kay"),
    (23, "E85",                                     "Don Toliver"),
    (24, "Be By You",                               "Luke Combs"),
    (25, "Homewrecker",                             "sombr"),
    (26, "Beauty And A Beat",                       "Justin Bieber"),
    (27, "Dandelion",                               "Ella Langley"),
    (28, "Pinky Up",                                "KATSEYE"),
    (29, "The Fall",                                "Cody Johnson"),
    (30, "American Girls",                          "Harry Styles"),
    (31, "Body",                                    "Don Toliver"),
    (32, "Pop Dat Thang",                           "DaBaby"),
    (33, "Change My Mind",                          "Riley Green"),
    (34, "White Keys",                              "Dominic Fike"),
    (35, "Freakin' Out",                            "Dexter And The Moonrocks"),
    (36, "Die On This Hill",                        "Sienna Spiro"),
    (37, "Let 'Em Know",                            "T.I."),
    (38, "I Ain't Coming Back",                     "Morgan Wallen"),
    (39, "Fever Dream",                             "Alex Warren"),
    (40, "Earrings",                                "Malcolm Todd"),
    (41, "When Did You Get Hot?",                   "Sabrina Carpenter"),
    (42, "Lush Life",                               "Zara Larsson"),
    (43, "Motion Party",                            "BossMan Dlow"),
    (44, "Midnight Sun",                            "Zara Larsson"),
    (45, "The Great Divide",                        "Noah Kahan"),
    (46, "Days Like These",                         "Luke Combs"),
    (47, "Baby",                                    "Justin Bieber"),
    (48, "What You Saying",                         "Lil Uzi Vert"),
    (49, "Brunette",                                "Tucker Wetmore"),
    (50, "Runway",                                  "Lady Gaga"),
    (51, "Elizabeth Taylor",                        "Taylor Swift"),
    (52, "Raindance",                               "Dave"),
    (53, "Broken",                                  "Ella Langley"),
    (54, "We Know Us",                              "Ella Langley"),
    (55, "You & Me Time",                           "Ella Langley"),
    (56, "What He'll Never Have",                   "Dylan Scott"),
    (57, "Obvious",                                 "Chris Brown"),
    (58, "McArthur",                                "HARDY"),
    (59, "FDO",                                     "Pooh Shiesty"),
    (60, "Boston",                                  "Stella Lefty"),
    (61, "In My Room",                              "Julia Wolf"),
    (62, "Low Lights",                              "Ella Langley"),
    (63, "Speaking Terms",                          "Ella Langley"),
    (64, "Father",                                  "Ye"),
    (65, "What You Need",                           "Tems"),
    (66, "Turn This Truck Around",                  "Jordan Davis"),
    (67, "Beautiful Things",                        "Megan Moroney"),
    (68, "Don't We",                                "Morgan Wallen"),
    (69, "Body To Body",                            "BTS"),
    (70, "One Of Them",                             "DJ Khaled"),
    (71, "Butterfly Season",                        "Ella Langley"),
    (72, "Porch Light",                             "Noah Kahan"),
    (73, "Rein Me In",                              "Sam Fender"),
    (74, "Dry Spell",                               "Kacey Musgraves"),
    (75, "Somethin' Simple",                        "Ella Langley"),
    (76, "Last Call For Us",                        "Ella Langley"),
    (77, "Go Away",                                 "Weezer"),
    (78, "Rethink Some Things",                     "Luke Combs"),
    (79, "Chanel",                                  "Tyla"),
    (80, "I Gotta Quit",                            "Ella Langley"),
    (81, "Mrs. Trendsetter",                        "Lil Baby"),
    (82, "Mr. Know It All",                         "Teddy Swims"),
    (83, "It Wasn't God Who Made Honky Tonk Angels","Ella Langley"),
    (84, "Ain't A Bad Life",                        "Thomas Rhett"),
    (85, "Hate How You Look",                       "Josh Ross"),
    (86, "All The Love",                            "Ye"),
    (87, "Dano",                                    "Peso Pluma"),
    (88, "2.0",                                     "BTS"),
    (89, "Ever Since U Left Me",                    "Max B"),
    (90, "Hooligan",                                "BTS"),
    (91, "The Visitor",                             "Sienna Spiro"),
    (92, "Rocky Mountain Low",                      "Corey Kent"),
    (93, "Jane!",                                   "The Long Faces"),
    (94, "Aperture",                                "Harry Styles"),
    (95, "Who Knows",                               "Daniel Caesar"),
    (96, "Don't Tell On Me",                        "Jason Aldean"),
    (97, "Self Aware",                              "Temper City"),
    (98, "Zoo",                                     "Shakira"),
    (99, "Plastic Cigarette",                       "Zach Bryan"),
    (100,"Woman",                                   "Kane Brown"),
]

# ── Artist → catalog genre fallback (used when iTunes fails) ─────────────────
ARTIST_GENRE = {
    "Ella Langley":         "country",
    "Olivia Dean":          "pop",
    "Bruno Mars":           "pop",
    "Alex Warren":          "pop",
    "PinkPantheress":       "pop",
    "Kehlani":              "r&b",
    "BTS":                  "pop",
    "Taylor Swift":         "pop",
    "Justin Bieber":        "pop",
    "RAYE":                 "pop",
    "Tame Impala":          "indie pop",
    "Luke Combs":           "country",
    "Dominic Fike":         "indie pop",
    "Bella Kay":            "pop",
    "Don Toliver":          "hip-hop",
    "sombr":                "indie pop",
    "KATSEYE":              "pop",
    "Cody Johnson":         "country",
    "Harry Styles":         "pop",
    "DaBaby":               "hip-hop",
    "Riley Green":          "country",
    "Dexter And The Moonrocks": "pop",
    "Sienna Spiro":         "indie pop",
    "T.I.":                 "hip-hop",
    "Morgan Wallen":        "country",
    "Malcolm Todd":         "country",
    "Sabrina Carpenter":    "pop",
    "Zara Larsson":         "pop",
    "BossMan Dlow":         "hip-hop",
    "Noah Kahan":           "folk",
    "Lady Gaga":            "pop",
    "Dave":                 "hip-hop",
    "Dylan Scott":          "country",
    "Chris Brown":          "r&b",
    "HARDY":                "country",
    "Pooh Shiesty":         "hip-hop",
    "Stella Lefty":         "country",
    "Julia Wolf":           "pop",
    "Ye":                   "hip-hop",
    "Tems":                 "r&b",
    "Jordan Davis":         "country",
    "Megan Moroney":        "country",
    "DJ Khaled":            "hip-hop",
    "Sam Fender":           "indie pop",
    "Kacey Musgraves":      "country",
    "Weezer":               "rock",
    "Tyla":                 "r&b",
    "Lil Baby":             "hip-hop",
    "Teddy Swims":          "r&b",
    "Thomas Rhett":         "country",
    "Josh Ross":            "country",
    "Peso Pluma":           "pop",
    "Max B":                "hip-hop",
    "Corey Kent":           "country",
    "The Long Faces":       "folk",
    "Daniel Caesar":        "r&b",
    "Jason Aldean":         "country",
    "Temper City":          "indie pop",
    "Shakira":              "pop",
    "Zach Bryan":           "country",
    "Kane Brown":           "country",
    "HUNTR/X":              "pop",
}

# ── iTunes genre → catalog genre ─────────────────────────────────────────────
ITUNES_GENRE_MAP = {
    "Pop": "pop", "Rock": "rock", "Alternative": "indie pop",
    "Hip-Hop/Rap": "hip-hop", "Rap": "hip-hop", "Country": "country",
    "R&B/Soul": "r&b", "Soul": "r&b", "Electronic": "edm",
    "Dance": "edm", "Jazz": "jazz", "Classical": "classical",
    "Metal": "metal", "Folk": "folk", "Reggae": "reggae",
    "Ambient": "ambient", "Soundtrack": "pop", "Singer/Songwriter": "folk",
    "Indie Pop": "indie pop", "Blues": "rock", "Latin": "pop",
    "World": "reggae", "K-Pop": "pop", "Punk": "rock",
    "Trap": "hip-hop", "Afrobeats": "r&b",
}

# ── Genre defaults for audio features ────────────────────────────────────────
GENRE_DEFAULTS = {
    "pop":      {"energy":0.75,"tempo_bpm":115,"valence":0.75,"danceability":0.75,"acousticness":0.20,"mood":"happy"},
    "rock":     {"energy":0.85,"tempo_bpm":140,"valence":0.50,"danceability":0.60,"acousticness":0.10,"mood":"intense"},
    "metal":    {"energy":0.95,"tempo_bpm":160,"valence":0.30,"danceability":0.50,"acousticness":0.05,"mood":"angry"},
    "lofi":     {"energy":0.40,"tempo_bpm":78, "valence":0.58,"danceability":0.60,"acousticness":0.75,"mood":"chill"},
    "jazz":     {"energy":0.40,"tempo_bpm":95, "valence":0.65,"danceability":0.55,"acousticness":0.85,"mood":"relaxed"},
    "classical":{"energy":0.25,"tempo_bpm":65, "valence":0.65,"danceability":0.30,"acousticness":0.95,"mood":"peaceful"},
    "hip-hop":  {"energy":0.75,"tempo_bpm":95, "valence":0.70,"danceability":0.85,"acousticness":0.15,"mood":"confident"},
    "r&b":      {"energy":0.60,"tempo_bpm":85, "valence":0.75,"danceability":0.70,"acousticness":0.40,"mood":"romantic"},
    "edm":      {"energy":0.92,"tempo_bpm":138,"valence":0.85,"danceability":0.92,"acousticness":0.05,"mood":"euphoric"},
    "ambient":  {"energy":0.30,"tempo_bpm":65, "valence":0.60,"danceability":0.40,"acousticness":0.90,"mood":"chill"},
    "country":  {"energy":0.55,"tempo_bpm":96, "valence":0.65,"danceability":0.60,"acousticness":0.70,"mood":"nostalgic"},
    "folk":     {"energy":0.35,"tempo_bpm":70, "valence":0.45,"danceability":0.45,"acousticness":0.88,"mood":"melancholic"},
    "reggae":   {"energy":0.60,"tempo_bpm":88, "valence":0.85,"danceability":0.78,"acousticness":0.55,"mood":"uplifting"},
    "synthwave":{"energy":0.72,"tempo_bpm":108,"valence":0.50,"danceability":0.72,"acousticness":0.22,"mood":"moody"},
    "indie pop":{"energy":0.65,"tempo_bpm":118,"valence":0.62,"danceability":0.68,"acousticness":0.35,"mood":"moody"},
}


def load_catalog() -> list:
    rows = []
    with open(DATA_PATH, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rows.append(row)
    return rows


def is_duplicate(catalog: list, title: str, artist: str) -> bool:
    t, a = title.lower().strip(), artist.lower().strip()
    return any(r["title"].lower().strip() == t and r["artist"].lower().strip() == a for r in catalog)


def next_id(catalog: list) -> int:
    return max(int(r["id"]) for r in catalog) + 1 if catalog else 1


def itunes_lookup(title: str, artist: str):
    """Return catalog genre string or None if lookup fails."""
    try:
        resp = requests.get(
            "https://itunes.apple.com/search",
            params={"term": f"{title} {artist}", "media": "music", "entity": "song", "limit": 5},
            timeout=8,
        )
        resp.raise_for_status()
        for item in resp.json().get("results", []):
            g = item.get("primaryGenreName", "")
            mapped = ITUNES_GENRE_MAP.get(g)
            if mapped:
                return mapped
    except Exception:
        pass
    return None


def append_row(row: dict):
    with open(DATA_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "id", "title", "artist", "genre", "mood",
            "energy", "tempo_bpm", "valence", "danceability", "acousticness",
        ])
        writer.writerow(row)


def main():
    catalog = load_catalog()
    added = skipped_dup = 0
    itunes_cache: dict[str, str] = {}  # artist → genre, cached per artist

    print(f"Catalog has {len(catalog)} songs before bulk-add.\n")

    for rank, title, artist in HOT_100:
        label = f"[{rank:3d}] {title[:40]:<40} — {artist[:25]}"

        if is_duplicate(catalog, title, artist):
            print(f"{label}  ⚠ ALREADY IN CATALOG")
            skipped_dup += 1
            continue

        # Genre lookup: cache per artist to reduce API calls
        if artist not in itunes_cache:
            genre = itunes_lookup(title, artist)
            if genre is None:
                genre = ARTIST_GENRE.get(artist, "pop")
            itunes_cache[artist] = genre
            time.sleep(0.25)  # polite rate limit
        else:
            genre = itunes_cache[artist]

        d = GENRE_DEFAULTS.get(genre, GENRE_DEFAULTS["pop"])
        new_row = {
            "id":           next_id(catalog),
            "title":        title,
            "artist":       artist,
            "genre":        genre,
            "mood":         d["mood"],
            "energy":       d["energy"],
            "tempo_bpm":    d["tempo_bpm"],
            "valence":      d["valence"],
            "danceability": d["danceability"],
            "acousticness": d["acousticness"],
        }
        append_row(new_row)
        catalog.append({k: str(v) for k, v in new_row.items()})
        print(f"{label}  ✅ ADDED  (id={new_row['id']} genre={genre})")
        added += 1

    print(f"\n{'='*70}")
    print(f"Done!  Added: {added}  |  Duplicates skipped: {skipped_dup}")
    print(f"Catalog now has {len(catalog)} songs.")


if __name__ == "__main__":
    main()
