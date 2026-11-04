import { FileText, Inbox, BarChartIcon, Repeat, CheckCircle, Download, TrendingUp } from '../icons'

const TABS = [
  { id: 'overview', label: 'Overview', Icon: Inbox },
  { id: 'transactions', label: 'Transactions', Icon: FileText },
  { id: 'dashboard', label: 'Dashboard', Icon: BarChartIcon },
  { id: 'recurring', label: 'Recurring', Icon: Repeat },
  { id: 'quality', label: 'Data quality', Icon: CheckCircle },
  { id: 'insights', label: 'Model insights', Icon: TrendingUp },
  { id: 'export', label: 'Export', Icon: Download },
]

export default function Tabs({ active, onChange }) {
  return (
    <div className="tabs">
      {TABS.map(({ id, label, Icon }) => (
        <button
          key={id}
          type="button"
          className={`tab-btn${active === id ? ' active' : ''}`}
          onClick={() => onChange(id)}
        >
          <Icon width={15} height={15} strokeWidth={1.9} />
          {label}
        </button>
      ))}
    </div>
  )
}
