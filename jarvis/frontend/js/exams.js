import { api } from './api.js';
import { h, toast, dateShort, daysLabel, stars } from './ui.js';

let root;
let editing = null; // Klausur, die gerade bearbeitet wird

export async function renderExams(container) {
  root = container;
  let exams = [];
  try {
    exams = await api.exams();
  } catch (err) {
    toast(err.message, 'error');
  }
  root.replaceChildren(h('div', { class: 'grid' },
    h('div', { class: 'panel span-4' }, ...formPanel()),
    h('div', { class: 'panel span-8' }, ...listPanel(exams)),
  ));
}

function field(label, input, cls = '', hint = '') {
  const id = `f-${input.name}`;
  input.id = id;
  return h('div', { class: `field ${cls}` }, h('label', { for: id }, label), input, hint ? h('small', {}, hint) : null);
}

function formPanel() {
  const e = editing || {};
  const subject = h('input', { name: 'subject', required: true, maxlength: 80, placeholder: 'z. B. Mathematik', value: e.subject || '', autocomplete: 'off' });
  const date = h('input', { name: 'date', type: 'date', required: true, value: e.date || '' });
  const time = h('input', { name: 'time', type: 'time', value: e.time || '' });
  const diffOut = h('output', {}, String(e.difficulty || 3));
  const difficulty = h('input', { name: 'difficulty', type: 'range', min: 1, max: 5, step: 1, value: e.difficulty || 3, oninput: () => { diffOut.value = difficulty.value; } });
  const notes = h('textarea', { name: 'notes', maxlength: 1000, placeholder: 'Themen, Raum, Hilfsmittel …' });
  notes.value = e.notes || '';

  const form = h('form', { class: 'form', novalidate: false, onsubmit: async (ev) => {
    ev.preventDefault();
    const body = {
      subject: subject.value.trim(),
      date: date.value,
      time: time.value || null,
      difficulty: Number(difficulty.value),
      notes: notes.value.trim(),
    };
    try {
      if (editing) { await api.updateExam(editing.id, body); toast('Klausur aktualisiert.'); }
      else { await api.createExam(body); toast('Klausur gespeichert.'); }
      editing = null;
      renderExams(root);
    } catch (err) { toast(err.message, 'error'); }
  } },
    field('Fach', subject, 'full'),
    field('Datum', date),
    field('Uhrzeit', time, '', 'optional – leer lassen, wenn unbekannt'),
    h('div', { class: 'field full' }, h('label', { for: 'f-difficulty' }, 'Schwierigkeit / Lernbedarf: ', diffOut), difficulty, h('small', {}, '1 = leicht · 5 = braucht viel Lernzeit')),
    field('Notizen', notes, 'full'),
    h('div', { class: 'form-actions' },
      editing ? h('button', { type: 'button', class: 'btn ghost', onclick: () => { editing = null; renderExams(root); } }, 'Abbrechen') : null,
      h('button', { type: 'submit', class: 'btn primary' }, editing ? 'Speichern' : '+ Hinzufügen')),
  );
  difficulty.id = 'f-difficulty';

  return [h('div', { class: 'panel-head' }, h('h2', {}, editing ? 'Klausur bearbeiten' : 'Neue Klausur')), form];
}

function listPanel(exams) {
  const head = h('div', { class: 'panel-head' }, h('h2', {}, 'Alle Klausuren'), h('span', { class: 'meta' }, `${exams.length} gespeichert`));
  if (!exams.length) return [head, h('div', { class: 'empty' }, 'Noch keine Klausuren gespeichert.')];
  const rows = exams.map((e) => h('tr', { class: e.days_left < 0 ? 'past' : '' },
    h('td', {}, h('b', {}, e.subject), e.notes ? h('div', { class: 'task-sub' }, e.notes) : null),
    h('td', {}, dateShort(e.date)),
    h('td', {}, e.time ? `${e.time}` : '—'),
    h('td', {}, stars(e.difficulty)),
    h('td', {}, h('span', { class: `badge ${e.days_left < 0 ? 'muted' : e.days_left <= 3 ? 'soon' : ''}` }, daysLabel(e.days_left))),
    h('td', { class: 'actions' },
      h('button', { class: 'btn sm ghost', title: 'Bearbeiten', 'aria-label': `${e.subject} bearbeiten`, onclick: () => { editing = e; renderExams(root); window.scrollTo({ top: 0, behavior: 'smooth' }); } }, '✎'),
      h('button', { class: 'btn sm danger', title: 'Löschen', 'aria-label': `${e.subject} löschen`, onclick: async () => {
        if (!confirm(`„${e.subject}“ am ${dateShort(e.date)} wirklich löschen?`)) return;
        try { await api.deleteExam(e.id); toast('Klausur gelöscht.'); renderExams(root); } catch (err) { toast(err.message, 'error'); }
      } }, '✕')),
  ));
  return [head, h('div', { class: 'table-wrap' }, h('table', { class: 'data' },
    h('thead', {}, h('tr', {}, ['Fach', 'Datum', 'Zeit', 'Lernbedarf', 'Countdown', ''].map((t) => h('th', {}, t)))),
    h('tbody', {}, rows)))];
}
