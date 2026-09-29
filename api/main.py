"""ContextShrink control-plane API.

Auth (signup / login / logout / me) plus the metrics ingest + summary
endpoints. Runs in its own container next to Postgres; the horizon proxy
stack is untouched.
"""

import os
from contextlib import asynccontextmanager
from typing import Optional

import asyncpg
from fastapi import Depends, FastAPI, Header, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field

import db
import security

CORS_ORIGINS = [
    o.strip()
    for o in os.environ.get(
        "CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
    ).split(",")
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


class AuthOut(BaseModel):
    token: str
    user: UserOut


class UsageEventIn(BaseModel):
    ts: Optional[str] = None
    session_id: Optional[str] = None
    agent: Optional[str] = None
    model: Optional[str] = None
    requests: int = 1
    tokens_in: int = 0
    tokens_out: int = 0
    tokens_saved: int = 0
    savings_usd: float = 0.0
    cache_hit: Optional[bool] = None


class IngestIn(BaseModel):
    events: list[UsageEventIn] = Field(min_length=1, max_length=1000)


# ----------------------------------------------------------------- helpers


async def current_user(
    authorization: Optional[str] = Header(default=None),
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
        raise HTTPException(status.HTTP_409_CONFLICT, "An account with this email already exists")
    await db.ensure_subscription(str(user["id"]))
    token = security.new_session_token()
    await db.create_session(str(user["id"]), security.hash_token(token))
    return AuthOut(token=token, user=UserOut(id=str(user["id"]), name=user["name"], email=user["email"]))


@app.post("/auth/login", response_model=AuthOut)
async def login(body: LoginIn):
    email = body.email.strip().lower()
    user = await db.get_user_by_email(email)
    if user is None or not security.verify_password(body.password, user["password_hash"]):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")
    token = security.new_session_token()
    await db.create_session(str(user["id"]), security.hash_token(token))
    return AuthOut(token=token, user=UserOut(id=str(user["id"]), name=user["name"], email=user["email"]))


@app.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(authorization: Optional[str] = Header(default=None)):
    if authorization and authorization.startswith("Bearer "):
        token = authorization.removeprefix("Bearer ").strip()
        await db.revoke_session(security.hash_token(token))


@app.get("/auth/me", response_model=UserOut)
async def me(user: asyncpg.Record = Depends(current_user)):
    return UserOut(id=str(user["user_id"]), name=user["name"], email=user["email"])


# --------------------------------------------------------- metrics routes


@app.post("/ingest/usage", status_code=status.HTTP_202_ACCEPTED)
async def ingest_usage(
    body: IngestIn,
    x_api_key: Optional[str] = Header(default=None),
):
    """Proxy instances push batched usage rows here using an API key."""
    if not x_api_key:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing X-API-Key header")
    key_row = await db.resolve_api_key(security.hash_token(x_api_key))
    if key_row is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid API key")
    rows = [{**e.model_dump(), "user_id": str(key_row["user_id"])} for e in body.events]
    await db.insert_usage_events(rows)
    return {"accepted": len(rows)}


@app.get("/usage/summary")
async def usage_summary(
    days: int = 30,
    user: asyncpg.Record = Depends(current_user),
):
    if not 1 <= days <= 365:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "days must be 1..365")
    return await db.usage_summary(str(user["user_id"]), days)
