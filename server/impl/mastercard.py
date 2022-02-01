import re
import os
from collections import defaultdict
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from io import StringIO
from bs4 import BeautifulSoup
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from pdfminer.converter import HTMLConverter
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter

SMALL_DATE_PATTERN = r"^[0-9]{2}/[0-9]{2}$"


def ms_identifier(t):
  return re.sub(r"\s+", "", "mastercard/{}/{}/{}/{}/{}/{}/{}/{}".format(
    t["amount"],
    t["account"],
    t["closing_date"].strftime("%d-%m-%Y"),
    t["debit_date"].strftime("%d-%m-%Y"),
    t["when"].strftime("%d-%m-%Y"),
    t["value_date"].strftime("%d-%m-%Y"),
    t["country_code"],
    t["country_or_site"]
  ))


def pdf2soups(filename):
  outfp = StringIO()
  rsrcmgr = PDFResourceManager()
  laparams = LAParams()
  device = HTMLConverter(rsrcmgr, outfp,  laparams=laparams)
  pages = list()
  with open(filename, 'rb') as fp:
    interpreter = PDFPageInterpreter(rsrcmgr, device)
    for page in PDFPage.get_pages(fp, set()):
      interpreter.process_page(page)
      outfp.seek(0)
      pages.append(BeautifulSoup(outfp, 'html.parser'))
      outfp.truncate(0)
  return pages


class PdfPageType(Enum):
  # contains actual transactions
  TRANSAC = "transactions"
  # contains only summary
  SUMMARY = "summary"


def extract_pos(div):
  style = div.attrs["style"]
  style_dict = {s.split(":")[0].strip(): s.split(":")[1].strip() for s in style.split(";") if len(s.strip()) > 0}
  return int(style_dict['top'][:-2]), int(style_dict['left'][:-2])


def index_rows(divs, first_div_index):
  top_div = divs[first_div_index]
  top_y, top_x = extract_pos(top_div)
  y_to_row_index = dict()

  curr_div_index = first_div_index
  index_last_row = first_div_index
  max_y = top_y - 1
  while curr_div_index < len(divs):
    div = divs[curr_div_index]
    div_y, div_x = extract_pos(div)

    pattern = re.compile(SMALL_DATE_PATTERN)
    if div_y > max_y and div_x == top_x and pattern.match(div.text.strip()) is not None:
      max_y = div_y
      index_last_row = curr_div_index
      y_to_row_index[div_y] = len(y_to_row_index)

    curr_div_index += 1

  return y_to_row_index, index_last_row


def get_closest_y_from_index(index, y, eps=1):
  if y in index:
    return y
  else:
    sorted_keys = sorted(enumerate(index.keys()), key=lambda k: abs(k[1] - y))
    found_y = sorted_keys[0][1]
    if abs(found_y - y) > eps:
      return -1
    else:
      return found_y


def parse_conversion_data(s):
  s = re.sub("\s+", " ", s)
  match = re.match(r".*[0-9]([a-z]+)$", s, re.IGNORECASE)
  if match is None:
    raise ValueError("no conversion data in '{}'".format(s))
  src_currency = match.group(1)
  splitted = s.split(src_currency)
  original_amount = splitted[0].strip()
  rate = splitted[1].rsplit("=", 1)[1].strip()
  return Decimal(original_amount.replace(",", ".")), src_currency, rate


def parse_amount(s):
  match = re.match("^([0-9]+(?:,[0-9]+))\s*([A-Z]+)\s*([-+])$", s)
  if match is None:
    raise ValueError("cannot parse amount '{}'".format(s))
  amount = Decimal(match.group(1).replace(",","."))
  if match.group(3) == "-":
    amount *= -1
  return amount, match.group(2)


def process_dates(date1, date2, _from, _to):
  day1, month1 = map(int, date1.split("/"))
  day2, month2 = map(int, date2.split("/"))
  if _from.month == month1:
    fdate1 = date(_from.year, month1, day1)
  else:
    fdate1 = date(_to.year, month1, day1)
  if _from.month == month2:
    fdate2 = date(_from.year, month2, day2)
  else:
    fdate2 = date(_to.year, month2, day2)
  if fdate1 > fdate2:
    fdate1, fdate2 = fdate2, fdate1
  return fdate1, fdate2


class PageInfo():
  def __init__(self, page_soup) -> None:
    self._raw = page_soup
    self._data_dict = self._parse_page(page_soup)
    self._type = self._data_dict["type"]

  @property
  def page_type(self):
    return self._page_type

  @property
  def data(self):
    return self._data_dict

  @property
  def raw(self):
    return self._raw

  @property
  def transactions(self):
    return self._data_dict.get("transactions", [])
      
  @classmethod
  def _parse_page(cls, page_soup):
    data = {}
    if len([div for div in page_soup.find_all("div") if div.text.startswith("Transactions -")]) > 0:
      data["type"] = PdfPageType.TRANSAC
      data.update(cls._parse_transactions(page_soup))
    else:
      data["type"] = PdfPageType.SUMMARY
      data.update(cls._parse_summary(page_soup))
    return data

  @classmethod
  def _transactions_date_range(cls, page_soup):
    filtered = [div for div in page_soup.find_all("div") if div.text.startswith("Transactions du")]
    if len(filtered) != 1:
      raise ValueError("transaction date range div cannot be found")
    matches = re.findall(r"([0-9]{2})/([0-9]{2})/([0-9]{4})", filtered[0].text)
    return (date(year=int(m[2]), month=int(m[1]), day=int(m[0])) for m in matches)

  @classmethod
  def _closing_debit_dates(cls, page_soup):
    divs = page_soup.find_all("div")
    closings = [d for d in divs if d.text.strip() == "Date de clôture"]
    debits = [d for d in divs if d.text.strip() == "Date de débit"]
    if len(closings) != 1 or len(debits) != 1:
      raise ValueError("no or several match(es) for closing and debit dates fields")
    closing_label = closings[0]
    closing_y, _ = extract_pos(closing_label)
    debit_label = debits[0]
    debit_y, _ = extract_pos(debit_label)
    date_pattern = re.compile("[0-9]{2}/[0-9]{2}/[0-9]{4}") 
    found_divs = [d for d in divs if date_pattern.match(d.text.strip()) is not None and extract_pos(d)[0] in {closing_y, debit_y}]
    if len(found_divs) != 2:
      raise ValueError("did not find date divs for debit and closing")
    if extract_pos(found_divs[0])[0] == debit_y:
      debit_date_div, closing_date_div = found_divs
    else:
      closing_date_div, debit_date_div = found_divs
    return {
      'closing_date': datetime.strptime(closing_date_div.text.strip(), '%d/%m/%Y').date(), 
      'debit_date': datetime.strptime(debit_date_div.text.strip(), '%d/%m/%Y').date()
    }

  @classmethod
  def _parse_summary(cls, page_soup):
    return {}

  @classmethod
  def _parse_transactions(cls, page_soup):
    divs = page_soup.find_all("div")

    """ 
    find rows ! 
    1) locate first row by locating first div with matching date string pattern
    2) associated index from there:
        - every matching string pattern div at the same x coordinate is a row (so we get the y for this row)
    """
    # skip to start of table
    index_first_row = 0
    small_date_pattern = re.compile(SMALL_DATE_PATTERN)
    while small_date_pattern.match(divs[index_first_row].text.strip()) is None:
      index_first_row += 1
    
    # extract coord 
    y_to_row_index, index_last_row = index_rows(divs, index_first_row)

    # extract data
    data = defaultdict(list)
    
    for div_index in range(index_first_row, len(divs)):
      div = divs[div_index]
      y, _ = extract_pos(div)
      actual_y = get_closest_y_from_index(y_to_row_index, y)
      if actual_y < 0:
        # skip div not in table
        continue 
      data[y_to_row_index[actual_y]].append(div.text.strip())

    debit_closing = cls._closing_debit_dates(page_soup)
    date_start, date_end = cls._transactions_date_range(page_soup)
    formatted_data = list()
    for t_data in data.values():
      # value_date earliest, accounted_date latest
      date1_idx, date2_idx = [i for i, s in enumerate(t_data) if small_date_pattern.match(s) is not None]
      early_date, late_date = process_dates(t_data[date1_idx], t_data[date2_idx], date_start, date_end)
      t_data_cpy = [t for i, t in enumerate(t_data) if i not in {date1_idx, date2_idx}]
      f_data = {
        'when': late_date,
        'value_date': early_date,
        'account': re.sub("([\r\n]+|\(Via.*\))", "", t_data_cpy[0]).strip(),
        'country_or_site': t_data_cpy[1],
        'country_code': t_data_cpy[2]
      }
      if len(t_data_cpy) > 4:  # has another currency
        f_data['original_amount'], f_data['original_currency'], f_data['rate_to_final'] = parse_conversion_data(t_data_cpy[3]) 
        amount_index = 4
      else:
        amount_index = 3

      amount, currency = parse_amount(t_data_cpy[amount_index])

      f_data.update({ 'amount': amount, 'currency': currency })
      f_data.update(debit_closing)
      formatted_data.append(f_data)

    return {'transactions': formatted_data}


def parse_mastercard_pdf(filename):
  pages = pdf2soups(filename)
  return [PageInfo(p) for p in pages]


def parse_folder(dirname):
  page_infos = list()
  for filename in os.listdir(dirname):
    page_infos.extend(parse_mastercard_pdf(os.path.join(dirname, filename)))
  
  # extract transactions and account names
  transactions = list()
  account_names = set()
  account2currency = dict()
  for page_info in page_infos:
    ts = page_info.transactions
    transactions.extend(ts)
    for t in ts:
      account2currency[t["account"]] = t.get("original_currency", t["currency"])
      account_names.add(t["account"])
    
  return page_infos, transactions, account_names, account2currency
