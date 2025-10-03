import './feature-card.css'

type Props = {
  icon: string
  title: string
  description: string
  accent?: boolean
  onClick?: () => void
}

function FeatureCard({ icon, title, description, accent, onClick }: Props) {
  const classes = [
    'feature-card',
    accent ? 'feature-card-accent' : null,
    onClick ? 'feature-card-actionable' : null,
  ]
    .filter(Boolean)
    .join(' ')

  return (
    <button type="button" className={classes} onClick={onClick} aria-label={`${title} - ${description}`}>
      <div className="feature-icon" aria-hidden>
        {icon}
      </div>
      <div className="feature-title">{title}</div>
      <div className="feature-desc">{description}</div>
    </button>
  )
}

export default FeatureCard


