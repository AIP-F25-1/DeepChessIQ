import './feature-card.css'

type Props = {
  icon: string
  title: string
  description: string
  accent?: boolean
}

function FeatureCard({ icon, title, description, accent }: Props) {
  const className = accent ? 'feature-card feature-card-accent' : 'feature-card'

  return (
    <div className={className}>
      <div className="feature-icon" aria-hidden>
        {icon}
      </div>
      <div className="feature-title">{title}</div>
      <div className="feature-desc">{description}</div>
    </div>
  )
}

export default FeatureCard


