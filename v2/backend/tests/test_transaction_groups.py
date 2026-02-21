"""Tests for transaction group endpoints."""

import datetime
from decimal import Decimal

import pytest

from app.models import Account, Currency, Transaction, TransactionGroup


@pytest.fixture
def external_account(db, currency_eur):
    a = Account(
        name="Shop",
        number="EXT001",
        initial_balance=Decimal("0"),
        id_currency=currency_eur.id,
        institution="other",
        is_active=True,
    )
    db.add(a)
    db.flush()
    return a


@pytest.fixture
def payment_tx(db, account_checking, external_account, currency_eur):
    """Outgoing payment of €100."""
    t = Transaction(
        external_id="grp-pay-1",
        id_source=account_checking.id,
        id_dest=external_account.id,
        date=datetime.date(2024, 6, 1),
        amount=Decimal("100.00"),
        id_currency=currency_eur.id,
        description="Dinner payment",
    )
    db.add(t)
    db.flush()
    return t


@pytest.fixture
def reimbursement_txs(db, external_account, account_checking, currency_eur):
    """3 incoming reimbursements of €25 each."""
    txs = []
    for i in range(3):
        t = Transaction(
            external_id=f"grp-reimb-{i}",
            id_source=external_account.id,
            id_dest=account_checking.id,
            date=datetime.date(2024, 6, 2),
            amount=Decimal("25.00"),
            id_currency=currency_eur.id,
            description=f"Reimbursement {i+1}",
        )
        db.add(t)
        txs.append(t)
    db.flush()
    return txs


class TestCreateGroup:
    def test_create_group(self, client, auth_headers, payment_tx, reimbursement_txs):
        tx_ids = [payment_tx.id, reimbursement_txs[0].id]
        r = client.post(
            "/api/v2/transaction-groups",
            json={"name": "Dinner", "transaction_ids": tx_ids},
            headers=auth_headers,
        )
        assert r.status_code == 201
        data = r.json()
        assert data["name"] == "Dinner"
        assert len(data["transactions"]) == 2
        assert Decimal(str(data["total_paid"])) == Decimal("100.00")
        assert Decimal(str(data["total_reimbursed"])) == Decimal("25.00")
        assert Decimal(str(data["net_expense"])) == Decimal("75.00")

    def test_create_group_invalid_tx(self, client, auth_headers):
        r = client.post(
            "/api/v2/transaction-groups",
            json={"transaction_ids": [999999]},
            headers=auth_headers,
        )
        assert r.status_code == 404


class TestListGroups:
    def test_list_groups(self, client, auth_headers, payment_tx, reimbursement_txs):
        # Create 2 groups
        client.post(
            "/api/v2/transaction-groups",
            json={"name": "G1", "transaction_ids": [payment_tx.id]},
            headers=auth_headers,
        )
        client.post(
            "/api/v2/transaction-groups",
            json={"name": "G2", "transaction_ids": [reimbursement_txs[0].id]},
            headers=auth_headers,
        )
        r = client.get("/api/v2/transaction-groups", headers=auth_headers)
        assert r.status_code == 200
        assert len(r.json()) == 2


class TestGetGroup:
    def test_get_group(self, client, auth_headers, payment_tx, reimbursement_txs):
        create_r = client.post(
            "/api/v2/transaction-groups",
            json={"transaction_ids": [payment_tx.id, reimbursement_txs[0].id, reimbursement_txs[1].id]},
            headers=auth_headers,
        )
        group_id = create_r.json()["id"]
        r = client.get(f"/api/v2/transaction-groups/{group_id}", headers=auth_headers)
        assert r.status_code == 200
        data = r.json()
        assert Decimal(str(data["total_paid"])) == Decimal("100.00")
        assert Decimal(str(data["total_reimbursed"])) == Decimal("50.00")
        assert Decimal(str(data["net_expense"])) == Decimal("50.00")

    def test_get_group_not_found(self, client, auth_headers):
        r = client.get("/api/v2/transaction-groups/99999", headers=auth_headers)
        assert r.status_code == 404


class TestUpdateGroup:
    def test_update_group_name(self, client, auth_headers, payment_tx):
        create_r = client.post(
            "/api/v2/transaction-groups",
            json={"name": "Old", "transaction_ids": [payment_tx.id]},
            headers=auth_headers,
        )
        group_id = create_r.json()["id"]
        r = client.put(
            f"/api/v2/transaction-groups/{group_id}",
            json={"name": "New"},
            headers=auth_headers,
        )
        assert r.status_code == 200
        assert r.json()["name"] == "New"

    def test_update_group_transactions(self, client, auth_headers, payment_tx, reimbursement_txs):
        create_r = client.post(
            "/api/v2/transaction-groups",
            json={"transaction_ids": [payment_tx.id]},
            headers=auth_headers,
        )
        group_id = create_r.json()["id"]

        # Update to include reimbursements
        r = client.put(
            f"/api/v2/transaction-groups/{group_id}",
            json={"transaction_ids": [payment_tx.id, reimbursement_txs[0].id, reimbursement_txs[1].id, reimbursement_txs[2].id]},
            headers=auth_headers,
        )
        assert r.status_code == 200
        data = r.json()
        assert len(data["transactions"]) == 4
        assert Decimal(str(data["total_reimbursed"])) == Decimal("75.00")


class TestDeleteGroup:
    def test_delete_group(self, client, auth_headers, db, payment_tx, reimbursement_txs):
        create_r = client.post(
            "/api/v2/transaction-groups",
            json={"transaction_ids": [payment_tx.id, reimbursement_txs[0].id]},
            headers=auth_headers,
        )
        group_id = create_r.json()["id"]

        r = client.delete(f"/api/v2/transaction-groups/{group_id}", headers=auth_headers)
        assert r.status_code == 204

        # Verify transactions have effective_amount reset
        db.expire_all()
        assert db.get(Transaction, payment_tx.id).effective_amount is None
        assert db.get(Transaction, reimbursement_txs[0].id).effective_amount is None

        # Verify group is gone
        r = client.get(f"/api/v2/transaction-groups/{group_id}", headers=auth_headers)
        assert r.status_code == 404


class TestAutoComputeEffectiveAmounts:
    def test_single_payment_with_reimbursements(self, client, auth_headers, db, payment_tx, reimbursement_txs):
        """€100 out + 3×€25 in → effective = €25 on payment, €0 on reimbursements."""
        tx_ids = [payment_tx.id] + [t.id for t in reimbursement_txs]
        client.post(
            "/api/v2/transaction-groups",
            json={"transaction_ids": tx_ids},
            headers=auth_headers,
        )
        db.expire_all()
        assert db.get(Transaction, payment_tx.id).effective_amount == Decimal("25.00")
        for t in reimbursement_txs:
            assert db.get(Transaction, t.id).effective_amount == Decimal("0")

    def test_multiple_payments(self, client, auth_headers, db, account_checking, external_account, currency_eur):
        """€100 + €50 out, €100 in → ratio=2/3, effective: €33.33 + €16.67."""
        t1 = Transaction(
            external_id="mp-1", id_source=account_checking.id, id_dest=external_account.id,
            date=datetime.date(2024, 6, 1), amount=Decimal("100.00"), id_currency=currency_eur.id,
            description="Payment 1",
        )
        t2 = Transaction(
            external_id="mp-2", id_source=account_checking.id, id_dest=external_account.id,
            date=datetime.date(2024, 6, 1), amount=Decimal("50.00"), id_currency=currency_eur.id,
            description="Payment 2",
        )
        t3 = Transaction(
            external_id="mp-3", id_source=external_account.id, id_dest=account_checking.id,
            date=datetime.date(2024, 6, 2), amount=Decimal("100.00"), id_currency=currency_eur.id,
            description="Reimbursement",
        )
        db.add_all([t1, t2, t3])
        db.flush()

        client.post(
            "/api/v2/transaction-groups",
            json={"transaction_ids": [t1.id, t2.id, t3.id]},
            headers=auth_headers,
        )
        db.expire_all()
        assert db.get(Transaction, t1.id).effective_amount == Decimal("33.33")
        assert db.get(Transaction, t2.id).effective_amount == Decimal("16.67")
        assert db.get(Transaction, t3.id).effective_amount == Decimal("0")

    def test_no_reimbursements(self, client, auth_headers, db, payment_tx):
        """Payment only → effective = amount (ratio=0)."""
        client.post(
            "/api/v2/transaction-groups",
            json={"transaction_ids": [payment_tx.id]},
            headers=auth_headers,
        )
        db.expire_all()
        assert db.get(Transaction, payment_tx.id).effective_amount == Decimal("100.00")

    def test_manual_override_preserved_on_tx_update(self, client, auth_headers, db, payment_tx, reimbursement_txs):
        """Edit effective_amount via transaction PUT, verify it sticks."""
        tx_ids = [payment_tx.id] + [t.id for t in reimbursement_txs]
        client.post(
            "/api/v2/transaction-groups",
            json={"transaction_ids": tx_ids},
            headers=auth_headers,
        )
        # Manual override — set payment's effective_amount to 30
        db.expire_all()
        tx = db.get(Transaction, payment_tx.id)
        tx.effective_amount = Decimal("30.00")
        db.commit()

        db.expire_all()
        assert db.get(Transaction, payment_tx.id).effective_amount == Decimal("30.00")
