"""Billing logic against fakes: no Postgres, no network calls to Stripe.

Run from the repo root with the API's requirements installed:
    python -m pytest api/tests
"""

import asyncio
import hashlib
import hmac
import json
import sys
import time
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

import pytest
import stripe
from fastapi import FastAPI
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import billing  # noqa: E402

UID = "7b0c6c1e-9d6a-4c51-9a55-0d9f1f0a2b3c"
START = datetime(2026, 9, 1, tzinfo=timezone.utc)
END = datetime(2026, 10, 1, tzinfo=timezone.utc)


class FakeConn:
    """Just enough of the asyncpg pool for billing.py's queries."""

    def __init__(self):
        self.events: set[str] = set()
        self.fees: dict[tuple, dict] = {}
        self.customers = {"cus_1": UID}
        self.plan_updates: list[tuple] = []

    async def fetchval(self, sql, *args):
        if "billing.stripe_events" in sql:
            return 1 if args[0] in self.events else None
        if "SELECT user_id FROM core.subscriptions WHERE stripe_customer_id" in sql:
            return self.customers.get(args[0])
        raise AssertionError(sql)

    async def fetchrow(self, sql, *args):
        if "FROM billing.savings_fees" in sql:
            return self.fees.get((args[0], args[1]))
        raise AssertionError(sql)

    async def execute(self, sql, *args):
        if "INSERT INTO billing.stripe_events" in sql:
            self.events.add(args[0])
        elif "INSERT INTO billing.savings_fees" in sql:
            self.fees.setdefault(
                (args[0], args[1]), {"fee_cents": args[4], "stripe_invoice_id": None}
            )
        elif "UPDATE billing.savings_fees" in sql:
            self.fees[(args[0], args[1])]["stripe_invoice_id"] = args[2]
        elif "UPDATE core.subscriptions SET plan=" in sql:
            self.plan_updates.append(args)
        else:
            raise AssertionError(sql)


class FakeStripe:
    def __init__(self):
        self.calls: list[tuple] = []
        record = self._record
        self.v1 = SimpleNamespace(
            invoices=SimpleNamespace(
                create=lambda p, o=None: record("invoice", p, o, SimpleNamespace(id="in_fee")),
                finalize_invoice=lambda i, p=None, o=None: record("finalize", i, o, None),
            ),
            invoice_items=SimpleNamespace(
                create=lambda p, o=None: record("item", p, o, None)
            ),
            subscriptions=SimpleNamespace(
                retrieve=lambda i: SimpleNamespace(default_payment_method="pm_1")
            ),
        )

    def _record(self, name, params, options, result):
        self.calls.append((name, params, options))
        return result


@pytest.fixture
def env(monkeypatch):
    conn = FakeConn()
    fake = FakeStripe()
    monkeypatch.setattr(billing.db, "_conn", lambda: conn)
    monkeypatch.setattr(billing, "_client", fake)
    return SimpleNamespace(conn=conn, stripe=fake)


# ── Fee rule ──────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "savings, fee",
    [("0", "0.00"), ("20.00", "0.00"), ("20.004", "0.00"), ("20.01", "1.00"), ("100", "5.00")],
)
def test_savings_fee_threshold_is_a_cliff(savings, fee):
    assert billing.savings_fee(Decimal(savings)) == Decimal(fee)


# ── Charging a period ─────────────────────────────────────────────────


def test_fee_invoiced_once_per_period(env, monkeypatch):
    async def savings(*_):
        return Decimal("100")

    monkeypatch.setattr(billing, "ledger_savings", savings)
    for _ in range(2):  # webhook redelivery
        asyncio.run(billing.charge_savings_fee(UID, "cus_1", START, END, "pm_1"))
    names = [c[0] for c in env.stripe.calls]
    assert names == ["invoice", "item", "finalize"]
    invoice, item = env.stripe.calls[0][1], env.stripe.calls[1][1]
    assert invoice["default_payment_method"] == "pm_1"
    assert invoice["pending_invoice_items_behavior"] == "exclude"
    assert item == {**item, "amount": 500, "currency": "usd", "invoice": "in_fee"}
    assert env.conn.fees[(UID, START)] == {"fee_cents": 500, "stripe_invoice_id": "in_fee"}


def test_no_invoice_when_savings_at_or_below_threshold(env, monkeypatch):
    async def savings(*_):
        return Decimal("20")

    monkeypatch.setattr(billing, "ledger_savings", savings)
    asyncio.run(billing.charge_savings_fee(UID, "cus_1", START, END, None))
    assert env.stripe.calls == []
    assert env.conn.fees[(UID, START)]["fee_cents"] == 0


# ── Event routing ─────────────────────────────────────────────────────


def _event(kind, obj):
    return stripe.Event.construct_from(
        {"id": "evt_1", "object": "event", "type": kind, "data": {"object": obj}}, "sk_test_x"
    )


def _invoice(reason):
    return {
        "object": "invoice",
        "id": "in_renewal",
        "customer": "cus_1",
        "billing_reason": reason,
        "period_start": int(START.timestamp()),
        "period_end": int(END.timestamp()),
        "parent": {"subscription_details": {"subscription": "sub_1"}},
    }


def test_renewal_invoice_bills_the_period_that_ended(env, monkeypatch):
    charged = []

    async def charge(*args):
        charged.append(args)

    monkeypatch.setattr(billing, "charge_savings_fee", charge)
    asyncio.run(billing.handle_event(_event("invoice.created", _invoice("subscription_cycle"))))
    assert charged == [(UID, "cus_1", START, END, "pm_1")]


def test_first_invoice_is_not_a_fee_period(env, monkeypatch):
    charged = []

    async def charge(*args):
        charged.append(args)

    monkeypatch.setattr(billing, "charge_savings_fee", charge)
    asyncio.run(billing.handle_event(_event("invoice.created", _invoice("subscription_create"))))
    assert charged == []


# ── Plan sync from real Stripe object types ───────────────────────────


def _subscription(status, metadata):
    # construct_from yields the same StripeObject types the API returns.
    return stripe.Subscription.construct_from(
        {
            "id": "sub_1",
            "object": "subscription",
            "customer": "cus_1",
            "status": status,
            "cancel_at_period_end": False,
            "metadata": metadata,
            "items": {
                "object": "list",
                "data": [
                    {
                        "object": "subscription_item",
                        "price": {"object": "price", "id": "price_pro"},
                        "current_period_start": int(START.timestamp()),
                        "current_period_end": int(END.timestamp()),
                    }
                ],
            },
        },
        "sk_test_x",
    )


@pytest.mark.parametrize("metadata", [{}, {"user_id": UID}])
@pytest.mark.parametrize("status, stored", [("active", "active"), ("trialing", "active"), ("past_due", "past_due")])
def test_sync_grants_pro_from_stripe_state(env, monkeypatch, metadata, status, stored):
    async def price_id(_):
        return "price_pro"

    monkeypatch.setattr(billing, "_price_id", price_id)
    env.stripe.v1.subscriptions.retrieve = lambda _id: _subscription(status, metadata)
    asyncio.run(billing.sync_subscription("sub_1"))
    assert env.conn.plan_updates == [(UID, "pro", stored, "sub_1", START, END, False)]


# ── Webhook endpoint ──────────────────────────────────────────────────


def _signed(payload: bytes, secret: str) -> str:
    ts = int(time.time())
    sig = hmac.new(secret.encode(), f"{ts}.".encode() + payload, hashlib.sha256).hexdigest()
    return f"t={ts},v1={sig}"


def test_webhook_verifies_signature_and_ignores_redelivery(monkeypatch):
    conn = FakeConn()
    handled = []

    async def handle(event):
        handled.append(event.id)

    monkeypatch.setattr(billing.db, "_conn", lambda: conn)
    monkeypatch.setattr(billing, "_client", stripe.StripeClient("sk_test_dummy"))
    monkeypatch.setattr(billing, "WEBHOOK_SECRET", "whsec_test")
    monkeypatch.setattr(billing, "handle_event", handle)
    app = FastAPI()
    billing.install(app, lambda: None)
    client = TestClient(app)
    payload = json.dumps(
        {"id": "evt_9", "object": "event", "type": "invoice.paid", "data": {"object": {}}}
    ).encode()

    bad = client.post("/stripe/webhook", content=payload, headers={"stripe-signature": "t=1,v1=00"})
    assert bad.status_code == 400
    for _ in range(2):
        ok = client.post(
            "/stripe/webhook",
            content=payload,
            headers={"stripe-signature": _signed(payload, "whsec_test")},
        )
        assert ok.status_code == 200
    assert handled == ["evt_9"]
