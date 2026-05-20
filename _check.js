
// ─── State ───────────────────────────────────
let allCandidates = [];
let currentPage = 1;
const PER_PAGE = 15;
let sortField = 'submitted_at';
let sortDir = 'desc';
let statsCache = null;
let chartsInit = { dashboard: false, analytics: false };
let chartInstances = {};

// ─── Auth ─────────────────────────────────────
async function doLogin() {
  const u = document.getElementById('login-username').value.trim();
  const p = document.getElementById('login-password').value;
  const btn = document.getElementById('login-btn');
  const err = document.getElementById('login-error');

  btn.textContent = 'Signing in...';
  btn.disabled = true;
  err.classList.remove('show');

  try {
    const res = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: u, password: p })
    });
    const data = await res.json();
    if (data.success) {
      document.getElementById('login-screen').style.display = 'none';
      document.getElementById('app-shell').classList.add('visible');
      document.getElementById('admin-name-display').textContent = data.username;
      document.getElementById('admin-avatar').textContent = data.username[0].toUpperCase();
      loadDashboard();
    } else {
      err.classList.add('show');
    }
  } catch(e) {
    err.textContent = 'Connection error. Is the server running?';
    err.classList.add('show');
  }
  btn.textContent = 'Sign In →';
  btn.disabled = false;
}

async function doLogout() {
  await fetch('/api/auth/logout', { method: 'POST' });
  document.getElementById('app-shell').classList.remove('visible');
  document.getElementById('login-screen').style.display = 'flex';
  document.getElementById('login-password').value = '';
}

// Auto-check auth
(async () => {
  const res = await fetch('/api/auth/check');
  const d = await res.json();
  if (d.authenticated) {
    document.getElementById('login-screen').style.display = 'none';
    document.getElementById('app-shell').classList.add('visible');
    loadDashboard();
  }
})();

// Enter key on login
document.getElementById('login-password').addEventListener('keydown', e => {
  if (e.key === 'Enter') doLogin();
});

// ─── Navigation ───────────────────────────────
const pageConfig = {
  dashboard: { title: 'Dashboard', sub: 'Overview of recruitment activity' },
  candidates: { title: 'All Candidates', sub: 'Manage and update candidate records' },
  analytics:  { title: 'Analytics', sub: 'Detailed data insights and charts' }
};

function showPage(name) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.sb-nav a').forEach(a => a.classList.remove('active'));
  document.getElementById('page-' + name).classList.add('active');
  document.getElementById('nav-' + name)?.classList.add('active');
  document.getElementById('page-title').textContent = pageConfig[name].title;
  document.getElementById('page-sub').textContent = pageConfig[name].sub;

  if (name === 'candidates') loadCandidates();
  if (name === 'analytics') loadAnalytics();
  if (name === 'dashboard') loadDashboard();
}

// ─── Dashboard ────────────────────────────────
async function loadDashboard() {
  try {
    const res = await fetch('/api/admin/stats');
    const s = await res.json();
    statsCache = s;
    renderStats(s);
    renderRecentTable(s.recent);
    if (!chartsInit.dashboard) {
      renderDashboardCharts(s);
      chartsInit.dashboard = true;
    } else {
      updateDashboardCharts(s);
    }
  } catch(e) {
    showToast('Failed to load dashboard data', 'error');
  }
}

function renderStats(s) {
  const grid = document.getElementById('stats-grid');
  grid.innerHTML = `
    <div class="stat-card blue">
      <div class="stat-top">
        <div><div class="stat-label">Total Submissions</div><div class="stat-value">${s.total}</div></div>
        <div class="stat-icon ic-blue"><svg width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/></svg></div>
      </div>
      <div class="stat-sub">${s.todayCount} submitted today</div>
    </div>
    <div class="stat-card green">
      <div class="stat-top">
        <div><div class="stat-label">Eligible Candidates</div><div class="stat-value">${s.eligible}</div></div>
        <div class="stat-icon ic-green"><svg width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M20 6L9 17l-5-5"/></svg></div>
      </div>
      <div class="stat-sub">${s.ineligible} ineligible out of ${s.total}</div>
    </div>
    <div class="stat-card amber">
      <div class="stat-top">
        <div><div class="stat-label">Selected</div><div class="stat-value">${s.selected}</div></div>
        <div class="stat-icon ic-amber"><svg width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg></div>
      </div>
      <div class="stat-sub">${s.pending} still pending decision</div>
    </div>
    <div class="stat-card purple">
      <div class="stat-top">
        <div><div class="stat-label">Medical Fit</div><div class="stat-value">${s.medFit}</div></div>
        <div class="stat-icon ic-purple"><svg width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg></div>
      </div>
      <div class="stat-sub">${s.medUnfit} medically unfit</div>
    </div>
  `;
}

function renderRecentTable(recent) {
  const tbody = document.getElementById('recent-tbody');
  if (!recent?.length) {
    tbody.innerHTML = '<tr><td colspan="6" class="empty-state">No submissions yet</td></tr>';
    return;
  }
  tbody.innerHTML = recent.map((r, i) => `
    <tr>
      <td style="color:var(--text-3);font-size:0.75rem">${i+1}</td>
      <td><div class="td-name">${r.name}</div><div class="td-sub">#${r.id}</div></td>
      <td style="font-size:0.82rem">${r.mobile}</td>
      <td><span class="badge badge-${r.criteria_met === 'YES' ? 'yes' : 'no'}">${r.criteria_met}</span></td>
      <td><span class="badge badge-${r.interview_status.toLowerCase()}">${r.interview_status}</span></td>
      <td style="font-size:0.75rem;color:var(--text-3)">${r.submitted_at?.split('T')[0] || r.submitted_at?.split(' ')[0] || '—'}</td>
    </tr>
  `).join('');
}

// ─── Dashboard Charts ─────────────────────────
const PALETTE = ['#1a4fad','#0d7c4a','#e8a020','#7c3aed','#c0392b','#16a085','#2980b9','#8e44ad'];

function destroyChart(id) {
  if (chartInstances[id]) { chartInstances[id].destroy(); delete chartInstances[id]; }
}

function renderDashboardCharts(s) {
  // Status doughnut
  destroyChart('status');
  chartInstances['status'] = new Chart(document.getElementById('chart-status'), {
    type: 'doughnut',
    data: {
      labels: ['Pending', 'Selected', 'Rejected'],
      datasets: [{ data: [s.pending, s.selected, s.rejected], backgroundColor: ['#fbbf24','#0d7c4a','#c0392b'], borderWidth: 2, borderColor: '#fff' }]
    },
    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'bottom', labels: { font: { family: 'DM Sans', size: 11 }, padding: 12 } } } }
  });

  // Track bar
  destroyChart('track');
  chartInstances['track'] = new Chart(document.getElementById('chart-track'), {
    type: 'bar',
    data: {
      labels: s.byTrack.map(t => t.education_track),
      datasets: [{ data: s.byTrack.map(t => t.cnt), backgroundColor: PALETTE, borderRadius: 6 }]
    },
    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true, ticks: { stepSize: 1 } }, x: { grid: { display: false } } } }
  });

  // District bar
  destroyChart('district');
  chartInstances['district'] = new Chart(document.getElementById('chart-district'), {
    type: 'bar',
    data: {
      labels: s.byDistrict.map(d => d.district),
      datasets: [{ data: s.byDistrict.map(d => d.cnt), backgroundColor: '#1a4fad', borderRadius: 5 }]
    },
    options: { responsive: true, maintainAspectRatio: false, indexAxis: 'y', plugins: { legend: { display: false } }, scales: { x: { beginAtZero: true, ticks: { stepSize: 1 } }, y: { grid: { display: false }, ticks: { font: { size: 11 } } } } }
  });

  // Category doughnut
  destroyChart('category');
  chartInstances['category'] = new Chart(document.getElementById('chart-category'), {
    type: 'doughnut',
    data: {
      labels: s.byCategory.map(c => c.category),
      datasets: [{ data: s.byCategory.map(c => c.cnt), backgroundColor: PALETTE, borderWidth: 2, borderColor: '#fff' }]
    },
    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'bottom', labels: { font: { family: 'DM Sans', size: 11 }, padding: 10 } } } }
  });
}

function updateDashboardCharts(s) { renderDashboardCharts(s); }

// ─── Analytics Charts ─────────────────────────
async function loadAnalytics() {
  if (!statsCache) {
    const res = await fetch('/api/admin/stats');
    statsCache = await res.json();
  }
  const s = statsCache;

  // Gender
  destroyChart('gender');
  chartInstances['gender'] = new Chart(document.getElementById('chart-gender'), {
    type: 'pie',
    data: {
      labels: ['Male', 'Female'],
      datasets: [{ data: [s.male, s.female], backgroundColor: ['#1a4fad', '#e8a020'], borderWidth: 2, borderColor: '#fff' }]
    },
    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'bottom', labels: { font: { family: 'DM Sans', size: 11 }, padding: 12 } } } }
  });

  // Medical
  destroyChart('medical');
  const medPending = (statsCache.total || 0) - s.medFit - s.medUnfit;
  chartInstances['medical'] = new Chart(document.getElementById('chart-medical'), {
    type: 'doughnut',
    data: {
      labels: ['Fit', 'Unfit', 'Pending'],
      datasets: [{ data: [s.medFit, s.medUnfit, medPending], backgroundColor: ['#0d7c4a','#c0392b','#fbbf24'], borderWidth: 2, borderColor: '#fff' }]
    },
    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'bottom', labels: { font: { family: 'DM Sans', size: 11 }, padding: 12 } } } }
  });

  // Eligible
  destroyChart('eligible');
  chartInstances['eligible'] = new Chart(document.getElementById('chart-eligible'), {
    type: 'pie',
    data: {
      labels: ['Eligible', 'Ineligible'],
      datasets: [{ data: [s.eligible, s.ineligible], backgroundColor: ['#0d7c4a','#c0392b'], borderWidth: 2, borderColor: '#fff' }]
    },
    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'bottom', labels: { font: { family: 'DM Sans', size: 11 }, padding: 12 } } } }
  });

  // Timeline
  destroyChart('timeline');
  chartInstances['timeline'] = new Chart(document.getElementById('chart-timeline'), {
    type: 'line',
    data: {
      labels: s.byDate.map(d => d.interview_date),
      datasets: [{ label: 'Candidates', data: s.byDate.map(d => d.cnt), borderColor: '#1a4fad', backgroundColor: 'rgba(26,79,173,0.08)', fill: true, tension: 0.4, pointBackgroundColor: '#1a4fad', pointRadius: 4 }]
    },
    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true, ticks: { stepSize: 1 } }, x: { grid: { display: false }, ticks: { font: { size: 10 } } } } }
  });

  // Trades
  destroyChart('trade');
  chartInstances['trade'] = new Chart(document.getElementById('chart-trade'), {
    type: 'bar',
    data: {
      labels: s.byTrade.map(t => t.iti_trade),
      datasets: [{ data: s.byTrade.map(t => t.cnt), backgroundColor: PALETTE, borderRadius: 5 }]
    },
    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true, ticks: { stepSize: 1 } }, x: { grid: { display: false }, ticks: { font: { size: 10 }, maxRotation: 30 } } } }
  });
}

// ─── Candidates Table ─────────────────────────
let debounceTimer;
function debouncedLoad() {
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(() => { currentPage = 1; loadCandidates(); }, 350);
}

async function loadCandidates() {
  const search = document.getElementById('search-input').value;
  const date = document.getElementById('filter-date').value;
  const status = document.getElementById('filter-status').value;
  const criteria = document.getElementById('filter-criteria').value;

  const params = new URLSearchParams({ search, date, status, criteria, sort: sortField, dir: sortDir });

  try {
    const res = await fetch('/api/admin/candidates?' + params);
    if (res.status === 401) { doLogout(); return; }
    allCandidates = await res.json();
    renderCandidatesTable();
  } catch(e) {
    showToast('Failed to load candidates', 'error');
  }
}

function renderCandidatesTable() {
  const tbody = document.getElementById('cand-tbody');
  const start = (currentPage - 1) * PER_PAGE;
  const slice = allCandidates.slice(start, start + PER_PAGE);

  if (!allCandidates.length) {
    tbody.innerHTML = `<tr><td colspan="9"><div class="empty-state">
      <svg width="40" height="40" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24"><circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/></svg>
      <div>No candidates found</div>
    </div></td></tr>`;
    document.getElementById('page-info').textContent = 'No records';
    document.getElementById('page-btns').innerHTML = '';
    return;
  }

  tbody.innerHTML = slice.map(c => `
    <tr>
      <td>
        <div class="td-name">${c.name}</div>
        <div class="td-sub">Father: ${c.father_name}</div>
        <div class="td-sub">📱 ${c.mobile} | PAN: ${c.pan}</div>
        <div class="td-sub" style="color:#7c3aed;font-size:0.7rem">Aadhaar: [Redacted]</div>
      </td>
      <td>
        <div style="font-size:0.82rem;font-weight:600">${c.age} yrs</div>
        <div class="td-sub">${c.dob}</div>
      </td>
      <td>
        <div class="td-sub">${c.gender} • ${c.marital_status}</div>
        <div class="td-sub">${c.candidate_type}</div>
        <div class="td-sub">${c.location}, ${c.district}</div>
      </td>
      <td>
        <div style="font-size:0.82rem;font-weight:600">${c.education_track}</div>
        ${c.iti_trade && c.iti_trade !== 'N/A' ? `<div class="td-sub">ITI: ${c.iti_trade}</div>` : ''}
        ${c.puc_branch && c.puc_branch !== 'N/A' ? `<div class="td-sub">PUC: ${c.puc_branch}</div>` : ''}
        ${c.degree && c.degree !== 'None' ? `<div class="td-sub">${c.degree}</div>` : ''}
      </td>
      <td>
        <div class="td-sub">SSLC: <b>${c.sslc_per}%</b></div>
        ${c.puc_per > 0 ? `<div class="td-sub">PUC: <b>${c.puc_per}%</b></div>` : ''}
        ${c.iti_per > 0 ? `<div class="td-sub">ITI: <b>${c.iti_per}%</b></div>` : ''}
        ${c.grad_per > 0 ? `<div class="td-sub">Grad: <b>${c.grad_per}%</b></div>` : ''}
      </td>
      <td><span class="badge badge-${c.criteria_met === 'YES' ? 'yes' : 'no'}">${c.criteria_met}</span></td>
      <td style="font-size:0.82rem;white-space:nowrap">${c.interview_date}</td>
      <td>
        <div style="margin-bottom:6px">
          <div class="td-sub" style="font-size:0.68rem;font-weight:700;letter-spacing:0.05em;text-transform:uppercase;margin-bottom:3px">Interview</div>
          <select class="mini-select" onchange="updateStatus(${c.id}, 'interview_status', this.value)">
            <option ${c.interview_status === 'Pending' ? 'selected' : ''}>Pending</option>
            <option ${c.interview_status === 'Selected' ? 'selected' : ''}>Selected</option>
            <option ${c.interview_status === 'Rejected' ? 'selected' : ''}>Rejected</option>
          </select>
        </div>
        <div>
          <div class="td-sub" style="font-size:0.68rem;font-weight:700;letter-spacing:0.05em;text-transform:uppercase;margin-bottom:3px">Medical</div>
          <select class="mini-select" onchange="updateStatus(${c.id}, 'medical_status', this.value)">
            <option ${c.medical_status === 'Pending' ? 'selected' : ''}>Pending</option>
            <option ${c.medical_status === 'Medical Fit' ? 'selected' : ''}>Medical Fit</option>
            <option ${c.medical_status === 'Medical Unfit' ? 'selected' : ''}>Medical Unfit</option>
          </select>
        </div>
      </td>
      <td>
        <button class="btn-del" onclick="deleteCandidate(${c.id}, '${c.name.replace(/'/g, "\\'")}')">
          <svg width="12" height="12" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14H6L5 6M10 11v6M14 11v6M9 6V4h6v2"/></svg>
        </button>
      </td>
    </tr>
  `).join('');

  // Pagination
  const total = allCandidates.length;
  const pages = Math.ceil(total / PER_PAGE);
  document.getElementById('page-info').textContent = `Showing ${start+1}–${Math.min(start+PER_PAGE, total)} of ${total} records`;

  const btns = document.getElementById('page-btns');
  btns.innerHTML = '';
  for (let i = 1; i <= pages; i++) {
    const btn = document.createElement('button');
    btn.className = 'page-btn' + (i === currentPage ? ' active' : '');
    btn.textContent = i;
    btn.onclick = () => { currentPage = i; renderCandidatesTable(); };
    btns.appendChild(btn);
  }
}

function setSort(field) {
  if (sortField === field) sortDir = sortDir === 'asc' ? 'desc' : 'asc';
  else { sortField = field; sortDir = 'asc'; }
  document.querySelectorAll('thead th').forEach(th => th.classList.remove('sorted'));
  const thMap = { name: 'th-name', dob: 'th-dob', education_track: 'th-edu', sslc_per: 'th-sslc', criteria_met: 'th-criteria', interview_date: 'th-date' };
  if (thMap[field]) document.getElementById(thMap[field])?.classList.add('sorted');
  loadCandidates();
}

async function updateStatus(id, field, value) {
  try {
    const res = await fetch(`/api/admin/candidates/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ [field]: value })
    });
    if (!res.ok) throw new Error();
    showToast('Status updated', 'success');
    statsCache = null;
  } catch(e) {
    showToast('Update failed', 'error');
  }
}

async function deleteCandidate(id, name) {
  if (!confirm(`Delete application for "${name}"? This cannot be undone.`)) return;
  try {
    const res = await fetch(`/api/admin/candidates/${id}`, { method: 'DELETE' });
    if (!res.ok) throw new Error();
    showToast('Record deleted', 'success');
    statsCache = null;
    loadCandidates();
  } catch(e) {
    showToast('Delete failed', 'error');
  }
}

// ─── Export ───────────────────────────────────
function exportCSV() {
  const date = document.getElementById('filter-date')?.value || '';
  const url = '/api/admin/export' + (date ? '?date=' + date : '');
  window.location.href = url;
}

// ─── Toast ────────────────────────────────────
function showToast(msg, type = '') {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.className = 'toast ' + type + ' show';
  setTimeout(() => t.classList.remove('show'), 2800);
}
