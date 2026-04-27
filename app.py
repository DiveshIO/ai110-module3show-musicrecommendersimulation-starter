"""MusicMind AI Recommender — Streamlit web app."""

from dotenv import load_dotenv
load_dotenv()

import csv
import html as html_lib
import json
import os
import subprocess
import sys

import pandas as pd
import requests
import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
from recommender import load_songs, recommend_songs, score_song
from ai_explainer import ai_explain_recommendations

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="MusicMind · AI Recommender",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT         = os.path.dirname(os.path.abspath(__file__))
DATA_PATH    = os.path.join(ROOT, "data", "songs.csv")
RATINGS_PATH = os.path.join(ROOT, "data", "ratings.json")
FAVS_PATH    = os.path.join(ROOT, "data", "favorites.json")

# ══════════════════════════════════════════════════════════════════════════════
# Theme CSS
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
/* ── Base ── */
[data-testid="stAppViewContainer"] {
    background: #07090f;
}
[data-testid="stSidebar"] {
    background: #0c0e1c;
    border-right: 1px solid rgba(139,92,246,0.2);
}
[data-testid="stSidebar"] *      { color: #d4c9ff !important; }
[data-testid="stSidebar"] label  { color: #a78bfa !important; font-weight:600; }
.block-container { padding-top: 1.2rem; }
* { font-family: 'Segoe UI', system-ui, sans-serif; }

/* ── Hero ── */
.hero {
    background: linear-gradient(135deg,rgba(139,92,246,.18),rgba(6,182,212,.12));
    border: 1px solid rgba(139,92,246,.35); border-radius: 20px;
    padding: 1.5rem 2rem; margin-bottom: 1rem; text-align: center;
}
.hero-title {
    font-size: 2.4rem; font-weight: 900; letter-spacing: -.02em;
    background: linear-gradient(90deg,#a78bfa,#38bdf8,#34d399);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    margin: 0; line-height: 1.1;
}
.hero-sub { color: #64748b; font-size: .95rem; margin-top: .4rem; }

/* ── Section header ── */
.sec-head {
    font-size: .85rem; font-weight: 700; color: #7c3aed; letter-spacing: .1em;
    text-transform: uppercase; margin-bottom: .6rem; padding-bottom: .3rem;
    border-bottom: 1px solid rgba(139,92,246,.2);
}

/* ── Metric row ── */
.mrow  { display: flex; gap: .7rem; margin-bottom: .8rem; }
.mcard {
    flex: 1; background: rgba(255,255,255,.03);
    border: 1px solid rgba(139,92,246,.18); border-radius: 12px;
    padding: .7rem .8rem; text-align: center;
}
.mnum { font-size: 1.6rem; font-weight: 800; color: #a78bfa; line-height:1.1; }
.mlbl { font-size: .65rem; color: #475569; text-transform: uppercase; letter-spacing:.07em; }

/* ── Song card (st.container border=True override) ── */
[data-testid="stVerticalBlockBorderWrapper"] {
    background: rgba(255,255,255,.04) !important;
    border: 1px solid rgba(139,92,246,.28) !important;
    border-radius: 16px !important;
    padding: .8rem 1rem .6rem !important;
    margin-bottom: .6rem !important;
    transition: border-color .2s, box-shadow .2s !important;
}
[data-testid="stVerticalBlockBorderWrapper"]:hover {
    border-color: rgba(167,139,250,.65) !important;
    box-shadow: 0 0 24px rgba(139,92,246,.12) !important;
}

/* ── Pills ── */
.pill {
    display:inline-block; padding:2px 10px; border-radius:99px;
    font-size:.7rem; font-weight:600; margin-right:4px; margin-top:3px;
}
.p-genre  {background:rgba(167,139,250,.18);color:#a78bfa;border:1px solid rgba(167,139,250,.35);}
.p-mood   {background:rgba(52,211,153,.12); color:#34d399;border:1px solid rgba(52,211,153,.28);}
.p-energy {background:rgba(251,191,36,.12); color:#fbbf24;border:1px solid rgba(251,191,36,.28);}
.p-fav    {background:rgba(251,113,133,.15);color:#fb7185;border:1px solid rgba(251,113,133,.3);}
.p-like   {background:rgba(52,211,153,.12); color:#34d399;border:1px solid rgba(52,211,153,.28);}
.p-dis    {background:rgba(248,113,113,.1); color:#f87171;border:1px solid rgba(248,113,113,.28);}

/* ── Art placeholder ── */
.art-box {
    aspect-ratio:1; background:linear-gradient(135deg,#6d28d9,#0891b2);
    border-radius:10px; display:flex; align-items:center; justify-content:center;
    font-size:2rem; width:100%;
}

/* ── Progress bar ── */
.pbar-bg  {height:5px;background:rgba(255,255,255,.07);border-radius:99px;margin:6px 0 4px;}
.pbar-fg  {height:100%;border-radius:99px;}

/* ── CLI terminal ── */
.cli {
    background:#060810; border:1px solid rgba(52,211,153,.25); border-radius:12px;
    padding:1rem; font-family:'Fira Code','Courier New',monospace; font-size:.82rem;
    color:#34d399; white-space:pre-wrap; max-height:500px; overflow-y:auto;
}

/* ── How-it-works ── */
.hw {
    display:flex; gap:.9rem; margin-bottom:.8rem; padding:.75rem .9rem;
    background:rgba(255,255,255,.025); border-radius:10px; border-left:3px solid #7c3aed;
}
.hw-n {font-size:1.3rem;font-weight:800;color:#7c3aed;min-width:1.8rem;}
.hw-t {font-size:.88rem;color:#cbd5e1;}
.hw-t strong {color:#e2e8f0;}

/* ── Empty state ── */
.empty {
    text-align:center; padding:3rem; color:#475569; font-size:1.05rem;
    background:rgba(255,255,255,.02); border-radius:16px;
    border:1px dashed rgba(139,92,246,.2);
}

/* ── Catalog table ── */
[data-testid="stDataFrame"] {border-radius:12px; overflow:hidden;}

/* ── Audio preview player ── */
[data-testid="stAudio"] {margin: 4px 0 2px;}
[data-testid="stAudio"] audio {
    width: 100%; height: 28px;
    border-radius: 6px;
    filter: invert(0.85) hue-rotate(180deg) brightness(0.9);
    opacity: 0.85;
}
[data-testid="stAudio"]:hover audio { opacity: 1; }

/* ── Notification banners ── */
.ok  {background:rgba(52,211,153,.1);border:1px solid rgba(52,211,153,.35);border-radius:10px;padding:.6rem .9rem;color:#34d399;font-size:.88rem;}
.err {background:rgba(248,113,113,.1);border:1px solid rgba(248,113,113,.35);border-radius:10px;padding:.6rem .9rem;color:#f87171;font-size:.88rem;}

/* ── Sidebar stat chips ── */
.stat-row {display:flex;gap:.5rem;flex-wrap:wrap;margin-top:.4rem;}
.stat-chip {
    background:rgba(139,92,246,.15); border:1px solid rgba(139,92,246,.3);
    border-radius:99px; padding:3px 10px; font-size:.75rem; color:#c4b5fd;
}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# Constants
# ══════════════════════════════════════════════════════════════════════════════
MOOD_EMOJI = {
    "happy":"😊","chill":"😌","intense":"🔥","relaxed":"🛋️","moody":"🌙",
    "focused":"🎯","peaceful":"🕊️","confident":"💪","romantic":"❤️",
    "nostalgic":"🌅","angry":"😤","uplifting":"🚀","euphoric":"✨",
    "melancholic":"🌧️","energized":"⚡","dreamy":"💭","hopeful":"🌟",
    "powerful":"💥","groovy":"🕺","sentimental":"🥹",
}
GENRE_EMOJI = {
    "pop":"🎤","lofi":"☕","rock":"🎸","ambient":"🌌","synthwave":"🌆",
    "jazz":"🎷","indie pop":"🌻","hip-hop":"🎧","classical":"🎻","r&b":"💜",
    "country":"🤠","metal":"🤘","reggae":"🌴","edm":"💃","folk":"🪕",
    "k-pop":"💫","soul":"🎼","blues":"🎺","latin":"🪘","trap":"🔊",
    "afrobeats":"🌍","alternative":"🎭","punk":"⚡",
}
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
}
ITUNES_GENRE_MAP = {
    "Pop":"pop","Rock":"rock","Alternative":"indie pop","Hip-Hop/Rap":"hip-hop",
    "Country":"country","R&B/Soul":"r&b","Soul":"soul","Electronic":"edm",
    "Dance":"edm","Jazz":"jazz","Classical":"classical","Metal":"metal",
    "Folk":"folk","Reggae":"reggae","Ambient":"ambient","Soundtrack":"pop",
    "Singer/Songwriter":"folk","Indie Pop":"indie pop","Blues":"blues",
    "Latin":"latin","K-Pop":"k-pop","Rap":"hip-hop","Trap":"trap",
    "Afrobeats":"afrobeats","Punk":"punk","World":"reggae",
}
ALL_GENRES = sorted(GENRE_DEFAULTS.keys())
ALL_MOODS  = sorted(MOOD_EMOJI.keys())

# ══════════════════════════════════════════════════════════════════════════════
# Data helpers
# ══════════════════════════════════════════════════════════════════════════════
@st.cache_data
def get_songs():
    return load_songs(DATA_PATH)

@st.cache_data
def get_catalog_df():
    return pd.read_csv(DATA_PATH)

def reload_catalog():
    get_songs.clear()
    get_catalog_df.clear()

def _load_json(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def _save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def next_song_id(df):
    return int(df["id"].max()) + 1 if not df.empty else 1

def append_song_to_csv(row: dict):
    with open(DATA_PATH, "a", newline="", encoding="utf-8") as f:
        csv.DictWriter(f, fieldnames=[
            "id","title","artist","genre","mood",
            "energy","tempo_bpm","valence","danceability","acousticness",
        ]).writerow(row)

# ── Session state ─────────────────────────────────────────────────────────────
if "ratings"  not in st.session_state:
    st.session_state.ratings  = _load_json(RATINGS_PATH, {})
if "favorites" not in st.session_state:
    st.session_state.favorites = set(str(x) for x in _load_json(FAVS_PATH, []))
if "artwork"   not in st.session_state:
    st.session_state.artwork = {}
if "preview"   not in st.session_state:
    st.session_state.preview = {}

# ── Interaction helpers ───────────────────────────────────────────────────────
def set_rating(sid: str, val: int):
    if val == 0:
        st.session_state.ratings.pop(sid, None)
    else:
        st.session_state.ratings[sid] = val
    _save_json(RATINGS_PATH, st.session_state.ratings)

def toggle_fav(sid: str):
    if sid in st.session_state.favorites:
        st.session_state.favorites.discard(sid)
    else:
        st.session_state.favorites.add(sid)
    _save_json(FAVS_PATH, list(st.session_state.favorites))

def apply_boosts(results, cat_df):
    genre_aff = {}
    for sid, r in st.session_state.ratings.items():
        row = cat_df[cat_df["id"] == int(sid)] if sid.isdigit() else pd.DataFrame()
        if not row.empty:
            g = row.iloc[0]["genre"]
            genre_aff[g] = round(genre_aff.get(g, 0.0) + r * 0.08, 3)
    boosted = []
    for song, score, exp in results:
        sid = str(song["id"])
        adj = max(0.0, round(
            score
            + st.session_state.ratings.get(sid, 0) * 0.75
            + genre_aff.get(song["genre"], 0.0)
            + (0.4 if sid in st.session_state.favorites else 0.0),
            2
        ))
        boosted.append((song, adj, exp))
    return sorted(boosted, key=lambda x: x[1], reverse=True)

# ── iTunes metadata (artwork + preview, one API call, both cached) ────────────
def _fetch_itunes(title: str, artist: str):
    """Fetch art URL and 30s preview URL from iTunes. Caches both in session state."""
    key = f"{title.lower()}|||{artist.lower()}"
    if key not in st.session_state.artwork:
        try:
            r = requests.get(
                "https://itunes.apple.com/search",
                params={"term": f"{title} {artist}", "media": "music", "entity": "song", "limit": 3},
                timeout=4,
            )
            items = r.json().get("results", [])
            first = items[0] if items else {}
            art = first.get("artworkUrl100", "").replace("100x100bb", "500x500bb")
            pre = first.get("previewUrl", "")
        except Exception:
            art, pre = "", ""
        st.session_state.artwork[key] = art
        st.session_state.preview[key] = pre

def get_artwork(title: str, artist: str) -> str:
    _fetch_itunes(title, artist)
    return st.session_state.artwork.get(f"{title.lower()}|||{artist.lower()}", "")

def get_preview(title: str, artist: str) -> str:
    _fetch_itunes(title, artist)
    return st.session_state.preview.get(f"{title.lower()}|||{artist.lower()}", "")

def prefetch(songs_list):
    for s in songs_list:
        _fetch_itunes(s["title"], s["artist"])

# ── iTunes search ─────────────────────────────────────────────────────────────
def itunes_search(query: str, limit=12) -> list:
    try:
        r = requests.get(
            "https://itunes.apple.com/search",
            params={"term": query, "media": "music", "entity": "song", "limit": limit},
            timeout=8,
        )
        r.raise_for_status()
        return [
            {
                "title":   item.get("trackName",""),
                "artist":  item.get("artistName",""),
                "genre":   item.get("primaryGenreName",""),
                "preview": item.get("previewUrl",""),
                "art":     item.get("artworkUrl100","").replace("100x100bb","400x400bb"),
            }
            for item in r.json().get("results",[]) if item.get("trackName")
        ]
    except Exception:
        return []

# ── UI helpers ────────────────────────────────────────────────────────────────
def pct_of(score: float) -> int:
    return min(100, round(score / 5.0 * 100))

def pct_color(p: int) -> str:
    return "#22c55e" if p >= 85 else "#eab308" if p >= 65 else "#f97316" if p >= 45 else "#ef4444"

def score_bar(pct: int, color: str) -> str:
    return (
        f'<div class="pbar-bg">'
        f'<div class="pbar-fg" style="width:{pct}%;background:{color}"></div>'
        f'</div>'
    )

def pills_html(song, is_fav, rating):
    g = GENRE_EMOJI.get(song["genre"],"🎵")
    m = MOOD_EMOJI.get(song["mood"],"🎭")
    out = (
        f'<span class="pill p-genre">{g} {song["genre"].title()}</span>'
        f'<span class="pill p-mood">{m} {song["mood"].title()}</span>'
        f'<span class="pill p-energy">⚡ {song["energy"]}</span>'
    )
    if is_fav:   out += '<span class="pill p-fav">❤️</span>'
    if rating==1: out += '<span class="pill p-like">👍</span>'
    elif rating==-1: out += '<span class="pill p-dis">👎</span>'
    return out

# ══════════════════════════════════════════════════════════════════════════════
# Load data
# ══════════════════════════════════════════════════════════════════════════════
SONGS      = get_songs()
CATALOG_DF = get_catalog_df()
AVAIL_GENRES = sorted(set(CATALOG_DF["genre"].unique().tolist() + ALL_GENRES))
AVAIL_MOODS  = sorted(set(CATALOG_DF["mood"].unique().tolist()  + ALL_MOODS))

# ══════════════════════════════════════════════════════════════════════════════
# Sidebar
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## 🎵 Taste Profile")
    st.markdown("---")

    pref_genre = st.selectbox(
        "Favorite Genre", AVAIL_GENRES,
        index=AVAIL_GENRES.index("pop") if "pop" in AVAIL_GENRES else 0,
        format_func=lambda g: f"{GENRE_EMOJI.get(g,'🎵')} {g.title()}",
    )
    pref_mood = st.selectbox(
        "Favorite Mood", AVAIL_MOODS,
        index=AVAIL_MOODS.index("happy") if "happy" in AVAIL_MOODS else 0,
        format_func=lambda m: f"{MOOD_EMOJI.get(m,'🎭')} {m.title()}",
    )
    pref_energy = st.slider("Target Energy", 0.0, 1.0, 0.72, 0.01)
    st.caption(
        ("🧘 Very Calm" if pref_energy < 0.3 else
         "😌 Relaxed"   if pref_energy < 0.5 else
         "🚶 Moderate"  if pref_energy < 0.7 else
         "🏃 High Energy" if pref_energy < 0.85 else
         "⚡ Extreme") + f"  ·  {pref_energy:.2f}"
    )
    pref_acoustic = st.toggle("Love acoustic sounds 🎸")

    st.markdown("---")
    top_k = st.slider("Recommendations", 1, min(30, len(SONGS)), 6)

    # Personalization stats
    n_l = sum(1 for v in st.session_state.ratings.values() if v > 0)
    n_d = sum(1 for v in st.session_state.ratings.values() if v < 0)
    n_f = len(st.session_state.favorites)
    if n_l + n_d + n_f:
        st.markdown("---")
        st.markdown("**Personalization**")
        st.markdown(
            f'<div class="stat-row">'
            f'<span class="stat-chip">❤️ {n_f} saved</span>'
            f'<span class="stat-chip">👍 {n_l} liked</span>'
            f'<span class="stat-chip">👎 {n_d} passed</span>'
            f'</div>',
            unsafe_allow_html=True,
        )
        if st.button("Reset ratings", use_container_width=True):
            st.session_state.ratings   = {}
            st.session_state.favorites = set()
            _save_json(RATINGS_PATH, {})
            _save_json(FAVS_PATH, [])
            st.rerun()

    st.markdown("---")
    st.caption(f"**{len(SONGS)}** songs · MusicMind AI")

user_prefs = {
    "favorite_genre": pref_genre,
    "favorite_mood":  pref_mood,
    "target_energy":  pref_energy,
    "likes_acoustic": pref_acoustic,
}

# ══════════════════════════════════════════════════════════════════════════════
# Hero
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="hero">
  <div class="hero-title">🎵 MusicMind AI Recommender</div>
  <div class="hero-sub">Personalized music · Rate songs to train your taste · 491 real tracks across every genre</div>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# Tabs
# ══════════════════════════════════════════════════════════════════════════════
tab_rec, tab_fav, tab_add, tab_cat, tab_cli, tab_how = st.tabs([
    "🎧 For You",
    "❤️ Favorites",
    "🔎 Search & Add",
    "📚 Catalog",
    "⚙️ CLI",
    "🔍 How It Works",
])

# ══════════════════════════════════════════════════════════════════════════════
# TAB — For You
# ══════════════════════════════════════════════════════════════════════════════
with tab_rec:
    songs_now   = get_songs()
    raw         = recommend_songs(user_prefs, songs_now, k=len(songs_now))
    all_boosted = apply_boosts(raw, CATALOG_DF)

    # ── Quality floor: only show songs ≥ 40 % match ──────────────────────
    # Scores below 40 % mean neither genre nor mood matched — not useful results.
    MIN_MATCH_PCT = 40
    quality  = [(s, sc, ex) for s, sc, ex in all_boosted if pct_of(sc) >= MIN_MATCH_PCT]
    results  = (quality if quality else all_boosted)[:top_k]

    # AI toggle row
    ai_c, note_c = st.columns([1, 3])
    with ai_c:
        use_ai = st.toggle("AI Explanations 🤖", help="Powered by Google Gemini (free). Set GEMINI_API_KEY in your .env file.")
    with note_c:
        if use_ai:
            if os.environ.get("GEMINI_API_KEY"):
                st.caption("🤖 Gemini active — auditing your picks + generating explanations")
            else:
                st.warning("Add `GEMINI_API_KEY=your_key` to `.env` to enable AI mode.", icon="⚠️")

    if use_ai and os.environ.get("GEMINI_API_KEY"):
        with st.spinner("Gemini is reviewing your picks…"):
            ai_out = ai_explain_recommendations(user_prefs, results)
        if ai_out["error"] is None:
            results = ai_out["final_recommendations"]
            if ai_out["removed"]:
                st.info(f"🤖 AI removed {len(ai_out['removed'])} poor-fit song(s) — {ai_out['removal_reason']}")
        else:
            st.warning(f"AI unavailable: {ai_out['error']}", icon="⚠️")

    # Metrics
    if results:
        tp = pct_of(results[0][1])
        ap = pct_of(sum(r[1] for r in results) / len(results))
        st.markdown(f"""
<div class="mrow">
  <div class="mcard"><div class="mnum">{len(songs_now)}</div><div class="mlbl">Songs</div></div>
  <div class="mcard"><div class="mnum" style="color:{pct_color(tp)}">{tp}%</div><div class="mlbl">Best Match</div></div>
  <div class="mcard"><div class="mnum" style="color:{pct_color(ap)}">{ap}%</div><div class="mlbl">Avg Match</div></div>
  <div class="mcard"><div class="mnum">{n_f + n_l}</div><div class="mlbl">Saved/Liked</div></div>
</div>""", unsafe_allow_html=True)

    st.markdown('<div class="sec-head">Top Picks For You</div>', unsafe_allow_html=True)
    if n_l + n_f:
        st.caption("✨ Scores are personalised — like or save more songs to keep improving them.")

    # Warn when this genre+mood combo has few quality matches
    n_quality = len(quality)
    if n_quality == 0:
        st.warning("No songs hit 40 % match for this profile — showing closest available. Try a different mood or genre.", icon="🎯")
    elif n_quality < top_k:
        # Count how many genre-only and mood-only matches exist to give useful advice
        genre_count = sum(1 for s, _, _ in all_boosted if s["genre"] == pref_genre)
        st.info(
            f"Only **{n_quality}** song{'s' if n_quality!=1 else ''} match your exact profile well "
            f"({genre_count} total {pref_genre} songs in catalog). "
            f"Showing best available — try adjusting mood or energy to see more.",
            icon="🎯",
        )

    # ── RAG Vibe Search ────────────────────────────────────────────────────
    with st.expander("🔍 Vibe Search — describe a mood or moment"):
        vibe_q = st.text_input(
            "",
            placeholder="e.g. late night drive, background music for studying, hype workout songs...",
            key="vibe_search_input",
        )
        st.caption("No API key needed — searches all 491 songs using local AI. Finds vibes the dropdowns can't.")

        if vibe_q.strip():
            from rag_retriever import retrieve as rag_retrieve
            rag_results = rag_retrieve(vibe_q.strip(), songs_now, k=6)

            if rag_results:
                rag_ai_out = None
                if use_ai and os.environ.get("GEMINI_API_KEY"):
                    from ai_explainer import ai_rag_explain
                    with st.spinner("Gemini is generating vibe explanations…"):
                        rag_ai_out = ai_rag_explain(vibe_q.strip(), rag_results)

                st.divider()
                st.markdown(
                    f'<div class="sec-head">Vibe matches for: \'{vibe_q.strip()}\'</div>',
                    unsafe_allow_html=True,
                )
                if rag_ai_out and rag_ai_out.get("summary"):
                    st.caption(f"✦ {rag_ai_out['summary']}")

                # Render cards in rows of 2 (fresh columns per row avoids expander layout quirks)
                for row_start in range(0, len(rag_results), 2):
                    row = rag_results[row_start:row_start + 2]
                    rcols = st.columns(len(row), gap="medium")
                    for j, (song, sim) in enumerate(row):
                        sid = str(song["id"])
                        sim_pct = max(1, round(sim * 100))
                        if sim >= 0.3:
                            sim_label = "🟢"
                        elif sim >= 0.15:
                            sim_label = "🟡"
                        else:
                            sim_label = "🟠"

                        is_fav = sid in st.session_state.favorites
                        rating = st.session_state.ratings.get(sid, 0)
                        art_url = get_artwork(song["title"], song["artist"])

                        with rcols[j]:
                            with st.container(border=True):
                                art_c, info_c = st.columns([1, 3], gap="small")
                                with art_c:
                                    if art_url:
                                        st.image(art_url, width=90)
                                    else:
                                        st.markdown(
                                            f'<div class="art-box">{GENRE_EMOJI.get(song["genre"], "🎵")}</div>',
                                            unsafe_allow_html=True,
                                        )
                                with info_c:
                                    st.caption(f"{sim_label} **{sim_pct}% match**")
                                    st.markdown(f"**{song['title']}**")
                                    st.caption(song["artist"])

                                st.markdown(f'<div>{pills_html(song, is_fav, rating)}</div>', unsafe_allow_html=True)

                                if rag_ai_out and rag_ai_out.get("explanations"):
                                    exp_text = rag_ai_out["explanations"].get(str(song["id"]), "")
                                    if exp_text:
                                        st.caption(f"✦ {exp_text}")

                                preview_url = get_preview(song["title"], song["artist"])
                                if preview_url:
                                    st.audio(preview_url, format="audio/mp4")

                                b1, b2, b3, _ = st.columns([1.3, 1.1, 1.1, 1])
                                with b1:
                                    if st.button(
                                        "❤️ Saved" if is_fav else "🤍 Save",
                                        key=f"rag_fv_{sid}",
                                        use_container_width=True,
                                    ):
                                        toggle_fav(sid)
                                        st.rerun()
                                with b2:
                                    if st.button(
                                        "👍 Liked" if rating == 1 else "👍 Like",
                                        key=f"rag_lk_{sid}",
                                        use_container_width=True,
                                    ):
                                        set_rating(sid, 0 if rating == 1 else 1)
                                        st.rerun()
                                with b3:
                                    if st.button(
                                        "👎 Passed" if rating == -1 else "👎 Pass",
                                        key=f"rag_ds_{sid}",
                                        use_container_width=True,
                                    ):
                                        set_rating(sid, 0 if rating == -1 else -1)
                                        st.rerun()
            else:
                st.info("No strong vibe matches found — try different words.")

    # Pre-fetch artwork silently
    with st.spinner("Fetching artwork…"):
        prefetch([s for s, _, _ in results])

    # ── Cards ──────────────────────────────────────────────────────────────
    col_l, col_r = st.columns(2, gap="medium")

    for i, (song, score, explanation) in enumerate(results):
        sid     = str(song["id"])
        pct     = pct_of(score)
        col     = pct_color(pct)
        is_fav  = sid in st.session_state.favorites
        rating  = st.session_state.ratings.get(sid, 0)
        art_url = get_artwork(song["title"], song["artist"])

        with (col_l if i % 2 == 0 else col_r):
            with st.container(border=True):
                # ── Row: artwork | info ──────────────────────────────────
                art_c, info_c = st.columns([1, 3], gap="small")

                with art_c:
                    if art_url:
                        st.image(art_url, width=90)
                    else:
                        st.markdown(
                            f'<div class="art-box">{GENRE_EMOJI.get(song["genre"],"🎵")}</div>',
                            unsafe_allow_html=True,
                        )

                with info_c:
                    # Rank + match badge (safe: only programmatic values)
                    st.markdown(
                        f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:3px">'
                        f'<span style="font-size:1.25rem;font-weight:900;background:linear-gradient(90deg,#a78bfa,#38bdf8);'
                        f'-webkit-background-clip:text;-webkit-text-fill-color:transparent">#{i+1}</span>'
                        f'<span style="font-size:.9rem;font-weight:800;color:{col};background:{col}22;'
                        f'border:1px solid {col}55;border-radius:99px;padding:1px 10px">{pct}% match</span>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                    # Title + artist — use markdown (handles & correctly, no HTML needed)
                    st.markdown(f"**{song['title']}**")
                    st.caption(song["artist"])

                # ── Pills (genre/mood are from catalog, controlled values) ─
                st.markdown(pills_html(song, is_fav, rating), unsafe_allow_html=True)

                # ── Score bar (pure programmatic values) ─────────────────
                st.markdown(score_bar(pct, col), unsafe_allow_html=True)

                # ── Explanation (plain text via st.caption — 100% safe) ──
                st.caption(f"✦ {explanation}")

                # ── 30-second preview ────────────────────────────────────
                preview_url = get_preview(song["title"], song["artist"])
                if preview_url:
                    st.audio(preview_url, format="audio/mp4")

                # ── Action buttons ───────────────────────────────────────
                b1, b2, b3, _ = st.columns([1.3, 1.1, 1.1, 1])
                with b1:
                    if st.button("❤️ Saved" if is_fav else "🤍 Save",
                                 key=f"fv_{sid}_{i}", use_container_width=True):
                        toggle_fav(sid)
                        st.rerun()
                with b2:
                    if st.button("👍 Liked" if rating==1 else "👍 Like",
                                 key=f"lk_{sid}_{i}", use_container_width=True):
                        set_rating(sid, 0 if rating==1 else 1)
                        st.rerun()
                with b3:
                    if st.button("👎 Passed" if rating==-1 else "👎 Pass",
                                 key=f"ds_{sid}_{i}", use_container_width=True):
                        set_rating(sid, 0 if rating==-1 else -1)
                        st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# TAB — Favorites
# ══════════════════════════════════════════════════════════════════════════════
with tab_fav:
    st.markdown('<div class="sec-head">❤️ My Saved Songs</div>', unsafe_allow_html=True)

    fav_songs = [s for s in get_songs() if str(s["id"]) in st.session_state.favorites]

    if not fav_songs:
        st.markdown('<div class="empty"><div style="font-size:3rem">🤍</div>'
                    '<div style="margin-top:.7rem">No saved songs yet.</div>'
                    '<div style="font-size:.85rem;color:#475569;margin-top:.3rem">'
                    'Hit <strong>Save</strong> on any recommendation.</div></div>',
                    unsafe_allow_html=True)
    else:
        st.caption(f"{len(fav_songs)} saved song{'s' if len(fav_songs)!=1 else ''}")
        prefetch(fav_songs)
        fc_l, fc_r = st.columns(2, gap="medium")
        for i, song in enumerate(fav_songs):
            sid     = str(song["id"])
            art_url = get_artwork(song["title"], song["artist"])
            s, _    = score_song(user_prefs, song)
            pct     = pct_of(s)
            col     = pct_color(pct)

            with (fc_l if i%2==0 else fc_r):
                with st.container(border=True):
                    a_c, i_c = st.columns([1, 3], gap="small")
                    with a_c:
                        if art_url:
                            st.image(art_url, width=75)
                        else:
                            st.markdown(f'<div class="art-box" style="font-size:1.6rem">{GENRE_EMOJI.get(song["genre"],"🎵")}</div>', unsafe_allow_html=True)
                    with i_c:
                        st.markdown(f"**{song['title']}**")
                        st.caption(song["artist"])
                        st.markdown(
                            f'<span class="pill p-genre">{GENRE_EMOJI.get(song["genre"],"🎵")} {song["genre"].title()}</span>'
                            f'<span style="font-size:.88rem;font-weight:700;color:{col}"> {pct}% match</span>',
                            unsafe_allow_html=True,
                        )
                    fav_preview = get_preview(song["title"], song["artist"])
                    if fav_preview:
                        st.audio(fav_preview, format="audio/mp4")
                    if st.button("💔 Remove", key=f"uf_{sid}_{i}"):
                        toggle_fav(sid)
                        st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# TAB — Search & Add
# ══════════════════════════════════════════════════════════════════════════════
with tab_add:
    st.markdown('<div class="sec-head">Search Real Songs · Add to Catalog</div>', unsafe_allow_html=True)
    st.markdown("Uses the **iTunes Search API** (free, no key). Find any track, tweak its audio features, and add it to your local catalog.")

    q = st.text_input("", placeholder="Search for an artist, song, or album… e.g. Kendrick Lamar, Chappell Roan")

    if q:
        with st.spinner("Searching iTunes…"):
            hits = itunes_search(q, limit=12)

        if not hits:
            st.markdown('<div class="err">⚠️ No results — check your internet connection.</div>', unsafe_allow_html=True)
        else:
            cur_df = pd.read_csv(DATA_PATH)
            def _dup(r):
                t, a = r["title"].lower().strip(), r["artist"].lower().strip()
                return not cur_df[(cur_df["title"].str.lower().str.strip()==t) &
                                  (cur_df["artist"].str.lower().str.strip()==a)].empty
            dup = [_dup(r) for r in hits]
            if any(dup):
                st.info(f"✅ {sum(dup)} result(s) are already in your catalog (marked ✅ below).")

            choice = st.radio(
                "Results",
                range(len(hits)),
                format_func=lambda i: f"{hits[i]['title']} — {hits[i]['artist']}  ({hits[i]['genre']})"
                                      + ("  ✅ in catalog" if dup[i] else ""),
                label_visibility="collapsed",
            )
            chosen        = hits[choice]
            mapped_genre  = ITUNES_GENRE_MAP.get(chosen["genre"], "pop")
            defaults      = GENRE_DEFAULTS.get(mapped_genre, GENRE_DEFAULTS["pop"])

            st.markdown("---")
            with st.container(border=True):
                p_c, d_c = st.columns([1, 4], gap="small")
                with p_c:
                    if chosen["art"]:
                        st.image(chosen["art"], width=80)
                    else:
                        st.markdown(f'<div class="art-box">{GENRE_EMOJI.get(mapped_genre,"🎵")}</div>', unsafe_allow_html=True)
                with d_c:
                    st.markdown(f"**{chosen['title']}**")
                    st.caption(chosen["artist"])
                    st.markdown(
                        f'iTunes genre: <span style="color:#60a5fa">{chosen["genre"]}</span>'
                        f' → mapped to <strong style="color:#a78bfa">{mapped_genre}</strong>',
                        unsafe_allow_html=True,
                    )
                if chosen.get("preview"):
                    st.audio(chosen["preview"], format="audio/mp4")

            if dup[choice]:
                st.markdown('<div class="ok">✅ This song is already in your catalog.</div>', unsafe_allow_html=True)

            st.markdown("**Fine-tune audio features:**")
            with st.form("add_form", border=True):
                l, r = st.columns(2)
                with l:
                    ft = st.text_input("Title",  value=chosen["title"])
                    fa = st.text_input("Artist", value=chosen["artist"])
                    fg = st.selectbox("Genre", ALL_GENRES,
                                      index=ALL_GENRES.index(mapped_genre) if mapped_genre in ALL_GENRES else 0,
                                      format_func=lambda g: f"{GENRE_EMOJI.get(g,'🎵')} {g.title()}")
                    fm = st.selectbox("Mood", ALL_MOODS,
                                      index=ALL_MOODS.index(defaults["mood"]) if defaults["mood"] in ALL_MOODS else 0,
                                      format_func=lambda m: f"{MOOD_EMOJI.get(m,'🎭')} {m.title()}")
                with r:
                    fe = st.slider("Energy",        0.0, 1.0, float(defaults["energy"]),  0.01)
                    ft2= st.slider("Tempo (BPM)",    40,  200, int(defaults["tempo_bpm"]),  1)
                    fv = st.slider("Valence",        0.0, 1.0, float(defaults["valence"]),  0.01)
                    fd = st.slider("Danceability",   0.0, 1.0, float(defaults["danceability"]), 0.01)
                    fc2= st.slider("Acousticness",   0.0, 1.0, float(defaults["acousticness"]), 0.01)

                if st.form_submit_button("➕ Add to Catalog", type="primary", use_container_width=True):
                    fresh = pd.read_csv(DATA_PATH)
                    dup2  = fresh[(fresh["title"].str.lower().str.strip()==ft.strip().lower()) &
                                  (fresh["artist"].str.lower().str.strip()==fa.strip().lower())]
                    if not dup2.empty:
                        st.markdown('<div class="err">⚠️ Already in catalog.</div>', unsafe_allow_html=True)
                    elif not ft.strip():
                        st.markdown('<div class="err">⚠️ Title cannot be empty.</div>', unsafe_allow_html=True)
                    else:
                        append_song_to_csv({
                            "id":next_song_id(fresh),"title":ft.strip(),"artist":fa.strip(),
                            "genre":fg,"mood":fm,"energy":round(fe,2),"tempo_bpm":ft2,
                            "valence":round(fv,2),"danceability":round(fd,2),"acousticness":round(fc2,2),
                        })
                        reload_catalog()
                        st.markdown(f'<div class="ok">✅ <strong>{html_lib.escape(ft)}</strong> added!</div>', unsafe_allow_html=True)
                        st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# TAB — Catalog
# ══════════════════════════════════════════════════════════════════════════════
with tab_cat:
    cat = get_catalog_df()
    st.markdown(f'<div class="sec-head">Song Catalog · {len(cat)} tracks</div>', unsafe_allow_html=True)

    cf1, cf2, cf3 = st.columns(3)
    with cf1: fg2 = st.multiselect("Genre", sorted(cat["genre"].unique()), placeholder="All genres")
    with cf2: fm2 = st.multiselect("Mood",  sorted(cat["mood"].unique()),  placeholder="All moods")
    with cf3: fq2 = st.text_input("Search title / artist", placeholder="type to filter…", label_visibility="collapsed")

    disp = cat.copy()
    if fg2: disp = disp[disp["genre"].isin(fg2)]
    if fm2: disp = disp[disp["mood"].isin(fm2)]
    if fq2.strip():
        q2 = fq2.strip().lower()
        disp = disp[disp["title"].str.lower().str.contains(q2, na=False) |
                    disp["artist"].str.lower().str.contains(q2, na=False)]

    disp = disp.copy()
    disp["⭐ match %"] = disp.apply(lambda row: pct_of(score_song(user_prefs, row.to_dict())[0]), axis=1)
    disp["❤️"] = disp["id"].apply(lambda x: "❤️" if str(x) in st.session_state.favorites else "")
    disp["👍"] = disp["id"].apply(lambda x:
        "👍" if st.session_state.ratings.get(str(x),0)==1 else
        ("👎" if st.session_state.ratings.get(str(x),0)==-1 else ""))
    disp = disp.sort_values("⭐ match %", ascending=False)

    st.dataframe(
        disp[["title","artist","genre","mood","energy","tempo_bpm","❤️","👍","⭐ match %"]].reset_index(drop=True),
        width="stretch", height=480,
    )
    st.caption(f"Showing {len(disp)} of {len(cat)} · ⭐ = match % for your current profile")

# ══════════════════════════════════════════════════════════════════════════════
# TAB — CLI
# ══════════════════════════════════════════════════════════════════════════════
with tab_cli:
    st.markdown('<div class="sec-head">Python CLI Runner</div>', unsafe_allow_html=True)
    c1, _ = st.columns([1, 3])
    with c1:
        if st.button("▶  Run main.py", type="primary", use_container_width=True):
            with st.spinner("Running…"):
                res = subprocess.run([sys.executable,"main.py"], cwd=ROOT,
                                     capture_output=True, text=True, timeout=30)
            out = res.stdout + ("\n\n--- STDERR ---\n"+res.stderr if res.stderr.strip() else "")
            st.markdown(f'<div class="cli">{html_lib.escape(out)}</div>', unsafe_allow_html=True)

    st.markdown("---")
    DEMOS = {"All Profiles Summary":"main.py","Lofi Chill User":"demo_lofi.py",
             "High-Energy Pop Fan":"demo_pop.py","Rock Listener":"demo_rock.py"}
    demo = st.selectbox("Preset demo", list(DEMOS.keys()))
    d1, _ = st.columns([1, 3])
    with d1:
        if st.button("▶  Run Demo", use_container_width=True):
            with st.spinner("Running…"):
                res2 = subprocess.run([sys.executable, DEMOS[demo]], cwd=ROOT,
                                      capture_output=True, text=True, timeout=15)
            o2 = res2.stdout + ("\n--- STDERR ---\n"+res2.stderr if res2.stderr.strip() else "")
            st.markdown(f'<div class="cli">{html_lib.escape(o2) or "(no output)"}</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB — How It Works
# ══════════════════════════════════════════════════════════════════════════════
with tab_how:
    st.markdown('<div class="sec-head">How MusicMind Works</div>', unsafe_allow_html=True)
    st.markdown("""
<div class="hw"><div class="hw-n">1</div><div class="hw-t"><strong>Catalog</strong><br>
  139 songs in <code>data/songs.csv</code> including the full Billboard Hot 100. Each track carries
  10 attributes: genre, mood, energy, tempo, valence, danceability, acousticness.</div></div>
<div class="hw"><div class="hw-n">2</div><div class="hw-t"><strong>Scoring (max 5.0) — Genre-first priority</strong><br>
  · <strong>Genre match → +2.0</strong> (primary — keeps results in your genre)<br>
  · Mood match → <strong>+1.5</strong> · Energy proximity → <strong>up to +1.0</strong>  (1.0 − |energy − target|)<br>
  · Acoustic preference → <strong>up to +0.5</strong> · Only songs ≥ 40 % match are shown</div></div>
<div class="hw"><div class="hw-n">3</div><div class="hw-t"><strong>Personalisation via Ratings</strong><br>
  👍 Like → +0.75 · genre gets +0.08 affinity per like &nbsp;|&nbsp;
  ❤️ Save → +0.40 &nbsp;|&nbsp; 👎 Pass → −0.75 penalty.<br>
  Genre affinity compounds — the more you rate, the smarter the feed gets.</div></div>
<div class="hw"><div class="hw-n">4</div><div class="hw-t"><strong>AI Agentic Workflow (optional)</strong><br>
  Google Gemini runs a two-step workflow: <em>Step 1</em> audits and removes poor-fit songs
  despite a high score; <em>Step 2</em> writes a natural-language explanation for each remaining track.</div></div>
<div class="hw"><div class="hw-n">5</div><div class="hw-t"><strong>Match %</strong><br>
  score ÷ 5.0 × 100 &nbsp;·&nbsp;
  <span style="color:#22c55e">■</span> ≥85% &nbsp;
  <span style="color:#eab308">■</span> ≥65% &nbsp;
  <span style="color:#f97316">■</span> ≥45% &nbsp;
  <span style="color:#ef4444">■</span> &lt;45%</div></div>
""", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### Score Breakdown · Current Profile")
    brows = []
    for _, row in get_catalog_df().iterrows():
        s, reasons = score_song(user_prefs, row.to_dict())
        brows.append({"Song": row["title"], "Artist": row["artist"],
                      "Match %": pct_of(s), "Reasons": ", ".join(reasons) or "no match"})
    bdf = pd.DataFrame(brows).sort_values("Match %", ascending=False).reset_index(drop=True)
    bc, tc = st.columns([2,3])
    with bc:
        st.bar_chart(bdf.set_index("Song")["Match %"], height=400)
    with tc:
        st.dataframe(bdf[["Song","Artist","Match %","Reasons"]], width="stretch", height=400)
