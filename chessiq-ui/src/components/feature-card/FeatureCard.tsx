import './feature-card.css'

type Props = {
  icon: string
  title: string
  description: string
  accent?: boolean
  onClick?: () => void
}

function FeatureCard({ icon, title, description, accent, onClick }: Props) {
  const className = accent ? 'feature-card feature-card-accent' : 'feature-card'

  return (
    <div className={className} onClick={onClick} role="button" tabIndex={0} onKeyDown={(e) => { if (onClick && (e.key === 'Enter' || e.key === ' ')) onClick() }}>
      <div className="feature-icon" aria-hidden>
        {icon}
      </div>
      <div className="feature-title">{title}</div>
      <div className="feature-desc">{description}</div>
    </div>
  )
}

export default FeatureCard


