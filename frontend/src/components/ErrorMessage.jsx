import { AlertCircle, RefreshCw } from 'lucide-react';
import './ErrorMessage.css';

export default function ErrorMessage({ message, onRetry }) {
  const displayMessage =
    typeof message === 'object' && message !== null
      ? message.message || message.detail || JSON.stringify(message)
      : String(message || 'An unexpected error occurred.');

  return (
    <div className="error-message animate-fade-in">
      <AlertCircle size={24} className="error-icon" />
      <div className="error-body">
        <p className="error-title">Something went wrong</p>
        <p className="error-detail">{displayMessage}</p>
      </div>
      {onRetry && (
        <button className="btn btn-secondary" onClick={onRetry}>
          <RefreshCw size={14} />
          Retry
        </button>
      )}
    </div>
  );
}
