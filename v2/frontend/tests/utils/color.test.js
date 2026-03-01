import { describe, it, expect } from 'vitest'
import { contrastText } from '../../src/utils/color'

describe('contrastText', () => {
  it('returns undefined for null/undefined input', () => {
    expect(contrastText(null)).toBeUndefined()
    expect(contrastText(undefined)).toBeUndefined()
  })

  it('returns dark color as-is (already readable)', () => {
    // Dark blue — luminance well below 0.4
    expect(contrastText('#1e3a8a')).toBe('#1e3a8a')
    // Dark red
    expect(contrastText('#991b1b')).toBe('#991b1b')
  })

  it('darkens bright colors for readability', () => {
    // Yellow (#fbbf24) is very bright — should be darkened
    const result = contrastText('#fbbf24')
    expect(result).not.toBe('#fbbf24')
    expect(result).toMatch(/^rgb\(/)
  })

  it('darkens lime/light green', () => {
    const result = contrastText('#84cc16')
    expect(result).not.toBe('#84cc16')
    expect(result).toMatch(/^rgb\(/)
  })

  it('keeps medium colors like standard blue', () => {
    // #3B82F6 (Tailwind blue-500) — luminance ~0.21
    expect(contrastText('#3B82F6')).toBe('#3B82F6')
  })

  it('handles 3-char hex', () => {
    // #fff is very bright
    const result = contrastText('#fff')
    expect(result).toMatch(/^rgb\(/)
  })

  it('returns pure black (#000000) as-is', () => {
    // Black has luminance 0 — well below the 0.4 threshold
    expect(contrastText('#000000')).toBe('#000000')
  })

  it('darkens pure white (#ffffff)', () => {
    // White has luminance 1.0 — well above the 0.4 threshold
    const result = contrastText('#ffffff')
    expect(result).not.toBe('#ffffff')
    expect(result).toMatch(/^rgb\(/)
  })

  it('keeps orange (#f97316) as-is (luminance below threshold)', () => {
    // Orange #f97316: R=249 G=115 B=22
    // Luminance ~0.29, which is below 0.4 threshold
    expect(contrastText('#f97316')).toBe('#f97316')
  })

  it('returns undefined for empty string', () => {
    expect(contrastText('')).toBeUndefined()
  })
})
