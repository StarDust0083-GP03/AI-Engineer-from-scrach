"""Run with python3 ebook/test_book.py; no third-party dependencies."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote
import unittest
import json
import re
import subprocess
from functools import lru_cache

ROOT = Path(__file__).resolve().parent


class Page(HTMLParser):
    def __init__(self, path):
        super().__init__()
        self.ids, self.links, self.assets = [], [], []
        self.feed(path.read_text())

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'id' in attrs:
            self.ids.append(attrs['id'])
        if tag == 'a' and 'href' in attrs:
            self.links.append(attrs['href'])
        if tag in ('script', 'img') and 'src' in attrs:
            self.assets.append(attrs['src'])
        if tag == 'link' and attrs.get('rel') == 'stylesheet':
            self.assets.append(attrs['href'])


@lru_cache(maxsize=None)
def parsed(path):
    return Page(path)


class BookTests(unittest.TestCase):
    def test_pages_links_and_ids(self):
        pages = list(ROOT.glob('*.html'))
        self.assertEqual(len(pages), 28)
        for path in pages:
            with self.subTest(page=path.name):
                page = parsed(path)
                self.assertEqual(len(page.ids), len(set(page.ids)))
                self.assertIn('main', page.ids)
                text = path.read_text()
                self.assertNotIn('</a>><', text)
                self.assertNotIn('</small<a', text)
                for href in page.links + page.assets:
                    url = urlsplit(href)
                    if url.scheme or url.netloc:
                        self.assertNotIn(href, page.assets, 'Reading must work offline')
                        continue
                    target = (path.parent / unquote(url.path)).resolve() if url.path else path
                    self.assertTrue(target.exists(), str(target))
                    if url.fragment and target.suffix == '.html':
                        self.assertIn(unquote(url.fragment), parsed(target).ids)

    def test_honest_status_and_chapter_navigation(self):
        index = (ROOT / 'index.html').read_text()
        self.assertNotIn('status">已编', index)
        self.assertIn('search-status', index)
        for path in ROOT.glob('*.html'):
            if path.name in ('index.html', 'book.html'):
                continue
            text = path.read_text()
            with self.subTest(page=path.name):
                self.assertIn('class="chapter-pager"', text)
                self.assertIn('<figure', text)
                self.assertNotIn('与前一章 ReAct 的关系', text)
                self.assertNotIn('key[:70]', text)

    def test_footnotes_have_bidirectional_links(self):
        chapters = [p for p in ROOT.glob('*.html') if p.name not in ('index.html', 'book.html')]
        self.assertEqual(len(chapters), 26)
        for path in chapters:
            page = Page(path)
            with self.subTest(page=path.name):
                self.assertIn('notes', page.ids)
                for number in (1, 2):
                    note = re.search(rf'<li id="note-{number}"[^>]*>(.*?)</li>', path.read_text(), re.S)
                    self.assertIsNotNone(note, 'Footnotes must contain authored guidance')
                    self.assertGreater(len(re.sub(r'<[^>]+>', '', note[1]).strip()), 35)
                    self.assertIn(f'note-{number}', page.ids)
                    self.assertIn(f'note-ref-{number}', page.ids)
                    self.assertIn(f'#note-{number}', page.links)
                    self.assertIn(f'#note-ref-{number}', page.links)

    def test_volume_is_standalone_and_complete(self):
        volume = (ROOT / 'book.html').read_text()
        page = parsed(ROOT / 'book.html')
        self.assertEqual(page.assets, [], 'The single file must not fetch CSS/JS/images')
        self.assertIn('fulltext-search', page.ids)
        self.assertNotIn('&lt;br&gt;', volume, 'Titles must not display HTML markup')
        for n in range(1, 26):
            self.assertIn(f'c{n:02}', page.ids)
            self.assertIn(f'c{n:02}-notes', page.ids)
        for href in page.links:
            self.assertFalse(href.startswith('../'), 'No repository dependency in volume')
        self.assertIn('coverage-inventory', page.ids)
        self.assertIn('多库路由', volume)
        self.assertIn('B17', volume, 'The volume must contain the new observation examples')
        self.assertIn('柳川', volume, 'The volume must contain the new bicycle examples')
        self.assertEqual(volume.count('<article class="volume"'), 26)

    def test_source_coverage_is_exhaustive_without_duplicate_files(self):
        manifest = json.loads((ROOT / 'coverage.json').read_text())
        tracked = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT.parent).decode().split('\0')
        expected = {p for p in tracked if p and not p.startswith('ebook/')}
        files = [p for unit in manifest['units'] for p in unit['files']]
        self.assertEqual(len(files), len(set(files)))
        self.assertEqual(set(files), expected)
        self.assertEqual(manifest['file_count'], len(expected))
        for unit in manifest['units']:
            url = urlsplit(unit['target'])
            target = ROOT / url.path
            self.assertTrue(target.exists())
            if url.fragment:
                self.assertIn(url.fragment, parsed(target).ids)


if __name__ == '__main__':
    unittest.main()
