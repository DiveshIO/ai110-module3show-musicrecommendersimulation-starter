# 🎧 Model Card: Music Recommender Simulation

## 1. Model Name

Give your model a short, descriptive name.  
Worst Shazam Model
We just guess randomly, but shazam is better lul

---

## 2. Intended Use

Describe what your recommender is designed to do and who it is for.

Prompts:

- What kind of recommendations does it generate
  A rank list of top 5 from the csv files, score them and reason why we picked them.

- What assumptions does it make about the user

make assumputon abuot user preference genre which used for the rating

- Is this for real users or classroom exploration
  it's just classroom exploration where need need more data for real users usage.

---

## 3. How the Model Works

Explain your scoring approach in simple language.

Prompts:

- What features of each song are used (genre, energy, mood, etc.)
  each song have 9 attriputes
- What user preferences are considered
  we look at favorite genre, mood, target energy, and acoustic sound perference

- How does the model turn those into a score
  the modle look at each song and it gievs +1 if matches genre, 1.5 if mood, 2 if energy, .5 is acoustic

- What changes did you make from the starter logic
  just added the +2 for genre those stuff only.

---

## 4. Data

Describe the dataset the model uses.

Prompts:

- How many songs are in the catalog
  18
- What genres or moods are represented
  15 genres: lofi, pop, rock, ambient, synthwave, jazz, indie pop, hip-hop, classical, r&b, country, metal, reggae, edm, folk.
- Did you add or remove data
  added 8 songs
- Are there parts of musical taste missing in the dataset
  there are missing musics as some have 1 songs linked

---

## 5. Strengths

Where does your system seem to work well

## User get their top result absed on their perference match where it was getting a good accurace score which shows it can match a good song.

## 6. Limitations and Bias

Where the system struggles or behaves unfairly.

- The system has error with genre where almost all the genre have 1 song where if a person pick a certain genre they will only get once.

## 7. Evaluation

How you checked whether the recommender behaved as expected.

- I train the test thought the AI model
  where we had the model actual score and then we try to calculate the weight it needs that's how it was evualated.

---

## 8. Future Work

Ideas for how you would improve the model next.

## Adding more data in the csv will help the model be able to train better where now it has one song liked to each genre which is not doing anything for the model.

## 9. Personal Reflection

This was an amazing lesson where it was great that the model can change based on how we score where it was a fun lesson.

What was your biggest learning moment during this project?
Being able to see the reason was and how the AI teach me about.

How did using AI tools help you, and when did you need to double-check them?
I used them to help me make them code better and ask to fix any bugess.

What surprised you about how simple algorithms can still "feel" like recommendations?
the score system was so simple. where it just add the thing based on matching where it was easy without using complex stuff

What would you try next if you extended this project?
I would try to add more user perference as it feels weak.
