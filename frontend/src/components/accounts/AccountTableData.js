

export function getColumns(ctx) {
  return [
    {
      'field': 'number',
      'label': ctx.$t('account.number'),
      'sortable': true  
    },
    {
      'field': 'name',
      'label': ctx.$t('account.name'),
      'sortable': true
    },
    {
      'field': 'balance',
      'label': ctx.$t('account.balance'),
      'numeric': true
    }
  ]
}

export function queryFilter(query, data) {
  return data.filter(account => {
    let q = '/.*' + query + ' .*/g';
    return !!((account.number && account.number.match(q)
                || account.name && account.name.match(q)))
  });
}
