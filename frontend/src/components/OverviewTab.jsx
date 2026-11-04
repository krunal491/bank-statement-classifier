import { rupees } from '../format'
import { FileText, ArrowDownRight, ArrowUpRight, CheckCircle, AlertTriangle, Landmark } from '../icons'

function StatTile({ icon, label, value, color }) {
  return (
    <div className="stat-tile">
      <div className="icon-chip" style={{ background: `color-mix(in srgb, ${color} 14%, transparent)`, color }}>
        {icon}
      </div>
      <div className="value">{value}</div>
      <div className="label">{label}</div>
    </div>
  )
}

export default function OverviewTab({ output }) {
  const { results, table, report, duplicatesRemoved } = output
  const needsReview = table.filter((r) => r.needs_review).length
  const iconProps = { width: 16, height: 16, strokeWidth: 2 }

  return (
    <div>
      <div className="stat-grid">
        <StatTile icon={<FileText {...iconProps} />} label="Transactions" value={report.transaction_count} color="var(--brand)" />
        <StatTile
          icon={<ArrowDownRight {...iconProps} />}
          label="Money in"
          value={rupees(report.total_credit, { decimals: false })}
          color="var(--good)"
        />
        <StatTile
          icon={<ArrowUpRight {...iconProps} />}
          label="Money out"
          value={rupees(report.total_debit, { decimals: false })}
          color="var(--critical)"
        />
        <StatTile
          icon={<CheckCircle {...iconProps} />}
          label="Balance check"
          value={`${report.balance_check_pass_rate ?? 0}%`}
          color="var(--good)"
        />
        <StatTile icon={<AlertTriangle {...iconProps} />} label="Need review" value={needsReview} color="var(--warning)" />
      </div>

      {duplicatesRemoved > 0 && (
        <div className="landing-info">
          Removed {duplicatesRemoved} duplicate transactions from your statement.
        </div>
      )}

      {results.map(({ account, report: rep }) => {
        const pageTypes = account.page_types || []
        const textPages = pageTypes.filter((p) => p === 'text').length
        const imagePages = pageTypes.filter((p) => p === 'image').length
        const grew = (rep.closing_balance ?? 0) >= (rep.opening_balance ?? 0)
        return (
          <div className="acct-card" key={account.file_name}>
            <div className="acct-head">
              <span className="acct-title">
                <Landmark width={18} height={18} strokeWidth={1.9} />
                {account.bank_name || 'Unknown bank'} — {account.file_name}
              </span>
              <span className={`acct-badge${grew ? '' : ' down'}`}>
                {grew ? <ArrowUpRight width={14} height={14} strokeWidth={2.2} /> : <ArrowDownRight width={14} height={14} strokeWidth={2.2} />}
                {rupees(rep.opening_balance)} → {rupees(rep.closing_balance)}
              </span>
            </div>
            <div className="acct-grid">
              <div>
                <div className="f-label">Account holder</div>
                <div className="f-value">{account.account_holder || '-'}</div>
              </div>
              <div>
                <div className="f-label">Account number</div>
                <div className="f-value">{account.account_number || '-'}</div>
              </div>
              <div>
                <div className="f-label">IFSC</div>
                <div className="f-value">{account.ifsc || '-'}</div>
              </div>
              <div>
                <div className="f-label">Branch</div>
                <div className="f-value">{account.branch || '-'}</div>
              </div>
              <div>
                <div className="f-label">Period</div>
                <div className="f-value">
                  {account.period_from || '?'} → {account.period_to || '?'}
                </div>
              </div>
              <div>
                <div className="f-label">Customer ID</div>
                <div className="f-value">{account.customer_id || '-'}</div>
              </div>
              <div>
                <div className="f-label">PDF type</div>
                <div className="f-value">{account.pdf_type}</div>
              </div>
              <div>
                <div className="f-label">Pages</div>
                <div className="f-value">
                  {pageTypes.length} ({textPages} text, {imagePages} scanned)
                </div>
              </div>
            </div>
          </div>
        )
      })}
    </div>
  )
}
