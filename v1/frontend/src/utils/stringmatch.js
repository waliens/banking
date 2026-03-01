import levenshtein from "js-levenshtein";
import longestCommonSubseq from 'longest-common-substring';

export let LEVENSHTEIN = 'levenshtein';
export let LONGEST_COMMON_SUBSTRING = 'longest-common-substring';

export function getStrategies() {
  return [
    { name: LEVENSHTEIN, maxScore: 99 },
    { name: LONGEST_COMMON_SUBSTRING, maxScore: -3 }
  ];
}

/** Returns a score measuring the strings similarities between keyFn(reference) and keyFn(other), the lower the close. */
export function matchScore(strategy, reference, other, keyFn) {
  let strRef = keyFn(reference), strOther = keyFn(other);
  if (strategy == LEVENSHTEIN) {
    return levenshtein(strRef, strOther);
  } else if (strategy == LONGEST_COMMON_SUBSTRING) {
    return -longestCommonSubseq([...(strRef.toLowerCase())], [...(strOther.toLowerCase())]).length;
  } else {
    throw new Error("unknown string match scoring strategy '" + strategy + "'");
  }
}

export function matchAndSortArray(strategy, reference, array, keyFn) {
  let withScore = array.map(obj => { return {obj, score: matchScore(strategy, reference, obj, keyFn) }; });
  let maxScore = getStrategies().filter(s => s.name == strategy)[0].maxScore;
  withScore = withScore.filter(scoreObj => scoreObj.score < maxScore);
  withScore.sort((a, b) => a.score - b.score);
  return withScore;
}