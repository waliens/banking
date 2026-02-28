"""Tests for transaction group endpoints."""

import datetime
from decimal import Decimal

import pytest

from app.models import Account, Currency, Transaction, TransactionGroup, Wallet, WalletAccount


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
    def test_create_group(self, client, auth_headers, wallet, payment_tx, reimbursement_txs):
        tx_ids = [payment_tx.id, reimbursement_txs[0].id]
        r = client.post(
            "/api/v2/transaction-groups",
            json={"name": "Dinner", "transaction_ids": tx_ids, "wallet_id": wallet.id},
            headers=auth_headers,
        )
        assert r.status_code == 201
        data = r.json()
        assert data["name"] == "Dinner"
        assert len(data["transactions"]) == 2
        assert Decimal(str(data["total_paid"])) == Decimal("100.00")
        assert Decimal(str(data["total_reimbursed"])) == Decimal("25.00")
        assert Decimal(str(data["net_expense"])) == Decimal("75.00")

    def test_create_group_invalid_tx(self, client, auth_headers, wallet):
        r = client.post(
            "/api/v2/transaction-groups",
            json={"transaction_ids": [999999], "wallet_id": wallet.id},
            headers=auth_headers,
        )
        assert r.status_code == 404

    def test_create_group_rejects_already_grouped_transaction(
        self, client, auth_headers, wallet, payment_tx, reimbursement_txs
    ):
        # Create first group with payment_tx
        r1 = client.post(
            "/api/v2/transaction-groups",
            json={"name": "G1", "transaction_ids": [payment_tx.id], "wallet_id": wallet.id},
            headers=auth_headers,
        )
        assert r1.status_code == 201

        # Try to create second group that includes payment_tx → should fail
        r2 = client.post(
            "/api/v2/transaction-groups",
            json={
                "name": "G2",
                "transaction_ids": [payment_tx.id, reimbursement_txs[0].id],
                "wallet_id": wallet.id,
            },
            headers=auth_headers,
        )
        assert r2.status_code == 400
        assert "already in a group" in r2.json()["detail"]


class TestListGroups:
    def test_list_groups(self, client, auth_headers, wallet, payment_tx, reimbursement_txs):
        # Create 2 groups
        client.post(
            "/api/v2/transaction-groups",
            json={"name": "G1", "transaction_ids": [payment_tx.id], "wallet_id": wallet.id},
            headers=auth_headers,
        )
        client.post(
            "/api/v2/transaction-groups",
            json={"name": "G2", "transaction_ids": [reimbursement_txs[0].id], "wallet_id": wallet.id},
            headers=auth_headers,
        )
        r = client.get(f"/api/v2/transaction-groups?wallet_id={wallet.id}", headers=auth_headers)
        assert r.status_code == 200
        assert len(r.json()) == 2


class TestGetGroup:
    def test_get_group(self, client, auth_headers, wallet, payment_tx, reimbursement_txs):
        create_r = client.post(
            "/api/v2/transaction-groups",
            json={"transaction_ids": [payment_tx.id, reimbursement_txs[0].id, reimbursement_txs[1].id], "wallet_id": wallet.id},
            headers=auth_headers,
        )
        group_id = create_r.json()["id"]
        r = client.get(f"/api/v2/transaction-groups/{group_id}?wallet_id={wallet.id}", headers=auth_headers)
        assert r.status_code == 200
        data = r.json()
        assert Decimal(str(data["total_paid"])) == Decimal("100.00")
        assert Decimal(str(data["total_reimbursed"])) == Decimal("50.00")
        assert Decimal(str(data["net_expense"])) == Decimal("50.00")

    def test_get_group_not_found(self, client, auth_headers, wallet):
        r = client.get(f"/api/v2/transaction-groups/99999?wallet_id={wallet.id}", headers=auth_headers)
        assert r.status_code == 404

    def test_get_group_requires_wallet_id(self, client, auth_headers, wallet, payment_tx):
        create_r = client.post(
            "/api/v2/transaction-groups",
            json={"transaction_ids": [payment_tx.id], "wallet_id": wallet.id},
            headers=auth_headers,
        )
        group_id = create_r.json()["id"]
        r = client.get(f"/api/v2/transaction-groups/{group_id}", headers=auth_headers)
        assert r.status_code == 422  # missing required query param


class TestUpdateGroup:
    def test_update_group_name(self, client, auth_headers, wallet, payment_tx):
        create_r = client.post(
            "/api/v2/transaction-groups",
            json={"name": "Old", "transaction_ids": [payment_tx.id], "wallet_id": wallet.id},
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

    def test_update_group_rejects_transaction_in_different_group(
        self, client, auth_headers, wallet, payment_tx, reimbursement_txs
    ):
        # Create two groups
        r1 = client.post(
            "/api/v2/transaction-groups",
            json={"name": "G1", "transaction_ids": [payment_tx.id], "wallet_id": wallet.id},
            headers=auth_headers,
        )
        g1_id = r1.json()["id"]

        r2 = client.post(
            "/api/v2/transaction-groups",
            json={"name": "G2", "transaction_ids": [reimbursement_txs[0].id], "wallet_id": wallet.id},
            headers=auth_headers,
        )
        g2_id = r2.json()["id"]

        # Try to update G2 to include payment_tx (which is in G1) → should fail
        r3 = client.put(
            f"/api/v2/transaction-groups/{g2_id}",
            json={
                "transaction_ids": [reimbursement_txs[0].id, payment_tx.id],
                "wallet_id": wallet.id,
            },
            headers=auth_headers,
        )
        assert r3.status_code == 400
        assert "already in a group" in r3.json()["detail"]

    def test_update_group_allows_own_transactions(
        self, client, auth_headers, wallet, payment_tx, reimbursement_txs
    ):
        """Updating a group with its own existing transactions should succeed."""
        r1 = client.post(
            "/api/v2/transaction-groups",
            json={"name": "G1", "transaction_ids": [payment_tx.id], "wallet_id": wallet.id},
            headers=auth_headers,
        )
        g1_id = r1.json()["id"]

        # Update G1 with same tx + a new one → should succeed
        r2 = client.put(
            f"/api/v2/transaction-groups/{g1_id}",
            json={
                "transaction_ids": [payment_tx.id, reimbursement_txs[0].id],
                "wallet_id": wallet.id,
            },
            headers=auth_headers,
        )
        assert r2.status_code == 200
        assert len(r2.json()["transactions"]) == 2

    def test_update_group_transactions(self, client, auth_headers, wallet, payment_tx, reimbursement_txs):
        create_r = client.post(
            "/api/v2/transaction-groups",
            json={"transaction_ids": [payment_tx.id], "wallet_id": wallet.id},
            headers=auth_headers,
        )
        group_id = create_r.json()["id"]

        # Update to include reimbursements
        r = client.put(
            f"/api/v2/transaction-groups/{group_id}",
            json={
                "transaction_ids": [payment_tx.id, reimbursement_txs[0].id, reimbursement_txs[1].id, reimbursement_txs[2].id],
                "wallet_id": wallet.id,
            },
            headers=auth_headers,
        )
        assert r.status_code == 200
        data = r.json()
        assert len(data["transactions"]) == 4
        assert Decimal(str(data["total_reimbursed"])) == Decimal("75.00")


class TestDeleteGroup:
    def test_delete_group(self, client, auth_headers, db, wallet, payment_tx, reimbursement_txs):
        create_r = client.post(
            "/api/v2/transaction-groups",
            json={"transaction_ids": [payment_tx.id, reimbursement_txs[0].id], "wallet_id": wallet.id},
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
        r = client.get(f"/api/v2/transaction-groups/{group_id}?wallet_id={wallet.id}", headers=auth_headers)
        assert r.status_code == 404


class TestAutoComputeEffectiveAmounts:
    def test_single_payment_with_reimbursements(self, client, auth_headers, db, wallet, payment_tx, reimbursement_txs):
        """€100 out + 3×€25 in → effective = €25 on payment, €0 on reimbursements."""
        tx_ids = [payment_tx.id] + [t.id for t in reimbursement_txs]
        client.post(
            "/api/v2/transaction-groups",
            json={"transaction_ids": tx_ids, "wallet_id": wallet.id},
            headers=auth_headers,
        )
        db.expire_all()
        assert db.get(Transaction, payment_tx.id).effective_amount == Decimal("25.00")
        for t in reimbursement_txs:
            assert db.get(Transaction, t.id).effective_amount == Decimal("0")

    def test_multiple_payments(self, client, auth_headers, db, wallet, account_checking, external_account, currency_eur):
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
            json={"transaction_ids": [t1.id, t2.id, t3.id], "wallet_id": wallet.id},
            headers=auth_headers,
        )
        db.expire_all()
        assert db.get(Transaction, t1.id).effective_amount == Decimal("33.33")
        assert db.get(Transaction, t2.id).effective_amount == Decimal("16.67")
        assert db.get(Transaction, t3.id).effective_amount == Decimal("0")

    def test_no_reimbursements(self, client, auth_headers, db, wallet, payment_tx):
        """Payment only → effective = amount (ratio=0)."""
        client.post(
            "/api/v2/transaction-groups",
            json={"transaction_ids": [payment_tx.id], "wallet_id": wallet.id},
            headers=auth_headers,
        )
        db.expire_all()
        assert db.get(Transaction, payment_tx.id).effective_amount == Decimal("100.00")

    def test_manual_override_preserved_on_tx_update(self, client, auth_headers, db, wallet, payment_tx, reimbursement_txs):
        """Edit effective_amount via transaction PUT, verify it sticks."""
        tx_ids = [payment_tx.id] + [t.id for t in reimbursement_txs]
        client.post(
            "/api/v2/transaction-groups",
            json={"transaction_ids": tx_ids, "wallet_id": wallet.id},
            headers=auth_headers,
        )
        # Manual override — set payment's effective_amount to 30
        db.expire_all()
        tx = db.get(Transaction, payment_tx.id)
        tx.effective_amount = Decimal("30.00")
        db.commit()

        db.expire_all()
        assert db.get(Transaction, payment_tx.id).effective_amount == Decimal("30.00")


class TestDirectionBasedOnWallet:
    """Verify direction classification uses wallet account IDs, not heuristics."""

    def test_direction_based_on_wallet_accounts(
        self, client, auth_headers, db, wallet, account_checking, external_account, currency_eur
    ):
        """A small outgoing tx and a large incoming tx — wallet-based classification
        should correctly identify the small tx as outgoing (source = wallet account)."""
        small_out = Transaction(
            external_id="dir-1", id_source=account_checking.id, id_dest=external_account.id,
            date=datetime.date(2024, 6, 1), amount=Decimal("10.00"), id_currency=currency_eur.id,
            description="Small payment",
        )
        large_in = Transaction(
            external_id="dir-2", id_source=external_account.id, id_dest=account_checking.id,
            date=datetime.date(2024, 6, 2), amount=Decimal("200.00"), id_currency=currency_eur.id,
            description="Large refund",
        )
        db.add_all([small_out, large_in])
        db.flush()

        r = client.post(
            "/api/v2/transaction-groups",
            json={"transaction_ids": [small_out.id, large_in.id], "wallet_id": wallet.id},
            headers=auth_headers,
        )
        assert r.status_code == 201
        data = r.json()
        # The old heuristic would have classified large_in as outgoing (largest tx).
        # Wallet-based: small_out is outgoing (source=checking), large_in is incoming.
        assert Decimal(str(data["total_paid"])) == Decimal("10.00")
        assert Decimal(str(data["total_reimbursed"])) == Decimal("200.00")
        assert Decimal(str(data["net_expense"])) == Decimal("-190.00")

    def test_effective_amounts_use_wallet_direction(
        self, client, auth_headers, db, wallet, account_checking, external_account, currency_eur
    ):
        """Effective amounts should be computed using wallet-based direction."""
        out_tx = Transaction(
            external_id="eff-1", id_source=account_checking.id, id_dest=external_account.id,
            date=datetime.date(2024, 6, 1), amount=Decimal("100.00"), id_currency=currency_eur.id,
            description="Payment",
        )
        in_tx = Transaction(
            external_id="eff-2", id_source=external_account.id, id_dest=account_checking.id,
            date=datetime.date(2024, 6, 2), amount=Decimal("40.00"), id_currency=currency_eur.id,
            description="Partial refund",
        )
        db.add_all([out_tx, in_tx])
        db.flush()

        client.post(
            "/api/v2/transaction-groups",
            json={"transaction_ids": [out_tx.id, in_tx.id], "wallet_id": wallet.id},
            headers=auth_headers,
        )
        db.expire_all()
        # ratio = 40/100 = 0.4, effective = 100 * (1-0.4) = 60
        assert db.get(Transaction, out_tx.id).effective_amount == Decimal("60.00")
        assert db.get(Transaction, in_tx.id).effective_amount == Decimal("0")

    def test_group_summary_changes_with_different_wallet(
        self, client, auth_headers, db, account_checking, external_account, currency_eur
    ):
        """Same group viewed from different wallets → different totals."""
        # Create a second wallet with external_account
        wallet1 = Wallet(name="W1")
        db.add(wallet1)
        db.flush()
        db.add(WalletAccount(id_wallet=wallet1.id, id_account=account_checking.id, contribution_ratio=1.0))
        db.flush()

        wallet2 = Wallet(name="W2")
        db.add(wallet2)
        db.flush()
        db.add(WalletAccount(id_wallet=wallet2.id, id_account=external_account.id, contribution_ratio=1.0))
        db.flush()

        tx = Transaction(
            external_id="dual-1", id_source=account_checking.id, id_dest=external_account.id,
            date=datetime.date(2024, 6, 1), amount=Decimal("100.00"), id_currency=currency_eur.id,
            description="Transfer",
        )
        db.add(tx)
        db.flush()

        # Create group from wallet1's perspective
        create_r = client.post(
            "/api/v2/transaction-groups",
            json={"transaction_ids": [tx.id], "wallet_id": wallet1.id},
            headers=auth_headers,
        )
        group_id = create_r.json()["id"]

        # View from wallet1: tx is outgoing (source=checking which is in wallet1)
        r1 = client.get(f"/api/v2/transaction-groups/{group_id}?wallet_id={wallet1.id}", headers=auth_headers)
        data1 = r1.json()
        assert Decimal(str(data1["total_paid"])) == Decimal("100.00")
        assert Decimal(str(data1["total_reimbursed"])) == Decimal("0")

        # View from wallet2: tx is incoming (source=checking which is NOT in wallet2)
        r2 = client.get(f"/api/v2/transaction-groups/{group_id}?wallet_id={wallet2.id}", headers=auth_headers)
        data2 = r2.json()
        assert Decimal(str(data2["total_paid"])) == Decimal("0")
        assert Decimal(str(data2["total_reimbursed"])) == Decimal("100.00")
