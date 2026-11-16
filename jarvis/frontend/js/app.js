import { api } from './api.js';
import { renderDashboard } from './dashboard.js';
import { renderExams } from './exams.js';
import { renderSettings } from './settings.js';

const VIEWS = {
  dashboard: { title: 'Dashboard', eyebrow: 'Systemübersicht', render: renderDashboard },
  exams: { title: 'Klausuren', eyebrow: 'Termine verwalten', render: renderExams },
  settings: { title: 'Einstellungen', eyebrow: 'Konfiguration', render: renderSettings },
};

function route() {
  const name = (location.hash.replace(/^#\/?/, '') || 'dashboard').split('?')[0];
  const key = name in VIEWS ? name : 'dashboard';
  const view = VIEWS[key];
  for (const k of Object.keys(VIEWS)) document.getElementById(`view-${k}`).hidden = k !== key;
  document.querySelectorAll('.nav a[data-view]').forEach((a) => a.classList.toggle('active', a.dataset.view === key));
  document.getElementById('view-title').textContent = view.title;
  document.getElementById('view-eyebrow').textContent = view.eyebrow;
  document.title = `JARVIS · ${view.title}`;
  view.render(document.getElementById(`view-${key}`));
}

// Uhr oben rechts
const fmtTime = new Intl.DateTimeFormat('de-DE', { hour: '2-digit', minute: '2-digit' });
const fmtDate = new Intl.DateTimeFormat('de-DE', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' });
let lastDay = new Date().toDateString();
function tick() {
  const now = new Date();
  document.getElementById('clock-time').textContent = fmtTime.format(now);
  document.getElementById('clock-date').textContent = fmtDate.format(now);
  // Bei Tageswechsel das Dashboard neu laden (z. B. wenn die App über Nacht offen bleibt)
  if (now.toDateString() !== lastDay) { lastDay = now.toDateString(); if (!document.getElementById('view-dashboard').hidden) route(); }
}

async function heartbeat() {
  const dot = document.getElementById('status-dot');
  const txt = document.getElementById('status-text');
  try { await api.health(); dot.className = 'dot online'; txt.textContent = 'System online'; }
  catch { dot.className = 'dot offline'; txt.textContent = 'Server offline'; }
}

window.addEventListener('hashchange', route);
tick(); setInterval(tick, 1000 * 15);
heartbeat(); setInterval(heartbeat, 30_000);
route();
