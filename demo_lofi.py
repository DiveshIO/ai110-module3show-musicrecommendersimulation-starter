import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
from recommender import load_songs, recommend_songs

songs = load_songs(os.path.join(os.path.dirname(__file__), "data", "songs.csv"))
user = {
    "favorite_genre": "lofi",
    "favorite_mood": "chill",
    "target_energy": 0.40,
    "likes_acoustic": True,
}

print("=== Lofi Chill User (loves acoustic) ===\n")
for rank, (song, score, why) in enumerate(recommend_songs(user, songs, k=5), 1):
    print(f"  #{rank}  [{score:.2f}/5.00]  {song['title']} — {song['artist']}")
    print(f"        genre={song['genre']}  mood={song['mood']}  energy={song['energy']}")
    print(f"        why: {why}\n")
