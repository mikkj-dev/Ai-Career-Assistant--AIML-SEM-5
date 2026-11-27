# Known limitations

- The benchmark uses fictional athletes, organisations and postings and independently defined proxy grades. Independent human annotations and validation on representative real data remain open.
- Location, age, role, experience and skill assumptions influence rank and proxy labels. The ablations measure behavior within this benchmark. They provide no fairness audit or evidence of athlete outcomes.
- Fixed score weights follow the reports. Equal weights perform better on this proxy task. A change to the live weights would require validation on independent data.
- TF-IDF can miss paraphrases. The local CPU Sentence-BERT experiment requires an optional model download and greater memory. The default demo uses TF-IDF and includes executed semantic results.
- The API scores up to 500 candidates after filtering. The demo gallery requests up to 100 results. Feed ordering is chronological and connection suggestions are same-sport.
- Local demo accounts are shared fixtures, with no password. Local resets restore the seeded profiles and selected application records. Fresh production environments require a separate database and Google configuration.
- Recorded identity requests stay pending. Real identity checking, phone sign-in, account messaging and follow graph features remain future work.
- The web stores a short-lived signed session in a JavaScript-readable SameSite cookie to send as a Bearer token. A shared-domain or backend-for-frontend deployment could use an HttpOnly session. Hosted hardening and load testing are outside this local demonstration.
- Hosting configuration is retained for Render and Vercel. No hosted instance or paid infrastructure was provisioned.
