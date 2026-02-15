"""MasterCard PDF parser — ported from v1 server/impl/mastercard.py.

Parses MasterCard statement PDFs into structured transaction data.
"""

import os
import re
from collections import defaultdict
from datetime import date, datetime
from decimal import Decimal
from io import StringIO
from typing import Any

from bs4 import BeautifulSoup
from pdfminer.converter import HTMLConverter
from pdfminer.layout import LAParams
from pdfminer.pdfinterp import PDFPageInterpreter, PDFResourceManager
from pdfminer.pdfpage import PDFPage

from app.parsers.common import ParsedTransaction

SMALL_DATE_PATTERN = r"^[0-9]{2}/[0-9]{2}$"

# Type alias for BeautifulSoup Tag (avoid strict import issues)
Tag = Any


def _pdf2soups(filename: str) -> list[BeautifulSoup]:
    outfp = StringIO()
    rsrcmgr = PDFResourceManager()
    laparams = LAParams()
    device = HTMLConverter(rsrcmgr, outfp, laparams=laparams)
    pages: list[BeautifulSoup] = []
    with open(filename, "rb") as fp:
        interpreter = PDFPageInterpreter(rsrcmgr, device)
        for page in PDFPage.get_pages(fp, set()):
            interpreter.process_page(page)
            outfp.seek(0)
            pages.append(BeautifulSoup(outfp, "html.parser"))
            outfp.truncate(0)
    return pages


def _extract_pos(div: Tag) -> tuple[int, int]:
    style = div.attrs["style"]
    style_dict = {s.split(":")[0].strip(): s.split(":")[1].strip() for s in style.split(";") if len(s.strip()) > 0}
    return int(style_dict["top"][:-2]), int(style_dict["left"][:-2])


def _index_rows(divs: list[Tag], first_div_index: int) -> tuple[dict[int, int], int]:
    top_div = divs[first_div_index]
    top_y, top_x = _extract_pos(top_div)
    y_to_row_index: dict[int, int] = {}
    curr_div_index = first_div_index
    index_last_row = first_div_index
    max_y = top_y - 1
    pattern = re.compile(SMALL_DATE_PATTERN)
    while curr_div_index < len(divs):
        div = divs[curr_div_index]
        div_y, div_x = _extract_pos(div)
        if div_y > max_y and div_x == top_x and pattern.match(div.text.strip()) is not None:
            max_y = div_y
            index_last_row = curr_div_index
            y_to_row_index[div_y] = len(y_to_row_index)
        curr_div_index += 1
    return y_to_row_index, index_last_row


def _get_closest_y(index: dict[int, int], y: int, eps: int = 1) -> int:
    if y in index:
        return y
    sorted_keys = sorted(index.keys(), key=lambda k: abs(k - y))
    if sorted_keys and abs(sorted_keys[0] - y) <= eps:
        return sorted_keys[0]
    return -1


def _parse_amount(s: str) -> tuple[Decimal, str]:
    match = re.match(r"^([0-9]{1,3}(?:\.[0-9]{3})?(?:,[0-9]*)?)\s*([A-Z]+)\s*([-+])$", s)
    if match is None:
        raise ValueError(f"cannot parse amount '{s}'")
    amount = Decimal(match.group(1).replace(".", "").replace(",", "."))
    if match.group(3) == "-":
        amount *= -1
    return amount, match.group(2)


def _process_dates(date1: str, date2: str, _from: date, _to: date) -> tuple[date, date]:
    day1, month1 = map(int, date1.split("/"))
    day2, month2 = map(int, date2.split("/"))
    fdate1 = date(_from.year if _from.month == month1 else _to.year, month1, day1)
    fdate2 = date(_from.year if _from.month == month2 else _to.year, month2, day2)
    if fdate1 > fdate2:
        fdate1, fdate2 = fdate2, fdate1
    return fdate1, fdate2


def _closing_debit_dates(page_soup: BeautifulSoup) -> dict[str, date]:
    divs = page_soup.find_all("div")
    closings = [d for d in divs if d.text.strip() == "Date de clôture"]
    debits = [d for d in divs if d.text.strip() == "Date de débit"]
    if len(closings) != 1 or len(debits) != 1:
        raise ValueError("no or several match(es) for closing and debit dates fields")
    closing_y, _ = _extract_pos(closings[0])
    debit_y, _ = _extract_pos(debits[0])
    date_pattern = re.compile(r"[0-9]{2}/[0-9]{2}/[0-9]{4}")
    found_divs = [
        d for d in divs if date_pattern.match(d.text.strip()) is not None and _extract_pos(d)[0] in {closing_y, debit_y}
    ]
    if len(found_divs) != 2:
        raise ValueError("did not find date divs for debit and closing")
    if _extract_pos(found_divs[0])[0] == debit_y:
        debit_div, closing_div = found_divs
    else:
        closing_div, debit_div = found_divs
    return {
        "closing_date": datetime.strptime(closing_div.text.strip(), "%d/%m/%Y").date(),
        "debit_date": datetime.strptime(debit_div.text.strip(), "%d/%m/%Y").date(),
    }


def _transactions_date_range(page_soup: BeautifulSoup) -> list[date]:
    filtered = [div for div in page_soup.find_all("div") if div.text.startswith("Transactions du")]
    if len(filtered) != 1:
        raise ValueError("transaction date range div cannot be found")
    matches = re.findall(r"([0-9]{2})/([0-9]{2})/([0-9]{4})", filtered[0].text)
    return [date(year=int(m[2]), month=int(m[1]), day=int(m[0])) for m in matches]


def _parse_page_transactions(page_soup: BeautifulSoup) -> list[dict[str, Any]]:
    divs = page_soup.find_all("div")

    index_first_row = 0
    small_date_pattern = re.compile(SMALL_DATE_PATTERN)
    while small_date_pattern.match(divs[index_first_row].text.strip()) is None:
        index_first_row += 1

    y_to_row_index, _ = _index_rows(divs, index_first_row)

    data = defaultdict(list)
    for div_index in range(index_first_row, len(divs)):
        div = divs[div_index]
        y, _ = _extract_pos(div)
        actual_y = _get_closest_y(y_to_row_index, y)
        if actual_y < 0:
            continue
        data[y_to_row_index[actual_y]].append(div)

    debit_closing = _closing_debit_dates(page_soup)
    date_start, date_end = _transactions_date_range(page_soup)

    formatted = []
    for t_divs in data.values():
        t_data = [d.text.strip() for d in sorted(t_divs, key=lambda div: _extract_pos(div)[1])]
        early_date, late_date = _process_dates(t_data[0], t_data[1], date_start, date_end)

        c_data = {}
        if len(t_data) > 6:
            s = re.sub(r"\s+", " ", t_data[5])
            match = re.match(r".*[0-9]([a-z]+)$", s, re.IGNORECASE)
            if match:
                src_currency = match.group(1)
                splitted = s.split(src_currency)
                c_data["original_amount"] = str(Decimal(splitted[0].strip().replace(".", "").replace(",", ".")))
                c_data["original_currency"] = src_currency
                c_data["rate_to_final"] = splitted[1].rsplit("=", 1)[1].strip()

        amount, currency = _parse_amount(t_data[-1])

        f_data = {
            "when": late_date,
            "value_date": early_date,
            "account": re.sub(r"([\r\n]+|\(Via.*\))", "", t_data[2]).strip(),
            "country_or_site": t_data[2],
            "country_code": t_data[4],
            "amount": amount,
            "currency": currency,
            **c_data,
            **debit_closing,
        }
        formatted.append(f_data)
    return formatted


def _ms_identifier(t: dict[str, Any], index: int) -> str:
    account = t["account"]
    return re.sub(
        r"\s+",
        "",
        f"mastercard/{t['amount']}/{account}/{t['closing_date'].isoformat()}/{t['debit_date'].isoformat()}/{t['when'].isoformat()}/{t['value_date'].isoformat()}/{t['country_code']}/{t['country_or_site']}/{index}",
    )


def parse_pdf(filename: str) -> list[dict[str, Any]]:
    pages = _pdf2soups(filename)
    all_transactions = []
    for page_soup in pages:
        if len([div for div in page_soup.find_all("div") if div.text.startswith("Transactions -")]) > 0:
            all_transactions.extend(_parse_page_transactions(page_soup))
    return all_transactions


def parse_folder(dirname: str) -> tuple[list[dict[str, Any]], set[str], dict[str, str]]:
    """Parse all PDFs in a folder.

    Returns:
        (transactions, account_names, account2currency)
    """
    transactions = []
    account_names = set()
    account2currency = {}

    for filename in os.listdir(dirname):
        if not filename.lower().endswith(".pdf"):
            continue
        page_transactions = parse_pdf(os.path.join(dirname, filename))
        for i, t in enumerate(page_transactions):
            t["index"] = i
            t["external_id"] = _ms_identifier(t, i)
            account2currency[t["account"]] = t.get("original_currency", t["currency"])
            account_names.add(t["account"])
        transactions.extend(page_transactions)

    return transactions, account_names, account2currency
