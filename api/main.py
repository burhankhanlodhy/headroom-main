"""ContextShrink control-plane API.

Session auth, account-owned proxy keys and private analytics. Only the
authenticated proxy service may submit usage events to the Postgres ledger.
"""

import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Literal

import analytics
import asyncpg
import db
import security
from fastapi import Depends, FastAPI, Header, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, EmailStr, Field

CORS_ORIGINS = [
    o.strip()
    for o in os.environ.get("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(
        ","
    )
    if o.strip()
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.init_pool()
    yield
    await db.close_pool()


app = FastAPI(title="ContextShrink Control Plane", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ------------------------------------------------------------------- models


class SignupIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=200)


class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=200)


class UserOut(BaseModel):
    id: str
    name: str
    email: str


class AccountOut(UserOut):
    created_at: datetime
    plan: str
    subscription_status: str


class SubscriptionIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    plan: Literal["free", "pro", "team"]


def _money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


async def account_billing_estimate(user: asyncpg.Record) -> dict:
    """Calculate a private estimate from the authenticated account's proxy ledger."""
    row = await db._conn().fetchrow(
        "SELECT current_period_start, current_period_end, seat_count "
        "FROM core.subscriptions WHERE user_id=$1",
        user["user_id"],
    )
    now = datetime.now(timezone.utc)
    start = row["current_period_start"] if row else None
    end = row["current_period_end"] if row else None
    if start is None or end is None or end <= now:
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if start.month == 12:
            end = start.replace(year=start.year + 1, month=1)
        else:
            end = start.replace(month=start.month + 1)
    seats = int(row["seat_count"] or 1) if row else 1
    savings_row = await db._conn().fetchrow(
        "SELECT COALESCE(SUM(NULLIF(data->>'savings_usd','')::numeric),0) AS savings "
        "FROM metrics.proxy_events WHERE user_id=$1 AND occurred_at >= $2 AND occurred_at < $3",
        user["user_id"], start, end,
    )
    savings = _money(Decimal(savings_row["savings"] or 0))
    savings_fee = _money(savings * Decimal("0.05")) if savings > Decimal("20.00") else Decimal("0.00")
    team_base = Decimal(seats * 5)
    current_plan = user["plan"]
    estimates = {
        "free": {"seat_fee": Decimal("0.00"), "savings_fee": Decimal("0.00"), "total": Decimal("0.00")},
        "pro": {"seat_fee": Decimal("0.00"), "savings_fee": savings_fee, "total": savings_fee},
        "team": {"seat_fee": team_base, "savings_fee": savings_fee, "total": team_base + savings_fee},
    }
    def as_usd(value: Decimal) -> float:
        return float(_money(value))
    return {
        "plan": current_plan,
        "period_start": start.isoformat(),
        "period_end": end.isoformat(),
        "period_source": "subscription" if row and row["current_period_start"] and row["current_period_end"] else "calendar_month",
        "estimated_savings_usd": as_usd(savings),
        "savings_fee_threshold_usd": 20.0,
        "savings_fee_rate": 0.05,
        "seat_count": seats,
        "estimates": {plan: {key: as_usd(value) for key, value in breakdown.items()} for plan, breakdown in estimates.items()},
        "estimated_total_usd": as_usd(estimates.get(current_plan, estimates["free"])["total"]),
        "currency": "USD",
    }


class AuthOut(BaseModel):
    token: str
    user: UserOut


class UsageEventIn(BaseModel):
    ts: str | None = None
    session_id: str | None = None
    agent: str | None = None
    model: str | None = None
    requests: int = 1
    tokens_in: int = 0
    tokens_out: int = 0
    tokens_saved: int = 0
    savings_usd: float = 0.0
    cache_hit: bool | None = None


class IngestIn(BaseModel):
    events: list[UsageEventIn] = Field(min_length=1, max_length=1000)


# ----------------------------------------------------------------- helpers


async def current_user(
    authorization: str | None = Header(default=None),
) -> asyncpg.Record:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing bearer token")
    token = authorization.removeprefix("Bearer ").strip()
    row = await db.resolve_session(security.hash_token(token))
    if row is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired session")
    return row


# ------------------------------------------------------------ auth routes


@app.get("/healthz")
async def healthz() -> dict:
    return {"ok": True, "service": "contextshrink-control-plane"}


@app.post("/auth/signup", status_code=status.HTTP_201_CREATED, response_model=AuthOut)
async def signup(body: SignupIn):
    email = body.email.strip().lower()
    if await db.get_user_by_email(email):
        raise HTTPException(status.HTTP_409_CONFLICT, "An account with this email already exists")
    try:
        user = await db.create_user(email, body.name.strip(), security.hash_password(body.password))
    except asyncpg.UniqueViolationError:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "An account with this email already exists"
        ) from None
    await db.ensure_subscription(str(user["id"]))
    token = security.new_session_token()
    await db.create_session(str(user["id"]), security.hash_token(token))
    return AuthOut(
        token=token, user=UserOut(id=str(user["id"]), name=user["name"], email=user["email"])
    )


@app.post("/auth/login", response_model=AuthOut)
async def login(body: LoginIn):
    email = body.email.strip().lower()
    user = await db.get_user_by_email(email)
    if user is None or not security.verify_password(body.password, user["password_hash"]):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")
    token = security.new_session_token()
    await db.create_session(str(user["id"]), security.hash_token(token))
    return AuthOut(
        token=token, user=UserOut(id=str(user["id"]), name=user["name"], email=user["email"])
    )


@app.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(authorization: str | None = Header(default=None)):
    if authorization and authorization.startswith("Bearer "):
        token = authorization.removeprefix("Bearer ").strip()
        await db.revoke_session(security.hash_token(token))


@app.get("/auth/me", response_model=AccountOut)
async def me(user: asyncpg.Record = Depends(current_user)):
    return AccountOut(
        id=str(user["user_id"]),
        name=user["name"],
        email=user["email"],
        created_at=user["created_at"],
        plan=user["plan"],
        subscription_status=user["subscription_status"],
    )


@app.get("/subscription")
async def subscription(user: asyncpg.Record = Depends(current_user)):
    return {
        "plan": user["plan"], "status": user["subscription_status"],
        "billing_mode": "stripe_not_configured",
        "estimate": await account_billing_estimate(user),
    }


@app.put("/subscription")
async def change_subscription(body: SubscriptionIn, user: asyncpg.Record = Depends(current_user)):
    # Free is always self-serve. Paid plans require configured Stripe Checkout;
    # never grant paid entitlements through a client-selected plan value.
    if body.plan != "free":
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "Paid plan checkout is not configured. Add Stripe sandbox billing settings before upgrading.",
        )
    await db._conn().execute(
        "INSERT INTO core.subscriptions(user_id,plan,status) VALUES($1,$2,'active') "
        "ON CONFLICT(user_id) DO UPDATE SET plan=EXCLUDED.plan,status='active', "
        "current_period_end=NULL,updated_at=now()",
        user["user_id"],
        body.plan,
    )
    return {"plan": body.plan, "status": "active", "billing_mode": "free"}


@app.get("/billing/estimate")
async def billing_estimate(user: asyncpg.Record = Depends(current_user)):
    return await account_billing_estimate(user)


# --------------------------------------------------------- metrics routes


@app.post("/ingest/usage", status_code=status.HTTP_202_ACCEPTED)
async def ingest_usage(
    body: IngestIn,
    x_api_key: str | None = Header(default=None),
):
    """Legacy client-supplied telemetry is disabled; only the proxy may ingest."""
    raise HTTPException(status.HTTP_410_GONE, "Use trusted proxy analytics ingestion")


@app.get("/usage/summary")
async def usage_summary(
    days: int = 30,
    user: asyncpg.Record = Depends(current_user),
):
    if not 1 <= days <= 365:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "days must be 1..365")
    return await analytics.basic_usage(user, days)


analytics.install(app, current_user)
