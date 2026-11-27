# Ground Up product requirements

Ground Up helps athletes discover relevant trials, scholarships, tournaments, scout showcases, clubs, training camps and development programmes. The M2 milestone and the later CSET312 report define the academic scope. The final demo uses the existing Next.js gallery, FastAPI and PostgreSQL.

## Problem and users

Athletes often find opportunities through local networks, social posts and word of mouth. Searching by sport or location leaves each athlete to judge position, skills, age and experience manually. Organisations face the same problem when reviewing applications from people who may not meet their requirements.

Professional and casual athletes maintain structured profiles, see suggested athletes, publish to the feed and submit applications. Authorised organisation accounts publish opportunities and see applications to their own listings. The score describes compatibility with stated requirements and has no role in guaranteeing selection.

## Local acceptance requirements

| ID | Capability | Acceptance |
|---|---|---|
| F1 | Authentication | Seeded fictional accounts sign in without external credentials. Production permits configured Google authentication and rejects demo sessions. |
| F2 | Identity request | Store document type and pending status only. |
| F3 | Profile | Create and edit mode, sport, position, age, location, level, skills, goals and bio. Profile updates change API recommendations. |
| F4 | Feed and people | List stored posts, publish a new post and suggest similar same-sport profiles. |
| F5 | Opportunity discovery | Browse active postings and filter and sort recommendations. Explore detail and a six-component explanation in the existing gallery. |
| F6 | Application | Apply with valid sport, deadline and age eligibility. A database constraint prevents duplicates. Show persisted history and the organisation inbox. |
| F7 | Organisation | Authorised teams create postings. Ownership determines access to applications. |
| F8 | Evaluation | Serve measured P@5/10, R@5/10 and NDCG@5/10 for random, filter-only, weighted TF-IDF and optional Sentence-BERT. Provide six renormalized ablations and sensitivity analysis. |
| F9 | Reproducibility | Compose, Alembic, fixed-seed dataset export, targeted demo reset, locked dependencies and browser verification. |

## Matching policy

Use same-sport, active-deadline candidates within the one-year tolerance. Mark tolerance results and unknown ages explicitly. Organisations can enforce hard age limits for applications. The score uses 25% position, 30% skills, 15% age, 10% location, 10% experience and 10% goals. Each result reports the text method, overlap, weak factors and eligibility. The illustrative component calculation gives 93.5.

## Research scope

The later PDF specifies 200 synthetic athletes and 300 synthetic opportunities. The final experiment adds organisations, posts and badminton and grades every athlete/posting pair on a 0–3 scale. Random and all other methods use a shared candidate pool. NDCG@10 is primary. Human relevance assessment, verified real data, supervised reranking, collaborative filtering, phone OTP and real KYC remain future work.

[Requirements traceability](docs/REQUIREMENTS_TRACEABILITY.md) · [Architecture](ARCHITECTURE.md) · [Research methods](docs/ML_METHODOLOGY.md) · [Known limitations](docs/KNOWN_LIMITATIONS.md)
