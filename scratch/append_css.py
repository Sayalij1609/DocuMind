css_code = """
/* ==========================================================================
   CLEAN OPTION BUTTONS & UNCONGESTED ANALYSIS VIEW
   ========================================================================== */

.clean-analysis-wrapper {
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
  margin-top: var(--space-4);
}

/* 1. Sleek Top Overview Strip */
.clean-audit-strip {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 24px;
  background: #ffffff;
  border-radius: var(--radius-lg);
  border: 1px solid rgba(15, 23, 42, 0.08);
  box-shadow: 0 4px 20px -2px rgba(15, 23, 42, 0.04);
  flex-wrap: wrap;
  gap: 16px;
}

.strip-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.strip-label {
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-tertiary);
}

.strip-val-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
}

.strip-value {
  font-size: 16px;
  font-weight: 700;
  color: var(--text-primary);
}

.strip-sub {
  font-size: 11px;
  color: var(--text-muted);
}

.strip-divider {
  width: 1px;
  height: 40px;
  background: rgba(15, 23, 42, 0.08);
}

@media (max-width: 900px) {
  .strip-divider {
    display: none;
  }
}

.strip-status-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: 9999px;
  font-size: 12px;
  font-weight: 600;
}

.strip-status-pill.pill-success {
  background: rgba(16, 185, 129, 0.1);
  color: #059669;
  border: 1px solid rgba(16, 185, 129, 0.2);
}

.strip-status-pill.pill-warning {
  background: rgba(245, 158, 11, 0.1);
  color: #d97706;
  border: 1px solid rgba(245, 158, 11, 0.2);
}

.strip-status-pill.pill-danger {
  background: rgba(239, 68, 68, 0.1);
  color: #dc2626;
  border: 1px solid rgba(239, 68, 68, 0.2);
}

.download-report-cta {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 18px;
  font-size: 13px;
  font-weight: 600;
  border-radius: var(--radius-md);
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.25);
  transition: all 0.2s ease;
  white-space: nowrap;
}

.download-report-cta:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 6px 16px rgba(37, 99, 235, 0.35);
}

/* 2. Clean Option Buttons Navigation */
.clean-options-container {
  padding: 16px 20px;
  background: #ffffff;
  border-radius: var(--radius-lg);
  border: 1px solid rgba(15, 23, 42, 0.08);
  box-shadow: 0 2px 10px rgba(15, 23, 42, 0.02);
}

.options-bar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;
}

.options-bar-title {
  font-size: 13px;
  font-weight: 700;
  color: var(--text-primary);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.options-bar-hint {
  font-size: 12px;
  color: var(--text-muted);
}

.clean-option-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.clean-opt-btn {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  padding: 10px 18px;
  border-radius: var(--radius-full);
  border: 1px solid rgba(15, 23, 42, 0.1);
  background: var(--bg-tertiary);
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  user-select: none;
}

.clean-opt-btn:hover {
  background: #f1f5f9;
  border-color: rgba(37, 99, 235, 0.3);
  color: var(--text-primary);
  transform: translateY(-1px);
}

.clean-opt-btn.active {
  background: #2563eb;
  border-color: #2563eb;
  color: #ffffff;
  box-shadow: 0 4px 14px rgba(37, 99, 235, 0.3);
}

.opt-icon-circle {
  display: flex;
  align-items: center;
  justify-content: center;
}

.clean-opt-btn.active .opt-icon-circle {
  color: #ffffff;
}

.opt-btn-label {
  white-space: nowrap;
}

.opt-btn-badge {
  font-size: 11px;
  padding: 2px 7px;
  border-radius: 9999px;
  background: rgba(15, 23, 42, 0.08);
  color: var(--text-secondary);
  font-weight: 700;
}

.clean-opt-btn.active .opt-btn-badge {
  background: rgba(255, 255, 255, 0.25);
  color: #ffffff;
}

.opt-btn-badge.badge-success {
  background: rgba(16, 185, 129, 0.15);
  color: #059669;
}
.clean-opt-btn.active .opt-btn-badge.badge-success {
  background: rgba(255, 255, 255, 0.3);
  color: #ffffff;
}

.opt-btn-badge.badge-warning {
  background: rgba(245, 158, 11, 0.15);
  color: #d97706;
}

.opt-btn-badge.badge-danger {
  background: rgba(239, 68, 68, 0.15);
  color: #dc2626;
}
.clean-opt-btn.active .opt-btn-badge.badge-danger {
  background: rgba(255, 255, 255, 0.3);
  color: #ffffff;
}

/* 3. Clean Content Panels */
.clean-content-panel {
  background: #ffffff;
  border-radius: var(--radius-lg);
  border: 1px solid rgba(15, 23, 42, 0.08);
  box-shadow: 0 4px 24px -2px rgba(15, 23, 42, 0.04);
  overflow: hidden;
}

.panel-section {
  padding: 24px 28px;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid rgba(15, 23, 42, 0.06);
  flex-wrap: wrap;
  gap: 16px;
}

.panel-title-wrap {
  display: flex;
  align-items: center;
  gap: 14px;
}

.panel-icon {
  width: 38px;
  height: 38px;
  padding: 8px;
  border-radius: var(--radius-md);
  background: var(--bg-tertiary);
  border: 1px solid rgba(15, 23, 42, 0.06);
}

.panel-title {
  font-size: 18px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 2px 0;
}

.panel-desc {
  font-size: 13px;
  color: var(--text-secondary);
  margin: 0;
}

.panel-search-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
  background: var(--bg-tertiary);
  padding: 8px 14px;
  border-radius: var(--radius-md);
  border: 1px solid rgba(15, 23, 42, 0.1);
  width: 240px;
}

.clean-search-input {
  border: none;
  background: transparent;
  outline: none;
  font-size: 13px;
  color: var(--text-primary);
  width: 100%;
}

/* Panel Body Elements */
.audit-brief-card {
  padding: 20px 24px;
  background: linear-gradient(135deg, rgba(37, 99, 235, 0.03) 0%, rgba(99, 102, 241, 0.05) 100%);
  border: 1px solid rgba(37, 99, 235, 0.12);
  border-left: 4px solid var(--accent-primary);
  border-radius: var(--radius-md);
  margin-bottom: 24px;
}

.audit-brief-text {
  font-size: 14.5px;
  line-height: 1.65;
  color: var(--text-primary);
  margin: 0;
}

.sub-heading {
  font-size: 14px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 12px 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.roles-tags-wrap {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 24px;
}

.counterparty-role-tag {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: var(--bg-tertiary);
  border: 1px solid rgba(15, 23, 42, 0.08);
  padding: 6px 12px;
  border-radius: var(--radius-md);
  font-size: 12px;
}

.entity-text {
  font-weight: 700;
  color: var(--text-primary);
}

.role-arrow {
  color: var(--text-muted);
}

.role-text {
  color: var(--accent-primary);
  font-weight: 600;
}

.audit-insights-section {
  margin-bottom: 24px;
}

.insights-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 12px;
}

.insight-card {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 12px 16px;
  background: var(--bg-tertiary);
  border-radius: var(--radius-md);
  border: 1px solid rgba(15, 23, 42, 0.06);
  font-size: 13px;
  line-height: 1.5;
  color: var(--text-primary);
}

.insight-check {
  color: var(--color-success);
  flex-shrink: 0;
  margin-top: 2px;
}

/* Transaction Identifiers Table */
.transaction-ids-card {
  background: #ffffff;
  border: 1px solid rgba(15, 23, 42, 0.08);
  border-radius: var(--radius-md);
  padding: 20px;
}

.tid-table {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 12px;
}

.tid-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  background: var(--bg-tertiary);
  border-radius: var(--radius-sm);
  border: 1px solid rgba(15, 23, 42, 0.05);
}

.tid-key {
  font-size: 12px;
  color: var(--text-secondary);
  font-weight: 500;
}

.tid-val {
  font-size: 13px;
  color: var(--text-primary);
  font-weight: 600;
}

/* Clean Tables */
.clean-table-card {
  border: 1px solid rgba(15, 23, 42, 0.08);
  border-radius: var(--radius-md);
  overflow: hidden;
  background: #ffffff;
}

.clean-data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.clean-data-table th {
  background: #f8fafc;
  color: var(--text-secondary);
  font-size: 11.5px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  padding: 12px 18px;
  text-align: left;
  border-bottom: 1px solid rgba(15, 23, 42, 0.08);
}

.clean-data-table td {
  padding: 12px 18px;
  border-bottom: 1px solid rgba(15, 23, 42, 0.06);
  color: var(--text-primary);
  vertical-align: middle;
}

.clean-data-table tr:last-child td {
  border-bottom: none;
}

.clean-data-table tr.clickable-row {
  cursor: pointer;
  transition: background 0.15s ease;
}

.clean-data-table tr.clickable-row:hover {
  background: #f8fafc;
}

.field-key-name {
  font-weight: 600;
  color: var(--text-primary);
  text-transform: capitalize;
}

.field-value-cell {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.copy-icon-hover {
  color: var(--text-muted);
  opacity: 0;
  transition: opacity 0.2s ease;
}

.clickable-row:hover .copy-icon-hover {
  opacity: 1;
}

.copied-pill {
  font-size: 11px;
  background: var(--color-success);
  color: #ffffff;
  padding: 2px 6px;
  border-radius: var(--radius-sm);
  font-weight: 600;
}

.confidence-pill {
  display: inline-block;
  padding: 3px 8px;
  border-radius: 9999px;
  font-size: 11px;
  font-weight: 700;
}

.conf-high {
  background: rgba(16, 185, 129, 0.12);
  color: #059669;
}

.conf-mid {
  background: rgba(245, 158, 11, 0.12);
  color: #d97706;
}

.conf-low {
  background: rgba(239, 68, 68, 0.12);
  color: #dc2626;
}

/* Status Banners */
.status-banner-card {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  padding: 18px 22px;
  border-radius: var(--radius-md);
  margin-bottom: 20px;
}

.status-banner-card.banner-success {
  background: rgba(16, 185, 129, 0.08);
  border: 1px solid rgba(16, 185, 129, 0.25);
  color: #065f46;
}

.status-banner-card.banner-warning {
  background: rgba(245, 158, 11, 0.08);
  border: 1px solid rgba(245, 158, 11, 0.25);
  color: #92400e;
}

.status-banner-card.banner-danger {
  background: rgba(239, 68, 68, 0.08);
  border: 1px solid rgba(239, 68, 68, 0.25);
  color: #991b1b;
}

.status-banner-card strong {
  display: block;
  font-size: 15px;
  margin-bottom: 4px;
}

.status-banner-card p {
  margin: 0;
  font-size: 13px;
  line-height: 1.5;
  opacity: 0.9;
}

/* Anomaly Scores Grid */
.anomaly-scores-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 16px;
  margin-top: 16px;
}

.score-box {
  padding: 18px 22px;
  background: #ffffff;
  border: 1px solid rgba(15, 23, 42, 0.08);
  border-radius: var(--radius-md);
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.score-label {
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--text-tertiary);
}

.score-val {
  font-size: 24px;
  font-weight: 800;
  color: var(--text-primary);
}

.score-sub {
  font-size: 11px;
  color: var(--text-muted);
}

/* Rule Status Tags */
.rule-status-tag {
  display: inline-block;
  padding: 3px 8px;
  border-radius: 9999px;
  font-size: 11px;
  font-weight: 700;
}

.status-pass {
  background: rgba(16, 185, 129, 0.12);
  color: #059669;
}

.status-fail {
  background: rgba(239, 68, 68, 0.12);
  color: #dc2626;
}

.status-warn {
  background: rgba(245, 158, 11, 0.12);
  color: #d97706;
}

.rule-msg-cell {
  color: var(--text-secondary);
  font-size: 13px;
}

/* AI Narrative Card */
.ai-narrative-card {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 14px 18px;
  background: rgba(99, 102, 241, 0.06);
  border: 1px solid rgba(99, 102, 241, 0.18);
  border-radius: var(--radius-md);
  margin-bottom: 20px;
  font-size: 13px;
}

.ai-narrative-card strong {
  display: block;
  color: var(--text-primary);
  margin-bottom: 2px;
}

.ai-narrative-card p {
  margin: 0;
  color: var(--text-secondary);
  line-height: 1.5;
}

/* Clean Empty Box */
.clean-empty-box {
  padding: 40px;
  text-align: center;
  color: var(--text-muted);
  font-size: 13.5px;
}

.table-header-title {
  padding: 12px 18px;
  font-size: 13px;
  font-weight: 700;
  color: var(--text-primary);
  border-bottom: 1px solid rgba(15, 23, 42, 0.08);
  background: #f8fafc;
}

.doc-link {
  color: var(--accent-primary);
  text-decoration: none;
  font-weight: 600;
}

.doc-link:hover {
  text-decoration: underline;
}

.type-badge {
  font-size: 11px;
  padding: 3px 8px;
  border-radius: var(--radius-sm);
  background: var(--bg-tertiary);
  color: var(--text-secondary);
  font-weight: 600;
}
"""

css_path = r"c:\docs\Downloads\My_Projects\Nexora\frontend\src\pages\DocumentDetailPage.css"

with open(css_path, "a", encoding="utf-8") as f:
    f.write(css_code)

print("Appended clean CSS styles successfully")
