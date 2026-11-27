"""Generate datasets, populate PostgreSQL or restore generated demo fixtures."""

import argparse
from datetime import UTC, datetime, timedelta
from pathlib import Path

from app.dataset import DATA_DIR, deadline, export_dataset, fixture_id, make_dataset

PROFILE_FIELDS = ("sport", "position", "age", "city", "region", "level", "skills", "goals", "bio")
OPPORTUNITY_FIELDS = ("title", "type", "sport", "positions", "age_min", "age_max", "city", "region",
                      "level", "skills", "description", "hard_age_limit", "synthetic")


def seed_db(dataset, *, reset=False):
    from sqlalchemy import delete, select, text
    from sqlalchemy.orm import lazyload

    from app.config import settings
    from app.db import SessionLocal
    from app.models import Application, Opportunity, Post, Profile, User

    if not settings.local_demo:
        raise RuntimeError("Database seeding requires ENV=development and DEMO_ENABLED=true")
    anchor = datetime.now(UTC).replace(microsecond=0)
    orgs = {row["organisation_id"]: row for row in dataset["organisations"]}

    def put(db, model, key, values):
        existing = db.get(model, key)
        if existing is None:
            db.add(model(**values))
        elif not existing.synthetic:
            raise RuntimeError(f"Refusing to modify a non-synthetic {model.__name__} with fixture ID {key}")
        elif reset:
            for field, value in values.items():
                setattr(existing, field, value)

    with SessionLocal.begin() as db:
        db.execute(text("SELECT pg_advisory_xact_lock(317061251)"))
        person_ids = [fixture_id(row["athlete_id"]) for row in dataset["athletes"]]
        person_ids.append(fixture_id("onboarding"))
        org_ids = [fixture_id(code) for code in orgs]
        if reset:
            demo_owned = select(Opportunity.id).where(Opportunity.posted_by.in_(org_ids), Opportunity.synthetic)
            db.execute(delete(Application).where(Application.athlete_id.in_(person_ids),
                                                 Application.opportunity_id.in_(demo_owned)))
        for code, row in orgs.items():
            key = fixture_id(code)
            put(db, User, key, dict(id=key, email=f"{code}@groundup.invalid", name=row["name"],
                                    role="team", mode="professional", organisation_name=row["name"],
                                    verification_status="unverified", synthetic=True))
        onboarding_id = fixture_id("onboarding")
        put(db, User, onboarding_id, dict(id=onboarding_id, email="onboarding@groundup.invalid",
                                         name="Demo Onboarding Athlete", role="athlete",
                                         mode="casual", verification_status="unverified", synthetic=True))
        db.flush()
        if reset:
            db.execute(delete(Profile).where(Profile.user_id == onboarding_id))
        for row in dataset["athletes"]:
            code = row["athlete_id"]
            key = fixture_id(code)
            put(db, User, key, dict(id=key, email=f"{code}@groundup.invalid", name=row["name"],
                                    role="athlete", mode=row["mode"], verification_status="unverified", synthetic=True))
            db.flush()
            profile = db.get(Profile, key, options=[lazyload(Profile.user)])
            values = {field: row[field] for field in PROFILE_FIELDS}
            if profile is None:
                db.add(Profile(user_id=key, **values))
            elif reset:
                for field, value in values.items():
                    setattr(profile, field, value)
        for row in dataset["opportunities"]:
            key = fixture_id(row["opportunity_id"])
            code = row["organisation_id"]
            put(db, Opportunity, key, dict(id=key, posted_by=fixture_id(code), org=orgs[code]["name"],
                                         deadline=deadline(row["deadline_offset_days"], anchor),
                                         **{field: row[field] for field in OPPORTUNITY_FIELDS}))
        for row in dataset["posts"]:
            key = fixture_id(row["post_id"])
            put(db, Post, key, dict(id=key, author_id=fixture_id(row["athlete_id"]), body=row["body"],
                                    created_at=anchor + timedelta(days=row["day_offset"]), synthetic=True))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--export-only", action="store_true", help="Write CSV files and metadata without a database")
    parser.add_argument("--export-dir", type=Path, default=DATA_DIR)
    parser.add_argument("--reset-demo", action="store_true", help="Restore fixture profiles and clear demo-to-demo applications")
    args = parser.parse_args()
    if args.export_only and args.reset_demo:
        parser.error("--export-only and --reset-demo cannot be used together")
    dataset = make_dataset()
    if args.export_only:
        export_dataset(dataset, args.export_dir)
    else:
        seed_db(dataset, reset=args.reset_demo)
    print(" · ".join(f"{len(rows)} {name.replace('_', ' ')}" for name, rows in dataset.items()))


if __name__ == "__main__":
    main()
