/**
 * app.js - Global application state, domain toggle, and shared utilities.
 */

// ── Domain State ────────────────────────────────────────────────────────────

const SUGGESTIONS = {
  medical: '🏥 Medical Mode: Doctors will be rotated across departments for balanced clinical exposure. ICU and Emergency shifts are prioritised.',
  it:      '💻 IT Mode: Employees are assigned based on skill match and workload balance. On-call rotation is distributed fairly.',
};

function getActiveDomain() {
  return localStorage.getItem('rosterDomain') || 'medical';
}

function setDomain(domain) {
  localStorage.setItem('rosterDomain', domain);
  _applyDomain(domain);
  // Notify any page-level handlers
  window.dispatchEvent(new CustomEvent('domainChanged', { detail: { domain } }));
}

function _applyDomain(domain) {
  document.body.classList.remove('domain-medical', 'domain-it');
  document.body.classList.add(`domain-${domain}`);

  const btnMed = document.getElementById('btnMedical');
  const btnIT  = document.getElementById('btnIT');
  if (btnMed) btnMed.classList.toggle('active', domain === 'medical');
  if (btnIT)  btnIT.classList.toggle('active', domain === 'it');

  const banner = document.getElementById('smartSuggestionBanner');
  const text   = document.getElementById('suggestionText');
  if (banner && text) {
    text.textContent = SUGGESTIONS[domain] || '';
    banner.style.display = 'flex';
  }
}

// Initialise on load
document.addEventListener('DOMContentLoaded', () => {
  _applyDomain(getActiveDomain());
});

// ── Loading Overlay ─────────────────────────────────────────────────────────

let _loadingEl = null;

function showLoading(msg = 'Generating schedule with AI engine…') {
  if (_loadingEl) return;
  _loadingEl = document.createElement('div');
  _loadingEl.className = 'loading-overlay';
  _loadingEl.innerHTML = `
    <div class="spinner-border text-light" role="status"></div>
    <div class="loading-text">${msg}</div>
  `;
  document.body.appendChild(_loadingEl);
}

function hideLoading() {
  if (_loadingEl) { _loadingEl.remove(); _loadingEl = null; }
}

// ── Toast Notifications ──────────────────────────────────────────────────────

function showToast(message, type = 'success') {
  const container = document.getElementById('toastContainer');
  if (!container) return;
  const icons = { success: 'check-circle-fill', danger: 'x-circle-fill', warning: 'exclamation-triangle-fill', info: 'info-circle-fill' };
  const id = 'toast_' + Date.now();
  const el = document.createElement('div');
  el.id = id;
  el.className = `toast align-items-center text-white bg-${type} border-0`;
  el.setAttribute('role', 'alert');
  el.innerHTML = `
    <div class="d-flex">
      <div class="toast-body d-flex align-items-center gap-2">
        <i class="bi bi-${icons[type] || 'info-circle-fill'}"></i>
        ${message}
      </div>
      <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
    </div>
  `;
  container.appendChild(el);
  const t = new bootstrap.Toast(el, { delay: 4000 });
  t.show();
  el.addEventListener('hidden.bs.toast', () => el.remove());
}

// ── Formatters ───────────────────────────────────────────────────────────────

function shiftBadge(shiftKey, shiftName) {
  return `<span class="shift-badge shift-${shiftKey}">${shiftName || shiftKey}</span>`;
}

function scoreBar(score) {
  const pct = Math.round((score || 0) * 100);
  const color = pct > 70 ? '#10b981' : pct > 40 ? '#f59e0b' : '#ef4444';
  return `
    <div class="score-bar-wrap d-flex align-items-center gap-1">
      <div class="score-bar-bg flex-grow-1">
        <div class="score-bar-fill" style="width:${pct}%;background:${color}"></div>
      </div>
      <small class="text-muted" style="width:32px;text-align:right">${pct}%</small>
    </div>`;
}

function domainPill(rosterType) {
  return `<span class="domain-pill-${rosterType}">${rosterType === 'medical' ? '🏥 Medical' : '💻 IT'}</span>`;
}

function formatDate(isoStr) {
  if (!isoStr) return '';
  const d = new Date(isoStr + 'T00:00:00');
  return d.toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' });
}

// ── Confirm Dialog ───────────────────────────────────────────────────────────

function confirmDialog(message) {
  return new Promise(resolve => {
    if (confirm(message)) resolve(true); else resolve(false);
  });
}

// ── Date Helpers ─────────────────────────────────────────────────────────────

function todayISO() {
  return new Date().toISOString().split('T')[0];
}

function addDays(isoDate, n) {
  const d = new Date(isoDate + 'T00:00:00');
  d.setDate(d.getDate() + n);
  return d.toISOString().split('T')[0];
}

function weekStart(isoDate) {
  const d = new Date(isoDate + 'T00:00:00');
  const day = d.getDay();
  const diff = (day === 0 ? -6 : 1 - day);
  d.setDate(d.getDate() + diff);
  return d.toISOString().split('T')[0];
}
