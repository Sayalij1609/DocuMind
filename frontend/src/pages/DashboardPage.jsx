import { useState, useEffect } from 'react';
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
  Upload,
  Sparkles,
  ShieldCheck,
  AlertTriangle,
  Search,
  Filter,
  ArrowRight,
  Zap,
  Bot,
  Activity,
  CheckCircle2,
  Play,
} from 'lucide-react';
import { useApi } from '../hooks/useApi';
import { getDocuments, startDocumentProcessing, getAIStatus } from '../services/api';
import MetricCard from '../components/MetricCard';
import StatusBadge from '../components/StatusBadge';
import LoadingSpinner from '../components/LoadingSpinner';
import './DashboardPage.css';

export default function DashboardPage() {
  const navigate = useNavigate();
  const { data, loading, error, refetch } = useApi(getDocuments);
  const [aiStatus, setAiStatus] = useState(null);
  const [selectedType, setSelectedType] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [actionLoadingId, setActionLoadingId] = useState(null);

  useEffect(() => {
    getAIStatus().then(setAiStatus).catch(() => null);
  }, []);

  if (loading && !data && !error) return <LoadingSpinner message="Loading enterprise dashboard..." />;

  const documents = data?.documents || [];
  const total = documents.length;

  // Compute live metrics
  const completed = documents.filter((d) => d.status === 'completed').length;
  const failed = documents.filter((d) => d.status === 'failed').length;
  const processing = documents.filter((d) => d.status === 'processing').length;
  const uploaded = documents.filter((d) => d.status === 'uploaded').length;
  const classified = documents.filter((d) => d.document_type).length;

  // Document type distribution
  const typeCounts = {};
  documents.forEach((d) => {
    const type = d.document_type || 'unclassified';
    typeCounts[type] = (typeCounts[type] || 0) + 1;
  });
  const typeEntries = Object.entries(typeCounts).sort((a, b) => b[1] - a[1]);

  // Filtering recent docs
  let filteredDocs = [...documents].sort((a, b) => new Date(b.created_at) - new Date(a.created_at));

  if (selectedType !== 'all') {
    filteredDocs = filteredDocs.filter((d) => (d.document_type || 'unclassified').toLowerCase() === selectedType.toLowerCase());
  }

  if (searchQuery.trim()) {
    const q = searchQuery.toLowerCase();
    filteredDocs = filteredDocs.filter(
      (d) =>
        d.filename.toLowerCase().includes(q) ||
        (d.document_type || '').toLowerCase().includes(q) ||
        (d.document_id || '').toLowerCase().includes(q)
    );
  }

  const handleStartAnalysis = async (e, docId) => {
    e.stopPropagation();
    setActionLoadingId(docId);
    try {
      await startDocumentProcessing(docId);
      refetch();
      navigate(`/documents/${docId}`);
    } catch {
      setActionLoadingId(null);
      navigate(`/documents/${docId}`);
    }
  };

  const successRate = total > 0 ? ((completed / total) * 100).toFixed(0) : '100';

  return (
    <div className="dashboard-page animate-fade-in">
      {/* Top Header */}
      <div className="dashboard-header-container">
        <div className="dashboard-header-left">
          <h1 className="dashboard-main-title">Document Intelligence Dashboard</h1>
          <p className="dashboard-main-subtitle">
            Live pipeline throughput, automated compliance auditing, and AI extraction monitoring
          </p>
        </div>

        <div className="dashboard-header-actions">
          <button className="btn btn-secondary btn-sm refresh-btn" onClick={refetch} title="Refresh Live Data">
            <RefreshCw size={14} />
            <span>Refresh</span>
          </button>
          <Link to="/upload" className="btn btn-primary btn-sm upload-cta-btn">
            <Upload size={15} />
            <span>Upload Document</span>
          </Link>
          <Link to="/" className="btn btn-secondary btn-sm home-btn" title="Back to Home">
            <Home size={14} />
            <span>Back to Home</span>
          </Link>
        </div>
      </div>

      {/* Offline notice if backend is unreachable */}
      {error && (
        <div className="backend-offline-banner card animate-fade-in">
          <div className="offline-banner-left">
            <AlertCircle size={20} className="offline-banner-icon" />
            <div>
              <p className="offline-banner-title">Backend Server Offline</p>
              <p className="offline-banner-desc">
                Could not connect to API server. Dashboard is displaying in offline mode. Start your backend with{' '}
                <code>uvicorn app.main:app --reload</code> on port 8000 to view live pipeline data.
              </p>
            </div>
          </div>
          <button className="btn btn-secondary btn-sm" onClick={refetch}>
            <RefreshCw size={14} />
            <span>Retry Connection</span>
          </button>
        </div>
      )}

      {/* System Engine Health Strip */}
      <div className="system-health-strip card animate-fade-in">
        <div className="health-item">
          <span className="health-dot dot-online" />
          <span className="health-label">API Gateway:</span>
          <strong className="health-val">Online (Port 8000)</strong>
        </div>
        <div className="health-divider" />
        <div className="health-item">
          <Zap size={14} className="health-icon" />
          <span className="health-label">OCR Engine:</span>
          <strong className="health-val">Tesseract OCR & Normalizer</strong>
        </div>
        <div className="health-divider" />
        <div className="health-item">
          <ShieldCheck size={14} className="health-icon" />
          <span className="health-label">Auditing:</span>
          <strong className="health-val">6 Deterministic Rules Active</strong>
        </div>
        <div className="health-divider" />
        <div className="health-item">
          <Bot size={14} className="health-icon" />
          <span className="health-label">AI Copilot:</span>
          <strong className="health-val">
            {aiStatus?.configured ? `Groq LLM (${aiStatus.model})` : 'Local Heuristic Mode'}
          </strong>
        </div>
      </div>

      {/* 4 Executive KPI Cards */}
      <div className="grid-metrics">
        <MetricCard
          icon={FileText}
          label="Total Ingested"
          value={total}
          subtitle={`${completed} analyzed • ${processing} processing`}
          color="var(--accent-primary)"
        />
        <MetricCard
          icon={CheckCircle}
          label="Audit Success Rate"
          value={`${successRate}%`}
          subtitle={`${completed} completed without fatal errors`}
          color="var(--color-success)"
        />
        <MetricCard
          icon={Clock}
          label="Ready to Analyze"
          value={uploaded}
          subtitle={uploaded > 0 ? `${uploaded} files waiting for analysis trigger` : 'All uploaded files analyzed'}
          color="var(--accent-secondary)"
        />
        <MetricCard
          icon={AlertTriangle}
          label="Failed / Flagged"
          value={failed}
          subtitle={failed > 0 ? `${failed} documents encountered errors` : 'Zero pipeline failures'}
          color={failed > 0 ? 'var(--color-error)' : 'var(--text-tertiary)'}
        />
      </div>

      {/* Visual Pipeline Workflow Strip */}
      <div className="pipeline-flow-card card animate-fade-in">
        <div className="flow-header">
          <h3 className="flow-title">
            <Activity size={18} />
            End-to-End Processing Architecture
          </h3>
          <span className="flow-badge">Real-Time Automated Pipeline</span>
        </div>
        <div className="flow-steps-strip">
          <div className="flow-step">
            <div className="flow-step-number">1</div>
            <div className="flow-step-info">
              <span className="flow-step-title">Ingest & Stage</span>
              <span className="flow-step-desc">Storage & Validation</span>
            </div>
          </div>
          <div className="flow-arrow">→</div>
          <div className="flow-step">
            <div className="flow-step-number">2</div>
            <div className="flow-step-info">
              <span className="flow-step-title">OCR Text</span>
              <span className="flow-step-desc">Tesseract Extraction</span>
            </div>
          </div>
          <div className="flow-arrow">→</div>
          <div className="flow-step">
            <div className="flow-step-number">3</div>
            <div className="flow-step-info">
              <span className="flow-step-title">SGD Classifier</span>
              <span className="flow-step-desc">Document Type Model</span>
            </div>
          </div>
          <div className="flow-arrow">→</div>
          <div className="flow-step">
            <div className="flow-step-number">4</div>
            <div className="flow-step-info">
              <span className="flow-step-title">Deterministic Rules</span>
              <span className="flow-step-desc">Math & Field Auditing</span>
            </div>
          </div>
          <div className="flow-arrow">→</div>
          <div className="flow-step">
            <div className="flow-step-number">5</div>
            <div className="flow-step-info">
              <span className="flow-step-title">Outlier & Dedup</span>
              <span className="flow-step-desc">Isolation Forest & Cosine</span>
            </div>
          </div>
          <div className="flow-arrow">→</div>
          <div className="flow-step">
            <div className="flow-step-number">6</div>
            <div className="flow-step-info">
              <span className="flow-step-title">Groq AI Reasoning</span>
              <span className="flow-step-desc">Executive Summary & QA</span>
            </div>
          </div>
        </div>
      </div>

      {/* Two-column layout: Type distribution + Recent docs */}
      <div className="dashboard-grid">
        {/* Document Type Distribution */}
        <div className="card type-distribution">
          <h3 className="card-title">
            <TrendingUp size={18} />
            Document Types
          </h3>
          <p className="type-distribution-subtitle">Categorization breakdown by SGD classifier</p>

          {typeEntries.length === 0 ? (
            <p className="no-data">No classified documents yet</p>
          ) : (
            <div className="type-list">
              {typeEntries.map(([type, count]) => {
                const pct = total > 0 ? ((count / total) * 100).toFixed(0) : 0;
                const isSelected = selectedType.toLowerCase() === type.toLowerCase();
                return (
                  <div
                    key={type}
                    className={`type-row-interactive ${isSelected ? 'active' : ''}`}
                    onClick={() => setSelectedType(isSelected ? 'all' : type)}
                    title={`Filter by ${type}`}
                  >
                    <div className="type-info-header">
                      <span className="type-name">{type}</span>
                      <span className="type-percentage">{pct}% ({count})</span>
                    </div>
                    <div className="type-bar-wrapper">
                      <div className="type-bar" style={{ width: `${pct}%` }} />
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {selectedType !== 'all' && (
            <button className="btn btn-ghost btn-xs clear-filter-btn" onClick={() => setSelectedType('all')}>
              Clear Filter ({selectedType})
            </button>
          )}

          {/* Quick upload drop CTA */}
          <div className="quick-upload-banner">
            <Sparkles size={16} className="quick-sparkle" />
            <div className="quick-upload-text">
              <strong>Need to analyze a new file?</strong>
              <span>Upload PDF, JPG or PNG to stage document.</span>
            </div>
            <Link to="/upload" className="btn btn-accent btn-xs">
              Upload
            </Link>
          </div>
        </div>

        {/* Recent Documents Table with Action Controls */}
        <div className="card recent-docs">
          <div className="recent-docs-header">
            <div className="recent-docs-title-wrap">
              <h3 className="card-title" style={{ margin: 0 }}>
                <Clock size={18} />
                Recent Documents Queue
              </h3>
              <span className="queue-count-badge">{filteredDocs.length} shown</span>
            </div>

            <div className="recent-docs-search">
              <Search size={14} className="search-icon" />
              <input
                type="text"
                placeholder="Search documents..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="search-input"
              />
            </div>
          </div>

          {filteredDocs.length === 0 ? (
            <div className="no-docs-box">
              <p className="no-data">No documents matching filter.</p>
              <Link to="/upload" className="btn btn-primary btn-sm">
                Upload First Document
              </Link>
            </div>
          ) : (
            <div className="table-responsive">
              <table className="modern-table">
                <thead>
                  <tr>
                    <th>Document</th>
                    <th>Class</th>
                    <th>Status</th>
                    <th>Confidence</th>
                    <th>Date</th>
                    <th style={{ textAlign: 'right' }}>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredDocs.slice(0, 10).map((doc) => {
                    const isUploaded = doc.status === 'uploaded';
                    const isProcessing = doc.status === 'processing';
                    const isCompleted = doc.status === 'completed';
                    const isLoading = actionLoadingId === doc.document_id;

                    return (
                      <tr
                        key={doc.document_id}
                        className="doc-row"
                        onClick={() => navigate(`/documents/${doc.document_id}`)}
                      >
                        <td className="doc-name-cell">
                          <div className="doc-avatar">
                            <FileText size={18} />
                          </div>
                          <div className="doc-meta-info">
                            <span className="doc-filename" title={doc.filename}>
                              {doc.filename}
                            </span>
                            <span className="doc-id-sub mono">{doc.document_id.slice(0, 8)}...</span>
                          </div>
                        </td>

                        <td>
                          <span className="type-tag">{doc.document_type || 'Unclassified'}</span>
                        </td>

                        <td>
                          <StatusBadge status={doc.status} />
                        </td>

                        <td>
                          {doc.classification_confidence != null ? (
                            <div className="confidence-meter-mini">
                              <div className="confidence-bar-mini">
                                <div
                                  className="confidence-fill-mini"
                                  style={{
                                    width: `${(doc.classification_confidence * 100).toFixed(0)}%`,
                                  }}
                                />
                              </div>
                              <span className="confidence-num">
                                {(doc.classification_confidence * 100).toFixed(0)}%
                              </span>
                            </div>
                          ) : (
                            <span className="text-muted">—</span>
                          )}
                        </td>

                        <td className="date-cell">
                          {doc.created_at ? new Date(doc.created_at).toLocaleDateString() : '—'}
                        </td>

                        <td style={{ textAlign: 'right' }}>
                          {isUploaded ? (
                            <button
                              className="btn btn-accent btn-xs analyze-action-btn"
                              onClick={(e) => handleStartAnalysis(e, doc.document_id)}
                              disabled={isLoading}
                              title="Run Document Audit"
                            >
                              {isLoading ? (
                                <>
                                  <RefreshCw size={12} className="spin-animation" />
                                  <span>Starting...</span>
                                </>
                              ) : (
                                <>
                                  <Play size={12} />
                                  <span>Audit</span>
                                </>
                              )}
                            </button>
                          ) : isProcessing ? (
                            <span className="processing-indicator-pill">
                              <RefreshCw size={12} className="spin-animation" />
                              <span>Processing</span>
                            </span>
                          ) : (
                            <button
                              className="btn btn-secondary btn-xs view-action-btn"
                              onClick={(e) => {
                                e.stopPropagation();
                                navigate(`/documents/${doc.document_id}`);
                              }}
                            >
                              <span>Report</span>
                              <ArrowRight size={12} />
                            </button>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
