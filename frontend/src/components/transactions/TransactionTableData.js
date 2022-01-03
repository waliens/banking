

export function queryFilter(query, data) {
  let q = new RegExp('.*' + query + '.*', "gi");
  return data.filter(transaction => {
    return (transaction.source.name && transaction.source.name.match(q)) || (transaction.source.number && transaction.source.number.match(q)) 
            || (transaction.dest.name && transaction.dest.name.match(q)) || (transaction.dest.number && transaction.dest.number.match(q))
            || (Object.entries(transaction.metadata_).filter((k, v) => (!!v) && (v instanceof String) && v.match(q)).length > 0)
            || (transaction.when && transaction.when.match(q)) || (transaction.amount && transaction.amount.match(q));
  });
}
