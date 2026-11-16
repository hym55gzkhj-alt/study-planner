// REST-Client für das JARVIS-Backend.

async function request(method, url, body) {
  const opts = { method, headers: { Accept: 'application/json' } };
  if (body !== undefined) {
    opts.headers['Content-Type'] = 'application/json';
    opts.body = JSON.stringify(body);
  }
  let res;
  try {
    res = await fetch(url, opts);
  } catch {
    throw new Error('Keine Verbindung zum JARVIS-Server.');
  }
  if (res.status === 204) return null;
  const data = await res.json().catch(() => null);
  if (!res.ok) {
    let msg = `Fehler ${res.status}`;
    if (data?.detail) {
      msg = Array.isArray(data.detail)
        ? data.detail.map((d) => `${(d.loc || []).slice(-1)[0]}: ${d.msg}`).join(' · ')
        : String(data.detail);
    }
    throw new Error(msg);
  }
  return data;
}

export const api = {
  health: () => request('GET', '/api/health'),
  dashboard: () => request('GET', '/api/dashboard'),
  exams: (upcoming = false) => request('GET', `/api/exams${upcoming ? '?upcoming=true' : ''}`),
  createExam: (exam) => request('POST', '/api/exams', exam),
  updateExam: (id, exam) => request('PUT', `/api/exams/${encodeURIComponent(id)}`, exam),
  deleteExam: (id) => request('DELETE', `/api/exams/${encodeURIComponent(id)}`),
  setTaskStatus: (id, status) => request('PATCH', `/api/tasks/${encodeURIComponent(id)}`, { status }),
  settings: () => request('GET', '/api/settings'),
  saveSettings: (s) => request('PUT', '/api/settings', s),
};
