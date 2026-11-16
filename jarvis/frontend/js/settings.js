import { api } from './api.js';
import { h, toast } from './ui.js';

export async function renderSettings(container) {
  let s;
  try { s = await api.settings(); } catch (err) { toast(err.message, 'error'); return; }

  const inp = (name, attrs) => h('input', { name, id: `s-${name}`, value: s[name] ?? '', ...attrs });
  const f = (label, input, hint, cls = '') => h('div', { class: `field ${cls}` }, h('label', { for: input.id }, label), input, hint ? h('small', {}, hint) : null);

  const fields = {
    user_name: inp('user_name', { maxlength: 40, placeholder: 'Wie soll JARVIS dich nennen?' }),
    class_name: inp('class_name', { maxlength: 20 }),
    daily_minutes: inp('daily_minutes', { type: 'number', min: 0, max: 720, step: 15 }),
    session_minutes: inp('session_minutes', { type: 'number', min: 15, max: 180, step: 5 }),
    break_minutes: inp('break_minutes', { type: 'number', min: 0, max: 60, step: 5 }),
    study_start: inp('study_start', { type: 'time' }),
    briefing_time: inp('briefing_time', { type: 'time' }),
  };

  const form = h('form', { class: 'form', onsubmit: async (ev) => {
    ev.preventDefault();
    const body = {};
    for (const [k, el] of Object.entries(fields)) body[k] = el.type === 'number' ? Number(el.value) : el.value;
    try { await api.saveSettings(body); toast('Einstellungen gespeichert.'); } catch (err) { toast(err.message, 'error'); }
  } },
    f('Dein Name', fields.user_name, '', 'third'),
    f('Klasse', fields.class_name, '', 'third'),
    f('Lernzeit pro Tag (Minuten)', fields.daily_minutes, 'Wie viel Zeit hast du realistisch täglich?', 'third'),
    f('Länge eines Lernblocks (Min.)', fields.session_minutes, '', 'third'),
    f('Pause zwischen Blöcken (Min.)', fields.break_minutes, '', 'third'),
    f('Lernbeginn', fields.study_start, 'Frühester Start nach der Schule', 'third'),
    f('Tagesbericht um', fields.briefing_time, 'Die tägliche Begrüßung (Standard 07:00)', 'third'),
    h('div', { class: 'form-actions' }, h('button', { type: 'submit', class: 'btn primary' }, 'Speichern')),
  );

  container.replaceChildren(h('div', { class: 'grid' },
    h('div', { class: 'panel span-8' }, h('div', { class: 'panel-head' }, h('h2', {}, 'Profil & Lernzeit')), form),
    h('div', { class: 'panel span-4' }, h('div', { class: 'panel-head' }, h('h2', {}, 'Systemstatus')),
      h('ul', { class: 'tasks' },
        h('li', { class: 'task' }, h('span', {}, '🗄'), h('div', {}, h('div', { class: 'task-title' }, 'Datenbank'), h('div', { class: 'task-sub' }, 'SQLite · lokal gespeichert')), h('span', { class: 'badge' }, 'OK')),
        h('li', { class: 'task' }, h('span', {}, '🧠'), h('div', {}, h('div', { class: 'task-title' }, 'KI-Schlüssel'), h('div', { class: 'task-sub' }, 'über ANTHROPIC_API_KEY')), h('span', { class: `badge ${s.ai_enabled ? '' : 'muted'}` }, s.ai_enabled ? 'aktiv' : 'nicht gesetzt')),
      ))));
}
