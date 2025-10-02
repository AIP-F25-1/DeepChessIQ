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

  const handleKeyDown = (event: React.KeyboardEvent<HTMLDivElement>) => {
    if (!onClick) return
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault()
      onClick()
    }
  }

  return (
    <div className={classes} onClick={onClick} role={onClick ? 'button' : undefined} tabIndex={onClick ? 0 : undefined} onKeyDown={handleKeyDown}>
      <div className="feature-icon" aria-hidden>
        {icon}
      </div>
      <div className="feature-title">{title}</div>
      <div className="feature-desc">{description}</div>
    </div>
  )
}

export default FeatureCard


