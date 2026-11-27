# Five-minute demonstration

Start Compose, seed the database and run the web app using the [setup guide](SETUP.md). If a previous practice run used the football athlete, run `docker compose exec api python -m app.seed --reset-demo` first. Use [localhost:3000](http://localhost:3000).

| Time | Action | What to show |
|---|---|---|
| 0:00–0:45 | Select **Football athlete**. | Show the profile, skills, goal, ranked upcoming opportunities and connections. The profile belongs to a fictional account. |
| 0:45–1:35 | Open **Opportunities** and **Football academy trial · Juniperline 001**. | Read the computed score, six component values, skill overlap and goals method. Explain discovery near the age boundary and the strict application rule. |
| 1:35–2:35 | Select **Edit athlete profile**. Change position to **Winger**, skills to `dribbling, pace, crossing`, and goals to `I want an academy trial for wide attackers with crossing, dribbling, and pace.` Save. | Compare the first result and score to the previous list. The same API reranks when profile fields change. |
| 2:35–3:15 | Open **Football academy trial · Juniperline 016**, then click **Apply**. Open **Applications** and refresh the page. | The application remains submitted. |
| 3:15–4:00 | Sign out and select **Organisation administrator**. | Find the application under **Received applications**. If time permits, publish a fictional development posting. |
| 4:00–5:00 | Open **Evaluation**. | Show NDCG as the primary metric, shared candidate pools, the semantic comparison, and the location and skills ablations. Explain how proxy labels shape the findings. |

The accounts are selectors, so there is no email or password to enter.

| Selector | Seeded identity |
|---|---|
| Football athlete | 19-year-old central midfielder in Delhi |
| Cricket athlete | 18-year-old bowler in Pune |
| Basketball athlete | 20-year-old point guard in Kochi |
| Athlete with no eligible opportunities | 56-year-old athletics thrower |
| Organisation administrator | Juniperline Eleven Collective |
| Start a new athlete profile | Fictional account with no profile until onboarding is saved |

Use the no-eligible account to demonstrate the empty state, then browse active opportunities across sports. The default live text method is TF-IDF. The evaluation dashboard includes the previously executed CPU experiment.
