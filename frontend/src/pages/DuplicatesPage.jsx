import { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Copy,
  FileText,
  ExternalLink,
  RefreshCw,
  CheckCircle,
  AlertCircle,
} from 'lucide-react';
import { getDocuments, getDocumentDuplicates } from '../services/api';
import DataTable from '../components/DataTable';
import MetricCard from '../components/MetricCard';
import StatusBadge from '../components/StatusBadge';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorMessage from '../components/ErrorMessage';
import './DuplicatesPage.css';

export default function DuplicatesPage() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [duplicateRecords, setDuplicateRecords] = useState([]);
  const [onlyHasDuplicates, setOnlyHasDuplicates] = useState(true);

  const fetchDuplicatesData = async () => {
    setLoading(true);
    setError(null);
    try {
      const docListRes = await getDocuments(1, 100);
      const docs = docListRes.documents || [];

      // Check duplicates for each document
      const results = await Promise.all(
        docs.map(async (doc) => {
          try {
            const dup = await getDocumentDuplicates(doc.document_id);
            return {
              ...doc,
              has_duplicates: dup.has_duplicates,
              exact_count: dup.exact_count || 0,
              near_count: dup.near_count || 0,
              matches: dup.matches || [],
            };
          } catch {
            return {
              ...doc,
              has_duplicates: false,
              exact_count: 0,
              near_count: 0,
              matches: [],
            };
          }
        })
      );

      setDuplicateRecords(results);
    } catch (err) {
      setError(err.message || 'Failed to fetch duplicate records');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDuplicatesData();
  }, []);

  const docsWithDuplicates = useMemo(
    () => duplicateRecords.filter((d) => d.has_duplicates),
    [duplicateRecords]
  );

  const displayedDocs = useMemo(
    () => (onlyHasDuplicates ? docsWithDuplicates : duplicateRecords),
    [onlyHasDuplicates, docsWithDuplicates, duplicateRecords]
  );

  const totalScanned = duplicateRecords.length;
  const duplicateCount = docsWithDuplicates.length;
  const totalExactMatches = duplicateRecords.reduce((acc, d) => acc + (d.exact_count || 0), 0);
  const totalNearMatches = duplicateRecords.reduce((acc, d) => acc + (d.near_count || 0), 0);

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
      key: 'has_duplicates',
      label: 'Duplicate Status',
      render: (val) => (
        <StatusBadge
          status={val ? 'duplicate' : 'normal'}
          label={val ? 'Duplicate Found' : 'Unique'}
        />
      ),
    },
    {
      key: 'matches',
      label: 'Matches',
      render: (matches, row) => (
        <div style={{ fontSize: 'var(--font-size-sm)' }}>
          {row.has_duplicates ? (
            <span>
              <strong style={{ color: 'var(--color-duplicate)' }}>{matches.length}</strong> match
              {matches.length > 1 ? 'es' : ''} ({row.exact_count} exact, {row.near_count} near)
            </span>
          ) : (
            <span style={{ color: 'var(--text-muted)' }}>0 matches</span>
          )}
        </div>
      ),
    },
    {
      key: 'highest_similarity',
      label: 'Highest Similarity',
      render: (_, row) => {
        if (!row.matches || row.matches.length === 0) return '—';
        const highest = Math.max(...row.matches.map((m) => m.similarity_score || 0));
        return (
          <span style={{ fontWeight: 600, fontFamily: 'monospace', color: 'var(--color-warning)' }}>
            {(highest * 100).toFixed(1)}%
          </span>
        );
      },
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

  if (loading && duplicateRecords.length === 0) {
    return <LoadingSpinner message="Checking documents for duplicates..." />;
  }

  if (error && duplicateRecords.length === 0) {
    return <ErrorMessage message={error} onRetry={fetchDuplicatesData} />;
  }

  return (
    <div className="duplicates-page animate-fade-in">
      <div className="page-header">
        <h1>Duplicate Detection</h1>
        <p>TF-IDF cosine vector matching across documents of the same category</p>
      </div>

      <div className="duplicates-banner">
        <Copy size={24} />
        <div className="banner-content">
          <h4>Cosine Similarity Thresholds</h4>
          <p>
            Documents are compared within their classification category. Exact duplicates (similarity ≥ 0.99) and near-duplicates (similarity ≥ 0.85) are identified for deduplication and audit tracking.
          </p>
        </div>
      </div>

      <div className="grid-metrics">
        <MetricCard
          icon={FileText}
          label="Total Documents"
          value={totalScanned}
          subtitle="Documents evaluated"
          color="var(--accent-primary)"
        />
        <MetricCard
          icon={Copy}
          label="Documents with Duplicates"
          value={duplicateCount}
          subtitle={totalScanned > 0 ? `${((duplicateCount / totalScanned) * 100).toFixed(1)}% duplicate rate` : 'None'}
          color="var(--color-duplicate)"
        />
        <MetricCard
          icon={AlertCircle}
          label="Exact Matches"
          value={totalExactMatches}
          subtitle="Similarity ≥ 0.99"
          color="var(--color-error)"
        />
        <MetricCard
          icon={CheckCircle}
          label="Near Matches"
          value={totalNearMatches}
          subtitle="Similarity ≥ 0.85"
          color="var(--color-warning)"
        />
      </div>

      <div className="duplicates-filter-bar">
        <label className="toggle-label">
          <input
            type="checkbox"
            className="toggle-checkbox"
            checked={onlyHasDuplicates}
            onChange={(e) => setOnlyHasDuplicates(e.target.checked)}
          />
          Show only documents with duplicates ({duplicateCount})
        </label>

        <button className="btn btn-secondary" onClick={fetchDuplicatesData}>
          <RefreshCw size={14} />
          Refresh
        </button>
      </div>

      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        <DataTable
          columns={columns}
          data={displayedDocs}
          emptyMessage={
            onlyHasDuplicates
              ? 'No duplicate documents detected in your repository'
              : 'No documents found'
          }
          onRowClick={(doc) => navigate(`/documents/${doc.document_id}`)}
        />
      </div>
    </div>
  );
}
