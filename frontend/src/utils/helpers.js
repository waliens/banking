import currency from 'currency.js';

export function hasOwnProperty(obj, prop) {
  var proto = obj.__proto__ || obj.constructor.prototype;
  return (prop in obj) &&
      (!(prop in proto) || proto[prop] !== obj[prop]);
}

export function regexpEscape(string) {
  return string.replace(/[-/\\^$*+?.()|[\]{}]/g, '\\$&');
}

export function strcurrency(s) {
  return currency(Number(s), { 
    precision: 2 
  });
}

export function monthMap(ctx) {
  return {
    0: ctx.$t("january"),
    1: ctx.$t("february"),
    2: ctx.$t("march"),
    3: ctx.$t("april"),
    4: ctx.$t("may"),
    5: ctx.$t("june"),
    6: ctx.$t("july"),
    7: ctx.$t("august"),
    8: ctx.$t("september"),
    9: ctx.$t("october"),
    10: ctx.$t("november"),
    11: ctx.$t("december")
  };
}

export function formatAccountNumber(number) {
  if (number == null) {
    return null;
  }

  // Remove any non-numeric characters
  let noSpace = number.replace(/\s/g, '');

  // Check if it is an IBAN
  let isIBAN = /^([A-Z]{2}\d{2})(.{1,30})$/.test(noSpace);

  // Format based on IBAN or legacy Belgian account number
  if (isIBAN) {
    return noSpace.replace(/(.{1,4})/g, '$1 ').trim();
  } else if (noSpace.length == 12) {
    // Format legacy Belgian account number
    return noSpace.replace(/(.{3})(.{7})(.{2})/, '$1-$2-$3');
  } else { // fallback to simply display the registered account number
    return number;
  }
} 