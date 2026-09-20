import { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Search,
  Upload,
  RefreshCw,
  Trash2,
  FileText,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import { useApi } from '../hooks/useApi';
import { getDocuments, deleteDocument } from '../services/api';
import DataTable from '../components/DataTable';
import StatusBadge from '../components/StatusBadge';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorMessage from '../components/ErrorMessage';
import './DocumentsPage.css';

function formatBytes(bytes) {
  if (!bytes || bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
}

export default function DocumentsPage() {
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = useState('');
  const [typeFilter, setTypeFilter] = useState('ALL');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 15;

  const { data, loading, error, refetch } = useApi(getDocuments, [1, 200]);

  const allDocuments = data?.documents || [];

  // Get distinct document types for filter
  const distinctTypes = useMemo(() => {
    const types = new Set();
    allDocuments.forEach((doc) => {
      if (doc.document_type) types.add(doc.document_type);
    });
    return Array.from(types).sort();
  }, [allDocuments]);

  // Filtered list
  const filteredDocuments = useMemo(() => {
    return allDocuments.filter((doc) => {
      const matchSearch =
        !searchTerm ||
        doc.filename?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        doc.document_id?.toLowerCase().includes(searchTerm.toLowerCase());

      const matchType =
        typeFilter === 'ALL' ||
        (typeFilter === 'unclassified' ? !doc.document_type : doc.document_type === typeFilter);

      const matchStatus =
        statusFilter === 'ALL' || doc.status?.toLowerCase() === statusFilter.toLowerCase();

      return matchSearch && matchType && matchStatus;
    });
  }, [allDocuments, searchTerm, typeFilter, statusFilter]);

  // Pagination calculation
  const totalPages = Math.max(1, Math.ceil(filteredDocuments.length / pageSize));
  const paginatedDocuments = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return filteredDocuments.slice(start, start + pageSize);
  }, [filteredDocuments, currentPage, pageSize]);

  const handleDelete = async (e, docId) => {
    e.stopPropagation();
    if (!window.confirm(`Are you sure you want to delete this document?`)) return;

    try {
      await deleteDocument(docId);
      refetch();
    } catch (err) {
      alert(`Failed to delete document: ${err.message}`);
    }
  };

  const columns = [
    {
      key: 'filename',
      label: 'Document',
      render: (val, doc) => (
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <FileText size={16} style={{ color: 'var(--accent-primary)', flexShrink: 0 }} />
          <div>
            <div style={{ fontWeight: 500, color: 'var(--text-primary)' }}>{val}</div>
            <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)' }}>
              ID: {doc.document_id?.slice(0, 8)}...
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
      render: (val) =>
        val != null ? (
          <span style={{ color: val > 0.8 ? 'var(--color-success)' : 'var(--text-secondary)' }}>
            {(val * 100).toFixed(1)}%
          </span>
        ) : (
          '—'
        ),
    },
    {
      key: 'file_size',
      label: 'Size',
      render: (val) => formatBytes(val),
    },
    {
      key: 'created_at',
      label: 'Created',
      render: (val) => (val ? new Date(val).toLocaleDateString() : '—'),
    },
    {
      key: 'actions',
      label: '',
      render: (_, doc) => (
        <button
          className="action-btn-danger"
          title="Delete document"
          onClick={(e) => handleDelete(e, doc.document_id)}
        >
          <Trash2 size={16} />
        </button>
      ),
    },
  ];

  if (loading && !data) return <LoadingSpinner message="Loading documents..." />;
  if (error && !data) return <ErrorMessage message={error} onRetry={refetch} />;

  return (
    <div className="documents-page animate-fade-in">
      <div className="page-header">
        <h1>Documents</h1>
        <p>Manage and inspect all processed documents in your repository</p>
      </div>

      <div className="documents-controls card">
        <div className="filters-group">
          <div className="search-box">
            <Search size={16} />
            <input
              type="text"
              placeholder="Search filename or ID..."
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                setCurrentPage(1);
              }}
            />
          </div>

          <select
            className="filter-select"
            value={typeFilter}
            onChange={(e) => {
              setTypeFilter(e.target.value);
              setCurrentPage(1);
            }}
          >
            <option value="ALL">All Types</option>
            {distinctTypes.map((type) => (
              <option key={type} value={type}>
                {type}
              </option>
            ))}
            <option value="unclassified">Unclassified</option>
          </select>

          <select
            className="filter-select"
            value={statusFilter}
            onChange={(e) => {
              setStatusFilter(e.target.value);
              setCurrentPage(1);
            }}
          >
            <option value="ALL">All Statuses</option>
            <option value="completed">Completed</option>
            <option value="processing">Processing</option>
            <option value="failed">Failed</option>
            <option value="uploaded">Uploaded</option>
          </select>
        </div>

        <div className="actions-group">
          <button className="btn btn-secondary" onClick={refetch} title="Refresh list">
            <RefreshCw size={15} />
            Refresh
          </button>
          <button className="btn btn-primary" onClick={() => navigate('/upload')}>
            <Upload size={15} />
            Upload New
          </button>
        </div>
      </div>

      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        <DataTable
          columns={columns}
          data={paginatedDocuments}
          emptyMessage={
            searchTerm || typeFilter !== 'ALL' || statusFilter !== 'ALL'
              ? 'No documents matched your filters'
              : 'No documents in repository yet'
          }
          onRowClick={(doc) => navigate(`/documents/${doc.document_id}`)}
        />
      </div>

      {totalPages > 1 && (
        <div className="pagination-controls">
          <div>
            Showing {(currentPage - 1) * pageSize + 1} to{' '}
            {Math.min(currentPage * pageSize, filteredDocuments.length)} of{' '}
            {filteredDocuments.length} documents
          </div>
          <div className="pagination-buttons">
            <button
              className="btn-icon"
              disabled={currentPage === 1}
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
            >
              <ChevronLeft size={18} />
            </button>
            <span>
              Page {currentPage} of {totalPages}
            </span>
            <button
              className="btn-icon"
              disabled={currentPage === totalPages}
              onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
            >
              <ChevronRight size={18} />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
