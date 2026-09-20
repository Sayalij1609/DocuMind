import { useState, useEffect, useRef } from 'react';
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
  Sparkles,
  Bot,
  Send,
  RefreshCw,
  Tag,
  ArrowRight,
  Calculator,
  Key,
  X,
  MessageSquare,
} from 'lucide-react';
import {
  getDocumentAnalysis,
  getDocumentValidation,
  getDocumentDuplicates,
  getDocumentAnomaly,
  getDocumentContent,
  askDocumentQuestion,
  reanalyzeDocument,
  getAIStatus,
  updateAIConfig,
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

  // AI Q&A states
  const [qaMessages, setQaMessages] = useState([]);
  const [qaInput, setQaInput] = useState('');
  const [qaLoading, setQaLoading] = useState(false);
  const qaEndRef = useRef(null);

  // AI Config states
  const [showApiKeyDialog, setShowApiKeyDialog] = useState(false);
  const [apiKeyInput, setApiKeyInput] = useState('');
  const [aiStatus, setAiStatus] = useState(null);
  const [reanalyzing, setReanalyzing] = useState(false);

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
        const [valRes, dupRes, anomRes, contentRes, aiRes] = await Promise.allSettled([
          getDocumentValidation(id),
          getDocumentDuplicates(id),
          getDocumentAnomaly(id),
          getDocumentContent(id),
          getAIStatus(),
        ]);

        if (isMounted) {
          if (valRes.status === 'fulfilled') setValidation(valRes.value);
          if (dupRes.status === 'fulfilled') setDuplicates(dupRes.value);
          if (anomRes.status === 'fulfilled') setAnomaly(anomRes.value);
          if (contentRes.status === 'fulfilled') setContent(contentRes.value);
          if (aiRes.status === 'fulfilled') setAiStatus(aiRes.value);
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

  // Auto-scroll Q&A
  useEffect(() => {
    qaEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [qaMessages]);

  const handleCopyText = (text) => {
    if (!text) return;
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleAskQuestion = async () => {
    if (!qaInput.trim() || qaLoading) return;

    const question = qaInput.trim();
    setQaInput('');
    setQaMessages(prev => [...prev, { role: 'user', text: question }]);
    setQaLoading(true);

    try {
      const result = await askDocumentQuestion(id, question);
      setQaMessages(prev => [...prev, {
        role: 'assistant',
        text: result.answer,
        citations: result.citations || [],
        method: result.method,
      }]);
    } catch {
      setQaMessages(prev => [...prev, {
        role: 'assistant',
        text: 'Sorry, I was unable to process your question. Please check your API key configuration and try again.',
        error: true,
      }]);
    } finally {
      setQaLoading(false);
    }
  };

  const handleReanalyze = async () => {
    setReanalyzing(true);
    try {
      const result = await reanalyzeDocument(id);
      // Refresh the full analysis
      const newAnalysis = await getDocumentAnalysis(id);
      setAnalysis(newAnalysis);
    } catch {
      // Silently fail — user can try again
    } finally {
      setReanalyzing(false);
    }
  };

  const handleSaveApiKey = async () => {
    if (!apiKeyInput.trim()) return;
    try {
      const status = await updateAIConfig(apiKeyInput.trim());
      setAiStatus(status);
      setShowApiKeyDialog(false);
      setApiKeyInput('');
    } catch {
      // Silently fail
    }
  };

  if (loading) return <LoadingSpinner message="Loading document analysis..." />;
  if (error) return <ErrorMessage message={error} onRetry={() => window.location.reload()} />;
  if (!analysis) return <EmptyState message="Document not found" />;

  const fields = analysis.extraction?.fields || {};
  const fieldEntries = Object.entries(fields);

  // AI Analysis data
  const ai = analysis.ai_analysis || {};
  const aiEntities = ai.entities || {};
  const aiRelationships = ai.relationships || [];
  const aiLineItems = ai.line_items || [];
  const aiFinValidation = ai.financial_validation || {};
  const hasAIAnalysis = !!ai.executive_summary;

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

        <div className="detail-header-actions">
          <button
            className="btn btn-accent-outline"
            onClick={() => setShowApiKeyDialog(true)}
            title="Configure AI API Key"
          >
            <Key size={15} />
            {aiStatus?.configured ? 'AI Active' : 'Configure AI'}
          </button>
          <button
            className="btn btn-accent"
            onClick={handleReanalyze}
            disabled={reanalyzing}
            title="Re-run AI Analysis"
          >
            <RefreshCw size={15} className={reanalyzing ? 'spin-animation' : ''} />
            {reanalyzing ? 'Analyzing...' : 'Re-Analyze'}
          </button>
          <button className="btn btn-secondary" onClick={() => navigate('/documents')}>
            <ArrowLeft size={16} />
            Back to List
          </button>
        </div>
      </div>

      {/* API Key Dialog */}
      {showApiKeyDialog && (
        <div className="dialog-overlay animate-fade-in" onClick={() => setShowApiKeyDialog(false)}>
          <div className="dialog-box" onClick={e => e.stopPropagation()}>
            <div className="dialog-header">
              <h3><Key size={18} /> Configure Groq API Key</h3>
              <button className="dialog-close" onClick={() => setShowApiKeyDialog(false)}>
                <X size={18} />
              </button>
            </div>
            <p className="dialog-desc">
              Enter your Groq API key to enable AI-powered document analysis, semantic entity extraction, and intelligent Q&A. Get your key at{' '}
              <a href="https://console.groq.com" target="_blank" rel="noopener noreferrer">console.groq.com</a>.
            </p>
            <div className="dialog-input-row">
              <input
                type="password"
                className="dialog-input"
                placeholder="gsk_..."
                value={apiKeyInput}
                onChange={e => setApiKeyInput(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && handleSaveApiKey()}
              />
              <button className="btn btn-accent" onClick={handleSaveApiKey}>
                Save Key
              </button>
            </div>
            {aiStatus && (
              <div className={`dialog-status ${aiStatus.configured ? 'active' : ''}`}>
                <span className={`status-dot ${aiStatus.configured ? 'dot-active' : 'dot-inactive'}`} />
                {aiStatus.configured
                  ? `AI Active — ${aiStatus.model} (${aiStatus.source})`
                  : 'AI not configured — using local heuristic engine'}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Executive Summary Hero */}
      {hasAIAnalysis && (
        <div className="ai-summary-hero animate-fade-in">
          <div className="ai-hero-badge">
            <Sparkles size={14} />
            AI Analysis — {ai.analysis_method === 'groq_llm' ? 'Groq LLM' : 'Local Heuristic'}
          </div>
          <p className="ai-hero-text">{ai.executive_summary}</p>
          {ai.risk_narrative && ai.risk_narrative !== 'No issues detected' && (
            <div className="ai-hero-risk">
              <AlertTriangle size={14} />
              <span>{ai.risk_narrative}</span>
            </div>
          )}
        </div>
      )}

      {/* Semantic Relationship Badges */}
      {aiRelationships.length > 0 && (
        <div className="semantic-badges-row animate-fade-in">
          {aiRelationships.map((rel, i) => (
            <div key={i} className="semantic-badge">
              <span className="sem-entity">{rel.entity}</span>
              <ArrowRight size={12} className="sem-arrow" />
              <span className="sem-role">{rel.role}</span>
            </div>
          ))}
        </div>
      )}

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

        {aiLineItems.length > 0 && (
          <button
            className={`tab-btn ${activeTab === 'line-items' ? 'active' : ''}`}
            onClick={() => setActiveTab('line-items')}
          >
            <Tag size={16} />
            Line Items
            <span className="tab-badge badge-count">{aiLineItems.length}</span>
          </button>
        )}

        {Object.keys(aiFinValidation).length > 0 && (
          <button
            className={`tab-btn ${activeTab === 'finance' ? 'active' : ''}`}
            onClick={() => setActiveTab('finance')}
          >
            <Calculator size={16} />
            Math Check
            {aiFinValidation.is_valid === true && (
              <span className="tab-badge badge-count">✓</span>
            )}
            {aiFinValidation.is_valid === false && (
              <span className="tab-badge badge-alert">✗</span>
            )}
          </button>
        )}

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
          Anomaly
          {anomaly?.is_anomaly && <span className="tab-badge badge-alert">Outlier</span>}
        </button>

        <button
          className={`tab-btn ${activeTab === 'copilot' ? 'active' : ''}`}
          onClick={() => setActiveTab('copilot')}
        >
          <MessageSquare size={16} />
          AI Copilot
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

          {/* AI Entities Overview */}
          {hasAIAnalysis && (
            <div className="ai-entities-overview card">
              <h3 className="overview-section-title">
                <Sparkles size={18} style={{ color: 'var(--accent-primary)' }} />
                Semantic Entity Map
              </h3>
              <div className="entities-grid">
                {/* Parties */}
                {(aiEntities.parties || []).length > 0 && (
                  <div className="entity-section">
                    <h4 className="entity-section-label">Parties</h4>
                    {aiEntities.parties.map((p, i) => (
                      <div key={i} className="entity-card-mini">
                        <span className="entity-role-tag">{p.role}</span>
                        <span className="entity-name">{p.name || '—'}</span>
                        {p.address && <span className="entity-detail">{p.address}</span>}
                        {p.tax_id && <span className="entity-detail">Tax ID: {p.tax_id}</span>}
                      </div>
                    ))}
                  </div>
                )}

                {/* Identifiers */}
                {(aiEntities.identifiers || []).filter(i => i.value).length > 0 && (
                  <div className="entity-section">
                    <h4 className="entity-section-label">Identifiers</h4>
                    {aiEntities.identifiers.filter(i => i.value).map((ident, i) => (
                      <div key={i} className="entity-card-mini">
                        <span className="entity-role-tag">{ident.type?.replace(/_/g, ' ')}</span>
                        <span className="entity-name mono">{ident.value}</span>
                      </div>
                    ))}
                  </div>
                )}

                {/* Dates */}
                {(aiEntities.dates || []).filter(d => d.value).length > 0 && (
                  <div className="entity-section">
                    <h4 className="entity-section-label">Dates</h4>
                    {aiEntities.dates.filter(d => d.value).map((d, i) => (
                      <div key={i} className="entity-card-mini">
                        <span className="entity-role-tag">{d.type?.replace(/_/g, ' ')}</span>
                        <span className="entity-name">{d.value}</span>
                      </div>
                    ))}
                  </div>
                )}

                {/* Financials */}
                {aiEntities.financials && Object.keys(aiEntities.financials).length > 0 && (
                  <div className="entity-section">
                    <h4 className="entity-section-label">Financials</h4>
                    {Object.entries(aiEntities.financials).filter(([, v]) => v != null).map(([k, v]) => (
                      <div key={k} className="entity-card-mini">
                        <span className="entity-role-tag">{k.replace(/_/g, ' ')}</span>
                        <span className="entity-name mono">
                          {typeof v === 'number' ? v.toLocaleString() : String(v)}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}
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
                {fieldEntries
                  .filter(([name]) => name !== '__ai_analysis__')
                  .map(([name, field]) => (
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

      {/* Tab: Line Items */}
      {activeTab === 'line-items' && (
        <div className="line-items-tab card animate-fade-in" style={{ padding: 0 }}>
          {aiLineItems.length === 0 ? (
            <EmptyState message="No line items extracted." />
          ) : (
            <table className="fields-table line-items-table">
              <thead>
                <tr>
                  <th>#</th>
                  <th>Description</th>
                  <th style={{ textAlign: 'right' }}>Qty</th>
                  <th style={{ textAlign: 'right' }}>Unit Price</th>
                  <th style={{ textAlign: 'right' }}>Amount</th>
                </tr>
              </thead>
              <tbody>
                {aiLineItems.map((item, idx) => (
                  <tr key={idx}>
                    <td style={{ color: 'var(--text-muted)' }}>{idx + 1}</td>
                    <td>{item.description || '—'}</td>
                    <td style={{ textAlign: 'right', fontFamily: 'monospace' }}>
                      {item.quantity ?? '—'}
                    </td>
                    <td style={{ textAlign: 'right', fontFamily: 'monospace' }}>
                      {item.unit_price != null ? Number(item.unit_price).toLocaleString() : '—'}
                    </td>
                    <td style={{ textAlign: 'right', fontWeight: 600, fontFamily: 'monospace' }}>
                      {item.amount != null ? Number(item.amount).toLocaleString() : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {/* Tab: Financial Reconciler */}
      {activeTab === 'finance' && (
        <div className="finance-tab animate-fade-in">
          <div className="card finance-card">
            <h3 className="overview-section-title">
              <Calculator size={18} style={{ color: 'var(--accent-primary)' }} />
              Arithmetic Validation
            </h3>

            <div className="finance-grid">
              <div className="finance-row">
                <span>Subtotal</span>
                <span className="mono">{aiFinValidation.subtotal ?? '—'}</span>
              </div>
              <div className="finance-row">
                <span>+ Tax</span>
                <span className="mono">{aiFinValidation.tax ?? '—'}</span>
              </div>
              <div className="finance-row">
                <span>− Discount</span>
                <span className="mono">{aiFinValidation.discount ?? '—'}</span>
              </div>
              <div className="finance-divider" />
              <div className="finance-row total-row">
                <span>Computed Total</span>
                <span className="mono">{aiFinValidation.computed_total ?? '—'}</span>
              </div>
              <div className="finance-row total-row">
                <span>Stated Total</span>
                <span className="mono">{aiFinValidation.stated_total ?? '—'}</span>
              </div>
              <div className="finance-divider" />
              <div className="finance-row verdict-row">
                <span>Verdict</span>
                <span>
                  {aiFinValidation.is_valid === true && (
                    <span className="verdict-pass"><CheckCircle2 size={16} /> Match — No Discrepancy</span>
                  )}
                  {aiFinValidation.is_valid === false && (
                    <span className="verdict-fail">
                      <AlertCircle size={16} /> Discrepancy: {aiFinValidation.discrepancy}
                    </span>
                  )}
                  {aiFinValidation.is_valid == null && (
                    <span className="verdict-unknown">Insufficient data</span>
                  )}
                </span>
              </div>
            </div>

            {aiFinValidation.notes && (
              <p className="finance-notes">{aiFinValidation.notes}</p>
            )}
          </div>
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

      {/* Tab: AI Copilot */}
      {activeTab === 'copilot' && (
        <div className="copilot-tab animate-fade-in">
          <div className="copilot-card card">
            <div className="copilot-header">
              <Bot size={20} />
              <h3>DocuMind AI Copilot</h3>
              <span className="copilot-badge">
                {aiStatus?.configured ? 'Groq LLM Active' : 'Local Mode'}
              </span>
            </div>

            <div className="copilot-messages">
              {qaMessages.length === 0 && (
                <div className="copilot-welcome">
                  <Sparkles size={24} className="copilot-welcome-icon" />
                  <p>Ask anything about this document.</p>
                  <div className="copilot-suggestions">
                    {[
                      'What is the total amount?',
                      'Who is the vendor?',
                      'What is the due date?',
                      'Summarize the key details',
                    ].map((q, i) => (
                      <button
                        key={i}
                        className="copilot-suggestion-btn"
                        onClick={() => {
                          setQaInput(q);
                        }}
                      >
                        {q}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {qaMessages.map((msg, idx) => (
                <div key={idx} className={`copilot-msg ${msg.role}`}>
                  {msg.role === 'assistant' && (
                    <div className="copilot-msg-avatar">
                      <Bot size={16} />
                    </div>
                  )}
                  <div className={`copilot-msg-bubble ${msg.error ? 'error-bubble' : ''}`}>
                    {msg.text}
                    {msg.citations && msg.citations.length > 0 && (
                      <div className="copilot-citations">
                        {msg.citations.map((c, ci) => (
                          <span key={ci} className="copilot-citation">{c}</span>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              ))}

              {qaLoading && (
                <div className="copilot-msg assistant">
                  <div className="copilot-msg-avatar">
                    <Bot size={16} />
                  </div>
                  <div className="copilot-msg-bubble typing">
                    <span className="typing-dot" />
                    <span className="typing-dot" />
                    <span className="typing-dot" />
                  </div>
                </div>
              )}

              <div ref={qaEndRef} />
            </div>

            <div className="copilot-input-row">
              <input
                type="text"
                className="copilot-input"
                placeholder="Ask a question about this document..."
                value={qaInput}
                onChange={e => setQaInput(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && handleAskQuestion()}
                disabled={qaLoading}
              />
              <button
                className="btn btn-accent copilot-send-btn"
                onClick={handleAskQuestion}
                disabled={qaLoading || !qaInput.trim()}
              >
                <Send size={16} />
              </button>
            </div>
          </div>
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
