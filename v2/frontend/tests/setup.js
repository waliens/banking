/**
 * Vitest global setup — runs before every test file.
 *
 * - Stubs localStorage (happy-dom provides one, but we ensure it's clean)
 * - Resets any module-level state between tests
 */
import { vi } from 'vitest'

// Ensure localStorage is clean before each test
beforeEach(() => {
  localStorage.clear()
})

// Stub window.location.href setter (used by api.js on refresh failure)
// happy-dom doesn't handle navigation, so we prevent errors
delete window.location
window.location = { href: '', reload: vi.fn() }
