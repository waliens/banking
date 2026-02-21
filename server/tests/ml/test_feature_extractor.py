import pytest
from ml.feature_extractor import DescriptionEncoder, DescriptionPrePreprocessor, description_fn

def test_remove_patterns():

  preproc = DescriptionPrePreprocessor(
    remove_patterns=DescriptionEncoder.REMOVE_PATTERNS,
    desc_attr_fn=description_fn,
  )
  test_cases = [
    ("REF. : 123456789", ""),
    ("VAL. 12-34", ""),
    ("LE 12/34 12:34", ""),
    ("2021-12-31", ""),
    ("N. ABC123-456", ""),
    ("12/34/56 - 12h34", " - "),
    ("This is a test REF. : 123456789", "This is a test "),
    ("Transaction VAL. 12-34", "Transaction "),
    ("Meeting LE 12/34 12:34", "Meeting "),
    ("Date 2021-12-31", "Date "),
    ("Code N. ABC123-456", "Code "),
    ("Time 12/34/56 - 12h34", "Time  - "),
    ("Virement instantané en euros Instantané le 28/12 - 11:09:41 De:", "Virement instantané en euros Instantané le  -  De:"),
    ("Virement instantané en euros Instantané le 28/12/24 - 11:09:41 De:", "Virement instantané en euros Instantané le  -  De:"),
    ("Virement instantané en euros Instantané le 28/12/2024 - 11:09:41 De:", "Virement instantané en euros Instantané le  -  De:"),
    ("Virement instantané en euros Instantané le 28/12/2024 - 11:09 De:", "Virement instantané en euros Instantané le  -  De:"),
    ("4413 30XX XXXX 2201 3", ""),
    ("4413 30XX XXXX 2201", ""),
    ("**123/4564/74449**", ""),
    ("123/4546/44789", ""),
    ("Référence ING: COP12345678901", ""),
    ("BE12345678901234", ""),
    ("BE12 3456 7890 1234", ""),
    ("Carte: 303-0439398-27-0207", "")
  ]
  for description, expected in test_cases:
    transaction = type('Transaction', (object,), {'description': description})()
    assert preproc(transaction) == expected, f"failed for '{description}'"
