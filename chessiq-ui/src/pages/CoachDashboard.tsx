import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../AuthContext'
import Navbar from '../components/Navbar'
import './coach-dashboard.css'

const demoStudents = [
  {
    id: 'stu-01',
    name: 'Ava Chen',
    rating: 1420,
    progress: '+35 this month',
    focus: 'Endgame fundamentals',
    activity: 'Played 12 games this week',
  },
  {
    id: 'stu-02',
    name: 'Mateo Ruiz',
    rating: 1565,
    progress: '+18 this month',
    focus: 'King safety and attack timing',
    activity: 'Completed 9 puzzle sets',
  },
  {
    id: 'stu-03',
    name: 'Priya Desai',
    rating: 1704,
    progress: '+22 this month',
    focus: 'Advanced opening repertoire',
    activity: 'Analyzed 4 annotated games',
  },
  {
    id: 'stu-04',
    name: 'Liam O’Connor',
    rating: 1348,
    progress: '+12 this month',
    focus: 'Tactical awareness',
    activity: 'Daily tactics streak: 19 days',
  },
]

function CoachDashboard() {
  const { user, coachEmail } = useAuth()
  const navigate = useNavigate()

  useEffect(() => {
    if (!user) {
      navigate('/signin', { replace: true })
      return
    }
    if (!user.isCoach) {
      navigate('/dashboard', { replace: true })
    }
  }, [navigate, user])

  if (!user?.isCoach) {
    return null
  }

  return (
    <div className="coach-dashboard">
      <Navbar />
      <main className="coach-main">
        <header className="coach-header">
          <div>
            <p className="coach-eyebrow">Coach Command Center</p>
            <h1>Welcome back, Coach</h1>
            <p className="coach-subtitle">
              Track your students’ progress, assign new training plans, and review recent activity — all in one place.
            </p>
          </div>
          <div className="coach-meta">
            <div className="coach-meta-card">
              <span className="coach-meta-label">Signed in as</span>
              <strong>{coachEmail}</strong>
            </div>
            <div className="coach-meta-card">
              <span className="coach-meta-label">Active students</span>
              <strong>{demoStudents.length}</strong>
            </div>
            <div className="coach-meta-card">
              <span className="coach-meta-label">Avg rating</span>
              <strong>
                {Math.round(
                  demoStudents.reduce((total, student) => total + student.rating, 0) /
                    demoStudents.length,
                )}
              </strong>
            </div>
          </div>
        </header>

        <section className="coach-section">
          <div className="coach-section-head">
            <h2>Your students</h2>
            <p>Quick snapshot of current focus areas and engagement.</p>
          </div>

          <div className="coach-grid">
            {demoStudents.map((student) => (
              <article className="coach-card" key={student.id}>
                <header className="coach-card-head">
                  <h3>{student.name}</h3>
                  <span className="coach-rating">Rating {student.rating}</span>
                </header>
                <dl className="coach-card-body">
                  <div>
                    <dt>Progress</dt>
                    <dd>{student.progress}</dd>
                  </div>
                  <div>
                    <dt>Current focus</dt>
                    <dd>{student.focus}</dd>
                  </div>
                  <div>
                    <dt>Latest activity</dt>
                    <dd>{student.activity}</dd>
                  </div>
                </dl>
                <footer className="coach-card-actions">
                  <button type="button" className="btn-primary">
                    Open Training Plan
                  </button>
                  <button type="button" className="btn-ghost">
                    Message
                  </button>
                </footer>
              </article>
            ))}
          </div>
        </section>
      </main>
    </div>
  )
}

export default CoachDashboard
