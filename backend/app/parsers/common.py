import csv
import re
from collections.abc import Generator
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal


@dataclass
class ParsedTransaction:
    """Intermediate representation of a parsed transaction before DB insertion."""

    external_id: str
    source_number: str | None
    source_name: str | None
    dest_number: str | None
    dest_name: str | None
    date: date
    amount: Decimal
    currency: str
    description: str
    data_source: str
    raw_metadata: dict[str, object] = field(default_factory=dict)


def sanitize(e: str) -> str | None:
    cleaned = re.sub(r"\s+", " ", e.strip())
    return None if len(cleaned) == 0 else cleaned


def sanitize_number(e: str) -> str | None:
    cleaned = re.sub(r"\s+", "", e.strip())
    return None if len(cleaned) == 0 else cleaned


def parse_csv_file(
    filepath: str, encoding: str = "latin1", header_length: int = 13, skip_header: bool = True
) -> Generator[list[str], None, None]:
    with open(filepath, "r", encoding=encoding) as f:
        reader = csv.reader(f, delimiter=";")
        for i, row in enumerate(reader):
            if skip_header and i < header_length:
                continue
            yield row


def parse_date_str(s: str) -> date:
    sanitized = sanitize(s)
    assert sanitized is not None, f"Cannot parse empty date string: {s!r}"
    s_sanitized = sanitized.replace("-", "/")
    try:
        from datetime import datetime

        return datetime.strptime(s_sanitized, "%d/%m/%Y").date()
    except ValueError:
        from datetime import datetime

        return datetime.strptime(s_sanitized, "%d/%m/%y").date()
