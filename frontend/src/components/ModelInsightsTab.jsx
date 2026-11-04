import { useEffect, useState } from 'react'
import { fetchModelInsights } from '../api'

function pct(v) {
  return `${(v * 100).toFixed(1)}%`
}

export default function ModelInsightsTab() {
  const [data, setData] = useState(null)
  const [error, setError] = useState('')
  const [attempt, setAttempt] = useState(0)

  useEffect(() => {
    const controller = new AbortController()
    let active = true
    let timedOut = false
    const timer = setTimeout(() => {
      timedOut = true
      controller.abort()
    }, 20000)
    fetchModelInsights(controller.signal)
      .then((result) => { if (active) setData(result) })
      .catch(() => {
        if (active) setError(timedOut
          ? 'Model insights are taking longer than expected. Please try again.'
          : 'Model insights are temporarily unavailable. Please try again.')
      })
      .finally(() => clearTimeout(timer))
    return () => { active = false; clearTimeout(timer); controller.abort() }
  }, [attempt])

  if (error) return (
    <div>
      <div className="alert alert-error" role="alert">{error}</div>
      <button className="btn btn-secondary" style={{ marginTop: '1rem' }} onClick={() => { setError(''); setAttempt((value) => value + 1) }}>Try again</button>
    </div>
  )
  if (!data) return <div className="spinner-row" role="status"><span className="spinner" />Loading model insights…</div>

  const { baseline, correctionsCount } = data
  const categories = Object.keys(baseline.per_category).sort()

  return (
    <div>
      <p className="caption">
        These baseline scores use synthetic test transactions kept separate from training.
        They indicate benchmark performance, not guaranteed accuracy on your statement.
        You can improve categorization by reviewing flagged transactions and saving corrections.
        There {correctionsCount === 1 ? 'is' : 'are'} <strong>{correctionsCount}</strong> saved correction{correctionsCount === 1 ? '' : 's'}.
      </p>

      <div className="compare-grid">
        <div className="compare-tile">
          <div className="tag">Baseline accuracy</div>
          <div className="big">{pct(baseline.accuracy)}</div>
          <div className="delta">Scored on {baseline.test_rows} test transactions</div>
        </div>
      </div>

      <div className="table-wrap">
        <table className="data-table">
          <thead>
            <tr>
              <th>Category</th>
              <th>Precision</th>
              <th>Recall</th>
              <th>F1</th>
              <th>Test rows</th>
            </tr>
          </thead>
          <tbody>
            {categories.map((cat) => {
              const m = baseline.per_category[cat]
              return (
                <tr key={cat}>
                  <td>{cat}</td>
                  <td className="cell-num">{pct(m.precision)}</td>
                  <td className="cell-num">{pct(m.recall)}</td>
                  <td className="cell-num">{pct(m.f1)}</td>
                  <td className="cell-num">{m.support}</td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
