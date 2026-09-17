import { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  AlertTriangle,
  FileText,
  ExternalLink,
  RefreshCw,
  SlidersHorizontal,
  CheckCircle,
} from 'lucide-react';
import { getDocuments, getDocumentAnalysis } from '../services/api';
import DataTable from '../components/DataTable';
import MetricCard from '../components/MetricCard';
import StatusBadge from '../components/StatusBadge';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorMessage from '../components/ErrorMessage';
import './AnomaliesPage.css';

export default function AnomaliesPage() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [docAnalyses, setDocAnalyses] = useState([]);
  const [onlyAnomalies, setOnlyAnomalies] = useState(true);

  const fetchAnomaliesData = async () => {
    setLoading(true);
    setError(null);
    try {
      const docListRes = await getDocuments(1, 100);
      const docs = docListRes.documents || [];

      // Fetch analysis for each document concurrently
      const analyses = await Promise.all(
        docs.map(async (doc) => {
          try {
            const a = await getDocumentAnalysis(doc.document_id);
            return { ...doc, ...a };
          } catch {
            return { ...doc, is_anomaly: false, anomaly_score: null };
          }
        })
      );

      setDocAnalyses(analyses);
    } catch (err) {
      setError(err.message || 'Failed to fetch anomaly records');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnomaliesData();
  }, []);

  const anomalyDocs = useMemo(
    () => docAnalyses.filter((d) => d.is_anomaly),
    [docAnalyses]
  );

  const displayedDocs = useMemo(
    () => (onlyAnomalies ? anomalyDocs : docAnalyses),
    [onlyAnomalies, anomalyDocs, docAnalyses]
  );

  const totalScanned = docAnalyses.length;
  const anomalyCount = anomalyDocs.length;
  const anomalyRate =
    totalScanned > 0 ? ((anomalyCount / totalScanned) * 100).toFixed(1) : '0.0';

  const columns = [
    {
      key: 'filename',
      label: 'Document',
      render: (val, row) => (
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <FileText size={16} style={{ color: 'var(--accent-primary)' }} />
          <div>
            <div style={{ fontWeight: 500, color: 'var(--text-primary)' }}>{val}</div>
            <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)' }}>
              ID: {row.document_id?.slice(0, 8)}...
            </div>
          </div>
        </div>
      ),
    },
    {
      key: 'document_type',
      label: 'Type',
      render: (val) => (
        <span style={{ textTransform: 'capitalize', fontWeight: 500 }}>
          {val || '—'}
        </span>
      ),
    },
    {
      key: 'is_anomaly',
      label: 'Evaluation',
      render: (val) => (
        <StatusBadge
          status={val ? 'anomaly' : 'normal'}
          label={val ? 'Flagged Outlier' : 'Normal'}
        />
      ),
    },
    {
      key: 'anomaly_score',
      label: 'Anomaly Score',
      render: (val, row) => (
        <span
          style={{
            fontWeight: 600,
            fontFamily: 'monospace',
            color: row.is_anomaly ? 'var(--color-anomaly)' : 'var(--text-secondary)',
          }}
        >
          {val != null ? val : '—'}
        </span>
      ),
    },
    {
      key: 'created_at',
      label: 'Analyzed',
      render: (val) => (val ? new Date(val).toLocaleDateString() : '—'),
    },
    {
      key: 'actions',
      label: '',
      render: (_, row) => (
        <button
          className="btn btn-secondary"
          style={{ padding: '4px 10px', fontSize: 'var(--font-size-xs)' }}
          onClick={(e) => {
            e.stopPropagation();
            navigate(`/documents/${row.document_id}`);
          }}
        >
          Inspect
          <ExternalLink size={12} />
        </button>
      ),
    },
  ];

  if (loading && docAnalyses.length === 0) {
    return <LoadingSpinner message="Scanning documents for anomalies..." />;
  }

  if (error && docAnalyses.length === 0) {
    return <ErrorMessage message={error} onRetry={fetchAnomaliesData} />;
  }

  return (
    <div className="anomalies-page animate-fade-in">
      <div className="page-header">
        <h1>Document Anomalies</h1>
        <p>Unsupervised outlier detection using Isolation Forest on structured features</p>
      </div>

      <div className="anomaly-alert-banner">
        <AlertTriangle size={24} />
        <div className="banner-content">
          <h4>Isolation Forest Outlier Engine</h4>
          <p>
            Anomalies indicate statistical deviations in features such as invoice amounts, page count, missing fields, or vendor frequency. They flag unusual patterns for human review without asserting fraud.
          </p>
        </div>
      </div>

      <div className="grid-metrics">
        <MetricCard
          icon={FileText}
          label="Total Scanned"
          value={totalScanned}
          subtitle="Processed documents evaluated"
          color="var(--accent-primary)"
        />
        <MetricCard
          icon={AlertTriangle}
          label="Anomalies Flagged"
          value={anomalyCount}
          subtitle={`${anomalyRate}% anomaly rate`}
          color="var(--color-anomaly)"
        />
        <MetricCard
          icon={CheckCircle}
          label="Normal Documents"
          value={totalScanned - anomalyCount}
          subtitle="Conforming to baseline distribution"
          color="var(--color-success)"
        />
        <MetricCard
          icon={SlidersHorizontal}
          label="Model Strategy"
          value="Isolation Forest"
          subtitle="Document-level features"
          color="var(--accent-secondary)"
        />
      </div>

      <div className="anomalies-filter-bar">
        <label className="toggle-label">
          <input
            type="checkbox"
            className="toggle-checkbox"
            checked={onlyAnomalies}
            onChange={(e) => setOnlyAnomalies(e.target.checked)}
          />
          Show only flagged anomalies ({anomalyCount})
        </label>

        <button className="btn btn-secondary" onClick={fetchAnomaliesData}>
          <RefreshCw size={14} />
          Refresh
        </button>
      </div>

      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        <DataTable
          columns={columns}
          data={displayedDocs}
          emptyMessage={
            onlyAnomalies
              ? 'No documents currently flagged as anomalies'
              : 'No documents found'
          }
          onRowClick={(doc) => navigate(`/documents/${doc.document_id}`)}
        />
      </div>
    </div>
  );
}
