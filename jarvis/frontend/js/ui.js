// Kleine UI-Helfer. Benutzerdaten werden IMMER als Text eingefügt (nie als HTML) – Schutz vor XSS.

/** Element erzeugen: h('div', {class: 'x', onclick: fn}, 'Text', kind, …) */
export function h(tag, attrs = {}, ...children) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (v === false || v == null) continue;
    if (k === 'class') el.className = v;
    else if (k === 'dataset') Object.assign(el.dataset, v);
    else if (k.startsWith('on') && typeof v === 'function') el.addEventListener(k.slice(2), v);
    else if (k === 'style' && typeof v === 'object') for (const [p, val] of Object.entries(v)) el.style.setProperty(p, val);
    else if (v === true) el.setAttribute(k, '');
    else el.setAttribute(k, String(v));
  }
  for (const c of children.flat(Infinity)) {
    if (c == null || c === false) continue;
    el.append(c instanceof Node ? c : document.createTextNode(String(c)));
  }
  return el;
}

const SVG_NS = 'http://www.w3.org/2000/svg';
export function svg(tag, attrs = {}, ...children) {
  const el = document.createElementNS(SVG_NS, tag);
  for (const [k, v] of Object.entries(attrs)) el.setAttribute(k, String(v));
  for (const c of children) el.append(c);
  return el;
}

/** Statisches, vertrauenswürdiges SVG-Icon (nur Pfade aus dem Code, keine Benutzerdaten). */
export function icon(paths, cls = '') {
  return svg('svg', { viewBox: '0 0 24 24', class: cls }, ...paths.map((d) => svg('path', { d })));
}

export function toast(message, type = 'info') {
  const box = document.getElementById('toasts');
  const t = h('div', { class: `toast ${type}` }, message);
  box.append(t);
  setTimeout(() => t.remove(), 3800);
}

// ---------- Formatierung (Deutsch) ----------
const fmtLong = new Intl.DateTimeFormat('de-DE', { weekday: 'long', day: 'numeric', month: 'long' });
const fmtShort = new Intl.DateTimeFormat('de-DE', { weekday: 'short', day: '2-digit', month: '2-digit' });
const fmtDay = new Intl.DateTimeFormat('de-DE', { weekday: 'short' });

export const parseISO = (s) => { const [y, m, d] = s.split('-').map(Number); return new Date(y, m - 1, d); };
export const dateLong = (iso) => fmtLong.format(parseISO(iso));
export const dateShort = (iso) => fmtShort.format(parseISO(iso));
export const weekday = (iso) => fmtDay.format(parseISO(iso)).replace('.', '');

export function daysLabel(n) {
  if (n === 0) return 'Heute';
  if (n === 1) return 'Morgen';
  if (n < 0) return `vor ${-n} T.`;
  return `in ${n} Tagen`;
}

export function minutes(m) {
  if (m < 60) return `${m} min`;
  const hh = Math.floor(m / 60), mm = m % 60;
  return mm ? `${hh} h ${mm} min` : `${hh} h`;
}

/** Animierter Fortschrittsring. value/max → Füllstand. */
export function ring({ value, max, center, caption, size = '', urgent = false }) {
  const r = 52, c = 2 * Math.PI * r;
  const pct = max > 0 ? Math.max(0, Math.min(1, value / max)) : 0;
  const bar = svg('circle', { class: 'bar', cx: 60, cy: 60, r, 'stroke-dasharray': c, 'stroke-dashoffset': c });
  const el = h('div', { class: `ring ${size} ${urgent ? 'urgent' : ''}`, role: 'img', 'aria-label': `${center} ${caption}` },
    svg('svg', { viewBox: '0 0 120 120' },
      svg('circle', { class: 'ticks', cx: 60, cy: 60, r: 59 }),
      svg('circle', { class: 'track', cx: 60, cy: 60, r }),
      bar,
      svg('circle', { class: 'spinner', cx: 60, cy: 60, r: 44 }),
    ),
    h('div', { class: 'ring-center' }, h('b', {}, center), h('small', {}, caption)),
  );
  requestAnimationFrame(() => requestAnimationFrame(() => bar.setAttribute('stroke-dashoffset', c * (1 - pct))));
  return el;
}

/** Text Buchstabe für Buchstabe einblenden (JARVIS-Effekt). */
export function typeText(el, text, speed = 18) {
  el.textContent = '';
  el.classList.add('typed');
  if (matchMedia('(prefers-reduced-motion: reduce)').matches) { el.textContent = text; el.classList.remove('typed'); return; }
  let i = 0;
  const tick = () => {
    el.textContent = text.slice(0, ++i);
    if (i < text.length) setTimeout(tick, speed);
    else setTimeout(() => el.classList.remove('typed'), 1200);
  };
  tick();
}

export function stars(n) {
  return h('span', { class: 'stars', 'aria-label': `Schwierigkeit ${n} von 5` },
    '★'.repeat(n), h('span', { class: 'off' }, '★'.repeat(5 - n)));
}
