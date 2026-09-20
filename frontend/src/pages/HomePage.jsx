import { useNavigate } from 'react-router-dom';
import {
  ArrowRight,
  Upload,
  LayoutDashboard,
  Layers,
  ShieldCheck,
  Copy,
  AlertTriangle,
  FileText,
  Cpu,
  Sparkles,
  CheckCircle2,
  Activity,
  FileSearch,
} from 'lucide-react';
import './HomePage.css';

export default function HomePage() {
  const navigate = useNavigate();

  const capabilities = [
    {
      icon: Cpu,
      title: 'Multimodal Document Vision',
      desc: 'LayoutLMv3 integration combining 200 DPI rendered page imagery, spatial bounding boxes, and OCR tokens for deep layout awareness.',
      tag: 'LayoutLMv3 + OCR',
      link: '/documents',
    },
    {
      icon: Activity,
      title: 'Automated ML Classification',
      desc: 'High-speed TF-IDF + SGD classification engine trained to distinguish invoices, receipts, contracts, forms, and financial records.',
      tag: 'SGD + TF-IDF Classifier',
      link: '/dashboard',
    },
    {
      icon: Layers,
      title: 'Intelligent Field Extraction',
      desc: 'Deterministic extraction strategy extracting invoice numbers, issue dates, line items, tax breakdowns, and total amounts.',
      tag: 'Extracted Field Registry',
      link: '/documents',
    },
    {
      icon: ShieldCheck,
      title: 'Deterministic Rule Engine',
      desc: 'Six automated business compliance checks verifying arithmetic integrity (Subtotal + Tax = Total), date sequences, and schema requirements.',
      tag: '6 Compliance Rules',
      link: '/documents',
    },
    {
      icon: Copy,
      title: 'Dual-Tier Deduplication',
      desc: 'SHA-256 content hashing for exact duplicate filtering paired with TF-IDF cosine similarity vector comparison for near-duplicates.',
      tag: 'Cosine Similarity ≥ 0.85',
      link: '/duplicates',
    },
    {
      icon: AlertTriangle,
      title: 'Unsupervised Anomaly Detection',
      desc: 'Isolation Forest outlier detection evaluating multi-dimensional feature vectors to identify irregular invoices and compliance anomalies.',
      tag: 'Isolation Forest Model',
      link: '/anomalies',
    },
  ];

  const pipelineSteps = [
    { num: '01', name: 'Ingestion', desc: 'PDF / JPG / PNG' },
    { num: '02', name: 'Layout & OCR', desc: 'Tesseract + BBoxes' },
    { num: '03', name: 'Classifier', desc: 'TF-IDF + SGD' },
    { num: '04', name: 'Extraction', desc: 'Regex & Heuristics' },
    { num: '05', name: 'Validation', desc: '6 Business Rules' },
    { num: '06', name: 'Deduplication', desc: 'Cosine Similarity' },
    { num: '07', name: 'Anomaly', desc: 'Isolation Forest' },
  ];

  const stats = [
    { value: '7', label: 'Pipeline Stages' },
    { value: '99.4%', label: 'Classifier Baseline' },
    { value: '6', label: 'Compliance Rules' },
    { value: '100%', label: 'Arithmetic Precision' },
  ];

  return (
    <div className="homepage animate-fade-in">
      {/* Decorative Background Shapes */}
      <div className="hero-bg-shapes" aria-hidden="true">
        <div className="shape shape-1" />
        <div className="shape shape-2" />
        <div className="shape shape-3" />
      </div>

      {/* Hero Section */}
      <section className="hero-section">
        <div className="hero-badge">
          <span className="pulse-dot" />
          <span>Documind Intelligent Document Processing</span>
        </div>

        <h1 className="hero-title">
          Transform Documents into{' '}
          <span className="text-gradient">Structured Intelligence</span>
        </h1>

        <p className="hero-subtitle">
          A production-grade document intelligence platform. Ingest PDFs and images,
          classify categories, extract key entities, enforce compliance rules, and detect
          anomalies — all in seconds.
        </p>

        <div className="hero-actions">
          <button className="btn-hero-primary" onClick={() => navigate('/dashboard')}>
            <LayoutDashboard size={18} />
            Open Dashboard
            <ArrowRight size={16} />
          </button>
          <button className="btn-hero-secondary" onClick={() => navigate('/upload')}>
            <Upload size={18} />
            Upload Document
          </button>
        </div>

        {/* Pipeline Visualizer */}
        <div className="pipeline-visualizer">
          <div className="visualizer-header">
            <div className="visualizer-title">
              <Sparkles size={16} />
              End-to-End Processing Architecture
            </div>
            <div className="visualizer-status-pills">
              <span className="pill pill-active">
                <span className="pill-dot" />
                Pipeline Active
              </span>
              <span className="pill pill-tech">FastAPI + PostgreSQL</span>
            </div>
          </div>

          <div className="visualizer-flow">
            {pipelineSteps.map((step, i) => (
              <div className="flow-step" key={step.num}>
                <span className="flow-step-num">{step.num}</span>
                <div className="flow-step-name">{step.name}</div>
                <div className="flow-step-desc">{step.desc}</div>
                {i < pipelineSteps.length - 1 && (
                  <div className="flow-connector" aria-hidden="true" />
                )}
              </div>
            ))}
          </div>

          {/* Sample Parsed Preview */}
          <div className="sample-parsed-card">
            <div className="sample-parsed-header">
              <div>
                <span className="sample-label">Live Document Sample:</span>{' '}
                <span className="sample-filename">acme_corp_invoice_1092.pdf</span>
              </div>
              <div className="sample-doc-meta">
                Classification: <strong>INVOICE (99.8%)</strong> | Status: <strong>COMPLETED</strong>
              </div>
            </div>

            <div className="sample-fields-grid">
              <div className="sample-field-item">
                <div className="sample-field-key">Vendor Name</div>
                <div className="sample-field-val">Acme Corporation</div>
              </div>
              <div className="sample-field-item">
                <div className="sample-field-key">Invoice Number</div>
                <div className="sample-field-val">INV-2026-1092</div>
              </div>
              <div className="sample-field-item">
                <div className="sample-field-key">Total Amount</div>
                <div className="sample-field-val">$14,250.00</div>
              </div>
              <div className="sample-field-item">
                <div className="sample-field-key">Validation Audit</div>
                <div className="sample-field-val success">✓ 6/6 Rules PASS</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Stats Strip */}
      <section className="metrics-strip">
        {stats.map((s, i) => (
          <div className="stat-box" key={i}>
            <div className="stat-value">{s.value}</div>
            <div className="stat-label">{s.label}</div>
          </div>
        ))}
      </section>

      {/* Capabilities Section */}
      <section className="capabilities-section">
        <div className="section-header">
          <div className="section-eyebrow">Comprehensive Capabilities</div>
          <h2 className="section-title">Built for Complex Document Intelligence</h2>
          <p className="section-desc">
            From raw visual pixels to verified financial ledger records, Documind delivers
            end-to-end automation with full explainability.
          </p>
        </div>

        <div className="capabilities-grid">
          {capabilities.map((item, idx) => {
            const Icon = item.icon;
            return (
              <div
                key={idx}
                className="capability-card"
                onClick={() => navigate(item.link)}
              >
                <div className="capability-icon-wrap">
                  <Icon size={22} />
                </div>
                <h3 className="capability-title">{item.title}</h3>
                <p className="capability-desc">{item.desc}</p>
                <div className="capability-footer-tag">
                  <span>{item.tag}</span>
                  <ArrowRight size={12} />
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* CTA Banner */}
      <section className="cta-banner">
        <h2 className="cta-title">Start Processing Documents with Documind</h2>
        <p className="cta-subtitle">
          Experience automated classification, deep extraction, rule validation, and outlier
          detection on your own invoices, contracts, and receipts.
        </p>
        <div className="cta-buttons">
          <button className="btn-hero-primary" onClick={() => navigate('/upload')}>
            <Upload size={18} />
            Upload Document Now
          </button>
          <button className="btn-hero-secondary" onClick={() => navigate('/dashboard')}>
            <LayoutDashboard size={18} />
            View Live Dashboard
          </button>
        </div>
      </section>
    </div>
  );
}
