"""Content-based athlete-to-opportunity ranking with six report-defined components."""

import logging
import math
import re
import unicodedata
from collections import OrderedDict
from datetime import UTC, datetime
from functools import lru_cache
from threading import Lock

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

WEIGHTS = {"position": 0.25, "skills": 0.30, "age": 0.15, "location": 0.10, "experience": 0.10, "goals": 0.10}
LEVELS = ("beginner", "district", "state", "national", "professional")
LEVEL_CODES = {level: index for index, level in enumerate(LEVELS)}
AGE_TOLERANCE = 1
ALIASES = {"center back": "centre back", "center midfielder": "central midfielder", "fullback": "full back",
           "centre": "center", "wicketkeeper": "wicket keeper", "allrounder": "all rounder",
           "batsman": "batter", "defence": "defense"}
RELATED_POSITIONS = {frozenset(pair) for pair in (
    ("central midfielder", "attacking midfielder"), ("central midfielder", "defensive midfielder"),
    ("attacking midfielder", "winger"), ("winger", "striker"), ("centre back", "full back"),
    ("centre back", "defensive midfielder"), ("batter", "wicket keeper"), ("all rounder", "batter"),
    ("all rounder", "bowler"), ("point guard", "shooting guard"), ("small forward", "power forward"),
    ("sprinter", "hurdler"), ("doubles", "mixed doubles"),
)}
LOGGER = logging.getLogger(__name__)


def normalize(value):
    text = unicodedata.normalize("NFKC", value or "").casefold()
    return " ".join(re.sub(r"[-‐‑–]+", " ", text).split())


def normalize_category(value):
    key = normalize(value)
    return ALIASES.get(key, key)


def categories(values):
    return {key for value in values or () if (key := normalize_category(value))}


def eligibility(athlete, opp, now=None):
    if not normalize(athlete.sport) or normalize(athlete.sport) != normalize(opp.sport):
        return "different_sport"
    deadline = getattr(opp, "deadline", None)
    if deadline is not None:
        deadline = deadline if deadline.tzinfo else deadline.replace(tzinfo=UTC)
        if deadline <= (now or datetime.now(UTC)):
            return "closed"
    lo, hi = opp.age_min, opp.age_max
    if athlete.age is None:
        return "age_unknown" if lo is not None or hi is not None else "strict"
    if (lo is not None and athlete.age < lo - AGE_TOLERANCE) or (
        hi is not None and athlete.age > hi + AGE_TOLERANCE
    ):
        return "age_ineligible"
    return "strict" if age_score(athlete.age, lo, hi) == 1 else "age_tolerance"


def eligible(athlete, opp, now=None):
    return eligibility(athlete, opp, now) in {"strict", "age_tolerance", "age_unknown"}


def position_score(pos, wanted):
    wanted = categories(wanted)
    pos = normalize_category(pos)
    if not wanted or pos in wanted:
        return 1.0
    return 0.6 if any(frozenset((pos, w)) in RELATED_POSITIONS for w in wanted) else 0.0


def skills_score(have, want):
    a, b = categories(have), categories(want)
    if not b:
        return 1.0
    if not a:
        return 0.0
    return len(a & b) / math.sqrt(len(a) * len(b))


def age_score(age, lo, hi):
    if lo is None and hi is None:
        return 1.0
    if age is None:
        return 0.5
    if (lo is None or age >= lo) and (hi is None or age <= hi):
        return 1.0
    return 0.5


def location_score(athlete, opp):
    city = normalize(opp.city)
    if city in {"", "online", "remote"}:
        return 1.0
    if normalize(athlete.city) == city:
        return 1.0
    if normalize(athlete.region) and normalize(athlete.region) == normalize(opp.region):
        return 0.6
    return 0.2


def experience_score(have, want):
    wanted = normalize(want)
    if not wanted:
        return 1.0
    a, b = LEVEL_CODES.get(normalize(have)), LEVEL_CODES.get(wanted)
    if a is None or b is None:
        return 0.5
    return {0: 1.0, 1: 0.6}.get(abs(a - b), 0.2)


@lru_cache(maxsize=8)
def tfidf_index(corpus):
    vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), strip_accents="unicode")
    analyze = vectorizer.build_analyzer()
    if not any(analyze(text) for text in corpus):
        return None, None, {}
    matrix = vectorizer.fit_transform(corpus)
    return vectorizer, matrix, {text: i for i, text in enumerate(corpus)}


def goals_scores(goals, texts, corpus=None):
    goals = normalize(goals)
    descriptions = [normalize(text) for text in texts]
    if not goals or not any(descriptions):
        return [0.5] * len(descriptions)
    reference = tuple(dict.fromkeys(normalize(t) for t in (descriptions if corpus is None else corpus)))
    vectorizer, matrix, index = tfidf_index(reference)
    if vectorizer is None:
        return [0.0 if text else 0.5 for text in descriptions]
    query = vectorizer.transform([goals])
    known = cosine_similarity(query, matrix)[0]
    return [
        0.5 if not text else float(np.clip(known[index[text]], 0, 1)) if text in index
        else float(np.clip(cosine_similarity(query, vectorizer.transform([text]))[0, 0], 0, 1))
        for text in descriptions
    ]


class SemanticEncoder:
    def __init__(self, model_name):
        from sentence_transformers import SentenceTransformer

        self.model = SentenceTransformer(model_name, device="cpu", local_files_only=True)
        self.cache = OrderedDict()
        self.lock = Lock()

    def scores(self, goals, texts):
        goals = normalize(goals)
        texts = [normalize(text) for text in texts]
        if not goals or not any(texts):
            return [0.5] * len(texts)
        with self.lock:
            missing = list(dict.fromkeys(text for text in texts if text and text not in self.cache))
            vectors = self.model.encode([goals, *missing], normalize_embeddings=True)
            self.cache.update(zip(missing, vectors[1:], strict=True))
            result = [float(np.clip(vectors[0] @ self.cache[text], 0, 1)) if text else 0.5 for text in texts]
            for text in dict.fromkeys(texts):
                if text:
                    self.cache.move_to_end(text)
            while len(self.cache) > 4096:
                self.cache.popitem(last=False)
        return result


@lru_cache(maxsize=2)
def semantic_encoder(model_name):
    try:
        return SemanticEncoder(model_name)
    except Exception as exc:
        LOGGER.warning("Sentence-BERT unavailable (%s). Using TF-IDF.", type(exc).__name__)
        return None


def combine(components, weights=None):
    weights = WEIGHTS if weights is None else weights
    return round(100 * sum(weights[k] * components[k] for k in weights) / sum(weights.values()), 1)


def explain(components, athlete, opp, score, status, common, missing):
    head = "Strong match" if score >= 80 else "Good match" if score >= 60 else "Partial match"
    reasons = [head]
    if not categories(opp.positions):
        reasons.append("Open to all positions")
    else:
        reasons.append({1.0: "Position matches", 0.6: "Related position", 0.0: "Requested position differs"}[components["position"]])
    if common:
        reasons.append("Skill overlap on " + " and ".join(common[:3]))
    if missing:
        reasons.append("Missing requested skills: " + ", ".join(missing))
    if status == "age_tolerance":
        message = "Outside the stated age range by one year"
        if getattr(opp, "hard_age_limit", True):
            message += ". Applications require the stated age range."
        reasons.append(message)
    elif status == "age_unknown":
        reasons.append("Add your age to confirm eligibility")
    elif opp.age_min is not None or opp.age_max is not None:
        reasons.append("Age within range")
    if components["location"] == 0.2:
        reasons.append("Different region or location unknown")
    elif components["location"] == 0.6:
        reasons.append("Same region")
    elif normalize(opp.city) not in {"", "online", "remote"}:
        reasons.append("Same city")
    if opp.level:
        if components["experience"] == 1.0:
            reasons.append("Level fits")
        elif components["experience"] <= 0.5:
            reasons.append("Experience level differs or is unknown")
    if not normalize(athlete.goals) or not normalize(opp.description):
        reasons.append("Goal or description text is missing")
    elif components["goals"] < 0.15:
        reasons.append("Limited overlap with your career goals")
    return reasons


def rank(athlete, opps, k=10, *, corpus=None, encoder=None, now=None):
    now = now or datetime.now(UTC)
    pool = [opp for opp in opps if eligible(athlete, opp, now)]
    if not pool:
        return []
    texts = [opp.description for opp in pool]
    method = "tfidf"
    if encoder is not None:
        try:
            goals = encoder.scores(athlete.goals, texts)
            method = "sentence-bert"
        except Exception as exc:
            LOGGER.warning("Sentence-BERT encoding failed (%s). Using TF-IDF.", type(exc).__name__)
    if method == "tfidf":
        goals = goals_scores(athlete.goals, texts, corpus)
    results = []
    for opp, goal in zip(pool, goals, strict=True):
        components = {
            "position": position_score(athlete.position, opp.positions),
            "skills": round(skills_score(athlete.skills, opp.skills), 3),
            "age": age_score(athlete.age, opp.age_min, opp.age_max),
            "location": location_score(athlete, opp),
            "experience": experience_score(athlete.level, opp.level),
            "goals": round(goal, 3),
        }
        score = combine(components)
        status = eligibility(athlete, opp, now)
        have, want = categories(athlete.skills), categories(opp.skills)
        common, missing = sorted(have & want), sorted(want - have)
        hard_age = getattr(opp, "hard_age_limit", True)
        can_apply = status == "strict" or (status == "age_tolerance" and not hard_age)
        results.append({
            "opportunity": opp, "score": score, "compatibility_score": score,
            "components": components, "eligibility": status, "can_apply": can_apply,
            "matching_skills": common, "missing_skills": missing, "similarity_method": method,
            "reasons": explain(components, athlete, opp, score, status, common, missing),
        })
    results.sort(key=lambda result: (-result["score"], str(getattr(result["opportunity"], "id", ""))))
    return results[:k]
