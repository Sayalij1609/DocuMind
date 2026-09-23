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
  Download,
  ChevronDown,
  Building2,
  ListChecks,
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
  downloadReport,
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

  const [activeSection, setActiveSection] = useState('overview');
  const [copied, setCopied] = useState(false);
  const [copiedFieldName, setCopiedFieldName] = useState(null);
  const [fieldSearch, setFieldSearch] = useState('');
  const [downloadingReport, setDownloadingReport] = useState(false);

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
  const aiRiskNarrative = ai.risk_narrative || '';
  const aiProfile = ai.complete_document_profile || {};
  const aiParties = aiEntities.parties || [];
  const aiIdentifiers = aiEntities.identifiers || [];
  const aiDates = aiEntities.dates || [];
  const aiFinancials = aiEntities.financials || {};
  const aiKeyFindings = aiProfile.key_findings || [];
  const aiRecommendations = aiProfile.recommendations || [];

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

  const accountNoVal =
    aiEntities.identifiers?.find((i) => /account|a\/c/i.test(i.type))?.value ??
    analysis.extraction?.fields?.account_number?.value ??
    null;

  const employeeIdVal =
    aiEntities.identifiers?.find((i) => /employee|emp/i.test(i.type))?.value ??
    analysis.extraction?.fields?.employee_id?.value ??
    null;

  const consumerNoVal =
    aiEntities.identifiers?.find((i) => /consumer|meter|ca/i.test(i.type))?.value ??
    analysis.extraction?.fields?.consumer_number?.value ??
    analysis.extraction?.fields?.meter_number?.value ??
    null;

  const customerVal =
    aiEntities.parties?.find((p) => /customer|recipient|buyer|client/i.test(p.role))?.name ??
    analysis.extraction?.fields?.customer_name?.value ??
    analysis.extraction?.fields?.client_name?.value ??
    null;

  const dueDateVal =
    aiEntities.dates?.find((d) => /due/i.test(d.type))?.value ??
    analysis.extraction?.fields?.due_date?.value ??
    null;

  const subtotalVal =
    aiFinancials?.subtotal ??
    aiFinValidation?.subtotal ??
    analysis.extraction?.fields?.subtotal?.value ??
    null;

  const taxVal =
    aiFinancials?.tax ??
    aiFinValidation?.tax ??
    analysis.extraction?.fields?.tax_amount?.value ??
    analysis.extraction?.fields?.tax?.value ??
    null;

  const discountVal =
    aiFinancials?.discount ??
    aiFinValidation?.discount ??
    analysis.extraction?.fields?.discount?.value ??
    null;

  const isUploadedOnly = analysis.status === 'uploaded';
  const isProcessing = analysis.status === 'processing';

  const options = [
    {
      id: 'overview',
      label: 'Complete Summary',
      icon: FileCheck,
      badge: 'All-in-One',
      badgeType: 'primary',
      desc: 'Executive Briefing, Profile & Insights',
    },
    {
      id: 'fields',
      label: 'Extracted Fields',
      icon: Layers,
      badge: filteredFieldEntries.length,
      desc: 'Normalized Key-Value Data',
    },
    ...(aiLineItems.length > 0
      ? [
          {
            id: 'line_items',
            label: 'Line Items',
            icon: Tag,
            badge: aiLineItems.length,
            desc: 'Tabular items breakdown',
          },
        ]
      : []),
    ...(Object.keys(aiFinValidation).length > 0
      ? [
          {
            id: 'finance',
            label: 'Financial Check',
            icon: Calculator,
            badge:
              aiFinValidation.is_valid === true
                ? '✓ Match'
                : aiFinValidation.is_valid === false
                ? 'Mismatch'
                : null,
            badgeType: aiFinValidation.is_valid === true ? 'success' : 'danger',
            desc: 'Arithmetic verification',
          },
        ]
      : []),
    {
      id: 'validation',
      label: 'Validation Rules',
      icon: ShieldCheck,
      badge:
        validation?.error_count > 0
          ? `${validation.error_count} Errors`
          : validation?.status || 'Audited',
      badgeType:
        validation?.error_count > 0
          ? 'danger'
          : validation?.warning_count > 0
          ? 'warning'
          : 'success',
      desc: 'Compliance rule results',
    },
    {
      id: 'duplicates',
      label: 'Duplicate Check',
      icon: Copy,
      badge: duplicates?.has_duplicates
        ? `${duplicates.matches?.length || 0} Matches`
        : 'Unique',
      badgeType: duplicates?.has_duplicates ? 'warning' : 'success',
      desc: 'Cross-document similarity',
    },
    {
      id: 'anomaly',
      label: 'Anomaly Detection',
      icon: AlertTriangle,
      badge: anomaly?.is_anomaly ? 'Outlier' : 'Normal',
      badgeType: anomaly?.is_anomaly ? 'danger' : 'success',
      desc: 'Isolation Forest ML scan',
    },
    {
      id: 'rawtext',
      label: 'Extracted Text (OCR)',
      icon: FileCode,
      badge: null,
      desc: 'Raw textual output',
    },
  ];

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

      {/* STATE 3: COMPLETED ANALYSIS — CLEAN OPTION BUTTONS LAYOUT */}
      {!isUploadedOnly && !isProcessing && (
        <div className="clean-analysis-wrapper">
          {/* 1. Quick Stats & Action Strip */}
          <div className="clean-audit-strip card">
            <div className="strip-item">
              <span className="strip-label">Classification</span>
              <div className="strip-val-wrap">
                <Activity size={16} className="text-primary" />
                <strong className="strip-value capitalize">{analysis.document_type || 'Unclassified'}</strong>
              </div>
              {analysis.classification_confidence != null && (
                <span className="strip-sub">{(analysis.classification_confidence * 100).toFixed(1)}% confidence</span>
              )}
            </div>

            <div className="strip-divider" />

            <div className="strip-item">
              <span className="strip-label">Financial Liability</span>
              <div className="strip-val-wrap">
                <Calculator size={16} className="text-accent" />
                <strong className="strip-value text-accent">
                  {totalAmountVal != null ? formatRupees(totalAmountVal) : '—'}
                </strong>
              </div>
              <span className="strip-sub">Currency: {aiEntities.financials?.currency || 'INR (₹)'}</span>
            </div>

            <div className="strip-divider" />

            <div className="strip-item">
              <span className="strip-label">Compliance</span>
              <div className="strip-val-wrap">
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
              </div>
              <span className="strip-sub">{analysis.validation_error_count ?? 0} errors</span>
            </div>

            <div className="strip-divider" />

            <div className="strip-item">
              <span className="strip-label">Integrity & Risk</span>
              <div className="strip-val-wrap">
                <span className={`strip-status-pill ${analysis.is_anomaly ? 'pill-danger' : 'pill-success'}`}>
                  <AlertTriangle size={13} />
                  <span>{analysis.is_anomaly ? 'Outlier Flagged' : 'Normal Pattern'}</span>
                </span>
              </div>
              <span className="strip-sub">{duplicates?.has_duplicates ? `${duplicates.matches?.length} matches` : 'Unique record'}</span>
            </div>

            <div className="strip-divider" />

            <div className="strip-item strip-action-item">
              <button
                className="btn btn-primary download-report-cta"
                disabled={downloadingReport}
                onClick={async () => {
                  try {
                    setDownloadingReport(true);
                    await downloadReport(id);
                  } catch (err) {
                    alert('Report generation failed: ' + (err.message || 'Unknown error'));
                  } finally {
                    setDownloadingReport(false);
                  }
                }}
              >
                <Download size={15} />
                <span>{downloadingReport ? 'Generating PDF...' : 'Download PDF Report'}</span>
              </button>
            </div>
          </div>

          {/* 2. Clean Option Buttons Bar */}
          <div className="clean-options-container card">
            <div className="options-bar-header">
              <span className="options-bar-title">Analysis Components</span>
              <span className="options-bar-hint">Click an option button to view its details</span>
            </div>

            <div className="clean-option-buttons">
              {options.map((opt) => {
                const Icon = opt.icon;
                const isActive = activeSection === opt.id;
                return (
                  <button
                    key={opt.id}
                    className={`clean-opt-btn ${isActive ? 'active' : ''}`}
                    onClick={() => setActiveSection(opt.id)}
                  >
                    <div className="opt-icon-circle">
                      <Icon size={16} />
                    </div>
                    <span className="opt-btn-label">{opt.label}</span>
                    {opt.badge != null && (
                      <span className={`opt-btn-badge ${opt.badgeType ? `badge-${opt.badgeType}` : ''}`}>
                        {opt.badge}
                      </span>
                    )}
                  </button>
                );
              })}
            </div>
          </div>

          {/* 3. Detailed Component Content View */}
          <div className="clean-content-panel animate-fade-in">
            {/* OPTION 1: COMPLETE SUMMARY & DOCUMENT ANALYSIS */}
            {activeSection === 'overview' && (
              <div className="panel-section complete-summary-panel">
                <div className="panel-header">
                  <div className="panel-title-wrap">
                    <FileCheck size={22} className="panel-icon text-primary" />
                    <div>
                      <h3 className="panel-title">Complete Document Analysis & Executive Summary</h3>
                      <p className="panel-desc">
                        Comprehensive audit profile, executive summary, risk evaluation, party mapping, and compliance verification
                      </p>
                    </div>
                  </div>
                  <div className="analysis-engine-badge">
                    <Sparkles size={14} className="text-accent" />
                    <span>
                      {ai.analysis_method === 'groq_llm'
                        ? 'Groq LLM Neural Engine'
                        : 'Smart Heuristic Audit Engine'}
                    </span>
                  </div>
                </div>

                <div className="panel-body complete-summary-body">
                  {/* 1. Document Purpose & Classification Card */}
                  <div className="doc-purpose-card card">
                    <div className="purpose-header">
                      <div className="purpose-title-wrap">
                        <Info size={16} className="text-primary" />
                        <h4 className="purpose-heading">Document Purpose & Context</h4>
                      </div>
                      <div className="purpose-meta-pills">
                        <span className="purpose-pill">
                          Class: <strong>{(analysis.document_type || 'Unclassified').replace(/_/g, ' ').toUpperCase()}</strong>
                        </span>
                        {analysis.classification_confidence != null && (
                          <span className="purpose-pill">
                            Confidence: <strong>{(analysis.classification_confidence * 100).toFixed(1)}%</strong>
                          </span>
                        )}
                        <span className="purpose-pill">
                          Status: <strong>{(analysis.status || 'Processed').toUpperCase()}</strong>
                        </span>
                      </div>
                    </div>
                    <p className="purpose-text">
                      {aiProfile.document_purpose ||
                        `This ${analysis.document_type || 'document'} (${analysis.filename}) serves as a verified transaction and operational record within the enterprise financial pipeline.`}
                    </p>
                  </div>

                  {/* 2. Executive Summary */}
                  <div className="summary-block">
                    <div className="summary-block-header">
                      <h4 className="sub-heading">
                        <FileText size={16} className="text-primary" /> Executive Audit Narrative
                      </h4>
                      <button
                        className="btn-copy-small"
                        onClick={() => handleCopyText(ai.executive_summary || '')}
                        title="Copy Summary"
                      >
                        {copied ? <Check size={12} /> : <Clipboard size={12} />}
                        <span>{copied ? 'Copied' : 'Copy'}</span>
                      </button>
                    </div>
                    <div className="audit-brief-card">
                      <p className="audit-brief-text">
                        {ai.executive_summary ||
                          `This document has been classified as ${analysis.document_type || 'unclassified'} (${analysis.filename}). Automated audits have extracted ${fieldEntries.length} fields with standard validation rules applied.`}
                      </p>
                    </div>
                  </div>

                  {/* 3. Fiscal Risk & Integrity Evaluation */}
                  {(aiRiskNarrative || analysis.is_anomaly != null) && (
                    <div className="summary-block">
                      <h4 className="sub-heading">
                        <AlertTriangle size={16} className={analysis.is_anomaly ? "text-danger" : "text-amber"} /> Fiscal Risk & Integrity Assessment
                      </h4>
                      <div className={`risk-evaluation-banner ${analysis.is_anomaly ? 'risk-elevated' : 'risk-nominal'}`}>
                        <div className="risk-banner-header">
                          <div className="risk-icon-wrap">
                            <ShieldCheck size={20} />
                          </div>
                          <div>
                            <strong>
                              {analysis.is_anomaly
                                ? 'Elevated Fiscal / Outlier Risk Profile'
                                : 'Standard Risk Level — Verification Audit Complete'}
                            </strong>
                            <span className="risk-banner-sub">
                              {analysis.is_anomaly
                                ? 'Document exhibits statistical variance from normal distribution.'
                                : 'Key identifiers, dates, and amounts reconcile with standard business conventions.'}
                            </span>
                          </div>
                        </div>
                        {aiRiskNarrative && (
                          <div className="risk-banner-text">
                            {aiRiskNarrative}
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {/* 4. Key Findings Cards */}
                  {aiKeyFindings.length > 0 && (
                    <div className="summary-block">
                      <h4 className="sub-heading">
                        <Sparkles size={16} className="text-accent" /> Key Extracted Findings
                      </h4>
                      <div className="key-findings-grid">
                        {aiKeyFindings.map((finding, idx) => (
                          <div key={idx} className="finding-card">
                            <div className="finding-badge">{idx + 1}</div>
                            <span className="finding-text">{finding}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* 5. Financial Overview & Structure */}
                  <div className="summary-block">
                    <h4 className="sub-heading">
                      <Calculator size={16} className="text-teal" /> Financial Structure & Reconciliation
                    </h4>
                    <div className="financial-overview-card card">
                      {aiProfile.financial_overview && (
                        <p className="financial-overview-narrative">
                          {aiProfile.financial_overview}
                        </p>
                      )}
                      <div className="financial-metrics-row">
                        <div className="fin-metric-cell highlight">
                          <span className="fin-metric-label">Gross Total</span>
                          <strong className="fin-metric-value text-accent">
                            {totalAmountVal != null ? formatRupees(totalAmountVal) : '—'}
                          </strong>
                          <span className="fin-metric-sub">{aiFinancials.currency || 'INR (₹)'}</span>
                        </div>
                        <div className="fin-metric-cell">
                          <span className="fin-metric-label">Subtotal</span>
                          <strong className="fin-metric-value">
                            {subtotalVal != null ? formatRupees(subtotalVal) : '—'}
                          </strong>
                          <span className="fin-metric-sub">Before tax & disc.</span>
                        </div>
                        <div className="fin-metric-cell">
                          <span className="fin-metric-label">Tax / GST</span>
                          <strong className="fin-metric-value">
                            {taxVal != null ? formatRupees(taxVal) : '—'}
                          </strong>
                          <span className="fin-metric-sub">Statutory levy</span>
                        </div>
                        <div className="fin-metric-cell">
                          <span className="fin-metric-label">Arithmetic Verification</span>
                          <strong className={`fin-metric-value ${aiFinValidation.is_valid === true ? 'text-success' : aiFinValidation.is_valid === false ? 'text-danger' : ''}`}>
                            {aiFinValidation.is_valid === true ? '✓ Reconciled' : aiFinValidation.is_valid === false ? '⚠ Discrepancy' : 'Audited'}
                          </strong>
                          <span className="fin-metric-sub">Line items sum</span>
                        </div>
                      </div>
                      {aiFinValidation.notes && (
                        <div className="financial-reconcile-notes">
                          <Info size={13} className="text-muted" />
                          <span>{aiFinValidation.notes}</span>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* 6. Entity & Counterparty Details */}
                  {(aiParties.length > 0 || aiRelationships.length > 0 || vendorVal || customerVal) && (
                    <div className="summary-block">
                      <h4 className="sub-heading">
                        <Building2 size={16} className="text-primary" /> Parties & Counterparty Mapping
                      </h4>
                      {aiParties.length > 0 ? (
                        <div className="parties-grid">
                          {aiParties.map((party, idx) => (
                            <div key={idx} className="party-card card">
                              <div className="party-header">
                                <span className="party-role-badge capitalize">{party.role || 'Counterparty'}</span>
                                {party.tax_id && (
                                  <span className="party-tax-badge mono">Tax ID: {party.tax_id}</span>
                                )}
                              </div>
                              <h5 className="party-name">{party.name || 'Unnamed Party'}</h5>
                              {party.address && <p className="party-detail">📍 {party.address}</p>}
                              {party.contact && <p className="party-detail">📞 {party.contact}</p>}
                            </div>
                          ))}
                        </div>
                      ) : (
                        aiRelationships.length > 0 && (
                          <div className="roles-tags-wrap">
                            {aiRelationships.map((rel, i) => (
                              <div key={i} className="counterparty-role-tag">
                                <span className="entity-text">{rel.entity}</span>
                                <ArrowRight size={12} className="role-arrow" />
                                <span className="role-text">{rel.role}</span>
                              </div>
                            ))}
                          </div>
                        )
                      )}
                    </div>
                  )}

                  {/* 7. Document Identifiers & Key Dates */}
                  <div className="summary-block">
                    <h4 className="sub-heading">
                      <Tag size={16} className="text-purple" /> Primary Identifiers & Chronology
                    </h4>
                    <div className="identifiers-dates-grid">
                      {/* Left: Identifiers */}
                      <div className="id-subcard card">
                        <h5 className="id-subcard-title">Document Reference Identifiers</h5>
                        <div className="tid-table">
                          <div className="tid-row">
                            <span className="tid-key">Document Type</span>
                            <span className="tid-val capitalize">{analysis.document_type || 'Unclassified'}</span>
                          </div>
                          {invoiceNoVal && (
                            <div className="tid-row">
                              <span className="tid-key">Invoice / Ref #</span>
                              <span className="tid-val mono">{invoiceNoVal}</span>
                            </div>
                          )}
                          {poNoVal && (
                            <div className="tid-row">
                              <span className="tid-key">Purchase Order #</span>
                              <span className="tid-val mono">{poNoVal}</span>
                            </div>
                          )}
                          {accountNoVal && (
                            <div className="tid-row">
                              <span className="tid-key">Account #</span>
                              <span className="tid-val mono">{accountNoVal}</span>
                            </div>
                          )}
                          {employeeIdVal && (
                            <div className="tid-row">
                              <span className="tid-key">Employee ID</span>
                              <span className="tid-val mono">{employeeIdVal}</span>
                            </div>
                          )}
                          {consumerNoVal && (
                            <div className="tid-row">
                              <span className="tid-key">Consumer / Meter #</span>
                              <span className="tid-val mono">{consumerNoVal}</span>
                            </div>
                          )}
                          {vendorVal && (
                            <div className="tid-row">
                              <span className="tid-key">Vendor / Issuer</span>
                              <span className="tid-val">{vendorVal}</span>
                            </div>
                          )}
                          {customerVal && (
                            <div className="tid-row">
                              <span className="tid-key">Recipient / Client</span>
                              <span className="tid-val">{customerVal}</span>
                            </div>
                          )}
                        </div>
                      </div>

                      {/* Right: Key Dates */}
                      <div className="id-subcard card">
                        <h5 className="id-subcard-title">Transaction Chronology</h5>
                        <div className="tid-table">
                          {primaryDateVal && (
                            <div className="tid-row">
                              <span className="tid-key">Primary Date</span>
                              <span className="tid-val">{primaryDateVal}</span>
                            </div>
                          )}
                          {dueDateVal && (
                            <div className="tid-row">
                              <span className="tid-key">Due Date</span>
                              <span className="tid-val">{dueDateVal}</span>
                            </div>
                          )}
                          {aiDates.length > 0 ? (
                            aiDates.slice(0, 4).map((d, i) => (
                              <div key={i} className="tid-row">
                                <span className="tid-key capitalize">{(d.type || 'Date').replace(/_/g, ' ')}</span>
                                <span className="tid-val">{d.value}</span>
                              </div>
                            ))
                          ) : (
                            <div className="tid-row">
                              <span className="tid-key">Uploaded Timestamp</span>
                              <span className="tid-val">{new Date(analysis.created_at).toLocaleString()}</span>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* 8. Actionable Recommendations */}
                  {aiRecommendations.length > 0 && (
                    <div className="summary-block">
                      <h4 className="sub-heading">
                        <ListChecks size={16} className="text-accent" /> Actionable Audit Recommendations
                      </h4>
                      <div className="recommendations-list">
                        {aiRecommendations.map((rec, i) => (
                          <div key={i} className="rec-card">
                            <CheckCircle2 size={16} className="rec-icon text-accent" />
                            <span className="rec-text">{rec}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* 9. Key Audit Observations */}
                  {aiInsights.length > 0 && (
                    <div className="summary-block">
                      <h4 className="sub-heading">
                        <Lightbulb size={16} className="text-amber" /> Operational Audit Observations
                      </h4>
                      <div className="insights-grid">
                        {aiInsights.map((insight, i) => (
                          <div key={i} className="insight-card">
                            <CheckCircle2 size={16} className="insight-check" />
                            <span>{insight}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* 10. System Compliance & Verification Synopsis */}
                  <div className="summary-block">
                    <h4 className="sub-heading">
                      <ShieldCheck size={16} className="text-teal" /> Multi-Layer System Verification Synopsis
                    </h4>
                    <div className="synopsis-grid">
                      <div className="synopsis-card card">
                        <div className="synopsis-header">
                          <ShieldCheck size={18} className="text-teal" />
                          <span className="synopsis-title">Deterministic Compliance</span>
                        </div>
                        <p className="synopsis-body">
                          {aiProfile.compliance_status ||
                            aiValidationSummary ||
                            (validation?.error_count === 0
                              ? 'All deterministic business compliance rules passed successfully.'
                              : `${validation?.error_count} rule error(s) flagged during automated check.`)}
                        </p>
                      </div>

                      <div className="synopsis-card card">
                        <div className="synopsis-header">
                          <Copy size={18} className="text-blue" />
                          <span className="synopsis-title">Uniqueness Verification</span>
                        </div>
                        <p className="synopsis-body">
                          {aiDuplicateAssessment ||
                            (duplicates?.has_duplicates
                              ? `${duplicates.matches?.length || 0} potential duplicate match(es) detected across repository.`
                              : 'Document has been verified as a unique transaction record.')}
                        </p>
                      </div>

                      <div className="synopsis-card card">
                        <div className="synopsis-header">
                          <AlertTriangle size={18} className={anomaly?.is_anomaly ? "text-danger" : "text-success"} />
                          <span className="synopsis-title">Statistical Anomaly Scan</span>
                        </div>
                        <p className="synopsis-body">
                          {aiAnomalyAssessment ||
                            (anomaly?.is_anomaly
                              ? 'Isolation Forest model flagged feature metrics as statistical outliers.'
                              : 'Evaluated feature vectors align within standard historical clustering.')}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* OPTION 2: EXTRACTED FIELDS */}
            {activeSection === 'fields' && (
              <div className="panel-section">
                <div className="panel-header">
                  <div className="panel-title-wrap">
                    <Layers size={20} className="panel-icon text-purple" />
                    <div>
                      <h3 className="panel-title">Extracted Key-Value Fields</h3>
                      <p className="panel-desc">Normalized entities extracted by OCR & pattern recognition pipelines</p>
                    </div>
                  </div>
                  <div className="panel-search-wrap">
                    <Search size={15} />
                    <input
                      type="text"
                      className="clean-search-input"
                      placeholder="Filter fields..."
                      value={fieldSearch}
                      onChange={(e) => setFieldSearch(e.target.value)}
                    />
                  </div>
                </div>

                <div className="panel-body">
                  {filteredFieldEntries.length > 0 ? (
                    <div className="clean-table-card">
                      <table className="clean-data-table">
                        <thead>
                          <tr>
                            <th>Field Name</th>
                            <th>Extracted Value</th>
                            <th style={{ width: '140px' }}>Confidence</th>
                          </tr>
                        </thead>
                        <tbody>
                          {filteredFieldEntries.map(([name, f]) => (
                            <tr
                              key={name}
                              className="clickable-row"
                              onClick={() => handleCopyFieldValue(name, f?.value)}
                              title="Click to copy value"
                            >
                              <td className="field-name-cell">
                                <span className="field-key-name">{name.replace(/_/g, ' ')}</span>
                              </td>
                              <td className="field-value-cell">
                                <span className="field-val-text">
                                  {formatFieldValue(name, f?.value)}
                                </span>
                                {copiedFieldName === name ? (
                                  <span className="copied-pill">Copied!</span>
                                ) : (
                                  <Clipboard size={12} className="copy-icon-hover" />
                                )}
                              </td>
                              <td>
                                <div className="confidence-pill-wrap">
                                  <div
                                    className={`confidence-pill ${
                                      f?.confidence >= 0.8
                                        ? 'conf-high'
                                        : f?.confidence >= 0.5
                                        ? 'conf-mid'
                                        : 'conf-low'
                                    }`}
                                  >
                                    {f?.confidence != null ? `${(f.confidence * 100).toFixed(0)}%` : '—'}
                                  </div>
                                </div>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ) : (
                    <div className="clean-empty-box">
                      <p>No fields matched your filter criteria.</p>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* OPTION 3: LINE ITEMS */}
            {activeSection === 'line_items' && aiLineItems.length > 0 && (
              <div className="panel-section">
                <div className="panel-header">
                  <div className="panel-title-wrap">
                    <Tag size={20} className="panel-icon text-orange" />
                    <div>
                      <h3 className="panel-title">Itemized Line Records</h3>
                      <p className="panel-desc">{aiLineItems.length} individual items identified in document tables</p>
                    </div>
                  </div>
                </div>

                <div className="panel-body">
                  <div className="clean-table-card">
                    <table className="clean-data-table">
                      <thead>
                        <tr>
                          <th style={{ width: '50px' }}>#</th>
                          <th>Description</th>
                          <th style={{ width: '90px' }}>Qty</th>
                          <th style={{ width: '130px' }}>Price</th>
                          <th style={{ width: '150px' }}>Total</th>
                        </tr>
                      </thead>
                      <tbody>
                        {aiLineItems.map((item, i) => (
                          <tr key={i}>
                            <td className="mono">{i + 1}</td>
                            <td>
                              <strong>{item.description || item.item || item.name || '—'}</strong>
                            </td>
                            <td>{item.quantity ?? item.qty ?? '—'}</td>
                            <td className="mono">
                              {item.unit_price ? formatRupees(item.unit_price) : (item.price ? formatRupees(item.price) : '—')}
                            </td>
                            <td className="mono font-bold text-accent">
                              {item.amount ? formatRupees(item.amount) : (item.total ? formatRupees(item.total) : '—')}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            )}

            {/* OPTION 4: FINANCIAL MATH CHECK */}
            {activeSection === 'finance' && Object.keys(aiFinValidation).length > 0 && (
              <div className="panel-section">
                <div className="panel-header">
                  <div className="panel-title-wrap">
                    <Calculator size={20} className="panel-icon text-teal" />
                    <div>
                      <h3 className="panel-title">Financial Reconciliation & Math Verification</h3>
                      <p className="panel-desc">Deterministic arithmetic audit verifying stated subtotal + taxes against gross liability</p>
                    </div>
                  </div>
                </div>

                <div className="panel-body">
                  <div className={`status-banner-card ${aiFinValidation.is_valid === true ? 'banner-success' : 'banner-warning'}`}>
                    <div className="banner-icon-wrap">
                      {aiFinValidation.is_valid === true ? <CheckCircle2 size={24} /> : <AlertTriangle size={24} />}
                    </div>
                    <div>
                      <strong>
                        {aiFinValidation.is_valid === true
                          ? 'Arithmetic Integrity Verified'
                          : 'Financial Totals Discrepancy Detected'}
                      </strong>
                      <p>
                        {aiFinValidation.message ||
                          (aiFinValidation.is_valid === true
                            ? 'All line items and calculated taxes mathematically match the final stated total.'
                            : 'The sum of extracted subtotal and taxes does not match the stated grand total.')}
                      </p>
                    </div>
                  </div>

                  <div className="clean-table-card" style={{ marginTop: '1rem' }}>
                    <table className="clean-data-table">
                      <thead>
                        <tr>
                          <th>Financial Metric</th>
                          <th>Value</th>
                        </tr>
                      </thead>
                      <tbody>
                        {Object.entries(aiFinValidation).map(([k, v]) => {
                          if (k === 'is_valid' || k === 'message') return null;
                          return (
                            <tr key={k}>
                              <td className="field-name-cell">
                                <span className="field-key-name">{k.replace(/_/g, ' ')}</span>
                              </td>
                              <td className="field-value-cell mono">
                                {typeof v === 'number' ? formatRupees(v) : String(v)}
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            )}

            {/* OPTION 5: VALIDATION RULES */}
            {activeSection === 'validation' && (
              <div className="panel-section">
                <div className="panel-header">
                  <div className="panel-title-wrap">
                    <ShieldCheck size={20} className="panel-icon text-teal" />
                    <div>
                      <h3 className="panel-title">Business Validation Rules</h3>
                      <p className="panel-desc">Compliance verification against 6 core deterministic enterprise rules</p>
                    </div>
                  </div>
                  {validation && (
                    <StatusBadge
                      status={
                        validation.error_count > 0
                          ? 'invalid'
                          : validation.warning_count > 0
                          ? 'warning'
                          : 'valid'
                      }
                    />
                  )}
                </div>

                <div className="panel-body">
                  {aiValidationSummary && (
                    <div className="ai-narrative-card">
                      <Sparkles size={16} className="text-accent" />
                      <div>
                        <strong>AI Compliance Evaluation</strong>
                        <p>{aiValidationSummary}</p>
                      </div>
                    </div>
                  )}

                  {validation?.rules?.length > 0 ? (
                    <div className="clean-table-card">
                      <table className="clean-data-table">
                        <thead>
                          <tr>
                            <th>Rule Name</th>
                            <th style={{ width: '120px' }}>Status</th>
                            <th>Audit Message</th>
                          </tr>
                        </thead>
                        <tbody>
                          {validation.rules.map((r, i) => (
                            <tr key={i}>
                              <td>
                                <strong>{r.rule_name}</strong>
                              </td>
                              <td>
                                <span
                                  className={`rule-status-tag ${
                                    r.status === 'PASS'
                                      ? 'status-pass'
                                      : r.status === 'FAIL'
                                      ? 'status-fail'
                                      : 'status-warn'
                                  }`}
                                >
                                  {r.status}
                                </span>
                              </td>
                              <td className="rule-msg-cell">{r.message || '—'}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ) : (
                    <div className="clean-empty-box">
                      <p>No deterministic validation rules were executed for this document.</p>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* OPTION 6: DUPLICATE DETECTION */}
            {activeSection === 'duplicates' && (
              <div className="panel-section">
                <div className="panel-header">
                  <div className="panel-title-wrap">
                    <Copy size={20} className="panel-icon text-blue" />
                    <div>
                      <h3 className="panel-title">Duplicate Document Detection</h3>
                      <p className="panel-desc">Cross-repository vector similarity & textual fingerprint comparison</p>
                    </div>
                  </div>
                  <span className={`strip-status-pill ${duplicates?.has_duplicates ? 'pill-warning' : 'pill-success'}`}>
                    {duplicates?.has_duplicates ? `${duplicates.matches?.length || 0} Matches` : 'Unique Record'}
                  </span>
                </div>

                <div className="panel-body">
                  {aiDuplicateAssessment && (
                    <div className="ai-narrative-card">
                      <Sparkles size={16} className="text-accent" />
                      <div>
                        <strong>AI Uniqueness & Repository Assessment</strong>
                        <p>{aiDuplicateAssessment}</p>
                      </div>
                    </div>
                  )}

                  {duplicates?.has_duplicates ? (
                    <div className="clean-table-card">
                      <table className="clean-data-table">
                        <thead>
                          <tr>
                            <th>Matched Document ID</th>
                            <th style={{ width: '140px' }}>Similarity Score</th>
                            <th style={{ width: '160px' }}>Duplicate Type</th>
                          </tr>
                        </thead>
                        <tbody>
                          {duplicates.matches?.map((m, i) => (
                            <tr key={i}>
                              <td className="mono">
                                <Link to={`/documents/${m.matched_document_id}`} className="doc-link">
                                  {m.matched_document_id}
                                </Link>
                              </td>
                              <td>
                                <strong>{(m.similarity_score * 100).toFixed(1)}%</strong>
                              </td>
                              <td>
                                <span className="type-badge capitalize">{m.duplicate_type}</span>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ) : (
                    <div className="status-banner-card banner-success">
                      <div className="banner-icon-wrap">
                        <CheckCircle2 size={24} />
                      </div>
                      <div>
                        <strong>No Duplicate Documents Found</strong>
                        <p>This document is unique across the entire document index.</p>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* OPTION 7: ANOMALY DETECTION */}
            {activeSection === 'anomaly' && (
              <div className="panel-section">
                <div className="panel-header">
                  <div className="panel-title-wrap">
                    <AlertTriangle size={20} className={`panel-icon ${anomaly?.is_anomaly ? 'text-danger' : 'text-success'}`} />
                    <div>
                      <h3 className="panel-title">Isolation Forest Anomaly Detection</h3>
                      <p className="panel-desc">Unsupervised machine learning analysis identifying statistical outliers</p>
                    </div>
                  </div>
                  <span className={`strip-status-pill ${anomaly?.is_anomaly ? 'pill-danger' : 'pill-success'}`}>
                    {anomaly?.is_anomaly ? 'Outlier Flagged' : 'Normal Cluster'}
                  </span>
                </div>

                <div className="panel-body">
                  {aiAnomalyAssessment && (
                    <div className="ai-narrative-card">
                      <Sparkles size={16} className="text-accent" />
                      <div>
                        <strong>AI Anomaly & Outlier Assessment</strong>
                        <p>{aiAnomalyAssessment}</p>
                      </div>
                    </div>
                  )}

                  {aiRiskNarrative && (
                    <div className="ai-narrative-card" style={{ borderColor: 'rgba(239, 68, 68, 0.25)', background: 'rgba(239, 68, 68, 0.04)' }}>
                      <AlertTriangle size={16} className="text-danger" />
                      <div>
                        <strong>Fiscal Risk & Integrity Narrative</strong>
                        <p>{aiRiskNarrative}</p>
                      </div>
                    </div>
                  )}

                  <div className={`status-banner-card ${anomaly?.is_anomaly ? 'banner-danger' : 'banner-success'}`}>
                    <div className="banner-icon-wrap">
                      {anomaly?.is_anomaly ? <AlertTriangle size={24} /> : <CheckCircle2 size={24} />}
                    </div>
                    <div>
                      <strong>
                        {anomaly?.is_anomaly
                          ? 'Document Flagged as Statistical Outlier'
                          : 'Document Within Normal Feature Distribution'}
                      </strong>
                      <p>
                        {anomaly?.is_anomaly
                          ? 'Features of this document (e.g. amount, text density, or field count) deviate significantly from historical patterns. Review recommended.'
                          : 'Evaluated feature vectors align closely with standard historical documents.'}
                      </p>
                    </div>
                  </div>

                  <div className="anomaly-scores-grid">
                    <div className="score-box card">
                      <span className="score-label">Anomaly Score</span>
                      <strong className="score-val mono">
                        {anomaly?.anomaly_score != null ? anomaly.anomaly_score.toFixed(6) : '—'}
                      </strong>
                      <span className="score-sub">&lt; 0.0 indicates higher outlier tendency</span>
                    </div>
                    <div className="score-box card">
                      <span className="score-label">Decision Function</span>
                      <strong className="score-val mono">
                        {anomaly?.decision_function_score != null ? anomaly.decision_function_score.toFixed(6) : '—'}
                      </strong>
                      <span className="score-sub">Model boundary threshold score</span>
                    </div>
                  </div>

                  {anomaly?.features && Object.keys(anomaly.features).length > 0 && (
                    <div className="clean-table-card" style={{ marginTop: '1.25rem' }}>
                      <div className="table-header-title">Evaluated Feature Vectors</div>
                      <table className="clean-data-table">
                        <thead>
                          <tr>
                            <th>Feature Vector</th>
                            <th>Numeric Value</th>
                          </tr>
                        </thead>
                        <tbody>
                          {Object.entries(anomaly.features).map(([fKey, fVal]) => (
                            <tr key={fKey}>
                              <td className="field-name-cell">
                                <span className="field-key-name">{fKey.replace(/_/g, ' ')}</span>
                              </td>
                              <td className="mono">
                                {typeof fVal === 'number' ? fVal.toLocaleString() : String(fVal)}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* OPTION 8: RAW OCR TEXT */}
            {activeSection === 'rawtext' && (
              <div className="panel-section">
                <div className="panel-header">
                  <div className="panel-title-wrap">
                    <FileCode size={20} className="panel-icon text-primary" />
                    <div>
                      <h3 className="panel-title">Cleaned OCR Text Output</h3>
                      <p className="panel-desc">Normalized text stream extracted by the Tesseract engine</p>
                    </div>
                  </div>
                  <button
                    className="btn btn-secondary btn-sm"
                    onClick={() => handleCopyText(content?.cleaned_text || content?.raw_text)}
                  >
                    {copied ? <Check size={14} /> : <Clipboard size={14} />}
                    <span>{copied ? 'Copied' : 'Copy Full Text'}</span>
                  </button>
                </div>

                <div className="panel-body">
                  <div className="ocr-text-viewer">
                    {content?.cleaned_text || content?.raw_text || 'No extracted text found for this document.'}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

