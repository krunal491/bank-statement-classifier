// Client-side equivalents of src/insights.py, computed from the table already in memory
// so switching chart views doesn't need a round trip to the backend.

export function categorySummary(table) {
  const byCategory = new Map()
  for (const r of table) {
    const key = r.category || 'Others'
    const entry = byCategory.get(key) || { category: key, transactions: 0, money_out: 0, money_in: 0 }
    entry.transactions += 1
    entry.money_out += r.debit || 0
    entry.money_in += r.credit || 0
    byCategory.set(key, entry)
  }
  const rows = [...byCategory.values()].sort((a, b) => b.money_out - a.money_out)
  const totalOut = rows.reduce((s, r) => s + r.money_out, 0) || 1
  return rows.map((r) => ({ ...r, share: Math.round((1000 * r.money_out) / totalOut) / 10 }))
}

export function monthlySummary(table) {
  const byMonth = new Map()
  for (const r of table) {
    if (!r.date) continue
    const month = r.date.slice(0, 7) // 'YYYY-MM'
    const entry = byMonth.get(month) || { month, money_in: 0, money_out: 0 }
    entry.money_in += r.credit || 0
    entry.money_out += r.debit || 0
    byMonth.set(month, entry)
  }
  return [...byMonth.values()].sort((a, b) => a.month.localeCompare(b.month))
}

export function topMerchants(table, limit = 10) {
  const byMerchant = new Map()
  for (const r of table) {
    if (r.debit === null || r.debit === undefined || !r.counterparty) continue
    const entry = byMerchant.get(r.counterparty) || {
      counterparty: r.counterparty,
      times: 0,
      total_spent: 0,
      category: r.category,
    }
    entry.times += 1
    entry.total_spent += r.debit
    byMerchant.set(r.counterparty, entry)
  }
  return [...byMerchant.values()].sort((a, b) => b.total_spent - a.total_spent).slice(0, limit)
}

function median(values) {
  const sorted = [...values].sort((a, b) => a - b)
  const mid = Math.floor(sorted.length / 2)
  return sorted.length % 2 ? sorted[mid] : (sorted[mid - 1] + sorted[mid]) / 2
}

// Rows are already flagged is_recurring server-side (src/insights.py's find_recurring);
// this just summarizes those rows per counterparty+category+type for display.
export function recurringSummary(table) {
  const groups = new Map()
  for (const r of table) {
    if (!r.is_recurring) continue
    const who = r.counterparty || (r.description || '').slice(0, 25)
    const type = r.debit !== null && r.debit !== undefined ? 'Money out' : 'Money in'
    const amount = r.debit ?? r.credit ?? 0
    const key = `${who}|${r.category}|${type}`
    const entry = groups.get(key) || { who, category: r.category, type, amounts: [], months: new Set() }
    entry.amounts.push(amount)
    if (r.date) entry.months.add(r.date.slice(0, 7))
    groups.set(key, entry)
  }
  const rows = [...groups.values()].map((g) => ({
    counterparty: g.who,
    category: g.category,
    type: g.type,
    typical_amount: Math.round(median(g.amounts) * 100) / 100,
    months_seen: g.months.size,
    frequency: g.months.size >= g.amounts.length * 0.8 ? 'Monthly' : 'Several times a month',
  }))
  return rows.sort((a, b) => b.typical_amount - a.typical_amount)
}

export function balanceSeries(table) {
  const bySource = new Map()
  for (const r of table) {
    if (r.balance === null || r.balance === undefined || !r.date) continue
    const list = bySource.get(r.source_file) || []
    list.push({ date: r.date, balance: r.balance })
    bySource.set(r.source_file, list)
  }
  for (const list of bySource.values()) list.sort((a, b) => a.date.localeCompare(b.date))
  return bySource
}
