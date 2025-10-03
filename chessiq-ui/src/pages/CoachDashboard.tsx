import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../AuthContext'
import Navbar from '../components/navbar/Navbar'
import './coach-dashboard.css'

const demoStudents = [
  {
    id: 'stu-01',
    name: 'Ava Chen',
    rating: 1420,
    progressDelta: 35,
    focus: 'Endgame fundamentals',
    activity: 'Played 12 games this week',
  },
  {
    id: 'stu-02',
    name: 'Mateo Ruiz',
    rating: 1565,
    progressDelta: 18,
    focus: 'King safety and attack timing',
    activity: 'Completed 9 puzzle sets',
  },
  {
    id: 'stu-03',
    name: 'Priya Desai',
    rating: 1704,
    progressDelta: 22,
    focus: 'Advanced opening repertoire',
    activity: 'Analyzed 4 annotated games',
  },
  {
    id: 'stu-04',
    name: 'Liam O’Connor',
    rating: 1348,
    progressDelta: 12,
    focus: 'Tactical awareness',
    activity: 'Daily tactics streak: 19 days',
  },
]

function CoachDashboard() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [inviteEmail, setInviteEmail] = useState('')
  const [inviteLink, setInviteLink] = useState('')
  const [copied, setCopied] = useState(false)
  function scrollToInvite() {
    const el = document.getElementById('coach-invite')
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
  }

  function generateInviteLink() {
    const baseUrl = window.location.origin
    const token = crypto.randomUUID ? crypto.randomUUID() : Math.random().toString(36).slice(2)
    const params = new URLSearchParams()
    params.set('invite', token)
    if (inviteEmail.trim()) {
      params.set('email', inviteEmail.trim())
    }
    if (user?.email) {
      params.set('coach', String(user.email))
    }
    const link = `${baseUrl}/register?${params.toString()}`
    setInviteLink(link)
    setCopied(false)
  }

  async function copyInviteLink() {
    if (!inviteLink) return
    try {
      await navigator.clipboard.writeText(inviteLink)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      setCopied(false)
    }
  }

  function emailInviteLink() {
    const to = inviteEmail || ''
    const subject = encodeURIComponent('Your ChessIQ registration link')
    const body = encodeURIComponent(
      `Hi,

Here is your ChessIQ student registration link:
${inviteLink || '[Generate link first]'}

This will associate your account with my coaching roster.

— ${user?.username || 'Your coach'}`,
    )
    window.location.href = `mailto:${to}?subject=${subject}&body=${body}`
  }

  const metrics = useMemo(() => {
    const totalRating = demoStudents.reduce((sum, student) => sum + student.rating, 0)
    const totalProgress = demoStudents.reduce((sum, student) => sum + student.progressDelta, 0)
    const peakPerformer = demoStudents.reduce((prev, current) =>
      current.progressDelta > prev.progressDelta ? current : prev,
    )

    return {
      averageRating: Math.round(totalRating / demoStudents.length),
      totalProgress,
      peakPerformer,
    }
  }, [])

  useEffect(() => {
    if (!user) {
      navigate('/signin', { replace: true })
      return
    }
    if (!user.isCoach) {
      navigate('/dashboard', { replace: true })
    }
  }, [navigate, user])

  if (!user?.isCoach) return null

  return (
    <div className="coach-dashboard">
      <Navbar />
      <main className="coach-main">
        <section className="coach-hero">
          <div className="coach-hero-content">
            <p className="coach-pill">Coach Hub</p>
            <h1>Guide every move with confidence</h1>
            <p className="coach-lede">
              Monitor student momentum, plan bespoke training blocks, and celebrate progress
              across your roster.
            </p>
            <div className="coach-actions">
              <button type="button" className="btn-primary">
                Create training plan
              </button>
              <button type="button" className="btn-ghost" onClick={() => navigate('/dashboard')}>
                Back to player view
              </button>
              <button type="button" className="btn-ghost" onClick={scrollToInvite}>
                Invite students
              </button>
            </div>
          </div>
          <dl className="coach-hero-metrics">
            <div>
              <dt>Active students</dt>
              <dd>{demoStudents.length}</dd>
            </div>
            <div>
              <dt>Avg Rating</dt>
              <dd>{metrics.averageRating}</dd>
            </div>
            <div>
              <dt>Monthly delta</dt>
              <dd>+{metrics.totalProgress} pts</dd>
            </div>
          </dl>
        </section>

        <section className="coach-section coach-invite" id="coach-invite">
          <header className="coach-section-head">
            <div>
              <span className="coach-section-pill">Onboard</span>
              <h2>Invite new students</h2>
            </div>
          </header>
          <div className="coach-invite-row">
            <input
              type="email"
              placeholder="Student email (optional)"
              value={inviteEmail}
              onChange={(e) => setInviteEmail(e.target.value)}
              className="coach-invite-input"
            />
            <button type="button" className="btn-primary" onClick={generateInviteLink}>
              Generate link
            </button>
          </div>
          <div className="coach-invite-row">
            <input
              type="text"
              placeholder="Generated link will appear here"
              value={inviteLink}
              readOnly
              className="coach-invite-input"
            />
            <button
              type="button"
              className="btn-ghost"
              onClick={copyInviteLink}
              disabled={!inviteLink}
            >
              {copied ? 'Copied!' : 'Copy'}
            </button>
            <button
              type="button"
              className="btn-ghost"
              onClick={emailInviteLink}
              disabled={!inviteLink}
            >
              Email
            </button>
          </div>
        </section>

        <section className="coach-section">
          <header className="coach-section-head">
            <div>
              <span className="coach-section-pill">Student roster</span>
              <h2>Momentum snapshot</h2>
            </div>
            <button type="button" className="coach-link">
              View assignments →
            </button>
          </header>

          <div className="coach-grid">
            {demoStudents.map((student) => (
              <article className="coach-card" key={student.id}>
                <header className="coach-card-head">
                  <div className="coach-card-ident">
                    <div className="coach-card-meta">
                      <p className="coach-card-name">{student.name}</p>
                    </div>
                  </div>
                  <div className="coach-progress">
                    <span className="coach-progress-value">+{student.progressDelta}</span>
                    <span className="coach-progress-label">pts</span>
                  </div>
                </header>
                <dl className="coach-card-body">
                  <div>
                    <dt>Rating</dt>
                    <dd>{student.rating}</dd>
                  </div>
                  <div>
                    <dt>Latest activity</dt>
                    <dd>{student.activity}</dd>
                  </div>
                </dl>
                <footer className="coach-card-actions">
                  <button type="button" className="btn-primary">
                    Review plan
                  </button>
                  <button type="button" className="btn-ghost">
                    Send check-in
                  </button>
                </footer>
              </article>
            ))}
          </div>
        </section>

        <section className="coach-highlight">
          <div className="coach-highlight-body">
            <div className="coach-highlight-meta">
              <span className="coach-section-pill">Spotlight</span>
              <p className="coach-highlight-title">{metrics.peakPerformer.name} is leading the charge</p>
            </div>
            <p className="coach-highlight-text">
              Continuous endgame study and a disciplined tactics habit have driven a +
              {metrics.peakPerformer.progressDelta} rating boost this month. Consider pairing them
              with a higher-rated sparring partner to sustain momentum.
            </p>
            <button type="button" className="btn-ghost">
              View player dossier
            </button>
          </div>
        </section>
      </main>
    </div>
  )
}

export default CoachDashboard
