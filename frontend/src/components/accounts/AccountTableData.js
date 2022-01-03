

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
    },
    {
      'field': "explore",
      'label': ctx.$t('explore'),
      'centered': true
    }
  ]
}

export function queryFilter(query, data) {
  let q = new RegExp('.*' + query + '.*', "gi");
  return data.filter(account => {
    return (account.number && account.number.match(q)) || (account.name && account.name.match(q));
  });
}
