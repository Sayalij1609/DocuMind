import { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Search,
  X,
  FileText,
  Filter,
  ExternalLink,
} from 'lucide-react';
import { useApi } from '../hooks/useApi';
import { getDocuments } from '../services/api';
import DataTable from '../components/DataTable';
import StatusBadge from '../components/StatusBadge';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorMessage from '../components/ErrorMessage';
import './SearchPage.css';

export default function SearchPage() {
  const navigate = useNavigate();
  const [query, setQuery] = useState('');
  const [selectedType, setSelectedType] = useState('ALL');

  const { data, loading, error, refetch } = useApi(getDocuments, [1, 500]);
  const documents = data?.documents || [];

  // Extract unique document types
  const types = useMemo(() => {
    const set = new Set();
    documents.forEach((d) => {
      if (d.document_type) set.add(d.document_type);
    });
    return Array.from(set).sort();
  }, [documents]);

  const filtered = useMemo(() => {
    return documents.filter((doc) => {
      const q = query.toLowerCase().trim();
      const matchQuery =
        !q ||
        doc.filename?.toLowerCase().includes(q) ||
        doc.document_id?.toLowerCase().includes(q) ||
        doc.document_type?.toLowerCase().includes(q) ||
        doc.status?.toLowerCase().includes(q);

      const matchType =
        selectedType === 'ALL' ||
        (selectedType === 'unclassified' ? !doc.document_type : doc.document_type === selectedType);

      return matchQuery && matchType;
    });
  }, [documents, query, selectedType]);

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
              ID: {row.document_id}
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
          {val || <span style={{ color: 'var(--text-muted)' }}>Unclassified</span>}
        </span>
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
      render: (val) => (val != null ? `${(val * 100).toFixed(1)}%` : '—'),
    },
    {
      key: 'created_at',
      label: 'Uploaded',
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
          View
          <ExternalLink size={12} />
        </button>
      ),
    },
  ];

  if (loading && !data) return <LoadingSpinner message="Loading search index..." />;
  if (error && !data) return <ErrorMessage message={error} onRetry={refetch} />;

  return (
    <div className="search-page animate-fade-in">
      <div className="page-header">
        <h1>Search Documents</h1>
        <p>Query repository by filename, ID, classification type, or processing status</p>
      </div>

      <div className="search-hero card">
        <div className="search-input-wrap">
          <Search size={22} className="search-hero-icon" />
          <input
            type="text"
            className="search-hero-input"
            placeholder="Search documents by filename, ID, or keywords..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            autoFocus
          />
          {query && (
            <button className="clear-search-btn" onClick={() => setQuery('')}>
              <X size={18} />
            </button>
          )}
        </div>

        <div className="quick-filter-chips">
          <span className="chip-label">
            <Filter size={12} style={{ display: 'inline', marginRight: '4px' }} />
            Category:
          </span>
          <button
            className={`filter-chip ${selectedType === 'ALL' ? 'active' : ''}`}
            onClick={() => setSelectedType('ALL')}
          >
            All
          </button>
          {types.map((t) => (
            <button
              key={t}
              className={`filter-chip ${selectedType === t ? 'active' : ''}`}
              onClick={() => setSelectedType(t)}
            >
              {t}
            </button>
          ))}
          <button
            className={`filter-chip ${selectedType === 'unclassified' ? 'active' : ''}`}
            onClick={() => setSelectedType('unclassified')}
          >
            Unclassified
          </button>
        </div>
      </div>

      <div className="search-results-info">
        <span>
          Showing <strong>{filtered.length}</strong> matching result
          {filtered.length === 1 ? '' : 's'}
          {query ? ` for "${query}"` : ''}
        </span>
      </div>

      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        <DataTable
          columns={columns}
          data={filtered}
          emptyMessage={
            query || selectedType !== 'ALL'
              ? 'No documents matched your query'
              : 'No documents in repository'
          }
          onRowClick={(doc) => navigate(`/documents/${doc.document_id}`)}
        />
      </div>
    </div>
  );
}
