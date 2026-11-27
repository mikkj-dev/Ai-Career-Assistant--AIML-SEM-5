# Requirements traceability

The root M2 HTML and the copy in Report have identical SHA-256 hashes. M2 describes the static frontend milestone. The 45-page CSET312 PDF describes a later prototype. Its figures include the architecture, pipeline, evaluation workflow, use cases, classes, ER relationships, desktop and mobile screens and historical experiments. The starting checkout had the API scaffold and a standalone frontend mock layer. The evaluation runner and supporting artifacts referenced by the PDF were absent.

| Requirement | Report reference | Existing implementation | Missing work | Verification | Status |
|---|---|---|---|---|---|
| Discover fitting sports opportunities and explain the rank | M2 §§1–4, PDF §§1–2 | Feed and gallery, basic matcher | Integrate the gallery and API with real profile state | Desktop Playwright uses actual API and PostgreSQL | Verified |
| Capture and edit athlete features in professional and casual modes | PDF §§3.3, 3.5–3.6 | Profile form and update route | Persist normalized features, confirm reranking | PostgreSQL profile tests and desktop profile edit | Verified |
| Local login and identity privacy | PDF §§3.3, 3.6 | Google adapter, arbitrary-email developer session, pending verification request | Seeded demo login, role enforcement and production guard | JWT and access control tests, browser switches accounts | Verified for local scope |
| Deterministic athlete and opportunity data | PDF §3.3, Table 7 | Opportunity seed replaced all synthetic postings | Export 200 athletes, 300 opportunities, organisation/post fixtures, stable IDs and targeted reset | Byte-reproducibility, count, relationship and reset tests | Verified |
| Public athlete data and independent relevance assessment | M2 §3, PDF §§3.7.7, 4.3 | No licensed real records or human ratings in the checkout | Evaluate source suitability and supply blank annotation template | Dataset guide and template | Public data reviewed; human and real-data validation open |
| Hard filtering and six weighted components | PDF §3.3, Table 6, M2 §4 and PRD §6 | Sport/age filter and 93.5 regression | Deadline, tolerance status, normalization, shared corpus and explanations | Component suite, API age test and browser breakdown | Verified |
| Sentence-BERT goals/description comparison | M2 §§4, 6, PDF §4.3 | TF-IDF only | Optional local CPU model, caching and fallback | Executed CPU benchmark and fallback tests | Verified |
| Precision, Recall and NDCG at 5 and 10 | PDF §§3.7.2–3.7.3 | Historical PDF numbers | Rerun with common candidates, 0–3 relevance and bootstrap intervals | Generated CSV, JSON, plots and dashboard | Verified |
| Ablations and weight sensitivity | PDF §§3.7.4–3.7.5 | Historical PDF tables and plots | Six renormalized variants, equal weights and 300 samples with mandatory filters | Generated study and dashboard | Verified |
| Organisation posts and athlete application | PDF §§3.4, 4.3 | Team role and disabled Apply button | Posting ownership, database uniqueness and application history/inbox | Concurrent submissions, cross-org access, browser refresh and API restart | Verified |
| Social posts and suggested athletes | PDF §§3.3, 3.5 | API and page existed with mock fallback | Serve current stored data and surface failures | API post and suggestions test, live dashboard | Verified |
| Local setup, portability and documentation | PDF §§3.6–4 | Compose and hosted configuration | Build, seed, evaluate, test and complete submission materials | Test report, final report, viva and screenshots | Verified locally |
| Google OAuth, real KYC and hosted scale | PDF §§3.6, 4.3 and original architecture | Configurable Google and example hosting blueprint | Requires configured credentials and separate production work | Production demo guard tested; local core independent of cloud | Hosted features unverified; KYC and scale future work |
| Optional supervised re-ranking | M2 §4, PDF §4.3 | No trained ranker | Needs independent labels and held-out evaluation | Synthetic proxy labels only | Deferred by design |

## Decisions

- The later PDF specifies 200 athletes and 300 opportunities, which take precedence over the suggested smaller count. Five sports, 15 organisations and 50 posts extend that setup. The public football source reviewed supplies events and lineups rather than the profile and preference fields needed here.
- The benchmark uses requested integer grades 0–3 with threshold 2. It keeps all profiles in the averages and applies the same candidate pool to random, filter-only and weighted methods. The historical PDF compared random across all openings, used a different grade scale and excluded profiles without relevant items. Its numerical results remain historical.
- The one-year discovery tolerance stays in force. Strict-age postings block a tolerance-band application. Unknown age remains explicit where a posting has a range.
- The 93.5 number is the historical hand calculation, reproduced by regression test. The current benchmark results are generated from the checked-in runner and fixtures.
- The app uses TF-IDF for the default demo. The optional CPU model produced a genuine comparison. The original gallery and supplied reports are preserved.
