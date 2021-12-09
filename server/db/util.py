



from db.models import Account
from parsing.util import UnionFind


def load_account_uf_from_database():
    accounts = Account.query.all()
    uf = UnionFind()

    for account in accounts:
      key = (account.number, account.name)
      uf.add_repres(key)
      for equiv in account.equivalences:
        eq_key = (equiv.number, equiv.name)
        uf.add_elem(eq_key, key)
    
    return accounts, uf