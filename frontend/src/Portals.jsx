import React, { useEffect, useMemo, useState } from 'react'
import {
  Activity, ArrowRight, ArrowUpRight, BriefcaseBusiness, CalendarClock, Check,
  ChevronRight, Download, FileText, Globe2, LockKeyhole, LogOut, Search,
  ShieldCheck, Sparkles, Target, UploadCloud, UserRound, Users, X
} from 'lucide-react'

async function request(path, options = {}) {
  const headers = new Headers(options.headers || {})
  const token = localStorage.getItem('resumeiq_access_token')
  if (token && !headers.has('Authorization')) headers.set('Authorization', `Bearer ${token}`)
  if (options.body && !(options.body instanceof FormData) && !headers.has('Content-Type')) headers.set('Content-Type', 'application/json')
  const response = await fetch(path, { ...options, headers })
  const type = response.headers.get('content-type') || ''
  const payload = type.includes('application/json') ? await response.json() : await response.text()
  if (!response.ok) throw new Error(payload?.detail || payload?.message || `Request failed (${response.status})`)
  return payload
}

const json = (method, data) => ({ method, body: JSON.stringify(data) })
const dateLabel = value => value ? new Date(value).toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: 'numeric' }) : 'To be confirmed'
const initials = value => (value || 'R').split(/\\s+/).slice(0, 2).map(part => part[0]).join('').toUpperCase()

function Brand({ light = false }) {
  return <div className={`portal-brand ${light ? 'portal-brand-light' : ''}`}>
    <div className="portal-brand-mark">R</div>
    <div><div className="portal-brand-name">resume<span>iq</span></div><div className="portal-brand-caption">TALENT INTELLIGENCE</div></div>
  </div>
}

function PortalHeader({ user, onLogin, onLogout, publicMode = false }) {
  return <header className="portal-header">
    <Brand/>
    <div className="portal-header-actions">
      {publicMode
        ? <button className="portal-button portal-button-secondary" onClick={onLogin}>Sign in <ArrowRight size={15}/></button>
        : <><span className="portal-user-chip"><span className="portal-user-avatar">{initials(user?.display_name)}</span>{user?.display_name || user?.email}</span><button className="portal-icon-button" title="Sign out" onClick={onLogout}><LogOut size={16}/></button></>}
    </div>
  </header>
}

function AuthPanel({ mode, setMode, onLogin, onRegister, onClose }) {
  const [form, setForm] = useState({ name: '', email: '', password: '' })
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const isRegister = mode === 'register'
  const submit = async event => {
    event.preventDefault()
    setError('')
    setBusy(true)
    try {
      if (isRegister) await onRegister(form.name, form.email, form.password)
      else await onLogin(form.email, form.password)
    } catch (err) {
      setError(err.message || 'Could not complete this request.')
    } finally {
      setBusy(false)
    }
  }
  return <div className="portal-modal-backdrop" onMouseDown={event => { if (event.target === event.currentTarget) onClose() }}>
    <section className="portal-auth-card">
      <button className="portal-modal-close" onClick={onClose} aria-label="Close"><X size={18}/></button>
      <div className="portal-auth-kicker">{isRegister ? 'CANDIDATE REGISTRATION' : 'WORKSPACE ACCESS'}</div>
      <h2>{isRegister ? 'Build your next opportunity.' : 'Welcome back.'}</h2>
      <p>{isRegister ? 'Create a candidate account to manage your profile, upload resumes and apply for roles.' : 'Sign in to continue to your ResumeIQ workspace.'}</p>
      <form onSubmit={submit} className="portal-form">
        {isRegister && <label>Full name<input required minLength={2} value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} placeholder="Your full name"/></label>}
        <label>Email address<input required type="email" value={form.email} onChange={e => setForm({ ...form, email: e.target.value })} placeholder="you@example.com"/></label>
        <label>Password<input required type="password" minLength={isRegister ? 12 : 1} value={form.password} onChange={e => setForm({ ...form, password: e.target.value })} placeholder={isRegister ? 'At least 12 characters' : 'Your password'}/></label>
        {error && <div className="portal-form-error">{error}</div>}
        <button className="portal-button portal-button-primary portal-button-full" disabled={busy}>{busy ? 'Please wait…' : isRegister ? 'Create candidate account' : 'Sign in'} <ArrowRight size={16}/></button>
      </form>
      <div className="portal-auth-switch">{isRegister ? 'Already registered?' : 'New to ResumeIQ?'} <button onClick={() => { setError(''); setMode(isRegister ? 'login' : 'register') }}>{isRegister ? 'Sign in' : 'Create a candidate account'}</button></div>
      <div className="portal-auth-foot"><LockKeyhole size={13}/> Candidate accounts can only access their own profile, resumes and applications.</div>
    </section>
  </div>
}

function PublicPortal({ onLogin, onRegister }) {
  const [data, setData] = useState({ dashboard: null, roles: [], candidates: [], insights: null })
  const [tab, setTab] = useState('overview')
  const [search, setSearch] = useState('')
  const [authMode, setAuthMode] = useState(null)
  const [selectedRole, setSelectedRole] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let alive = true
    Promise.all([
      request('/api/public/dashboard'),
      request('/api/public/roles'),
      request('/api/public/candidates'),
      request('/api/public/insights')
    ]).then(([dashboard, roles, candidates, insights]) => {
      if (alive) setData({ dashboard, roles, candidates, insights })
    }).catch(err => { if (alive) setError(err.message || 'The public workspace could not be loaded.') })
      .finally(() => { if (alive) setLoading(false) })
    return () => { alive = false }
  }, [])

  const roles = useMemo(() => data.roles.filter(role => !search || [role.title, role.department, role.location, ...(role.required_skills || [])].join(' ').toLowerCase().includes(search.toLowerCase())), [data.roles, search])
  const candidates = useMemo(() => data.candidates.filter(candidate => !search || [candidate.display_name, candidate.headline, candidate.location, ...(candidate.skills || [])].join(' ').toLowerCase().includes(search.toLowerCase())), [data.candidates, search])
  const showLogin = () => setAuthMode('login')
  return <div className="portal-shell">
    <PortalHeader publicMode onLogin={showLogin}/>
    <main className="portal-main">
      <section className="portal-hero">
        <div className="portal-eyebrow"><span/> RECRUITMENT, WITH MORE SIGNAL</div>
        <div className="portal-hero-grid">
          <div><h1>Talent deserves<br/><em>a clearer picture.</em></h1><p>Explore published opportunities, discover opted-in professional profiles and understand recruitment activity through one transparent workspace.</p>
            <div className="portal-hero-actions"><button className="portal-button portal-button-primary" onClick={() => { setTab('roles'); document.getElementById('portal-content')?.scrollIntoView({ behavior: 'smooth' }) }}>Explore open roles <ArrowUpRight size={16}/></button><button className="portal-button portal-button-secondary" onClick={() => setAuthMode('register')}>Create your profile <UserRound size={16}/></button></div>
          </div>
          <div className="portal-hero-aside"><div className="portal-orbit"><div className="portal-orbit-core"><Target size={30}/></div><span className="portal-orbit-node node-a"><Users size={17}/></span><span className="portal-orbit-node node-b"><BriefcaseBusiness size={17}/></span><span className="portal-orbit-node node-c"><Activity size={17}/></span></div><div className="portal-orbit-caption">PEOPLE · OPPORTUNITY · INSIGHT</div></div>
        </div>
      </section>
      <section className="portal-stat-grid">
        <div className="portal-stat"><span>PUBLIC PROFILES</span><strong>{data.dashboard?.public_candidate_profiles ?? '—'}</strong><small>Professionals who opted in</small></div>
        <div className="portal-stat"><span>OPEN ROLES</span><strong>{data.dashboard?.open_roles ?? '—'}</strong><small>Currently accepting applications</small></div>
        <div className="portal-stat"><span>APPLICATIONS</span><strong>{data.dashboard?.applications_total ?? '—'}</strong><small>Aggregate platform activity</small></div>
        <div className="portal-stat"><span>SCHEDULED INTERVIEWS</span><strong>{data.dashboard?.scheduled_interviews ?? '—'}</strong><small>Private meeting details excluded</small></div>
      </section>
      <section className="portal-content" id="portal-content">
        <div className="portal-content-heading"><div><div className="portal-eyebrow">EXPLORE RESUMEIQ</div><h2>One workspace. Different perspectives.</h2></div><div className="portal-search"><Search size={16}/><input value={search} onChange={e => setSearch(e.target.value)} placeholder={tab === 'candidates' ? 'Search public profiles' : 'Search roles and skills'}/></div></div>
        <nav className="portal-tabs">
          {[['overview','Overview'],['roles','Open roles'],['candidates','Talent directory'],['insights','Recruitment insights']].map(([key,label]) => <button key={key} className={tab === key ? 'active' : ''} onClick={() => setTab(key)}>{label}</button>)}
        </nav>
        {loading ? <div className="portal-empty">Loading the public workspace…</div> : error ? <div className="portal-empty portal-error">{error}</div> : <>
          {tab === 'overview' && <div className="portal-overview-grid">
            <article className="portal-feature-card"><div className="portal-card-label">OPPORTUNITIES</div><h3>Find work that<br/>moves you forward.</h3><p>Browse open roles, review expectations and apply with a candidate profile of your own.</p><button className="portal-text-action" onClick={() => setTab('roles')}>View published roles <ArrowRight size={15}/></button></article>
            <article className="portal-feature-card portal-feature-muted"><div className="portal-card-label">TALENT DIRECTORY</div><h3>Professional profiles,<br/>shared by choice.</h3><p>Explore profiles that candidates have explicitly chosen to make public. Contact details and original resumes stay private.</p><button className="portal-text-action" onClick={() => setTab('candidates')}>Explore public profiles <ArrowRight size={15}/></button></article>
            <article className="portal-feature-card portal-feature-wide"><div className="portal-card-label">WORKSPACE ACCESS</div><h3>Your profile. Your documents. Your control.</h3><p>Create a free candidate account to upload and update resumes, manage your profile, apply for opportunities and track interview invitations.</p><button className="portal-text-action" onClick={() => setAuthMode('register')}>Create a candidate account <ArrowRight size={15}/></button></article>
          </div>}
          {tab === 'roles' && <div className="portal-role-grid">{roles.map(role => <article className="portal-role-card" key={role.id}><div className="portal-role-top"><span>{role.department || 'Opportunity'}</span><span className="portal-open-tag">OPEN</span></div><h3>{role.title}</h3><div className="portal-role-meta">{role.location} · {role.work_mode} · {role.employment_type}</div><p>{(role.description || '').slice(0, 230)}{role.description?.length > 230 ? '…' : ''}</p><div className="portal-tags">{(role.required_skills || []).slice(0, 5).map(skill => <span key={skill}>{skill}</span>)}</div><div className="portal-role-bottom"><button className="portal-text-action" onClick={() => setSelectedRole(role)}>View role <ArrowRight size={15}/></button><button className="portal-button portal-button-small" onClick={() => setAuthMode('register')}>Apply <ArrowUpRight size={14}/></button></div></article>)}
            {!roles.length && <div className="portal-empty">No published roles match that search.</div>}</div>}
          {tab === 'candidates' && <div className="portal-candidate-grid">{candidates.map(candidate => <article className="portal-candidate-card" key={candidate.id}><div className="portal-candidate-avatar">{initials(candidate.display_name)}</div><div className="portal-candidate-name">{candidate.display_name}</div><div className="portal-candidate-headline">{candidate.headline || 'Professional profile'}</div><div className="portal-candidate-meta">{candidate.location || 'Location not shared'}{candidate.total_experience_years != null ? ` · ${candidate.total_experience_years} years experience` : ''}</div><p>{candidate.summary || 'This candidate has shared selected profile information with the public directory.'}</p><div className="portal-tags">{(candidate.skills || []).slice(0, 6).map(skill => <span key={skill}>{skill}</span>)}</div><div className="portal-private-note"><ShieldCheck size={13}/> Contact details and original resumes are private.</div></article>)}{!candidates.length && <div className="portal-empty">No public profiles are available yet. Candidates control whether their profiles appear here.</div>}</div>}
          {tab === 'insights' && <div className="portal-insight-grid"><article className="portal-insight-card"><div className="portal-card-label">APPLICATION PIPELINE</div>{Object.entries(data.dashboard?.pipeline || {}).map(([stage,count]) => <div className="portal-insight-row" key={stage}><span>{stage.replace(/_/g,' ')}</span><strong>{count}</strong></div>)}</article><article className="portal-insight-card"><div className="portal-card-label">INTERVIEW ACTIVITY</div>{(data.insights?.interview_types || []).map(item => <div className="portal-insight-row" key={item.type}><span>{item.type}</span><strong>{item.count}</strong></div>)}{!(data.insights?.interview_types || []).length && <p>No interview activity to display.</p>}</article><article className="portal-insight-card"><div className="portal-card-label">ROLE STATUS</div>{(data.insights?.role_statuses || []).map(item => <div className="portal-insight-row" key={item.status}><span>{item.status}</span><strong>{item.count}</strong></div>)}</article><div className="portal-privacy-note"><ShieldCheck size={17}/> Recruitment insights are aggregated. Candidate identities, interview links, private feedback and recruiter notes are never published here.</div></div>}
        </>}
      </section>
      <footer className="portal-footer"><Brand/><span>Public information is shown only where permitted. Candidate resumes and private recruitment records remain protected.</span></footer>
    </main>
    {selectedRole && <div className="portal-modal-backdrop" onMouseDown={event => { if (event.target === event.currentTarget) setSelectedRole(null) }}><section className="portal-detail-card"><button className="portal-modal-close" onClick={() => setSelectedRole(null)}><X size={18}/></button><div className="portal-eyebrow">PUBLISHED OPPORTUNITY</div><h2>{selectedRole.title}</h2><div className="portal-role-meta">{selectedRole.department} · {selectedRole.location} · {selectedRole.employment_type}</div><h3>Role overview</h3><p>{selectedRole.description}</p><h3>Responsibilities</h3><ul>{(selectedRole.responsibilities || []).map((item,index) => <li key={index}>{item}</li>)}</ul><h3>Required skills</h3><div className="portal-tags">{(selectedRole.required_skills || []).map(skill => <span key={skill}>{skill}</span>)}</div><button className="portal-button portal-button-primary portal-button-full" onClick={() => { setSelectedRole(null); setAuthMode('register') }}>Create an account to apply <ArrowRight size={16}/></button></section></div>}
    {authMode && <AuthPanel mode={authMode} setMode={setAuthMode} onLogin={onLogin} onRegister={onRegister} onClose={() => setAuthMode(null)}/>}
  </div>
}

function CandidatePortal({ user, onLogout }) {
  const [profile, setProfile] = useState(null)
  const [applications, setApplications] = useState([])
  const [interviews, setInterviews] = useState([])
  const [roles, setRoles] = useState([])
  const [tab, setTab] = useState('overview')
  const [busy, setBusy] = useState(false)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const [edit, setEdit] = useState({ full_name:'', phone:'', location:'', headline:'', summary:'', total_experience_years:'', skills:'', experience:'[]', education:'[]', projects:'[]', certifications:'[]', achievements:'[]', publications:'[]', languages:'[]', volunteering:'[]', links:'{}' })
  const [publicName, setPublicName] = useState('')

  const load = async () => {
    const [me, apps, events, openRoles] = await Promise.all([
      request('/api/candidate/me'), request('/api/candidate/me/applications'),
      request('/api/candidate/me/interviews'), request('/api/public/roles')
    ])
    setProfile(me)
    setApplications(apps)
    setInterviews(events)
    setRoles(openRoles)
    setPublicName(me.public_profile?.display_name || '')
    const person = me.candidate
    setEdit({
      full_name: person.full_name || '', phone: person.phone || '', location: person.location || '',
      headline: person.headline || '', summary: person.summary || '',
      total_experience_years: person.total_experience_years ?? '',
      skills: (person.skills || []).join(', '),
      experience: JSON.stringify(person.experience || [], null, 2),
      education: JSON.stringify(person.education || [], null, 2),
      projects: JSON.stringify(person.projects || [], null, 2),
      certifications: JSON.stringify(person.certifications || [], null, 2),
      achievements: JSON.stringify(person.achievements || [], null, 2),
      publications: JSON.stringify(person.publications || [], null, 2),
      languages: JSON.stringify(person.languages || [], null, 2),
      volunteering: JSON.stringify(person.volunteering || [], null, 2),
      links: JSON.stringify(person.links || {}, null, 2)
    })
  }
  useEffect(() => { load().catch(err => setError(err.message || 'Could not load your candidate workspace.')) }, [])

  const saveProfile = async event => {
    event.preventDefault()
    setBusy(true); setMessage(''); setError('')
    try {
      const parseArray = field => { const value = JSON.parse(edit[field] || '[]'); if (!Array.isArray(value)) throw new Error(`${field} must be a JSON array.`); return value }
      const links = JSON.parse(edit.links || '{}')
      if (!links || Array.isArray(links) || typeof links !== 'object') throw new Error('Links must be a JSON object.')
      const payload = {
        full_name: edit.full_name, phone: edit.phone, location: edit.location,
        headline: edit.headline, summary: edit.summary,
        total_experience_years: edit.total_experience_years === '' ? null : Number(edit.total_experience_years),
        skills: edit.skills.split(',').map(value => value.trim()).filter(Boolean), links,
        experience: parseArray('experience'), education: parseArray('education'), projects: parseArray('projects'),
        certifications: parseArray('certifications'), achievements: parseArray('achievements'),
        publications: parseArray('publications'), languages: parseArray('languages'), volunteering: parseArray('volunteering')
      }
      await request('/api/candidate/me', json('PATCH', payload))
      await load()
      setMessage('Profile updated.')
    } catch (err) { setError(err.message || 'Could not save your profile.') }
    finally { setBusy(false) }
  }
  const upload = async event => {
    const file = event.target.files?.[0]
    event.target.value = ''
    if (!file) return
    const body = new FormData(); body.append('file', file)
    setBusy(true); setMessage(''); setError('')
    try { await request('/api/candidate/me/resumes', { method:'POST', body }); await load(); setMessage('Resume uploaded and parsed.') }
    catch (err) { setError(err.message || 'Resume upload failed.') }
    finally { setBusy(false) }
  }
  const removeResume = async id => {
    if (!window.confirm('Delete this resume from your profile?')) return
    try { await request(`/api/candidate/me/resumes/${id}`, { method:'DELETE' }); await load(); setMessage('Resume deleted.') }
    catch (err) { setError(err.message || 'Could not delete this resume.') }
  }
  const apply = async id => {
    try { await request(`/api/candidate/me/applications?job_id=${id}`, { method:'POST' }); await load(); setMessage('Application submitted.') }
    catch (err) { setError(err.message || 'Could not submit your application.') }
  }
  const download = async doc => {
    try {
      const response = await fetch(`/api/candidate/me/resumes/${doc.id}/download`, { headers: { Authorization: `Bearer ${localStorage.getItem('resumeiq_access_token')}` } })
      if (!response.ok) throw new Error('Resume download failed.')
      const blob = await response.blob(); const href = URL.createObjectURL(blob)
      const link = document.createElement('a'); link.href = href; link.download = doc.original_filename; link.click(); URL.revokeObjectURL(href)
    } catch (err) { setError(err.message) }
  }
  const togglePublic = async enabled => {
    try { await request('/api/candidate/me/public-profile', json('PATCH', { enabled, display_name: publicName })); await load(); setMessage(enabled ? 'Your selected profile details are now public.' : 'Your public profile has been hidden.') }
    catch (err) { setError(err.message || 'Could not update profile visibility.') }
  }
  const person = profile?.candidate
  const docs = profile?.documents || []
  return <div className="portal-shell portal-candidate-shell">
    <PortalHeader user={user} onLogout={onLogout}/>
    <main className="portal-main portal-candidate-main">
      <section className="portal-candidate-welcome"><div><div className="portal-eyebrow">CANDIDATE WORKSPACE</div><h1>Your next move,<br/><em>on your terms.</em></h1><p>Manage your professional profile, keep your resume current and follow every application in one place.</p></div><div className="portal-candidate-welcome-mark"><UserRound size={54}/></div></section>
      {(message || error) && <div className={`portal-alert ${error ? 'is-error' : ''}`}>{error || message}<button onClick={() => { setMessage(''); setError('') }}><X size={14}/></button></div>}
      <section className="portal-stat-grid portal-candidate-stats"><div className="portal-stat"><span>RESUME VERSIONS</span><strong>{docs.length}</strong><small>Your uploaded documents</small></div><div className="portal-stat"><span>APPLICATIONS</span><strong>{applications.length}</strong><small>Roles you've applied to</small></div><div className="portal-stat"><span>INTERVIEWS</span><strong>{interviews.length}</strong><small>Your scheduled conversations</small></div><div className="portal-stat"><span>PROFILE STATUS</span><strong className="portal-stat-word">{person ? 'Active' : '—'}</strong><small>Editable any time</small></div></section>
      <nav className="portal-tabs portal-candidate-tabs">{[['overview','Overview'],['profile','Edit profile'],['resumes','My resumes'],['applications','Applications'],['interviews','Interviews'],['roles','Browse roles']].map(([key,label]) => <button key={key} className={tab===key?'active':''} onClick={() => setTab(key)}>{label}</button>)}</nav>
      {!profile && !error && <div className="portal-empty">Loading your candidate workspace…</div>}
      {person && tab === 'overview' && <div className="portal-overview-grid">
        <article className="portal-feature-card"><div className="portal-card-label">PROFILE COMPLETENESS</div><h3>{person.full_name || 'Your profile'}</h3><p>{person.headline || 'Add a professional headline so recruiters can understand your direction.'}</p><button className="portal-text-action" onClick={() => setTab('profile')}>Edit your profile <ArrowRight size={15}/></button></article>
        <article className="portal-feature-card portal-feature-muted"><div className="portal-card-label">RESUME LIBRARY</div><h3>{docs.length ? `${docs.length} resume ${docs.length === 1 ? 'version' : 'versions'} saved` : 'Add your first resume.'}</h3><p>PDF and DOCX files are parsed into editable profile fields. Your original files are private to you and authorized recruitment staff.</p><button className="portal-text-action" onClick={() => setTab('resumes')}>Manage resumes <ArrowRight size={15}/></button></article>
        <article className="portal-feature-card portal-feature-wide"><div className="portal-card-label">PUBLIC PROFILE CONTROL</div><h3>Choose what the public can see.</h3><p>Only the profile fields you approve can appear in the public talent directory. Contact information and original resume files remain private.</p><label className="portal-switch-row"><span>Show my selected profile in the public directory</span><input type="checkbox" checked={!!profile.public_profile?.enabled} onChange={e => togglePublic(e.target.checked)}/></label>{profile.public_profile?.enabled && <input className="portal-public-name" value={publicName} onChange={e => setPublicName(e.target.value)} placeholder="Public display name (optional)"/>}{profile.public_profile?.enabled && <button className="portal-text-action" onClick={() => togglePublic(true)}>Save public display name <Check size={14}/></button>}</article>
      </div>}
      {person && tab === 'profile' && <form className="portal-edit-form" onSubmit={saveProfile}><div className="portal-section-title"><h2>Your professional profile</h2><p>Keep your details accurate. Changes are visible to authorized recruitment staff.</p></div><div className="portal-form-grid">
        <label>Full name<input value={edit.full_name} onChange={e=>setEdit({...edit,full_name:e.target.value})}/></label><label>Phone<input value={edit.phone} onChange={e=>setEdit({...edit,phone:e.target.value})} placeholder="Optional"/></label><label>Location<input value={edit.location} onChange={e=>setEdit({...edit,location:e.target.value})}/></label><label>Professional headline<input value={edit.headline} onChange={e=>setEdit({...edit,headline:e.target.value})}/></label><label>Years of experience<input type="number" min="0" max="60" step="0.1" value={edit.total_experience_years} onChange={e=>setEdit({...edit,total_experience_years:e.target.value})}/></label><label>Skills, comma separated<input value={edit.skills} onChange={e=>setEdit({...edit,skills:e.target.value})} placeholder="Python, SQL, React"/></label><label className="portal-form-full">Professional summary<textarea rows="5" value={edit.summary} onChange={e=>setEdit({...edit,summary:e.target.value})}/></label>
        {['experience','education','projects','certifications','achievements','publications','languages','volunteering'].map(field=><label className="portal-form-full" key={field}>{field.charAt(0).toUpperCase()+field.slice(1)} · JSON array<textarea rows="5" spellCheck="false" value={edit[field]} onChange={e=>setEdit({...edit,[field]:e.target.value})}/></label>)}
        <label className="portal-form-full">Links · JSON object<textarea rows="3" spellCheck="false" value={edit.links} onChange={e=>setEdit({...edit,links:e.target.value})}/></label>
      </div><button className="portal-button portal-button-primary" disabled={busy}>Save profile <Check size={16}/></button></form>}
      {person && tab === 'resumes' && <section className="portal-data-section"><div className="portal-section-title"><h2>Your resumes</h2><p>Upload PDF or DOCX files. You can replace or delete versions at any time.</p></div><label className="portal-upload-zone"><UploadCloud size={23}/><strong>Upload a resume</strong><span>PDF or DOCX · Up to 15 MB</span><input type="file" accept=".pdf,.docx" onChange={upload} disabled={busy}/></label><div className="portal-document-list">{docs.map(doc=><article className="portal-document-row" key={doc.id}><FileText size={19}/><div><strong>{doc.original_filename}</strong><span>{Math.round(doc.file_size/1024)} KB · {doc.page_count} pages · Added {dateLabel(doc.created_at)}</span></div><button className="portal-icon-button" title="Download" onClick={()=>download(doc)}><Download size={15}/></button><button className="portal-icon-button portal-danger-icon" title="Delete" onClick={()=>removeResume(doc.id)}><X size={15}/></button></article>)}{!docs.length && <div className="portal-empty">You haven't uploaded a resume yet.</div>}</div></section>}
      {person && tab === 'applications' && <section className="portal-data-section"><div className="portal-section-title"><h2>Application activity</h2><p>Track the progress of every role you've applied for.</p></div><div className="portal-document-list">{applications.map(item=><article className="portal-application-row" key={item.id}><div><strong>{item.job_title}</strong><span>{item.department} · {item.location} · Applied {dateLabel(item.created_at)}</span></div><span className={`portal-stage stage-${item.stage}`}>{item.stage}</span></article>)}{!applications.length && <div className="portal-empty">No applications yet. Browse open roles to get started.</div>}</div></section>}
      {person && tab === 'interviews' && <section className="portal-data-section"><div className="portal-section-title"><h2>Your interviews</h2><p>Interview invitations and attendance details are private to your account.</p></div><div className="portal-document-list">{interviews.map(item=><article className="portal-interview-row" key={item.id}><div className="portal-interview-date"><strong>{new Date(item.scheduled_at).getDate()}</strong><span>{new Date(item.scheduled_at).toLocaleDateString(undefined,{month:'short'})}</span></div><div><strong>{item.title}</strong><span>{item.job_title} · {item.interview_type} · {item.duration_minutes} min</span>{item.location_or_link && <a href={item.location_or_link} target="_blank" rel="noreferrer">Join / location details <ArrowUpRight size={13}/></a>}</div><span className={`portal-stage stage-${item.status}`}>{item.status}</span></article>)}{!interviews.length && <div className="portal-empty">No interviews scheduled yet.</div>}</div></section>}
      {person && tab === 'roles' && <div className="portal-role-grid">{roles.map(role=><article className="portal-role-card" key={role.id}><div className="portal-role-top"><span>{role.department}</span><span className="portal-open-tag">OPEN</span></div><h3>{role.title}</h3><div className="portal-role-meta">{role.location} · {role.work_mode}</div><p>{role.description.slice(0,190)}…</p><div className="portal-tags">{(role.required_skills||[]).slice(0,5).map(skill=><span key={skill}>{skill}</span>)}</div><button className="portal-button portal-button-small" onClick={()=>apply(role.id)} disabled={applications.some(item=>item.job_id===role.id)}> {applications.some(item=>item.job_id===role.id) ? 'Already applied' : 'Apply for this role'} <ArrowRight size={14}/></button></article>)}{!roles.length && <div className="portal-empty">No roles are currently open.</div>}</div>}
      <footer className="portal-footer"><Brand/><span>Signed in as {user.email}. You control your candidate profile and documents.</span></footer>
    </main>
  </div>
}

function InterviewerPortal({ user, onLogout }) {
  const [items, setItems] = useState([])
  const [selected, setSelected] = useState(null)
  const [review, setReview] = useState({ status:'scheduled', notes:'', scorecard:{} })
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const load = async () => setItems(await request('/api/interviewer/me/interviews'))
  useEffect(() => { load().catch(err=>setError(err.message || 'Could not load assigned interviews.')) }, [])
  const open = async id => {
    try {
      const data = await request(`/api/interviewer/me/interviews/${id}`)
      setSelected(data)
      setReview({ status:data.interview.status, notes:data.interview.notes || '', scorecard:data.interview.scorecard || {} })
    } catch(err) { setError(err.message) }
  }
  const downloadResume = async (interviewId, doc) => {
    try {
      const response = await fetch(`/api/interviewer/me/interviews/${interviewId}/resumes/${doc.id}/download`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('resumeiq_access_token')}` }
      })
      if (!response.ok) throw new Error('Resume download failed.')
      const blob = await response.blob()
      const href = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = href
      link.download = doc.original_filename
      link.click()
      URL.revokeObjectURL(href)
    } catch (err) { setError(err.message || 'Could not download the resume.') }
  }
  const save = async () => {
    setBusy(true); setError('')
    try {
      await request(`/api/interviewer/me/interviews/${selected.interview.id}`, json('PATCH', review))
      await load()
      const data = await request(`/api/interviewer/me/interviews/${selected.interview.id}`)
      setSelected(data)
    } catch(err) { setError(err.message || 'Could not save interview feedback.') }
    finally { setBusy(false) }
  }
  return <div className="portal-shell">
    <PortalHeader user={user} onLogout={onLogout}/>
    <main className="portal-main portal-candidate-main">
      <section className="portal-candidate-welcome"><div><div className="portal-eyebrow">INTERVIEWER WORKSPACE</div><h1>Conversations<br/><em>with context.</em></h1><p>Review only the interviews assigned to your account, inspect candidate evidence and submit structured feedback.</p></div><div className="portal-candidate-welcome-mark"><CalendarClock size={54}/></div></section>
      {error && <div className="portal-alert is-error">{error}</div>}
      {!selected ? <section className="portal-data-section"><div className="portal-section-title"><h2>Assigned interviews</h2><p>Interviews are visible only when your email or display name is assigned by the recruitment team.</p></div><div className="portal-document-list">{items.map(item=><article className="portal-interview-row" key={item.id}><div className="portal-interview-date"><strong>{new Date(item.scheduled_at).getDate()}</strong><span>{new Date(item.scheduled_at).toLocaleDateString(undefined,{month:'short'})}</span></div><div><strong>{item.candidate_name}</strong><span>{item.title} · {item.job_title} · {item.interview_type}</span><span>{dateLabel(item.scheduled_at)} · {item.duration_minutes} minutes</span></div><button className="portal-text-action" onClick={()=>open(item.id)}>Review <ArrowRight size={14}/></button></article>)}{!items.length && <div className="portal-empty">No interviews have been assigned to you yet.</div>}</div></section> : <section className="portal-data-section"><button className="portal-text-action" onClick={()=>setSelected(null)}>← Back to interviews</button><div className="portal-section-title"><h2>{selected.candidate.full_name}</h2><p>{selected.candidate.headline || 'Candidate'} · {selected.interview.job_title} · {selected.interview.title}</p></div><div className="portal-profile-summary"><p>{selected.candidate.summary}</p><div className="portal-tags">{(selected.candidate.skills||[]).map(skill=><span key={skill}>{skill}</span>)}</div><strong>Resume documents</strong>{selected.documents.map(doc=><span key={doc.id} className="portal-interviewer-document">{doc.original_filename} · {doc.page_count} pages <button className="portal-text-action" onClick={()=>downloadResume(selected.interview.id,doc)}>Download <Download size={13}/></button></span>)}</div><div className="portal-form-grid"><label>Interview status<select value={review.status} onChange={e=>setReview({...review,status:e.target.value})}><option value="scheduled">Scheduled</option><option value="completed">Completed</option><option value="rescheduled">Rescheduled</option><option value="cancelled">Cancelled</option></select></label><label>Overall recommendation<select value={review.scorecard.recommendation || ''} onChange={e=>setReview({...review,scorecard:{...review.scorecard,recommendation:e.target.value}})}><option value="">Not evaluated</option><option value="strong_yes">Strong yes</option><option value="yes">Yes</option><option value="mixed">Mixed</option><option value="no">No</option></select></label><label className="portal-form-full">Technical assessment<textarea rows="3" value={review.scorecard.technical || ''} onChange={e=>setReview({...review,scorecard:{...review.scorecard,technical:e.target.value}})}/></label><label className="portal-form-full">Communication and collaboration<textarea rows="3" value={review.scorecard.communication || ''} onChange={e=>setReview({...review,scorecard:{...review.scorecard,communication:e.target.value}})}/></label><label className="portal-form-full">Private interviewer feedback<textarea rows="5" value={review.notes} onChange={e=>setReview({...review,notes:e.target.value})}/></label></div><button className="portal-button portal-button-primary" disabled={busy} onClick={save}>Save interview feedback <Check size={16}/></button></section>}
      <footer className="portal-footer"><Brand/><span>Assigned interview access · Internal feedback remains private to the recruitment team.</span></footer>
    </main>
  </div>
}

export { PublicPortal, CandidatePortal, InterviewerPortal }
