import { useRef, useState } from 'react'
import { Upload, Lock, Eye, EyeOff, Zap, Sun, Moon } from '../icons'
import { Logomark } from '../icons'
import { useTheme } from '../theme.jsx'

export default function Sidebar({ uploads, setUploads, password, setPassword, onProcess, processing, busy }) {
  const [fileError, setFileError] = useState('')
  const [dragging, setDragging] = useState(false)
  const [showPassword, setShowPassword] = useState(false)
  const fileInput = useRef(null)
  const { theme, toggle } = useTheme()

  function addFiles(fileList) {
    if (busy) return
    const files = Array.from(fileList)
    if (!files.length) return
    if (files.length !== 1) {
      setFileError('Choose one PDF at a time.')
      return
    }
    const file = files[0]
    if (file.type !== 'application/pdf' && !file.name.toLowerCase().endsWith('.pdf')) {
      setFileError('Choose a PDF bank statement.')
      return
    }
    if (file.size > 20 * 1024 * 1024) {
      setFileError('Choose a PDF smaller than 20 MB.')
      return
    }
    setFileError('')
    setUploads([file])
    setPassword('')
  }

  function removeUpload(index) {
    setFileError('')
    setUploads((prev) => prev.filter((_, i) => i !== index))
  }

  return (
    <aside className="sidebar">
      <div className="brand">
        <Logomark className="mark" size={24} />
        <div>
          <div className="word">Ledger</div>
          <div className="sub">Statement classifier</div>
        </div>
      </div>

      <div className="field">
        <label>
          <Upload width={14} height={14} strokeWidth={2} /> Bank statement PDF
        </label>
        <div
          className={`dropzone${dragging ? ' dragging' : ''}`}
          role="button"
          tabIndex={busy ? -1 : 0}
          aria-label="Choose a bank statement PDF"
          aria-disabled={busy}
          onKeyDown={(e) => {
            if (!busy && (e.key === 'Enter' || e.key === ' ')) {
              e.preventDefault()
              fileInput.current?.click()
            }
          }}
          onClick={() => !busy && fileInput.current?.click()}
          onDragOver={(e) => {
            e.preventDefault()
            setDragging(true)
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={(e) => {
            e.preventDefault()
            setDragging(false)
            addFiles(e.dataTransfer.files)
          }}
        >
          <Upload width={20} height={20} />
          Drop one PDF here, or click to browse
          <input
            ref={fileInput}
            type="file"
            accept="application/pdf"
            disabled={busy}
            onChange={(e) => {
              addFiles(e.target.files)
              e.target.value = ''
            }}
          />
        </div>
        <p className="upload-hint">One PDF, up to 20 MB. Choosing a new file replaces the selection.</p>
        {fileError && <div className="alert alert-error" role="alert">{fileError}</div>}
        <div className="file-chip-list">
            {uploads.map((f, i) => (
              <span className="chip" key={`${f.name}-${i}`}>
                <span className="file-name" title={f.name}>{f.name}</span>
                <button type="button" disabled={busy} onClick={() => removeUpload(i)} aria-label={`Remove ${f.name}`}>
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
                    <path d="m6 6 12 12M18 6 6 18" />
                  </svg>
                </button>
              </span>
            ))}
        </div>
      </div>

      <div className="field">
        <label htmlFor="pdf-password">
          <Lock width={14} height={14} strokeWidth={2} /> PDF password
        </label>
        <div className="password-field">
          <input
            id="pdf-password"
            disabled={busy}
            type={showPassword ? 'text' : 'password'}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Leave blank if not locked"
          />
          <button
            type="button"
            className="password-toggle"
            onClick={() => setShowPassword((v) => !v)}
            aria-label={showPassword ? 'Hide password' : 'Show password'}
          >
            {showPassword ? <EyeOff width={16} height={16} /> : <Eye width={16} height={16} />}
          </button>
        </div>
      </div>

      <button className="btn btn-primary" onClick={onProcess} disabled={busy || uploads.length === 0}>
        {processing ? (
          <>
            <span className="spinner" style={{ borderTopColor: 'var(--brand-ink)', borderColor: 'rgba(255,255,255,0.35)' }} />
            Processing…
          </>
        ) : (
          <>
            <Zap width={16} height={16} strokeWidth={2} /> Process
          </>
        )}
      </button>

      <div className="process-status" role="status" aria-live="polite">
        {processing ? 'Reading your statement… Scanned pages may take longer.' : (uploads.length ? 'Ready to process' : 'Choose a statement to begin')}
      </div>

      <p className="sidebar-note">
        <Lock width={13} height={13} strokeWidth={2} />
        Your PDF is processed for this report and is not kept after the request.
      </p>

      <div className="sidebar-footer">
        <button className="theme-toggle" onClick={toggle} aria-label="Toggle theme">
          {theme === 'dark' ? <Sun width={14} height={14} /> : <Moon width={14} height={14} />}
          {theme === 'dark' ? 'Light' : 'Dark'}
        </button>
      </div>
    </aside>
  )
}
