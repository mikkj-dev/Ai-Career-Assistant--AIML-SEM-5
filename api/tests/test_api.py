import os
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker
from sqlalchemy.schema import CreateSchema, DropSchema

from app import db as database
from app.auth import issue_token
from app.config import settings
from app.dataset import fixture_id, make_dataset
from app.main import app
from app.models import Application, Opportunity, Post, User
from app.seed import seed_db


@pytest.fixture(scope="module")
def postgres_sessions():
    url = os.environ.get("GROUNDUP_TEST_DATABASE_URL")
    if not url:
        pytest.skip("Set GROUNDUP_TEST_DATABASE_URL to run isolated PostgreSQL integration tests")
    schema = f"groundup_test_{uuid4().hex}"
    admin = create_engine(url)
    with admin.begin() as connection:
        connection.execute(CreateSchema(schema))
    engine = create_engine(make_url(url).update_query_dict({"options": f"-csearch_path={schema}"}))
    try:
        database.Base.metadata.create_all(engine)
        yield sessionmaker(engine, expire_on_commit=False)
    finally:
        engine.dispose()
        with admin.begin() as connection:
            connection.execute(DropSchema(schema, cascade=True))
        admin.dispose()


@pytest.fixture
def client(postgres_sessions, monkeypatch):
    monkeypatch.setattr(settings, "env", "development")
    monkeypatch.setattr(settings, "demo_enabled", True)
    monkeypatch.setattr(database, "SessionLocal", postgres_sessions)
    seed_db(make_dataset(), reset=True)
    with TestClient(app) as result:
        yield result


def sign_in(client, identity):
    response = client.post("/auth/demo", json={"account": identity})
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['token']}"}


def test_authentication_and_production_boundary(client, monkeypatch):
    assert client.get("/me").status_code == 401
    assert client.get("/me", headers={"Authorization": "Bearer invalid"}).status_code == 401
    assert client.post("/auth/dev", json={"email": "unrelated@example.org"}).status_code == 422
    athlete = sign_in(client, "football")
    assert client.get("/me", headers=athlete).json()["synthetic"]
    assert client.get("/demo/info").json()["enabled"]
    monkeypatch.setattr(settings, "env", "production")
    assert client.get("/demo/info").json() == {"enabled": False, "accounts": []}
    assert client.post("/auth/demo", json={"account": "organisation"}).status_code == 404
    assert client.get("/me", headers=athlete).status_code == 401


def test_create_update_and_persist_profile(client):
    athlete = sign_in(client, "new")
    assert client.get("/me", headers=athlete).json()["profile"] is None
    assert client.post("/me/verification", headers=athlete, json={
        "doc_type": "passport", "document_number": "unused",
    }).status_code == 422
    created = client.put("/me/profile", headers=athlete, json={
        "sport": "  FOOTBALL ", "position": "Full-back", "age": 19, "skills": [" Passing ", "passing"],
    })
    assert created.status_code == 200, created.text
    assert created.json()["profile"]["skills"] == ["passing"]
    assert client.put("/me/profile", headers=athlete, json={"role": "team"}).status_code == 422
    assert client.put("/me/profile", headers=athlete, json={"position": "batter"}).status_code == 422
    assert client.put("/me/profile", headers=athlete, json={"sport": "cricket", "skills": None}).status_code == 200
    profile = client.get("/me", headers=athlete).json()["profile"]
    assert profile["position"] is None and profile["skills"] == [] and profile["age"] == 19


def test_recommendations_change_with_features_and_mark_age(client):
    athlete = sign_in(client, "football")
    path = "/opportunities/recommended?k=100"
    before = client.get(path, headers=athlete).json()
    assert before[0]["opportunity"]["id"] == str(fixture_id("p001"))
    assert all(0 <= row["score"] <= 100 and row["similarity_method"] == "tfidf" for row in before)
    near = next(row for row in before if row["opportunity"]["id"] == str(fixture_id("p031")))
    assert near["eligibility"] == "age_tolerance" and not near["can_apply"]
    assert near["components"]["age"] == 0.5
    assert str(fixture_id("p046")) not in {row["opportunity"]["id"] for row in before}
    assert client.put("/me/profile", headers=athlete, json={
        "position": "winger", "skills": ["dribbling", "pace", "crossing"], "goals": "wide attackers academy trial",
    }).status_code == 200
    after = client.get(path, headers=athlete).json()
    assert after[0]["opportunity"]["id"] != before[0]["opportunity"]["id"]
    assert client.get(path, headers=sign_in(client, "limited")).json() == []


def test_application_persistence_roles_and_concurrent_duplicates(client, postgres_sessions):
    athlete = sign_in(client, "football")
    org = sign_in(client, "organisation")
    payload = {"title": "Verification trial", "type": "trial", "sport": "football",
               "description": "An organised academy trial for district players.", "age_min": 17, "age_max": 22}
    assert client.post("/opportunities", headers=athlete, json=payload).status_code == 403
    assert client.post("/opportunities", headers=org, json=payload | {"age_min": 25}).status_code == 422
    created = client.post("/opportunities", headers=org, json=payload)
    assert created.status_code == 201, created.text
    opportunity = created.json()
    assert opportunity["synthetic"]
    path = f"/opportunities/{opportunity['id']}"
    assert client.get(path, headers=athlete).json()["eligibility"] == "strict"
    assert client.post(f"{path}/apply", headers=org).status_code == 403
    with ThreadPoolExecutor(max_workers=2) as executor:
        statuses = list(executor.map(lambda _: client.post(f"{path}/apply", headers=athlete).status_code, range(2)))
    assert sorted(statuses) == [201, 409]
    history = client.get("/me/applications", headers=athlete).json()
    assert len(history) == 1 and history[0]["opportunity"]["id"] == opportunity["id"]
    assert client.get("/organisation/applications", headers=org).json()[0]["id"] == history[0]["id"]
    assert client.get("/organisation/applications", headers=athlete).status_code == 403
    assert client.post(f"/opportunities/{fixture_id('p031')}/apply", headers=athlete).status_code == 409
    with postgres_sessions.begin() as session:
        other_org = session.get(User, fixture_id("o002"))
        other_token = issue_token(other_org, demo=True)
    other_headers = {"Authorization": f"Bearer {other_token}"}
    assert client.get("/organisation/applications", headers=other_headers).json() == []
    assert all(row["id"] != opportunity["id"] for row in client.get("/organisation/opportunities", headers=other_headers).json())


def test_browse_social_and_evaluation(client):
    athlete = sign_in(client, "cricket")
    listings = client.get("/opportunities?sport=cricket&type=trial&sort=deadline").json()
    assert listings and all(row["sport"] == "cricket" and row["type"] == "trial" for row in listings)
    assert client.get("/opportunities?limit=-1").status_code == 422
    assert client.post("/posts", headers=athlete, json={"body": "   "}).status_code == 422
    assert client.post("/posts", headers=athlete, json={"body": "Local integration test post."}).status_code == 201
    assert client.get("/posts").json()[0]["body"] == "Local integration test post."
    assert 0 < len(client.get("/people/suggested", headers=athlete).json()) <= 5
    results = client.get("/evaluation/results")
    assert results.status_code == 200
    assert results.json()["dataset"]["counts"]["athletes"] == 200
    assert client.get("/evaluation/plots/model_comparison").headers["content-type"] == "image/png"


def test_seed_is_idempotent_and_reset_is_targeted(client, postgres_sessions):
    athlete = sign_in(client, "football")
    seeded = fixture_id("p001")
    assert client.post(f"/opportunities/{seeded}/apply", headers=athlete).status_code == 201
    assert client.put("/me/profile", headers=athlete, json={"goals": "An edited demo goal"}).status_code == 200
    with postgres_sessions.begin() as session:
        person = User(email="existing@example.org", name="Existing user")
        session.add(person)
        session.flush()
        unrelated_id = person.id
        session.add(Post(author_id=person.id, body="Existing post"))
        session.add(Application(athlete_id=person.id, opportunity_id=seeded))
    seed_db(make_dataset())
    assert client.get("/me", headers=athlete).json()["profile"]["goals"] == "An edited demo goal"
    assert len(client.get("/me/applications", headers=athlete).json()) == 1
    seed_db(make_dataset(), reset=True)
    assert client.get("/me", headers=athlete).json()["profile"]["goals"] != "An edited demo goal"
    assert client.get("/me/applications", headers=athlete).json() == []
    with postgres_sessions() as session:
        assert session.get(User, unrelated_id) is not None
        assert session.scalar(select(Post).where(Post.author_id == unrelated_id)).body == "Existing post"
        assert session.scalar(select(Application).where(Application.athlete_id == unrelated_id)) is not None
        assert session.scalar(select(func.count()).select_from(Opportunity).where(Opportunity.synthetic)) >= 300
