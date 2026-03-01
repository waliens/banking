import { hasMatchingAliases } from "./AccountAliasTableData";
import { regexpEscape } from "../../utils/helpers";


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
      'field': 'contribution_ratio',
      'label': ctx.$t('account_group.contribution_ratio'),
      'numeric': true,
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

export function queryFilter(query, data, checkAliases=false) {
  let q = new RegExp('.*' + regexpEscape(query) + '.*', "gi");
  return data.filter(accountGroup => {
    return (accountGroup.account.number && accountGroup.account.number.match(q)) || (accountGroup.account.name && accountGroup.account.name.match(q)) 
            || (checkAliases && accountGroup.account.aliases instanceof Array && accountGroup.account.aliases.length > 0 && hasMatchingAliases(q, accountGroup.account.aliases));
  });
}
