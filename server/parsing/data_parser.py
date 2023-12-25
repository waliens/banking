from abc import abstractmethod, ABC

from .account import AccountGroup
from .transaction import Transaction


def check_add_to_env_group(env_group: AccountGroup, t: Transaction, excluded_identifiers: set):
  """Check whether the current transaction should be added to the environment by checking excluded account numbers.
  If source or dest is not in excluded numbers than env_group is update to contain the account(s) and the transaction.

  Params
  ------
  env_group: AccountGroup
  t: Transaction
  excluded_identifiers: set

  Returns
  -------
  added: bool
    True if the transaction was added to the env group
  """
  if t.source.identifier not in excluded_identifiers and t.source.identifier not in env_group:
    env_group.add_account(t.source)
  if t.dest.identifier not in excluded_identifiers and t.dest.identifier not in env_group:
    env_group.add_account(t.dest)
  return env_group.submit_transaction(t)


class ParserOrchestrator(ABC):
  @abstractmethod
  def read(self, path, add_env_group=False):
    """
    Params:
    -------
    path: str
      Path of a root folder containing all data needed to set up transactions, accounts and groups
    add_env_group: bool
      True to include an environment account group

    Returns:
    --------
    groups: A list of account groups
      The parsed transaction
    """
    pass

