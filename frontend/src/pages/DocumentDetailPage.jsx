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
  Sparkles,
  RefreshCw,
  Tag,
  ArrowRight,
  Calculator,
  Key,
  X,
  Info,
  Lightbulb,
  Play,
  Clock,
  FileSpreadsheet,
  FileCheck,
  Zap,
  Home,
  Search,
} from 'lucide-react';
import {
  getDocumentAnalysis,
  getDocumentValidation,
  getDocumentDuplicates,
  getDocumentAnomaly,
  getDocumentContent,
  reanalyzeDocument,
  getAIStatus,
  updateAIConfig,
  startDocumentProcessing,
} from '../services/api';
import StatusBadge from '../components/StatusBadge';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorMessage from '../components/ErrorMessage';
import EmptyState from '../components/EmptyState';
import './DocumentDetailPage.css';

const formatRupees = (val) => {
  if (val == null || val === '') return '—';
  if (typeof val === 'number') return `₹${val.toLocaleString('en-IN')}`;
  const str = String(val).trim();
  if (str.startsWith('₹')) return str;
  const num = parseFloat(str.replace(/[^0-9.-]+/g, ''));
  if (!isNaN(num)) return `₹${num.toLocaleString('en-IN')}`;
  return str.replace(/\$/g, '₹');
};

const formatFieldValue = (name, val) => {
  if (val === null || val === undefined) return 'null';
  const str = String(val);
  const isMoney = /amount|total|subtotal|tax|price|fee|balance/i.test(name);
  if (isMoney && !str.includes('₹') && !str.includes('INR')) {
    const num = parseFloat(str.replace(/[^0-9.-]+/g, ''));
    if (!isNaN(num)) {
      return `₹${num.toLocaleString('en-IN')}`;
    }
  }
  return str.replace(/\$/g, '₹');
};

export default function DocumentDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [activeTab, setActiveTab] = useState('overview');
  const [copied, setCopied] = useState(false);
  const [copiedFieldName, setCopiedFieldName] = useState(null);
  const [fieldSearch, setFieldSearch] = useState('');

  // Core States
  const [analysis, setAnalysis] = useState(null);
  const [validation, setValidation] = useState(null);
  const [duplicates, setDuplicates] = useState(null);
  const [anomaly, setAnomaly] = useState(null);
  const [content, setContent] = useState(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [startingAnalysis, setStartingAnalysis] = useState(false);

  // AI Config states
  const [showApiKeyDialog, setShowApiKeyDialog] = useState(false);
  const [apiKeyInput, setApiKeyInput] = useState('');
  const [aiStatus, setAiStatus] = useState(null);
  const [reanalyzing, setReanalyzing] = useState(false);

  // Initial Data Load
  useEffect(() => {
    let isMounted = true;

    async function loadData() {
      setLoading(true);
      setError(null);

      try {
        const analysisData = await getDocumentAnalysis(id);
        if (!isMounted) return;
        setAnalysis(analysisData);

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

  // Polling when document is in "processing" state
  useEffect(() => {
    if (analysis?.status !== 'processing') return;

    const interval = setInterval(async () => {
      try {
        const updated = await getDocumentAnalysis(id);
        if (updated.status !== 'processing') {
          setAnalysis(updated);
          const [valRes, dupRes, anomRes, contentRes] = await Promise.allSettled([
            getDocumentValidation(id),
            getDocumentDuplicates(id),
            getDocumentAnomaly(id),
            getDocumentContent(id),
          ]);
          if (valRes.status === 'fulfilled') setValidation(valRes.value);
          if (dupRes.status === 'fulfilled') setDuplicates(dupRes.value);
          if (anomRes.status === 'fulfilled') setAnomaly(anomRes.value);
          if (contentRes.status === 'fulfilled') setContent(contentRes.value);
        }
      } catch {
        // Silently retry on next tick
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [analysis?.status, id]);

  const handleCopyText = (text) => {
    if (!text) return;
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleCopyFieldValue = (name, text) => {
    if (!text) return;
    navigator.clipboard.writeText(String(text));
    setCopiedFieldName(name);
    setTimeout(() => setCopiedFieldName(null), 2000);
  };

  const handleStartAnalysis = async () => {
    setStartingAnalysis(true);
    setError(null);
    try {
      await startDocumentProcessing(id);
      setAnalysis((prev) => ({ ...prev, status: 'processing' }));
    } catch (err) {
      setError(err.message || 'Failed to start document processing');
    } finally {
      setStartingAnalysis(false);
    }
  };

  const handleReanalyze = async () => {
    setReanalyzing(true);
    try {
      await reanalyzeDocument(id);
      const newAnalysis = await getDocumentAnalysis(id);
      setAnalysis(newAnalysis);
    } catch {
      // Silently fail
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

  // Filtered fields based on search query
  const filteredFieldEntries = fieldEntries
    .filter(([name]) => name !== '__ai_analysis__')
    .filter(([name, f]) => {
      if (!fieldSearch.trim()) return true;
      const q = fieldSearch.toLowerCase();
      const valStr = String(f?.value || '').toLowerCase();
      return name.toLowerCase().includes(q) || valStr.includes(q);
    });

  // AI Analysis data
  const ai = analysis.ai_analysis || {};
  const aiEntities = ai.entities || {};
  const aiRelationships = ai.relationships || [];
  const aiLineItems = ai.line_items || [];
  const aiFinValidation = ai.financial_validation || {};
  const hasAIAnalysis = !!ai.executive_summary;
  const aiInsights = ai.insights || [];
  const aiValidationSummary = ai.validation_summary || '';
  const aiDuplicateAssessment = ai.duplicate_assessment || '';
  const aiAnomalyAssessment = ai.anomaly_assessment || '';

  // Computed Audit Values
  const totalAmountVal =
    aiEntities.financials?.total ??
    aiEntities.financials?.stated_total ??
    analysis.extraction?.fields?.total_amount?.value ??
    analysis.extraction?.fields?.total?.value ??
    analysis.extraction?.fields?.amount?.value ??
    null;

  const invoiceNoVal =
    aiEntities.identifiers?.find((i) => /invoice/i.test(i.type))?.value ??
    analysis.extraction?.fields?.invoice_number?.value ??
    analysis.extraction?.fields?.invoice_id?.value ??
    null;

  const poNoVal =
    aiEntities.identifiers?.find((i) => /po|purchase/i.test(i.type))?.value ??
    analysis.extraction?.fields?.po_number?.value ??
    analysis.extraction?.fields?.purchase_order?.value ??
    null;

  const vendorVal =
    aiEntities.parties?.find((p) => /vendor|issuer/i.test(p.role))?.name ??
    analysis.extraction?.fields?.vendor_name?.value ??
    analysis.extraction?.fields?.merchant_name?.value ??
    null;

  const primaryDateVal =
    aiEntities.dates?.[0]?.value ??
    analysis.extraction?.fields?.invoice_date?.value ??
    analysis.extraction?.fields?.date?.value ??
    null;

  const isUploadedOnly = analysis.status === 'uploaded';
  const isProcessing = analysis.status === 'processing';

  return (
    <div className="document-detail-page animate-fade-in">
      {/* Top Header & Breadcrumbs */}
      <div className="detail-header">
        <div className="detail-header-left">
          <nav className="breadcrumb-nav">
            <Link to="/documents" className="breadcrumb-link">
              Documents
            </Link>
            <ChevronRight size={14} />
            <span className="breadcrumb-current">{analysis.filename}</span>
          </nav>

          <div className="detail-title-row">
            <div className="detail-file-icon">
              <FileText size={24} />
            </div>
            <h1 className="detail-filename" title={analysis.filename}>
              {analysis.filename}
            </h1>
            <StatusBadge status={analysis.status} />
          </div>

          <div className="detail-meta-row">
            <span className="meta-pill">
              Type: <strong>{(analysis.document_type || 'Unclassified').toUpperCase()}</strong>
            </span>
            <span className="meta-pill">
              Format: <strong>{(analysis.file_type || 'PDF').toUpperCase()}</strong>
            </span>
            <span className="meta-pill">
              Size: <strong>{analysis.file_size ? `${(analysis.file_size / 1024).toFixed(1)} KB` : '—'}</strong>
            </span>
            <span className="meta-pill">
              Uploaded: <strong>{new Date(analysis.created_at).toLocaleDateString()}</strong>
            </span>
            <span className="meta-pill mono">ID: {analysis.document_id.slice(0, 12)}...</span>
          </div>
        </div>

        <div className="detail-header-actions">
          {!isUploadedOnly && !isProcessing && (
            <button
              className="btn btn-accent btn-sm"
              onClick={handleReanalyze}
              disabled={reanalyzing}
              title="Re-run Document Audit"
            >
              <RefreshCw size={14} className={reanalyzing ? 'spin-animation' : ''} />
              <span>{reanalyzing ? 'Auditing...' : 'Re-Audit'}</span>
            </button>
          )}

          <button className="btn btn-secondary btn-sm" onClick={() => navigate('/documents')} title="Back to Document List">
            <ArrowLeft size={14} />
            <span>Documents</span>
          </button>

          <Link to="/" className="btn btn-secondary btn-sm" title="Back to Home">
            <Home size={14} />
            <span>Home</span>
          </Link>
        </div>
      </div>

      {/* API Key Dialog Modal */}
      {showApiKeyDialog && (
        <div className="dialog-overlay animate-fade-in" onClick={() => setShowApiKeyDialog(false)}>
          <div className="dialog-box" onClick={(e) => e.stopPropagation()}>
            <div className="dialog-header">
              <h3><Key size={18} /> Configure Groq API Key</h3>
              <button className="dialog-close" onClick={() => setShowApiKeyDialog(false)}>
                <X size={18} />
              </button>
            </div>
            <p className="dialog-desc">
              Enter your Groq API key to enable Llama-3.3-70B document analysis, semantic entity extraction, and detailed insights. Get your key at{' '}
              <a href="https://console.groq.com" target="_blank" rel="noopener noreferrer">console.groq.com</a>.
            </p>
            <div className="dialog-input-row">
              <input
                type="password"
                className="dialog-input"
                placeholder="gsk_..."
                value={apiKeyInput}
                onChange={(e) => setApiKeyInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSaveApiKey()}
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

      {/* STATE 1: DOCUMENT UPLOADED (READY FOR ANALYSIS) */}
      {isUploadedOnly && (
        <div className="staging-ready-screen card animate-fade-in">
          <div className="staging-ready-header">
            <div className="staging-ready-icon-wrap">
              <Clock size={32} className="staging-ready-icon" />
            </div>
            <div>
              <h2 className="staging-ready-title">Document Staged & Ready for Analysis</h2>
              <p className="staging-ready-subtitle">
                This document is safely stored in the repository. Click below to initiate the automated 6-point extraction and compliance audit.
              </p>
            </div>
          </div>

          <div className="staging-ready-body">
            <div className="staging-pipeline-list">
              <h4 className="staging-pipeline-heading">
                <Zap size={16} /> Pipeline Audits to be Performed:
              </h4>
              <div className="staging-pipeline-grid">
                <div className="staging-step-item">
                  <span className="step-badge">1</span>
                  <div>
                    <strong>OCR Text Extraction</strong>
                    <p>Tesseract engine normalizes raw textual layout</p>
                  </div>
                </div>
                <div className="staging-step-item">
                  <span className="step-badge">2</span>
                  <div>
                    <strong>ML Classification</strong>
                    <p>TF-IDF + SGD model predicts document class</p>
                  </div>
                </div>
                <div className="staging-step-item">
                  <span className="step-badge">3</span>
                  <div>
                    <strong>Field Extraction</strong>
                    <p>Heuristic regex extracts amounts, dates & entities</p>
                  </div>
                </div>
                <div className="staging-step-item">
                  <span className="step-badge">4</span>
                  <div>
                    <strong>Deterministic Validation</strong>
                    <p>6 enterprise business rules verify compliance</p>
                  </div>
                </div>
                <div className="staging-step-item">
                  <span className="step-badge">5</span>
                  <div>
                    <strong>Duplicate & Anomaly Check</strong>
                    <p>Isolation Forest and vector similarity scans</p>
                  </div>
                </div>
                <div className="staging-step-item">
                  <span className="step-badge">6</span>
                  <div>
                    <strong>Executive Audit Synthesis</strong>
                    <p>Generates executive summary and audit observations</p>
                  </div>
                </div>
              </div>
            </div>

            <div className="staging-ready-cta-box">
              <button
                className="btn btn-primary staging-start-cta"
                onClick={handleStartAnalysis}
                disabled={startingAnalysis}
              >
                {startingAnalysis ? (
                  <>
                    <RefreshCw size={18} className="spin-animation" />
                    <span>Initiating Pipeline...</span>
                  </>
                ) : (
                  <>
                    <Play size={16} />
                    <span>Execute Document Audit</span>
                  </>
                )}
              </button>
              <button
                className="btn btn-secondary"
                onClick={() => setShowApiKeyDialog(true)}
              >
                <Key size={14} />
                <span>{aiStatus?.configured ? 'AI Key Ready' : 'Set Groq API Key'}</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* STATE 2: PROCESSING IN PROGRESS (ACTIVE STEPPER) */}
      {isProcessing && (
        <div className="processing-progress-screen card animate-fade-in">
          <div className="processing-hero">
            <div className="processing-spinner-outer">
              <RefreshCw size={36} className="spin-animation text-accent" />
            </div>
            <h2 className="processing-title">Auditing Document in Real-Time</h2>
            <p className="processing-subtitle">
              Running OCR extraction, machine learning classification, rule validation, and audit checks.
            </p>
          </div>

          <div className="pipeline-stepper">
            <div className="stepper-step completed">
              <div className="stepper-dot"><CheckCircle2 size={16} /></div>
              <div className="stepper-content">
                <strong>1. Ingestion & Storage</strong>
                <span>File saved securely</span>
              </div>
            </div>

            <div className="stepper-step active">
              <div className="stepper-dot"><span className="pulse-dot" /></div>
              <div className="stepper-content">
                <strong>2. Layout & OCR Normalization</strong>
                <span>Tesseract extracting coordinate bounding boxes</span>
              </div>
            </div>

            <div className="stepper-step active">
              <div className="stepper-dot"><span className="pulse-dot" /></div>
              <div className="stepper-content">
                <strong>3. Classification</strong>
                <span>Categorizing document type via SGD classifier</span>
              </div>
            </div>

            <div className="stepper-step active">
              <div className="stepper-dot"><span className="pulse-dot" /></div>
              <div className="stepper-content">
                <strong>4. Field Extraction</strong>
                <span>Identifying key-value fields and financial totals</span>
              </div>
            </div>

            <div className="stepper-step active">
              <div className="stepper-dot"><span className="pulse-dot" /></div>
              <div className="stepper-content">
                <strong>5. Rule Validation</strong>
                <span>Evaluating 6 deterministic business compliance rules</span>
              </div>
            </div>

            <div className="stepper-step active">
              <div className="stepper-dot"><span className="pulse-dot" /></div>
              <div className="stepper-content">
                <strong>6. Audit Findings</strong>
                <span>Generating executive summary & audit observations</span>
              </div>
            </div>
          </div>

          <div className="processing-poll-indicator">
            <span className="poll-spinner" />
            <span>Polling analysis status every 2 seconds... Your page will automatically refresh once finished.</span>
          </div>
        </div>
      )}

      {/* STATE 3: COMPLETED ANALYSIS (AIRY, EXECUTIVE WORKSPACE) */}
      {!isUploadedOnly && !isProcessing && (
        <>
          {/* 4-Metric Audit Health Ribbon */}
          <div className="audit-health-ribbon">
            <div className="health-tile card">
              <div className="tile-icon-wrap class-icon">
                <Activity size={18} />
              </div>
              <div className="tile-content">
                <span className="tile-label">Document Classification</span>
                <strong className="tile-main-value capitalize">
                  {analysis.document_type || 'Unclassified'}
                </strong>
                {analysis.classification_confidence != null && (
                  <span className="tile-sub success">
                    {(analysis.classification_confidence * 100).toFixed(1)}% model confidence
                  </span>
                )}
              </div>
            </div>

            <div className="health-tile card">
              <div className="tile-icon-wrap field-icon">
                <Calculator size={18} />
              </div>
              <div className="tile-content">
                <span className="tile-label">Gross Financial Liability</span>
                <strong className="tile-main-value text-accent">
                  {totalAmountVal != null ? formatRupees(totalAmountVal) : '—'}
                </strong>
                <span className="tile-sub">
                  Currency: {aiEntities.financials?.currency || 'INR (₹)'}
                </span>
              </div>
            </div>

            <div className="health-tile card">
              <div className="tile-icon-wrap rule-icon">
                <ShieldCheck size={18} />
              </div>
              <div className="tile-content">
                <span className="tile-label">Deterministic Compliance</span>
                <div className="tile-status-line">
                  <StatusBadge
                    status={
                      analysis.validation_status === 'VALID'
                        ? 'valid'
                        : analysis.validation_status === 'INVALID'
                        ? 'invalid'
                        : analysis.validation_status === 'WARNING'
                        ? 'warning'
                        : 'normal'
                    }
                  />
                  <span className="tile-sub">
                    {analysis.validation_error_count ?? 0} errors
                  </span>
                </div>
              </div>
            </div>

            <div className="health-tile card">
              <div className="tile-icon-wrap anomaly-icon">
                <AlertTriangle size={18} />
              </div>
              <div className="tile-content">
                <span className="tile-label">Integrity & Risk</span>
                <strong className={`tile-main-value ${analysis.is_anomaly ? 'text-anomaly' : 'text-success'}`}>
                  {analysis.is_anomaly ? 'Outlier Flagged' : 'Normal Structure'}
                </strong>
                <span className="tile-sub">
                  {analysis.has_duplicates ? 'Duplicate Found' : 'Unique Record'}
                </span>
              </div>
            </div>
          </div>

          {/* Tabs Navigation */}
          <div className="tabs-nav">
            <button
              className={`tab-btn ${activeTab === 'overview' ? 'active' : ''}`}
              onClick={() => setActiveTab('overview')}
            >
              <Activity size={16} />
              <span>Audit Summary</span>
            </button>

            <button
              className={`tab-btn ${activeTab === 'extraction' ? 'active' : ''}`}
              onClick={() => setActiveTab('extraction')}
            >
              <Layers size={16} />
              <span>Extracted Fields</span>
              <span className="tab-badge badge-count">{fieldEntries.length}</span>
            </button>

            {aiLineItems.length > 0 && (
              <button
                className={`tab-btn ${activeTab === 'line-items' ? 'active' : ''}`}
                onClick={() => setActiveTab('line-items')}
              >
                <Tag size={16} />
                <span>Line Items</span>
                <span className="tab-badge badge-count">{aiLineItems.length}</span>
              </button>
            )}

            {Object.keys(aiFinValidation).length > 0 && (
              <button
                className={`tab-btn ${activeTab === 'finance' ? 'active' : ''}`}
                onClick={() => setActiveTab('finance')}
              >
                <Calculator size={16} />
                <span>Math Check</span>
                {aiFinValidation.is_valid === true && <span className="tab-badge badge-count">✓</span>}
                {aiFinValidation.is_valid === false && <span className="tab-badge badge-alert">✗</span>}
              </button>
            )}

            <button
              className={`tab-btn ${activeTab === 'validation' ? 'active' : ''}`}
              onClick={() => setActiveTab('validation')}
            >
              <ShieldCheck size={16} />
              <span>Validation Rules</span>
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
              <span>Duplicates</span>
              {duplicates?.has_duplicates && (
                <span className="tab-badge badge-warn">{duplicates.matches?.length || 0}</span>
              )}
            </button>

            <button
              className={`tab-btn ${activeTab === 'anomaly' ? 'active' : ''}`}
              onClick={() => setActiveTab('anomaly')}
            >
              <AlertTriangle size={16} />
              <span>Anomaly Detection</span>
              {anomaly?.is_anomaly && <span className="tab-badge badge-alert">Outlier</span>}
            </button>

            <button
              className={`tab-btn ${activeTab === 'content' ? 'active' : ''}`}
              onClick={() => setActiveTab('content')}
            >
              <FileCode size={16} />
              <span>Raw Text</span>
            </button>
          </div>

          {/* TAB 1: AUDIT SUMMARY (SPACIOUS 2-COLUMN EXECUTIVE DASHBOARD) */}
          {activeTab === 'overview' && (
            <div className="audit-overview-layout animate-fade-in">
              {/* Left Column: Briefing & Observations */}
              <div className="audit-overview-main-col">
                {/* Executive Briefing Card */}
                <div className="card audit-card-briefing">
                  <div className="audit-card-header">
                    <div className="audit-header-icon-wrap">
                      <FileCheck size={18} />
                    </div>
                    <div>
                      <h3 className="audit-card-title">Executive Audit Briefing</h3>
                      <p className="audit-card-subtitle">Automated structural evaluation and counterparty summary</p>
                    </div>
                  </div>

                  <p className="audit-narrative-text">
                    {ai.executive_summary ||
                      `Document processed and registered as ${analysis.document_type || 'unclassified'}. Structural coordinates and field data are verified against standard accounting conventions.`}
                  </p>

                  {aiRelationships.length > 0 && (
                    <div className="audit-roles-strip">
                      <span className="audit-roles-label">Detected Counterparty Roles:</span>
                      <div className="audit-roles-tags">
                        {aiRelationships.map((rel, i) => (
                          <div key={i} className="audit-role-tag">
                            <span className="role-entity">{rel.entity}</span>
                            <ArrowRight size={11} className="role-arrow" />
                            <span className="role-name">{rel.role}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                {/* Audit Findings & Observations Card */}
                <div className="card audit-card-findings">
                  <div className="audit-card-header">
                    <div className="audit-header-icon-wrap success">
                      <ShieldCheck size={18} />
                    </div>
                    <div>
                      <h3 className="audit-card-title">Audit Findings & Observations</h3>
                      <p className="audit-card-subtitle">Key compliance checkpoints, financial notes, and control recommendations</p>
                    </div>
                  </div>

                  <div className="audit-findings-list">
                    {aiInsights.length > 0 ? (
                      aiInsights.map((insight, i) => (
                        <div key={i} className="audit-finding-item">
                          <div className="finding-bullet-icon">
                            <CheckCircle2 size={15} />
                          </div>
                          <div className="finding-text">{insight}</div>
                        </div>
                      ))
                    ) : (
                      <div className="audit-finding-item">
                        <div className="finding-bullet-icon">
                          <CheckCircle2 size={15} />
                        </div>
                        <div className="finding-text">
                          Document conforms to standard layout conventions with no structural blocking errors.
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Right Column: Key Identifiers & Risk Assessment */}
              <div className="audit-overview-side-col">
                {/* Core Transaction Identifiers */}
                <div className="card audit-card-identifiers">
                  <div className="audit-card-header">
                    <div className="audit-header-icon-wrap">
                      <Layers size={18} />
                    </div>
                    <div>
                      <h3 className="audit-card-title">Transaction Identifiers</h3>
                      <p className="audit-card-subtitle">Primary financial & reference records</p>
                    </div>
                  </div>

                  <div className="audit-kv-list">
                    <div className="audit-kv-row">
                      <span className="audit-kv-key">Document Type</span>
                      <span className="audit-kv-val capitalize font-bold">{analysis.document_type || 'Unclassified'}</span>
                    </div>

                    <div className="audit-kv-row highlight-row">
                      <span className="audit-kv-key">Gross Total</span>
                      <span className="audit-kv-val currency-val">
                        {totalAmountVal != null ? formatRupees(totalAmountVal) : '—'}
                      </span>
                    </div>

                    <div className="audit-kv-row">
                      <span className="audit-kv-key">Currency</span>
                      <span className="audit-kv-val mono">{aiEntities.financials?.currency || 'INR (₹)'}</span>
                    </div>

                    <div className="audit-kv-row">
                      <span className="audit-kv-key">PO Number</span>
                      <div className="audit-val-with-copy">
                        <span className="audit-kv-val mono">{poNoVal || '—'}</span>
                        {poNoVal && (
                          <button
                            className="btn-tiny-copy"
                            title="Copy PO Number"
                            onClick={() => {
                              navigator.clipboard.writeText(poNoVal);
                              setCopiedFieldName('po');
                              setTimeout(() => setCopiedFieldName(null), 1500);
                            }}
                          >
                            {copiedFieldName === 'po' ? <Check size={12} /> : <Copy size={12} />}
                          </button>
                        )}
                      </div>
                    </div>

                    <div className="audit-kv-row">
                      <span className="audit-kv-key">Invoice Number</span>
                      <div className="audit-val-with-copy">
                        <span className="audit-kv-val mono">{invoiceNoVal || '—'}</span>
                        {invoiceNoVal && (
                          <button
                            className="btn-tiny-copy"
                            title="Copy Invoice Number"
                            onClick={() => {
                              navigator.clipboard.writeText(invoiceNoVal);
                              setCopiedFieldName('inv');
                              setTimeout(() => setCopiedFieldName(null), 1500);
                            }}
                          >
                            {copiedFieldName === 'inv' ? <Check size={12} /> : <Copy size={12} />}
                          </button>
                        )}
                      </div>
                    </div>

                    {vendorVal && (
                      <div className="audit-kv-row">
                        <span className="audit-kv-key">Vendor / Issuer</span>
                        <span className="audit-kv-val">{vendorVal}</span>
                      </div>
                    )}

                    <div className="audit-kv-row">
                      <span className="audit-kv-key">Transaction Date</span>
                      <span className="audit-kv-val">{primaryDateVal || new Date(analysis.created_at).toLocaleDateString()}</span>
                    </div>
                  </div>
                </div>

                {/* Fiscal Risk & Integrity Card */}
                <div className="card audit-card-risk">
                  <div className="audit-card-header">
                    <div className="audit-header-icon-wrap warn">
                      <AlertTriangle size={18} />
                    </div>
                    <div>
                      <h3 className="audit-card-title">Fiscal Risk & Controls</h3>
                      <p className="audit-card-subtitle">Automated disbursement controls</p>
                    </div>
                  </div>

                  <p className="audit-risk-paragraph">
                    {ai.risk_narrative || "No elevated financial or structural risks detected for this document."}
                  </p>

                  <div className="risk-badges-grid">
                    <div className="risk-badge-item">
                      <span className="risk-item-label">Outlier Scan:</span>
                      <StatusBadge
                        status={analysis.is_anomaly ? 'anomaly' : 'normal'}
                        label={analysis.is_anomaly ? 'Outlier Flagged' : 'Normal Structure'}
                      />
                    </div>
                    <div className="risk-badge-item">
                      <span className="risk-item-label">Duplicate Scan:</span>
                      <StatusBadge
                        status={analysis.has_duplicates ? 'duplicate' : 'normal'}
                        label={analysis.has_duplicates ? 'Duplicate Match' : 'Unique Record'}
                      />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 2: EXTRACTION */}
          {activeTab === 'extraction' && (
            <div className="extraction-tab card animate-fade-in">
              <div className="tab-pane-header-with-search">
                <div>
                  <h3 className="tab-pane-title">Extracted Key-Value Fields</h3>
                  <p className="tab-pane-desc">
                    Normalized deterministic field values extracted from document layout coordinates.
                  </p>
                </div>
                <div className="field-search-box">
                  <Search size={14} className="field-search-icon" />
                  <input
                    type="text"
                    placeholder="Filter fields..."
                    value={fieldSearch}
                    onChange={(e) => setFieldSearch(e.target.value)}
                    className="field-search-input"
                  />
                </div>
              </div>

              {filteredFieldEntries.length === 0 ? (
                <EmptyState message={fieldSearch ? "No fields match your search query." : "No fields were extracted for this document."} />
              ) : (
                <div className="table-responsive">
                  <table className="spacious-table">
                    <thead>
                      <tr>
                        <th>Field Name</th>
                        <th>Extracted Value</th>
                        <th>Confidence</th>
                        <th>Source</th>
                        <th style={{ textAlign: 'right', width: '60px' }}>Copy</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredFieldEntries.map(([name, field]) => (
                        <tr key={name}>
                          <td className="field-name-cell">{name.replace(/_/g, ' ')}</td>
                          <td>
                            <span className="field-value-pill">
                              {formatFieldValue(name, field?.value)}
                            </span>
                          </td>
                          <td>
                            <div className="confidence-meter-wide">
                              <div className="meter-track">
                                <div
                                  className="meter-fill-bar"
                                  style={{
                                    width: `${(field?.confidence || 0) * 100}%`,
                                    background:
                                      (field?.confidence || 0) > 0.8
                                        ? 'var(--color-success)'
                                        : 'var(--color-warning)',
                                  }}
                                />
                              </div>
                              <span className="meter-val-text">
                                {((field?.confidence || 0) * 100).toFixed(0)}%
                              </span>
                            </div>
                          </td>
                          <td>
                            <span className="meta-source-tag">{field?.source || 'heuristic'}</span>
                          </td>
                          <td style={{ textAlign: 'right' }}>
                            <button
                              className="btn-ghost field-copy-btn"
                              onClick={() => handleCopyFieldValue(name, field?.value)}
                              title="Copy value"
                            >
                              {copiedFieldName === name ? (
                                <Check size={13} style={{ color: 'var(--color-success)' }} />
                              ) : (
                                <Clipboard size={13} />
                              )}
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {/* TAB 3: LINE ITEMS */}
          {activeTab === 'line-items' && (
            <div className="line-items-tab card animate-fade-in">
              <div className="tab-pane-header">
                <h3 className="tab-pane-title">Invoice Itemization & Breakdown</h3>
                <p className="tab-pane-desc">Structured line item breakdown with quantities and unit prices.</p>
              </div>

              {aiLineItems.length === 0 ? (
                <EmptyState message="No itemized rows extracted." />
              ) : (
                <div className="table-responsive">
                  <table className="spacious-table">
                    <thead>
                      <tr>
                        <th style={{ width: '40px' }}>#</th>
                        <th>Item Description</th>
                        <th style={{ textAlign: 'right' }}>Quantity</th>
                        <th style={{ textAlign: 'right' }}>Unit Price (₹)</th>
                        <th style={{ textAlign: 'right' }}>Total (₹)</th>
                      </tr>
                    </thead>
                    <tbody>
                      {aiLineItems.map((item, idx) => (
                        <tr key={idx}>
                          <td style={{ color: 'var(--text-muted)' }}>{idx + 1}</td>
                          <td style={{ fontWeight: 600 }}>{item.description || '—'}</td>
                          <td style={{ textAlign: 'right', fontFamily: 'monospace' }}>
                            {item.quantity ?? '—'}
                          </td>
                          <td style={{ textAlign: 'right', fontFamily: 'monospace' }}>
                            {item.unit_price != null ? formatRupees(item.unit_price) : '—'}
                          </td>
                          <td style={{ textAlign: 'right', fontWeight: 700, fontFamily: 'monospace' }}>
                            {item.amount != null ? formatRupees(item.amount) : '—'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {/* TAB 4: FINANCIAL RECONCILER */}
          {activeTab === 'finance' && (
            <div className="finance-tab animate-fade-in">
              <div className="card finance-container-card">
                <div className="tab-pane-header">
                  <h3 className="tab-pane-title">Arithmetic Reconciliation</h3>
                  <p className="tab-pane-desc">
                    Mathematical validation verifying whether subtotal, taxes, and stated total reconcile properly.
                  </p>
                </div>

                <div className="finance-sheet">
                  <div className="finance-line">
                    <span className="f-label">Stated Subtotal</span>
                    <span className="f-val mono">{formatRupees(aiFinValidation.subtotal)}</span>
                  </div>
                  <div className="finance-line">
                    <span className="f-label">+ Stated Tax / Fees</span>
                    <span className="f-val mono">{formatRupees(aiFinValidation.tax)}</span>
                  </div>
                  <div className="finance-line">
                    <span className="f-label">− Applied Discount</span>
                    <span className="f-val mono">{formatRupees(aiFinValidation.discount)}</span>
                  </div>
                  <div className="f-divider" />
                  <div className="finance-line total-highlight">
                    <span className="f-label">Computed Mathematical Total</span>
                    <span className="f-val mono">{formatRupees(aiFinValidation.computed_total)}</span>
                  </div>
                  <div className="finance-line total-highlight">
                    <span className="f-label">Stated Document Total</span>
                    <span className="f-val mono">{formatRupees(aiFinValidation.stated_total)}</span>
                  </div>
                  <div className="f-divider" />
                  <div className="finance-line verdict-line">
                    <span className="f-label">Reconciliation Verdict</span>
                    <div>
                      {aiFinValidation.is_valid === true && (
                        <span className="verdict-tag pass">
                          <CheckCircle2 size={16} /> Balanced — No Discrepancy
                        </span>
                      )}
                      {aiFinValidation.is_valid === false && (
                        <span className="verdict-tag fail">
                          <AlertCircle size={16} /> Discrepancy: {formatRupees(aiFinValidation.discrepancy)}
                        </span>
                      )}
                      {aiFinValidation.is_valid == null && (
                        <span className="verdict-tag unknown">Insufficient numeric data</span>
                      )}
                    </div>
                  </div>
                </div>

                {aiFinValidation.notes && (
                  <div className="finance-notes-callout">
                    <strong>Audit Note:</strong> {aiFinValidation.notes}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* TAB 5: VALIDATION RULES */}
          {activeTab === 'validation' && (
            <div className="validation-tab animate-fade-in">
              <div className="explainer-card">
                <div className="explainer-icon">
                  <Info size={18} />
                </div>
                <div className="explainer-content">
                  <div className="explainer-title">What is Deterministic Validation?</div>
                  <p className="explainer-text">
                    DocuMind evaluates your document against 6 deterministic business rules: checking that required fields are present, verifying arithmetic sums (subtotal + tax = total), confirming logical date order (due date after invoice date), ensuring non-negative amounts, and checking for duplicate invoice identifiers.
                  </p>
                </div>
              </div>

              {aiValidationSummary && (
                <div className="ai-narrative-box">
                  <div className="ai-narrative-icon">
                    <Sparkles size={14} />
                  </div>
                  <div className="ai-narrative-content">
                    <div className="ai-narrative-label">AI Validation Narrative</div>
                    <p className="ai-narrative-text">{aiValidationSummary}</p>
                  </div>
                </div>
              )}

              {!validation || !validation.results || validation.results.length === 0 ? (
                <div className="card">
                  <EmptyState message="No validation rules executed for this document." />
                </div>
              ) : (
                <div className="rules-grid">
                  {validation.results.map((rule, idx) => {
                    const isPass = rule.status === 'PASS';
                    const isFail = rule.status === 'FAIL';
                    const isWarn = rule.status === 'WARN';

                    return (
                      <div key={idx} className={`rule-card card ${isPass ? 'pass' : isFail ? 'fail' : 'warn'}`}>
                        <div className="rule-card-top">
                          <div className="rule-title-group">
                            {isPass && <CheckCircle2 size={20} style={{ color: 'var(--color-success)' }} />}
                            {isFail && <AlertCircle size={20} style={{ color: 'var(--color-error)' }} />}
                            {isWarn && <AlertTriangle size={20} style={{ color: 'var(--color-warning)' }} />}
                            <span className="rule-name-text">{rule.rule_name}</span>
                          </div>
                          <StatusBadge
                            status={isPass ? 'valid' : isFail ? 'invalid' : 'warning'}
                            label={rule.status}
                          />
                        </div>
                        <p className="rule-message-text">{rule.message}</p>
                        {rule.details && Object.keys(rule.details).length > 0 && (
                          <div className="rule-details-raw">
                            {JSON.stringify(rule.details)}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          )}

          {/* TAB 6: DUPLICATES */}
          {activeTab === 'duplicates' && (
            <div className="duplicates-tab animate-fade-in">
              <div className="explainer-card">
                <div className="explainer-icon">
                  <Info size={18} />
                </div>
                <div className="explainer-content">
                  <div className="explainer-title">What is Duplicate Detection?</div>
                  <p className="explainer-text">
                    DocuMind uses TF-IDF cosine similarity and SHA-256 content hashing to compare your document against all existing records in the repository. Exact matches indicate identical resubmissions, while near matches (85-99%) flag revised versions, duplicates with minor edits, or potential double-billing.
                  </p>
                </div>
              </div>

              {aiDuplicateAssessment && (
                <div className="ai-narrative-box">
                  <div className="ai-narrative-icon">
                    <Sparkles size={14} />
                  </div>
                  <div className="ai-narrative-content">
                    <div className="ai-narrative-label">AI Duplicate Assessment</div>
                    <p className="ai-narrative-text">{aiDuplicateAssessment}</p>
                  </div>
                </div>
              )}

              <div className="card">
                <h3 className="tab-pane-title">Vector Similarity Results</h3>
                <p className="tab-pane-desc">
                  Repository scan comparing content vectors against all historical records of the same class.
                </p>

                {!duplicates || !duplicates.matches || duplicates.matches.length === 0 ? (
                  <EmptyState message="No duplicate matches found. This document is completely unique." />
                ) : (
                  <div className="duplicates-list">
                    {duplicates.matches.map((match, idx) => (
                      <div key={idx} className="duplicate-match-card card">
                        <div className="dup-header">
                          <div className="dup-info">
                            <Copy size={20} className="dup-icon" />
                            <div>
                              <strong className="dup-doc-id">Matched: {match.matched_document_id}</strong>
                              <span className="dup-type-tag">{match.duplicate_type}</span>
                            </div>
                          </div>
                          <button
                            className="btn btn-secondary btn-xs"
                            onClick={() => navigate(`/documents/${match.matched_document_id}`)}
                          >
                            <span>Inspect Document</span>
                            <ExternalLink size={12} />
                          </button>
                        </div>
                        <div className="dup-similarity-strip">
                          <span>Similarity Score:</span>
                          <strong className="dup-score-val">
                            {(match.similarity_score * 100).toFixed(2)}%
                          </strong>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* TAB 7: ANOMALY DETECTION */}
          {activeTab === 'anomaly' && (
            <div className="anomaly-tab animate-fade-in">
              <div className="explainer-card">
                <div className="explainer-icon">
                  <Info size={18} />
                </div>
                <div className="explainer-content">
                  <div className="explainer-title">What is Anomaly Detection?</div>
                  <p className="explainer-text">
                    DocuMind uses an Isolation Forest machine learning model to evaluate numerical features (file size, text length, financial amounts, field counts). Documents differing significantly from normal historical clusters are flagged as outliers for human review.
                  </p>
                </div>
              </div>

              {aiAnomalyAssessment && (
                <div className="ai-narrative-box">
                  <div className="ai-narrative-icon">
                    <Sparkles size={14} />
                  </div>
                  <div className="ai-narrative-content">
                    <div className="ai-narrative-label">AI Anomaly Assessment</div>
                    <p className="ai-narrative-text">{aiAnomalyAssessment}</p>
                  </div>
                </div>
              )}

              <div className="anomaly-stats-grid">
                <div className="card anomaly-stat-box">
                  <span className="stat-label">Model Classification</span>
                  <div className="stat-val-row">
                    <StatusBadge
                      status={anomaly?.is_anomaly ? 'anomaly' : 'normal'}
                      label={anomaly?.is_anomaly ? 'Outlier Flagged' : 'Normal Cluster'}
                    />
                  </div>
                </div>

                <div className="card anomaly-stat-box">
                  <span className="stat-label">Anomaly Score</span>
                  <div className="stat-number">{anomaly?.anomaly_score != null ? anomaly.anomaly_score : '—'}</div>
                </div>

                <div className="card anomaly-stat-box">
                  <span className="stat-label">Decision Function</span>
                  <div className="stat-number">{anomaly?.decision_function_score != null ? anomaly.decision_function_score : '—'}</div>
                </div>
              </div>

              {/* Feature vectors table */}
              {anomaly?.features && Object.keys(anomaly.features).length > 0 && (
                <div className="card feature-vectors-card">
                  <h4 className="tab-pane-title" style={{ fontSize: '15px' }}>
                    Evaluated Feature Vectors
                  </h4>
                  <div className="table-responsive">
                    <table className="spacious-table">
                      <thead>
                        <tr>
                          <th>Vector Feature</th>
                          <th>Numeric Value</th>
                        </tr>
                      </thead>
                      <tbody>
                        {Object.entries(anomaly.features).map(([fKey, fVal]) => (
                          <tr key={fKey}>
                            <td className="field-name-cell">{fKey.replace(/_/g, ' ')}</td>
                            <td>
                              <span className="field-value-pill mono">
                                {typeof fVal === 'number' ? fVal.toLocaleString() : String(fVal)}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* TAB 8: RAW TEXT */}
          {activeTab === 'content' && (
            <div className="content-tab animate-fade-in">
              <div className="card">
                <div className="tab-pane-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <h3 className="tab-pane-title">Cleaned OCR Output</h3>
                    <p className="tab-pane-desc">Full textual content extracted by the Tesseract normalization pipeline.</p>
                  </div>
                  <button
                    className="btn btn-secondary btn-sm"
                    onClick={() => handleCopyText(content?.cleaned_text || content?.raw_text)}
                  >
                    {copied ? <Check size={14} /> : <Clipboard size={14} />}
                    <span>{copied ? 'Copied' : 'Copy Text'}</span>
                  </button>
                </div>
                <div className="ocr-text-viewer">
                  {content?.cleaned_text || content?.raw_text || 'No extracted text found for this document.'}
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
