# Recommendation and evaluation methodology

## Input and eligibility

The API validates field lengths, sport/position combinations, age bounds and ordered age ranges. Text and categories use Unicode normalization, case folding, whitespace collapse and aliases for common position and skill spellings. Skills are represented by a binary vector over the union of normalized skill terms. Experience has five ordered categories from beginner to professional.

Posting candidates must match the sport and have an open deadline. The documented age tolerance allows discovery one year outside either bound. A result in that band has an age score of 0.5 and carries a tolerance label. Applications require strict age fit for postings that enforce their range. Unknown age is flagged on age-constrained postings and prevents applying until supplied.

## Six components

| Component | Weight | Calculation |
|---|---:|---|
| Position | 0.25 | 1 for an exact match or open positions, 0.6 for a recognized related position, 0 otherwise |
| Skills | 0.30 | Binary cosine equals shared count divided by the geometric mean of skill-set sizes. Unspecified requirements score 1. |
| Age | 0.15 | 1 for the strict range or an unrestricted posting, 0.5 for missing age with constraints or tolerance matches |
| Location | 0.10 | 1 for the same city or open/online, 0.6 for the same region, 0.2 otherwise |
| Experience | 0.10 | 1 for matching levels or an unspecified requirement, 0.6 for a gap of one, 0.2 for a larger gap, 0.5 when required data is missing |
| Goals | 0.10 | TF-IDF cosine or clipped Sentence-BERT cosine. Missing text scores 0.5. Nonempty text with no comparable TF-IDF terms scores 0. |

```text
Score = 100 × (0.25 Position + 0.30 Skills + 0.15 Age
             + 0.10 Location + 0.10 Experience + 0.10 Goals)
```

The app rounds skill and goal components to three decimals, then the score to one decimal, and breaks ties by opportunity ID. The report's worked example substitutes 1.00, 0.85, 1.00, 1.00, 1.00 and 0.80 and gives 100 × (0.25 + 0.255 + 0.15 + 0.10 + 0.10 + 0.08) = 93.5. Explanations use the same factors, show overlapping and missing skills, and identify eligibility and weak evidence.

TF-IDF fits a shared vocabulary of words and two-word phrases from active descriptions. The athlete query is transformed in that same vector space. The cached corpus stays fixed when an athlete changes their age, sport, goals or list filters. Posting changes and closed deadlines can change the reference corpus. Sentence-BERT is loaded lazily on CPU from a local MiniLM snapshot. It caches normalized opportunity embeddings and changes only the goal component. Negative cosine values are clipped to zero. Check the per-result method to distinguish fallback from semantic ranking.

## Evaluation

Random, deadline-ordered filter-only, weighted TF-IDF and weighted Sentence-BERT see the same eligible items for every athlete. Random averages 50 fixed-seed shuffles. Labels are independent decision-tree proxies defined in the [dataset guide](DATASET.md). They include travel and intent criteria that the matcher does not directly receive. Grades 2 and 3 count as relevant for binary metrics.

Precision@K divides retrieved relevant items by K, including for short lists. Recall@K divides by the total number of relevant opportunities in that candidate pool. NDCG uses the 0–3 grade as linear gain and discounts position i by log2(i+1). Its denominator is the ideal ranking of that pool. Missing ranks contribute zero. An empty relevant set or zero ideal gain contributes zero to the affected metric. Macro-averages include every athlete. NDCG@10 is primary. Bootstrap intervals resample whole athletes 2,000 times with fixed seeds.

For each ablation, zero one weight and normalize the remainder. Sport, deadline checks and the age tolerance all stay active. Equal weights and 300 Dirichlet weight samples evaluate sensitivity. The benchmark uses the design weights in the app and avoids tuning them against the same proxy labels used for testing.

[Executed results and plotted evidence](../evaluation/evaluation_report.md) · [Setup for CPU Sentence-BERT](SETUP.md#optional-cpu-sentence-bert-experiment)
