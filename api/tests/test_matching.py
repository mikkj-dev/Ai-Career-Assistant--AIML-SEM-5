from datetime import UTC, datetime
from types import SimpleNamespace as NS

import pytest

from app import matching
from app.matching import combine, rank

ATHLETE = NS(sport="football", position="central midfielder", age=19, city="Delhi", region="North",
             level="state", skills=["passing", "vision"], goals="academy trial to grow as a creative midfielder")


def opp(**kw):
    base = dict(sport="football", positions=["central midfielder"], age_min=17, age_max=21, city="Delhi",
                region="North", level="state", skills=["passing", "vision"], description="academy trial for midfielders")
    return NS(**{**base, **kw})


def test_report_worked_example():
    # M2 report, section 4: hand-calculated example must score 93.5.
    c = dict(position=1.0, skills=0.85, age=1.0, location=1.0, experience=1.0, goals=0.80)
    assert combine(c) == 93.5


def test_hard_filters_drop_ineligible():
    pool = [opp(), opp(sport="cricket"), opp(age_min=23, age_max=25)]
    assert len(rank(ATHLETE, pool)) == 1


def test_ranking_and_reasons():
    good, far = opp(), opp(city="Chennai", region="South", positions=["striker"], skills=["finishing"])
    top = rank(ATHLETE, [far, good])
    assert top[0]["opportunity"] is good and top[0]["score"] > top[1]["score"]
    assert {"Position matches", "Age within range", "Same city"} <= set(top[0]["reasons"])
    assert 0 <= top[1]["score"] <= 100


def test_position_aliases_related_and_open():
    assert matching.position_score("Full-back", ["full back"]) == 1
    assert matching.position_score("centre back", ["full back"]) == 0.6
    assert matching.position_score("winger", ["goalkeeper"]) == 0
    assert matching.position_score(None, [" "]) == 1
    assert "Open to all positions" in rank(ATHLETE, [opp(positions=[])])[0]["reasons"]


def test_skills_binary_cosine_and_normalization():
    assert matching.skills_score(["passing", " PASSING ", "vision"], ["passing"]) == pytest.approx(2 ** -0.5)
    assert matching.skills_score([], ["passing"]) == 0
    assert matching.skills_score([" "], []) == 1


def test_eligibility_and_deadline():
    now = datetime(2026, 10, 1, tzinfo=UTC)
    assert matching.eligibility(ATHLETE, opp(deadline=now), now) == "closed"
    assert matching.eligibility(ATHLETE, opp(age_min=21), now) == "age_ineligible"
    assert matching.eligibility(ATHLETE, opp(age_min=None, age_max=19), now) == "strict"
    for hard_limit in [True, False]:
        match = rank(ATHLETE, [opp(age_min=20, hard_age_limit=hard_limit)], now=now)[0]
        assert match["eligibility"] == "age_tolerance"
        assert match["components"]["age"] == 0.5
        assert match["can_apply"] is not hard_limit
    with_unknown_age = NS(**(vars(ATHLETE) | {"age": None}))
    assert rank(with_unknown_age, [opp()])[0]["eligibility"] == "age_unknown"
    assert not rank(with_unknown_age, [opp()])[0]["can_apply"]


def test_location_and_experience_scores():
    assert matching.location_score(ATHLETE, opp(city="   ")) == 1
    assert matching.location_score(ATHLETE, opp(city=" delhi ")) == 1
    assert matching.location_score(ATHLETE, opp(city="Lucknow", region=" NORTH ")) == 0.6
    assert matching.location_score(ATHLETE, opp(city="Kochi", region="South")) == 0.2
    assert matching.experience_score(" State ", "state") == 1
    assert matching.experience_score("district", "state") == 0.6
    assert matching.experience_score("professional", "beginner") == 0.2
    assert matching.experience_score(None, "state") == 0.5


def test_text_similarity_uses_reference_corpus_and_handles_empty_vocabulary():
    corpus = ["academy midfield training", "fast bowling drills"]
    whole = matching.goals_scores("academy midfield training", corpus, corpus)
    subset = matching.goals_scores("academy midfield training", corpus[:1], corpus)
    assert whole == pytest.approx([1, 0])
    assert subset == pytest.approx(whole[:1])
    assert matching.goals_scores("the", ["an", "", None]) == [0, 0.5, 0.5]
    assert matching.goals_scores(" ", ["academy training"]) == [0.5]
    assert matching.goals_scores("goals", []) == []
    assert matching.goals_scores("unknown token", corpus, corpus) == [0, 0]


def test_score_extremes_and_deterministic_ties():
    assert combine(dict.fromkeys(matching.WEIGHTS, 0)) == 0
    assert combine(dict.fromkeys(matching.WEIGHTS, 1)) == 100
    first, second = opp(id="a"), opp(id="b")
    assert [row["opportunity"].id for row in rank(ATHLETE, [second, first])] == ["a", "b"]
    assert rank(ATHLETE, []) == []


def test_semantic_method_and_fallback():
    class Encoder:
        def scores(self, goals, texts):
            return [0.85 for _ in texts]

    class Unavailable:
        def scores(self, goals, texts):
            raise RuntimeError("model unavailable")

    scored = rank(ATHLETE, [opp()], encoder=Encoder())[0]
    assert scored["similarity_method"] == "sentence-bert"
    assert scored["components"]["goals"] == 0.85
    fallback = rank(ATHLETE, [opp()], encoder=Unavailable())[0]
    assert fallback["similarity_method"] == "tfidf"
    assert fallback["components"] == rank(ATHLETE, [opp()])[0]["components"]
