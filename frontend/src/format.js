// Indian number grouping: ₹1,23,456.78
export function rupees(value, { decimals = true } = {}) {
  if (value === null || value === undefined || Number.isNaN(value)) return '-'
  const sign = value < 0 ? '-' : ''
  const abs = Math.abs(value)
  const [wholeRaw, frac] = abs.toFixed(2).split('.')
  let whole = wholeRaw
  if (whole.length > 3) {
    const head = whole.slice(0, -3)
    const tail = whole.slice(-3)
    const groups = []
    let i = head.length
    while (i > 0) {
      groups.unshift(head.slice(Math.max(i - 2, 0), i))
      i -= 2
    }
    whole = `${groups.join(',')},${tail}`
  }
  return `₹${sign}${whole}${decimals ? `.${frac}` : ''}`
}

// Fixed-order, colorblind-safe categorical palette. Light and dark are each their own
// validated set (not one palette dimmed/brightened for the other mode) - see index.css's
// --series-* tokens for where these values come from.
const PALETTE_LIGHT = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#e87ba4', '#008300', '#4a3aa7', '#e34948']
const PALETTE_DARK = ['#3987e5', '#d95926', '#199e70', '#c98500', '#d55181', '#1fae1f', '#9085e9', '#e66767']

export function seriesPalette(theme) {
  return theme === 'dark' ? PALETTE_DARK : PALETTE_LIGHT
}

// Status colors are mode-invariant by design (chosen to clear contrast on both surfaces).
export const STATUS = {
  good: '#0ca30c',
  critical: '#d03b3b',
}
