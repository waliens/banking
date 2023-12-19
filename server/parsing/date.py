from dateutil import parser

def parse_date(input_string):
  try:
    # Attempt to parse as datetime
    dt = parser.parse(input_string)
    return dt.date()  # Extract date component
  except ValueError:
    try:
      # Attempt to parse as date
      date = parser.parse(input_string, ignoretz=True)
      return date.date()
    except ValueError:
      print("Unable to extract date from the provided string.")
      return None