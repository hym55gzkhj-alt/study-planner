import { api } from './api.js';
import { h, toast } from './ui.js';

const MODES = [
  { id: 'chat', icon: '💬', label: 'Fragen', hint: 'Frag JARVIS alles – auch zu deinen Klausuren.' },
  { id: 'explain', icon: '📘', label: 'Erklären', hint: 'JARVIS erklärt ein Thema Schritt für Schritt.' },
  { id: 'quiz', icon: '🎯', label: 'Abfragen', hint: 'JARVIS stellt dir Fragen und gibt Feedback.' },
  { id: 'cards', icon: '🧠', label: 'Karteikarten', hint: 'JARVIS erstellt Karteikarten zum Thema.' },
  { id: 'summary', icon: '📝', label: 'Lernzettel', hint: 'JARVIS fasst ein Thema kompakt zusammen.' },
];

const QUICK = {
  chat: ['Was muss ich heute lernen?', 'Wann schreibe ich meine nächste Klausur?', 'Welche Klausur kommt zuerst?', 'Erstelle mir einen Lernplan für morgen.', 'Was habe ich diese Woche geschafft?'],
  explain: ['Erkläre mir das wichtigste Thema für meine nächste Klausur.', 'Erkläre mir das so, als wäre ich neu im Thema: '],
  quiz: ['Frag mich ab! Starte mit einer leichten Frage.', 'Quiz mich zu: '],
  cards: ['Erstelle Karteikarten zu: '],
  summary: ['Erstelle mir einen Lernzettel zu: '],
};

const state = { mode: 'chat', subject: '', busy: false, aiEnabled: false };
let els = {};

export async function renderChat(container) {
  let hist = { messages: [], ai_enabled: false };
  let exams = [];
  try {
    [hist, exams] = await Promise.all([api.chatHistory(), api.exams(true)]);
  } catch (err) { toast(err.message, 'error'); }
  state.aiEnabled = hist.ai_enabled;

  els.log = h('div', { class: 'chat-log', 'aria-live': 'polite' });
  els.input = h('textarea', { class: 'chat-input', rows: 1, maxlength: 4000, placeholder: 'Schreib JARVIS eine Nachricht …', 'aria-label': 'Nachricht',
    onkeydown: (e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); } },
    oninput: autosize });
  els.send = h('button', { class: 'btn primary send', type: 'button', onclick: () => send(), 'aria-label': 'Senden' }, '➤');
  els.quick = h('div', { class: 'quick' });
  els.hint = h('p', { class: 'mode-hint' });

  const subjects = [...new Set(exams.map((e) => e.subject))];
  const subjectSel = h('select', { id: 'chat-subject', onchange: (e) => { state.subject = e.target.value; } },
    h('option', { value: '' }, 'Allgemein / kein Fach'),
    subjects.map((s) => h('option', { value: s, selected: s === state.subject }, s)));

  const modeBtns = h('div', { class: 'modes', role: 'radiogroup', 'aria-label': 'Lernmodus' }, MODES.map((m) =>
    h('button', { type: 'button', class: 'mode', role: 'radio', dataset: { mode: m.id }, onclick: () => setMode(m.id) },
      h('span', { class: 'mode-icon' }, m.icon), m.label)));

  const side = h('div', { class: 'panel span-4 chat-side' },
    h('div', { class: 'panel-head' }, h('h2', {}, 'Lernmodus')),
    modeBtns, els.hint,
    h('div', { class: 'field full' }, h('label', { for: 'chat-subject' }, 'Fach'), subjectSel),
    h('div', { class: 'panel-head', style: { 'margin-top': '18px' } }, h('h2', {}, 'Schnellstart')),
    els.quick,
    h('div', { class: `ai-status ${state.aiEnabled ? 'on' : ''}` },
      h('span', { class: `dot ${state.aiEnabled ? 'online' : ''}` }),
      state.aiEnabled ? 'KI-Kern aktiv' : 'Offline-Modus: nur Fragen zu deinen Daten. Für den KI-Lernpartner ANTHROPIC_API_KEY in .env setzen.'),
  );

  const main = h('div', { class: 'panel span-8 chat-main' },
    h('div', { class: 'panel-head' }, h('h2', {}, 'JARVIS'),
      h('button', { class: 'btn sm ghost', type: 'button', onclick: clearChat }, 'Verlauf löschen')),
    els.log,
    h('div', { class: 'chat-bar' }, els.input, els.send));

  container.replaceChildren(h('div', { class: 'grid chat-grid' }, main, side));
  setMode(state.mode, modeBtns);

  if (!hist.messages.length) {
    addMessage('assistant', `Hallo! Ich bin JARVIS, dein Lernpartner. ${state.aiEnabled
      ? 'Ich kann dir Themen erklären, dich abfragen, Karteikarten und Lernzettel erstellen – und kenne deine Klausurtermine.'
      : 'Ich kenne deine Klausurtermine und Aufgaben. Frag mich zum Beispiel: „Was muss ich heute lernen?“'} Wähle links einen Modus und ein Fach.`);
  } else {
    hist.messages.forEach((m) => addMessage(m.role, m.content));
  }
  scrollDown();
}

function setMode(id, root = document) {
  state.mode = id;
  root.querySelectorAll?.('.mode').forEach((b) => {
    const on = b.dataset.mode === id;
    b.classList.toggle('active', on);
    b.setAttribute('aria-checked', String(on));
  });
  const m = MODES.find((x) => x.id === id);
  els.hint.textContent = m.hint;
  els.quick.replaceChildren(...QUICK[id].map((q) => h('button', { type: 'button', class: 'chip', onclick: () => {
    if (q.endsWith(': ')) { els.input.value = q + (state.subject ? `${state.subject} – ` : ''); els.input.focus(); autosize(); }
    else send(q);
  } }, q.endsWith(': ') ? q.replace(/: $/, ' …') : q)));
}

function autosize() {
  els.input.style.setProperty('height', 'auto');
  els.input.style.setProperty('height', `${Math.min(els.input.scrollHeight, 160)}px`);
}

function scrollDown() { els.log.scrollTop = els.log.scrollHeight; }

function addMessage(role, text) {
  const body = h('div', { class: 'msg-body' });
  renderMarkdown(body, text);
  const msg = h('div', { class: `msg ${role}` },
    role === 'assistant' ? h('span', { class: 'avatar', 'aria-hidden': 'true' }, h('i'), h('i')) : null,
    body);
  els.log.append(msg);
  return body;
}

async function send(text) {
  const message = (text ?? els.input.value).trim();
  if (!message || state.busy) return;
  state.busy = true;
  els.send.disabled = true;
  els.input.value = ''; autosize();
  addMessage('user', message);
  const body = addMessage('assistant', '');
  body.parentElement.classList.add('typing');
  body.append(h('span', { class: 'dots' }, h('i'), h('i'), h('i')));
  scrollDown();

  let full = '';
  try {
    await api.chatStream({ message, mode: state.mode, subject: state.subject || null }, (ev) => {
      if (ev.type === 'delta') {
        full += ev.text;
        body.parentElement.classList.remove('typing');
        renderMarkdown(body, full);
        scrollDown();
      } else if (ev.type === 'error') {
        body.parentElement.classList.remove('typing');
        body.parentElement.classList.add('error');
        renderMarkdown(body, (full ? full + '\n\n' : '') + `⚠ ${ev.message}`);
      }
    });
    if (!full && !body.parentElement.classList.contains('error')) renderMarkdown(body, '…');
  } catch (err) {
    body.parentElement.classList.add('error');
    renderMarkdown(body, `⚠ ${err.message}`);
  } finally {
    body.parentElement.classList.remove('typing');
    state.busy = false;
    els.send.disabled = false;
    els.input.focus();
    scrollDown();
  }
}

async function clearChat() {
  if (!confirm('Gesamten Chatverlauf löschen?')) return;
  try { await api.clearChat(); els.log.replaceChildren(); addMessage('assistant', 'Verlauf gelöscht. Womit fangen wir an?'); }
  catch (err) { toast(err.message, 'error'); }
}

// ---------- Sicherer Mini-Markdown-Renderer (erzeugt nur DOM-Knoten, nie HTML-Strings) ----------
function inline(text) {
  const out = [];
  const re = /(\*\*[^*]+\*\*|`[^`]+`|_[^_]+_)/g;
  let last = 0, m;
  while ((m = re.exec(text))) {
    if (m.index > last) out.push(text.slice(last, m.index));
    const t = m[0];
    if (t.startsWith('**')) out.push(h('strong', {}, t.slice(2, -2)));
    else if (t.startsWith('`')) out.push(h('code', {}, t.slice(1, -1)));
    else out.push(h('em', {}, t.slice(1, -1)));
    last = m.index + t.length;
  }
  if (last < text.length) out.push(text.slice(last));
  return out;
}

function renderMarkdown(el, src) {
  const nodes = [];
  let list = null;
  for (const raw of src.split('\n')) {
    const line = raw.trimEnd();
    const ul = line.match(/^\s*[-*•]\s+(.*)/);
    const ol = line.match(/^\s*(\d+)[.)]\s+(.*)/);
    if (ul || ol) {
      const tag = ul ? 'ul' : 'ol';
      if (!list || list.tagName.toLowerCase() !== tag) { list = h(tag); nodes.push(list); }
      list.append(h('li', {}, inline(ul ? ul[1] : ol[2])));
      continue;
    }
    list = null;
    const hd = line.match(/^#{1,4}\s+(.*)/);
    if (hd) nodes.push(h('h4', {}, inline(hd[1])));
    else if (line.trim() === '---') nodes.push(h('hr'));
    else if (line.trim()) nodes.push(h('p', {}, inline(line)));
  }
  el.replaceChildren(...nodes);
}
