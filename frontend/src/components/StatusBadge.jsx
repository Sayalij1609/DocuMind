import './StatusBadge.css';

const STATUS_MAP = {
  completed: { label: 'Completed', className: 'badge-success' },
  processing: { label: 'Processing', className: 'badge-info' },
  uploaded: { label: 'Uploaded', className: 'badge-secondary' },
  failed: { label: 'Failed', className: 'badge-error' },
  valid: { label: 'Valid', className: 'badge-success' },
  invalid: { label: 'Invalid', className: 'badge-error' },
  warning: { label: 'Warning', className: 'badge-warning' },
  anomaly: { label: 'Anomaly', className: 'badge-anomaly' },
  duplicate: { label: 'Duplicate', className: 'badge-duplicate' },
  normal: { label: 'Normal', className: 'badge-success' },
  pending: { label: 'Pending', className: 'badge-secondary' },
  skipped: { label: 'Skipped', className: 'badge-secondary' },
};

export default function StatusBadge({ status, label }) {
  const key = (status || '').toLowerCase();
  const config = STATUS_MAP[key] || { label: status, className: 'badge-secondary' };

  return (
    <span className={`status-badge ${config.className}`}>
      <span className="status-dot" />
      {label || config.label}
    </span>
  );
}
