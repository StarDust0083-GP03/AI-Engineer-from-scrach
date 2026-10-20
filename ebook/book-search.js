'use strict';
// Search the embedded text, not fetch(): works from a moved, offline HTML file.
(() => {
  const input = document.getElementById('fulltext-search');
  if (!input) return;
  const output = document.getElementById('fulltext-results');
  const status = document.getElementById('fulltext-status');
  const entries = [...document.querySelectorAll('.volume section[id]')].map(section => ({
    id: section.id,
    heading: section.querySelector('h2')?.textContent || '',
    chapter: section.closest('.volume').querySelector('h1').textContent,
    text: section.textContent.replace(/\s+/g, ' ').trim()
  }));
  let timer;
  function find() {
    output.replaceChildren();
    const query = input.value.trim().toLocaleLowerCase();
    if (!query) { status.textContent = '全文在本文件内搜索，无需网络。'; return; }
    const terms = query.split(/\s+/);
    const matches = entries.filter(entry => terms.every(term => entry.text.toLocaleLowerCase().includes(term)));
    status.textContent = matches.length ? `找到 ${matches.length} 个小节${matches.length > 40 ? '，显示前 40 个，请增加关键词缩小范围' : ''}` : '没有匹配内容，请尝试别名或缩短关键词。';
    for (const entry of matches.slice(0, 40)) {
      const item = document.createElement('li');
      const link = document.createElement('a');
      link.href = '#' + entry.id;
      link.textContent = entry.chapter + ' / ' + entry.heading;
      const snippet = document.createElement('p');
      const position = entry.text.toLocaleLowerCase().indexOf(terms[0]);
      const start = Math.max(0, position - 36);
      snippet.textContent = (start ? '…' : '') + entry.text.slice(start, start + 180) + (entry.text.length > start + 180 ? '…' : '');
      item.append(link, snippet);
      output.append(item);
    }
  }
  input.addEventListener('input', () => { clearTimeout(timer); timer = setTimeout(find, 120); });
  input.addEventListener('keydown', event => {
    if (event.key === 'Escape') { clearTimeout(timer); input.value = ''; find(); }
    if (event.key === 'Enter') { clearTimeout(timer); find(); }
  });
  find();
})();
