import { FileText, Landmark, Repeat, BarChartIcon } from '../icons'

export default function Header() {
  return (
    <div className="app-header">
      <div className="app-header-row">
        <div>
          <h1>Understand your bank statement</h1>
          <p>
            Turn your bank statement into organized transactions, spending insights and a downloadable report.
          </p>
        </div>
      </div>
      <div className="pill-row">
        <span className="pill">
          <FileText width={14} height={14} strokeWidth={2} /> Text + scanned PDFs
        </span>
        <span className="pill">
          <Landmark width={14} height={14} strokeWidth={2} /> SBI · HDFC · ICICI · Axis · Kotak
        </span>
        <span className="pill">
          <Repeat width={14} height={14} strokeWidth={2} /> Learns from your corrections
        </span>
        <span className="pill">
          <BarChartIcon width={14} height={14} strokeWidth={2} /> Spend dashboard
        </span>
      </div>
    </div>
  )
}
