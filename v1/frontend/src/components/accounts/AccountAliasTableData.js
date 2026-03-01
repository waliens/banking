export function getColumns(ctx) {
  return [
    {
      'label': ctx.$t("account.name"),
      'field': 'name',
      'sortable': true
    },
    {
      'label': ctx.$t("account.number"),
      'field': 'number',
      'sortable': true
    },
  ]
}

export function matchAlias(regex, alias) {
  return (alias.number && alias.number.match(regex)) || (alias.name && alias.name.match(regex))
}

export function hasMatchingAliases(regex, aliases) {
  return aliases.filter(alias => {
    return matchAlias(regex, alias);
  }).length > 0;
}

export function queryFilter(query, data) {
  let q = new RegExp('.*' + query + '.*', "gi");
  return data.filter(alias => {
    return matchAlias(q, alias);
  });
}
