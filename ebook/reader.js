'use strict';

// Native scripts only: the whole ebook folder can be opened with file://.
const storage = {
  get(key) { try { return localStorage.getItem('ai-book:' + key); } catch { return null; } },
  set(key, value) { try { localStorage.setItem('ai-book:' + key, value); } catch {} }
};
const chapterFiles = ['01.html', 'react.html', ...Array.from({length: 23}, (_, i) => String(i + 3).padStart(2, '0') + '.html'), 'coverage.html', 'book.html'];
const validSection = value => typeof value === 'string' && /^[a-z][a-z0-9-]{0,100}$/.test(value);
const file = location.pathname.split('/').pop();
const sections = [...document.querySelectorAll('article section[id]')];
const notice = document.getElementById('notice');
function announce(message) { if (notice) notice.textContent = message; }

let size = Number(storage.get('size')) || 20;
if (![18, 20, 22, 24].includes(size)) size = 20;
function applySize() {
  document.documentElement.style.setProperty('--reading-size', size + 'px');
  const label = document.getElementById('font-value');
  if (label) label.textContent = size + 'px';
  document.querySelectorAll('[data-size]').forEach(button => {
    button.disabled = Number(button.dataset.size) < 0 ? size === 18 : size === 24;
  });
}
applySize();
document.querySelectorAll('[data-size]').forEach(button => button.addEventListener('click', () => {
  size = Math.max(18, Math.min(24, size + Number(button.dataset.size)));
  applySize();
  storage.set('size', size);
}));
document.querySelectorAll('[data-print]').forEach(button => button.addEventListener('click', () => window.print()));

// Validate both fields before allowing stored state to become a navigation URL.
const resume = document.getElementById('resume');
if (resume) {
  let saved;
  try { saved = JSON.parse(storage.get('bookmark')); } catch {}
  if (saved && chapterFiles.includes(saved.file) && validSection(saved.section)) {
    resume.hidden = false;
    resume.href = saved.file + '#' + saved.section;
    const number = chapterFiles.indexOf(saved.file) + 1;
    const label = {'19.html': '学习地图附录', 'coverage.html': '项目覆盖地图', 'book.html': '离线合订本'}[saved.file] || ('第 ' + String(number).padStart(2, '0') + ' 篇');
    resume.textContent = '继续阅读 · ' + label + ' →';
  }
}

let current = '';
function progress() {
  const max = document.documentElement.scrollHeight - innerHeight;
  const bar = document.querySelector('.progress');
  if (bar) bar.style.width = (max > 0 ? Math.max(0, Math.min(100, scrollY / max * 100)) : 0) + '%';
  current = '';
  for (const section of sections) {
    if (section.getBoundingClientRect().top < 210) current = section.id;
  }
  document.querySelectorAll('.chapter-toc a').forEach(a => {
    if (a.hash === '#' + current || (file === 'book.html' && current.startsWith(a.hash.slice(1) + '-'))) a.setAttribute('aria-current', 'location');
    else a.removeAttribute('aria-current');
  });
}
function saveBookmark() {
  if (chapterFiles.includes(file) && validSection(current)) {
    storage.set('bookmark', JSON.stringify({file, section: current}));
  }
}
let saveTimer;
addEventListener('scroll', () => {
  progress();
  clearTimeout(saveTimer);
  saveTimer = setTimeout(saveBookmark, 250);
}, {passive: true});
addEventListener('pagehide', saveBookmark);
addEventListener('resize', progress);
document.addEventListener('visibilitychange', () => { if (document.hidden) saveBookmark(); });
progress();

document.querySelectorAll('[data-copy]').forEach(button => button.addEventListener('click', async () => {
  const code = document.getElementById(button.dataset.copy);
  if (!code) return;
  try {
    await navigator.clipboard.writeText(code.textContent);
    button.textContent = '已复制';
    announce('代码已复制。');
  } catch {
    const selection = getSelection();
    const range = document.createRange();
    range.selectNodeContents(code);
    selection.removeAllRanges();
    selection.addRange(range);
    button.textContent = '已选中';
    announce('浏览器限制复制，代码已选中，请按 Ctrl+C 或长按复制。');
  }
  setTimeout(() => { button.textContent = '复制'; }, 1800);
}));

const search = document.getElementById('chapter-search');
const result = document.getElementById('search-status');
function filterChapters() {
  if (!search) return;
  const query = search.value.trim().toLocaleLowerCase();
  let count = 0;
  document.querySelectorAll('.part').forEach(part => {
    let matches = 0;
    part.querySelectorAll('.chapter').forEach(chapter => {
      chapter.hidden = !!query && !chapter.textContent.toLocaleLowerCase().includes(query);
      if (!chapter.hidden) matches++;
    });
    count += matches;
    part.hidden = matches === 0;
  });
  if (result) result.textContent = query ? (count ? '找到 ' + count + ' 项' : '没有匹配章节，请换个关键词或清空搜索。') : '';
}
if (search) {
  search.addEventListener('input', filterChapters);
  search.addEventListener('keydown', event => {
    if (event.key === 'Escape') { search.value = ''; filterChapters(); }
  });
  filterChapters();
}

// Print the complete document, not just the currently expanded/filtered view.
let printState = null;
addEventListener('beforeprint', () => {
  if (printState) return;
  printState = {
    details: [...document.querySelectorAll('article details:not([open]):not(.inventory-files)')],
    hidden: [...document.querySelectorAll('.part[hidden], .chapter[hidden]')]
  };
  printState.details.forEach(d => { d.open = true; });
  printState.hidden.forEach(element => { element.hidden = false; });
});
addEventListener('afterprint', () => {
  if (!printState) return;
  printState.details.forEach(d => { d.open = false; });
  printState = null;
  filterChapters();
});
