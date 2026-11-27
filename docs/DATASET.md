# Synthetic dataset

Ground Up generates fictional athletes, organisations, postings and social posts. The 200 athlete and 300 opportunity counts follow the later CSET312 report. The project adds a fifth sport, three posting types, ownership and social examples for the live demonstration.

| File | Records | Contents |
|---|---:|---|
| athletes.csv | 200 | Sport, valid position-specific skills, age, region, city, experience, goals, bio and mode |
| opportunities.csv | 300 | Organisation, posting type, sport, requirements, description and optional deadline |
| organisations.csv | 15 | Three fictional organisations per sport |
| posts.csv | 50 | Fictional training updates linked to athlete IDs |
| relevance_labels.csv | 60,000 | One integer grade and rationale for every athlete/opportunity pair |

The athlete seed is 7 and the opportunity seed is 42. Football, cricket, basketball, athletics and badminton each have 60 postings. Athlete sport and experience distributions are in [metadata.json](../data/metadata.json). The first four athlete fixtures support the demo selector. A separate blank demo account onboards a new profile and is excluded from the benchmark. Skills are sampled from position-specific lists. The generator includes open positions, near age matches, expired listings, rolling deadlines, different cities and regions, profiles with no available candidates, partially overlapping skills, and distinct wording for the same career intent.

CSV IDs are stable. PostgreSQL uses namespaced UUIDv5 fixture IDs. Array cells use JSON, blank fields are null and the synthetic indicator is always true. The experiment fixes time to 2026-10-01 UTC. Database seeding rebases deadline offsets to the current UTC time so time-sensitive examples work at the demo. Ordinary seeding preserves existing deadlines and edits.

## Relevance

Grading follows a decision tree. Wrong sport, closed deadlines and ages outside the stated range receive 0. Each remaining pair is assessed using separately generated intent and travel flexibility, exact or open role, minimum readiness, and the presence of an entry skill. Grade 3 requires the target career pathway and all readiness/access checks. Grade 2 represents an accessible target or credible alternate pathway. Grade 1 reflects an exploratory option with a barrier. These are synthetic proxy labels. The rubric does not use cosine similarity, matcher scores, component weights or distance-based experience similarity.

The [annotation template](../data/human_annotation_template.csv) provides a starter sample including ambiguous and adverse cases. Show an annotator the profile and posting, omit algorithm output and proxy labels, and ask for a 0–3 grade plus the decisive reason. Compare independently assigned grades before adjudicating disagreements. No human ratings were collected for this run.

## Public data review

The M2 report proposed public player attributes if licensing allowed. The later PDF deliberately used a fully synthetic benchmark. StatsBomb publishes football lineups and match event data under its public data terms, with attribution and logo requirements for shared analysis. Its published structure does not supply the multi-sport athlete profiles, career goals and opportunity relevance annotations this prototype needs. This project includes zero real player or opportunity records. [StatsBomb data and terms](https://github.com/hudl/open-data)

Synthetic profiles and postings simplify readiness, age and travel constraints and cannot establish real-world relevance, fairness or selection outcomes.
