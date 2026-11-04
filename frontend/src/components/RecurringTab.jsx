import { recurringSummary } from '../insights'
import { rupees } from '../format'
import { Repeat } from '../icons'

export default function RecurringTab({ table }) {
  const rows = recurringSummary(table)
  const monthlyOut = rows.filter((r) => r.type === 'Money out').reduce((s, r) => s + r.typical_amount, 0)

  return (
    <div>
      <p className="caption">
        Payments that repeat with a similar amount in at least two different months (salary, rent, EMIs, SIPs,
        subscriptions).
      </p>
      {rows.length === 0 ? (
        <div className="landing-info">
          <Repeat width={17} height={17} strokeWidth={1.9} />
          No recurring payments found. Use a statement covering at least two months to help identify recurring payments.
        </div>
      ) : (
        <>
          <div className="metric-inline">
            <span className="value">{rupees(monthlyOut)}</span>
            <span className="label">Fixed monthly commitments</span>
          </div>
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Counterparty</th>
                  <th>Category</th>
                  <th>Type</th>
                  <th>Typical amount</th>
                  <th>Months seen</th>
                  <th>Frequency</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((r) => (
                  <tr key={`${r.counterparty}-${r.category}-${r.type}`}>
                    <td>{r.counterparty}</td>
                    <td>{r.category}</td>
                    <td>{r.type}</td>
                    <td className="cell-num">{rupees(r.typical_amount)}</td>
                    <td className="cell-num">{r.months_seen}</td>
                    <td>{r.frequency}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  )
}
