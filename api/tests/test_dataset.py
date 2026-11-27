from collections import Counter

from app.catalog import CITIES, SPORTS, TYPES
from app.dataset import export_dataset, fixture_id, make_dataset, metadata


def test_generation_is_reproducible(tmp_path):
    dataset = make_dataset()
    assert dataset == make_dataset()
    export_dataset(dataset, tmp_path / "first")
    export_dataset(make_dataset(), tmp_path / "second")
    first = tmp_path / "first"
    for path in first.rglob("*.*"):
        assert path.read_bytes() == (tmp_path / "second" / path.relative_to(first)).read_bytes()


def test_dataset_counts_and_relations():
    dataset = make_dataset()
    counts = metadata(dataset)["counts"]
    assert counts == {"athletes": 200, "opportunities": 300, "organisations": 15, "posts": 50, "relevance_labels": 60_000}
    key_names = {"athletes": "athlete_id", "opportunities": "opportunity_id",
                 "organisations": "organisation_id", "posts": "post_id"}
    identifiers = {key: {row[field] for row in dataset[key]} for key, field in key_names.items()}
    for key in identifiers:
        assert len(identifiers[key]) == counts[key]
    all_ids = {fixture_id(code) for values in identifiers.values() for code in values}
    assert len(all_ids) == 565
    assert all(row["synthetic"] is True for rows in dataset.values() for row in rows)
    orgs = {row["organisation_id"]: row for row in dataset["organisations"]}
    for athlete in dataset["athletes"]:
        position_skills = SPORTS[athlete["sport"]][athlete["position"]]
        assert set(athlete["skills"]) <= set(position_skills)
        assert 8 <= athlete["age"] <= 60 and CITIES[athlete["city"]] == athlete["region"]
    for opp in dataset["opportunities"]:
        assert orgs[opp["organisation_id"]]["sport"] == opp["sport"]
        assert set(opp["positions"]) <= SPORTS[opp["sport"]].keys()
        assert opp["type"] in TYPES and 8 <= opp["age_min"] <= opp["age_max"] <= 60
    assert all(post["athlete_id"] in identifiers["athletes"] for post in dataset["posts"])
    assert len({(r["athlete_id"], r["opportunity_id"]) for r in dataset["relevance_labels"]}) == 60_000
    assert set(Counter(row["grade"] for row in dataset["relevance_labels"])) == {0, 1, 2, 3}
    assert all(row["athlete_id"] in identifiers["athletes"] and row["opportunity_id"] in identifiers["opportunities"]
               for row in dataset["relevance_labels"])
