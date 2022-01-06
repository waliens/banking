import levenshtein from "js-levenshtein";

export let LEVENSHTEIN = 'levenshtein';

export function getStrategies() {
  return [
    LEVENSHTEIN,
  ];
}

export function matchScore(strategy, reference, other, keyFn) {
  let strRef = keyFn(reference), strOther = keyFn(other);
  if (strategy == LEVENSHTEIN) {
    return levenshtein(strRef, strOther);
  } else {
    throw new Error("unknown string match scoring strategy '" + strategy + "'");
  }
}

export function matchAndSortArray(strategy, reference, array, keyFn) {
  let withScore = array.map(obj => { return {obj, score: matchScore(strategy, reference, obj, keyFn) }; });
  withScore.sort((a, b) => a.score - b.score);
  return withScore;
}