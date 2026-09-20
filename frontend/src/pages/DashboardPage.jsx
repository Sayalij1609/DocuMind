import { useNavigate, Link } from 'react-router-dom';
import {
  FileText,
  CheckCircle,
  XCircle,
  BarChart3,
  TrendingUp,
  ArrowLeft,
  Home,
  AlertCircle,
  RefreshCw,
  Clock,
} from 'lucide-react';
import { useApi } from '../hooks/useApi';
import { getDocuments } from '../services/api';
import MetricCard from '../components/MetricCard';
import DataTable from '../components/DataTable';
import StatusBadge from '../components/StatusBadge';
import LoadingSpinner from '../components/LoadingSpinner';
import './DashboardPage.css';

export default function DashboardPage() {
  const navigate = useNavigate();
  const { data, loading, error, refetch } = useApi(getDocuments);

  if (loading && !data && !error) return <LoadingSpinner message="Loading dashboard..." />;

  const documents = data?.documents || [];
  const total = documents.length;

  // Compute live metrics
  const completed = documents.filter((d) => d.status === 'completed').length;
  const failed = documents.filter((d) => d.status === 'failed').length;
  const processing = documents.filter((d) => d.status === 'processing').length;
  const classified = documents.filter((d) => d.document_type).length;

  // Document type distribution
  const typeCounts = {};
  documents.forEach((d) => {
    const type = d.document_type || 'unclassified';
    typeCounts[type] = (typeCounts[type] || 0) + 1;
  });
  const typeEntries = Object.entries(typeCounts).sort((a, b) => b[1] - a[1]);

  // Recent documents (last 8)
  const recent = [...documents]
    .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
    .slice(0, 8);

  const recentColumns = [
    {
      key: 'filename',
      label: 'Filename',
      render: (val) => (
        <span className="filename-cell" title={val}>
          {val?.length > 35 ? val.slice(0, 35) + '…' : val}
        </span>
      ),
    },
    {
      key: 'document_type',
      label: 'Type',
      render: (val) => (
        <span className="type-cell">{val || '—'}</span>
      ),
    },
    {
      key: 'status',
      label: 'Status',
      render: (val) => <StatusBadge status={val} />,
    },
    {
      key: 'classification_confidence',
      label: 'Confidence',
      render: (val) => val != null ? `${(val * 100).toFixed(1)}%` : '—',
    },
    {
      key: 'created_at',
      label: 'Uploaded',
      render: (val) => val ? new Date(val).toLocaleDateString() : '—',
    },
  ];

  return (
    <div className="dashboard-page animate-fade-in">
      <div className="page-header">
        <div className="page-header-top-nav">
          <Link to="/" className="inline-back-home" title="Go to Home">
            <ArrowLeft size={14} />
            <Home size={14} />
            <span>Back to Home</span>
          </Link>
        </div>
        <h1>Dashboard</h1>
        <p>Overview of your document intelligence pipeline</p>
      </div>

      {/* Offline notice if backend is unreachable */}
      {error && (
        <div className="backend-offline-banner card animate-fade-in">
          <div className="offline-banner-left">
            <AlertCircle size={20} className="offline-banner-icon" />
            <div>
              <p className="offline-banner-title">Backend Server Offline</p>
              <p className="offline-banner-desc">
                Could not connect to API server. Dashboard is displaying in offline mode. Start your backend with <code>uvicorn app.main:app --reload</code> on port 8000 to view live pipeline data.
              </p>
            </div>
          </div>
          <button className="btn btn-secondary btn-sm" onClick={refetch}>
            <RefreshCw size={14} />
            <span>Retry Connection</span>
          </button>
        </div>
      )}
      <div className="grid-metrics">
        <MetricCard
          icon={FileText}
          label="Total Documents"
          value={total}
          subtitle={`${processing} currently processing`}
          color="var(--accent-primary)"
        />
        <MetricCard
          icon={CheckCircle}
          label="Completed"
          value={completed}
          subtitle={total > 0 ? `${((completed / total) * 100).toFixed(0)}% success rate` : 'No documents'}
          color="var(--color-success)"
        />
        <MetricCard
          icon={XCircle}
          label="Failed"
          value={failed}
          subtitle={total > 0 ? `${((failed / total) * 100).toFixed(0)}% failure rate` : 'No failures'}
          color="var(--color-error)"
        />
        <MetricCard
          icon={BarChart3}
          label="Classified"
          value={classified}
          subtitle={`${typeEntries.length} document types`}
          color="var(--accent-secondary)"
        />
      </div>

      {/* Two-column layout: Type distribution + Recent docs */}
      <div className="dashboard-grid">
        {/* Document Type Distribution */}
        <div className="card type-distribution">
          <h3 className="card-title">
            <TrendingUp size={18} />
            Document Types
          </h3>
          {typeEntries.length === 0 ? (
            <p className="no-data">No classified documents yet</p>
          ) : (
            <div className="type-list">
              {typeEntries.map(([type, count]) => (
                <div key={type} className="type-row">
                  <span className="type-name">{type}</span>
                  <div className="type-bar-wrapper">
                    <div
                      className="type-bar"
                      style={{ width: `${(count / total) * 100}%` }}
                    />
                  </div>
                  <span className="type-count">{count}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Recent Documents */}
        <div className="card recent-docs">
          <h3 className="card-title">
            <Clock size={18} />
            Recent Documents
          </h3>
          <DataTable
            columns={recentColumns}
            data={recent}
            emptyMessage="No documents uploaded yet"
            onRowClick={(doc) => navigate(`/documents/${doc.document_id}`)}
          />
        </div>
      </div>
    </div>
  );
}
