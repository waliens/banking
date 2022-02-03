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