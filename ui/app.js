const form = document.querySelector('#ask-form');
const input = document.querySelector('#question');
const send = document.querySelector('#send');
const welcome = document.querySelector('#welcome');
const conversation = document.querySelector('#conversation');
const historyEl = document.querySelector('#history');
let history = JSON.parse(localStorage.getItem('haven-history') || '[]');

const escapeHTML = (value = '') => value.replace(/[&<>'"]/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[char]));
const sourceLabel = path => (path || 'Reference source').split('/').pop().replace(/[_-]/g, ' ').replace(/\.(pdf|html?)$/i, '').replace(/\b\w/g, c => c.toUpperCase());

function renderAnswer(text) {
  let safe = escapeHTML(text);
  safe = safe.replace(/\[Source\s+(\d+)\]/gi, (_, n) => `<button class="citation" data-source="${n}">Source ${n}</button>`);
  safe = safe.replace(/^###? (.+)$/gm, '<strong>$1</strong>');
  safe = safe.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  const blocks = safe.split(/\n{2,}/).map(block => {
    if (/^(?:- |\* )/m.test(block)) return `<ul>${block.split('\n').map(x => `<li>${x.replace(/^(?:- |\* )/, '')}</li>`).join('')}</ul>`;
    return `<p>${block.replace(/\n/g, '<br>')}</p>`;
  });
  return blocks.join('');
}

function renderHistory() {
  historyEl.innerHTML = history.length ? history.slice(0, 8).map(item => `<button class="history-item" data-question="${escapeHTML(item)}">${escapeHTML(item)}</button>`).join('') : '<p class="history-empty">Your recent questions will appear here.</p>';
}

async function ask(question) {
  if (!question.trim() || send.disabled) return;
  welcome.classList.add('hidden'); conversation.classList.remove('hidden');
  conversation.insertAdjacentHTML('beforeend', `<div class="message user-message"><div class="user-bubble">${escapeHTML(question)}</div></div><div class="message assistant-row pending"><div class="assistant-avatar">⌂</div><div><div class="thinking"><i></i><i></i><i></i></div></div></div>`);
  input.value = ''; input.style.height = 'auto'; send.disabled = true; window.scrollTo({top:document.body.scrollHeight,behavior:'smooth'});
  try {
    const response = await fetch('/ask', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question, k:20, rerank_top_n:5})});
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Something went wrong.');
    const sources = data.documents.map((doc, i) => `<article class="source-card" id="source-${i+1}"><div class="source-head"><span class="source-number">${i+1}</span><span class="source-name">${escapeHTML(sourceLabel(doc.source))}</span><span class="source-page">Page ${escapeHTML(String(doc.page))}</span></div><p class="source-excerpt">${escapeHTML(doc.content)}</p></article>`).join('');
    document.querySelector('.pending').outerHTML = `<div class="message assistant-row"><div class="assistant-avatar">⌂</div><div><div class="answer">${renderAnswer(data.answer)}</div>${sources ? `<div class="sources"><div class="sources-title">SOURCES USED · ${data.documents.length}</div><div class="source-list">${sources}</div></div>` : ''}</div></div>`;
    history = [question, ...history.filter(x => x !== question)].slice(0, 12); localStorage.setItem('haven-history', JSON.stringify(history)); renderHistory();
  } catch (error) {
    document.querySelector('.pending').outerHTML = `<div class="message assistant-row"><div class="assistant-avatar">!</div><div class="answer"><p><strong>I couldn’t complete that answer.</strong><br>${escapeHTML(error.message)} Please check that the API is running and try again.</p></div></div>`;
  } finally { send.disabled = false; input.focus(); window.scrollTo({top:document.body.scrollHeight,behavior:'smooth'}); }
}

form.addEventListener('submit', event => { event.preventDefault(); ask(input.value.trim()); });
input.addEventListener('keydown', event => { if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); form.requestSubmit(); }});
input.addEventListener('input', () => { input.style.height='auto'; input.style.height=Math.min(input.scrollHeight,150)+'px'; });
document.querySelectorAll('.prompt-card').forEach(card => card.addEventListener('click', () => ask(card.dataset.question)));
historyEl.addEventListener('click', e => { const item=e.target.closest('[data-question]'); if(item) ask(item.dataset.question); });
conversation.addEventListener('click', e => { const cite=e.target.closest('.citation'); if(!cite)return; const source=document.querySelector(`#source-${cite.dataset.source}`); source?.scrollIntoView({behavior:'smooth',block:'center'}); source?.classList.add('highlight'); setTimeout(()=>source?.classList.remove('highlight'),1600); });
document.querySelector('#new-chat').addEventListener('click', () => { conversation.innerHTML=''; conversation.classList.add('hidden'); welcome.classList.remove('hidden'); document.querySelector('#sidebar').classList.remove('open'); document.querySelector('#scrim').classList.remove('show'); input.focus(); window.scrollTo({top:0,behavior:'smooth'}); });
const sidebar=document.querySelector('#sidebar'), scrim=document.querySelector('#scrim'); document.querySelector('#menu-button').addEventListener('click',()=>{sidebar.classList.add('open');scrim.classList.add('show')}); scrim.addEventListener('click',()=>{sidebar.classList.remove('open');scrim.classList.remove('show')});
const dialog=document.querySelector('#about-dialog'); document.querySelector('#about-button').addEventListener('click',()=>dialog.showModal()); document.querySelector('.close-dialog').addEventListener('click',()=>dialog.close());
renderHistory();
