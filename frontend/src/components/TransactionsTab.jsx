import { useMemo, useState } from 'react'
import { rupees } from '../format'
import { Search, Save, CheckCircle, X } from '../icons'

export default function TransactionsTab({ table, categories, onSave, saving }) {
  const [search, setSearch] = useState('')
  const [category, setCategory] = useState('All')
  const [kind, setKind] = useState('All')
  const [reviewOnly, setReviewOnly] = useState(false)
  const [edits, setEdits] = useState({}) // { [row.id]: newCategory }

  const filtered = useMemo(() => {
    let rows = table
    if (search.trim()) {
      const q = search.trim().toLowerCase()
      rows = rows.filter((r) => (r.description || '').toLowerCase().includes(q))
    }
    if (category !== 'All') rows = rows.filter((r) => (edits[r.id] ?? r.category) === category)
    if (kind === 'Money out') rows = rows.filter((r) => r.debit !== null)
    else if (kind === 'Money in') rows = rows.filter((r) => r.credit !== null)
    if (reviewOnly) rows = rows.filter((r) => r.needs_review)
    return rows
  }, [table, search, category, kind, reviewOnly, edits])

  // Rows whose dropdown now differs from the category the row actually has. Counting raw
  // `edits` entries instead would let the button read "(1)" and sit enabled after picking a
  // row's *existing* category - clicking it would then save nothing and never clear.
  const changedRows = useMemo(
    () => table.filter((r) => edits[r.id] !== undefined && edits[r.id] !== r.category),
    [table, edits],
  )

  function handleSave() {
    const rows = changedRows.map((r) => ({
      description: r.description,
      direction: r.direction,
      category: edits[r.id],
    }))
    onSave(rows, () => setEdits({}))
  }

  return (
    <div>
      <div className="filter-bar">
        <div className="field">
          <label htmlFor="txn-search">Search</label>
          <div className="search-input">
            <Search width={15} height={15} strokeWidth={2} />
            <input id="txn-search" type="text" value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search description" />
          </div>
        </div>
        <div className="field">
          <label htmlFor="txn-category">Category</label>
          <select id="txn-category" value={category} onChange={(e) => setCategory(e.target.value)}>
            <option>All</option>
            {categories.map((c) => (
              <option key={c}>{c}</option>
            ))}
          </select>
        </div>
        <div className="field">
          <label htmlFor="txn-type">Type</label>
          <select id="txn-type" value={kind} onChange={(e) => setKind(e.target.value)}>
            <option>All</option>
            <option>Money out</option>
            <option>Money in</option>
          </select>
        </div>
        <label className="checkbox-field">
          <input type="checkbox" checked={reviewOnly} onChange={(e) => setReviewOnly(e.target.checked)} />
          Only rows to review
        </label>
      </div>

      <p className="caption">
        Change the <strong>Category</strong> column, then press <em>Save corrections</em> so the model learns.
      </p>

      <div className="table-wrap">
        <table className="data-table">
          <thead>
            <tr>
              <th>Date</th>
              <th className="wrap">Description</th>
              <th>Counterparty</th>
              <th>Mode</th>
              <th>Debit</th>
              <th>Credit</th>
              <th>Balance</th>
              <th>Category</th>
              <th>Confidence</th>
              <th>Method</th>
              <th>Review?</th>
              <th>Recurring</th>
              <th>Balance OK</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((r) => (
              <tr key={r.id} className={r.needs_review ? 'needs-review' : ''}>
                <td>{r.date}</td>
                <td className="wrap">{r.description}</td>
                <td>{r.counterparty || '-'}</td>
                <td>{r.mode || '-'}</td>
                <td className={`cell-num${r.debit !== null ? ' cell-critical' : ''}`}>{r.debit !== null ? rupees(r.debit) : '-'}</td>
                <td className={`cell-num${r.credit !== null ? ' cell-good' : ''}`}>{r.credit !== null ? rupees(r.credit) : '-'}</td>
                <td className="cell-num">{r.balance !== null ? rupees(r.balance) : '-'}</td>
                <td>
                  <select
                    className="category-select"
                    value={edits[r.id] ?? r.category}
                    onChange={(e) => setEdits((prev) => ({ ...prev, [r.id]: e.target.value }))}
                  >
                    {categories.map((c) => (
                      <option key={c}>{c}</option>
                    ))}
                  </select>
                </td>
                <td>
                  <span className="confidence-bar">
                    <span style={{ width: `${Math.round((r.confidence ?? 0) * 100)}%` }} />
                  </span>
                  {(r.confidence ?? 0).toFixed(2)}
                </td>
                <td>{r.method}</td>
                <td>{r.needs_review ? <CheckCircle width={15} height={15} strokeWidth={2} style={{ color: 'var(--warning)' }} /> : <X width={13} height={13} strokeWidth={2} style={{ color: 'var(--ink-muted)', opacity: 0.5 }} />}</td>
                <td>{r.is_recurring ? <CheckCircle width={15} height={15} strokeWidth={2} style={{ color: 'var(--brand)' }} /> : <X width={13} height={13} strokeWidth={2} style={{ color: 'var(--ink-muted)', opacity: 0.5 }} />}</td>
                <td>
                  <span className={`badge-dot ${r.balance_ok ? 'ok' : 'fail'}`} />
                  {r.balance_ok ? 'OK' : 'Fail'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <button className="btn btn-primary" style={{ width: 'auto', marginTop: '0.8rem' }} onClick={handleSave} disabled={changedRows.length === 0 || saving}>
        <Save width={15} height={15} strokeWidth={2} />
        {saving ? 'Saving…' : `Save corrections (${changedRows.length})`}
      </button>
    </div>
  )
}
