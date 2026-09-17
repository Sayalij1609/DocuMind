import './MetricCard.css';

export default function MetricCard({ icon: Icon, label, value, subtitle, color }) {
  const accentStyle = color ? { '--card-accent': color } : {};

  return (
    <div className="metric-card card" style={accentStyle}>
      <div className="metric-card-header">
        {Icon && (
          <div className="metric-icon-wrap">
            <Icon size={20} />
          </div>
        )}
        <span className="metric-label">{label}</span>
      </div>
      <div className="metric-value">{value ?? '—'}</div>
      {subtitle && <div className="metric-subtitle">{subtitle}</div>}
    </div>
  );
}
