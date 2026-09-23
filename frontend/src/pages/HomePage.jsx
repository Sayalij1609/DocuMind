import { useNavigate } from 'react-router-dom';
import {
  ArrowRight,
  Upload,
  LayoutDashboard,
  Layers,
  ShieldCheck,
  Copy,
  AlertTriangle,
  Cpu,
  Sparkles,
  Activity,
  CheckCircle2,
  FileText,
  Receipt,
  FileCheck,
  Building2,
  FileSpreadsheet,
  Zap,
  Calculator,
  Landmark,
  TrendingUp,
} from 'lucide-react';
import './HomePage.css';

export default function HomePage() {
  const navigate = useNavigate();

  const supportedDocs = [
    { name: 'Invoices', desc: 'B2B & Vendor tax bills', icon: FileText, tag: 'Line-item extraction' },
    { name: 'Bank Statements', desc: 'Financial audit trails', icon: Building2, tag: 'Debit & credit balances' },
    { name: 'Salary Slips', desc: 'Payroll & pay advices', icon: Landmark, tag: 'Gross, net & deductions' },
    { name: 'Receipts', desc: 'POS & expense slips', icon: Receipt, tag: 'Merchant & totals' },
    { name: 'Purchase Orders', desc: 'Procurement contracts', icon: FileCheck, tag: 'SKU & order terms' },
    { name: 'Utility & Bills', desc: 'Energy & service slips', icon: FileSpreadsheet, tag: 'Due dates & meters' },
    { name: 'Tax Documents', desc: 'Form 16 & returns', icon: FileSpreadsheet, tag: 'PAN & TDS computations' },
    { name: 'Insurance Claims', desc: 'Policy & incident forms', icon: ShieldCheck, tag: 'Coverage & claim IDs' },
    { name: 'Credit & Debit Notes', desc: 'Adjustment memos', icon: Calculator, tag: 'Dispute & refund notes' },
    { name: 'Financial Statements', desc: 'P&L & Balance sheets', icon: TrendingUp, tag: 'Ledger reconciliation' },
  ];

  const capabilities = [
    {
      icon: Cpu,
      title: 'Multimodal Document Vision',
      desc: 'Combines rendered 200 DPI imagery, spatial 2D bounding boxes, and high-precision OCR tokens for deep layout awareness.',
      tag: 'LayoutLMv3 + OCR Engine',
      link: '/documents',
    },
    {
      icon: Activity,
      title: 'Automated ML Classification',
      desc: 'Sub-second TF-IDF and SGD classifier trained across standard business schemas to categorize incoming files instantly.',
      tag: 'SGD + TF-IDF Classifier',
      link: '/dashboard',
    },
    {
      icon: Layers,
      title: 'Intelligent Entity Extraction',
      desc: 'Robust extraction strategies parsing invoice numbers, dates, addresses, tax breakdowns, currencies, and total amounts.',
      tag: 'Field Extraction Engine',
      link: '/documents',
    },
    {
      icon: ShieldCheck,
      title: 'Deterministic Rule Verification',
      desc: 'Automated compliance engine running 6 mathematical and schema checks (Subtotal + Tax = Total, date sequences).',
      tag: '6 Compliance Rules',
      link: '/documents',
    },
    {
      icon: Copy,
      title: 'Dual-Tier Deduplication',
      desc: 'Cryptographic SHA-256 hash matching for exact duplicates paired with cosine similarity vector scoring for near-duplicates.',
      tag: 'Cosine Similarity ≥ 0.85',
      link: '/duplicates',
    },
    {
      icon: AlertTriangle,
      title: 'Unsupervised Anomaly Detection',
      desc: 'Isolation Forest outlier detection evaluating multi-dimensional feature vectors to surface suspicious or irregular files.',
      tag: 'Isolation Forest Model',
      link: '/anomalies',
    },
  ];

  const pipelineSteps = [
    { num: '01', name: 'Ingestion', desc: 'PDF / JPG / PNG' },
    { num: '02', name: 'Layout & OCR', desc: 'Tesseract + BBoxes' },
    { num: '03', name: 'Classifier', desc: 'TF-IDF + SGD' },
    { num: '04', name: 'Extraction', desc: 'Regex & LLM Schema' },
    { num: '05', name: 'Validation', desc: '6 Business Rules' },
    { num: '06', name: 'Deduplication', desc: 'Cosine Vector' },
    { num: '07', name: 'Anomaly', desc: 'Isolation Forest' },
  ];

  const stats = [
    { value: '7', label: 'Pipeline Stages', sub: 'End-to-end automation' },
    { value: '99.4%', label: 'Classifier Accuracy', sub: 'Trained model baseline' },
    { value: '6/6', label: 'Math Compliance Rules', sub: 'Automated reconciliation' },
    { value: '< 1.2s', label: 'Processing Speed', sub: 'Average ingestion latency' },
  ];

  const intelligenceModules = [
    {
      icon: Layers,
      title: 'Semantic Field Extraction',
      badge: 'Data Extraction',
      tagline: 'What is extracted from your document:',
      items: [
        { label: 'Counterparty Entities', desc: 'Vendor & customer names, physical addresses, contact info, and tax registrations (GSTIN/PAN/VAT).' },
        { label: 'Commercial References', desc: 'Invoice numbers, Purchase Order (PO) numbers, Challan references, and policy IDs.' },
        { label: 'Audit Chronology', desc: 'Document issue dates, payment due dates, delivery dates, and billing periods.' },
        { label: 'Line-Item Breakdown', desc: 'Full itemized SKU descriptions, quantities, unit rates, and row extended amounts.' },
        { label: 'Financial Liabilities', desc: 'Subtotal, applied tax amounts, discounts, and gross liability in Indian Rupees (₹).' },
      ],
      benefit: 'Eliminates 100% of manual data entry and feeds structured JSON directly into your ERP.',
      link: '/documents',
    },
    {
      icon: ShieldCheck,
      title: 'Deterministic Rule Validation',
      badge: 'Compliance & Quality',
      tagline: 'What is checked and enforced:',
      items: [
        { label: 'Mandatory Field Integrity', desc: 'Flags missing invoice numbers, unstated vendor names, or missing totals.' },
        { label: 'Format & Type Schema', desc: 'Verifies alphanumeric invoice structures, valid GST formats, and parseable dates.' },
        { label: 'Timeline Sequence Logic', desc: 'Verifies that issue date chronologically precedes due date and delivery date.' },
        { label: 'Boundary & Sign Audit', desc: 'Enforces positive monetary amounts and non-zero quantities where mandated.' },
      ],
      benefit: 'Guarantees 100% data completeness and statutory conformity before ledger posting.',
      link: '/documents',
    },
    {
      icon: Calculator,
      title: 'Mathematical Consistency Audit',
      badge: 'Arithmetic Verification',
      tagline: 'What mathematical checks run:',
      items: [
        { label: 'Gross Reconciliation', desc: 'Recalculates: Subtotal + Tax Amount - Applied Discounts = Stated Gross Total.' },
        { label: 'Line-Item Multiplication', desc: 'Audits every row: Quantity × Unit Price = Stated Extended Line Amount.' },
        { label: 'Tax Rate Consistency', desc: 'Verifies statutory GST/sales tax percentage application against item totals.' },
        { label: 'Discrepancy Reporting', desc: 'Pinpoints the exact discrepancy figure down to the paisa (₹).' },
      ],
      benefit: 'Catches hidden calculation errors, billing inflation, and rounding discrepancies instantly.',
      link: '/documents',
    },
    {
      icon: Copy,
      title: 'Dual-Tier Duplicate Detection',
      badge: 'Fraud Prevention',
      tagline: 'What duplicate vectors are checked:',
      items: [
        { label: 'SHA-256 Exact Hash', desc: 'Catches 100% identical files submitted under renamed or altered filenames.' },
        { label: 'TF-IDF Cosine Similarity', desc: 'Surfaces near-duplicates (similarity ≥ 85%) with minor date or line-item edits.' },
        { label: 'Vendor + Number Collision', desc: 'Alerts immediately when a duplicate invoice number is submitted by the same vendor.' },
        { label: 'Side-by-Side Comparison', desc: 'Provides match confidence %, previous upload dates, and original file references.' },
      ],
      benefit: 'Completely eliminates duplicate vendor disbursements and accidental double payments.',
      link: '/duplicates',
    },
    {
      icon: AlertTriangle,
      title: 'Statistical Anomaly & Outlier Scoring',
      badge: 'Risk Intelligence',
      tagline: 'What outlier indicators are flagged:',
      items: [
        { label: 'Isolation Forest Model', desc: 'Multidimensional unsupervised ML model scores spend behavior against history.' },
        { label: 'Outsized Transaction Alerting', desc: 'Flags invoices with totals that abnormally exceed historical vendor averages.' },
        { label: 'Atypical Billing Patterns', desc: 'Identifies off-cycle submissions or unexpected spikes in billing frequency.' },
        { label: 'Automated Risk Verdict', desc: 'Labels files as "Normal Record" vs. "Outlier Flagged / Review Recommended".' },
      ],
      benefit: 'Alerts controllers to anomalous spend and rogue transactions before funds are wired.',
      link: '/anomalies',
    },
    {
      icon: Sparkles,
      title: 'Executive Audit Findings & Narrative',
      badge: 'Executive Intelligence',
      tagline: 'What insights are delivered:',
      items: [
        { label: 'Executive Audit Briefing', desc: 'Concise corporate narrative detailing transaction nature, counterparty, and amounts.' },
        { label: '3-Way Match Verification', desc: 'Actionable advisory cross-referencing invoice claims with PO and Delivery Challan.' },
        { label: 'Tax & Compliance Notes', desc: 'Verifies vendor tax deduction, withholding status, and statutory GST notes.' },
        { label: 'Disbursement Advisory', desc: 'Clear, prioritized recommendations for accounts payable controllers.' },
      ],
      benefit: 'Empowers finance leaders with instantaneous visibility without reading dense invoices.',
      link: '/dashboard',
    },
  ];

  return (
    <div className="homepage animate-fade-in">
      {/* Decorative Ambient Shapes */}
      <div className="hero-bg-shapes" aria-hidden="true">
        <div className="shape shape-1" />
        <div className="shape shape-2" />
        <div className="shape shape-3" />
      </div>

      {/* Hero Section — 2-Column Split */}
      <section className="hero-split-section">
        <div className="hero-content">
          <div className="hero-badge">
            <span className="pulse-dot" />
            <Sparkles size={13} className="hero-badge-icon" />
            <span>DocuMind Cognitive Document Intelligence</span>
          </div>

          <h1 className="hero-title">
            Transform Raw Documents into{' '}
            <span className="text-gradient">Structured Business Intelligence</span>
          </h1>

          <p className="hero-subtitle">
            An enterprise-grade document intelligence platform that automatically ingests business
            files, classifies document types, extracts structured entities, reconciles financial
            arithmetic, and flags anomalies in seconds.
          </p>

          {/* Quick value highlights */}
          <div className="hero-highlights">
            <div className="highlight-item">
              <CheckCircle2 size={16} className="highlight-icon" />
              <span>Multi-format Vision & OCR</span>
            </div>
            <div className="highlight-item">
              <CheckCircle2 size={16} className="highlight-icon" />
              <span>Deterministic Math Audit</span>
            </div>
            <div className="highlight-item">
              <CheckCircle2 size={16} className="highlight-icon" />
              <span>Isolation Forest Anomalies</span>
            </div>
          </div>

          {/* Call to Action Buttons */}
          <div className="hero-actions">
            <button className="btn-hero-primary" onClick={() => navigate('/upload')}>
              <Upload size={18} />
              <span>Upload Document</span>
              <ArrowRight size={16} />
            </button>
            <button className="btn-hero-secondary" onClick={() => navigate('/dashboard')}>
              <LayoutDashboard size={18} />
              <span>Explore Dashboard</span>
            </button>
          </div>

          {/* Trust telemetry bar */}
          <div className="hero-telemetry-bar">
            <div className="telemetry-stat">
              <span className="telemetry-val">100%</span>
              <span className="telemetry-lbl">Arithmetic Precision</span>
            </div>
            <div className="telemetry-divider" />
            <div className="telemetry-stat">
              <span className="telemetry-val">Zero</span>
              <span className="telemetry-lbl">Manual Data Entry</span>
            </div>
            <div className="telemetry-divider" />
            <div className="telemetry-stat">
              <span className="telemetry-val">Real-time</span>
              <span className="telemetry-lbl">Semantic Copilot</span>
            </div>
          </div>
        </div>

        {/* Hero Right Visual: 3D Illustration + Floating Live Telemetry Cards */}
        <div className="hero-visual-col">
          <div className="hero-illustration-wrapper">
            {/* Glow backdrop behind illustration */}
            <div className="illustration-glow-backdrop" aria-hidden="true" />

            {/* Custom 3D AI Document Pipeline Illustration */}
            <img
              src="/hero-illustration.jpg"
              alt="DocuMind AI Document Processing Architecture Illustration"
              className="hero-illustration-img"
              loading="eager"
            />

            {/* Floating Live Card 1: Top-Right Document Classified */}
            <div className="floating-card floating-card-top animate-float-slow">
              <div className="floating-card-icon success">
                <CheckCircle2 size={16} />
              </div>
              <div className="floating-card-body">
                <div className="floating-card-title">INVOICE CLASSIFIED</div>
                <div className="floating-card-sub">
                  Confidence: <strong>99.8% (SGD Engine)</strong>
                </div>
              </div>
            </div>

            {/* Floating Live Card 2: Bottom-Left Reconciled Extraction */}
            <div className="floating-card floating-card-bottom animate-float-delayed">
              <div className="floating-card-icon blue">
                <Zap size={16} />
              </div>
              <div className="floating-card-body">
                <div className="floating-card-title">LIVE EXTRACTION AUDIT</div>
                <div className="floating-card-sub">
                  Total: <strong>₹14,250.00</strong> · Subtotal + Tax <span className="tag-pass">PASS ✓</span>
                </div>
              </div>
            </div>

            {/* Floating Live Badge: Bottom-Right Anomaly Score */}
            <div className="floating-badge-chip">
              <span className="chip-indicator" />
              <span>Anomaly Risk: 0.02 · Clean File</span>
            </div>
          </div>
        </div>
      </section>

      {/* Target Supported Document Types Section */}
      <section className="supported-docs-section">
        <div className="section-header-compact">
          <div className="section-eyebrow">Supported Document Types</div>
          <h2 className="section-title-compact">Built for Every Financial & Business Format</h2>
        </div>

        <div className="docs-grid">
          {supportedDocs.map((doc, i) => {
            const DocIcon = doc.icon;
            return (
              <div className="doc-type-card" key={i} onClick={() => navigate('/upload')}>
                <div className="doc-icon-box">
                  <DocIcon size={20} />
                </div>
                <div className="doc-info">
                  <h4 className="doc-name">{doc.name}</h4>
                  <p className="doc-desc">{doc.desc}</p>
                </div>
                <span className="doc-tag">{doc.tag}</span>
              </div>
            );
          })}
        </div>
      </section>

      {/* Pipeline Visualizer Strip */}
      <section className="pipeline-section">
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
              <span className="pill pill-tech">FastAPI + PostgreSQL + Groq LLM</span>
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
                <span className="sample-label">Real-time Pipeline Audit:</span>{' '}
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
                <div className="sample-field-val">₹14,250.00</div>
              </div>
              <div className="sample-field-item">
                <div className="sample-field-key">Validation Audit</div>
                <div className="sample-field-val success">✓ 6/6 Rules PASS</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Comprehensive Intelligence & Verification Breakdown Section */}
      <section className="intelligence-breakdown-section">
        <div className="section-header">
          <div className="section-eyebrow">Document Intelligence Architecture</div>
          <h2 className="section-title">What DocuMind Analyzes, Verifies & Extracts</h2>
          <p className="section-desc">
            Explore how every incoming business document undergoes rigorous entity extraction,
            mathematical reconciliation, duplicate checking, and anomaly scoring.
          </p>
        </div>

        <div className="intelligence-modules-grid">
          {intelligenceModules.map((mod, idx) => {
            const ModIcon = mod.icon;
            return (
              <div key={idx} className="intelligence-module-card">
                <div className="module-card-header">
                  <div className="module-icon-wrap">
                    <ModIcon size={22} />
                  </div>
                  <div className="module-header-meta">
                    <span className="module-badge">{mod.badge}</span>
                    <h3 className="module-title">{mod.title}</h3>
                  </div>
                </div>

                <p className="module-tagline">{mod.tagline}</p>

                <ul className="module-items-list">
                  {mod.items.map((item, itemIdx) => (
                    <li key={itemIdx} className="module-item">
                      <span className="item-bullet">▸</span>
                      <div>
                        <strong className="item-label">{item.label}:</strong>{' '}
                        <span className="item-desc">{item.desc}</span>
                      </div>
                    </li>
                  ))}
                </ul>

                <div className="module-card-footer">
                  <div className="module-benefit">
                    <span className="benefit-label">Enterprise Value:</span> {mod.benefit}
                  </div>
                  <button className="module-nav-link" onClick={() => navigate(mod.link)}>
                    <span>Inspect Pipeline</span>
                    <ArrowRight size={13} />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* Metrics Strip */}
      <section className="metrics-strip">
        {stats.map((s, i) => (
          <div className="stat-box" key={i}>
            <div className="stat-value">{s.value}</div>
            <div className="stat-label">{s.label}</div>
            <div className="stat-sub">{s.sub}</div>
          </div>
        ))}
      </section>

      {/* Capabilities Section */}
      <section className="capabilities-section">
        <div className="section-header">
          <div className="section-eyebrow">Enterprise Capabilities</div>
          <h2 className="section-title">Engineered for Complex Document Understanding</h2>
          <p className="section-desc">
            From raw visual pixels to reconciled ledger data, DocuMind combines computer vision,
            probabilistic machine learning, and semantic reasoning.
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
                  <ArrowRight size={13} />
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* CTA Banner */}
      <section className="cta-banner">
        <div className="cta-banner-content">
          <h2 className="cta-title">Start Processing Documents with DocuMind Today</h2>
          <p className="cta-subtitle">
            Experience automated document classification, deep entity extraction, math reconciliation,
            and outlier detection on your own business documents.
          </p>
          <div className="cta-buttons">
            <button className="btn-hero-primary" onClick={() => navigate('/upload')}>
              <Upload size={18} />
              <span>Upload Document Now</span>
              <ArrowRight size={16} />
            </button>
            <button className="btn-hero-secondary" onClick={() => navigate('/dashboard')}>
              <LayoutDashboard size={18} />
              <span>Open Analytics Dashboard</span>
            </button>
          </div>
        </div>
      </section>
    </div>
  );
}
