import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import {
  Activity, ArrowDownRight, ArrowRight, ArrowUpRight, Award, BriefcaseBusiness, CalendarClock,
  Check, CheckCheck, ChevronDown, ChevronLeft, ChevronRight, CircleHelp, Clock3, Code2,
  Command, FileCheck2, FileSearch, FileText, Filter, Gauge, Github, GraduationCap, LayoutDashboard,
  ListFilter, LogOut, Mail, Menu, MessageSquareText, MoreHorizontal, Plus, RefreshCw, Search,
  Settings2, ShieldCheck, Sparkles, Target, UploadCloud, Users, X, Zap, Building2, MapPin,
  Pencil, Trash2, Download, ExternalLink, Linkedin, Globe2, Layers3, CircleAlert, CalendarDays,
  Briefcase, SlidersHorizontal, ChevronUp, BrainCircuit, CheckCircle2
} from 'lucide-react'
import { api } from './api'
import { PublicPortal, CandidatePortal, InterviewerPortal } from './Portals.jsx'

const NAV = [
  { id: 'overview', label: 'Overview', icon: LayoutDashboard, group: 'Workspace' },
  { id: 'candidates', label: 'Candidates', icon: Users, group: 'Workspace' },
  { id: 'jobs', label: 'Roles', icon: BriefcaseBusiness, group: 'Workspace' },
  { id: 'applications', label: 'Applications', icon: Layers3, group: 'Workflow' },
  { id: 'interviews', label: 'Interviews', icon: CalendarClock, group: 'Workflow' },
  { id: 'matching', label: 'Intelligence', icon: BrainCircuit, group: 'Intelligence' },
  { id: 'analytics', label: 'Analytics', icon: Activity, group: 'Intelligence' },
  { id: 'settings', label: 'Workspace settings', icon: Settings2, group: 'Manage' }
]
const STAGES = [
  { id: 'new', label: 'New', color: 'steel' },
  { id: 'screening', label: 'Screening', color: 'violet' },
  { id: 'interview', label: 'Interview', color: 'blue' },
  { id: 'offer', label: 'Offer', color: 'amber' },
  { id: 'hired', label: 'Hired', color: 'green' },
  { id: 'rejected', label: 'Closed', color: 'red' }
]
const fmtDate = (value, options = { day: '2-digit', month: 'short', year: 'numeric' }) => value ? new Date(value).toLocaleDateString(undefined, options) : '—'
const fmtTime = value => value ? new Date(value).toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' }) : '—'
const initials = name => (name || 'N A').split(/\s+/).slice(0, 2).map(x => x[0]).join('').toUpperCase()
const commaList = value => value.split(',').map(x => x.trim()).filter(Boolean)

function App() {
  const [page, setPage] = useState('overview')
  const [dashboard, setDashboard] = useState(null)
  const [candidates, setCandidates] = useState([])
  const [jobs, setJobs] = useState([])
  const [applications, setApplications] = useState([])
  const [interviews, setInterviews] = useState([])
  const [activity, setActivity] = useState([])
  const [health, setHealth] = useState(null)
  const [loading, setLoading] = useState(true)
  const [auth, setAuth] = useState({ checking: true, enabled: false, required: false, user: null })
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState('')
  const [toast, setToast] = useState(null)
  const [modal, setModal] = useState(null)
  const [selectedCandidate, setSelectedCandidate] = useState(null)
  const [selectedApplication, setSelectedApplication] = useState(null)
  const [date, setDate] = useState(() => new Date())
  const [uploadProgress, setUploadProgress] = useState(null)
  const fileInput = useRef(null)

  const notify = useCallback((message, tone = 'success') => {
    setToast({ message, tone })
    window.setTimeout(() => setToast(null), 3800)
  }, [])

  const refresh = useCallback(async (quiet = false) => {
    if (!quiet) setRefreshing(true)
    try {
      const [dash, people, roles, apps, events, activityLog, status] = await Promise.all([
        api.dashboard(), api.candidates(), api.jobs(), api.applications(), api.interviews(), api.activity(), api.health()
      ])
      setDashboard(dash)
      setCandidates(people)
      setJobs(roles)
      setApplications(apps)
      setInterviews(events)
      setActivity(activityLog)
      setHealth(status)
      setError('')
    } catch (err) {
      setError(err.message || 'Could not connect to the ResumeIQ API.')
      setHealth(null)
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }, [])

  useEffect(() => {
    let cancelled = false
    const initialize = async () => {
      try {
        const status = await api.authStatus()
        if (status.enabled) {
          try {
            const session = await api.me()
            if (cancelled) return
            setAuth({ checking: false, enabled: true, required: false, user: session.user })
            if (!['admin', 'recruiter', 'reviewer', 'viewer'].includes(session.user?.role)) {
              setLoading(false)
              return
            }
          } catch {
            api.logout()
            if (cancelled) return
            setAuth({ checking: false, enabled: true, required: false, user: null })
            setLoading(false)
            return
          }
        } else if (!cancelled) {
          setAuth({ checking: false, enabled: false, required: false, user: null })
        }
        if (!cancelled) await refresh()
      } catch {
        if (!cancelled) {
          setAuth({ checking: false, enabled: false, required: false, user: null })
          await refresh()
        }
      }
    }
    initialize()
    const interval = window.setInterval(() => {
      if (document.visibilityState === 'visible' && (!auth.enabled || ['admin', 'recruiter', 'reviewer', 'viewer'].includes(auth.user?.role))) {
        setDate(new Date())
        refresh(true)
      }
    }, 30000)
    const onFocus = () => { setDate(new Date()); if (!auth.enabled || ['admin', 'recruiter', 'reviewer', 'viewer'].includes(auth.user?.role)) refresh(true) }
    window.addEventListener('focus', onFocus)
    return () => { cancelled = true; window.clearInterval(interval); window.removeEventListener('focus', onFocus) }
  }, [refresh, auth.required, auth.enabled, auth.user?.role])

  const act = async (fn, successMessage) => {
    try {
      const result = await fn()
      await refresh(true)
      if (successMessage) notify(successMessage)
      return result
    } catch (err) {
      notify(err.message || 'Something went wrong.', 'error')
      throw err
    }
  }

  const onPickFile = () => fileInput.current?.click()
  const onUpload = async event => {
    const files = Array.from(event.target.files || [])
    event.target.value = ''
    if (!files.length) return
    const accepted = files.filter(file => /\.(pdf|docx)$/i.test(file.name))
    const rejected = files.filter(file => !/\.(pdf|docx)$/i.test(file.name)).map(file => `${file.name}: unsupported format`)
    if (!accepted.length) return notify('Choose PDF or DOCX resumes.', 'error')
    const uploaded = []
    const duplicates = []
    const failures = [...rejected]
    setUploadProgress({ completed: 0, total: accepted.length, current: accepted[0]?.name || '' })
    for (let index = 0; index < accepted.length; index += 1) {
      const file = accepted[index]
      setUploadProgress({ completed: index, total: accepted.length, current: file.name })
      try {
        const result = await api.upload(file)
        uploaded.push(result)
      } catch (err) {
        const detail = err.detail
        if (err.status === 409) {
          const existing = detail?.candidate_name ? ` (${detail.candidate_name})` : ''
          duplicates.push(`${file.name}${existing}`)
        } else failures.push(`${file.name}: ${err.message}`)
      }
      setUploadProgress({ completed: index + 1, total: accepted.length, current: accepted[index + 1]?.name || file.name })
    }
    await refresh(true)
    if (uploaded.length) {
      try { setSelectedCandidate(await api.candidate(uploaded[0].candidate.id)) }
      catch { setSelectedCandidate({ candidate: uploaded[0].candidate, documents: [uploaded[0].document], field_evidence: uploaded[0].parsed_profile.field_evidence, sections_detected: uploaded[0].parsed_profile.sections_detected }) }
    }
    setUploadProgress(null)
    const summary = `${uploaded.length} uploaded · ${duplicates.length} duplicates · ${failures.length} failed`
    const detail = [...duplicates.map(name => `Duplicate: ${name}`), ...failures].slice(0, 4).join(' · ')
    if (uploaded.length && !duplicates.length && !failures.length) notify(`${uploaded.length} resume${uploaded.length === 1 ? '' : 's'} parsed successfully. ${summary}`)
    else if (uploaded.length) notify(`${summary}${detail ? `. ${detail}` : ''}`, 'warning')
    else if (duplicates.length) notify(`${summary}. Existing candidate records were left unchanged.`, 'warning')
    else notify(`${summary}. ${detail}`, 'error')
  }

  const handleLogin = async (email, password) => {
    const result = await api.login(email, password)
    setAuth({ checking: false, enabled: true, required: false, user: result.user })
    if (['admin', 'recruiter', 'reviewer', 'viewer'].includes(result.user.role)) {
      setLoading(true)
      await refresh()
    } else {
      setLoading(false)
    }
    return result
  }
  const handleRegister = async (displayName, email, password) => {
    const result = await api.registerCandidate(displayName, email, password)
    setAuth({ checking: false, enabled: true, required: false, user: result.user })
    setLoading(false)
    return result
  }
  const handleLogout = () => {
    api.logout()
    setAuth({ checking: false, enabled: true, required: false, user: null })
    setLoading(false)
  }

  if (auth.checking) return <LoginLoading />
  const role = auth.user?.role || 'admin'
  if (auth.enabled && !auth.user) return <PublicPortal onLogin={handleLogin} onRegister={handleRegister} />
  if (auth.enabled && role === 'candidate') return <CandidatePortal user={auth.user} onLogout={handleLogout} />
  if (auth.enabled && role === 'interviewer') return <InterviewerPortal user={auth.user} onLogout={handleLogout} />
  if (auth.required) return <LoginScreen onLogin={handleLogin} />

  const pageTitle = NAV.find(item => item.id === page)?.label || 'Overview'
  const canManageRoles = !auth.enabled || ['admin', 'recruiter'].includes(role)
  const canReviewWorkflow = !auth.enabled || ['admin', 'recruiter', 'reviewer'].includes(role)
  const canManageUsers = auth.enabled && role === 'admin'
  const showSettings = !auth.enabled || canManageUsers

  return <div className="app-shell">
    <input ref={fileInput} type="file" multiple accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document" hidden onChange={onUpload} />
    <Sidebar page={page} setPage={setPage} counts={{ candidates: dashboard?.total_candidates || 0, jobs: dashboard?.open_jobs || 0 }} onUpload={onPickFile} user={auth.user} canUpload={canManageRoles} showSettings={showSettings} />
    <main className="main-shell">
      <Topbar pageTitle={pageTitle} date={date} health={health} refreshing={refreshing} onRefresh={() => refresh()} onHelp={() => setModal({ type: 'help' })} user={auth.user} onLogout={handleLogout} />
      {error && <div className="connection-banner"><CircleAlert size={16}/><span>{error}</span><button onClick={() => refresh()}>Retry connection</button></div>}
      {uploadProgress && <div className="upload-progress-banner"><div className="upload-progress-copy"><strong>Indexing resumes</strong><span>{uploadProgress.completed} of {uploadProgress.total} · {uploadProgress.current}</span></div><div className="upload-progress-track"><i style={{ width: `${uploadProgress.completed / uploadProgress.total * 100}%` }}/></div></div>}
      {loading ? <LoadingState /> : <div className="page-content">
        {page === 'overview' && <OverviewPage dashboard={dashboard} jobs={jobs} applications={applications} onNavigate={setPage} onUpload={onPickFile} onCreateJob={() => setModal({ type: 'job' })} onOpenCandidate={async id => { const data = await api.candidate(id); setSelectedCandidate(data) }} canManage={canManageRoles} canReview={canReviewWorkflow} />}
        {page === 'candidates' && <CandidatesPage candidates={candidates} jobs={jobs} onUpload={onPickFile} onOpen={async id => { const data = await api.candidate(id); setSelectedCandidate(data) }} onDelete={id => act(() => api.deleteCandidate(id), 'Candidate deleted.')} onCreateApplication={data => setModal({ type: 'application', candidateId: data.id })} canManage={canManageRoles} canReview={canReviewWorkflow} />}
        {page === 'jobs' && <JobsPage jobs={jobs} applications={applications} onCreate={() => setModal({ type: 'job' })} onUpdate={(id, data) => act(() => api.updateJob(id, data), 'Role updated.')} onDelete={id => act(() => api.deleteJob(id), 'Role deleted.')} onNavigate={setPage} canManage={canManageRoles} />}
        {page === 'applications' && <ApplicationsPage applications={applications} onUpdate={(id, data) => act(() => api.updateApplication(id, data), 'Application updated.')} onOpen={item => setSelectedApplication(item)} onCreate={() => setModal({ type: 'application' })} canEdit={canReviewWorkflow} />}
        {page === 'interviews' && <InterviewsPage interviews={interviews} applications={applications} onCreate={() => setModal({ type: 'interview' })} onUpdate={(id, data) => act(() => api.updateInterview(id, data), 'Interview updated.')} canEdit={canReviewWorkflow} />}
        {page === 'matching' && <MatchingPage jobs={jobs} applications={applications} onCreateApplication={data => act(() => api.createApplication(data), 'Candidate added to the pipeline.')} canEdit={canReviewWorkflow} />}
        {page === 'analytics' && <AnalyticsPage dashboard={dashboard} applications={applications} jobs={jobs} interviews={interviews} />}
        {page === 'settings' && showSettings && <SettingsPage health={health} onRefresh={() => refresh()} user={auth.user} />}
      </div>}
    </main>
    <AnimateToast toast={toast} />
    {selectedCandidate && <CandidateDrawer data={selectedCandidate} onClose={() => setSelectedCandidate(null)} onSave={async (id, data) => { await act(() => api.updateCandidate(id, data), 'Candidate profile saved.'); const fresh = await api.candidate(id); setSelectedCandidate(fresh) }} onApplication={candidate => { setSelectedCandidate(null); setModal({ type: 'application', candidateId: candidate.id }) }} canManage={canManageRoles} canReview={canReviewWorkflow} />}
    {selectedApplication && <ApplicationDrawer item={selectedApplication} interviews={interviews.filter(i => i.application_id === selectedApplication.id)} onClose={() => setSelectedApplication(null)} onSave={async (id, data) => { await act(() => api.updateApplication(id, data), 'Application updated.'); setSelectedApplication(null) }} onSchedule={() => { setSelectedApplication(null); setModal({ type: 'interview', applicationId: selectedApplication.id }) }} onDelete={async id => { await act(() => api.deleteApplication(id), 'Application deleted.'); setSelectedApplication(null) }} canEdit={canReviewWorkflow} canDelete={canManageRoles} />}
    {modal && <ModalHost modal={modal} onClose={() => setModal(null)} candidates={candidates} jobs={jobs} applications={applications} onCreateJob={data => act(() => api.createJob(data), 'Role created.')} onCreateApplication={data => act(() => api.createApplication(data), 'Application added to pipeline.')} onCreateInterview={data => act(() => api.createInterview(data), 'Interview scheduled.')} />}
  </div>
}

function LoginLoading() {
  return <div className="login-screen"><div className="login-card"><div className="brand-lockup"><div className="brand-symbol"><span>R</span><i/></div><div><div className="brand-name">resume<span>iq</span></div><div className="brand-descriptor">TALENT INTELLIGENCE</div></div></div><div className="loading-orb"><span/></div><strong>Checking workspace access</strong></div></div>
}

function LoginScreen({ onLogin }) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const submit = async event => {
    event.preventDefault()
    setBusy(true); setError('')
    try { await onLogin(email, password) } catch (err) { setError(err.message || 'Could not sign in.') } finally { setBusy(false) }
  }
  return <div className="login-screen"><div className="login-card"><div className="brand-lockup"><div className="brand-symbol"><span>R</span><i/></div><div><div className="brand-name">resume<span>iq</span></div><div className="brand-descriptor">TALENT INTELLIGENCE</div></div></div><div className="section-label">WORKSPACE ACCESS</div><h1>Welcome back.</h1><p>Sign in to view your recruitment workspace.</p><form className="form-stack" onSubmit={submit}><Field label="Work email"><input type="email" autoComplete="username" value={email} onChange={event => setEmail(event.target.value)} required placeholder="you@company.com"/></Field><Field label="Password"><input type="password" autoComplete="current-password" value={password} onChange={event => setPassword(event.target.value)} required placeholder="Your password"/></Field>{error && <div className="inline-error"><CircleAlert size={15}/>{error}</div>}<button className="button-primary wide" disabled={busy}>{busy ? 'Signing in...' : 'Sign in'} <ArrowRight size={15}/></button></form><span className="login-footnote"><ShieldCheck size={13}/> Read-only viewer accounts can access workspace records without editing them.</span></div></div>
}

function Sidebar({ page, setPage, counts, onUpload, user, canUpload, showSettings }) {
  const [mobileOpen, setMobileOpen] = useState(false)
  const visibleNav = NAV.filter(item => showSettings || item.id !== 'settings')
  const groups = [...new Set(visibleNav.map(item => item.group))]
  const userName = user?.display_name || user?.email || 'Recruitment Team'
  const roleLabel = user?.role ? `${user.role.charAt(0).toUpperCase()}${user.role.slice(1)} access` : 'Local workspace'
  return <>
    <button className="mobile-sidebar-toggle" onClick={() => setMobileOpen(!mobileOpen)}><Menu size={19}/></button>
    <aside className={`sidebar ${mobileOpen ? 'sidebar-open' : ''}`}>
      <div className="brand-lockup">
        <div className="brand-symbol"><span>R</span><i/></div>
        <div><div className="brand-name">resume<span>iq</span></div><div className="brand-descriptor">TALENT INTELLIGENCE</div></div>
      </div>
      <div className="workspace-switcher">
        <div className="workspace-avatar">R</div>
        <div className="workspace-copy"><strong>Recruitment team</strong><span>Workspace / Main</span></div>
        <ChevronDown size={15}/>
      </div>
      <nav className="sidebar-nav">
        {groups.map(group => <div className="nav-group" key={group}>
          <div className="nav-group-label">{group}</div>
          {visibleNav.filter(item => item.group === group).map(item => {
            const Icon = item.icon
            const count = item.id === 'candidates' ? counts.candidates : item.id === 'jobs' ? counts.jobs : null
            return <button key={item.id} className={`nav-item ${page === item.id ? 'active' : ''}`} onClick={() => { setPage(item.id); setMobileOpen(false) }}>
              <Icon size={17} strokeWidth={1.8}/><span>{item.label}</span>{count !== null && <em>{count}</em>}
            </button>
          })}
        </div>)}
      </nav>
      <div className="sidebar-bottom">
        {canUpload && <div className="sidebar-cta"><div className="cta-icon"><Sparkles size={16}/></div><strong>Less sorting.<br/>More signal.</strong><p>One clear workspace for every candidate and role.</p><button onClick={onUpload}>Upload resumes <ArrowUpRight size={14}/></button></div>}
        <div className="sidebar-user"><div className="user-avatar">{initials(userName)}</div><div><strong>{userName}</strong><span>{roleLabel}</span></div><MoreHorizontal size={18}/></div>
      </div>
    </aside>
  </>
}

function Topbar({ pageTitle, date, health, refreshing, onRefresh, onHelp, user, onLogout }) {
  return <header className="topbar">
    <div className="breadcrumbs"><span>Workspace</span><ChevronRight size={14}/><strong>{pageTitle}</strong></div>
    <div className="topbar-actions">
      <div className="topbar-date"><CalendarDays size={15}/><span>{date.toLocaleDateString(undefined, { weekday: 'short', day: '2-digit', month: 'short', year: 'numeric' })}</span></div>
      <div className={`api-status ${health ? 'online' : 'offline'}`}><i/>{health ? 'API connected' : 'API unavailable'}</div>
      <button className="icon-button" onClick={onRefresh} title="Refresh workspace"><RefreshCw size={16} className={refreshing ? 'spin' : ''}/></button>
      <button className="icon-button" onClick={onHelp} title="Help"><CircleHelp size={17}/></button>
      {user ? <button className="top-avatar user-top-avatar" title={`Signed in as ${user.email}. Click to sign out.`} onClick={onLogout}>{initials(user.display_name || user.email)}</button> : <div className="top-avatar">RT</div>}
    </div>
  </header>
}

function PageHeading({ eyebrow, title, description, actions, compact = false }) {
  return <div className={`page-heading ${compact ? 'compact' : ''}`}>
    <div><div className="eyebrow">{eyebrow}</div><h1>{title}</h1>{description && <p>{description}</p>}</div>
    {actions && <div className="heading-actions">{actions}</div>}
  </div>
}

function OverviewPage({ dashboard, jobs, applications, onNavigate, onUpload, onCreateJob, onOpenCandidate, canManage, canReview }) {
  const stats = [
    { label: 'Candidates in talent pool', value: dashboard?.total_candidates || 0, icon: Users, tone: 'ruby', note: 'Indexed profiles' },
    { label: 'Open positions', value: dashboard?.open_jobs || 0, icon: BriefcaseBusiness, tone: 'chrome', note: `${dashboard?.total_jobs || 0} total roles` },
    { label: 'Applications', value: dashboard?.total_applications || 0, icon: Layers3, tone: 'blue', note: 'Across all roles' },
    { label: 'Interviews scheduled', value: dashboard?.active_interviews || 0, icon: CalendarClock, tone: 'amber', note: `${dashboard?.matches_computed || 0} match results` },
  ]
  const pipelineTotal = Object.values(dashboard?.pipeline || {}).reduce((sum, value) => sum + value, 0)
  return <>
    <PageHeading eyebrow="WORKSPACE / OVERVIEW" title="Talent, in focus." description="A clear view of the candidate pool, open roles and hiring activity." actions={canManage ? <><button className="button-secondary" onClick={onCreateJob}><Plus size={16}/> New role</button><button className="button-primary" onClick={onUpload}><UploadCloud size={16}/> Upload resumes</button></> : <span className="access-pill">Read-only access</span>}/>
    <div className="welcome-strip"><div className="welcome-mark"><Sparkles size={18}/></div><div><strong>{canReview ? 'Your intelligence workspace is ready.' : 'Workspace overview.'}</strong><span>{canReview ? ' Add resumes and define a role to surface relevant candidate signals.' : ' Review candidates, roles and hiring activity across the workspace.'}</span></div><button onClick={() => onNavigate(canReview ? 'matching' : 'applications')}>{canReview ? 'Explore matching' : 'View applications'} <ArrowRight size={15}/></button></div>
    <section className="stat-grid">
      {stats.map(item => { const Icon = item.icon; return <div className="stat-card" key={item.label}><div className="stat-label">{item.label}<span className={`stat-icon ${item.tone}`}><Icon size={17}/></span></div><div className="stat-value">{item.value.toLocaleString()}</div><div className="stat-note"><span className="note-dot"/>{item.note}</div></div> })}
    </section>
    <section className="overview-grid">
      <div className="panel skill-panel">
        <div className="panel-heading"><div><div className="section-label">TALENT INTELLIGENCE</div><h2>Skill signals</h2><p>Skills appearing most often across the current talent pool.</p></div><button className="text-action" onClick={() => onNavigate('analytics')}>Full analytics <ArrowUpRight size={14}/></button></div>
        {dashboard?.top_skills?.length ? <div className="skill-bars">{dashboard.top_skills.slice(0, 7).map((item, index) => <div className="skill-bar-row" key={item.skill}><span>{item.skill}</span><div className="bar-track"><i style={{ width: `${Math.max(4, item.count / dashboard.top_skills[0].count * 100)}%` }}/></div><b>{item.count}</b></div>)}</div> : <EmptyState icon={Activity} title="No skill signals yet" text="Skill signals will appear as resumes are added to the workspace." action={canManage ? "Upload first resume" : undefined} onClick={canManage ? onUpload : undefined}/>}
      </div>
      <div className="panel pipeline-panel">
        <div className="panel-heading"><div><div className="section-label">RECRUITMENT FLOW</div><h2>Hiring pipeline</h2><p>Applications moving through the process.</p></div><span className="live-pill"><i/> LIVE</span></div>
        <div className="pipeline-summary"><strong>{pipelineTotal}</strong><span>active applications</span></div>
        <div className="pipeline-mini">{STAGES.map(stage => <button key={stage.id} onClick={() => onNavigate('applications')} className="pipeline-mini-row"><span className={`stage-dot ${stage.color}`}/><span>{stage.label}</span><b>{dashboard?.pipeline?.[stage.id] || 0}</b><ChevronRight size={14}/></button>)}</div>
        <div className="panel-footnote"><ShieldCheck size={14}/> Match scores are estimates, not hiring decisions.</div>
      </div>
    </section>
    <section className="bottom-grid">
      <div className="panel roles-panel">
        <div className="panel-heading"><div><div className="section-label">HIRING NEEDS</div><h2>Open roles</h2><p>Roles currently accepting candidates.</p></div><button className="text-action" onClick={() => onNavigate('jobs')}>View roles <ArrowUpRight size={14}/></button></div>
        {jobs.filter(job => job.status === 'open').length ? jobs.filter(job => job.status === 'open').slice(0, 4).map(job => <div className="role-row" key={job.id}><div className="role-icon"><BriefcaseBusiness size={17}/></div><div className="role-info"><strong>{job.title}</strong><span>{job.department} · {job.location}</span></div><div className="role-count"><b>{job.application_count || applications.filter(app => app.job_id === job.id).length}</b><span>applications</span></div><ChevronRight size={15}/></div>) : <EmptyState icon={BriefcaseBusiness} title="No open roles" text="Open roles will appear here once they are added to the workspace." action={canManage ? "Create a role" : undefined} onClick={canManage ? onCreateJob : undefined}/>}
      </div>
      <div className="panel activity-panel">
        <div className="panel-heading"><div><div className="section-label">WORKSPACE HISTORY</div><h2>Recent activity</h2><p>The latest changes across the workspace.</p></div></div>
        {dashboard?.recent_activity?.length ? dashboard.recent_activity.slice(0, 5).map((event, index) => <div className="activity-row" key={event.id}><div className={`activity-mark mark-${index % 4}`}><Activity size={14}/></div><div className="activity-copy"><strong>{event.description}</strong><span>{fmtDate(event.created_at, { day: '2-digit', month: 'short' })} · {fmtTime(event.created_at)}{event.actor_email ? ` · ${event.actor_email}` : ''}</span></div></div>) : <EmptyState icon={Activity} title="Nothing happening yet" text="Workspace activity will appear here as records are updated."/>}
      </div>
    </section>
  </>
}

function CandidatesPage({ candidates, jobs, onUpload, onOpen, onDelete, onCreateApplication, canManage, canReview }) {
  const [query, setQuery] = useState('')
  const [reviewOnly, setReviewOnly] = useState(false)
  const filtered = candidates.filter(candidate => {
    const match = `${candidate.full_name} ${candidate.email || ''} ${candidate.headline || ''} ${(candidate.skills || []).join(' ')}`.toLowerCase().includes(query.toLowerCase())
    return match && (!reviewOnly || candidate.extraction_quality?.requires_review)
  })
  return <>
    <PageHeading eyebrow="TALENT / CANDIDATES" title="The talent pool." description="Candidate profiles, extracted skills and source documents in one place." actions={canManage ? <button className="button-primary" onClick={onUpload}><UploadCloud size={16}/> Upload resumes</button> : <span className="access-pill">Read-only access</span>}/>
    <div className="toolbar"><div className="search-field"><Search size={17}/><input value={query} onChange={e => setQuery(e.target.value)} placeholder="Search people, skills or titles..."/><kbd>/</kbd></div><button className={`filter-button ${reviewOnly ? 'selected' : ''}`} onClick={() => setReviewOnly(!reviewOnly)}><Filter size={15}/> Needs review {reviewOnly && <X size={13}/>}</button><span className="result-count">{filtered.length} profiles</span></div>
    <div className="panel table-panel">
      <div className="table-headline"><div><span className="section-label">CANDIDATE DIRECTORY</span><h2>Profiles <span>{filtered.length}</span></h2></div><div className="table-meta">Sorted by recently updated</div></div>
      {filtered.length ? <div className="table-scroll"><table className="data-table"><thead><tr><th>Candidate</th><th>Profile</th><th>Core skills</th><th>Experience</th><th>Parser signal</th><th/></tr></thead><tbody>{filtered.map(candidate => <tr key={candidate.id} onClick={() => onOpen(candidate.id)} className="clickable-row"><td><div className="person-cell"><div className="person-avatar">{initials(candidate.full_name)}</div><div><strong>{candidate.full_name}</strong><span>{candidate.email || 'Email not found'}</span></div></div></td><td><div className="profile-cell"><strong>{candidate.headline || 'Profile needs review'}</strong><span>{candidate.location || 'Location not listed'}</span></div></td><td><div className="chip-list">{(candidate.skills || []).slice(0, 3).map(skill => <span className="skill-chip" key={skill}>{skill}</span>)}{candidate.skills?.length > 3 && <span className="more-chip">+{candidate.skills.length - 3}</span>}</div></td><td className="numeric-cell">{candidate.total_experience_years === null ? '—' : `${candidate.total_experience_years} yrs`}</td><td><QualityPill quality={candidate.extraction_quality}/></td><td><div className="row-actions">{canReview && <button title="Add to role" onClick={e => { e.stopPropagation(); onCreateApplication(candidate) }}><Plus size={15}/></button>}{canManage && <button title="Delete candidate" onClick={e => { e.stopPropagation(); if (window.confirm(`Delete ${candidate.full_name} and their stored resume?`)) onDelete(candidate.id) }}><Trash2 size={15}/></button>}<ChevronRight size={16}/></div></td></tr>)}</tbody></table></div> : <EmptyState icon={Users} title="No candidate profiles yet" text="Candidate profiles will appear here when resumes are added to the workspace." action={canManage ? "Upload a resume" : undefined} onClick={canManage ? onUpload : undefined}/>}
    </div>
  </>
}

function QualityPill({ quality }) {
  const score = quality?.score ?? 0
  const needsReview = quality?.requires_review
  return <span className={`quality-pill ${needsReview ? 'review' : 'verified'}`}><i/>{score ? `${score}% signal` : 'No score'} {needsReview ? '· Review' : '· Ready'}</span>
}

function JobsPage({ jobs, applications, onCreate, onUpdate, onDelete, onNavigate, canManage }) {
  const [filter, setFilter] = useState('all')
  const filtered = jobs.filter(job => filter === 'all' || job.status === filter)
  return <>
    <PageHeading eyebrow="HIRING / ROLES" title="Roles with purpose." description="Review role requirements, hiring status and application activity." actions={canManage ? <button className="button-primary" onClick={onCreate}><Plus size={16}/> Create role</button> : <span className="access-pill">Read-only access</span>}/>
    <div className="segmented-toolbar"><div className="segmented-control">{[['all', 'All roles'], ['open', 'Open'], ['paused', 'Paused'], ['closed', 'Closed']].map(([id, label]) => <button key={id} className={filter === id ? 'active' : ''} onClick={() => setFilter(id)}>{label}<span>{id === 'all' ? jobs.length : jobs.filter(job => job.status === id).length}</span></button>)}</div><span className="result-count">{filtered.length} roles</span></div>
    <div className="job-grid">{filtered.map(job => <article className="job-card" key={job.id}><div className="job-card-top"><span className={`job-status ${job.status}`}>{job.status}</span>{canManage && <button className="ghost-icon" title="Delete role" onClick={() => { if (window.confirm(`Delete ${job.title}? Associated applications and interviews will also be removed.`)) onDelete(job.id) }}><MoreHorizontal size={18}/></button>}</div><div className="job-card-icon"><BriefcaseBusiness size={20}/></div><h2>{job.title}</h2><div className="job-meta"><span><Building2 size={13}/>{job.department}</span><span><MapPin size={13}/>{job.location}</span></div><p>{job.description}</p><div className="job-tags">{(job.required_skills || []).slice(0, 5).map(skill => <span key={skill}>{skill}</span>)}{job.required_skills?.length > 5 && <span>+{job.required_skills.length - 5}</span>}</div><div className="job-card-bottom"><div className="job-applicants"><Users size={15}/><strong>{job.application_count ?? applications.filter(app => app.job_id === job.id).length}</strong><span>in pipeline</span></div><div className="job-actions"><button className="text-action" onClick={() => onNavigate('applications')}>Pipeline <ArrowUpRight size={14}/></button>{canManage && <button className="button-small" onClick={() => onUpdate(job.id, { status: job.status === 'open' ? 'paused' : 'open' })}>{job.status === 'open' ? 'Pause role' : 'Reopen'}</button>}</div></div></article>)}</div>
    {!filtered.length && <div className="panel"><EmptyState icon={BriefcaseBusiness} title="No roles in this view" text={canManage ? "Create a role to start matching candidates against a clear brief." : "No roles have been added to this workspace yet."} action={canManage ? "Create role" : undefined} onClick={canManage ? onCreate : undefined}/></div>}
  </>
}

function ApplicationsPage({ applications, onUpdate, onOpen, onCreate, canEdit }) {
  const [dragging, setDragging] = useState(null)
  const [filter, setFilter] = useState('all')
  const visible = applications.filter(item => filter === 'all' || item.job_id === Number(filter))
  return <>
    <PageHeading eyebrow="WORKFLOW / APPLICATIONS" title="The hiring pipeline." description="Review application progress and the context attached to each candidate." actions={canEdit ? <button className="button-primary" onClick={onCreate}><Plus size={16}/> Add application</button> : <span className="access-pill">Read-only access</span>}/>
    <div className="pipeline-toolbar"><div className="filter-select"><ListFilter size={16}/><select value={filter} onChange={e => setFilter(e.target.value)}><option value="all">All roles</option>{[...new Map(applications.map(item => [item.job_id, item.job_title])).entries()].map(([id, title]) => <option value={id} key={id}>{title}</option>)}</select><ChevronDown size={14}/></div><div className="pipeline-count"><span className="live-dot"/>{visible.length} applications in view</div><span className="drag-hint">{canEdit ? 'Drag cards to move stages' : 'Viewing only · stages cannot be changed'}</span></div>
    <div className="kanban-board">{STAGES.map(stage => {
      const items = visible.filter(item => item.stage === stage.id)
      return <div className={`kanban-column ${dragging && 'drag-active'}`} key={stage.id} onDragOver={e => { if (canEdit) e.preventDefault() }} onDrop={async e => { if (!canEdit) return; e.preventDefault(); const id = Number(e.dataTransfer.getData('text/plain')); if (id) await onUpdate(id, { stage: stage.id }); setDragging(null) }}>
        <div className="kanban-column-head"><div><span className={`stage-dot ${stage.color}`}/><strong>{stage.label}</strong><em>{items.length}</em></div>{canEdit && <button onClick={onCreate} title="Add application"><Plus size={15}/></button>}</div>
        <div className="kanban-cards">{items.map(item => <article key={item.id} className="application-card" draggable={canEdit} onDragStart={canEdit ? e => { e.dataTransfer.setData('text/plain', String(item.id)); setDragging(item.id) } : undefined} onDragEnd={canEdit ? () => setDragging(null) : undefined} onClick={() => onOpen(item)}><div className="application-card-top">{canEdit ? <span className="drag-grip">⠿</span> : <span className="stage-dot steel" />}<span>{fmtDate(item.created_at, { day: '2-digit', month: 'short' })}</span><MoreHorizontal size={16}/></div><div className="application-person"><div className="person-avatar small">{initials(item.candidate_name)}</div><div><strong>{item.candidate_name}</strong><span>{item.candidate_headline || 'Candidate profile'}</span></div></div><div className="application-role"><BriefcaseBusiness size={13}/>{item.job_title}</div><div className="application-skills">{(item.candidate_skills || []).slice(0, 3).map(skill => <span key={skill}>{skill}</span>)}</div><div className="application-card-bottom"><span>{item.candidate_experience === null ? 'Experience n/a' : `${item.candidate_experience} yrs experience`}</span><span className="view-detail">Details <ArrowUpRight size={12}/></span></div></article>)}
          {!items.length && <div className="kanban-empty">{canEdit ? 'Drop an application here' : 'No applications in this stage'}</div>}
        </div>
      </div>
    })}</div>
  </>
}

function MatchingPage({ jobs, applications, onCreateApplication, canEdit }) {
  const [jobId, setJobId] = useState('')
  const [matches, setMatches] = useState([])
  const [busy, setBusy] = useState(false)
  const [ranAt, setRanAt] = useState(null)
  const [error, setError] = useState('')
  const selectedJob = jobs.find(job => job.id === Number(jobId))
  useEffect(() => { if (!jobId && jobs.length) setJobId(String(jobs.find(job => job.status === 'open')?.id || jobs[0].id)) }, [jobs, jobId])
  useEffect(() => { if (jobId) api.matches(jobId).then(data => setMatches(data)).catch(() => setMatches([])) }, [jobId])
  const run = async () => {
    if (!jobId || !canEdit) return
    setBusy(true); setError('')
    try { const result = await api.runMatching(Number(jobId)); setMatches(result.results); setRanAt(new Date()); }
    catch (err) { setError(err.message) }
    finally { setBusy(false) }
  }
  const existingApplicationIds = new Set(applications.filter(app => app.job_id === Number(jobId)).map(app => app.candidate_id))
  return <>
    <PageHeading eyebrow="INTELLIGENCE / ROLE FIT" title="Find the signal." description="Compare candidate evidence against role requirements, then inspect why a profile surfaced." actions={canEdit ? <span className="method-pill"><BrainCircuit size={15}/> Explainable matching</span> : <span className="access-pill">Read-only results</span>}/>
    <div className="match-hero panel"><div className="match-hero-copy"><div className="section-label">MATCHING WORKSPACE</div><h2>Role context in.<br/><em>Relevant profiles out.</em></h2><p>ResumeIQ blends skill coverage, text relevance, experience fit and education alignment into a transparent relevance estimate.</p></div><div className="match-controls"><label>Choose a role<select value={jobId} onChange={e => setJobId(e.target.value)}><option value="">Select a role</option>{jobs.map(job => <option value={job.id} key={job.id}>{job.title} · {job.department}</option>)}</select></label>{selectedJob && <div className="match-role-context"><strong>{selectedJob.title}</strong><span>{selectedJob.required_skills?.length || 0} required skills · {selectedJob.minimum_experience || 0}+ years</span></div>}{canEdit ? <button className="button-primary wide" disabled={!selectedJob || busy} onClick={run}>{busy ? <RefreshCw className="spin" size={16}/> : <Sparkles size={16}/>} {busy ? 'Evaluating profiles...' : 'Run candidate matching'}</button> : <div className="read-only-callout">Existing results are available for review. Viewer access cannot start new matching runs.</div>}{ranAt && <span className="run-stamp">Last computed {fmtTime(ranAt)}</span>}</div></div>
    {error && <div className="inline-error"><CircleAlert size={15}/>{error}</div>}
    <div className="match-results-heading"><div><div className="section-label">RANKED PROFILES</div><h2>Candidate results <span>{matches.length}</span></h2></div><span className="result-count">Scores are relevance estimates</span></div>
    {matches.length ? <div className="match-list">{matches.map((match, index) => <article className="match-card" key={match.id}><div className="match-rank">{String(index + 1).padStart(2, '0')}</div><div className="match-main"><div className="match-person"><div className="person-avatar">{initials(match.candidate_name)}</div><div><strong>{match.candidate_name}</strong><span>{match.candidate_headline || 'Candidate profile'} · {match.candidate_experience ?? '—'} years</span></div></div><div className="match-skills"><span className="match-label">Matched</span>{match.matched_skills.slice(0, 5).map(skill => <i key={skill}>{skill}</i>)}{!match.matched_skills.length && <small>No required skill overlap</small>}</div><div className="match-skills missing"><span className="match-label">Gaps</span>{match.missing_skills.slice(0, 4).map(skill => <i key={skill}>{skill}</i>)}{!match.missing_skills.length && <small>No required skill gaps detected</small>}</div><div className="match-explain">{match.explanation.slice(0, 2).map(line => <p key={line}><CheckCircle2 size={13}/>{line}</p>)}</div></div><div className="match-score"><div className="score-ring" style={{ '--score': `${match.overall_score}%` }}><div><strong>{Math.round(match.overall_score)}</strong><span>FIT</span></div></div><div className="score-components">{Object.entries(match.component_scores).filter(([key]) => key !== 'weights').map(([key, value]) => <div key={key}><span>{key.replace('_', ' ')}</span><b>{value}%</b></div>)}</div>{canEdit && <button className="button-small" disabled={existingApplicationIds.has(match.candidate_id)} onClick={() => onCreateApplication({ candidate_id: match.candidate_id, job_id: Number(jobId), stage: 'new', source: 'matching', notes: `Added from matching run. Score: ${match.overall_score}%.` })}>{existingApplicationIds.has(match.candidate_id) ? <><Check size={13}/> In pipeline</> : <><Plus size={13}/> Add to pipeline</>}</button>}</div></article>)}</div> : <div className="panel"><EmptyState icon={Target} title="No matching results yet" text={jobs.length ? 'No saved matching results are available for this role.' : 'No roles are available in the workspace yet.'}/></div>}
  </>
}

function InterviewsPage({ interviews, applications, onCreate, onUpdate, canEdit }) {
  const [feedbackInterview, setFeedbackInterview] = useState(null)
  const upcoming = interviews.filter(item => item.status === 'scheduled' && new Date(item.scheduled_at) >= new Date()).sort((a, b) => new Date(a.scheduled_at) - new Date(b.scheduled_at))
  const completed = interviews.filter(item => item.status !== 'scheduled')
  return <>
    <PageHeading eyebrow="WORKFLOW / INTERVIEW OPERATIONS" title="Every conversation, connected." description="Review interview schedules, participants and feedback linked to each application." actions={canEdit ? <button className="button-primary" onClick={onCreate} disabled={!applications.length}><Plus size={16}/> Schedule interview</button> : <span className="access-pill">Read-only access</span>}/>
    <section className="stat-grid interview-stats"><MiniStat label="Upcoming" value={upcoming.length} icon={CalendarClock}/><MiniStat label="Completed" value={completed.filter(item => item.status === 'completed').length} icon={CheckCheck}/><MiniStat label="Applications" value={applications.length} icon={Users}/><MiniStat label="Scheduled next" value={upcoming[0] ? fmtDate(upcoming[0].scheduled_at, { day: '2-digit', month: 'short' }) : '—'} icon={Clock3}/></section>
    <div className="panel table-panel"><div className="table-headline"><div><span className="section-label">INTERVIEW CALENDAR</span><h2>Upcoming conversations <span>{upcoming.length}</span></h2></div></div>
      {upcoming.length ? <div className="interview-list">{upcoming.map(item => <div className="interview-row" key={item.id}><div className="interview-date"><strong>{new Date(item.scheduled_at).getDate()}</strong><span>{new Date(item.scheduled_at).toLocaleDateString(undefined, { month: 'short' })}</span></div><div className="interview-primary"><strong>{item.title}</strong><span>{item.candidate_name} · {item.job_title}</span></div><div className="interview-kind"><span>{item.interview_type}</span><small>{fmtTime(item.scheduled_at)} · {item.duration_minutes} min</small></div><div className="interview-people">{item.interviewers?.slice(0, 2).map(name => <span key={name}>{initials(name)}</span>)}</div>{canEdit && <button className="button-small" onClick={() => setFeedbackInterview(item)}>Add feedback</button>}</div>)}</div> : <EmptyState icon={CalendarClock} title="No interviews scheduled" text="Scheduled interviews will appear here once they are added to an application." action={canEdit && applications.length ? "Schedule interview" : undefined} onClick={canEdit && applications.length ? onCreate : undefined}/>}
    </div>
    <div className="panel completed-panel"><div className="table-headline"><div><span className="section-label">HISTORY</span><h2>Past & completed</h2></div></div>{completed.length ? completed.map(item => <div className="completed-row" key={item.id}><span className={`status-dot ${item.status}`}/><strong>{item.candidate_name}</strong><span>{item.title}</span><small>{fmtDate(item.scheduled_at)}</small>{(canEdit || item.scorecard || item.notes) && <button className="text-action" onClick={() => setFeedbackInterview(item)}>{canEdit ? 'View feedback' : 'View details'}</button>}{canEdit && <button className="text-action" onClick={() => onUpdate(item.id, { status: 'scheduled' })}>Reopen</button>}</div>) : <div className="muted-empty">Completed interviews and scorecards will appear here.</div>}</div>
    {feedbackInterview && <InterviewFeedbackModal item={feedbackInterview} readOnly={!canEdit} onClose={() => setFeedbackInterview(null)} onSave={async data => { await onUpdate(feedbackInterview.id, data); setFeedbackInterview(null) }}/>}
  </>
}

function InterviewFeedbackModal({ item, onClose, onSave, readOnly = false }) {
  const existing = item.scorecard || {}
  const [form, setForm] = useState({
    technical: String(existing.technical ?? 3),
    problem_solving: String(existing.problem_solving ?? 3),
    communication: String(existing.communication ?? 3),
    overall: String(existing.overall ?? 3),
    recommendation: existing.recommendation || 'lean_yes',
    notes: item.notes || ''
  })
  const [busy, setBusy] = useState(false)
  const update = event => setForm(value => ({ ...value, [event.target.name]: event.target.value }))
  const submit = async event => {
    event.preventDefault()
    if (readOnly) return
    setBusy(true)
    try {
      const scorecard = {
        technical: Number(form.technical),
        problem_solving: Number(form.problem_solving),
        communication: Number(form.communication),
        overall: Number(form.overall),
        recommendation: form.recommendation
      }
      await onSave({ scorecard, notes: form.notes, status: 'completed' })
    } finally { setBusy(false) }
  }
  return <Modal title="Interview feedback" subtitle={`${item.candidate_name} · ${item.job_title} · ${item.title}`} onClose={onClose}>
    <form className="form-stack" onSubmit={submit}>
      <div className="form-two">
        <Field label="Technical depth (1–5)"><select name="technical" value={form.technical} onChange={update} disabled={readOnly}>{[1,2,3,4,5].map(value => <option value={value} key={value}>{value} / 5</option>)}</select></Field>
        <Field label="Problem solving (1–5)"><select name="problem_solving" value={form.problem_solving} onChange={update} disabled={readOnly}>{[1,2,3,4,5].map(value => <option value={value} key={value}>{value} / 5</option>)}</select></Field>
        <Field label="Communication (1–5)"><select name="communication" value={form.communication} onChange={update} disabled={readOnly}>{[1,2,3,4,5].map(value => <option value={value} key={value}>{value} / 5</option>)}</select></Field>
        <Field label="Overall assessment (1–5)"><select name="overall" value={form.overall} onChange={update} disabled={readOnly}>{[1,2,3,4,5].map(value => <option value={value} key={value}>{value} / 5</option>)}</select></Field>
      </div>
      <Field label="Recommendation"><select name="recommendation" value={form.recommendation} onChange={update} disabled={readOnly}><option value="strong_yes">Strong yes</option><option value="lean_yes">Lean yes</option><option value="undecided">Undecided</option><option value="lean_no">Lean no</option><option value="strong_no">Strong no</option></select></Field>
      <Field label="Evidence and notes"><textarea name="notes" rows="5" value={form.notes} onChange={update} disabled={readOnly} placeholder="No interview notes have been recorded."/></Field>
      <div className="modal-actions">{readOnly ? <button type="button" className="button-secondary" onClick={onClose}>Close</button> : <><button type="button" className="button-secondary" onClick={onClose}>Cancel</button><button className="button-primary" disabled={busy}>{busy ? 'Saving feedback...' : 'Save scorecard'} <Check size={15}/></button></>}</div>
    </form>
  </Modal>
}

function AnalyticsPage({ dashboard, applications, jobs, interviews }) {
  const pipeline = dashboard?.pipeline || {}
  const max = Math.max(1, ...STAGES.map(stage => pipeline[stage.id] || 0))
  const jobStats = jobs.map(job => ({ title: job.title, count: applications.filter(item => item.job_id === job.id).length })).sort((a, b) => b.count - a.count).slice(0, 6)
  return <>
    <PageHeading eyebrow="INTELLIGENCE / ANALYTICS" title="Understand the movement." description="Operational signals from your actual candidates, roles and applications." actions={<span className="live-pill"><i/> LIVE DATA</span>}/>
    <section className="stat-grid"><MiniStat label="Total candidates" value={dashboard?.total_candidates || 0} icon={Users}/><MiniStat label="Open positions" value={dashboard?.open_jobs || 0} icon={BriefcaseBusiness}/><MiniStat label="Applications" value={applications.length} icon={Layers3}/><MiniStat label="Average match score" value={`${dashboard?.average_match_score || 0}%`} icon={Gauge}/></section>
    <div className="analytics-grid"><div className="panel"><div className="panel-heading"><div><div className="section-label">APPLICATION DISTRIBUTION</div><h2>Pipeline stages</h2><p>Where active applications currently sit.</p></div></div><div className="analytics-bars">{STAGES.map(stage => <div className="analytics-bar-row" key={stage.id}><span>{stage.label}</span><div className="bar-track"><i className={`fill-${stage.color}`} style={{ width: `${(pipeline[stage.id] || 0) / max * 100}%` }}/></div><b>{pipeline[stage.id] || 0}</b></div>)}</div></div><div className="panel"><div className="panel-heading"><div><div className="section-label">ROLE ACTIVITY</div><h2>Applications by role</h2><p>Current applications grouped by requisition.</p></div></div>{jobStats.length ? <div className="role-stat-list">{jobStats.map(item => <div key={item.title}><span>{item.title}</span><b>{item.count}</b></div>)}</div> : <div className="muted-empty">Create roles and applications to populate this view.</div>}</div></div>
    <div className="analytics-footnote"><ShieldCheck size={15}/> Metrics are descriptive operational data. They do not establish model accuracy or hiring quality.</div>
  </>
}

function SettingsPage({ health, onRefresh, user }) {
  return <>
    <PageHeading eyebrow="MANAGE / WORKSPACE" title="Workspace settings." description="Service health, document processing and access management." actions={<button className="button-secondary" onClick={onRefresh}><RefreshCw size={15}/> Check health</button>}/>
    <div className="settings-grid"><div className="panel settings-main"><div className="panel-heading"><div><div className="section-label">SYSTEM STATUS</div><h2>Services & connectivity</h2><p>Current status reported by the backend.</p></div><span className={`api-status ${health ? 'online' : 'offline'}`}><i/>{health ? 'Operational' : 'Unavailable'}</span></div><div className="service-row"><div className="service-icon"><Code2 size={18}/></div><div><strong>ResumeIQ API</strong><span>{health?.service || 'FastAPI service'}</span></div><b>{health?.status || 'Unknown'}</b></div><div className="service-row"><div className="service-icon"><Layers3 size={18}/></div><div><strong>Database</strong><span>Persistent candidate and workflow records</span></div><b>{health?.database || 'Unknown'}</b></div><div className="service-row"><div className="service-icon"><FileSearch size={18}/></div><div><strong>Resume parser</strong><span>PDF and DOCX document processing</span></div><b>Ready</b></div><div className="service-row"><div className="service-icon"><BrainCircuit size={18}/></div><div><strong>Matching engine</strong><span>Skills, text relevance, experience and education</span></div><b>Ready</b></div></div><div className="panel settings-side"><div className="section-label">DOCUMENT PROCESSING</div><h2>Parser boundaries</h2><p>Text-based PDFs and DOCX documents are supported. OCR is optional and requires Tesseract to be installed and enabled.</p><div className="setting-line"><span>Maximum upload</span><strong>Configured limit</strong></div><div className="setting-line"><span>Supported formats</span><strong>PDF · DOCX</strong></div><div className="setting-line"><span>OCR</span><strong>Optional</strong></div><div className="setting-line"><span>Field evidence</span><strong>Enabled</strong></div></div></div>
    {user?.role === 'admin' && <WorkspaceUsers/>}
    <div className="panel security-note"><div className="security-icon"><ShieldCheck size={20}/></div><div><strong>Access and candidate privacy</strong><p>Workspace viewer accounts can inspect candidate records, resume files, applications and interview feedback but cannot modify them. This is internal access, not public access. Grant it only to trusted people who are permitted to view sensitive recruitment information.</p></div></div>
  </>
}

function WorkspaceUsers() {
  const [users, setUsers] = useState([])
  const [form, setForm] = useState({ display_name: '', email: '', password: '', role: 'viewer' })
  const [loadingUsers, setLoadingUsers] = useState(true)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  const loadUsers = async () => {
    setLoadingUsers(true)
    try { setUsers(await api.users()); setError('') }
    catch (err) { setError(err.message || 'Could not load workspace accounts.') }
    finally { setLoadingUsers(false) }
  }
  useEffect(() => { loadUsers() }, [])
  const update = event => setForm(value => ({ ...value, [event.target.name]: event.target.value }))
  const submit = async event => {
    event.preventDefault()
    setBusy(true)
    setError('')
    setMessage('')
    try {
      const created = await api.createUser(form)
      setMessage(`${created.display_name} can now sign in as a ${created.role}. Share the initial password securely; no invitation email is sent.`)
      setForm({ display_name: '', email: '', password: '', role: 'viewer' })
      await loadUsers()
    } catch (err) {
      setError(err.message || 'Could not create the workspace account.')
    } finally { setBusy(false) }
  }
  const roleLabel = role => ({ admin: 'Administrator', recruiter: 'Recruiter', reviewer: 'Reviewer', interviewer: 'Interviewer', viewer: 'Viewer' }[role] || role)
  return <section className="panel workspace-users-panel">
    <div className="panel-heading"><div><div className="section-label">ACCESS / TEAM MEMBERS</div><h2>Workspace accounts</h2><p>Create accounts and assign the access level required for each person.</p></div><span className="result-count">{users.length} accounts</span></div>
    <div className="viewer-access-warning"><ShieldCheck size={17}/><div><strong>Viewer access is read-only</strong><p>Viewers can inspect roles, candidates, applications, interview schedules, recruiter notes and feedback. They cannot change records or manage accounts.</p></div></div>
    <form className="form-grid workspace-user-form" onSubmit={submit}>
      <Field label="Display name"><input name="display_name" value={form.display_name} onChange={update} required minLength="2" maxLength="180" placeholder="e.g. Alex Morgan"/></Field>
      <Field label="Work email"><input type="email" name="email" value={form.email} onChange={update} required maxLength="254" placeholder="alex@company.com"/></Field>
      <Field label="Initial password"><input type="password" name="password" value={form.password} onChange={update} required minLength="12" maxLength="200" autoComplete="new-password" placeholder="At least 12 characters"/></Field>
      <Field label="Access level"><select name="role" value={form.role} onChange={update}><option value="viewer">Viewer · Read-only</option><option value="reviewer">Reviewer · Application workflow</option><option value="interviewer">Interviewer · Assigned interviews</option><option value="recruiter">Recruiter · Workspace operations</option></select></Field>
      <div className="workspace-user-form-foot"><span>Share the initial password through a separate secure channel. Password recovery is not configured.</span><button className="button-primary" disabled={busy}>{busy ? 'Creating account...' : 'Create account'} <Plus size={15}/></button></div>
    </form>
    {error && <div className="inline-error"><CircleAlert size={15}/>{error}</div>}
    {message && <div className="inline-success"><CheckCircle2 size={15}/>{message}</div>}
    <div className="workspace-user-list"><div className="workspace-user-list-head"><strong>Current accounts</strong><button className="text-action" type="button" onClick={loadUsers}><RefreshCw size={13}/> Refresh</button></div>
      {loadingUsers ? <div className="muted-empty">Loading workspace accounts...</div> : users.length ? users.map(item => <div className="workspace-user-row" key={item.id}><div className="user-avatar">{initials(item.display_name || item.email)}</div><div className="workspace-user-copy"><strong>{item.display_name}</strong><span>{item.email}</span></div><span className={`role-pill role-${item.role}`}>{roleLabel(item.role)}</span><span className={`account-status ${item.is_active ? 'active' : 'inactive'}`}>{item.is_active ? 'Active' : 'Disabled'}</span></div>) : <div className="muted-empty">No workspace accounts were found.</div>}
    </div>
  </section>
}

function MiniStat({ label, value, icon: Icon }) {
  return <div className="stat-card compact-stat"><div className="stat-label">{label}<span className="stat-icon chrome"><Icon size={17}/></span></div><div className="stat-value">{value}</div></div>
}

function EmptyState({ icon: Icon, title, text, action, onClick }) {
  return <div className="empty-state"><div className="empty-icon"><Icon size={22}/></div><h3>{title}</h3><p>{text}</p>{action && onClick && <button className="button-secondary" onClick={onClick}>{action}<ArrowRight size={14}/></button>}</div>
}

function LoadingState() {
  return <div className="loading-page"><div className="loading-orb"><span/></div><strong>Opening your workspace</strong><span>Connecting candidates, roles and hiring activity.</span></div>
}

function AnimateToast({ toast }) {
  if (!toast) return null
  const Icon = toast.tone === 'error' ? CircleAlert : toast.tone === 'warning' ? CircleHelp : CheckCircle2
  return <div className={`toast ${toast.tone}`}><Icon size={17}/>{toast.message}</div>
}

function Modal({ title, subtitle, onClose, children, wide = false }) {
  useEffect(() => {
    const onKey = event => { if (event.key === 'Escape') onClose() }
    window.addEventListener('keydown', onKey)
    document.body.style.overflow = 'hidden'
    return () => { window.removeEventListener('keydown', onKey); document.body.style.overflow = '' }
  }, [onClose])
  return <div className="modal-backdrop" onMouseDown={event => { if (event.target === event.currentTarget) onClose() }}><section className={`modal-card ${wide ? 'wide' : ''}`}><div className="modal-heading"><div><div className="section-label">RESUMEIQ WORKSPACE</div><h2>{title}</h2>{subtitle && <p>{subtitle}</p>}</div><button className="icon-button" onClick={onClose}><X size={18}/></button></div>{children}</section></div>
}

function ModalHost({ modal, onClose, candidates, jobs, applications, onCreateJob, onCreateApplication, onCreateInterview }) {
  if (modal.type === 'job') return <JobModal onClose={onClose} onSubmit={async data => { await onCreateJob(data); onClose() }}/>
  if (modal.type === 'application') return <ApplicationModal modal={modal} candidates={candidates} jobs={jobs} onClose={onClose} onSubmit={async data => { await onCreateApplication(data); onClose() }}/>
  if (modal.type === 'interview') return <InterviewModal modal={modal} applications={applications} onClose={onClose} onSubmit={async data => { await onCreateInterview(data); onClose() }}/>
  if (modal.type === 'help') return <Modal title="A little orientation" subtitle="The main workflows, without the scavenger hunt." onClose={onClose}><div className="help-list"><div><UploadCloud/><span><strong>Build your talent pool</strong><small>Upload PDF or DOCX resumes and review extracted evidence.</small></span></div><div><BriefcaseBusiness/><span><strong>Define a role</strong><small>Capture the requirements that matching will evaluate.</small></span></div><div><BrainCircuit/><span><strong>Compare with context</strong><small>Run the explainable baseline and inspect strengths and gaps.</small></span></div><div><Layers3/><span><strong>Move applications</strong><small>Keep notes, stage changes and interviews attached to each application.</small></span></div></div></Modal>
  return null
}

function JobModal({ onClose, onSubmit }) {
  const [form, setForm] = useState({ title: '', department: 'Engineering', location: 'Remote', work_mode: 'remote', employment_type: 'full-time', description: '', responsibilities: '', required_skills: '', preferred_skills: '', minimum_experience: '0', maximum_experience: '', education_requirement: '' })
  const [busy, setBusy] = useState(false)
  const update = event => setForm(value => ({ ...value, [event.target.name]: event.target.value }))
  const submit = async event => { event.preventDefault(); setBusy(true); try { await onSubmit({ ...form, responsibilities: form.responsibilities.split('\n').map(x => x.trim()).filter(Boolean), required_skills: commaList(form.required_skills), preferred_skills: commaList(form.preferred_skills), minimum_experience: Number(form.minimum_experience), maximum_experience: form.maximum_experience ? Number(form.maximum_experience) : null }) } finally { setBusy(false) } }
  return <Modal title="Create a role" subtitle="Write a clear brief so the intelligence layer has useful context." onClose={onClose} wide><form className="form-grid" onSubmit={submit}><Field label="Role title" required><input name="title" value={form.title} onChange={update} placeholder="e.g. Backend Engineer" required maxLength="180"/></Field><Field label="Department"><input name="department" value={form.department} onChange={update}/></Field><Field label="Location"><input name="location" value={form.location} onChange={update} placeholder="Remote / Bhubaneswar"/></Field><Field label="Work mode"><select name="work_mode" value={form.work_mode} onChange={update}><option value="remote">Remote</option><option value="hybrid">Hybrid</option><option value="onsite">On-site</option></select></Field><Field label="Employment type"><select name="employment_type" value={form.employment_type} onChange={update}><option value="full-time">Full-time</option><option value="part-time">Part-time</option><option value="contract">Contract</option><option value="internship">Internship</option><option value="temporary">Temporary</option></select></Field><Field label="Minimum experience (years)"><input type="number" min="0" max="60" step="0.5" name="minimum_experience" value={form.minimum_experience} onChange={update}/></Field><Field label="Maximum experience (years)"><input type="number" min="0" max="60" step="0.5" name="maximum_experience" value={form.maximum_experience} onChange={update} placeholder="Optional"/></Field><Field label="Education requirement"><input name="education_requirement" value={form.education_requirement} onChange={update} placeholder="e.g. B.Tech or equivalent"/></Field><Field label="Required skills" full><input name="required_skills" value={form.required_skills} onChange={update} placeholder="Python, FastAPI, PostgreSQL, Docker"/><small>Separate skills with commas.</small></Field><Field label="Preferred skills" full><input name="preferred_skills" value={form.preferred_skills} onChange={update} placeholder="Redis, Kubernetes, AWS"/></Field><Field label="Responsibilities" full><textarea name="responsibilities" rows="3" value={form.responsibilities} onChange={update} placeholder="One responsibility per line"/></Field><Field label="Job description" full><textarea name="description" rows="5" minLength="20" required value={form.description} onChange={update} placeholder="Describe the role, expectations and outcomes..."/></Field><div className="modal-actions"><button type="button" className="button-secondary" onClick={onClose}>Cancel</button><button type="submit" className="button-primary" disabled={busy}>{busy ? 'Saving role...' : 'Create role'} <ArrowRight size={15}/></button></div></form></Modal>
}

function ApplicationModal({ modal, candidates, jobs, onClose, onSubmit }) {
  const [candidateId, setCandidateId] = useState(modal.candidateId ? String(modal.candidateId) : '')
  const [jobId, setJobId] = useState('')
  const [notes, setNotes] = useState('')
  const [busy, setBusy] = useState(false)
  const submit = async event => { event.preventDefault(); setBusy(true); try { await onSubmit({ candidate_id: Number(candidateId), job_id: Number(jobId), stage: 'new', source: 'recruiter', notes }) } finally { setBusy(false) } }
  return <Modal title="Add to applications" subtitle="Connect a candidate to an open role." onClose={onClose}><form className="form-stack" onSubmit={submit}><Field label="Candidate"><select value={candidateId} onChange={e => setCandidateId(e.target.value)} required><option value="">Choose a candidate</option>{candidates.map(item => <option value={item.id} key={item.id}>{item.full_name} · {item.email || 'No email'}</option>)}</select></Field><Field label="Role"><select value={jobId} onChange={e => setJobId(e.target.value)} required><option value="">Choose an open role</option>{jobs.filter(job => job.status === 'open').map(item => <option value={item.id} key={item.id}>{item.title}</option>)}</select></Field><Field label="Recruiter note"><textarea rows="3" value={notes} onChange={e => setNotes(e.target.value)} placeholder="Context for the next reviewer..."/></Field><div className="modal-actions"><button type="button" className="button-secondary" onClick={onClose}>Cancel</button><button className="button-primary" disabled={busy || !candidates.length || !jobs.length}>{busy ? 'Adding...' : 'Add application'} <ArrowRight size={15}/></button></div></form></Modal>
}

function InterviewModal({ modal, applications, onClose, onSubmit }) {
  const [form, setForm] = useState({ application_id: modal.applicationId ? String(modal.applicationId) : '', title: 'Technical interview', interview_type: 'technical', scheduled_at: '', duration_minutes: '45', location_or_link: '', interviewers: '', notes: '' })
  const [busy, setBusy] = useState(false)
  const update = e => setForm(value => ({ ...value, [e.target.name]: e.target.value }))
  const submit = async e => { e.preventDefault(); setBusy(true); try { await onSubmit({ ...form, application_id: Number(form.application_id), scheduled_at: new Date(form.scheduled_at).toISOString(), duration_minutes: Number(form.duration_minutes), interviewers: commaList(form.interviewers) }) } finally { setBusy(false) } }
  return <Modal title="Schedule an interview" subtitle="Keep the conversation attached to the right candidate and role." onClose={onClose}><form className="form-stack" onSubmit={submit}><Field label="Application"><select name="application_id" value={form.application_id} onChange={update} required><option value="">Choose an application</option>{applications.map(item => <option value={item.id} key={item.id}>{item.candidate_name} · {item.job_title}</option>)}</select></Field><Field label="Interview title"><input name="title" value={form.title} onChange={update} required/></Field><div className="form-two"><Field label="Interview type"><select name="interview_type" value={form.interview_type} onChange={update}><option value="screening">Screening</option><option value="technical">Technical</option><option value="behavioral">Behavioral</option><option value="managerial">Managerial</option><option value="culture">Culture</option><option value="final">Final</option></select></Field><Field label="Duration"><select name="duration_minutes" value={form.duration_minutes} onChange={update}><option value="30">30 minutes</option><option value="45">45 minutes</option><option value="60">60 minutes</option><option value="90">90 minutes</option></select></Field></div><Field label="Date and time"><input type="datetime-local" name="scheduled_at" value={form.scheduled_at} onChange={update} required/></Field><Field label="Meeting link or location"><input name="location_or_link" value={form.location_or_link} onChange={update} placeholder="Meeting URL or room"/></Field><Field label="Interviewers"><input name="interviewers" value={form.interviewers} onChange={update} placeholder="Names separated by commas"/></Field><Field label="Notes"><textarea name="notes" rows="2" value={form.notes} onChange={update} placeholder="Agenda or preparation context..."/></Field><div className="modal-actions"><button type="button" className="button-secondary" onClick={onClose}>Cancel</button><button className="button-primary" disabled={busy || !applications.length}>{busy ? 'Scheduling...' : 'Schedule interview'} <CalendarClock size={15}/></button></div></form></Modal>
}

function Field({ label, required = false, full = false, children }) { return <label className={`field ${full ? 'full' : ''}`}><span>{label}{required && <i> *</i>}</span>{children}</label> }

function CandidateDrawer({ data, onClose, onSave, onApplication, canManage, canReview }) {
  const candidate = data.candidate || data
  const [editing, setEditing] = useState(false)
  const [saving, setSaving] = useState(false)
  const structuredKeys = ['experience', 'education', 'projects', 'certifications', 'achievements', 'publications', 'languages', 'volunteering', 'links']
  const [jsonFields, setJsonFields] = useState(() => Object.fromEntries(structuredKeys.map(key => [key, JSON.stringify(candidate[key] || (key === 'links' ? {} : []), null, 2)])))
  const [jsonError, setJsonError] = useState('')
  const [form, setForm] = useState({ full_name: candidate.full_name || '', email: candidate.email || '', phone: candidate.phone || '', location: candidate.location || '', headline: candidate.headline || '', summary: candidate.summary || '', total_experience_years: candidate.total_experience_years ?? '', skills: candidate.skills || [], soft_skills: candidate.soft_skills || [], tools: candidate.tools || [] })
  const update = e => setForm(value => ({ ...value, [e.target.name]: e.target.value }))
  const save = async e => {
    e.preventDefault()
    setSaving(true)
    setJsonError('')
    try {
      const structured = {}
      for (const key of structuredKeys) {
        const parsed = JSON.parse(jsonFields[key] || (key === 'links' ? '{}' : '[]'))
        if (key === 'links' ? (!parsed || Array.isArray(parsed) || typeof parsed !== 'object') : !Array.isArray(parsed)) {
          throw new Error(`${key} must be ${key === 'links' ? 'a JSON object' : 'a JSON array'}.`)
        }
        structured[key] = parsed
      }
      await onSave(candidate.id, {
        ...form,
        total_experience_years: form.total_experience_years === '' ? null : Number(form.total_experience_years),
        skills: Array.isArray(form.skills) ? form.skills : commaList(form.skills),
        soft_skills: Array.isArray(form.soft_skills) ? form.soft_skills : commaList(form.soft_skills),
        tools: Array.isArray(form.tools) ? form.tools : commaList(form.tools),
        ...structured
      })
      setEditing(false)
    } catch (error) {
      setJsonError(error.message || 'Check the structured profile JSON.')
    } finally {
      setSaving(false)
    }
  }
  const downloadResume = async document => {
    try { await api.downloadDocument(document.id, document.original_filename) }
    catch (error) { window.alert(error.message || 'Resume download failed.') }
  }
  const sections = [
    ['Experience', candidate.experience, item => <><strong>{item.role || 'Role not identified'}</strong><span>{item.company || 'Company not identified'} · {item.start_date || '—'} to {item.end_date || '—'}</span>{item.responsibilities?.map(text => <p key={text}>{text}</p>)}</>],
    ['Education', candidate.education, item => <><strong>{item.degree || 'Qualification'}</strong><span>{item.institution || 'Institution not identified'} · {item.end_date || '—'}</span></>],
    ['Projects', candidate.projects, item => <><strong>{item.name}</strong><span>{item.description || 'Description not extracted'}</span><div className="chip-list">{item.technologies?.map(skill => <span className="skill-chip" key={skill}>{skill}</span>)}</div></>],
    ['Certifications', candidate.certifications, item => <strong>{item.name || item.text || item.credential}</strong>],
    ['Achievements', candidate.achievements, item => <span>{item.text || item.title}</span>],
    ['Publications', candidate.publications, item => <><strong>{item.title || item.text}</strong><span>{item.publisher || item.publication || ''}</span></>],
    ['Languages', candidate.languages, item => <><strong>{item.language || item.name || item.text}</strong><span>{item.proficiency || item.level || ''}</span></>],
    ['Volunteering', candidate.volunteering, item => <><strong>{item.role || item.title || item.text}</strong><span>{item.organization || item.company || ''}</span></>],
  ]
  return <div className="drawer-backdrop" onMouseDown={e => { if (e.target === e.currentTarget) onClose() }}><aside className="candidate-drawer"><div className="drawer-top"><span className="section-label">TALENT PROFILE / #{candidate.id}</span><button className="icon-button" onClick={onClose}><X size={18}/></button></div><div className="drawer-profile-head"><div className="profile-avatar-large">{initials(candidate.full_name)}</div><div className="drawer-profile-info"><h2>{candidate.full_name}</h2><p>{candidate.headline || 'Professional headline not available'}</p><div><span><Mail size={13}/>{candidate.email || 'No email'}</span><span><MapPin size={13}/>{candidate.location || 'Location not listed'}</span></div></div></div>{(canManage || canReview) && <div className="drawer-actions">{canManage && <button className="button-secondary" onClick={() => setEditing(!editing)}><Pencil size={14}/>{editing ? 'Cancel editing' : 'Edit profile'}</button>}{canReview && <button className="button-primary" onClick={() => onApplication(candidate)}><Plus size={14}/> Add to role</button>}</div>}
    <div className="drawer-scroll">{editing ? <form className="edit-profile-form" onSubmit={save}><div className="section-label">PROFILE CORRECTION</div><Field label="Full name"><input name="full_name" value={form.full_name} onChange={update}/></Field><Field label="Email"><input name="email" value={form.email} onChange={update}/></Field><Field label="Phone"><input name="phone" value={form.phone} onChange={update}/></Field><Field label="Location"><input name="location" value={form.location} onChange={update}/></Field><Field label="Headline"><input name="headline" value={form.headline} onChange={update}/></Field><Field label="Experience (years)"><input type="number" min="0" max="60" step="0.5" name="total_experience_years" value={form.total_experience_years} onChange={update}/></Field><Field label="Summary"><textarea name="summary" rows="4" value={form.summary} onChange={update}/></Field><Field label="Technical skills"><input value={form.skills.join(', ')} onChange={e => setForm(value => ({ ...value, skills: commaList(e.target.value) }))}/></Field><Field label="Soft skills"><input value={form.soft_skills.join(', ')} onChange={e => setForm(value => ({ ...value, soft_skills: commaList(e.target.value) }))}/></Field><Field label="Tools & platforms"><input value={form.tools.join(', ')} onChange={e => setForm(value => ({ ...value, tools: commaList(e.target.value) }))}/></Field><details className="advanced-profile-editor"><summary>Structured sections · advanced correction</summary><p>Each section must be valid JSON. Use arrays for sections and an object for professional links.</p>{structuredKeys.map(key => <Field key={key} label={key.replaceAll('_', ' ')}><textarea rows={key === 'experience' || key === 'projects' ? 7 : 4} value={jsonFields[key]} onChange={event => setJsonFields(value => ({ ...value, [key]: event.target.value }))} spellCheck="false"/></Field>)}</details>{jsonError && <div className="inline-error">{jsonError}</div>}<button className="button-primary wide" disabled={saving}>{saving ? 'Saving...' : 'Save corrections'} <Check size={15}/></button></form> : <>
      <div className="profile-metrics"><div><strong>{candidate.total_experience_years ?? '—'}</strong><span>Years experience</span></div><div><strong>{candidate.skills?.length || 0}</strong><span>Technical skills</span></div><div><strong>{candidate.document_count ?? data.documents?.length ?? 0}</strong><span>Resume files</span></div></div>
      <div className="drawer-section"><div className="drawer-section-head"><h3>Extraction quality</h3><QualityPill quality={candidate.extraction_quality}/></div>{candidate.extraction_quality?.warnings?.length ? <ul className="warning-list">{candidate.extraction_quality.warnings.map(item => <li key={item}>{item}</li>)}</ul> : <p className="muted-copy">No parser warnings were recorded for the current profile.</p>}</div>
      {candidate.summary && <div className="drawer-section"><h3>Professional summary</h3><p>{candidate.summary}</p></div>}
      <div className="drawer-section"><h3>Technical skills</h3><div className="chip-list">{candidate.skills?.map(skill => <span className="skill-chip" key={skill}>{skill}</span>)}{!candidate.skills?.length && <span className="muted-copy">No skills extracted.</span>}</div></div>
      <div className="drawer-section"><h3>Soft skills</h3><div className="chip-list">{candidate.soft_skills?.map(skill => <span className="soft-chip" key={skill}>{skill}</span>)}{!candidate.soft_skills?.length && <span className="muted-copy">No soft skills found.</span>}</div></div>
      {sections.map(([title, items, render]) => <div className="drawer-section" key={title}><h3>{title}</h3>{items?.length ? items.map((item, index) => <div className="profile-entry" key={index}>{render(item)}</div>) : <span className="muted-copy">No {title.toLowerCase()} entries were detected.</span>}</div>)}
      <div className="drawer-section"><h3>Professional links</h3><div className="profile-links">{Object.entries(candidate.links || {}).map(([key, value]) => <a href={value.startsWith('http') ? value : `mailto:${value}`} target="_blank" rel="noreferrer" key={key}><Globe2 size={14}/>{key}<ExternalLink size={12}/></a>)}{!Object.keys(candidate.links || {}).length && <span className="muted-copy">No links found.</span>}</div></div>
      <div className="drawer-section"><h3>Source documents</h3>{data.documents?.length ? data.documents.map(doc => <div className="document-row" key={doc.id}><FileText size={16}/><div><strong>{doc.original_filename}</strong><span>{(doc.file_size / 1024).toFixed(0)} KB · {doc.page_count || 'DOCX'} pages</span></div><button type="button" className="document-download" onClick={() => downloadResume(doc)} aria-label={`Download ${doc.original_filename}`}><Download size={15}/></button></div>) : <span className="muted-copy">No document metadata loaded.</span>}</div>
      {data.field_evidence && <div className="drawer-section"><h3>Field evidence</h3><p className="muted-copy">Extracted values keep a source snippet and parser confidence where available.</p><div className="evidence-list">{Object.entries(data.field_evidence).filter(([, value]) => value).map(([key, value]) => <div key={key}><strong>{key.replaceAll('_', ' ')}</strong><span>{Math.round((value.confidence || 0) * 100)}% confidence</span><p>{value.snippet || 'No direct text snippet available.'}</p></div>)}</div></div>}
      </>}</div></aside></div>
}

function ApplicationDrawer({ item, interviews, onClose, onSave, onSchedule, onDelete, canEdit, canDelete }) {
  const [stage, setStage] = useState(item.stage)
  const [notes, setNotes] = useState(item.notes || '')
  const [saving, setSaving] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const submit = async () => { setSaving(true); try { await onSave(item.id, { stage, notes }) } finally { setSaving(false) } }
  const remove = async () => {
    const confirmed = window.confirm(`Delete the application for ${item.candidate_name}? Any interviews scheduled for this application will also be deleted. The candidate profile and resume will remain. This cannot be undone.`)
    if (!confirmed) return
    setDeleting(true)
    try { await onDelete(item.id) } finally { setDeleting(false) }
  }
  const currentStage = STAGES.find(stageItem => stageItem.id === item.stage)
  return <div className="drawer-backdrop" onMouseDown={e => { if (e.target === e.currentTarget) onClose() }}><aside className="candidate-drawer application-drawer"><div className="drawer-top"><span className="section-label">APPLICATION / #{item.id}</span><button className="icon-button" onClick={onClose}><X size={18}/></button></div><div className="drawer-profile-head"><div className="profile-avatar-large">{initials(item.candidate_name)}</div><div className="drawer-profile-info"><h2>{item.candidate_name}</h2><p>{item.candidate_headline || 'Candidate profile'}</p><div><span><BriefcaseBusiness size={13}/>{item.job_title}</span><span><Mail size={13}/>{item.candidate_email || 'No email'}</span></div></div></div><div className="drawer-scroll"><div className="drawer-section"><h3>Application stage</h3>{canEdit ? <div className="stage-choice-grid">{STAGES.map(stageItem => <button className={stage === stageItem.id ? 'active' : ''} onClick={() => setStage(stageItem.id)} key={stageItem.id}><i className={`stage-dot ${stageItem.color}`}/>{stageItem.label}</button>)}</div> : <span className="read-only-stage"><i className={`stage-dot ${currentStage?.color || 'steel'}`}/>{currentStage?.label || item.stage}</span>}</div><div className="drawer-section"><h3>Recruiter notes</h3><textarea className="drawer-notes" rows="7" value={notes} onChange={e => setNotes(e.target.value)} placeholder="No recruiter notes have been added." readOnly={!canEdit}/>{canEdit && <button className="button-primary wide" onClick={submit} disabled={saving}>{saving ? 'Saving...' : 'Save application'} <Check size={15}/></button>}</div><div className="drawer-section"><div className="drawer-section-head"><h3>Interviews</h3>{canEdit && <button className="text-action" onClick={onSchedule}><Plus size={14}/> Schedule</button>}</div>{interviews.length ? interviews.map(interview => <div className="profile-entry" key={interview.id}><strong>{interview.title}</strong><span>{fmtDate(interview.scheduled_at)} · {fmtTime(interview.scheduled_at)} · {interview.status}</span></div>) : <span className="muted-copy">No interviews scheduled for this application.</span>}</div><div className="drawer-section"><h3>Candidate skills</h3><div className="chip-list">{item.candidate_skills?.map(skill => <span className="skill-chip" key={skill}>{skill}</span>)}</div></div>{canDelete && <div className="drawer-section application-danger-zone"><div className="drawer-section-head"><h3>Danger zone</h3></div><p>Delete this application and its scheduled interviews. The candidate profile and resume will stay in your talent pool.</p><button type="button" className="button-secondary button-danger wide" onClick={remove} disabled={saving || deleting}><Trash2 size={15}/>{deleting ? 'Deleting...' : 'Delete application'}</button></div>}</div></aside></div>
}
export default App;