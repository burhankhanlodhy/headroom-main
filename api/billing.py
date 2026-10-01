"""Stripe billing for paid plans.

Pro has a $0 monthly Stripe subscription (Checkout saves the payment method)
plus a savings fee computed from the account's own proxy ledger: 5% of the
whole cycle's savings when they exceed $20. At each renewal the fee for the
cycle that just ended is invoiced separately, keyed by (account, period) so a
period is never charged twice. Plan state is synced only from verified Stripe
webhooks; the browser can never grant a paid plan.
"""

import asyncio
import logging
import os
from datetime import datetime, timezone
from decimal import ROUND_HALF_UP, Decimal
from typing import Literal

import db
import stripe
from fastapi import Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict

logger = logging.getLogger("contextshrink.billing")

SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "")
WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
APP_URL = os.environ.get("APP_URL", "https://app.contextshrink.com").rstrip("/")
PRO_PRICE_LOOKUP_KEY = os.environ.get("STRIPE_PRO_PRICE_LOOKUP_KEY", "contextshrink_pro_monthly")
# Tags Checkout Sessions in the Stripe Dashboard (fixed random suffix).
CHECKOUT_INTEGRATION_ID = "contextshrink-pro-checkout-qhzvmtra"

SAVINGS_FEE_RATE = Decimal("0.05")
SAVINGS_FEE_THRESHOLD_USD = Decimal("20.00")

# Stripe statuses that keep paid entitlements; everything else is not "active".
ENTITLED_STATUSES = {"active", "trialing"}
ENDED_STATUSES = {"canceled", "incomplete_expired"}

_client = stripe.StripeClient(SECRET_KEY, max_network_retries=2) if SECRET_KEY else None
_price_ids: dict[str, str] = {}


def money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def savings_fee(savings: Decimal) -> Decimal:
    """5% of the full cycle savings, waived at or below the $20 threshold."""
    savings = money(savings)
    return money(savings * SAVINGS_FEE_RATE) if savings > SAVINGS_FEE_THRESHOLD_USD else Decimal("0.00")


async def ledger_savings(user_id, start: datetime, end: datetime) -> Decimal:
    value = await db._conn().fetchval(
        "SELECT COALESCE(SUM(NULLIF(data->>'savings_usd','')::numeric),0) "
        "FROM metrics.proxy_events WHERE user_id=$1 AND occurred_at >= $2 AND occurred_at < $3",
        user_id,
        start,
        end,
    )
    return Decimal(value or 0)


def _stripe():
    if _client is None:
        raise HTTPException(503, "Billing is not configured")
    return _client


async def _call(fn, *args, **kwargs):
    # stripe-python is synchronous; keep it off the event loop.
    return await asyncio.to_thread(fn, *args, **kwargs)


async def _price_id(lookup_key: str) -> str:
    if lookup_key not in _price_ids:
        prices = await _call(
            _stripe().v1.prices.list, {"lookup_keys": [lookup_key], "active": True, "limit": 1}
        )
        if not prices.data:
            raise HTTPException(503, "Billing price is not set up")
        _price_ids[lookup_key] = prices.data[0].id
    return _price_ids[lookup_key]


def _ts(value) -> datetime | None:
    return datetime.fromtimestamp(value, timezone.utc) if value else None


def _expandable_id(value) -> str | None:
    return value if isinstance(value, str) or value is None else value.id


async def _billing_row(user_id):
    return await db._conn().fetchrow(
        "SELECT plan, status, stripe_customer_id, stripe_subscription_id, cancel_at_period_end "
        "FROM core.subscriptions WHERE user_id=$1",
        user_id,
    )


async def _ensure_customer(user) -> str:
    await db.ensure_subscription(str(user["user_id"]))
    row = await _billing_row(user["user_id"])
    if row and row["stripe_customer_id"]:
        return row["stripe_customer_id"]
    customer = await _call(
        _stripe().v1.customers.create,
        {"email": user["email"], "name": user["name"], "metadata": {"user_id": str(user["user_id"])}},
        {"idempotency_key": f"customer-{user['user_id']}"},
    )
    # Keep the first stored customer if two requests raced.
    return await db._conn().fetchval(
        "UPDATE core.subscriptions SET stripe_customer_id=COALESCE(stripe_customer_id,$2), "
        "updated_at=now() WHERE user_id=$1 RETURNING stripe_customer_id",
        user["user_id"],
        customer.id,
    )


# ---------------------------------------------------------------- webhooks


async def _user_for_customer(customer_id: str, metadata_user_id: str | None):
    user_id = await db._conn().fetchval(
        "SELECT user_id FROM core.subscriptions WHERE stripe_customer_id=$1", customer_id
    )
    if user_id is None and metadata_user_id:
        # Fallback only: the customer is created by this API, so it is normally stored.
        user_id = await db._conn().fetchval(
            "UPDATE core.subscriptions SET stripe_customer_id=$2, updated_at=now() "
            "WHERE user_id=$1::uuid AND stripe_customer_id IS NULL RETURNING user_id",
            metadata_user_id,
            customer_id,
        )
    return user_id


async def _plan_for(subscription) -> Literal["pro"] | None:
    pro_price = await _price_id(PRO_PRICE_LOOKUP_KEY)
    for item in subscription["items"].data:
        if item.price.id == pro_price:
            return "pro"
    return None


async def sync_subscription(subscription_id: str) -> None:
    """Mirror a Stripe subscription onto the account, from Stripe's current state."""
    sub = await _call(_stripe().v1.subscriptions.retrieve, subscription_id)
    customer_id = _expandable_id(sub.customer)
    user_id = await _user_for_customer(customer_id, (sub.metadata or {}).get("user_id"))
    if user_id is None:
        logger.warning("Stripe subscription %s has no matching account", subscription_id)
        return
    if sub.status in ENDED_STATUSES:
        await db._conn().execute(
            "UPDATE core.subscriptions SET plan='free', status='active', stripe_subscription_id=NULL, "
            "cancel_at_period_end=false, current_period_start=NULL, current_period_end=NULL, "
            "updated_at=now() WHERE user_id=$1 AND stripe_subscription_id=$2",
            user_id,
            subscription_id,
        )
        return
    plan = await _plan_for(sub)
    if plan is None:
        logger.warning("Stripe subscription %s has no recognised plan price", subscription_id)
        return
    item = sub["items"].data[0]
    await db._conn().execute(
        "UPDATE core.subscriptions SET plan=$2, status=$3, stripe_subscription_id=$4, "
        "current_period_start=$5, current_period_end=$6, cancel_at_period_end=$7, updated_at=now() "
        "WHERE user_id=$1",
        user_id,
        plan,
        "active" if sub.status in ENTITLED_STATUSES else sub.status,
        subscription_id,
        _ts(item.current_period_start),
        _ts(item.current_period_end),
        bool(sub.cancel_at_period_end),
    )


async def charge_savings_fee(
    user_id, customer_id: str, start: datetime, end: datetime, payment_method: str | None
) -> None:
    """Invoice the savings fee for one ended period, at most once."""
    existing = await db._conn().fetchrow(
        "SELECT fee_cents, stripe_invoice_id FROM billing.savings_fees "
        "WHERE user_id=$1 AND period_start=$2",
        user_id,
        start,
    )
    if existing and (existing["fee_cents"] == 0 or existing["stripe_invoice_id"]):
        return
    savings = await ledger_savings(user_id, start, end)
    fee_cents = int(savings_fee(savings) * 100)
    await db._conn().execute(
        "INSERT INTO billing.savings_fees(user_id, period_start, period_end, savings_usd, fee_cents) "
        "VALUES($1,$2,$3,$4,$5) ON CONFLICT (user_id, period_start) DO NOTHING",
        user_id,
        start,
        end,
        savings,
        fee_cents,
    )
    if fee_cents == 0:
        return
    period = f"{start:%Y-%m-%d} to {end:%Y-%m-%d}"
    key = f"savings-fee-{user_id}-{int(start.timestamp())}"
    client = _stripe()
    invoice_params = {
        "customer": customer_id,
        "collection_method": "charge_automatically",
        "auto_advance": True,
        "pending_invoice_items_behavior": "exclude",
        "description": f"ContextShrink Pro savings fee, {period}",
        "metadata": {"user_id": str(user_id), "period_start": start.isoformat()},
    }
    if payment_method:
        invoice_params["default_payment_method"] = payment_method
    invoice = await _call(
        client.v1.invoices.create, invoice_params, {"idempotency_key": key + "-invoice"}
    )
    await _call(
        client.v1.invoice_items.create,
        {
            "customer": customer_id,
            "invoice": invoice.id,
            "currency": "usd",
            "amount": fee_cents,
            "description": f"5% of ${money(savings)} saved, {period}",
        },
        {"idempotency_key": key + "-item"},
    )
    await _call(
        client.v1.invoices.finalize_invoice,
        invoice.id,
        {"auto_advance": True},
        {"idempotency_key": key + "-finalize"},
    )
    await db._conn().execute(
        "UPDATE billing.savings_fees SET stripe_invoice_id=$3 WHERE user_id=$1 AND period_start=$2",
        user_id,
        start,
        invoice.id,
    )


def _invoice_subscription_id(invoice) -> str | None:
    details = getattr(getattr(invoice, "parent", None), "subscription_details", None)
    return _expandable_id(details.subscription) if details else None


async def handle_event(event) -> None:
    obj = event.data.object
    kind = event.type
    if kind == "checkout.session.completed":
        if obj.mode == "subscription" and obj.subscription:
            await sync_subscription(_expandable_id(obj.subscription))
    elif kind in (
        "customer.subscription.created",
        "customer.subscription.updated",
        "customer.subscription.paused",
        "customer.subscription.resumed",
    ):
        await sync_subscription(obj.id)
    elif kind == "customer.subscription.deleted":
        await sync_subscription(obj.id)
        # Cancellation creates no renewal invoice: bill the final partial period.
        user_id = await _user_for_customer(_expandable_id(obj.customer), None)
        item = obj["items"].data[0]
        if user_id:
            ended = _ts(obj.ended_at or obj.canceled_at) or datetime.now(timezone.utc)
            await charge_savings_fee(
                user_id,
                _expandable_id(obj.customer),
                _ts(item.current_period_start),
                ended,
                _expandable_id(obj.default_payment_method),
            )
    elif kind in ("invoice.paid", "invoice.payment_failed"):
        sub_id = _invoice_subscription_id(obj)
        if sub_id:
            await sync_subscription(sub_id)
    elif kind == "invoice.created":
        sub_id = _invoice_subscription_id(obj)
        # A renewal invoice's period is the cycle that just ended.
        if obj.billing_reason == "subscription_cycle" and sub_id:
            user_id = await _user_for_customer(_expandable_id(obj.customer), None)
            if user_id:
                sub = await _call(_stripe().v1.subscriptions.retrieve, sub_id)
                await charge_savings_fee(
                    user_id,
                    _expandable_id(obj.customer),
                    _ts(obj.period_start),
                    _ts(obj.period_end),
                    _expandable_id(sub.default_payment_method),
                )


# ------------------------------------------------------------------ routes


class CheckoutIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    plan: Literal["pro"]


def install(app, current_user):
    @app.exception_handler(stripe.StripeError)
    async def stripe_error(request, exc):
        # Never echo provider details; Stripe retries webhooks on 5xx.
        logger.error("Stripe request failed: %s %s", type(exc).__name__, getattr(exc, "code", ""))
        return JSONResponse({"detail": "Billing provider error. Please try again."}, status_code=502)

    @app.post("/billing/checkout")
    async def checkout(body: CheckoutIn, user=Depends(current_user)):
        row = await _billing_row(user["user_id"])
        if row and row["stripe_subscription_id"]:
            raise HTTPException(409, "You already have a subscription. Use Manage billing to change it.")
        customer_id = await _ensure_customer(user)
        session = await _call(
            _stripe().v1.checkout.sessions.create,
            {
                "mode": "subscription",
                "customer": customer_id,
                "client_reference_id": str(user["user_id"]),
                "line_items": [{"price": await _price_id(PRO_PRICE_LOOKUP_KEY), "quantity": 1}],
                # Pro costs $0 up front; the card is needed for the savings fee.
                "payment_method_collection": "always",
                "subscription_data": {"metadata": {"user_id": str(user["user_id"])}},
                "integration_identifier": CHECKOUT_INTEGRATION_ID,
                "success_url": f"{APP_URL}/subscriptions?checkout=success",
                "cancel_url": f"{APP_URL}/subscriptions?checkout=cancelled",
            },
        )
        return {"url": session.url}

    @app.post("/billing/portal")
    async def portal(user=Depends(current_user)):
        row = await _billing_row(user["user_id"])
        if not row or not row["stripe_customer_id"]:
            raise HTTPException(404, "No billing account yet")
        session = await _call(
            _stripe().v1.billing_portal.sessions.create,
            {"customer": row["stripe_customer_id"], "return_url": f"{APP_URL}/subscriptions"},
        )
        return {"url": session.url}

    @app.get("/billing/invoices")
    async def invoices(user=Depends(current_user)):
        row = await _billing_row(user["user_id"])
        if not row or not row["stripe_customer_id"] or _client is None:
            return []
        result = await _call(
            _client.v1.invoices.list, {"customer": row["stripe_customer_id"], "limit": 24}
        )
        return [
            {
                "id": inv.id,
                "number": inv.number,
                "created": _ts(inv.created).isoformat(),
                "description": inv.description or "ContextShrink Pro subscription",
                "total": inv.total / 100,
                "currency": inv.currency,
                "status": inv.status,
                "url": inv.hosted_invoice_url,
            }
            for inv in result.data
            if inv.status != "draft"
        ]

    @app.post("/stripe/webhook")
    async def webhook(request: Request):
        if _client is None or not WEBHOOK_SECRET:
            raise HTTPException(503, "Billing webhooks are not configured")
        payload = await request.body()
        try:
            event = _client.construct_event(
                payload, request.headers.get("stripe-signature"), WEBHOOK_SECRET
            )
        except (ValueError, stripe.SignatureVerificationError):
            raise HTTPException(400, "Invalid Stripe signature") from None
        done = await db._conn().fetchval(
            "SELECT 1 FROM billing.stripe_events WHERE event_id=$1", event.id
        )
        if not done:
            # Errors propagate as 500 so Stripe retries; handlers are idempotent.
            await handle_event(event)
            await db._conn().execute(
                "INSERT INTO billing.stripe_events(event_id, type) VALUES($1,$2) "
                "ON CONFLICT DO NOTHING",
                event.id,
                event.type,
            )
        return {"received": True}
