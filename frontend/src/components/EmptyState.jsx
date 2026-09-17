import { Inbox } from 'lucide-react';
import './EmptyState.css';

export default function EmptyState({ icon: Icon = Inbox, message, action }) {
  return (
    <div className="empty-state animate-fade-in">
      <Icon size={48} className="empty-icon" />
      <p className="empty-message">{message || 'Nothing here yet'}</p>
      {action && (
        <div className="empty-action">{action}</div>
      )}
    </div>
  );
}
