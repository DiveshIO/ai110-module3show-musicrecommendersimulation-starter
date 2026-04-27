# Model Card — MusicMind AI Recommender

## 1. Model Name

**MusicMind AI Recommender v2.0**

Built off the CodePath AI110 Module 3 project, but heavily extended.

---

## 2. What this thing actually does

This app recommends songs from a 491-track dataset based on what the user picks (genre, mood, energy, acoustic preference).

It’s mainly for the AI110 showcase, but honestly it works well enough to use for finding music.

There are basically two parts:

- A **scoring system** that ranks songs based on how well they match what the user wants
- An optional **AI layer (Gemini 2.0 Flash)** that filters out bad matches and explains why songs were picked

This is **not a real production recommender**. No accounts, no collaborative filtering, no real audio analysis.

---

## 3. How it works

### Step 1 — Scoring (always runs)

Every song gets a score out of 5.0 based on match:

| Match                  | Points     |
| ---------------------- | ---------- |
| Same genre             | +2.0       |
| Same mood              | +1.5       |
| Energy close to target | up to +1.0 |
| Acoustic match         | up to +0.5 |

Genre matters the most. If someone picks hip-hop, they want hip-hop — not some random rock song that “feels intense.”

Anything below ~40% match just gets filtered out completely.

---

### Step 2 — Rating boosts

If the user interacts with songs, scores get adjusted:

- Liked → +0.75 (and small boost to that genre)
- Saved → +0.40
- Passed → −0.75

So over time, it actually starts adapting instead of staying static.

---

### Step 3 — Gemini AI (optional)

If there’s an API key:

- Gemini checks top results and removes anything that doesn’t actually fit (even if the score says it does)
- Then it writes short explanations for why each song matches

If Gemini fails or isn’t set up, nothing breaks — it just skips this part.

---

## 4. Data

- 491 songs across 23 genres (pop, hip-hop, rock, edm, etc.)
- Started messy, cleaned it up:
  - Removed all fake songs
  - Added real songs manually + bulk imports

- Around 27 fake/placeholder artists were removed

Important limitation:

- Audio features (energy, tempo, etc.) are **not real**
- They’re just guessed based on genre

Also:

- Dataset is biased toward English pop + hip-hop
- Stuff like jazz, classical, lofi is underrepresented

---

## 5. What’s actually good about it

- **Genre-first logic works** — you don’t get weird cross-genre garbage
- **Filters out low-quality matches** instead of spamming results
- Uses real songs with artwork + previews, so it feels legit
- Doesn’t crash if APIs fail (this matters more than people think)
- Gets better as you rate songs

---

## 6. What’s weak (be honest)

- **Fake audio features** → energy matching is kinda unreliable
- **No collaborative filtering** → doesn’t learn from other users
- **Some combinations are dead zones** (like hip-hop + certain moods)
- **Cold start problem** → new users get generic results
- **Dataset bias** → mostly US/UK music
- **iTunes gaps** → some songs missing previews/art

---

## 7. Testing

### Test harness

Ran 8 profile-based tests:

- Pop user gets pop → PASS
- Lofi user gets lofi → PASS
- Scores sorted correctly → PASS
- Score never exceeds 5 → PASS
- Unknown genre still returns results → PASS (but weak confidence)
- Low-energy user gets calm songs → PASS
- Acoustic preference works → PASS
- Output format correct → PASS

Average confidence: **0.89**

---

### Unit tests

12 pytest tests on core logic — all pass.

---

### Manual testing

Big issue before:

- Mood was overpowering genre
- Example: hip-hop + intense → returned rock/metal

Fixed by making genre weight higher again.

Now it behaves how people expect.

---

## 8. AI usage (what actually happened)

Used Claude a lot during development for:

- Building the Streamlit UI
- Designing Gemini prompts
- Debugging annoying issues (like HTML breaking on `&`)
- Writing test harness
- Cleaning dataset
- Fixing scoring logic

---

### One thing AI got right

Switching from custom HTML to native Streamlit components.

The old approach broke on song titles like “Earth, Wind & Fire” because of `&`.

That bug was stupid but real. Native components fixed it completely.

---

### One thing AI got wrong

It suggested making mood more important than genre.

That completely broke the system.

Users picking hip-hop started getting rock songs just because they matched “intense.”

Fix was obvious in hindsight:

- Genre first
- Mood second

---

### Biggest limitation

Audio features are fake.

Every pop song basically has the same energy value, which makes the energy slider kinda pointless.

Real fix:
→ integrate Spotify API for actual audio data

---

## 9. Future improvements

- Real audio features (Spotify API)
- Collaborative filtering
- User accounts + persistent data
- Better search (like “late night drive” type queries)
- Let AI actually learn from user history, not just current input

---

If you want it even sharper or more aggressive, I can tighten it more. Right now this sounds like a real dev explaining their system instead of trying to impress a professor.
