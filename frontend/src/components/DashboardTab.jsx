import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { balanceSeries, categorySummary, monthlySummary, topMerchants } from '../insights'
import { seriesPalette, STATUS, rupees } from '../format'
import { useTheme } from '../theme.jsx'

const CHROME = {
  light: { grid: '#e4e4ee', muted: '#8c8fa0', tooltipBg: '#ffffff', tooltipBorder: '#e4e4ee', pieStroke: '#ffffff' },
  dark: { grid: '#212636', muted: '#6b7386', tooltipBg: '#171c27', tooltipBorder: '#2a3142', pieStroke: '#121621' },
}

function money(v) {
  return rupees(v, { decimals: false })
}

export default function DashboardTab({ table }) {
  const { theme } = useTheme()
  const palette = seriesPalette(theme)
  const chrome = CHROME[theme] || CHROME.light
  const colorFor = (index) => palette[((index % palette.length) + palette.length) % palette.length]
  const axisStyle = { fontSize: 12, fill: chrome.muted }
  const tooltipStyle = {
    background: chrome.tooltipBg,
    border: `1px solid ${chrome.tooltipBorder}`,
    borderRadius: 10,
    fontSize: 13,
    boxShadow: '0 8px 24px rgba(0,0,0,0.12)',
  }

  const cats = categorySummary(table)
  const spend = cats.filter((c) => c.money_out > 0)
  const months = monthlySummary(table)
  const merchants = topMerchants(table, 10).slice().sort((a, b) => a.total_spent - b.total_spent)
  const bySource = balanceSeries(table)
  const sources = [...bySource.keys()]

  // merge per-source balance points onto a shared date axis for the line chart
  const allDates = [...new Set([...bySource.values()].flatMap((list) => list.map((p) => p.date)))].sort()
  const balanceRows = allDates.map((date) => {
    const row = { date }
    for (const source of sources) {
      const point = bySource.get(source).find((p) => p.date === date)
      if (point) row[source] = point.balance
    }
    return row
  })

  const merchantCategories = [...new Set(merchants.map((m) => m.category))]

  return (
    <div>
      <div className="chart-grid">
        <div className="chart-card">
          <h3>Where the money went</h3>
          <ResponsiveContainer width="100%" height={380}>
            <PieChart>
              <Pie
                data={spend}
                dataKey="money_out"
                nameKey="category"
                innerRadius={70}
                outerRadius={120}
                paddingAngle={1}
                isAnimationActive={false}
              >
                {spend.map((entry, i) => (
                  <Cell key={entry.category} fill={colorFor(i)} stroke={chrome.pieStroke} strokeWidth={2} />
                ))}
              </Pie>
              <Tooltip contentStyle={tooltipStyle} formatter={(v, n) => [money(v), n]} />
              <Legend
                wrapperStyle={{ fontSize: 12, color: 'var(--ink-secondary)' }}
                formatter={(value, entry) => `${value} (${entry.payload.share}%)`}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div className="chart-card">
          <h3>Money in vs out per month</h3>
          <ResponsiveContainer width="100%" height={380}>
            <BarChart data={months} margin={{ left: 8, right: 8 }}>
              <CartesianGrid stroke={chrome.grid} vertical={false} />
              <XAxis dataKey="month" tick={axisStyle} axisLine={{ stroke: chrome.grid }} tickLine={false} />
              <YAxis tick={axisStyle} axisLine={{ stroke: chrome.grid }} tickLine={false} tickFormatter={(v) => `${v / 1000}k`} />
              <Tooltip contentStyle={tooltipStyle} formatter={(v) => money(v)} />
              <Legend wrapperStyle={{ fontSize: 12, color: 'var(--ink-secondary)' }} />
              <Bar dataKey="money_in" name="Money in" fill={STATUS.good} radius={[4, 4, 0, 0]} />
              <Bar dataKey="money_out" name="Money out" fill={STATUS.critical} radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="chart-grid">
        <div className="chart-card">
          <h3>Balance over time</h3>
          <ResponsiveContainer width="100%" height={360}>
            <LineChart data={balanceRows} margin={{ left: 8, right: 8 }}>
              <CartesianGrid stroke={chrome.grid} vertical={false} />
              <XAxis dataKey="date" tick={axisStyle} axisLine={{ stroke: chrome.grid }} tickLine={false} />
              <YAxis tick={axisStyle} axisLine={{ stroke: chrome.grid }} tickLine={false} tickFormatter={(v) => `${v / 1000}k`} />
              <Tooltip contentStyle={tooltipStyle} formatter={(v) => money(v)} />
              {sources.length > 1 && <Legend wrapperStyle={{ fontSize: 12, color: 'var(--ink-secondary)' }} />}
              {sources.map((source, i) => (
                <Line
                  key={source}
                  type="stepAfter"
                  dataKey={source}
                  name={source}
                  stroke={colorFor(i)}
                  strokeWidth={2.5}
                  dot={false}
                  connectNulls
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="chart-card">
          <h3>Top 10 places you spent money</h3>
          <ResponsiveContainer width="100%" height={360}>
            <BarChart data={merchants} layout="vertical" margin={{ left: 24, right: 16 }}>
              <CartesianGrid stroke={chrome.grid} horizontal={false} />
              <XAxis type="number" tick={axisStyle} axisLine={{ stroke: chrome.grid }} tickLine={false} tickFormatter={(v) => `${v / 1000}k`} />
              <YAxis type="category" dataKey="counterparty" tick={axisStyle} axisLine={{ stroke: chrome.grid }} tickLine={false} width={110} />
              <Tooltip contentStyle={tooltipStyle} formatter={(v, n, p) => [money(v), p.payload.category]} />
              <Bar dataKey="total_spent" radius={[0, 4, 4, 0]}>
                {merchants.map((m) => (
                  <Cell key={m.counterparty} fill={colorFor(merchantCategories.indexOf(m.category))} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="table-wrap">
        <table className="data-table">
          <thead>
            <tr>
              <th>Category</th>
              <th>Transactions</th>
              <th>Money out</th>
              <th>Money in</th>
              <th>Share of spending</th>
            </tr>
          </thead>
          <tbody>
            {cats.map((c) => (
              <tr key={c.category}>
                <td>{c.category}</td>
                <td className="cell-num">{c.transactions}</td>
                <td className="cell-num">{money(c.money_out)}</td>
                <td className="cell-num">{money(c.money_in)}</td>
                <td className="cell-num">{c.share}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
