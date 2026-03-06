/**
 * Format a Date object (or date-like value) as YYYY-MM-DD string.
 * Returns null if the input is falsy.
 */
export function formatDate(d) {
  if (!d) return null
  const dt = new Date(d)
  return `${dt.getFullYear()}-${String(dt.getMonth() + 1).padStart(2, '0')}-${String(dt.getDate()).padStart(2, '0')}`
}

/**
 * Format a datetime string as a locale-formatted date-time string.
 * Returns '—' if the input is falsy.
 */
export function formatDateTime(dt) {
  if (!dt) return '—'
  return new Date(dt).toLocaleString()
}

/**
 * Compute a { date_from, date_to } range based on period type and parameters.
 *
 * @param {Object} opts
 * @param {'year'|'month'|'range'} opts.periodType
 * @param {number} opts.year
 * @param {number} [opts.month] - 1-based month number
 * @param {Date|string|null} [opts.dateFrom] - custom range start
 * @param {Date|string|null} [opts.dateTo] - custom range end
 * @returns {{ date_from: string|null, date_to: string|null }}
 */
export function getDateRange({ periodType, year, month, dateFrom, dateTo }) {
  if (periodType === 'year') {
    return {
      date_from: `${year}-01-01`,
      date_to: `${year}-12-31`,
    }
  }
  if (periodType === 'month') {
    const lastDay = new Date(year, month, 0).getDate()
    return {
      date_from: `${year}-${String(month).padStart(2, '0')}-01`,
      date_to: `${year}-${String(month).padStart(2, '0')}-${String(lastDay).padStart(2, '0')}`,
    }
  }
  // range
  return {
    date_from: formatDate(dateFrom),
    date_to: formatDate(dateTo),
  }
}
