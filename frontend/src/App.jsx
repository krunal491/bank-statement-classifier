import { useState } from 'react'
import Sidebar from './components/Sidebar'
import Header from './components/Header'
import Tabs from './components/Tabs'
import OverviewTab from './components/OverviewTab'
import TransactionsTab from './components/TransactionsTab'
import DashboardTab from './components/DashboardTab'
import RecurringTab from './components/RecurringTab'
import DataQualityTab from './components/DataQualityTab'
import ModelInsightsTab from './components/ModelInsightsTab'
import ExportTab from './components/ExportTab'
import { processStatements, saveCorrections } from './api'
import { AlertTriangle, Inbox } from './icons'

export default function App() {
  const [uploads, setUploads] = useState([])
  const [password, setPassword] = useState('')

  const [processing, setProcessing] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [output, setOutput] = useState(null) // { results, table, report, duplicatesRemoved, categories }
  const [resultVersion, setResultVersion] = useState(0)
  const [activeTab, setActiveTab] = useState('overview')

  async function handleProcess() {
    if (processing || saving) return
    setError('')
    if (uploads.length !== 1) {
      setError('Choose one PDF statement to process.')
      return
    }
    setProcessing(true)
    try {
      const result = await processStatements({ files: uploads, password })
      setOutput(result)
      setResultVersion((version) => version + 1)
    } catch (e) {
      setError(e.message)
    } finally {
      setProcessing(false)
    }
  }

  async function handleSaveCorrections(rows, onDone) {
    if (rows.length === 0) return
    setSaving(true)
    try {
      const result = await saveCorrections({ table: output.table, corrections: rows })
      setOutput((prev) => ({ ...prev, table: result.table }))
      onDone?.()
    } catch (e) {
      setError(e.message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="app-shell">
      <Sidebar
        uploads={uploads}
        setUploads={setUploads}
        password={password}
        setPassword={setPassword}
        onProcess={handleProcess}
        processing={processing}
        busy={processing || saving}
      />

      <main className="main" aria-busy={processing}>
        <Header />

        {error && (
          <div className="alert alert-error" style={{ marginBottom: '1rem' }}>
            <AlertTriangle width={16} height={16} strokeWidth={2} />
            {error}
          </div>
        )}

        {!output && (
          <>
            <div className="landing-info">
              <Inbox width={17} height={17} strokeWidth={1.9} />
              Upload a bank statement PDF, then press <strong>&nbsp;Process</strong>.
            </div>
            <details className="expander" open>
              <summary>How does it work?</summary>
              <div className="expander-body">
                <ol>
                  <li><strong>Upload your statement.</strong> Choose a PDF and enter its password if it is locked.</li>
                  <li><strong>Review your transactions.</strong> Check spending categories, balances and any items flagged for review.</li>
                  <li><strong>Explore your spending.</strong> See category totals and recurring payments.</li>
                  <li><strong>Download your report.</strong> Export your results to Excel or CSV.</li>
                </ol>
              </div>
            </details>
          </>
        )}

        {output && (
          <>
            <Tabs active={activeTab} onChange={setActiveTab} />
            {activeTab === 'overview' && <OverviewTab output={output} />}
            {activeTab === 'transactions' && (
              <TransactionsTab
                key={resultVersion}
                table={output.table}
                categories={output.categories}
                onSave={handleSaveCorrections}
                saving={saving || processing}
              />
            )}
            {activeTab === 'dashboard' && <DashboardTab table={output.table} />}
            {activeTab === 'recurring' && <RecurringTab table={output.table} />}
            {activeTab === 'quality' && <DataQualityTab results={output.results} />}
            {activeTab === 'insights' && <ModelInsightsTab />}
            {activeTab === 'export' && (
              <ExportTab table={output.table} results={output.results} report={output.report} />
            )}
          </>
        )}
      </main>
    </div>
  )
}
