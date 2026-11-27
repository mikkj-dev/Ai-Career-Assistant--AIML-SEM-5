from datetime import UTC, datetime
from typing import Annotated, Literal
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator
from sqlalchemy import func, or_, select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session, joinedload

from app import matching
from app.auth import current_user, issue_token, optional_user, verify_google
from app.catalog import DEMO_ACCOUNTS, SPORTS, TYPES
from app.config import settings
from app.dataset import fixture_id
from app.db import get_db
from app.models import Application, Opportunity, Post, Profile, User
from app.seed import PROFILE_FIELDS

app = FastAPI(title="Ground Up API", version="1.0.0")
app.add_middleware(
    CORSMiddleware, allow_origins=[o.strip() for o in settings.cors_origins.split(",")],
    allow_methods=["GET", "POST", "PUT"], allow_headers=["Authorization", "Content-Type"],
)

Level = Literal["beginner", "district", "state", "national", "professional"]
Sport = Literal["football", "cricket", "basketball", "athletics", "badminton"]
OpportunityType = Literal["trial", "scholarship", "tournament", "camp", "scouting", "club", "development"]
Skill = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=40)]
Position = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=60)]
ReadyLimit = Annotated[int, Query(ge=1, le=100)]
DB = Annotated[Session, Depends(get_db)]
SignedIn = Annotated[User, Depends(current_user)]
OptionalUser = Annotated[User | None, Depends(optional_user)]
DEMO_IDENTITIES = DEMO_ACCOUNTS | {"new": ("Start a new athlete profile", "onboarding")}


class Input(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")


class GoogleIn(Input):
    credential: str = Field(min_length=1, max_length=8192)


class DemoLoginIn(Input):
    account: str = Field(min_length=1, max_length=40)


class ProfileIn(Input):
    name: str | None = Field(None, min_length=1, max_length=120)
    mode: Literal["professional", "casual"] | None = None
    sport: str | None = Field(None, max_length=40)
    position: str | None = Field(None, max_length=60)
    age: int | None = Field(None, ge=8, le=60)
    city: str | None = Field(None, max_length=80)
    region: str | None = Field(None, max_length=40)
    level: Level | None = None
    skills: list[Skill] | None = Field(None, max_length=20)
    goals: str | None = Field(None, max_length=1000)
    bio: str | None = Field(None, max_length=1000)


class VerificationIn(Input):
    doc_type: Literal["aadhaar", "passport", "driving_licence", "other"]


class PostIn(Input):
    body: str = Field(min_length=1, max_length=2000)


class OpportunityIn(Input):
    title: str = Field(min_length=3, max_length=160)
    type: OpportunityType
    sport: Sport
    positions: list[Position] = Field(default_factory=list, max_length=15)
    age_min: int | None = Field(None, ge=8, le=60)
    age_max: int | None = Field(None, ge=8, le=60)
    city: str | None = Field(None, max_length=80)
    region: str | None = Field(None, max_length=40)
    level: Level | None = None
    skills: list[Skill] = Field(default_factory=list, max_length=20)
    description: str = Field(min_length=10, max_length=4000)
    deadline: datetime | None = None
    hard_age_limit: bool = True

    @model_validator(mode="after")
    def check_requirements(self):
        if self.age_min is not None and self.age_max is not None and self.age_min > self.age_max:
            raise ValueError("Minimum age must be at most maximum age")
        self.positions = sorted(matching.categories(self.positions))
        if set(self.positions) - SPORTS[self.sport].keys():
            raise ValueError("Choose positions offered by the selected sport")
        if self.deadline is not None and (self.deadline.tzinfo is None or self.deadline <= datetime.now(UTC)):
            raise ValueError("Deadline must include a timezone and be in the future")
        self.skills = sorted(matching.categories(self.skills))
        return self


def user_out(user):
    profile = user.profile
    return {
        "id": user.id, "email": user.email, "name": user.name, "avatar_url": user.avatar_url,
        "role": user.role, "mode": user.mode, "verification_status": user.verification_status,
        "organisation_name": user.organisation_name, "synthetic": user.synthetic,
        "profile": {field: getattr(profile, field) for field in PROFILE_FIELDS} if profile else None,
    }


def opp_out(opp):
    return {field: getattr(opp, field) for field in (
        "id", "title", "org", "type", "sport", "positions", "age_min", "age_max", "city", "region",
        "level", "skills", "description", "deadline", "synthetic", "hard_age_limit",
    )}


def match_out(match):
    return match | {"opportunity": opp_out(match["opportunity"])}


def application_out(application):
    return {
        "id": application.id, "status": application.status, "created_at": application.created_at,
        "opportunity": opp_out(application.opportunity),
        "athlete": {"id": application.athlete.id, "name": application.athlete.name},
    }


def lookup_opportunity(db, opportunity_id):
    opportunity = db.get(Opportunity, opportunity_id)
    if opportunity is None:
        raise HTTPException(404, "Opportunity not found")
    return opportunity


def require_athlete(user):
    if user.role != "athlete":
        raise HTTPException(403, "An athlete account is required")


def require_organisation(user):
    if user.role != "team" or not user.organisation_name:
        raise HTTPException(403, "An authorised organisation account is required")


def active(when):
    return or_(Opportunity.deadline.is_(None), Opportunity.deadline > when)


def encoder():
    if settings.similarity_method == "sentence-bert":
        return matching.semantic_encoder(settings.sentence_bert_model)
    return None


def reference_corpus(db, when):
    # Stable across athlete ages, browse filters and K. Changes when active postings change.
    return tuple(db.scalars(select(Opportunity.description).where(active(when)).order_by(Opportunity.id)))


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/ready")
def readiness(db: DB):
    db.execute(text("SELECT 1 FROM users LIMIT 1"))
    return {"ok": True}


@app.get("/catalog")
def catalog():
    return {"sports": {sport: list(positions) for sport, positions in SPORTS.items()},
            "types": TYPES, "levels": matching.LEVELS}


@app.get("/demo/info")
def demo_info(db: DB):
    if not settings.local_demo:
        return {"enabled": False, "accounts": []}
    ids = [fixture_id(code) for _, code in DEMO_IDENTITIES.values()]
    seeded = set(db.scalars(select(User.id).where(User.synthetic, User.id.in_(ids))))
    accounts = [{"id": key, "label": label} for key, (label, code) in DEMO_IDENTITIES.items()
                if fixture_id(code) in seeded]
    return {"enabled": True, "accounts": accounts}


@app.post("/auth/google")
def auth_google(body: GoogleIn, db: DB):
    info = verify_google(body.credential)
    if not info.get("email_verified"):
        raise HTTPException(401, "Google email not verified")
    email = info["email"].casefold()
    if email.endswith("@groundup.invalid"):
        raise HTTPException(403, "Reserved demo email domain")
    db.execute(insert(User).values(email=email, name=info.get("name"), avatar_url=info.get("picture"))
               .on_conflict_do_nothing(index_elements=[User.email]))
    db.commit()
    user = db.scalar(select(User).where(User.email == email, User.synthetic.is_(False)))
    if user is None:
        raise HTTPException(403, "Google sign-in is unavailable for this account")
    return {"token": issue_token(user), "user": user_out(user)}


@app.post("/auth/demo")
@app.post("/auth/dev", include_in_schema=False)
def auth_demo(body: DemoLoginIn, db: DB):
    if not settings.local_demo or body.account not in DEMO_IDENTITIES:
        raise HTTPException(404, "Demo account unavailable")
    user = db.get(User, fixture_id(DEMO_IDENTITIES[body.account][1]))
    if user is None or not user.synthetic:
        raise HTTPException(503, "Load the synthetic fixtures to enable local demo sign-in")
    return {"token": issue_token(user, demo=True), "user": user_out(user)}


@app.get("/me")
def me(user: SignedIn):
    return user_out(user)


@app.put("/me/profile")
def update_profile(body: ProfileIn, user: SignedIn, db: DB):
    require_athlete(user)
    data = body.model_dump(exclude_unset=True)
    if data.get("mode") is not None:
        user.mode = data["mode"]
    data.pop("mode", None)
    if "name" in data:
        user.name = data.pop("name")
    if user.profile is None:
        user.profile = Profile(user_id=user.id)
    if "sport" in data:
        data["sport"] = matching.normalize(data["sport"]) or None
        if data["sport"] is not None and data["sport"] not in SPORTS:
            raise HTTPException(422, "Unknown sport")
    sport = data.get("sport", user.profile.sport)
    if "position" in data:
        data["position"] = matching.normalize_category(data["position"]) or None
        if data["position"] and data["position"] not in SPORTS.get(sport, {}):
            raise HTTPException(422, "Position must belong to the selected sport")
    elif sport != user.profile.sport:
        data["position"] = None
    if "skills" in data:
        data["skills"] = sorted(matching.categories(data["skills"]))
    for field, value in data.items():
        setattr(user.profile, field, value)
    db.commit()
    return user_out(user)


@app.post("/me/verification")
def submit_verification(body: VerificationIn, user: SignedIn, db: DB):
    user.verification_doc = body.doc_type
    user.verification_status = "pending"
    db.commit()
    return user_out(user)


@app.get("/opportunities")
def list_opportunities(db: DB, sport: Sport | None = None, type: OpportunityType | None = None,
                       sort: Literal["newest", "deadline"] = "newest", limit: ReadyLimit = 100):
    q = select(Opportunity).where(active(datetime.now(UTC)))
    if sport:
        q = q.where(func.lower(func.trim(Opportunity.sport)) == sport)
    if type:
        q = q.where(Opportunity.type == type)
    order = Opportunity.deadline.asc().nulls_last() if sort == "deadline" else Opportunity.created_at.desc()
    return [opp_out(opp) for opp in db.scalars(q.order_by(order, Opportunity.id).limit(limit))]


@app.get("/opportunities/recommended")
def recommended(user: SignedIn, db: DB, k: ReadyLimit = 10):
    profile = user.profile
    if profile is None or not matching.normalize(profile.sport):
        return []
    when = datetime.now(UTC)
    q = select(Opportunity).where(active(when), func.lower(func.trim(Opportunity.sport)) == matching.normalize(profile.sport))
    # Keep the existing bounded retrieval window and preserve the age tolerance in SQL.
    if profile.age is not None:
        tolerance = matching.AGE_TOLERANCE
        q = q.where(or_(Opportunity.age_min.is_(None), Opportunity.age_min - tolerance <= profile.age),
                    or_(Opportunity.age_max.is_(None), Opportunity.age_max + tolerance >= profile.age))
    pool = list(db.scalars(q.order_by(Opportunity.created_at.desc(), Opportunity.id).limit(500)))
    if not pool:
        return []
    return [match_out(match) for match in matching.rank(
        profile, pool, k, corpus=reference_corpus(db, when), encoder=encoder(), now=when
    )]


@app.post("/opportunities", status_code=201)
def create_opportunity(body: OpportunityIn, user: SignedIn, db: DB):
    require_organisation(user)
    opportunity = Opportunity(**body.model_dump(), posted_by=user.id, org=user.organisation_name,
                              synthetic=user.synthetic)
    db.add(opportunity)
    db.commit()
    return opp_out(opportunity)


@app.get("/opportunities/{opportunity_id}")
def opportunity_detail(opportunity_id: UUID, user: OptionalUser, db: DB):
    opportunity = lookup_opportunity(db, opportunity_id)
    when = datetime.now(UTC)
    profile = user.profile if user and user.role == "athlete" else None
    eligibility = matching.eligibility(profile, opportunity, when) if profile else "profile_required"
    matches = []
    if profile and matching.eligible(profile, opportunity, when):
        matches = matching.rank(profile, [opportunity], corpus=reference_corpus(db, when), encoder=encoder(), now=when)
    application = db.scalar(select(Application).where(Application.athlete_id == user.id,
                                                      Application.opportunity_id == opportunity.id)) if user else None
    return {"opportunity": opp_out(opportunity), "match": match_out(matches[0]) if matches else None,
            "eligibility": eligibility, "application": application_out(application) if application else None}


@app.post("/opportunities/{opportunity_id}/apply", status_code=201)
def apply(opportunity_id: UUID, user: SignedIn, db: DB):
    require_athlete(user)
    opportunity = lookup_opportunity(db, opportunity_id)
    if not user.profile:
        raise HTTPException(422, "Complete an athlete profile before applying")
    eligibility = matching.eligibility(user.profile, opportunity)
    if eligibility != "strict" and not (eligibility == "age_tolerance" and not opportunity.hard_age_limit):
        raise HTTPException(409, "This opportunity is closed or your profile does not meet sport and age requirements")
    application_id = db.scalar(insert(Application).values(athlete_id=user.id, opportunity_id=opportunity.id)
                               .on_conflict_do_nothing(constraint="uq_application_athlete_opportunity")
                               .returning(Application.id))
    if application_id is None:
        raise HTTPException(409, "You have already applied to this opportunity")
    db.commit()
    return application_out(db.get(Application, application_id))


@app.get("/me/applications")
def applications(user: SignedIn, db: DB):
    require_athlete(user)
    rows = db.scalars(select(Application).options(joinedload(Application.opportunity), joinedload(Application.athlete))
                      .where(Application.athlete_id == user.id).order_by(Application.created_at.desc(), Application.id))
    return [application_out(row) for row in rows]


@app.get("/organisation/opportunities")
def organisation_opportunities(user: SignedIn, db: DB):
    require_organisation(user)
    rows = db.scalars(select(Opportunity).where(Opportunity.posted_by == user.id)
                      .order_by(Opportunity.created_at.desc(), Opportunity.id))
    return [opp_out(row) for row in rows]


@app.get("/organisation/applications")
def organisation_applications(user: SignedIn, db: DB):
    require_organisation(user)
    rows = db.scalars(select(Application).join(Application.opportunity)
                      .options(joinedload(Application.opportunity), joinedload(Application.athlete))
                      .where(Opportunity.posted_by == user.id).order_by(Application.created_at.desc(), Application.id))
    return [application_out(row) for row in rows]


@app.get("/posts")
def list_posts(db: DB, before: datetime | None = None, limit: ReadyLimit = 20):
    q = select(Post).order_by(Post.created_at.desc(), Post.id).limit(limit)
    if before:
        q = q.where(Post.created_at < before)
    return [{"id": post.id, "body": post.body, "created_at": post.created_at, "synthetic": post.synthetic,
             "author": {"id": post.author.id, "name": post.author.name, "avatar_url": post.author.avatar_url,
                        "role": post.author.role}} for post in db.scalars(q)]


@app.post("/posts", status_code=201)
def create_post(body: PostIn, user: SignedIn, db: DB):
    post = Post(author_id=user.id, body=body.body, synthetic=user.synthetic)
    db.add(post)
    db.commit()
    return {"id": post.id}


@app.get("/people/suggested")
def suggested_people(user: SignedIn, db: DB):
    profile = user.profile
    if not profile or not profile.sport:
        return []
    rows = db.scalars(select(Profile).join(Profile.user).options(joinedload(Profile.user))
                      .where(Profile.sport == profile.sport, Profile.user_id != user.id, User.role == "athlete")
                      .order_by(Profile.user_id).limit(200)).all()
    scored = sorted(rows, key=lambda p: -matching.skills_score(profile.skills, p.skills)
                    - 0.5 * (bool(p.city) and matching.normalize(p.city) == matching.normalize(profile.city)))
    return [{"id": p.user_id, "name": p.user.name, "avatar_url": p.user.avatar_url, "position": p.position,
             "city": p.city, "role": p.user.role} for p in scored[:5]]


@app.get("/evaluation/model")
def evaluation_model():
    return {"configured": settings.similarity_method,
            "active": "sentence-bert" if encoder() is not None else "tfidf",
            "weights": matching.WEIGHTS}


@app.get("/evaluation/results")
def evaluation_results():
    path = settings.evaluation_dir / "results.json"
    if not path.is_file():
        raise HTTPException(503, "Run the offline evaluation to generate results")
    return FileResponse(path, media_type="application/json")


@app.get("/evaluation/plots/{name}")
def evaluation_plot(name: Literal["model_comparison", "ablation_study", "score_distribution", "dataset_distribution"]):
    path = settings.evaluation_dir / "plots" / f"{name}.png"
    if not path.is_file():
        raise HTTPException(404, "Evaluation figure unavailable")
    return FileResponse(path, media_type="image/png")
