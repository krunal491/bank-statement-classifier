import { useState } from 'react'
import { downloadCsv, downloadExcel } from '../api'
import { Download } from '../icons'

export default function ExportTab({ table, results, report }) {
  const [busy, setBusy] = useState('')

  const account =
    results.length === 1 ? results[0].account : { ...results[0].account, file_name: 'multiple files' }

  async function handle(kind, fn) {
    setBusy(kind)
    try {
      await fn()
    } catch (e) {
      alert(e.message)
    } finally {
      setBusy('')
    }
  }

  return (
    <div>
      <div className="download-row">
        <button
          className="btn btn-primary"
          style={{ width: 'auto' }}
          disabled={busy !== ''}
          onClick={() => handle('xlsx', () => downloadExcel({ table, account, report }))}
        >
          <Download width={16} height={16} strokeWidth={2} />
          {busy === 'xlsx' ? 'Preparing…' : 'Download Excel (.xlsx)'}
        </button>
        <button
          className="btn btn-secondary"
          disabled={busy !== ''}
          onClick={() => handle('csv', () => downloadCsv({ table }))}
        >
          <Download width={16} height={16} strokeWidth={2} />
          {busy === 'csv' ? 'Preparing…' : 'Download CSV (.csv)'}
        </button>
      </div>
      <p className="caption">
        The Excel file has 7 sheets: Transactions, Account Summary, Category Summary, Monthly Summary, Recurring
        Payments, Top Merchants and Data Quality. Yellow rows need a category review; red rows failed the balance
        check.
      </p>
    </div>
  )
}
