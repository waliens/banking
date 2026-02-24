import os
import tempfile

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models import Account, ImportRecord, Transaction, User
from app.parsers import belfius, ing, mastercard
from app.schemas.import_record import ImportRecordResponse
from app.schemas.account import AccountResponse
from app.schemas.transaction import TransactionResponse
from app.services.import_service import import_parsed_transactions

router = APIRouter()


@router.post("/upload", response_model=ImportRecordResponse)
async def upload_files(
    files: list[UploadFile],
    format: str = Query(...),
    id_mscard_account: int | None = Query(default=None),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> ImportRecord:
    if format not in {"belfius", "ing", "mastercard_pdf"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unsupported format: {format}")

    filenames = [f.filename or f"file_{i}" for i, f in enumerate(files)]

    with tempfile.TemporaryDirectory() as tmpdir:
        # save uploaded files
        for i, file in enumerate(files):
            ext = os.path.splitext(file.filename or "")[1] or ""
            filepath = os.path.join(tmpdir, f"{i}{ext}")
            content = await file.read()
            with open(filepath, "wb") as f:
                f.write(content)

        if format == "belfius":
            if not belfius.check_files(tmpdir):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="File format not matching Belfius data source"
                )
            parsed = belfius.parse_folder(tmpdir)
            import_record = import_parsed_transactions(db, parsed, "belfius", filenames=filenames)

        elif format == "ing":
            if not ing.check_files(tmpdir):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="File format not matching ING data source"
                )
            parsed = ing.parse_folder(tmpdir)
            import_record = import_parsed_transactions(db, parsed, "ing", filenames=filenames)

        elif format == "mastercard_pdf":
            if id_mscard_account is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="id_mscard_account required for MasterCard import"
                )
            raw_transactions, account_names, account2currency = mastercard.parse_folder(tmpdir)

            # convert mastercard dicts to ParsedTransactions
            from app.parsers.common import ParsedTransaction

            parsed = []
            for t in raw_transactions:
                amount = t["amount"]
                src_name, dest_name = None, t["account"]
                if amount > 0:
                    src_name, dest_name = t["account"], None

                parsed.append(
                    ParsedTransaction(
                        external_id=t["external_id"],
                        source_number=None,
                        source_name=src_name,
                        dest_number=None,
                        dest_name=dest_name,
                        date=t["when"],
                        amount=amount.copy_abs(),
                        currency=t["currency"],
                        description="",
                        data_source="mastercard",
                        raw_metadata={
                            "country_code": t.get("country_code"),
                            "country_or_site": t.get("country_or_site"),
                            "closing_date": t["closing_date"].isoformat(),
                            "debit_date": t["debit_date"].isoformat(),
                            "value_date": t["value_date"].isoformat(),
                            **(
                                {
                                    "original_amount": t["original_amount"],
                                    "original_currency": t["original_currency"],
                                    "rate_to_final": t["rate_to_final"],
                                }
                                if "original_amount" in t
                                else {}
                            ),
                        },
                    )
                )
            import_record = import_parsed_transactions(db, parsed, "mastercard", filenames=filenames)

    return import_record


@router.get("", response_model=list[ImportRecordResponse])
def list_imports(
    start: int = 0,
    count: int = 20,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> list[ImportRecord]:
    q = select(ImportRecord).order_by(ImportRecord.created_at.desc()).offset(start).limit(count)
    return list(db.execute(q).scalars().all())


@router.get("/{import_id}", response_model=ImportRecordResponse)
def get_import(
    import_id: int,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> ImportRecord:
    record = db.get(ImportRecord, import_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Import record not found")
    return record


@router.get("/{import_id}/transactions", response_model=list[TransactionResponse])
def get_import_transactions(
    import_id: int,
    start: int = 0,
    count: int = 50,
    duplicate_only: bool = False,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> list[Transaction]:
    record = db.get(ImportRecord, import_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Import record not found")

    q = select(Transaction).where(Transaction.id_import == import_id)
    if duplicate_only:
        q = q.where(Transaction.id_duplicate_of.is_not(None))
    else:
        q = q.where(Transaction.id_duplicate_of.is_(None))
    q = q.order_by(Transaction.date.desc(), Transaction.id.desc()).offset(start).limit(count)
    return list(db.execute(q).scalars().unique().all())


@router.get("/{import_id}/accounts", response_model=list[AccountResponse])
def get_import_accounts(
    import_id: int,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> list[Account]:
    record = db.get(ImportRecord, import_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Import record not found")

    # Find accounts that were first seen in transactions from this import
    account_ids = (
        db.execute(
            select(Transaction.id_source)
            .where(Transaction.id_import == import_id, Transaction.id_source.is_not(None))
            .union(
                select(Transaction.id_dest).where(
                    Transaction.id_import == import_id, Transaction.id_dest.is_not(None)
                )
            )
        )
        .scalars()
        .all()
    )
    if not account_ids:
        return []
    accounts = db.execute(select(Account).where(Account.id.in_(account_ids))).scalars().unique().all()
    return list(accounts)
