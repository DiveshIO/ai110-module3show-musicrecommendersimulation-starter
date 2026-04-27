#!/usr/bin/env python3
"""
Rebuild the songs catalog:
  1. Remove fake/placeholder songs (no-iTunes artists, fabricated titles).
  2. Keep all verified real songs already in the CSV.
  3. Append ~250 curated real songs (skipping any already present).
  4. Reassign IDs sequentially.

Run:  python scripts/rebuild_catalog.py
"""

import csv, os, sys, time
from pathlib import Path

ROOT      = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "data" / "songs.csv"

# ── Genre defaults (energy, tempo_bpm, valence, danceability, acousticness, mood) ──
GENRE_DEFAULTS = {
    "pop":       {"energy":0.75,"tempo_bpm":115,"valence":0.75,"danceability":0.75,"acousticness":0.20,"mood":"happy"},
    "rock":      {"energy":0.85,"tempo_bpm":140,"valence":0.50,"danceability":0.60,"acousticness":0.10,"mood":"intense"},
    "metal":     {"energy":0.95,"tempo_bpm":160,"valence":0.30,"danceability":0.50,"acousticness":0.05,"mood":"angry"},
    "lofi":      {"energy":0.40,"tempo_bpm":78, "valence":0.58,"danceability":0.60,"acousticness":0.75,"mood":"chill"},
    "jazz":      {"energy":0.40,"tempo_bpm":95, "valence":0.65,"danceability":0.55,"acousticness":0.85,"mood":"relaxed"},
    "classical": {"energy":0.25,"tempo_bpm":65, "valence":0.65,"danceability":0.30,"acousticness":0.95,"mood":"peaceful"},
    "hip-hop":   {"energy":0.75,"tempo_bpm":95, "valence":0.70,"danceability":0.85,"acousticness":0.15,"mood":"confident"},
    "r&b":       {"energy":0.60,"tempo_bpm":85, "valence":0.75,"danceability":0.70,"acousticness":0.40,"mood":"romantic"},
    "edm":       {"energy":0.92,"tempo_bpm":138,"valence":0.85,"danceability":0.92,"acousticness":0.05,"mood":"euphoric"},
    "ambient":   {"energy":0.30,"tempo_bpm":65, "valence":0.60,"danceability":0.40,"acousticness":0.90,"mood":"chill"},
    "country":   {"energy":0.55,"tempo_bpm":96, "valence":0.65,"danceability":0.60,"acousticness":0.70,"mood":"nostalgic"},
    "folk":      {"energy":0.35,"tempo_bpm":70, "valence":0.45,"danceability":0.45,"acousticness":0.88,"mood":"melancholic"},
    "reggae":    {"energy":0.60,"tempo_bpm":88, "valence":0.85,"danceability":0.78,"acousticness":0.55,"mood":"uplifting"},
    "synthwave": {"energy":0.72,"tempo_bpm":108,"valence":0.50,"danceability":0.72,"acousticness":0.22,"mood":"moody"},
    "indie pop": {"energy":0.65,"tempo_bpm":118,"valence":0.62,"danceability":0.68,"acousticness":0.35,"mood":"moody"},
    "k-pop":     {"energy":0.80,"tempo_bpm":128,"valence":0.82,"danceability":0.80,"acousticness":0.12,"mood":"euphoric"},
    "soul":      {"energy":0.55,"tempo_bpm":88, "valence":0.72,"danceability":0.68,"acousticness":0.50,"mood":"romantic"},
    "blues":     {"energy":0.45,"tempo_bpm":78, "valence":0.40,"danceability":0.55,"acousticness":0.65,"mood":"melancholic"},
    "latin":     {"energy":0.72,"tempo_bpm":105,"valence":0.80,"danceability":0.85,"acousticness":0.30,"mood":"happy"},
    "trap":      {"energy":0.78,"tempo_bpm":140,"valence":0.55,"danceability":0.80,"acousticness":0.08,"mood":"confident"},
    "afrobeats": {"energy":0.72,"tempo_bpm":105,"valence":0.82,"danceability":0.88,"acousticness":0.22,"mood":"uplifting"},
    "alternative":{"energy":0.70,"tempo_bpm":120,"valence":0.45,"danceability":0.58,"acousticness":0.30,"mood":"moody"},
    "punk":      {"energy":0.90,"tempo_bpm":160,"valence":0.40,"danceability":0.65,"acousticness":0.05,"mood":"angry"},
}

# ── Known fake/placeholder artists (definitely remove any song by these) ──────
FAKE_ARTISTS = {
    "neon echo","loroom","voltline","paper lanterns","max pulse",
    "orbit bloom","slow stereo","indigo parade","blacktop kings",
    "clara voss","velvet shore","dusty hollow","thornwall",
    "coral drift","flux state","wren calloway",
    "huntr/x","sienna spiro","stella lefty",
    "dexter and the moonrocks","temper city","the long faces",
}

# ── Known fake song+artist pairs (title mismatch with real discography) ──────
FAKE_SONGS = {
    ("aperture", "harry styles"),       # not a real Harry Styles song
    ("american girls", "harry styles"), # not a real Harry Styles song
}

# ── 250 curated real songs: (title, artist, genre, mood_override_or_None) ─────
# mood=None → use genre default
SONGS_TO_ADD = [
    # ── Pop ──────────────────────────────────────────────────────────────────
    ("Anti-Hero",                   "Taylor Swift",        "pop",       "moody"),
    ("Shake It Off",                "Taylor Swift",        "pop",       "happy"),
    ("Blank Space",                 "Taylor Swift",        "pop",       "moody"),
    ("Cruel Summer",                "Taylor Swift",        "pop",       "energized"),
    ("Love Story",                  "Taylor Swift",        "pop",       "romantic"),
    ("Cardigan",                    "Taylor Swift",        "indie pop", "melancholic"),
    ("August",                      "Taylor Swift",        "indie pop", "nostalgic"),
    ("All Too Well (Ten Minute Version)", "Taylor Swift",  "pop",       "melancholic"),
    ("7 Rings",                     "Ariana Grande",       "pop",       "confident"),
    ("Thank U Next",                "Ariana Grande",       "pop",       "confident"),
    ("No Tears Left to Cry",        "Ariana Grande",       "pop",       "uplifting"),
    ("God is a Woman",              "Ariana Grande",       "pop",       "powerful"),
    ("Problem",                     "Ariana Grande",       "pop",       "happy"),
    ("Into You",                    "Ariana Grande",       "pop",       "romantic"),
    ("Bad Guy",                     "Billie Eilish",       "pop",       "confident"),
    ("Ocean Eyes",                  "Billie Eilish",       "pop",       "melancholic"),
    ("Therefore I Am",              "Billie Eilish",       "pop",       "confident"),
    ("Happier Than Ever",           "Billie Eilish",       "pop",       "moody"),
    ("What Was I Made For?",        "Billie Eilish",       "pop",       "melancholic"),
    ("Lovely",                      "Billie Eilish",       "pop",       "melancholic"),
    ("Circles",                     "Post Malone",         "pop",       "melancholic"),
    ("Sunflower",                   "Post Malone",         "pop",       "happy"),
    ("Rockstar",                    "Post Malone",         "hip-hop",   "confident"),
    ("Better Now",                  "Post Malone",         "pop",       "melancholic"),
    ("White Iverson",               "Post Malone",         "hip-hop",   "confident"),
    ("Bad Romance",                 "Lady Gaga",           "pop",       "intense"),
    ("Poker Face",                  "Lady Gaga",           "pop",       "confident"),
    ("Just Dance",                  "Lady Gaga",           "edm",       "euphoric"),
    ("Telephone",                   "Lady Gaga",           "pop",       "energized"),
    ("Shallow",                     "Lady Gaga",           "pop",       "powerful"),
    ("Roar",                        "Katy Perry",          "pop",       "powerful"),
    ("Firework",                    "Katy Perry",          "pop",       "uplifting"),
    ("Teenage Dream",               "Katy Perry",          "pop",       "happy"),
    ("Dark Horse",                  "Katy Perry",          "pop",       "moody"),
    ("Flowers",                     "Miley Cyrus",         "pop",       "uplifting"),
    ("Midnight Sky",                "Miley Cyrus",         "pop",       "moody"),
    ("Don't Start Now",             "Dua Lipa",            "pop",       "confident"),
    ("Physical",                    "Dua Lipa",            "pop",       "energized"),
    ("New Rules",                   "Dua Lipa",            "pop",       "confident"),
    ("Save Your Tears",             "The Weeknd",          "pop",       "melancholic"),
    ("Can't Feel My Face",          "The Weeknd",          "pop",       "happy"),
    ("Starboy",                     "The Weeknd",          "synthwave", "confident"),
    ("Earned It",                   "The Weeknd",          "r&b",       "romantic"),
    ("As It Was",                   "Harry Styles",        "pop",       "melancholic"),
    ("Adore You",                   "Harry Styles",        "pop",       "romantic"),
    ("Late Night Talking",          "Harry Styles",        "pop",       "happy"),
    ("Golden",                      "Harry Styles",        "pop",       "happy"),
    ("drivers license",             "Olivia Rodrigo",      "pop",       "melancholic"),
    ("good 4 u",                    "Olivia Rodrigo",      "pop",       "energized"),
    ("brutal",                      "Olivia Rodrigo",      "pop",       "angry"),
    ("vampire",                     "Olivia Rodrigo",      "pop",       "moody"),
    ("traitor",                     "Olivia Rodrigo",      "pop",       "melancholic"),
    ("deja vu",                     "Olivia Rodrigo",      "pop",       "nostalgic"),
    ("Espresso",                    "Sabrina Carpenter",   "pop",       "confident"),
    ("Please Please Please",        "Sabrina Carpenter",   "pop",       "hopeful"),
    ("Feather",                     "Sabrina Carpenter",   "pop",       "happy"),
    ("Good Luck Babe",              "Chappell Roan",       "pop",       "moody"),
    ("Pink Pony Club",              "Chappell Roan",       "pop",       "euphoric"),
    ("Can't Stop the Feeling!",     "Justin Timberlake",   "pop",       "happy"),
    ("Cry Me a River",              "Justin Timberlake",   "r&b",       "moody"),
    ("SexyBack",                    "Justin Timberlake",   "pop",       "confident"),
    ("Mirrors",                     "Justin Timberlake",   "pop",       "romantic"),
    ("Attention",                   "Charlie Puth",        "pop",       "confident"),
    ("We Don't Talk Anymore",       "Charlie Puth",        "pop",       "melancholic"),
    ("Perfect",                     "Ed Sheeran",          "pop",       "romantic"),
    ("Thinking Out Loud",           "Ed Sheeran",          "pop",       "romantic"),
    ("Bad Habits",                  "Ed Sheeran",          "pop",       "happy"),
    ("Shivers",                     "Ed Sheeran",          "pop",       "happy"),
    ("Hello",                       "Adele",               "pop",       "melancholic"),
    ("Someone Like You",            "Adele",               "pop",       "melancholic"),
    ("Easy On Me",                  "Adele",               "pop",       "melancholic"),
    ("Skyfall",                     "Adele",               "pop",       "powerful"),
    ("Stay With Me",                "Sam Smith",           "pop",       "melancholic"),
    ("Writing's on the Wall",       "Sam Smith",           "pop",       "melancholic"),
    ("Take Me to Church",           "Hozier",              "indie pop", "moody"),
    ("Work Song",                   "Hozier",              "indie pop", "sentimental"),
    ("Royals",                      "Lorde",               "pop",       "confident"),
    ("Green Light",                 "Lorde",               "pop",       "happy"),
    ("Stitches",                    "Shawn Mendes",        "pop",       "melancholic"),
    ("Treat You Better",            "Shawn Mendes",        "pop",       "hopeful"),
    ("Havana",                      "Camila Cabello",      "latin",     "happy"),
    ("Happy",                       "Pharrell Williams",   "pop",       "happy"),
    ("Uptown Funk",                 "Mark Ronson",         "pop",       "groovy"),
    ("Just the Way You Are",        "Bruno Mars",          "pop",       "romantic"),
    ("Grenade",                     "Bruno Mars",          "pop",       "melancholic"),
    ("24K Magic",                   "Bruno Mars",          "pop",       "happy"),
    ("Talking to the Moon",         "Bruno Mars",          "pop",       "melancholic"),
    # ── Hip-Hop ──────────────────────────────────────────────────────────────
    ("HUMBLE.",                     "Kendrick Lamar",      "hip-hop",   "confident"),
    ("Not Like Us",                 "Kendrick Lamar",      "hip-hop",   "angry"),
    ("DNA.",                        "Kendrick Lamar",      "hip-hop",   "confident"),
    ("Alright",                     "Kendrick Lamar",      "hip-hop",   "hopeful"),
    ("Swimming Pools (Drank)",      "Kendrick Lamar",      "hip-hop",   "moody"),
    ("Money Trees",                 "Kendrick Lamar",      "hip-hop",   "melancholic"),
    ("God's Plan",                  "Drake",               "hip-hop",   "confident"),
    ("In My Feelings",              "Drake",               "hip-hop",   "groovy"),
    ("One Dance",                   "Drake",               "afrobeats", "happy"),
    ("Started From the Bottom",     "Drake",               "hip-hop",   "confident"),
    ("Nice For What",               "Drake",               "hip-hop",   "confident"),
    ("SICKO MODE",                  "Travis Scott",        "hip-hop",   "intense"),
    ("Goosebumps",                  "Travis Scott",        "hip-hop",   "moody"),
    ("Antidote",                    "Travis Scott",        "hip-hop",   "energized"),
    ("HIGHEST IN THE ROOM",         "Travis Scott",        "hip-hop",   "dreamy"),
    ("Butterfly Effect",            "Travis Scott",        "hip-hop",   "moody"),
    ("No Role Modelz",              "J. Cole",             "hip-hop",   "confident"),
    ("MIDDLE CHILD",                "J. Cole",             "hip-hop",   "confident"),
    ("Power Trip",                  "J. Cole",             "hip-hop",   "romantic"),
    ("WAP",                         "Cardi B",             "hip-hop",   "confident"),
    ("Bodak Yellow",                "Cardi B",             "hip-hop",   "confident"),
    ("Savage",                      "Megan Thee Stallion", "hip-hop",   "confident"),
    ("Body",                        "Megan Thee Stallion", "hip-hop",   "confident"),
    ("Super Bass",                  "Nicki Minaj",         "pop",       "confident"),
    ("Starships",                   "Nicki Minaj",         "pop",       "euphoric"),
    ("Anaconda",                    "Nicki Minaj",         "hip-hop",   "confident"),
    ("Mask Off",                    "Future",              "trap",      "moody"),
    ("Life Is Good",                "Future",              "hip-hop",   "confident"),
    ("Say So",                      "Doja Cat",            "pop",       "happy"),
    ("Kiss Me More",                "Doja Cat",            "pop",       "romantic"),
    ("Streets",                     "Doja Cat",            "r&b",       "romantic"),
    ("Need to Know",                "Doja Cat",            "pop",       "romantic"),
    ("Drip Too Hard",               "Lil Baby",            "hip-hop",   "confident"),
    ("EARFQUAKE",                   "Tyler the Creator",   "r&b",       "romantic"),
    ("See You Again",               "Tyler the Creator",   "r&b",       "melancholic"),
    ("What's Poppin",               "Jack Harlow",         "hip-hop",   "confident"),
    ("The Box",                     "Roddy Ricch",         "hip-hop",   "confident"),
    ("What You Know Bout Love",     "Pop Smoke",           "hip-hop",   "moody"),
    ("Lucid Dreams",                "Juice WRLD",          "pop",       "melancholic"),
    ("Legends",                     "Juice WRLD",          "pop",       "melancholic"),
    ("Bank Account",                "21 Savage",           "hip-hop",   "confident"),
    ("Pop Out",                     "Polo G",              "hip-hop",   "melancholic"),
    # ── R&B ──────────────────────────────────────────────────────────────────
    ("Crazy in Love",               "Beyonce",             "r&b",       "confident"),
    ("Halo",                        "Beyonce",             "pop",       "romantic"),
    ("CUFF IT",                     "Beyonce",             "r&b",       "groovy"),
    ("BREAK MY SOUL",               "Beyonce",             "edm",       "uplifting"),
    ("Love On Top",                 "Beyonce",             "r&b",       "happy"),
    ("Drunk in Love",               "Beyonce",             "r&b",       "romantic"),
    ("Umbrella",                    "Rihanna",             "pop",       "confident"),
    ("We Found Love",               "Rihanna",             "edm",       "euphoric"),
    ("Diamonds",                    "Rihanna",             "pop",       "hopeful"),
    ("Stay",                        "Rihanna",             "pop",       "melancholic"),
    ("Thinking Bout You",           "Frank Ocean",         "r&b",       "romantic"),
    ("Pink + White",                "Frank Ocean",         "r&b",       "peaceful"),
    ("Nights",                      "Frank Ocean",         "r&b",       "melancholic"),
    ("Kill Bill",                   "SZA",                 "r&b",       "moody"),
    ("Good Days",                   "SZA",                 "r&b",       "dreamy"),
    ("Nobody Gets Me",              "SZA",                 "r&b",       "melancholic"),
    ("Snooze",                      "SZA",                 "r&b",       "dreamy"),
    ("Shirt",                       "SZA",                 "r&b",       "confident"),
    ("Best Part",                   "H.E.R.",              "r&b",       "romantic"),
    ("Focus",                       "H.E.R.",              "r&b",       "confident"),
    ("All of Me",                   "John Legend",         "pop",       "romantic"),
    ("Ordinary People",             "John Legend",         "r&b",       "romantic"),
    ("Yeah!",                       "Usher",               "r&b",       "happy"),
    ("Confessions Part II",         "Usher",               "r&b",       "melancholic"),
    ("No One",                      "Alicia Keys",         "pop",       "hopeful"),
    ("Fallin'",                     "Alicia Keys",         "r&b",       "romantic"),
    ("Girl on Fire",                "Alicia Keys",         "pop",       "powerful"),
    ("Rehab",                       "Amy Winehouse",       "soul",      "melancholic"),
    ("Back to Black",               "Amy Winehouse",       "soul",      "melancholic"),
    ("Valerie",                     "Amy Winehouse",       "soul",      "uplifting"),
    ("Let's Get It On",             "Marvin Gaye",         "soul",      "romantic"),
    ("What's Going On",             "Marvin Gaye",         "soul",      "melancholic"),
    ("I Will Always Love You",      "Whitney Houston",     "pop",       "romantic"),
    ("Greatest Love of All",        "Whitney Houston",     "pop",       "hopeful"),
    ("Superstition",                "Stevie Wonder",       "soul",      "groovy"),
    ("Isn't She Lovely",            "Stevie Wonder",       "soul",      "happy"),
    ("Sir Duke",                    "Stevie Wonder",       "soul",      "happy"),
    # ── Rock ─────────────────────────────────────────────────────────────────
    ("Stairway to Heaven",          "Led Zeppelin",        "rock",      "powerful"),
    ("Black Dog",                   "Led Zeppelin",        "rock",      "energized"),
    ("Whole Lotta Love",            "Led Zeppelin",        "rock",      "intense"),
    ("Kashmir",                     "Led Zeppelin",        "rock",      "powerful"),
    ("Hey Jude",                    "The Beatles",         "rock",      "uplifting"),
    ("Let It Be",                   "The Beatles",         "rock",      "peaceful"),
    ("Come Together",               "The Beatles",         "rock",      "groovy"),
    ("Yesterday",                   "The Beatles",         "folk",      "melancholic"),
    ("Here Comes the Sun",          "The Beatles",         "folk",      "hopeful"),
    ("Blackbird",                   "The Beatles",         "folk",      "hopeful"),
    ("Thunderstruck",               "AC/DC",               "rock",      "energized"),
    ("Back in Black",               "AC/DC",               "rock",      "intense"),
    ("Highway to Hell",             "AC/DC",               "rock",      "energized"),
    ("Everlong",                    "Foo Fighters",        "rock",      "intense"),
    ("Best of You",                 "Foo Fighters",        "rock",      "powerful"),
    ("Times Like These",            "Foo Fighters",        "rock",      "hopeful"),
    ("Under the Bridge",            "Red Hot Chili Peppers","rock",     "melancholic"),
    ("Californication",             "Red Hot Chili Peppers","rock",     "melancholic"),
    ("Can't Stop",                  "Red Hot Chili Peppers","rock",     "energized"),
    ("Sweet Child O' Mine",         "Guns N' Roses",       "rock",      "happy"),
    ("November Rain",               "Guns N' Roses",       "rock",      "melancholic"),
    ("Welcome to the Jungle",       "Guns N' Roses",       "rock",      "intense"),
    ("Yellow",                      "Coldplay",            "rock",      "romantic"),
    ("Fix You",                     "Coldplay",            "rock",      "hopeful"),
    ("The Scientist",               "Coldplay",            "rock",      "melancholic"),
    ("Viva la Vida",                "Coldplay",            "rock",      "uplifting"),
    ("A Sky Full of Stars",         "Coldplay",            "edm",       "euphoric"),
    ("Do I Wanna Know?",            "Arctic Monkeys",      "rock",      "moody"),
    ("R U Mine?",                   "Arctic Monkeys",      "rock",      "intense"),
    ("505",                         "Arctic Monkeys",      "rock",      "melancholic"),
    ("I Wanna Be Yours",            "Arctic Monkeys",      "indie pop", "romantic"),
    ("Wonderwall",                  "Oasis",               "rock",      "hopeful"),
    ("Champagne Supernova",         "Oasis",               "rock",      "nostalgic"),
    ("Don't Look Back in Anger",    "Oasis",               "rock",      "hopeful"),
    ("Basket Case",                 "Green Day",           "punk",      "energized"),
    ("Boulevard of Broken Dreams",  "Green Day",           "rock",      "melancholic"),
    ("Stressed Out",                "Twenty One Pilots",   "pop",       "melancholic"),
    ("Ride",                        "Twenty One Pilots",   "pop",       "happy"),
    ("Radioactive",                 "Imagine Dragons",     "rock",      "powerful"),
    ("Demons",                      "Imagine Dragons",     "rock",      "melancholic"),
    ("Believer",                    "Imagine Dragons",     "rock",      "powerful"),
    ("Enemy",                       "Imagine Dragons",     "alternative","moody"),
    ("In the End",                  "Linkin Park",         "rock",      "melancholic"),
    ("Numb",                        "Linkin Park",         "rock",      "melancholic"),
    ("Crawling",                    "Linkin Park",         "rock",      "melancholic"),
    ("Supermassive Black Hole",     "Muse",                "rock",      "intense"),
    ("Seven Nation Army",           "The White Stripes",   "rock",      "intense"),
    ("Last Nite",                   "The Strokes",         "indie pop", "confident"),
    ("Reptilia",                    "The Strokes",         "indie pop", "energized"),
    ("Mr. Brightside",              "The Killers",         "rock",      "intense"),
    ("Somebody Told Me",            "The Killers",         "rock",      "energized"),
    ("Use Somebody",                "Kings of Leon",       "rock",      "hopeful"),
    ("Sex on Fire",                 "Kings of Leon",       "rock",      "intense"),
    # ── EDM ──────────────────────────────────────────────────────────────────
    ("Get Lucky",                   "Daft Punk",           "edm",       "groovy"),
    ("Around the World",            "Daft Punk",           "edm",       "euphoric"),
    ("Harder Better Faster Stronger","Daft Punk",          "edm",       "energized"),
    ("Summer",                      "Calvin Harris",       "edm",       "happy"),
    ("Feel So Close",               "Calvin Harris",       "edm",       "uplifting"),
    ("This Is What You Came For",   "Calvin Harris",       "edm",       "euphoric"),
    ("Titanium",                    "David Guetta",        "edm",       "powerful"),
    ("Without You",                 "David Guetta",        "edm",       "melancholic"),
    ("Alone",                       "Marshmello",          "edm",       "melancholic"),
    ("Happier",                     "Marshmello",          "pop",       "hopeful"),
    ("Wolves",                      "Marshmello",          "pop",       "intense"),
    ("Closer",                      "The Chainsmokers",    "pop",       "nostalgic"),
    ("Something Just Like This",    "The Chainsmokers",    "pop",       "hopeful"),
    ("Don't Let Me Down",           "The Chainsmokers",    "edm",       "intense"),
    ("Firestone",                   "Kygo",                "edm",       "peaceful"),
    ("Stole the Show",              "Kygo",                "edm",       "melancholic"),
    ("Wake Me Up",                  "Avicii",              "edm",       "uplifting"),
    ("The Nights",                  "Avicii",              "edm",       "hopeful"),
    ("Levels",                      "Avicii",              "edm",       "euphoric"),
    ("Bangarang",                   "Skrillex",            "edm",       "energized"),
    ("Lean On",                     "Major Lazer",         "edm",       "uplifting"),
    ("Clarity",                     "Zedd",                "edm",       "uplifting"),
    ("Don't You Worry Child",       "Swedish House Mafia", "edm",       "hopeful"),
    ("Animals",                     "Martin Garrix",       "edm",       "intense"),
    ("Rather Be",                   "Clean Bandit",        "pop",       "happy"),
    ("Rockabye",                    "Clean Bandit",        "pop",       "melancholic"),
    ("Pompeii",                     "Bastille",            "pop",       "hopeful"),
    # ── Country ──────────────────────────────────────────────────────────────
    ("Last Night",                  "Morgan Wallen",       "country",   "nostalgic"),
    ("Sand in My Boots",            "Morgan Wallen",       "country",   "nostalgic"),
    ("More Than My Hometown",       "Morgan Wallen",       "country",   "nostalgic"),
    ("Wasted on You",               "Morgan Wallen",       "country",   "melancholic"),
    ("When It Rains It Pours",      "Luke Combs",          "country",   "happy"),
    ("Beautiful Crazy",             "Luke Combs",          "country",   "romantic"),
    ("Forever After All",           "Luke Combs",          "country",   "romantic"),
    ("Tennessee Whiskey",           "Chris Stapleton",     "country",   "romantic"),
    ("Fire Away",                   "Chris Stapleton",     "country",   "melancholic"),
    ("Broken Halos",                "Chris Stapleton",     "country",   "melancholic"),
    ("Die a Happy Man",             "Thomas Rhett",        "country",   "romantic"),
    ("T-Shirt",                     "Thomas Rhett",        "country",   "happy"),
    ("Heaven",                      "Kane Brown",          "country",   "hopeful"),
    ("Homesick",                    "Kane Brown",          "country",   "nostalgic"),
    ("Rainbow",                     "Kacey Musgraves",     "country",   "hopeful"),
    ("Slow Burn",                   "Kacey Musgraves",     "country",   "peaceful"),
    ("Butterflies",                 "Kacey Musgraves",     "country",   "happy"),
    ("Something in the Orange",     "Zach Bryan",          "country",   "melancholic"),
    ("I Remember Everything",       "Zach Bryan",          "country",   "nostalgic"),
    ("Heading South",               "Zach Bryan",          "folk",      "nostalgic"),
    ("Heart Like a Truck",          "Lainey Wilson",       "country",   "uplifting"),
    ("Watermelon Moonshine",        "Lainey Wilson",       "country",   "nostalgic"),
    ("Whitehouse Road",             "Tyler Childers",      "country",   "nostalgic"),
    ("Then",                        "Brad Paisley",        "country",   "romantic"),
    ("Jolene",                      "Dolly Parton",        "country",   "melancholic"),
    ("Ring of Fire",                "Johnny Cash",         "country",   "happy"),
    ("Folsom Prison Blues",         "Johnny Cash",         "country",   "melancholic"),
    # ── Jazz / Soul / Classic ────────────────────────────────────────────────
    ("So What",                     "Miles Davis",         "jazz",      "chill"),
    ("Kind of Blue",                "Miles Davis",         "jazz",      "chill"),
    ("My Favorite Things",          "John Coltrane",       "jazz",      "focused"),
    ("A Love Supreme",              "John Coltrane",       "jazz",      "peaceful"),
    ("Watermelon Man",              "Herbie Hancock",      "jazz",      "groovy"),
    ("Cantaloupe Island",           "Herbie Hancock",      "jazz",      "groovy"),
    ("Don't Know Why",              "Norah Jones",         "jazz",      "melancholic"),
    ("Come Away with Me",           "Norah Jones",         "jazz",      "peaceful"),
    ("Feeling Good",                "Nina Simone",         "jazz",      "uplifting"),
    ("I Put a Spell on You",        "Nina Simone",         "jazz",      "moody"),
    ("What a Wonderful World",      "Louis Armstrong",     "jazz",      "happy"),
    ("Summertime",                  "Ella Fitzgerald",     "jazz",      "melancholic"),
    ("Fly Me to the Moon",          "Frank Sinatra",       "jazz",      "romantic"),
    ("The Way You Look Tonight",    "Frank Sinatra",       "jazz",      "romantic"),
    ("A Change Is Gonna Come",      "Sam Cooke",           "soul",      "hopeful"),
    ("(Sittin' On) The Dock of the Bay","Otis Redding",    "soul",      "melancholic"),
    ("Stand by Me",                 "Ben E. King",         "soul",      "hopeful"),
    # ── K-pop ────────────────────────────────────────────────────────────────
    ("Dynamite",                    "BTS",                 "k-pop",     "happy"),
    ("Butter",                      "BTS",                 "k-pop",     "groovy"),
    ("Boy With Luv",                "BTS",                 "k-pop",     "happy"),
    ("How You Like That",           "BLACKPINK",           "k-pop",     "confident"),
    ("Pink Venom",                  "BLACKPINK",           "k-pop",     "confident"),
    ("Lovesick Girls",              "BLACKPINK",           "k-pop",     "melancholic"),
    ("Hype Boy",                    "NewJeans",            "k-pop",     "euphoric"),
    ("OMG",                         "NewJeans",            "k-pop",     "happy"),
    ("Attention",                   "NewJeans",            "k-pop",     "chill"),
    ("Fancy",                       "TWICE",               "k-pop",     "confident"),
    ("Feel Special",                "TWICE",               "k-pop",     "uplifting"),
    # ── Latin ────────────────────────────────────────────────────────────────
    ("Tití Me Preguntó",            "Bad Bunny",           "latin",     "happy"),
    ("Efecto",                      "Bad Bunny",           "latin",     "romantic"),
    ("Me Porto Bonito",             "Bad Bunny",           "latin",     "happy"),
    ("Dakiti",                      "Bad Bunny",           "latin",     "confident"),
    ("Hips Don't Lie",              "Shakira",             "latin",     "happy"),
    ("Waka Waka",                   "Shakira",             "pop",       "uplifting"),
    ("Mi Gente",                    "J Balvin",            "latin",     "happy"),
    ("TUSA",                        "KAROL G",             "latin",     "confident"),
    ("Bichota",                     "KAROL G",             "latin",     "confident"),
    # ── Indie / Alternative ──────────────────────────────────────────────────
    ("The Less I Know the Better",  "Tame Impala",         "indie pop", "dreamy"),
    ("Borderline",                  "Tame Impala",         "indie pop", "dreamy"),
    ("Eventually",                  "Tame Impala",         "indie pop", "melancholic"),
    ("Chamber of Reflection",       "Mac DeMarco",         "indie pop", "melancholic"),
    ("Ode to Viceroy",              "Mac DeMarco",         "indie pop", "chill"),
    ("Loving is Easy",              "Rex Orange County",   "indie pop", "happy"),
    ("Sunflower",                   "Rex Orange County",   "indie pop", "happy"),
    ("Coffee",                      "beabadoobee",         "indie pop", "chill"),
    ("Death Bed",                   "Powfu",               "lofi",      "melancholic"),
    ("Pretty Girl",                 "Clairo",              "indie pop", "chill"),
    ("Sofia",                       "Clairo",              "indie pop", "melancholic"),
    ("Supalonely",                  "BENEE",               "indie pop", "moody"),
    ("Motion Sickness",             "Phoebe Bridgers",     "indie pop", "melancholic"),
    ("Garden Song",                 "Phoebe Bridgers",     "folk",      "peaceful"),
    ("Skinny Love",                 "Bon Iver",            "folk",      "melancholic"),
    ("Holocene",                    "Bon Iver",            "folk",      "peaceful"),
    ("White Winter Hymnal",         "Fleet Foxes",         "folk",      "peaceful"),
    ("Helplessness Blues",          "Fleet Foxes",         "folk",      "melancholic"),
    ("Bloodbuzz Ohio",              "The National",        "indie pop", "melancholic"),
    ("Slow Show",                   "The National",        "indie pop", "melancholic"),
    ("Electric Feel",               "MGMT",                "indie pop", "euphoric"),
    ("Time to Pretend",             "MGMT",                "indie pop", "dreamy"),
    ("Little Talks",                "Of Monsters and Men", "indie pop", "uplifting"),
    ("King of Anything",            "Sara Bareilles",      "pop",       "confident"),
    # ── Lofi / Ambient ───────────────────────────────────────────────────────
    ("Feather",                     "Nujabes",             "lofi",      "chill"),
    ("Aruarian Dance",              "Nujabes",             "lofi",      "chill"),
    ("Luv(sic) Part 3",             "Nujabes",             "lofi",      "chill"),
    ("Slow Dancing in the Dark",    "Joji",                "r&b",       "melancholic"),
    ("Glimpse of Us",               "Joji",                "pop",       "melancholic"),
    ("Run",                         "Joji",                "pop",       "melancholic"),
    ("Goodie Bag",                  "Still Woozy",         "indie pop", "dreamy"),
    ("Can I Call You Tonight?",     "Dayglow",             "indie pop", "dreamy"),
    ("Retrograde",                  "James Blake",         "ambient",   "melancholic"),
    ("Limit to Your Love",          "James Blake",         "ambient",   "melancholic"),
    ("Never Catch Me",              "Flying Lotus",        "lofi",      "dreamy"),
    ("On & On",                     "Erykah Badu",         "r&b",       "chill"),
    ("Appletree",                   "Erykah Badu",         "r&b",       "chill"),
    ("Otherside",                   "Red Hot Chili Peppers","rock",     "melancholic"),
    # ── Classics ─────────────────────────────────────────────────────────────
    ("Lose Yourself",               "Eminem",              "hip-hop",   "intense"),
    ("Without Me",                  "Eminem",              "hip-hop",   "confident"),
    ("The Real Slim Shady",         "Eminem",              "hip-hop",   "confident"),
    ("Still D.R.E.",                "Dr. Dre",             "hip-hop",   "confident"),
    ("Nuthin' But a G Thang",       "Dr. Dre",             "hip-hop",   "groovy"),
    ("California Love",             "2Pac",                "hip-hop",   "confident"),
    ("Changes",                     "2Pac",                "hip-hop",   "melancholic"),
    ("Juicy",                       "The Notorious B.I.G.","hip-hop",   "confident"),
    ("Hypnotize",                   "The Notorious B.I.G.","hip-hop",   "confident"),
    ("99 Problems",                 "Jay-Z",               "hip-hop",   "intense"),
    ("Empire State of Mind",        "Jay-Z",               "pop",       "uplifting"),
    ("Gold Digger",                 "Kanye West",          "hip-hop",   "confident"),
    ("Stronger",                    "Kanye West",          "hip-hop",   "confident"),
    ("Runaway",                     "Kanye West",          "hip-hop",   "melancholic"),
    ("Purple Rain",                 "Prince",              "r&b",       "powerful"),
    ("When Doves Cry",              "Prince",              "pop",       "melancholic"),
    ("Raspberry Beret",             "Prince",              "pop",       "happy"),
    ("Heroes",                      "David Bowie",         "rock",      "uplifting"),
    ("Space Oddity",                "David Bowie",         "rock",      "dreamy"),
    ("Life on Mars?",               "David Bowie",         "rock",      "dreamy"),
    ("Roxanne",                     "The Police",          "rock",      "moody"),
    ("Every Breath You Take",       "The Police",          "rock",      "melancholic"),
    ("Don't Stop Believin'",        "Journey",             "rock",      "hopeful"),
    ("Sweet Home Alabama",          "Lynyrd Skynyrd",      "rock",      "happy"),
    ("Hotel California",            "Eagles",              "rock",      "moody"),
    ("Take It Easy",                "Eagles",              "rock",      "peaceful"),
    ("Go Your Own Way",             "Fleetwood Mac",       "rock",      "intense"),
    ("The Chain",                   "Fleetwood Mac",       "rock",      "intense"),
    ("Eye of the Tiger",            "Survivor",            "rock",      "energized"),
    ("Don't Stop Me Now",           "Queen",               "rock",      "euphoric"),
    ("We Will Rock You",            "Queen",               "rock",      "energized"),
    ("Somebody to Love",            "Queen",               "rock",      "hopeful"),
    ("Under Pressure",              "Queen",               "rock",      "intense"),
]

FIELDNAMES = ["id","title","artist","genre","mood","energy","tempo_bpm","valence","danceability","acousticness"]


def load_csv():
    with open(DATA_PATH, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def save_csv(rows):
    with open(DATA_PATH, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDNAMES)
        w.writeheader()
        w.writerows(rows)


def normalize(s):
    return s.strip().lower()


def main():
    rows = load_csv()
    print(f"Loaded {len(rows)} songs from catalog.\n")

    # ── Step 1: Remove fake songs ─────────────────────────────────────────────
    kept, removed = [], []
    for r in rows:
        artist_key = normalize(r["artist"])
        title_key  = normalize(r["title"])
        if artist_key in FAKE_ARTISTS:
            removed.append(r)
            print(f"  REMOVED (fake artist): {r['title']} — {r['artist']}")
        elif (title_key, artist_key) in FAKE_SONGS:
            removed.append(r)
            print(f"  REMOVED (fake song):   {r['title']} — {r['artist']}")
        else:
            kept.append(r)

    print(f"\n→ Removed {len(removed)} fake songs, kept {len(kept)} real songs.\n")

    # ── Step 2: Build duplicate index ────────────────────────────────────────
    existing = {(normalize(r["title"]), normalize(r["artist"])) for r in kept}

    # ── Step 3: Add curated real songs ───────────────────────────────────────
    added = 0
    for title, artist, genre, mood in SONGS_TO_ADD:
        key = (normalize(title), normalize(artist))
        if key in existing:
            continue  # already in catalog
        d = GENRE_DEFAULTS.get(genre, GENRE_DEFAULTS["pop"])
        row = {
            "id":           0,           # assigned below
            "title":        title,
            "artist":       artist,
            "genre":        genre,
            "mood":         mood if mood else d["mood"],
            "energy":       d["energy"],
            "tempo_bpm":    d["tempo_bpm"],
            "valence":      d["valence"],
            "danceability": d["danceability"],
            "acousticness": d["acousticness"],
        }
        kept.append(row)
        existing.add(key)
        added += 1

    print(f"→ Added {added} new curated songs.")

    # ── Step 4: Reassign IDs sequentially ────────────────────────────────────
    for i, r in enumerate(kept, start=1):
        r["id"] = i

    save_csv(kept)
    print(f"\n✅  Catalog rebuilt: {len(kept)} songs saved to {DATA_PATH}")


if __name__ == "__main__":
    main()
