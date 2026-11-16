import { api } from './api.js';
import { h, icon, ring, toast, typeText, dateLong, dateShort, weekday, daysLabel, minutes } from './ui.js';

const ICON_CAL = ['M8 2v4M16 2v4M3 10h18M5 4h14a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2z'];
const ICON_TASK = ['M9 11l3 3L22 4', 'M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11'];
const ICON_CHART = ['M3 3v18h18', 'M7 15l4-4 3 3 5-6'];

let root;

export async function renderDashboard(container) {
  root = container;
  if (!root.childElementCount) root.append(skeleton());
  try {
    const data = await api.dashboard();
    root.replaceChildren(build(data));
  } catch (err) {
    root.replaceChildren(h('div', { class: 'panel' }, h('div', { class: 'empty' }, `⚠ ${err.message}`)));
  }
}

function skeleton() {
  return h('div', { class: 'grid' },
    [12, 3, 3, 3, 3, 7, 5].map((s) => h('div', { class: `panel span-${s}` }, h('div', { class: 'skeleton' }), h('div', { class: 'skeleton' }))));
}

function build(d) {
  let delay = 0;
  const panel = (cls, ...kids) => {
    const p = h('div', { class: `panel ${cls}` }, ...kids);
    p.style.setProperty('animation-delay', `${(delay += 60)}ms`);
    return p;
  };

  return h('div', { class: 'grid' },
    panel('span-12 hero', ...hero(d)),
    panel('span-3 stat', ...stat('Klausuren', d.exam_count, 'offen', d.next_exam ? `nächste: ${d.next_exam.subject}` : 'keine geplant', ICON_CAL)),
    panel('span-3 stat', ...stat('Heute', minutes(d.today_summary.minutes), '', `${d.today_summary.done}/${d.today_summary.total} Blöcke erledigt`, ICON_TASK)),
    panel('span-3 stat', ...stat('Diese Woche', minutes(d.week.total_minutes), '', `${d.week.tasks_done} Aufgaben erledigt`, ICON_CHART)),
    panel('span-3 stat', ...stat('Lernserie', d.week.streak, d.week.streak === 1 ? 'Tag' : 'Tage', d.week.streak ? 'Weiter so!' : 'Starte heute deine Serie', ICON_CHART)),
    panel('span-7', ...todayPanel(d)),
    panel('span-5', ...examsPanel(d)),
    panel('span-7', ...progressPanel(d)),
    panel('span-5', ...weekPanel(d)),
  );
}

// ---------- Begrüßung + nächste Klausur ----------
function hero(d) {
  const name = d.user_name ? `, ${d.user_name}` : '';
  const msg = h('p');
  const e = d.next_exam;
  let text;
  if (!e) {
    text = 'Ich habe noch keine Klausuren gespeichert. Trage deine Termine unter „Klausuren“ ein – danach erstelle ich deinen Lernplan.';
  } else {
    const when = e.days_left === 0 ? 'heute' : e.days_left === 1 ? 'morgen' : `am ${dateLong(e.date)}`;
    text = `Hier ist dein Lagebericht. Deine nächste Klausur ist ${e.subject} ${when}${e.time ? ` um ${e.time} Uhr` : ''}. `;
    text += d.today_summary.total
      ? `Heute stehen ${d.today_summary.total} Lernblöcke mit insgesamt ${minutes(d.today_summary.minutes)} an.`
      : 'Für heute sind noch keine Lernaufgaben geplant.';
    if (d.overdue_tasks.length) text += ` ${d.overdue_tasks.length} Aufgabe(n) von früher sind noch offen.`;
  }
  requestAnimationFrame(() => typeText(msg, text));

  const left = h('div', { class: 'hero-text' },
    h('span', { class: 'eyebrow' }, `${d.class_name || 'JARVIS'} · ${dateLong(d.today)}`),
    h('h2', {}, `${d.greeting}`, h('span', { class: 'accent' }, name), '.'),
    msg,
    e
      ? h('div', { class: 'next-exam' },
          h('div', {}, h('span', { class: 'label' }, 'Nächste Klausur'), h('span', { class: 'value' }, e.subject)),
          h('div', {}, h('span', { class: 'label' }, 'Datum'), h('span', { class: 'value' }, dateShort(e.date))),
          h('div', {}, h('span', { class: 'label' }, 'Uhrzeit'), h('span', { class: 'value' }, e.time ? `${e.time} Uhr` : 'unbekannt')))
      : h('a', { class: 'btn primary', href: '#/exams' }, '+ Klausur hinzufügen'),
  );

  const right = e
    ? ring({ value: Math.max(0, 28 - e.days_left), max: 28, center: String(e.days_left), caption: e.days_left === 1 ? 'Tag' : 'Tage', urgent: e.days_left <= 3 })
    : ring({ value: 0, max: 1, center: '—', caption: 'Standby' });
  return [left, right];
}

function stat(label, value, unit, hint, paths) {
  return [
    icon(paths, 'spark'),
    h('div', { class: 'label' }, label),
    h('div', { class: 'value' }, String(value), unit ? h('small', {}, unit) : null),
    h('div', { class: 'hint' }, hint),
  ];
}

// ---------- Heutige Aufgaben ----------
function todayPanel(d) {
  const head = h('div', { class: 'panel-head' }, h('h2', {}, 'Heute'), h('span', { class: 'meta' }, `${d.today_summary.done}/${d.today_summary.total} erledigt`));
  const out = [head];
  if (d.overdue_tasks.length) {
    out.push(h('div', { class: 'alert' }, '⚠', h('span', {}, `${d.overdue_tasks.length} nicht erledigte Aufgabe(n) aus den letzten Tagen werden bei der nächsten Planung berücksichtigt.`)));
  }
  if (!d.today_tasks.length) {
    out.push(h('div', { class: 'empty' }, icon(ICON_TASK), h('div', {}, 'Für heute sind keine Lernblöcke geplant.'),
      h('small', {}, d.exam_count ? 'Der automatische Lernplaner verteilt hier bald deine Lernblöcke.' : 'Füge zuerst deine Klausuren hinzu.')));
    return out;
  }
  out.push(h('ul', { class: 'tasks' }, d.today_tasks.map(taskItem)));
  return out;
}

function taskItem(t) {
  if (t.kind === 'break') {
    return h('li', { class: 'task break' }, h('span', {}, '☕'), h('div', {}, h('div', { class: 'task-sub' }, `${t.start_time || ''} Pause`)), h('span', { class: 'task-min' }, `${t.minutes}′`));
  }
  const cb = h('input', {
    type: 'checkbox', class: 'check', checked: t.status === 'done', 'aria-label': `${t.title} erledigt`,
    onchange: async () => {
      li.classList.toggle('done', cb.checked);
      try {
        await api.setTaskStatus(t.id, cb.checked ? 'done' : 'open');
        if (cb.checked) toast('Erledigt. Gut gemacht!');
        renderDashboard(root);
      } catch (err) {
        cb.checked = !cb.checked; li.classList.toggle('done', cb.checked); toast(err.message, 'error');
      }
    },
  });
  const li = h('li', { class: `task ${t.status === 'done' ? 'done' : ''}` },
    cb,
    h('div', {}, h('div', { class: 'task-title' }, t.subject ? `${t.subject} – ${t.title}` : t.title),
      h('div', { class: 'task-sub' }, [t.start_time ? `${t.start_time} Uhr` : null, t.kind === 'review' ? 'Wiederholung' : 'Lernblock'].filter(Boolean).join(' · '))),
    h('span', { class: 'task-min' }, `${t.minutes} min`),
  );
  return li;
}

// ---------- Kommende Klausuren ----------
function examsPanel(d) {
  const head = h('div', { class: 'panel-head' }, h('h2', {}, 'Nächste Klausuren'), h('a', { class: 'meta', href: '#/exams' }, 'Alle →'));
  if (!d.upcoming_exams.length) {
    return [head, h('div', { class: 'empty' }, icon(ICON_CAL), h('div', {}, 'Keine anstehenden Klausuren.'), h('a', { class: 'btn sm', href: '#/exams' }, 'Klausur eintragen'))];
  }
  return [head, h('ul', { class: 'timeline' }, d.upcoming_exams.map((e) => {
    const cls = e.days_left === 0 ? 'today' : e.days_left <= 3 ? 'soon' : '';
    return h('li', {},
      h('div', {}, h('div', { class: 'subj' }, e.subject), h('div', { class: 'when' }, `${weekday(e.date)}, ${dateShort(e.date).split(', ').pop()}${e.time ? ` · ${e.time} Uhr` : ''}`)),
      h('span', { class: `badge ${cls}` }, daysLabel(e.days_left)));
  }))];
}

// ---------- Fortschritt ----------
function progressPanel(d) {
  const head = h('div', { class: 'panel-head' }, h('h2', {}, 'Lernfortschritt'), h('span', { class: 'meta' }, `${minutes(d.overall_progress.done_minutes)} von ${minutes(d.overall_progress.planned_minutes)}`));
  const rows = d.subject_progress.slice(0, 6).map((p) => {
    const fill = h('i');
    requestAnimationFrame(() => requestAnimationFrame(() => fill.style.setProperty('width', `${p.percent}%`)));
    return h('div', { class: 'bar-row' },
      h('div', { class: 'bar-label' }, h('span', {}, p.subject), h('span', {}, p.planned_minutes ? `${p.percent} %` : 'noch kein Plan')),
      h('div', { class: 'meter' }, fill));
  });
  return [head, h('div', { class: 'progress-wrap' },
    ring({ value: d.overall_progress.percent, max: 100, center: `${d.overall_progress.percent}%`, caption: 'Gesamt', size: 'sm' }),
    h('div', { class: 'bars' }, rows.length ? rows : h('div', { class: 'empty' }, 'Sobald ein Lernplan existiert, siehst du hier deinen Fortschritt pro Fach.')))];
}

// ---------- Woche ----------
function weekPanel(d) {
  const max = Math.max(60, ...d.week.days.map((x) => x.minutes));
  const head = h('div', { class: 'panel-head' }, h('h2', {}, 'Letzte 7 Tage'), h('span', { class: 'meta' }, minutes(d.week.total_minutes)));
  return [head, h('div', { class: 'week', role: 'img', 'aria-label': 'Lernminuten der letzten 7 Tage' }, d.week.days.map((day) => {
    const bar = h('i', { title: `${day.minutes} min` });
    requestAnimationFrame(() => requestAnimationFrame(() => bar.style.setProperty('height', `${Math.round((day.minutes / max) * 100)}%`)));
    return h('div', { class: `col ${day.date === d.today ? 'today' : ''}` }, bar, h('span', {}, weekday(day.date)));
  }))];
}
