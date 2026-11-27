"""Deterministic synthetic fixtures and independent graded relevance annotations."""

import csv
import json
import random
from collections import Counter
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from app.catalog import CITIES, SPORTS, TYPES

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
AS_OF = datetime(2026, 10, 1, tzinfo=UTC)
LEVELS = ("beginner", "district", "state", "national", "professional")

# Athlete language and posting language deliberately include paraphrases.
INTENTS = {
    "selection": ("I want an academy trial and a place on a competitive squad.",
                  "Selection assessment for entry into a performance roster."),
    "education": ("I need funding to continue playing while studying.",
                  "Sports scholarship with tuition support and an academic pathway."),
    "competition": ("I want tournament experience against stronger opponents.",
                    "Organised fixtures and competitive match play."),
    "training": ("I want coached practice to improve my technique.",
                 "Supervised training sessions with technical development and feedback."),
    "exposure": ("I want to be seen by scouts and find representation.",
                 "Recruiter showcase with talent identification sessions."),
}
TYPE_INTENT = dict(zip(TYPES, ("selection", "education", "competition", "training", "exposure", "selection", "training")))
ORG_FIRST = ("Juniperline", "Asterbank", "Kestrelbend")
ORG_LAST = ("Eleven", "Wickets", "Courts", "Track", "Shuttles")
FIRST = ("Aarvi", "Nivan", "Tavish", "Ishani", "Kavya", "Dhrumi", "Tejal", "Riyan", "Anika", "Devik")
LAST = ("Aster", "Fern", "Kite", "Lake", "Lark", "Pine", "Reed", "Vale", "Wren", "Zephyr")


def fixture_id(code):
    return uuid5(NAMESPACE_URL, f"groundup.local/synthetic/v1/{code}")


def deadline(offset, anchor=AS_OF):
    return anchor + timedelta(days=offset) if offset is not None else None


def make_organisations():
    return [
        {"organisation_id": f"o{3 * s + i + 1:03}", "name": f"{prefix} {ORG_LAST[s]} Collective",
         "sport": sport, "city": city, "region": CITIES[city], "synthetic": True}
        for s, sport in enumerate(SPORTS)
        for i, (prefix, city) in enumerate(zip(ORG_FIRST, ("Delhi", "Pune", "Kochi"), strict=True))
    ]


def make_athletes(seed=7):
    rng = random.Random(seed)
    names = [f"{first} {last}" for first in FIRST for last in LAST]
    names += [f"{first} {last}-Mere" for first in FIRST for last in LAST]
    rng.shuffle(names)
    starters = [
        ("football", "central midfielder", 19, "Delhi", "district", "selection"),
        ("cricket", "bowler", 18, "Pune", "district", "competition"),
        ("basketball", "point guard", 20, "Kochi", "state", "education"),
        ("athletics", "thrower", 56, "Chennai", "beginner", "training"),
    ]
    result = []
    for i, name in enumerate(names):
        if i < len(starters):
            sport, position, age, city, level, intent = starters[i]
        else:
            sport = rng.choice(tuple(SPORTS))
            position = rng.choice(tuple(SPORTS[sport]))
            age = rng.randint(13, 27) if i % 29 else 46
            city = rng.choice(tuple(CITIES))
            possible_levels = LEVELS[:3] if age < 16 else LEVELS[:4] if age < 19 else LEVELS
            level = rng.choice(possible_levels)
            intent = rng.choice(tuple(INTENTS))
        skills = sorted(rng.sample(SPORTS[sport][position], rng.randint(2, 4)))
        if i == 0:
            skills = ["passing", "vision", "ball control"]
        result.append({
            "athlete_id": f"a{i + 1:03}", "name": name, "sport": sport, "position": position,
            "age": age, "city": city, "region": CITIES[city], "level": level, "skills": skills,
            "goals": INTENTS[intent][0], "bio": f"Fictional {position} training in {city}.",
            "mode": "professional" if i < 3 or rng.random() < 0.7 else "casual",
            "intent": intent, "travel_flexible": rng.random() < 0.3, "synthetic": True,
        })
    return result


def make_opportunities(organisations, seed=42):
    rng = random.Random(seed)
    featured = [
        ("trial", "central midfielder", 17, 21, "district", ("passing", "vision", "ball control")),
        ("trial", "winger", 17, 21, "district", ("dribbling", "pace", "crossing")),
        ("camp", "attacking midfielder", 20, 23, "state", ("vision", "passing")),
        ("trial", "central midfielder", 17, 21, "district", ("passing", "vision")),
    ]
    result = []
    for i in range(300):
        org = organisations[i % len(organisations)]
        sport = org["sport"]
        options = SPORTS[sport]
        position = rng.choice(tuple(options))
        positions = [position] if rng.random() < 0.85 else []
        skills = sorted(rng.sample(options[position], rng.randint(1, 3)))
        lo = rng.randint(12, 23)
        hi = lo + rng.randint(2, 6)
        level = rng.choice(LEVELS[:3] if lo < 15 else LEVELS[:4])
        kind = rng.choice(tuple(TYPES))
        city = rng.choice((org["city"], org["city"], rng.choice(tuple(CITIES)), None))
        offset = None if i % 23 == 0 else rng.randint(12, 120)
        if i % 43 == 42:
            offset = -7
        if i % 15 == 0 and i // 15 < len(featured):
            kind, position, lo, hi, level, skills = featured[i // 15]
            positions, city, offset = [position], "Delhi", 30 + i if i != 45 else -1
        intent = TYPE_INTENT[kind]
        description = f"{INTENTS[intent][1]} Open to {', '.join(positions) or 'all positions'}."
        if i == 0:
            description = "An academy trial for midfielders seeking a place on a competitive squad. Passing and vision drills."
        if i == 15:
            description = "An academy trial for wide attackers with crossing, dribbling, and pace."
        result.append({
            "opportunity_id": f"p{i + 1:03}", "organisation_id": org["organisation_id"],
            "title": f"{sport.title()} {TYPES[kind].lower()} · {org['name'].split()[0]} {i + 1:03}",
            "type": kind, "sport": sport, "positions": positions, "age_min": lo, "age_max": hi,
            "skills": skills, "level": level, "city": city, "region": CITIES.get(city),
            "description": description, "deadline_offset_days": offset,
            "deadline": deadline(offset).isoformat() if offset is not None else None,
            "intent": intent, "hard_age_limit": i % 7 != 6, "synthetic": True,
        })
    return result


def make_posts(athletes):
    milestones = ("finished a technique session", "joined a friendly fixture", "logged a recovery day",
                  "set a new training goal", "practised with a district group")
    return [
        {"post_id": f"s{i + 1:03}", "athlete_id": a["athlete_id"],
         "body": f"Synthetic training diary: I {milestones[i % len(milestones)]} for {a['sport']} in {a['city']}.",
         "day_offset": -i, "synthetic": True}
        for i, a in enumerate(athletes[:50])
    ]


def relevance(athlete, opp):
    """Decision tree using explicit intent, travel tolerance and minimum readiness."""
    if athlete["sport"] != opp["sport"]:
        return 0, "different sport"
    if opp["deadline_offset_days"] is not None and opp["deadline_offset_days"] <= 0:
        return 0, "closed"
    if not opp["age_min"] <= athlete["age"] <= opp["age_max"]:
        return 0, "outside stated age range"
    intent = athlete["intent"] == opp["intent"]
    accessible = not opp["city"] or athlete["region"] == opp["region"] or athlete["travel_flexible"]
    prerequisite = not opp["positions"] or athlete["position"] in opp["positions"]
    ready = LEVELS.index(athlete["level"]) >= LEVELS.index(opp["level"])
    has_entry_skill = bool(set(athlete["skills"]).intersection(opp["skills"]))
    if not accessible and not intent:
        return 0, "travel and intent mismatch"
    if intent and accessible and prerequisite and ready and has_entry_skill:
        return 3, "accessible target pathway with readiness"
    if accessible and ((intent and (prerequisite or ready)) or (prerequisite and ready and has_entry_skill)):
        return 2, "accessible target or plausible alternate pathway"
    return 1, "exploratory option with barriers"


def make_dataset():
    organisations = make_organisations()
    athletes = make_athletes()
    opportunities = make_opportunities(organisations)
    labels = [
        {"athlete_id": athlete["athlete_id"], "opportunity_id": opp["opportunity_id"],
         "grade": grade, "rationale": rationale, "synthetic": True}
        for athlete in athletes for opp in opportunities
        for grade, rationale in [relevance(athlete, opp)]
    ]
    return {
        "athletes": athletes, "opportunities": opportunities, "organisations": organisations,
        "posts": make_posts(athletes), "relevance_labels": labels,
    }


def metadata(dataset):
    return {
        "synthetic": True, "as_of": AS_OF.isoformat(), "seeds": {"athletes": 7, "opportunities": 42},
        "counts": {name: len(rows) for name, rows in dataset.items()},
        "athletes_by_sport": dict(Counter(row["sport"] for row in dataset["athletes"])),
        "opportunities_by_sport": dict(Counter(row["sport"] for row in dataset["opportunities"])),
        "opportunities_by_type": dict(Counter(row["type"] for row in dataset["opportunities"])),
        "pair_grades": dict(Counter(row["grade"] for row in dataset["relevance_labels"])),
    }


def export_dataset(dataset, directory=DATA_DIR):
    synthetic = directory / "synthetic"
    synthetic.mkdir(parents=True, exist_ok=True)
    for name, rows in dataset.items():
        with (synthetic / f"{name}.csv").open("w", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(file, rows[0], lineterminator="\n")
            writer.writeheader()
            for row in rows:
                writer.writerow({k: json.dumps(v, ensure_ascii=False) if isinstance(v, (list, tuple, bool)) else v
                                 for k, v in row.items()})
    (directory / "metadata.json").write_text(json.dumps(metadata(dataset), indent=2) + "\n", encoding="utf-8")
