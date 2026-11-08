const API_ROOT = '/api'

async function request(path, options = {}) {
  const headers = new Headers(options.headers || {})
  const token = localStorage.getItem('resumeiq_access_token')
  if (token && !headers.has('Authorization')) headers.set('Authorization', `Bearer ${token}`)
  if (!(options.body instanceof FormData) && options.body && !headers.has('Content-Type')) headers.set('Content-Type', 'application/json')
  const response = await fetch(`${API_ROOT}${path}`, { ...options, headers })
  const contentType = response.headers.get('content-type') || ''
  const payload = contentType.includes('application/json') ? await response.json() : await response.text()
  if (!response.ok) {
    const detail = payload?.detail
    const message = typeof detail === 'string' ? detail : detail?.message || payload?.message || `Request failed (${response.status})`
    const error = new Error(message)
    error.status = response.status
    error.detail = detail
    throw error
  }
  return payload
}

const json = (method, body) => ({ method, body: JSON.stringify(body) })
export const api = {
  authStatus: () => request('/auth/status'),
  me: () => request('/auth/me'),
  login: async (email, password) => { const result = await request('/auth/login', json('POST', { email, password })); localStorage.setItem('resumeiq_access_token', result.access_token); return result },
  logout: () => localStorage.removeItem('resumeiq_access_token'),
  health: () => request('/health'),
  dashboard: () => request('/dashboard'),
  candidates: (params = {}) => request(`/candidates?${new URLSearchParams(params)}`),
  candidate: (id) => request(`/candidates/${id}`),
  upload: (file) => { const body = new FormData(); body.append('file', file); return request('/candidates/upload', { method: 'POST', body }) },
  downloadDocument: async (id, filename = 'resume') => {
    const headers = new Headers()
    const token = localStorage.getItem('resumeiq_access_token')
    if (token) headers.set('Authorization', `Bearer ${token}`)
    const response = await fetch(`${API_ROOT}/documents/${id}/download`, { headers })
    if (!response.ok) {
      const payload = await response.json().catch(() => ({}))
      throw new Error(payload.detail || `Download failed (${response.status})`)
    }
    const blob = await response.blob()
    const url = URL.createObjectURL(blob)
    const anchor = document.createElement('a')
    anchor.href = url
    anchor.download = filename
    document.body.appendChild(anchor)
    anchor.click()
    anchor.remove()
    window.setTimeout(() => URL.revokeObjectURL(url), 1000)
  },
  updateCandidate: (id, data) => request(`/candidates/${id}`, json('PATCH', data)),
  deleteCandidate: (id) => request(`/candidates/${id}`, { method: 'DELETE' }),
  jobs: (params = {}) => request(`/jobs?${new URLSearchParams(params)}`),
  createJob: (data) => request('/jobs', json('POST', data)),
  updateJob: (id, data) => request(`/jobs/${id}`, json('PATCH', data)),
  deleteJob: (id) => request(`/jobs/${id}`, { method: 'DELETE' }),
  applications: (params = {}) => request(`/applications?${new URLSearchParams(params)}`),
  createApplication: (data) => request('/applications', json('POST', data)),
  updateApplication: (id, data) => request(`/applications/${id}`, json('PATCH', data)),
  deleteApplication: (id) => request(`/applications/${id}`, { method: 'DELETE' }),
  runMatching: (jobId) => request(`/matches/jobs/${jobId}/run`, { method: 'POST' }),
  matches: (jobId) => request(`/matches/jobs/${jobId}`),
  interviews: (params = {}) => request(`/interviews?${new URLSearchParams(params)}`),
  createInterview: (data) => request('/interviews', json('POST', data)),
  updateInterview: (id, data) => request(`/interviews/${id}`, json('PATCH', data)),
  activity: () => request('/activity')
}
