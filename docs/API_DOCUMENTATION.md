# Ground Up API

The base URL is `http://localhost:8001`. FastAPI publishes [OpenAPI documentation](http://localhost:8001/docs). Protected requests use `Authorization: Bearer <token>`. Match scores describe fit to a listing, and the service checks application eligibility again at submission.

| Method and path | Access | Behavior |
|---|---|---|
| GET /health, GET /ready | Public | Process liveness and migrated database readiness |
| GET /catalog | Public | Sports with valid positions, opportunity types and levels |
| GET /demo/info | Public | Enabled flag and seeded local account choices |
| POST /auth/demo | Local development only | Accepts an account ID such as `football`. Returns token and user. |
| POST /auth/google | Configured Google identity | Exchanges verified Google credential for a user session |
| GET /me | Signed in | Account and athlete profile |
| PUT /me/profile | Athlete | Create or update profile. Omitted fields retain their values. |
| POST /me/verification | Signed in | Accepts only a document type and records a pending request |
| GET /opportunities | Public | Browse active listings. Optional sport, type, limit and sort by deadline or newest. |
| GET /opportunities/recommended | Signed in | Returns ranked matches for the athlete profile. K is 1–100. |
| GET /opportunities/{id} | Public | Listing detail. With an athlete token, adds personalized match, eligibility and existing application. |
| POST /opportunities | Authorised organisation | Creates a listing owned by the caller and returns HTTP 201 |
| POST /opportunities/{id}/apply | Athlete | Creates one application and returns HTTP 201 |
| GET /me/applications | Athlete | Caller’s application history |
| GET /organisation/opportunities | Authorised organisation | Listings owned by the caller |
| GET /organisation/applications | Authorised organisation | Applications to the caller’s listings |
| GET /posts | Public | Latest posts, optionally before a timestamp |
| POST /posts | Signed in | Creates a post and returns HTTP 201 |
| GET /people/suggested | Signed in | Same-sport athletes ranked using skills and city |
| GET /evaluation/model | Public | Live configured and loaded default text method and weights |
| GET /evaluation/results | Public | Executed offline benchmark JSON |
| GET /evaluation/plots/{name} | Public | One of the four plotted artifacts used by the dashboard |

Recommendation records include `compatibility_score` and the older `score` alias, `components`, `reasons`, `matching_skills`, `missing_skills`, `eligibility`, `can_apply` and `similarity_method`. The optional semantic encoder can fall back during a request. The method on each match records what that request used.

The existing `/auth/dev` path accepts the same seeded selector payload as `/auth/demo`. Arbitrary email sign-in and self-assigned roles were removed. Demo accounts have no password and work only with `ENV=development` and `DEMO_ENABLED=true`. Production rejects demo-issued tokens.

HTTP 401 indicates a missing or invalid token. HTTP 403 indicates insufficient role or ownership. HTTP 404 covers unavailable records and disabled demo endpoints. HTTP 409 indicates already applied or a failed eligibility check. HTTP 422 identifies invalid payloads and missing profile requirements. HTTP 503 indicates missing demo fixtures, Google configuration or evaluation artifacts where applicable.

The duplicate-application constraint is enforced by PostgreSQL. Concurrent submissions to the same listing produce one application. Identity request inputs forbid document numbers and any other undeclared fields.
