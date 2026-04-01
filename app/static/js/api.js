/**
 * api.js - Thin wrapper around fetch() for all backend calls.
 * All functions return Promise<data> or throw on HTTP error.
 */

const API_BASE = '/api';

async function _request(method, path, body = null, params = null) {
  let url = API_BASE + path;
  if (params) {
    const qs = new URLSearchParams(
      Object.entries(params).filter(([, v]) => v !== null && v !== undefined && v !== '')
    ).toString();
    if (qs) url += '?' + qs;
  }
  const opts = {
    method,
    headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
  };
  if (body !== null) opts.body = JSON.stringify(body);

  const res = await fetch(url, opts);
  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try { const j = await res.json(); detail = j.detail || detail; } catch { /* ignore */ }
    throw new Error(detail);
  }
  if (res.status === 204) return null;
  return res.json();
}

// ── Employees ──────────────────────────────────────────────────────────────

const EmployeeAPI = {
  list:     (params = {}) => _request('GET',    '/employees/',      null, params),
  get:      (id)          => _request('GET',    `/employees/${id}`),
  create:   (data)        => _request('POST',   '/employees/',      data),
  update:   (id, data)    => _request('PUT',    `/employees/${id}`, data),
  delete:   (id)          => _request('DELETE', `/employees/${id}`),
  workload: (params)      => _request('GET',    '/employees/workload', null, params),
};

// ── Departments ────────────────────────────────────────────────────────────

const DepartmentAPI = {
  /** Active departments only (used for schedule generation) */
  list:    (params = {}) => _request('GET',   '/departments/',          null, params),
  /** ALL departments including inactive (used for management UI) */
  listAll: (params = {}) => _request('GET',   '/departments/all/list',  null, params),
  get:     (id)          => _request('GET',   `/departments/${id}`),
  create:  (data)        => _request('POST',  '/departments/',          data),
  update:  (id, data)    => _request('PUT',   `/departments/${id}`,     data),
  delete:  (id)          => _request('DELETE',`/departments/${id}`),
  /** Flip is_active on a department, returns the updated record */
  toggle:  (id)          => _request('PATCH', `/departments/${id}/toggle`),
};

// ── Schedules ──────────────────────────────────────────────────────────────

const ScheduleAPI = {
  generate:  (data)   => _request('POST',   '/schedules/generate', data),
  list:      (params) => _request('GET',    '/schedules/',         null, params),
  override:  (data)   => _request('POST',   '/schedules/override', data),
  confirm:   (id)     => _request('PATCH',  `/schedules/${id}/confirm`),
  delete:    (id)     => _request('DELETE', `/schedules/${id}`),
  feedback:  (data)   => _request('POST',   '/schedules/feedback', data),
  exportCsvUrl:   (params) => `${API_BASE}/schedules/export/csv?${new URLSearchParams(params).toString()}`,
  exportExcelUrl: (params) => `${API_BASE}/schedules/export/excel?${new URLSearchParams(params).toString()}`,
};

// ── Shifts ─────────────────────────────────────────────────────────────────

const ShiftAPI = {
  list: (params = {}) => _request('GET', '/shifts/', null, params),
};

// ── Simulation ─────────────────────────────────────────────────────────────

const SimulationAPI = {
  run: (data) => _request('POST', '/simulate/', data),
};

// ── Auth ───────────────────────────────────────────────────────────────────

const AuthAPI = {
  me: () => _request('GET', '/auth/me'),
};
