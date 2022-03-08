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