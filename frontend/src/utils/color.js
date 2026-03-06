/**
 * Parse a hex color string (#RGB or #RRGGBB) into [r, g, b].
 */
function hexToRgb(hex) {
  let h = hex.replace('#', '')
  if (h.length === 3) h = h[0] + h[0] + h[1] + h[1] + h[2] + h[2]
  return [parseInt(h.slice(0, 2), 16), parseInt(h.slice(2, 4), 16), parseInt(h.slice(4, 6), 16)]
}

/**
 * Relative luminance per WCAG 2.0.
 */
function luminance(r, g, b) {
  const [rs, gs, bs] = [r, g, b].map((c) => {
    c = c / 255
    return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4)
  })
  return 0.2126 * rs + 0.7152 * gs + 0.0722 * bs
}

/**
 * Return a text color (dark or the original color) that ensures readable
 * contrast on a light-tinted background of `hex`.
 *
 * For light category colors (e.g. yellow, lime) the raw hex is unreadable
 * on a white-ish background, so we darken it. For already-dark colors
 * we return them as-is.
 *
 * @param {string} hex  The category color, e.g. "#f59e0b"
 * @returns {string}    A CSS color string safe for text on a light bg
 */
export function contrastText(hex) {
  if (!hex) return undefined
  const [r, g, b] = hexToRgb(hex)
  const lum = luminance(r, g, b)
  // If the color is bright (luminance > 0.4), darken it for readability
  if (lum > 0.4) {
    const factor = 0.45
    return `rgb(${Math.round(r * factor)}, ${Math.round(g * factor)}, ${Math.round(b * factor)})`
  }
  return hex
}
