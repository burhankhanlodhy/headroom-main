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
        self.failures: list[str] = []

    def _by_invoice(self, invoice_id):
        return next((r for r in self.fees.values() if r["stripe_invoice_id"] == invoice_id), None)

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
                (args[0], args[1]),
                {
                    "fee_cents": args[4],
                    "stripe_invoice_id": None,
                    "payment_status": args[5],
                    "payment_failed_at": None,
                    "invoice_url": None,
                },
            )
        elif "SET stripe_invoice_id=" in sql:
            self.fees[(args[0], args[1])]["stripe_invoice_id"] = args[2]
        elif "SET invoice_url=" in sql:
            self._by_invoice(args[0])["invoice_url"] = args[1]
        elif "SET payment_status='failed'" in sql:
            row = self._by_invoice(args[0])
            if row and row["payment_status"] not in ("paid", "void"):
                row["payment_status"] = "failed"
                row["payment_failed_at"] = row["payment_failed_at"] or len(self.failures) + 1
                row["invoice_url"] = args[1] or row["invoice_url"]
            self.failures.append(args[0])
        elif "SET payment_status=$2" in sql:
            row = self._by_invoice(args[0])
            if row:
                row.update(payment_status=args[1], payment_failed_at=None)
        elif "UPDATE core.subscriptions SET plan=" in sql:
            self.plan_updates.append(args)
        else:
            raise AssertionError(sql)


class FakeStripe:
    def __init__(self, conn=None):
        self.calls: list[tuple] = []
        self.linked_at_finalize = None
        record = self._record

        def finalize(invoice_id, params=None, options=None):
            # Payment is attempted on finalize; its webhook needs the link.
            if conn is not None:
                self.linked_at_finalize = conn._by_invoice(invoice_id) is not None
            return record(
                "finalize", invoice_id, options, SimpleNamespace(hosted_invoice_url="https://pay.test/in_fee")
            )

        self.v1 = SimpleNamespace(
            invoices=SimpleNamespace(
                create=lambda p, o=None: record("invoice", p, o, SimpleNamespace(id="in_fee")),
                finalize_invoice=finalize,
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
    fake = FakeStripe(conn)
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
    fee = env.conn.fees[(UID, START)]
    assert (fee["fee_cents"], fee["stripe_invoice_id"], fee["payment_status"]) == (500, "in_fee", "pending")
    assert fee["invoice_url"] == "https://pay.test/in_fee"
    # Linked before finalize, so the payment webhook can find the row.
    assert env.stripe.linked_at_finalize is True


def test_no_invoice_when_savings_at_or_below_threshold(env, monkeypatch):
    async def savings(*_):
        return Decimal("20")

    monkeypatch.setattr(billing, "ledger_savings", savings)
    asyncio.run(billing.charge_savings_fee(UID, "cus_1", START, END, None))
    assert env.stripe.calls == []
    assert env.conn.fees[(UID, START)]["fee_cents"] == 0
    assert env.conn.fees[(UID, START)]["payment_status"] == "none"


# ── Fee payment tracking ──────────────────────────────────────────────


def _fee_invoice(url="https://pay.test/in_fee"):
    return stripe.Invoice.construct_from(
        {"id": "in_fee", "object": "invoice", "customer": "cus_1", "hosted_invoice_url": url},
        "sk_test_x",
    )


@pytest.fixture
def charged(env, monkeypatch):
    async def savings(*_):
        return Decimal("50")

    monkeypatch.setattr(billing, "ledger_savings", savings)
    asyncio.run(billing.charge_savings_fee(UID, "cus_1", START, END, None))
    return env.conn.fees[(UID, START)]


def test_failed_fee_keeps_first_failure_time_across_retries(env, charged):
    for _ in range(3):  # Stripe retries
        asyncio.run(billing.handle_event(_event("invoice.payment_failed", _fee_invoice())))
    assert charged["payment_status"] == "failed"
    assert charged["payment_failed_at"] == 1  # grace clock starts at the first failure


@pytest.mark.parametrize("kind, status", [("invoice.paid", "paid"), ("invoice.voided", "void")])
def test_settling_the_fee_clears_the_failure(env, charged, kind, status):
    asyncio.run(billing.handle_event(_event("invoice.payment_failed", _fee_invoice())))
    asyncio.run(billing.handle_event(_event(kind, _fee_invoice())))
    assert (charged["payment_status"], charged["payment_failed_at"]) == (status, None)


def test_late_failure_event_does_not_reopen_a_paid_fee(env, charged):
    asyncio.run(billing.handle_event(_event("invoice.paid", _fee_invoice())))
    asyncio.run(billing.handle_event(_event("invoice.payment_failed", _fee_invoice())))
    assert charged["payment_status"] == "paid"


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


def _subscription(status, metadata, *, cancel_at=None, cancel_at_period_end=False):
    # construct_from yields the same StripeObject types the API returns.
    return stripe.Subscription.construct_from(
        {
            "id": "sub_1",
            "object": "subscription",
            "customer": "cus_1",
            "status": status,
            "cancel_at_period_end": cancel_at_period_end,
            "cancel_at": cancel_at,
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
    assert env.conn.plan_updates == [(UID, "pro", stored, "sub_1", START, END, False, None)]


@pytest.mark.parametrize(
    "fields",
    [
        {"cancel_at": int(END.timestamp())},  # Customer Portal on newer API versions
        {"cancel_at_period_end": True},  # older style flag
    ],
)
def test_sync_records_scheduled_cancellation(env, monkeypatch, fields):
    async def price_id(_):
        return "price_pro"

    monkeypatch.setattr(billing, "_price_id", price_id)
    env.stripe.v1.subscriptions.retrieve = lambda _id: _subscription("active", {}, **fields)
    asyncio.run(billing.sync_subscription("sub_1"))
    # Still Pro until the cancellation date, which is recorded.
    assert env.conn.plan_updates == [(UID, "pro", "active", "sub_1", START, END, True, END)]


@pytest.mark.parametrize(
    "fields, update",
    [
        ({"cancel_at": int(END.timestamp())}, {"cancel_at": ""}),
        ({"cancel_at_period_end": True}, {"cancel_at_period_end": False}),
    ],
)
def test_renew_clears_the_scheduled_cancellation(env, monkeypatch, fields, update):
    async def price_id(_):
        return "price_pro"

    updates = []
    state = {"sub": _subscription("active", {}, **fields)}

    def apply(sub_id, params):
        updates.append(params)
        state["sub"] = _subscription("active", {})

    monkeypatch.setattr(billing, "_price_id", price_id)
    env.stripe.v1.subscriptions.retrieve = lambda _id: state["sub"]
    env.stripe.v1.subscriptions.update = apply
    asyncio.run(billing.renew_subscription("sub_1"))
    assert updates == [update]
    assert env.conn.plan_updates[-1] == (UID, "pro", "active", "sub_1", START, END, False, None)


def test_renew_refuses_an_ended_subscription(env):
    env.stripe.v1.subscriptions.retrieve = lambda _id: _subscription("canceled", {})
    with pytest.raises(billing.HTTPException) as exc:
        asyncio.run(billing.renew_subscription("sub_1"))
    assert exc.value.status_code == 409


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
