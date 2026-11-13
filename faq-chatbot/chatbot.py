"""
chatbot.py
----------
Core FAQ matching engine: TF-IDF vectors + cosine similarity.

Upgrades in this version:
    * Small talk replies (hello, thanks, bye, help)
    * "Did you mean...?" suggestions when the match is weak
"""

import json
import os

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from preprocess import clean_tokens, preprocess, tokenize

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FAQ_PATH = os.path.join(BASE_DIR, "faqs.json")

SIMILARITY_THRESHOLD = 0.30     # at or above this -> answer is shown
MIN_COVERAGE = 0.5              # at least half of the user's words must appear in the matched FAQ
SUGGESTION_MIN_SCORE = 0.12     # between this and the threshold -> show suggestions
MAX_SUGGESTIONS = 3

FALLBACK_MESSAGE = (
    "Sorry, I couldn't understand your question. Please try asking differently."
)
EMPTY_MESSAGE = "Please type a question so I can help you."
SUGGEST_MESSAGE = "I'm not sure I understood. Did you mean one of these?"

# Small talk rules: (anchor words, extra allowed words, reply).
# A message is small talk only if it contains an anchor word AND every word
# of the message is in anchors + extras. So "hi fees" is NOT small talk.
SMALL_TALK = [
    ({"hi", "hello", "hey", "hii", "hiii", "hola", "namaste",
      "morning", "afternoon", "evening"},
     {"good", "there", "bot", "assistant"},
     "Hello! 👋 I'm the College FAQ Assistant. Ask me about admissions, "
     "fees, exams, attendance, placements, scholarships or the library."),
    ({"thanks", "thank", "thankyou", "thx", "ty"},
     {"you", "so", "much", "very", "a", "lot", "bot", "assistant"},
     "You're welcome! Let me know if you have any other questions."),
    ({"bye", "goodbye", "tata", "later"},
     {"see", "you", "take", "care", "bot"},
     "Goodbye! Have a great day. 👋"),
    ({"help"},
     {"me", "please", "need", "i", "can", "you"},
     "I can answer questions about admission, courses, fees, exams, attendance, "
     "placements, scholarships, the library, hostel and Wi-Fi. "
     "Just type your question!"),
]


class FAQChatbot:
    """Loads the FAQs once, builds the TF-IDF matrix, and answers questions."""

    def __init__(self, faq_path: str = FAQ_PATH, threshold: float = SIMILARITY_THRESHOLD):
        self.threshold = threshold
        self.faqs = self._load_faqs(faq_path)
        self.questions = [item["question"] for item in self.faqs]
        self.answers = [item["answer"] for item in self.faqs]

        # Vocabulary of (unstemmed) words from the FAQ questions, used for spell correction
        self.vocabulary = set()
        for q in self.questions:
            self.vocabulary.update(clean_tokens(q))

        # Preprocess every FAQ question, then learn TF-IDF weights from them
        self.processed_questions = [preprocess(q) for q in self.questions]
        self.vectorizer = TfidfVectorizer(sublinear_tf=True)
        self.faq_matrix = self.vectorizer.fit_transform(self.processed_questions)

    @staticmethod
    def _load_faqs(path: str) -> list:
        """Read and validate the FAQ JSON file."""
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"FAQ file not found: {path}")
        except json.JSONDecodeError as exc:
            raise ValueError(f"faqs.json is not valid JSON: {exc}")

        if not isinstance(data, list) or not data:
            raise ValueError("faqs.json must contain a non-empty list of FAQs.")
        for i, item in enumerate(data):
            if "question" not in item or "answer" not in item:
                raise ValueError(f"FAQ #{i + 1} needs both 'question' and 'answer'.")
        return data

    @staticmethod
    def _result(status, answer, matched=None, score=0.0, suggestions=None):
        """Build the response dictionary in one consistent shape."""
        return {"status": status, "answer": answer, "matched_question": matched,
                "score": score, "suggestions": suggestions or []}

    @staticmethod
    def _small_talk(user_input: str):
        """Return a small-talk reply (hello, thanks, bye, help) or None."""
        words = set(tokenize(user_input))
        if not words:
            return None
        for anchors, extras, reply in SMALL_TALK:
            if words & anchors and words <= (anchors | extras):
                return reply
        return None

    def _best_match(self, scores, user_words: set):
        """
        Look at the 5 highest-scoring FAQs and pick the one that has the best
        mix of cosine score AND word coverage. Returns (index, score, coverage).
        """
        best = None
        for i in scores.argsort()[::-1][:5]:
            faq_words = set(self.processed_questions[i].split())
            coverage = len(user_words & faq_words) / len(user_words)
            rank = float(scores[i]) * (0.5 + 0.5 * coverage)
            if best is None or rank > best[0]:
                best = (rank, int(i), float(scores[i]), coverage)
        return best[1], best[2], best[3]

    def get_response(self, user_input: str) -> dict:
        """
        Return a dict:
            status           : 'ok' | 'suggest' | 'fallback' | 'smalltalk' | 'empty'
            answer           : text shown to the user
            matched_question : best FAQ question (only when status == 'ok')
            score            : cosine similarity of the best match (0-1)
            suggestions      : list of similar FAQ questions (only when 'suggest')
        """
        if not isinstance(user_input, str) or not user_input.strip():
            return self._result("empty", EMPTY_MESSAGE)

        reply = self._small_talk(user_input)
        if reply:
            return self._result("smalltalk", reply)

        processed = preprocess(user_input, self.vocabulary)
        if not processed:  # e.g. only stopwords or symbols like "???"
            return self._result("fallback", FALLBACK_MESSAGE)

        user_vector = self.vectorizer.transform([processed])
        scores = cosine_similarity(user_vector, self.faq_matrix).flatten()

        # Coverage = share of the user's words found in the FAQ question.
        # This stops a match on a single word (e.g. only "semester") from
        # returning a wrong answer.
        user_words = set(processed.split())
        best_index, best_score, coverage = self._best_match(scores, user_words)

        # Strong match -> answer it
        if best_score >= self.threshold and coverage >= MIN_COVERAGE:
            return self._result("ok", self.answers[best_index],
                                self.questions[best_index], round(best_score, 3))

        # Weak match -> offer up to 3 similar questions to click
        ranked = scores.argsort()[::-1][:MAX_SUGGESTIONS]
        suggestions = [self.questions[i] for i in ranked if scores[i] >= SUGGESTION_MIN_SCORE]
        if suggestions:
            return self._result("suggest", SUGGEST_MESSAGE, None,
                                round(best_score, 3), suggestions)

        return self._result("fallback", FALLBACK_MESSAGE, None, round(best_score, 3))


if __name__ == "__main__":
    # Simple command-line chat for quick testing
    bot = FAQChatbot()
    print("College FAQ Assistant (type 'quit' to exit)")
    while True:
        text = input("You: ")
        if text.strip().lower() in {"quit", "exit"}:
            break
        result = bot.get_response(text)
        print("Bot:", result["answer"], f"[score={result['score']}]")
        for s in result["suggestions"]:
            print("   - Did you mean:", s)