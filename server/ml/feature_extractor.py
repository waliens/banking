import re
import nltk
import numpy as np
from nltk.corpus import stopwords
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.base import TransformerMixin
from sklearn.preprocessing import OneHotEncoder, LabelEncoder

from impl.belfius import parse_date
from db.models import Category
from db.util import tag_tree_from_database


# description -> tfidf
# src account -> one hot
# dst account -> one hot
# amount
# date -> year, month, day, day of the week
# hour minute (if exists)
def transaction_fn(x):
  return x.metadata_['transaction']

def when_fn(x):
  return x.when

def valued_at_fn(x):
  return parse_date(x.metadata_['valued_at'])

def amount_fn(x):
  return float(x.amount)

class DateTransformer(TransformerMixin):
  def __init__(self, date_attr_fn=None):
    """Converts an object with a date attribute named as `date_attr` into a vector of integer containing date info: (year, month, day, week day)
    """
    TransformerMixin.__init__(self)
    self._date_attr_fn = date_attr_fn

  def _date_features(self, date):
    return [date.year, date.month, date.day, date.weekday()]

  def fit(self, X, y=None):
    return self 

  def transform(self, X, y=None):
    return [self._date_features(self._date_attr_fn(x)) for x in X]


class AccountsOneHot(TransformerMixin):
  def __init__(self):
    """One hot encodes source and dest accounts from transactions"""
    self._encoder = OneHotEncoder(handle_unknown="ignore")  # validate 'ignore'

  def _accounts(self, X):
    return np.array([[
      x.id_source if x.id_source is not None else -1,
      x.id_dest if x.id_dest is not None else -1
    ] for x in X])

  def fit(self, X, y=None):
    self._encoder.fit(self._accounts(X))
    return self

  def transform(self, X, y=None):
    return self._encoder.transform(self._accounts(X)).toarray()


class DescriptionPrePreprocessor(TransformerMixin):
  def __init__(self, remove_patterns, desc_attr_fn):
    self._remove_patterns = [re.compile(p, re.IGNORECASE | re.UNICODE) for p in remove_patterns]
    self._desc_attr_fn = desc_attr_fn
  
  def fit(self, X, y=None):
    return self 

  def transform(self, X, y=None):
    return [self(x) for x in X]

  def __call__(self, transaction):
    val = str(self._desc_attr_fn(transaction))
    for pattern in self._remove_patterns:
      val = re.sub(pattern, "", val)
    return val


class DescriptionEncoder(TransformerMixin):
  def __init__(self, desc_attr_fn, remove_patterns):
    nltk.download('stopwords')
    self._preprocessor = DescriptionPrePreprocessor(remove_patterns, desc_attr_fn)
    self._tfidf = TfidfVectorizer(
      decode_error="replace", 
      strip_accents="unicode", 
      stop_words=stopwords.words('english') + stopwords.words('french'), 
      max_df=0.9, 
      min_df=2
    )
    self._pipeline = Pipeline([('desc-preprocess', self._preprocessor), ('tfidf', self._tfidf)])

  @classmethod
  def belfius(cls):
    return cls(
      desc_attr_fn=transaction_fn, 
      remove_patterns=[
        r"REF\. : [0-9A-Z]{9,13}",
        r"VAL\. [0-9]{0,2}-[0-9]{0,2}",
        r"LE [0-9]{0,2}/[0-9]{0,2} [0-9]{0,2}:[0-9]{0,2}",
        r"[0-9]{2,4}[/-][0-9]{2}[/-][0-9]{2,4}",
        r"\b(?:N. )?(?:[A-Z]+)?[0-9-]+\b"
      ]
    )

  def fit(self, X, y=None):
    self._pipeline.fit(X)
    return self

  def transform(self, X, y=None):
    return self._pipeline.transform(X)

class BelfiusHourMinuteTransformer(TransformerMixin):
  def fit(self, X, y=None):
    return self
  
  def _extract_time(self, transaction):
    desc = transaction.metadata_["transaction"]
    match = re.match(r".*LE [0-9]{2}/[0-9]{2} ([0-9]{2}):([0-9]{2}).*", desc)
    if match is None:
      return [-1, -1]
    return [int(match.group(1)), int(match.group(2))]

  def transform(self, X, y=None):
    return [self._extract_time(t) for t in X]


class SingleFeatureTransformer(TransformerMixin):
  def __init__(self, val_fn):
    self._val_fn = val_fn
  
  def fit(self, X, y=None):
    return self

  def transform(self, X, y=None):
    return [[self._val_fn(x)] for x in X]


class CategoryEncoder(TransformerMixin):
  def __init__(self, level='fine', id_categ_fn=None):
    if level not in {'fine', 'coarse'}:
      raise ValueError("unknown category encoder level '{}'".format(level))
    if id_categ_fn is None:
      id_categ_fn = lambda v: v
    self._id_categ_fn = id_categ_fn
    self._level = level
    self._categories = tag_tree_from_database()
    self._tag_index = self._get_at_level()
    self._tag_inv_index = self._make_inv_index(self._tag_index)
    # sort for preserving order accross calls
    self._label_encoder = LabelEncoder()
    self._label_encoder.fit(list(self._tag_index.keys()))

  def _make_inv_index(self, index):
    inverted_index = dict()
    for sel, mapped in index.items():
      for label in mapped:
        inverted_index[label] = sel
    return inverted_index 

  def _get_at_level(self):
    result_dict = dict()
    for root in self._categories.roots:
      result_dict.update(self._get_at_level_recur(root, 0))
    return result_dict

  def _get_at_level_recur(self, tag, depth=0):
    if not self._categories.has_children(tag.id):
      return {tag.id: {tag.id}}
    if (depth == 1 and self._level == 'coarse') or (depth == 2 and self._level == 'fine'):
      return {tag.id: set([tag.id] + self._categories.get_children(tag.id))}
    result_dict = dict()
    for child_id in self._categories.get_children(tag.id):
      child_tag = self._categories[child_id]
      result_dict.update(self._get_at_level_recur(child_tag, depth + 1))
    return result_dict
  
  def _cvt_to_selected(self, X):
    return [self._tag_inv_index[self._id_categ_fn(x)] for x in X]

  def fit(self, X, y=None):
    return self

  def transform(self, X, y=None):
    return self._label_encoder.transform(self._cvt_to_selected(X))

  def inverse_transform(self, X):
    return self._label_encoder.inverse_transform(X)


def belfius_transformer():
  feature_union = FeatureUnion([
    ('desc-tf-idf', DescriptionEncoder.belfius()),
    ('when-to-scalars', DateTransformer(when_fn)),
    ('value-at-to-scalars', DateTransformer(valued_at_fn)),
    ('accounts-one-hot', AccountsOneHot()),
    ('hour-minute-extractor', BelfiusHourMinuteTransformer()),
    ('amount-extractor', SingleFeatureTransformer(val_fn=amount_fn))
  ])
  return feature_union

  
