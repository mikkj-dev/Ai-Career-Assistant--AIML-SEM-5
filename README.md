# Ground Up

Ground Up helps athletes discover academy trials, scholarships, tournaments, scout showcases, clubs, training camps and development programmes. The recommender ranks open opportunities using sport and age eligibility and six compatibility components, then explains the result. Compatibility measures how well the profile fits the stated requirements.

**CSET312 AIML Semester 5 mini-project**

Parikshit Dagar and Mehul Jakhmola · Guide Dr. Mala Saraswat · Bennett University

## Run the local demo

With Docker Desktop running, execute these commands from the repository root.

```powershell
docker compose up --build -d --wait
docker compose exec api python -m app.seed
Set-Location web
npm ci
npm run dev
```

Open [Ground Up](http://localhost:3000), then choose **Football athlete**. Pick **Organisation administrator** to publish opportunities and see incoming applications. [API documentation](http://localhost:8001/docs) and the [ML evaluation dashboard](http://localhost:3000/evaluation) are available locally.

The offline benchmark covers 200 fictional athletes, 300 opportunities, 15 organisations and 50 posts. It includes an executed CPU Sentence-BERT comparison. The app runs TF-IDF by default, with no model download, Google login or paid service needed for the demo.

- [Setup and test commands](docs/SETUP.md)
- [Five-minute demo](docs/DEMO_GUIDE.md)
- [Final project report](docs/FINAL_PROJECT_REPORT.md)
- [Generated evaluation report](evaluation/evaluation_report.md)
- [Requirements and verification](docs/REQUIREMENTS_TRACEABILITY.md)
- [Test evidence](docs/TEST_REPORT.md)
- [Viva preparation](docs/VIVA_PREPARATION.md)

Original reports are in [Report/](Report/) and the root M2 HTML. The current experiment uses a shared candidate pool and compares methods under a different protocol from the historical PDF.
