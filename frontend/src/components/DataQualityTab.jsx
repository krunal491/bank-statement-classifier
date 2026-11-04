import { useState } from 'react'
import { CheckCircle, AlertTriangle } from '../icons'

function ResultExpander({ result }) {
  const [open, setOpen] = useState(result.report.problems.length > 0)
  const rate = result.report.balance_check_pass_rate
  const problems = result.report.problems
  const hasProblems = problems.length > 0

  return (
    <details className={`expander ${hasProblems ? 'warn' : 'good'}`} open={open} onToggle={(e) => setOpen(e.target.open)}>
      <summary>
        {hasProblems ? <AlertTriangle width={16} height={16} strokeWidth={2} /> : <CheckCircle width={16} height={16} strokeWidth={2} />}
        {result.account.file_name} — balance check {rate}% — {problems.length} note(s)
      </summary>
      <div className="expander-body">
        {problems.length ? (
          <ul>
            {problems.map((p, i) => (
              <li key={i}>{p}</li>
            ))}
          </ul>
        ) : (
          'No problems found.'
        )}
      </div>
    </details>
  )
}

export default function DataQualityTab({ results }) {
  return (
    <div>
      <p className="caption">
        Every row is checked with <strong>previous balance − debit + credit = balance</strong>. A failed check
        usually means a misread number (common in scans) or a missing row.
      </p>
      {results.map((r) => (
        <ResultExpander key={r.account.file_name} result={r} />
      ))}
    </div>
  )
}
