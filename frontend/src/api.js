// In dev, Vite proxies /api to the local backend (see vite.config.js). In production the
// frontend (Vercel) and backend (Render) are separate origins, so VITE_API_BASE_URL points
// straight at the deployed API - set it in the Vercel project's environment variables.
const BASE = `${(import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '')}/api`

async function unwrap(res) {
  if (!res.ok) {
    let message = `Request failed (${res.status})`
    try {
      const body = await res.json()
      message = typeof body.detail === 'string' ? body.detail : message
    } catch {
      // response wasn't JSON (e.g. a file download error) - keep the generic message
    }
    const error = new Error(message)
    error.status = res.status
    throw error
  }
  return res
}

export async function processStatements({ files, password }) {
  if (files.length !== 1) throw new Error('Choose one PDF statement to process.')
  const form = new FormData()
  for (const f of files) form.append('files', f, f.name)
  form.append('password', password || '')
  const res = await unwrap(await fetch(`${BASE}/process`, { method: 'POST', body: form }))
  return res.json()
}

export async function saveCorrections({ table, corrections }) {
  const res = await unwrap(
    await fetch(`${BASE}/corrections`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ table, corrections }),
    }),
  )
  return res.json()
}

export async function fetchModelInsights(signal) {
  const res = await unwrap(await fetch(`${BASE}/model/insights`, { signal }))
  return res.json()
}

async function downloadFile(path, body, filename) {
  const res = await unwrap(
    await fetch(`${BASE}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    }),
  )
  const blob = await res.blob()
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(url)
}

export function downloadExcel({ table, account, report }) {
  return downloadFile('/export/excel', { table, account, report }, 'classified_transactions.xlsx')
}

export function downloadCsv({ table }) {
  return downloadFile('/export/csv', { table }, 'classified_transactions.csv')
}
