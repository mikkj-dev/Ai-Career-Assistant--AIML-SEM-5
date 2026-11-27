"""Run the shared-candidate ranking experiment and write its artifacts."""

import argparse
import json
from math import log2
from pathlib import Path
from types import SimpleNamespace

import matplotlib
import numpy as np
import pandas as pd

from app import matching
from app.dataset import AS_OF, ROOT, deadline, make_dataset, metadata

matplotlib.use("Agg")
from matplotlib import pyplot as plt  # noqa: E402

K_VALUES = (5, 10)
METRICS = [f"{metric}@{k}" for k in K_VALUES for metric in ("Precision", "Recall", "NDCG")]
THRESHOLD = 2
RANDOM_TRIALS = 50
BOOTSTRAP_TRIALS = 2000
WEIGHT_TRIALS = 300
SEEDS = {"random": 1, "bootstrap": 3, "weights": 11}
METHODS = {
    "random": "Random (shared pool)", "filter_only": "Filter only", "tfidf": "Weighted TF-IDF",
    "sentence_bert": "Weighted Sentence-BERT", "equal": "Equal weights",
}


def dcg(gains, k):
    return sum(grade / log2(index + 2) for index, grade in enumerate(gains[:k]))


def metrics(order, labels):
    gains = [labels[identifier] for identifier in order]
    ideal = sorted(labels.values(), reverse=True)
    relevant = sum(grade >= THRESHOLD for grade in ideal)
    result = []
    for k in K_VALUES:
        hits = sum(grade >= THRESHOLD for grade in gains[:k])
        ideal_dcg = dcg(ideal, k)
        result += [hits / k, hits / relevant if relevant else 0, dcg(gains, k) / ideal_dcg if ideal_dcg else 0]
    return np.array(result)


def weighted_order(components, ids, weights):
    scores = np.round(100 * (components @ weights) / weights.sum(), 1)
    return ids[np.lexsort((ids, -scores))]


def bootstrap_metrics(values, samples):
    estimates = np.asarray(values)
    draws = estimates[samples].mean(axis=1)
    limits = np.quantile(draws, [0.025, 0.975], axis=0).T
    return {
        "metrics": dict(zip(METRICS, estimates.mean(axis=0).tolist(), strict=True)),
        "ci95": dict(zip(METRICS, limits.tolist(), strict=True)),
    }


def evaluate(dataset, semantic):
    rng = np.random.default_rng(SEEDS["random"])
    weight_rng = np.random.default_rng(SEEDS["weights"])
    sampled_weights = weight_rng.dirichlet(np.ones(len(matching.WEIGHTS)), size=WEIGHT_TRIALS)
    default_weights = np.array(list(matching.WEIGHTS.values()))
    variants = {}
    for index, feature in enumerate(matching.WEIGHTS):
        weights = default_weights.copy()
        weights[index] = 0
        variants[f"without_{feature}"] = weights
    variants["equal"] = np.ones(len(matching.WEIGHTS))
    opportunities = [
        SimpleNamespace(**(row | {"id": row["opportunity_id"], "deadline": deadline(row["deadline_offset_days"])}))
        for row in dataset["opportunities"]
    ]
    corpus = tuple(opp.description for opp in opportunities if opp.deadline is None or opp.deadline > AS_OF)
    grades = {(row["athlete_id"], row["opportunity_id"]): row["grade"] for row in dataset["relevance_labels"]}
    measurements = {method: [] for method in ("random", "filter_only", "tfidf", *variants)}
    semantic_failed = False
    measurements["sentence_bert"] = []
    all_scores, counts, relevant_counts = [], [], []
    sensitivity = np.zeros(WEIGHT_TRIALS)
    for row in dataset["athletes"]:
        athlete = SimpleNamespace(**row)
        pool = [opp for opp in opportunities if matching.eligible(athlete, opp, AS_OF)]
        labels = {opp.id: grades[(athlete.athlete_id, opp.id)] for opp in pool}
        ids = np.array(list(labels), dtype=str)
        counts.append(len(labels))
        relevant_counts.append(sum(grade >= THRESHOLD for grade in labels.values()))
        measurements["random"].append(np.mean([metrics(rng.permutation(ids), labels) for _ in range(RANDOM_TRIALS)], axis=0))
        by_deadline = sorted(pool, key=lambda opp: (opp.deadline is None, opp.deadline, opp.id))
        measurements["filter_only"].append(metrics([opp.id for opp in by_deadline], labels))
        ranked = matching.rank(athlete, pool, len(pool), corpus=corpus, now=AS_OF)
        measurements["tfidf"].append(metrics([entry["opportunity"].id for entry in ranked], labels))
        all_scores.extend(entry["score"] for entry in ranked)
        if semantic is not None and not semantic_failed:
            other = matching.rank(athlete, pool, len(pool), corpus=corpus, encoder=semantic, now=AS_OF)
            semantic_failed = any(entry["similarity_method"] != "sentence-bert" for entry in other)
            measurements["sentence_bert"].append(metrics([entry["opportunity"].id for entry in other], labels))
        components = np.array([list(entry["components"].values()) for entry in ranked]).reshape(-1, len(default_weights))
        ranked_ids = np.array([entry["opportunity"].id for entry in ranked], dtype=str)
        for key, weights in variants.items():
            measurements[key].append(metrics(weighted_order(components, ranked_ids, weights), labels))
        for i, weights in enumerate(sampled_weights):
            sensitivity[i] += metrics(weighted_order(components, ranked_ids, weights), labels)[-1]

    rng = np.random.default_rng(SEEDS["bootstrap"])
    n = len(counts)
    indices = rng.integers(n, size=(BOOTSTRAP_TRIALS, n))
    results = {key: bootstrap_metrics(values, indices) for key, values in measurements.items()
               if values and (key != "sentence_bert" or not semantic_failed)}
    paired = bootstrap_metrics(np.array(measurements["tfidf"]) - measurements["filter_only"], indices)
    semantic_paired = None
    if "sentence_bert" in results:
        semantic_paired = bootstrap_metrics(np.array(measurements["sentence_bert"]) - measurements["tfidf"], indices)
    distribution, edges = np.histogram(all_scores, bins=np.arange(0, 101, 10))
    dataset_info = metadata(dataset) | {
        "evaluated_profiles": n, "candidate_pairs": sum(counts), "mean_candidates": float(np.mean(counts)),
        "profiles_with_no_candidates": counts.count(0), "profiles_with_no_relevant_items": relevant_counts.count(0),
    }
    sensitivity /= n
    payload = {
        "dataset": dataset_info,
        "weights": matching.WEIGHTS,
        "methodology": {
            "label_source": "Synthetic proxy labels",
            "threshold": THRESHOLD, "gain": "linear grade (0–3)",
            "aggregation": "Macro-average over all profiles. Precision divides by K. Empty ideal DCG and zero relevant candidates yield zero.",
            "candidate_policy": "Same sport, active deadline and one-year age tolerance; identical pool for all methods.",
            "bootstrap_resamples": BOOTSTRAP_TRIALS, "random_shuffles_per_profile": RANDOM_TRIALS, "seeds": SEEDS,
        },
        "semantic_status": "evaluated" if "sentence_bert" in results else "encoding_failed" if semantic_failed
        else "unavailable" if semantic is None else "no_candidates",
        "models": [{"id": key, "name": METHODS[key], **results[key]} for key in METHODS if key in results and key != "equal"],
        "ablations": [
            {"id": key, "name": ("Full TF-IDF" if key == "tfidf" else METHODS[key] if key in METHODS
                                else f"Without {key.removeprefix('without_')}"), **results[key],
             "delta_ndcg10": results[key]["metrics"]["NDCG@10"] - results["tfidf"]["metrics"]["NDCG@10"]}
            for key in ("tfidf", *variants)
        ],
        "paired_tfidf_minus_filter": paired,
        "paired_sentence_bert_minus_tfidf": semantic_paired,
        "score_distribution": [{"range": f"{lo}–{hi}", "count": int(count)}
                               for count, lo, hi in zip(distribution, edges[:-1], edges[1:], strict=True)],
        "weight_sensitivity": {"samples": WEIGHT_TRIALS, "min": float(sensitivity.min()),
                               "median": float(np.median(sensitivity)), "max": float(sensitivity.max()),
                               "fraction_below_default": float(np.mean(sensitivity < results["tfidf"]["metrics"]["NDCG@10"]))},
    }
    return payload


def draw_plots(payload, directory):
    directory.mkdir(exist_ok=True)
    plt.rcParams.update({"figure.dpi": 145, "axes.spines.top": False, "axes.spines.right": False})

    def save(fig, name):
        fig.tight_layout()
        fig.savefig(directory / f"{name}.png", bbox_inches="tight", facecolor="white")
        plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 3.6))
    models = payload["models"]
    positions = np.arange(len(models))
    for shift, key, color in [(-0.18, "NDCG@5", "#458c78"), (0.18, "NDCG@10", "#14674d")]:
        means = np.array([row["metrics"][key] for row in models])
        bounds = np.array([row["ci95"][key] for row in models]).T
        ax.bar(positions + shift, means, 0.34, yerr=np.abs(bounds - means), capsize=3, color=color, label=key)
    ax.set_xticks(positions, [model["name"] for model in models])
    ax.set_ylim(0, 1)
    ax.set_title("Ranking quality on a shared candidate pool")
    ax.legend(frameon=False)
    save(fig, "model_comparison")

    fig, ax = plt.subplots(figsize=(8, 4))
    variants = list(reversed(payload["ablations"][1:]))
    deltas = [row["delta_ndcg10"] for row in variants]
    ax.barh([row["name"] for row in variants], deltas, color=["#14674d" if value >= 0 else "#a75043" for value in deltas])
    ax.axvline(0, color="#303834", linewidth=1)
    ax.set_xlabel("Change in NDCG@10 from full TF-IDF")
    save(fig, "ablation_study")

    fig, ax = plt.subplots(figsize=(8, 3.5))
    bins = payload["score_distribution"]
    ax.bar([row["range"] for row in bins], [row["count"] for row in bins], color="#14674d")
    ax.set(xlabel="Compatibility score", ylabel="Candidate pairs", title="TF-IDF compatibility scores")
    save(fig, "score_distribution")

    fig, axes = plt.subplots(1, 2, figsize=(10, 3.6))
    data = payload["dataset"]
    for ax, key, title in zip(axes, ("athletes_by_sport", "opportunities_by_type"), ("Athletes by sport", "Opportunities by type"), strict=True):
        ax.barh(list(data[key]), list(data[key].values()), color="#14674d")
        ax.set_title(title)
    save(fig, "dataset_distribution")


def format_table(rows):
    header = "| Method | " + " | ".join(METRICS) + " |"
    divider = "|---|" + "---:|" * len(METRICS)
    values = [f"| {row['name']} | " + " | ".join(f"{row['metrics'][key]:.4f}" for key in METRICS) + " |" for row in rows]
    return "\n".join([header, divider, *values])


def write_artifacts(payload, directory):
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "results.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    for name, rows in (("baseline_comparison", payload["models"]), ("ablation_results", payload["ablations"]),
                       ("metrics", payload["models"] + payload["ablations"][1:])):
        pd.DataFrame([{"method": row["id"], "name": row["name"], **row["metrics"],
                       **({"delta_ndcg10": row["delta_ndcg10"]} if "delta_ndcg10" in row else {})}
                      for row in rows]).to_csv(directory / f"{name}.csv", index=False, float_format="%.6f")
    draw_plots(payload, directory / "plots")
    stats = payload["dataset"]
    paired = payload["paired_tfidf_minus_filter"]
    ci = paired["ci95"]["NDCG@10"]
    semantic_paired = payload["paired_sentence_bert_minus_tfidf"]
    semantic_comparison = ""
    if semantic_paired:
        difference = semantic_paired["metrics"]["NDCG@10"]
        low, high = semantic_paired["ci95"]["NDCG@10"]
        semantic_comparison = (f"\n\nThe paired Sentence-BERT minus TF-IDF NDCG@10 difference is "
                               f"{difference:+.4f} with a 95% interval from {low:+.4f} to {high:+.4f}.")
    ablations = payload["ablations"][1:-1]
    biggest_drop = min(ablations, key=lambda row: row["delta_ndcg10"])
    biggest_gain = max(ablations, key=lambda row: row["delta_ndcg10"])
    sensitivity = payload["weight_sensitivity"]
    n = stats["evaluated_profiles"]
    prose = f"""# Ground Up ranking evaluation

All numbers were generated by this runner. The {n} synthetic profiles share candidate pools across methods. There were {stats['candidate_pairs']:,} candidate pairs, {stats['profiles_with_no_candidates']} profiles with no candidates and {stats['profiles_with_no_relevant_items']} profiles without a grade of 2 or 3 in their pool.

## Baselines and model comparison

{format_table(payload['models'])}

The paired TF-IDF minus filter-only NDCG@10 difference is {paired['metrics']['NDCG@10']:+.4f} with a 95% athlete bootstrap interval from {ci[0]:+.4f} to {ci[1]:+.4f}. Sentence-BERT status is `{payload['semantic_status']}`.{semantic_comparison}

## Ablation and sensitivity

{format_table(payload['ablations'])}

The lowest removal result is {biggest_drop['name'].lower()} ({biggest_drop['delta_ndcg10']:+.4f} NDCG@10). The highest removal result is {biggest_gain['name'].lower()} ({biggest_gain['delta_ndcg10']:+.4f}). Across {sensitivity['samples']} Dirichlet weight vectors, median NDCG@10 is {sensitivity['median']:.4f}, with a range of {sensitivity['min']:.4f}–{sensitivity['max']:.4f}. These experiments measure dependence on the proxy labels. The app keeps the report's design weights.

## Protocol and limitations

- Filter-only orders by nearest deadline, with rolling deadlines last and ID for ties. Random averages {RANDOM_TRIALS} shuffles per athlete. The recommender breaks score ties by ID.
- Precision divides by K even for short lists. Recall uses all the eligible grade 2–3 items for the athlete. NDCG uses the grade as linear gain and log2(rank + 1) discount. Zero denominators contribute zero. Averages weight all athletes equally.
- Bootstrap intervals resample whole athletes {BOOTSTRAP_TRIALS:,} times. They describe variation within this synthetic design.
- Labels are rule-based proxies with structured intent and travel preference. Their assumptions can favor or penalize specific scoring features. Independent human ratings and a representative sample of real opportunities are future work.

![Model comparison](plots/model_comparison.png)
![Ablation study](plots/ablation_study.png)
![Score distribution](plots/score_distribution.png)
![Dataset distribution](plots/dataset_distribution.png)
"""
    (directory / "evaluation_report.md").write_text(prose, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "evaluation")
    parser.add_argument("--sentence-bert", metavar="MODEL", nargs="?", const="sentence-transformers/all-MiniLM-L6-v2")
    args = parser.parse_args()
    semantic = matching.semantic_encoder(args.sentence_bert) if args.sentence_bert else None
    payload = evaluate(make_dataset(), semantic)
    if not args.sentence_bert:
        payload["semantic_status"] = "not_requested"
    write_artifacts(payload, args.output)
    print(format_table(payload["models"]))


if __name__ == "__main__":
    main()
