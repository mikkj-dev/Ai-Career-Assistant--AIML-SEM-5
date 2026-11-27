# Viva preparation

| Question | Concise answer |
|---|---|
| Why content-based recommendation? | Each profile and posting already has useful attributes. The system can personalize recommendations as soon as the athlete fills in a profile. |
| What makes this AI/ML? | It extracts sparse text and skill vectors, computes cosine similarity, ranks eligible items and evaluates the ranks against a separate set of relevance labels. It also compares pretrained sentence embeddings with TF-IDF. |
| How does TF-IDF work? | Term frequency measures how much a term occurs in a description. Inverse document frequency reduces the influence of terms common throughout the corpus. The same fitted vocabulary transforms the athlete query. |
| How does cosine similarity work? | Divide the dot product by the product of the vector lengths. For binary skill vectors, the numerator is the number of shared skills. |
| How does Sentence-BERT differ? | It maps a sentence to a dense semantic vector using a pretrained encoder. That can give similar vectors to paraphrases with different words. Both methods use cosine in this project. |
| Why weighted scoring? | It expresses the design priorities in an inspectable equation. An athlete can see how each factor contributes and which factors are weaker. |
| What is cold start? | A new platform or user has too little interaction data to build behavior-based recommendations. A structured profile and posting attributes are sufficient to start content matching. |
| Why skip collaborative filtering? | Meaningful collaborative signals require enough real athlete actions and item interactions. The synthetic demonstration does not supply those signals. |
| What are Precision@K and Recall@K? | Precision divides relevant results in the top K by K. Recall divides those hits by the total number of relevant candidates for that athlete. Grades 2 and 3 count as relevant. |
| What is NDCG? | Add each relevance grade divided by log2(rank + 1), then divide by the best possible ordering at the same cut-off. Strong results count more near the top. |
| What is an ablation? | Remove one component of the score, redistribute its weight proportionally and measure the change with all eligibility gates fixed. This shows dependence on that component under the benchmark rubric. |
| Why synthetic data? | Real structured multi-sport opportunity postings and athlete preference-to-posting judgments were unavailable. Fictional fixtures permit repeatable tests and avoid collecting personal data. |
| What limits the labels? | The rule tree encodes assumptions about goal intent, travel and readiness. It can favor certain features, and a synthetic grade is no evidence of enrolment or success. |
| Does the matcher train? | The TF-IDF vocabulary and document frequencies are fitted without labels. The weights are fixed design choices and MiniLM is pretrained. There is no supervised reranker. |
| What happens after a profile edit? | PostgreSQL stores the new features. The next recommendation request rebuilds eligibility and scoring against the current profile. A change to position, skills, city or goals can change both scores and order. |
| Is 93.5 a measured result? | It is the report’s hand-calculated score for six illustrative component values. The experimental results are separate aggregate rankings. |
| Did Sentence-BERT improve performance? | It had the highest NDCG@10 among the four primary methods on this run by a small margin over TF-IDF. The study is synthetic and describes compatibility ranking. |
| Does the score claim talent or selection? | It measures the fit of available profile features to a posting’s declared requirements. Selection is the organisation’s decision. |
