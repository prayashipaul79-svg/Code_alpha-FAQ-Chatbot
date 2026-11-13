"""
preprocess.py
-------------
Text preprocessing for the FAQ chatbot.

Steps (applied to both FAQ questions and user input):
    1. Lowercase
    2. Remove punctuation / special characters
    3. Tokenize into words
    4. Map synonyms to one word (needed/required -> required) and remove stopwords
    5. (Optional) correct spelling mistakes using the FAQ vocabulary
    6. Stem words (NLTK PorterStemmer if installed, otherwise a simple built-in stemmer)

Everything here works offline. No NLTK data download is needed, because the
stopword list is built in and the Porter stemmer needs no data files.
"""

import difflib
import re

# ---------------------------------------------------------------------------
# Stemmer: use NLTK's PorterStemmer when available, else a lightweight fallback
# ---------------------------------------------------------------------------
try:
    from nltk.stem import PorterStemmer

    _porter = PorterStemmer()
    NLTK_AVAILABLE = True
except ImportError:  # NLTK not installed
    _porter = None
    NLTK_AVAILABLE = False

# Longest suffixes first so "ations" is tried before "s".
_SUFFIXES = (
    "ations", "ation", "ingly", "ments", "ness", "ities", "ment",
    "ings", "ing", "ies", "ied", "ers", "ions", "ion", "ally",
    "ed", "es", "er", "ly", "s",
)


def _simple_stem(word: str) -> str:
    """Very small suffix-stripping stemmer used when NLTK is missing."""
    if len(word) <= 3:
        return word
    for suffix in _SUFFIXES:
        if word.endswith(suffix) and len(word) - len(suffix) >= 3:
            stem = word[: -len(suffix)]
            if suffix in ("ies", "ied"):
                stem += "y"
            return stem
    # drop a final "e" so "course" and "courses" give the same stem
    if word.endswith("e") and len(word) > 4:
        return word[:-1]
    return word


def stem_word(word: str) -> str:
    """Stem one word with NLTK if possible, else with the fallback."""
    if NLTK_AVAILABLE:
        return _porter.stem(word)
    return _simple_stem(word)


# ---------------------------------------------------------------------------
# Stopwords (built-in English list, so no nltk.download() is required)
# ---------------------------------------------------------------------------
STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "if", "so", "than", "then", "that",
    "this", "these", "those", "is", "am", "are", "was", "were", "be", "been",
    "being", "do", "does", "did", "doing", "have", "has", "had", "having",
    "i", "me", "my", "we", "our", "us", "you", "your", "he", "she", "it",
    "its", "they", "them", "their", "what", "which", "who", "whom", "how",
    "when", "where", "why", "will", "would", "can", "could", "should", "shall",
    "may", "might", "must", "of", "at", "by", "for", "with", "about", "to",
    "from", "in", "out", "on", "off", "over", "under", "into", "as", "any",
    "some", "there", "here", "also", "just", "get", "tell", "please", "want",
    "present", "inside",
    "know", "like", "need", "much", "many", "very", "too", "up", "down",
}


def tokenize(text: str) -> list:
    """Lowercase, strip punctuation/special characters and split into words."""
    text = text.lower()
    text = re.sub(r"(?<=[a-z])[.\-](?=[a-z])", "", text)  # "wi-fi" -> "wifi", "b.tech" -> "btech"
    text = re.sub(r"\b([bm])\s+(tech|sc|com)\b", r"\1\2", text)  # "b tech" -> "btech", "m sc" -> "msc"
    text = re.sub(r"[^a-z0-9\s]", " ", text)  # keep only letters, digits, spaces
    return text.split()


# Words that mean the same thing in this domain are mapped to one word, so that
# "attendance needed" matches "attendance required". Easy to extend.
SYNONYMS = {
    "need": "required", "needed": "required", "needs": "required",
    "require": "required", "requires": "required", "requirement": "required",
    "requirements": "required", "compulsory": "required", "mandatory": "required",
    "cost": "fee", "costs": "fee", "charges": "fee", "charge": "fee", "price": "fee",
    "job": "placement", "jobs": "placement", "recruit": "placement",
    "recruiters": "company", "recruiter": "company",
    "grant": "scholarship", "grants": "scholarship", "funding": "scholarship",
    "long": "duration", "length": "duration", "period": "duration",
    "eligible": "eligibility", "qualification": "eligibility", "qualify": "eligibility",
    "offered": "offer", "offers": "offer",
    "join": "admission", "joining": "admission", "enroll": "admission", "enrol": "admission",
    "mid": "middle", "midway": "middle", "between": "middle",
    "quit": "leave", "dropout": "leave",
    "switch": "change", "shift": "change", "move": "change", "changing": "change",
    "transfer": "change", "transferring": "change", "migrate": "change",
}


def normalize_synonyms(tokens: list) -> list:
    """Replace known synonyms with one common word."""
    return [SYNONYMS.get(t, t) for t in tokens]


def remove_stopwords(tokens: list) -> list:
    """Drop common words that carry little meaning."""
    return [t for t in tokens if t not in STOPWORDS]


def correct_spelling(tokens: list, vocabulary: set) -> list:
    """
    Replace unknown words by the closest known word from the FAQ vocabulary.
    Example: 'scholarshp' -> 'scholarship'. Words that are already known, or
    have no close match, are left unchanged.
    """
    corrected = []
    for token in tokens:
        if token in vocabulary or len(token) < 4 or token.isdigit():
            corrected.append(token)
            continue
        match = difflib.get_close_matches(token, vocabulary, n=1, cutoff=0.8)
        corrected.append(match[0] if match else token)
    return corrected


def clean_tokens(text: str) -> list:
    """Lowercase -> remove punctuation -> tokenize -> synonyms -> remove stopwords (no stemming)."""
    return remove_stopwords(normalize_synonyms(tokenize(text)))


def preprocess(text: str, vocabulary: set = None) -> str:
    """
    Full pipeline. Returns a single cleaned string of stemmed tokens,
    ready to be fed to the TF-IDF vectorizer.
    """
    if not isinstance(text, str):
        return ""
    tokens = clean_tokens(text)
    if vocabulary:
        tokens = correct_spelling(tokens, vocabulary)
    return " ".join(stem_word(t) for t in tokens)


if __name__ == "__main__":
    sample = "What's the MINIMUM attendance required for the exams?!"
    print("Original :", sample)
    print("Processed:", preprocess(sample))
    print("Using NLTK stemmer:", NLTK_AVAILABLE)