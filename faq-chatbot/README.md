# College FAQ Assistant (NLP + TF-IDF + Cosine Similarity)

A beginner-friendly FAQ chatbot built with Python, Flask, scikit-learn and plain HTML/CSS/JS.
It runs fully offline: no API key, no paid service.

## Project structure

```
faq-chatbot/
├── app.py            # Flask server (routes: "/" and "/chat")
├── chatbot.py        # TF-IDF + cosine similarity matching engine
├── preprocess.py     # lowercase, punctuation removal, tokenize, stopwords, stemming
├── faqs.json         # 35 college FAQs (question + answer)
├── requirements.txt
├── README.md
├── templates/
│   └── index.html
└── static/
    ├── style.css
    └── script.js
```

## Installation and running

**Requirements:** Python 3.9 or newer (check with `python --version`).

```bash
# 1. go into the project folder
cd faq-chatbot

# 2. create a virtual environment
python -m venv venv

# 3. activate it
#    Windows (PowerShell):  venv\Scripts\Activate.ps1
#    Windows (cmd):         venv\Scripts\activate.bat
#    macOS / Linux:         source venv/bin/activate

# 4. install dependencies
pip install -r requirements.txt

# 5. run the app
python app.py
```

Open **http://127.0.0.1:5000** in your browser.

Quick command-line test without the browser: `python chatbot.py`

### About NLTK
`preprocess.py` uses NLTK's `PorterStemmer` when NLTK is installed (it is listed in
`requirements.txt`). If NLTK is missing, it automatically falls back to a small built-in
stemmer, so the app still runs. The stopword list is built in, so **no `nltk.download()`
is needed**.

### Troubleshooting

| Problem | Fix |
|---|---|
| `python` not found | Try `python3`, or reinstall Python and tick "Add to PATH". |
| `ModuleNotFoundError: flask` / `sklearn` | The virtual environment is not active, or step 4 was skipped. Activate it and run `pip install -r requirements.txt`. |
| PowerShell says scripts are disabled | Run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, or use `activate.bat` in cmd. |
| `Address already in use` (port 5000) | Change the port in `app.py` (`port=5001`), or stop the other program (macOS AirPlay uses 5000). |
| Page loads but replies say "Could not reach the server" | Make sure `python app.py` is still running in the terminal. |
| `FileNotFoundError: faqs.json` | Run commands from inside the `faq-chatbot` folder. |
| Edited `faqs.json` but nothing changed | Restart the app: FAQs are loaded once at startup. |
| `faqs.json is not valid JSON` | Check for a missing comma or quote near the line shown in the error. |

## Testing results

Run against the finished project (threshold = 0.30):

| Test type | Input | Chatbot output | Score |
|---|---|---|---|
| Exact FAQ question | `What is the minimum attendance required?` | "A minimum of 75% attendance in each subject is required to be eligible for the end-semester examination." | 1.00 |
| Different wording, same meaning | `how much attendance do i need to sit for exams` | Matches "What is the minimum attendance required?" | 0.64 |
| Different wording | `when do placements companies come to campus` | Matches "Which companies visit the campus for placements?" | 0.84 |
| Spelling mistakes | `waht scholarshp can i get as a studnt` | Matches "What scholarships are available for students?" | 0.85 |
| Spelling mistakes | `libary timmings` | "The library is open from 8:00 AM to 8:00 PM, Monday to Saturday..." | 1.00 |
| Unrelated | `Who won the cricket world cup?` | "Sorry, I couldn't understand your question. Please try asking differently." | 0.00 |
| Unrelated | `What is the capital of France?` | Same fallback message | 0.00 |
| Empty input | `` (or spaces) | "Please type a question so I can help you." (HTTP 400) | 0.00 |
| Only symbols | `???` | Fallback message | 0.00 |

In an automated run of 22 inputs, 21 matched the expected FAQ. The remaining one (`what is
mid semester exam`) returned the general exam-schedule FAQ because no FAQ covers
mid-semester exams. All 35 FAQ questions also match themselves with score 1.0.

## Sample conversation

```
Bot : Hello! I'm the College FAQ Assistant. Ask me about admissions, courses, fees, exams...
You : how do i pay fees online
Bot : Fees can be paid online through the student portal using net banking, UPI, or debit/credit card...
      Matched FAQ: How can I pay my tuition fees?
You : is wifi available
Bot : Yes. High-speed Wi-Fi is available across classrooms, labs, the library and hostels...
      Matched FAQ: Is Wi-Fi available on campus?
You : what is the weather today
Bot : Sorry, I couldn't understand your question. Please try asking differently.
```

## Key functions

| File | Function | What it does |
|---|---|---|
| `preprocess.py` | `tokenize` | Lowercases, joins "wi-fi" to "wifi", strips punctuation, splits into words |
| | `normalize_synonyms` | Maps words like needed/need/required to one word |
| | `remove_stopwords` | Removes words like "the", "is", "what" |
| | `correct_spelling` | Fixes typos using the closest word in the FAQ vocabulary (`difflib`) |
| | `preprocess` | Runs the whole pipeline and stems each word |
| `chatbot.py` | `FAQChatbot.__init__` | Loads FAQs, preprocesses questions, builds the TF-IDF matrix once |
| | `FAQChatbot.get_response` | Vectorises the user question, finds the best cosine score, applies the threshold |
| `app.py` | `/chat` route | Accepts JSON `{"message": ...}` and returns JSON with the answer |
| `script.js` | `sendMessage` | Calls `/chat` using `fetch` and shows the reply |

## Concepts explained

**1. What is an FAQ chatbot?**
A program that answers common questions automatically. It compares your question with a stored list of
questions and replies with the answer linked to the closest one.

**2. What is NLP?**
Natural Language Processing is the area of AI that lets computers work with human language: cleaning
text, finding meaning, and comparing sentences.

**3. What is tokenization?**
Splitting text into small units (tokens), usually words. "What is the fee?" becomes
`["what", "is", "the", "fee"]`.

**4. What are stopwords?**
Very common words ("the", "is", "of", "what") that add little meaning for matching. Removing them lets the
important words ("attendance", "scholarship") count more.

**5. What is TF-IDF?**
Term Frequency x Inverse Document Frequency gives every word a weight. A word gets a higher weight if it
appears often in one question (TF) but in few questions overall (IDF). So rare, meaningful words like
"scholarship" matter more than words that appear everywhere. Each question becomes a list of numbers (a vector).

**6. What is cosine similarity?**
It measures the angle between two vectors. The score runs from 0 (nothing in common) to 1 (identical
direction). It compares word patterns, not text length.

**7. How does the chatbot find the best match?**
It preprocesses your question, converts it to a TF-IDF vector, computes cosine similarity with all 35 FAQ
vectors, and picks the FAQ with the highest score.

**8. Why a similarity threshold?**
Without it, the bot would always return some answer, even for "What is the capital of France?". If the best
score is below 0.30, the bot says it did not understand instead of giving a wrong answer. A higher threshold
makes it stricter; a lower one makes it more willing to guess.

**9. How do Flask and the frontend communicate?**
`script.js` sends a `POST` request to `/chat` with JSON `{"message": "..."}`. Flask runs the chatbot and
returns JSON with `status`, `answer`, `matched_question` and `score`. JavaScript reads that JSON and adds
a new chat bubble, with no page reload.

**10. Limitations and future improvements**
- TF-IDF matches words, not meaning: "How do I join?" may fail to match "How can I apply for admission?".
  Fix: use word embeddings or sentence-transformers.
- Spelling correction only works for words close to the FAQ vocabulary.
- Synonyms must be added by hand in `SYNONYMS`.
- No memory of earlier messages, so follow-up questions are not understood.
- Only English; only the 35 stored FAQs.
- Ideas: show the top-3 suggestions when unsure, add feedback buttons, store chat logs, add an admin page
  for editing FAQs, and deploy online.

## Complete workflow in simple English

1. **Server starts.** `app.py` creates the chatbot. The chatbot reads `faqs.json`, cleans each question,
   and turns them into TF-IDF number vectors. This happens once.
2. **You open the page.** Flask sends `index.html`, which loads the CSS and JavaScript. A welcome message appears.
3. **You type a question** and press Send or Enter. JavaScript shows your message and a loading indicator.
4. **The browser sends it** to `/chat` as JSON.
5. **Flask checks it.** An empty message gets a polite "please type a question" reply.
6. **The text is cleaned:** lowercase, no punctuation, split into words, synonyms unified, stopwords removed,
   typos fixed, words reduced to stems.
7. **The question becomes a vector** using the same TF-IDF model built at startup.
8. **Cosine similarity** compares it with every FAQ vector. The highest score wins.
9. **The threshold decides.** At 0.30 or above, the matching answer is returned. Below that, the fallback message is returned.
10. **The browser shows the reply** as a chatbot bubble. You can keep asking, or press "Clear chat" to start over.
