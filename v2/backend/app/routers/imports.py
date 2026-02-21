import os
import tempfile

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models import User
from app.parsers import belfius, ing, mastercard
from app.services.import_service import import_parsed_transactions

router = APIRouter()


@router.post("/upload")
async def upload_files(
    files: list[UploadFile],
    format: str = Query(...),
    id_mscard_account: int | None = Query(default=None),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict[str, object]:
    if format not in {"belfius", "ing", "mastercard_pdf"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unsupported format: {format}")

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
            transactions = import_parsed_transactions(db, parsed, "belfius")

        elif format == "ing":
            if not ing.check_files(tmpdir):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="File format not matching ING data source"
                )
            parsed = ing.parse_folder(tmpdir)
            transactions = import_parsed_transactions(db, parsed, "ing")

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
            transactions = import_parsed_transactions(db, parsed, "mastercard")

    return {"status": "ok", "imported": len(transactions)}
