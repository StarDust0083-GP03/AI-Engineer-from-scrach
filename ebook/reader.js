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

/* Progressive reading controls; no network and no dependency on writable storage. */
(() => {
  const root = document.documentElement;
  const themeKey = 'ebook-reader:appearance';
  const get = key => { try { return localStorage.getItem(key); } catch { return null; } };
  const put = (key, value) => { try { localStorage.setItem(key, value); } catch {} };
  let theme = get(themeKey) || root.dataset.theme || 'auto';
  if (!['auto', 'light', 'dark'].includes(theme)) theme = 'auto';
  const old = document.querySelector('button[data-theme]');
  const button = old ? old.cloneNode(true) : document.createElement('button');
  button.type = 'button';
  button.dataset.readerTheme = '';
  button.classList.add('control');
  if (old) old.replaceWith(button);
  else {
    const tools = document.querySelector('.reader-tools,.topbar .tools,.topbar,.bar-inner nav,.tools');
    if (tools) tools.append(button);
  }
  function applyTheme() {
    root.dataset.theme = theme;
    button.textContent = {auto:'自动',light:'浅色',dark:'深色'}[theme];
    button.setAttribute('aria-label', '外观：' + button.textContent + '，点击切换');
    button.title = '依次切换自动、浅色、深色';
  }
  applyTheme();
  button.addEventListener('click', () => {
    theme = {auto:'light',light:'dark',dark:'auto'}[theme];
    applyTheme(); put(themeKey, theme);
  });

  const bookNav = document.querySelector('.layout>nav.toc');
  if (bookNav) {
    const wrapper = document.createElement('details');
    wrapper.className = 'reader-book-toc';
    const wide = matchMedia('(min-width:1001px)');
    wrapper.open = wide.matches;
    wide.addEventListener('change', event => { wrapper.open = event.matches; });
    const summary = document.createElement('summary'); summary.textContent = '全书目录';
    bookNav.before(wrapper); wrapper.append(summary, bookNav);
  }
  const rail = document.querySelector('.chapter-rail');
  if (rail && !document.querySelector('.reader-mobile-toc')) {
    const list = rail.querySelector('ol');
    const header = document.querySelector('.chapter-head');
    if (list && header) {
      const toc = document.createElement('details');
      toc.className = 'reader-mobile-toc';
      const label = document.createElement('summary');
      label.textContent = '本章目录';
      toc.append(label, list.cloneNode(true));
      header.after(toc);
    }
  }
  document.querySelectorAll('table').forEach(table => {
    if (table.closest('.table-wrap')) return;
    const wrap = document.createElement('div');
    wrap.className = 'table-wrap';
    table.before(wrap); wrap.append(table);
  });
  document.querySelectorAll('.table-wrap').forEach(wrap => {
    wrap.tabIndex = 0;
    wrap.setAttribute('role', 'region');
    if (!wrap.hasAttribute('aria-label')) wrap.setAttribute('aria-label', '数据表，可横向滚动');
  });
  document.querySelectorAll('pre').forEach(pre => {
    pre.tabIndex = 0;
    pre.setAttribute('aria-label', '代码示例，可横向滚动');
  });
  document.querySelectorAll('.prose pre,.content pre').forEach(pre => {
    if (pre.querySelector('button')) return;
    const copy = document.createElement('button');
    copy.className = 'copy'; copy.type = 'button'; copy.textContent = '复制';
    pre.append(copy);
  });
  document.querySelectorAll('button.copy').forEach(oldButton => {
    // Replace the original listener so clipboard rejection always has a recovery.
    const copy = oldButton.cloneNode(true);
    oldButton.replaceWith(copy);
    copy.setAttribute('aria-label', '复制这段代码');
    copy.setAttribute('aria-live', 'polite');
    copy.addEventListener('click', async () => {
      const code = copy.closest('pre')?.querySelector('code');
      if (!code) return;
      try {
        await navigator.clipboard.writeText(code.textContent);
        copy.textContent = '已复制';
      } catch {
        const range = document.createRange(); range.selectNodeContents(code);
        const selection = getSelection(); selection.removeAllRanges(); selection.addRange(range);
        copy.textContent = '已选中';
        copy.title = '浏览器限制复制，请按 Ctrl+C 或长按复制';
      }
      setTimeout(() => { copy.textContent = '复制'; }, 1600);
    });
  });
  // Print folded examples too, then restore the reader's disclosure state.
  let printDetails = [];
  addEventListener('beforeprint', () => {
    printDetails = [...new Set([...printDetails, ...document.querySelectorAll('main details:not([open])')])];
    printDetails.forEach(details => { details.open = true; });
  });
  addEventListener('afterprint', () => {
    printDetails.forEach(details => { details.open = false; });
    printDetails = [];
  });
  const links = [...document.querySelectorAll('.chapter-rail a[href^="#"],.reader-mobile-toc a[href^="#"],nav.toc>a[href^="#"]')];
  const headings = [...new Set(links.map(link => document.getElementById(decodeURIComponent(link.hash.slice(1)))).filter(Boolean))];
  if (headings.length && 'IntersectionObserver' in window) {
    const observer = new IntersectionObserver(entries => {
      for (const entry of entries) if (entry.isIntersecting) {
        links.forEach(link => {
          if (decodeURIComponent(link.hash.slice(1)) === entry.target.id) link.setAttribute('aria-current','location');
          else link.removeAttribute('aria-current');
        });
      }
    }, {rootMargin:'-10% 0px -65% 0px'});
    headings.forEach(heading => observer.observe(heading));
  }
})();
