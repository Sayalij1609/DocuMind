import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import {
  FileText,
  CheckCircle2,
  AlertCircle,
  AlertTriangle,
  Copy,
  Activity,
  Layers,
  FileCode,
  ShieldCheck,
  ChevronRight,
  ArrowLeft,
  ExternalLink,
  Clipboard,
  Check,
} from 'lucide-react';
import {
  getDocumentAnalysis,
  getDocumentValidation,
  getDocumentDuplicates,
  getDocumentAnomaly,
  getDocumentContent,
} from '../services/api';
import StatusBadge from '../components/StatusBadge';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorMessage from '../components/ErrorMessage';
import EmptyState from '../components/EmptyState';
import './DocumentDetailPage.css';

export default function DocumentDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [activeTab, setActiveTab] = useState('overview');
  const [copied, setCopied] = useState(false);

  // States
  const [analysis, setAnalysis] = useState(null);
  const [validation, setValidation] = useState(null);
  const [duplicates, setDuplicates] = useState(null);
  const [anomaly, setAnomaly] = useState(null);
  const [content, setContent] = useState(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let isMounted = true;

    async function loadData() {
      setLoading(true);
      setError(null);

      try {
        // Fetch core analysis first
        const analysisData = await getDocumentAnalysis(id);
        if (!isMounted) return;
        setAnalysis(analysisData);

        // Fetch other endpoints concurrently in parallel without failing the whole page if one fails
        const [valRes, dupRes, anomRes, contentRes] = await Promise.allSettled([
          getDocumentValidation(id),
          getDocumentDuplicates(id),
          getDocumentAnomaly(id),
          getDocumentContent(id),
        ]);

        if (isMounted) {
          if (valRes.status === 'fulfilled') setValidation(valRes.value);
          if (dupRes.status === 'fulfilled') setDuplicates(dupRes.value);
          if (anomRes.status === 'fulfilled') setAnomaly(anomRes.value);
          if (contentRes.status === 'fulfilled') setContent(contentRes.value);
        }
      } catch (err) {
        if (isMounted) {
          setError(err.message || 'Failed to load document analysis');
        }
      } finally {
        if (isMounted) setLoading(false);
      }
    }

    loadData();
    return () => {
      isMounted = false;
    };
  }, [id]);

  const handleCopyText = (text) => {
    if (!text) return;
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (loading) return <LoadingSpinner message="Loading document analysis..." />;
  if (error) return <ErrorMessage message={error} onRetry={() => window.location.reload()} />;
  if (!analysis) return <EmptyState message="Document not found" />;

  const fields = analysis.extraction?.fields || {};
  const fieldEntries = Object.entries(fields);

  return (
    <div className="document-detail-page animate-fade-in">
      {/* Header & Breadcrumbs */}
      <div className="detail-header">
        <div>
          <nav className="breadcrumb-nav">
            <Link to="/documents" className="breadcrumb-link">
              Documents
            </Link>
            <ChevronRight size={14} />
            <span>{analysis.filename}</span>
          </nav>

          <div className="detail-title">
            <FileText size={28} style={{ color: 'var(--accent-primary)' }} />
            <span>{analysis.filename}</span>
            <StatusBadge status={analysis.status} />
          </div>

          <div className="detail-meta-pills">
            <span className="meta-pill">
              Type: <strong style={{ textTransform: 'capitalize' }}>{analysis.document_type || 'Unclassified'}</strong>
            </span>
            {analysis.classification_confidence != null && (
              <span className="meta-pill">
                Confidence: <strong>{(analysis.classification_confidence * 100).toFixed(1)}%</strong>
              </span>
            )}
            <span className="meta-pill">ID: {analysis.document_id}</span>
            <span className="meta-pill">
              Created: {new Date(analysis.created_at).toLocaleString()}
            </span>
          </div>
        </div>

        <button className="btn btn-secondary" onClick={() => navigate('/documents')}>
          <ArrowLeft size={16} />
          Back to List
        </button>
      </div>

      {/* Tabs Navigation */}
      <div className="tabs-nav">
        <button
          className={`tab-btn ${activeTab === 'overview' ? 'active' : ''}`}
          onClick={() => setActiveTab('overview')}
        >
          <Activity size={16} />
          Overview
        </button>

        <button
          className={`tab-btn ${activeTab === 'extraction' ? 'active' : ''}`}
          onClick={() => setActiveTab('extraction')}
        >
          <Layers size={16} />
          Extraction
          <span className="tab-badge badge-count">{fieldEntries.length}</span>
        </button>

        <button
          className={`tab-btn ${activeTab === 'validation' ? 'active' : ''}`}
          onClick={() => setActiveTab('validation')}
        >
          <ShieldCheck size={16} />
          Validation
          {validation && (
            <span
              className={`tab-badge ${
                validation.error_count > 0
                  ? 'badge-alert'
                  : validation.warning_count > 0
                  ? 'badge-warn'
                  : 'badge-count'
              }`}
            >
              {validation.error_count > 0 ? `${validation.error_count} Errors` : validation.status}
            </span>
          )}
        </button>

        <button
          className={`tab-btn ${activeTab === 'duplicates' ? 'active' : ''}`}
          onClick={() => setActiveTab('duplicates')}
        >
          <Copy size={16} />
          Duplicates
          {duplicates?.has_duplicates && (
            <span className="tab-badge badge-warn">{duplicates.matches?.length || 0}</span>
          )}
        </button>

        <button
          className={`tab-btn ${activeTab === 'anomaly' ? 'active' : ''}`}
          onClick={() => setActiveTab('anomaly')}
        >
          <AlertTriangle size={16} />
          Anomaly Analysis
          {anomaly?.is_anomaly && <span className="tab-badge badge-alert">Outlier</span>}
        </button>

        <button
          className={`tab-btn ${activeTab === 'content' ? 'active' : ''}`}
          onClick={() => setActiveTab('content')}
        >
          <FileCode size={16} />
          Raw Content
        </button>
      </div>

      {/* Tab: Overview */}
      {activeTab === 'overview' && (
        <div className="overview-tab animate-fade-in">
          <div className="overview-grid">
            <div className="card">
              <h3 className="overview-section-title">
                <FileText size={18} style={{ color: 'var(--accent-primary)' }} />
                Document Metadata
              </h3>
              <div className="kv-list">
                <div className="kv-item">
                  <span className="kv-key">Document ID</span>
                  <span className="kv-val" style={{ fontFamily: 'monospace' }}>
                    {analysis.document_id}
                  </span>
                </div>
                <div className="kv-item">
                  <span className="kv-key">File Format</span>
                  <span className="kv-val">{analysis.file_type || '—'}</span>
                </div>
                <div className="kv-item">
                  <span className="kv-key">File Size</span>
                  <span className="kv-val">
                    {analysis.file_size ? `${(analysis.file_size / 1024).toFixed(1)} KB` : '—'}
                  </span>
                </div>
                <div className="kv-item">
                  <span className="kv-key">Processing Status</span>
                  <StatusBadge status={analysis.status} />
                </div>
              </div>
            </div>

            <div className="card">
              <h3 className="overview-section-title">
                <Activity size={18} style={{ color: 'var(--accent-secondary)' }} />
                Classification
              </h3>
              <div className="kv-list">
                <div className="kv-item">
                  <span className="kv-key">Predicted Class</span>
                  <span className="kv-val" style={{ textTransform: 'capitalize', fontWeight: 600 }}>
                    {analysis.document_type || 'Unclassified'}
                  </span>
                </div>
                <div className="kv-item">
                  <span className="kv-key">Confidence</span>
                  <span className="kv-val">
                    {analysis.classification_confidence != null
                      ? `${(analysis.classification_confidence * 100).toFixed(1)}%`
                      : '—'}
                  </span>
                </div>
                <div className="kv-item">
                  <span className="kv-key">Extraction Method</span>
                  <span className="kv-val">
                    {analysis.extraction?.extraction_method || 'Standard (Rule/Regex)'}
                  </span>
                </div>
                <div className="kv-item">
                  <span className="kv-key">Fields Extracted</span>
                  <span className="kv-val">{fieldEntries.length}</span>
                </div>
              </div>
            </div>

            <div className="card">
              <h3 className="overview-section-title">
                <ShieldCheck size={18} style={{ color: 'var(--color-success)' }} />
                Quality & Compliance
              </h3>
              <div className="kv-list">
                <div className="kv-item">
                  <span className="kv-key">Validation Status</span>
                  <StatusBadge
                    status={
                      analysis.validation_status === 'VALID'
                        ? 'valid'
                        : analysis.validation_status === 'INVALID'
                        ? 'invalid'
                        : analysis.validation_status === 'WARNING'
                        ? 'warning'
                        : 'pending'
                    }
                  />
                </div>
                <div className="kv-item">
                  <span className="kv-key">Validation Failures</span>
                  <span
                    className="kv-val"
                    style={{
                      color:
                        analysis.validation_error_count > 0
                          ? 'var(--color-error)'
                          : 'var(--text-primary)',
                    }}
                  >
                    {analysis.validation_error_count ?? 0}
                  </span>
                </div>
                <div className="kv-item">
                  <span className="kv-key">Duplicate Detected</span>
                  <StatusBadge
                    status={analysis.has_duplicates ? 'duplicate' : 'normal'}
                    label={analysis.has_duplicates ? 'Yes' : 'No'}
                  />
                </div>
                <div className="kv-item">
                  <span className="kv-key">Anomaly Assessment</span>
                  <StatusBadge
                    status={analysis.is_anomaly ? 'anomaly' : 'normal'}
                    label={analysis.is_anomaly ? 'Anomaly' : 'Normal'}
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tab: Extraction */}
      {activeTab === 'extraction' && (
        <div className="extraction-tab card animate-fade-in" style={{ padding: 0 }}>
          {fieldEntries.length === 0 ? (
            <EmptyState message="No fields were extracted for this document." />
          ) : (
            <table className="fields-table">
              <thead>
                <tr>
                  <th>Field</th>
                  <th>Extracted Value</th>
                  <th>Confidence</th>
                  <th>Source</th>
                </tr>
              </thead>
              <tbody>
                {fieldEntries.map(([name, field]) => (
                  <tr key={name}>
                    <td className="field-key">{name.replace(/_/g, ' ')}</td>
                    <td>
                      <span className="field-val-box">
                        {field?.value !== null && field?.value !== undefined
                          ? String(field.value)
                          : 'null'}
                      </span>
                    </td>
                    <td>
                      <div className="confidence-meter">
                        <div className="meter-bar">
                          <div
                            className="meter-fill"
                            style={{
                              width: `${(field?.confidence || 0) * 100}%`,
                              background:
                                (field?.confidence || 0) > 0.8
                                  ? 'var(--color-success)'
                                  : 'var(--color-warning)',
                            }}
                          />
                        </div>
                        <span style={{ fontSize: 'var(--font-size-xs)' }}>
                          {((field?.confidence || 0) * 100).toFixed(0)}%
                        </span>
                      </div>
                    </td>
                    <td>
                      <span className="meta-pill">{field?.source || 'heuristic'}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {/* Tab: Validation */}
      {activeTab === 'validation' && (
        <div className="validation-tab animate-fade-in">
          {!validation || !validation.results || validation.results.length === 0 ? (
            <div className="card">
              <EmptyState message="No validation rules executed for this document type." />
            </div>
          ) : (
            <div className="rules-list">
              {validation.results.map((rule, idx) => {
                const isPass = rule.status === 'PASS';
                const isFail = rule.status === 'FAIL';
                const isWarn = rule.status === 'WARN';

                return (
                  <div
                    key={idx}
                    className={`rule-item ${isPass ? 'pass' : isFail ? 'fail' : 'warn'}`}
                  >
                    {isPass && <CheckCircle2 size={20} style={{ color: 'var(--color-success)' }} />}
                    {isFail && <AlertCircle size={20} style={{ color: 'var(--color-error)' }} />}
                    {isWarn && <AlertTriangle size={20} style={{ color: 'var(--color-warning)' }} />}

                    <div className="rule-body">
                      <div className="rule-title-row">
                        <span className="rule-name">{rule.rule_name}</span>
                        <StatusBadge
                          status={isPass ? 'valid' : isFail ? 'invalid' : 'warning'}
                          label={rule.status}
                        />
                      </div>
                      <p className="rule-desc">{rule.message}</p>
                      {rule.details && Object.keys(rule.details).length > 0 && (
                        <div
                          style={{
                            marginTop: '8px',
                            background: 'var(--bg-tertiary)',
                            padding: '6px 10px',
                            borderRadius: 'var(--radius-sm)',
                            fontSize: 'var(--font-size-xs)',
                            fontFamily: 'monospace',
                          }}
                        >
                          {JSON.stringify(rule.details)}
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* Tab: Duplicates */}
      {activeTab === 'duplicates' && (
        <div className="duplicates-tab animate-fade-in">
          <div className="card">
            <h3 className="overview-section-title">
              <Copy size={18} style={{ color: 'var(--accent-primary)' }} />
              Similarity & Duplication Analysis
            </h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: 'var(--font-size-sm)', marginBottom: 'var(--space-4)' }}>
              Evaluated using TF-IDF cosine vector matching against existing repository documents of the same category.
            </p>

            {!duplicates || !duplicates.matches || duplicates.matches.length === 0 ? (
              <EmptyState message="No duplicate matches found. This document is unique." />
            ) : (
              <div className="rules-list">
                {duplicates.matches.map((match, idx) => (
                  <div key={idx} className="rule-item warn">
                    <Copy size={20} style={{ color: 'var(--color-warning)' }} />
                    <div className="rule-body">
                      <div className="rule-title-row">
                        <span className="rule-name">
                          Matched Document: {match.matched_document_id}
                        </span>
                        <span className="meta-pill" style={{ textTransform: 'uppercase' }}>
                          {match.duplicate_type}
                        </span>
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '8px' }}>
                        <span style={{ fontSize: 'var(--font-size-sm)', color: 'var(--text-secondary)' }}>
                          Similarity Score: <strong>{(match.similarity_score * 100).toFixed(2)}%</strong>
                        </span>
                        <button
                          className="btn btn-secondary"
                          style={{ padding: '4px 10px', fontSize: 'var(--font-size-xs)' }}
                          onClick={() => navigate(`/documents/${match.matched_document_id}`)}
                        >
                          View Document
                          <ExternalLink size={12} />
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Tab: Anomaly Analysis */}
      {activeTab === 'anomaly' && (
        <div className="anomaly-tab animate-fade-in">
          <div className="card" style={{ marginBottom: 'var(--space-6)' }}>
            <h3 className="overview-section-title">
              <AlertTriangle size={18} style={{ color: 'var(--color-anomaly)' }} />
              Isolation Forest Evaluation
            </h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: 'var(--font-size-sm)', marginBottom: 'var(--space-4)' }}>
              Structural and numerical anomaly detection identifying mathematical outliers in extracted features.
            </p>

            <div className="overview-grid" style={{ marginBottom: 0 }}>
              <div className="card" style={{ background: 'var(--bg-secondary)' }}>
                <span className="kv-key">Anomaly Status</span>
                <div style={{ marginTop: '8px' }}>
                  <StatusBadge
                    status={anomaly?.is_anomaly ? 'anomaly' : 'normal'}
                    label={anomaly?.is_anomaly ? 'Flagged Anomaly' : 'Normal Document'}
                  />
                </div>
              </div>

              <div className="card" style={{ background: 'var(--bg-secondary)' }}>
                <span className="kv-key">Anomaly Score</span>
                <div style={{ marginTop: '8px', fontSize: 'var(--font-size-xl)', fontWeight: 700 }}>
                  {anomaly?.anomaly_score != null ? anomaly.anomaly_score : '—'}
                </div>
              </div>

              <div className="card" style={{ background: 'var(--bg-secondary)' }}>
                <span className="kv-key">Decision Function Score</span>
                <div style={{ marginTop: '8px', fontSize: 'var(--font-size-xl)', fontWeight: 700 }}>
                  {anomaly?.decision_function_score != null ? anomaly.decision_function_score : '—'}
                </div>
              </div>
            </div>
          </div>

          {/* Features Table */}
          {anomaly?.features && Object.keys(anomaly.features).length > 0 && (
            <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
              <div style={{ padding: 'var(--space-4) var(--space-5)', borderBottom: '1px solid var(--surface-glass-border)' }}>
                <h4 style={{ fontSize: 'var(--font-size-sm)', color: 'var(--text-secondary)' }}>
                  Evaluated Feature Vectors
                </h4>
              </div>
              <table className="fields-table">
                <thead>
                  <tr>
                    <th>Feature Name</th>
                    <th>Value</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(anomaly.features).map(([fKey, fVal]) => (
                    <tr key={fKey}>
                      <td className="field-key">{fKey.replace(/_/g, ' ')}</td>
                      <td>
                        <span className="field-val-box">
                          {typeof fVal === 'number' ? fVal.toLocaleString() : String(fVal)}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Tab: Content */}
      {activeTab === 'content' && (
        <div className="content-tab animate-fade-in">
          <div className="card">
            <div className="content-header">
              <h3 className="overview-section-title" style={{ margin: 0 }}>
                <FileCode size={18} style={{ color: 'var(--accent-primary)' }} />
                Cleaned OCR Text
              </h3>
              <button
                className="btn btn-secondary"
                style={{ padding: '6px 12px', fontSize: 'var(--font-size-xs)' }}
                onClick={() => handleCopyText(content?.cleaned_text || content?.raw_text)}
              >
                {copied ? <Check size={14} /> : <Clipboard size={14} />}
                {copied ? 'Copied' : 'Copy Text'}
              </button>
            </div>

            <div className="text-viewer">
              {content?.cleaned_text || content?.raw_text || 'No extracted text found for this document.'}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
