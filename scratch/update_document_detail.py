import os

source_path = r"c:\docs\Downloads\My_Projects\Nexora\frontend\src\pages\DocumentDetailPage.jsx"

with open(source_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

# Find the start of STATE 3
cutoff_idx = -1
for i, line in enumerate(lines):
    if "STATE 3: COMPLETED ANALYSIS" in line:
        cutoff_idx = i
        break

if cutoff_idx == -1:
    print("Could not find STATE 3 marker")
    exit(1)

print(f"Found STATE 3 at line {cutoff_idx + 1}")

state_3_code = """      {/* STATE 3: COMPLETED ANALYSIS — CLEAN OPTION BUTTONS LAYOUT */}
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
            {/* OPTION 1: AUDIT SUMMARY */}
            {activeSection === 'overview' && (
              <div className="panel-section">
                <div className="panel-header">
                  <div className="panel-title-wrap">
                    <FileCheck size={20} className="panel-icon text-primary" />
                    <div>
                      <h3 className="panel-title">Executive Audit Briefing</h3>
                      <p className="panel-desc">Structural evaluation, detected counterparty roles, and synthesized findings</p>
                    </div>
                  </div>
                </div>

                <div className="panel-body">
                  <div className="audit-brief-card">
                    <p className="audit-brief-text">
                      {ai.executive_summary ||
                        `This is a ${analysis.document_type || 'unclassified'} document (${analysis.filename}). Automated audits have extracted ${fieldEntries.length} fields with standard validation rules applied.`}
                    </p>
                  </div>

                  {aiRelationships.length > 0 && (
                    <div className="audit-roles-section">
                      <h4 className="sub-heading">Detected Counterparty Roles</h4>
                      <div className="roles-tags-wrap">
                        {aiRelationships.map((rel, i) => (
                          <div key={i} className="counterparty-role-tag">
                            <span className="entity-text">{rel.entity}</span>
                            <ArrowRight size={12} className="role-arrow" />
                            <span className="role-text">{rel.role}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {aiInsights.length > 0 && (
                    <div className="audit-insights-section">
                      <h4 className="sub-heading">
                        <Lightbulb size={15} /> Key Audit Observations
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

                  <div className="transaction-ids-card">
                    <h4 className="sub-heading">Primary Transaction Identifiers</h4>
                    <div className="tid-table">
                      <div className="tid-row">
                        <span className="tid-key">Document Type</span>
                        <span className="tid-val capitalize">{analysis.document_type || 'Unclassified'}</span>
                      </div>
                      <div className="tid-row">
                        <span className="tid-key">Gross Total</span>
                        <span className="tid-val text-accent font-bold">
                          {totalAmountVal != null ? formatRupees(totalAmountVal) : '—'}
                        </span>
                      </div>
                      <div className="tid-row">
                        <span className="tid-key">Invoice / Ref #</span>
                        <span className="tid-val mono">{invoiceNoVal || '—'}</span>
                      </div>
                      <div className="tid-row">
                        <span className="tid-key">Purchase Order (PO)</span>
                        <span className="tid-val mono">{poNoVal || '—'}</span>
                      </div>
                      <div className="tid-row">
                        <span className="tid-key">Vendor / Issuer</span>
                        <span className="tid-val">{vendorVal || '—'}</span>
                      </div>
                      <div className="tid-row">
                        <span className="tid-key">Primary Date</span>
                        <span className="tid-val">{primaryDateVal || '—'}</span>
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
"""

new_content = "".join(lines[:cutoff_idx]) + state_3_code + "\n"

with open(source_path, "w", encoding="utf-8") as f:
    f.write(new_content)

print(f"Successfully updated {source_path}")
