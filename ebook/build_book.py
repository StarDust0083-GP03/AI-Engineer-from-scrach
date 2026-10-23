"""Build only coverage.html, coverage.json and book.html; authored chapters stay untouched.
Run: python3 ebook/build_book.py. Standard library only, deterministic for a source snapshot.
"""
from collections import defaultdict
from html import escape, unescape
from pathlib import Path
import json
import re
import subprocess

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
CHAPTERS = ['01.html', 'react.html'] + [f'{n:02}.html' for n in range(3, 26)]
# Module-level coverage: not a claim of per-line commentary or runtime verification.
ROUTES = {
    '00-大纲': ('19.html', '教学顺序、能力层次与学习路线'),
    '01-Agent': ('01.html', '工具调用、协议、执行与消息回填'),
    '01-Agent/02-Agent_react': ('react.html', '工具循环、观察、退出与错误'),
    '01-Agent/02-Plan-and-Execute': ('03.html', '规划、执行、共享状态与重规划'),
    '01-Agent/03-Reﬂexion': ('03.html', '尝试、评估、反思与再次尝试'),
    '01-Agent/04-LATS': ('03.html', '树搜索、探索利用与预算'),
    '01-Agent/05-Multi-Agent-Crew': ('08.html', '角色分工与任务编排'),
    '02-RAG': ('04.html', '入库、分块、嵌入、检索与回答'),
    '02-RAG/02-RAG_basic': ('25.html#rag', '清洗、PDF、切块、向量、BM25、混合、RRF、重排与 MMR；原理详见 04–05'),
    '02-RAG/03-high_level_RAG': ('05.html', 'Graph / Agentic / Self / Corrective / Adaptive RAG'),
    '02-RAG/04_RAG_Evaluation': ('06.html', '检索指标、生成指标、评测分工'),
    '02-RAG/05_PDF_process': ('06.html', '文字层、OCR、版面、表格与清洗；out 是导出产物'),
    '02-RAG/06 Agentic RAG': ('20.html', '多库路由、模拟边界、超时与 Naive 对照'),
    '03-memory': ('07.html', '窗口、摘要、长期检索、三因子与组合'),
    '04-multiagent': ('08.html', '黑板、订阅、队列、状态机、路由、脱敏、冲突与刹车'),
    '04-multiagent/multi-agent-arch': ('21.html', '架构实验、分层报告、监督、框架实践与 Agent Ops'),
    '05-model-route': ('09.html', '模型选择、熔断、缓存、权限、计费、灰度与治理'),
    '06-harnes': ('10.html', '工作约束、规则、工具、环境、状态与反馈'),
    '06-harnes/01-simple_harnes_demo': ('10.html', '最小 PIV、规则与验证闭环'),
    '06-harnes/02-rag-harness-demo': ('23.html#piv', 'TF-IDF 基线、模板生成、LLM 升级、Hook 与离线测试'),
    '06-harnes/harness-engineering-demo': ('23.html#piv', 'Schedulr、PIV、AST 导航与跨会话 Ralph；业务源码按项目合并'),
    '06-harnes/learn-claude-code': ('22.html', 's01–s20 全机制；多语言说明、图片和展示站合并归属'),
    '06-harnes/learn-harness-engineering': ('23.html#projects', '六项目、starter / solution、讲义、模板与展示站'),
    '06-harnes/ragent': ('23.html#ragent', '平台模块职责、入库与问答主链路、流式任务、检索容错；非逐个 API 手册'),
    '07-llm_from_scrach': ('13.html', '模型、训练、现代架构、MoE、SFT、RM、PPO、GRPO'),
    '08-hermes-agent': ('24.html', '记忆、主循环、Prompt、环境、Cron、Provider、Gateway 与评测'),
    '08-hermes-agent/13-pi-agent': ('16.html', 'Pi 补充笔记，与根目录 Pi 材料合并阅读'),
    '08-hermes-agent/hermes-study': ('24.html', '只读源码学习副本；不作为可直接运行工程'),
    '09-loop-engineering': ('11.html', '目标、状态、验证、持续推进与成本'),
    '10-CICD': ('12.html', '基础、pytest、GitLab CI、故障排查、Jenkins 与工具'),
    '10-CICD/09-writing': ('25.html#cicd', 'Python、Shell、日志巡检、Linux 进程 / 网络 / 权限 / core dump'),
    '11-langgraph': ('17.html', '课程、Chatbot、TripMate、状态、恢复、async 与校验'),
    '12-hermes-agent-small': ('15.html', 'waku：Harness、Loop、Memory、Ops、评测与发布'),
    '13-pi-agent': ('16.html', '仓库学习快照：Core / Interactive、事件、会话树、压缩、HITL、能力扩展'),
    '14-deepseek-harness': ('18.html', '架构笔记：模型、工具、配置、会话与可替换边界'),
    '15-Edge-Agent': ('18.html', '研究笔记：本机推理、预算、权限、出域与端云协同'),
    '99-My idea': ('19.html', '学习指南、AI coding、Agent eval、记忆研究和演示材料'),
    '.cursor': ('coverage.html#scope', '仓库作者的绘图技能辅助，不是课程业务能力'),
}


def route(path):
    matches = [prefix for prefix in ROUTES if path == prefix or path.startswith(prefix + '/')]
    return ROUTES[max(matches, key=len)] if matches else ('coverage.html#scope', '根目录说明、环境模板或 Git 辅助配置')


def unit(path):
    parts = path.split('/')
    if len(parts) < 2:
        return '根目录支持文件'
    if path.startswith('06-harnes/learn-claude-code/') and len(parts) > 3:
        return '/'.join(parts[:3])
    if path.startswith('06-harnes/learn-harness-engineering/projects/') and len(parts) > 4:
        return '/'.join(parts[:4])
    if path.startswith('06-harnes/ragent/') and len(parts) > 3:
        return '/'.join(parts[:3])
    if path.startswith('04-multiagent/multi-agent-arch/'):
        return path if parts[-1].endswith('.ipynb') else '/'.join(parts[:2])
    return '/'.join(parts[:2]) if len(parts) > 2 else parts[0]


def title(path):
    heading = re.search(r'<h1[^>]*>(.*?)</h1>', path.read_text(), re.S)[1]
    return unescape(re.sub(r'<[^>]+>', '', heading))


def build_coverage():
    raw = subprocess.check_output(['git', 'ls-files', '-z'], cwd=REPO).decode().split('\0')
    paths = sorted(p for p in raw if p and not p.startswith('ebook/'))
    groups = defaultdict(list)
    for path in paths:
        groups[unit(path)].append(path)
    records, rows = [], []
    for key, files in sorted(groups.items()):
        target, description = route(files[0])
        # A root overview can contain several independent demos: broad roots map to broad chapters.
        if key in ROUTES:
            target, description = ROUTES[key]
        records.append({'unit': key, 'target': target, 'description': description, 'files': files})
        file_list = ''.join(f'<li><code>{escape(f)}</code></li>' for f in files)
        rows.append(f'<tr><td><strong>{escape(key)}</strong><details class="inventory-files"><summary>{len(files)} 个文件 · 展开追溯清单</summary><ul class="source-list">{file_list}</ul></details></td><td>{escape(description)}<br><a href="{target}">阅读对应讲解 →</a></td></tr>')
    snapshot = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD'], cwd=REPO).decode().strip()
    (ROOT / 'coverage.json').write_text(json.dumps({'snapshot': snapshot, 'file_count': len(paths), 'units': records}, ensure_ascii=False, indent=2) + '\n')
    content = f'''<section id="scope"><h2>覆盖口径：覆盖教学内容，不等于逐行转录</h2>
<p>这张地图将源快照 <code>{snapshot}</code> 中的 <strong>{len(paths)} 个跟踪文件</strong> 分配到 <strong>{len(records)} 个材料单元</strong>，为每个单元提供章节入口。它核对的是资料归属；正文围绕机制与执行边界重新讲解，不承诺逐行注释所有文件。</p>
<p>Ragent、Schedulr 与展示站等大型材料按模块和运行链阅读，组件细节与 API 全集仍需回到源码。不同语言、讲义、图片与 Notebook 中重复的内容归于同一知识单元，测试用于核验所属行为，日志和导出文件则作为相应流程的产物。</p>
<p>章节可离线阅读，但源项目运行可能需要另外安装依赖、准备数据或付费服务。本次不声称全部项目均已运行。Hermes 学习副本并非完整可执行发行版；DeepSeek Harness 与 Edge Agent 的研究说明也不能当作已验收系统。正文分别标记<strong>实现事实、虚构案例、候选设计与离线演算</strong>。<sup><a class="note-ref" id="note-ref-1" href="#note-1">1</a></sup></p></section>
<section id="reading"><h2>只看 HTML 的三种读法</h2><figure class="book-diagram"><table><thead><tr><th>当前问题</th><th>从哪里开始</th><th>读完核对什么</th></tr></thead><tbody><tr><td>缺少基础词义</td><td>25 术语与手算</td><td>能否独立写出状态变化</td></tr><tr><td>需要理解执行</td><td>01 至 18 主线</td><td>谁决定、谁执行、谁验证</td></tr><tr><td>正在接入工程</td><td>20 至 24 补编</td><td>边界、依赖与失败合同</td></tr><tr><td>要查来源</td><td>本页映射</td><td>章节对应哪些材料单元</td></tr></tbody></table><figcaption>图 A-1 · 按阅读问题选择入口，不要求所有读者沿同一条线前进。19 保留学习附录，合订本用于离线检索。</figcaption></figure><p>概念可用<a href="book.html#book-search">合订本搜索</a>定位，材料路径可查下表。先用章节中的输入、状态和结果复核理解，再决定是否配置项目环境；阅读验收与运行验收是两项工作。<sup><a class="note-ref" id="note-ref-2" href="#note-2">2</a></sup></p></section>
<section id="inventory"><h2>材料单元 → HTML 讲解</h2><p>展开单元可以检查具体文件；收起时保留教学归属与入口。清单负责追溯，机制说明仍在章节中。</p><table class="coverage-table"><thead><tr><th scope="col">材料与文件归属</th><th scope="col">解释内容与阅读入口</th></tr></thead><tbody>{''.join(rows)}</tbody></table></section>
<section id="notes" class="footnotes"><h2>补充脚注</h2><ol><li id="note-1"><strong>编辑补充：</strong>构建器只枚举 git ls-files 的受跟踪路径来核对归属，不读取认证内容，也不会自动执行课程项目。<a class="note-back" href="#note-ref-1">返回正文 ↑</a></li><li id="note-2"><strong>编辑补充：</strong>页面能打开且链接有效，只证明阅读产物可用。真实模型、供应商接口和源代码功能需要各自的环境与验证记录。<a class="note-back" href="#note-ref-2">返回正文 ↑</a></li></ol></section>'''
    html = f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>项目覆盖地图 · AI 工程师</title><link rel="stylesheet" href="reader.css"><script defer src="reader.js"></script></head><body><a class="skip" href="#main">跳到正文</a><header class="bar"><div class="bar-inner"><a class="brand" href="index.html">← 全书目录</a><a href="book.html">离线合订本 ↗</a></div></header><main id="main" class="wrap reading"><article><header class="chapter-head"><span class="edition">阅读本 2.0 · 项目覆盖核对</span><h1>项目覆盖地图</h1><p class="deck">从材料找到解释，从解释确认边界。</p></header>{content}<nav class="chapter-pager"><a href="25.html">← 全书推演</a><a href="book.html">打开合订本 →</a></nav></article></main><p id="notice" class="sr-only" role="status"></p></body></html>'''
    (ROOT / 'coverage.html').write_text(html)


def build_volume():
    files = CHAPTERS + ['coverage.html']
    prefixes = {f: ('c02' if f == 'react.html' else 'coverage' if f == 'coverage.html' else 'c' + f[:2]) for f in files}
    names = {f: title(ROOT / f) for f in files}
    nav = ''.join(f'<a href="#{prefixes[f]}">{escape(names[f])}</a>' for f in files)
    volumes = []
    for filename in files:
        page = (ROOT / filename).read_text()
        body = re.search(r'<article>(.*?)</article>', page, re.S)[1]
        body = re.sub(r'<details class="mobile-toc".*?</details>', '', body, flags=re.S)
        body = re.sub(r'<nav class="chapter-pager".*?</nav>', '', body, flags=re.S)
        prefix = prefixes[filename]
        body = re.sub(r'\bid="([^"]+)"', lambda m: f'id="{prefix}-{m[1]}"', body)
        body = re.sub(r'data-copy="([^"]+)"', lambda m: f'data-copy="{prefix}-{m[1]}"', body)
        body = re.sub(r'aria-labelledby="([^"]+)"',
                      lambda m: 'aria-labelledby="' + ' '.join(prefix + '-' + key for key in m[1].split()) + '"', body)

        def link(match):
            href, text = unescape(match[1]), match[2]
            if href.startswith('../'):
                return f'<span class="source-path" title="原仓库路径：{escape(href, quote=True)}">{text}</span>'
            if href.startswith('#'):
                href = '#' + prefix + '-' + href[1:]
            else:
                name, _, fragment = href.partition('#')
                if name in prefixes:
                    href = '#' + prefixes[name] + ('-' + fragment if fragment else '')
                elif name == 'index.html':
                    href = '#book-contents'
                elif name == 'book.html':
                    href = '#' + (fragment or 'book-contents')
            # Preserve footnote and source-link accessibility attributes.
            original = match[0]
            return original.replace(match[1], escape(href, quote=True), 1)

        body = re.sub(r'<a\b[^>]*href="([^"]+)"[^>]*>(.*?)</a>', link, body, flags=re.S)
        volumes.append(f'<article class="volume" id="{prefix}">{body}</article>')
    css = (ROOT / 'reader.css').read_text()
    js = (ROOT / 'reader.js').read_text() + '\n' + (ROOT / 'book-search.js').read_text()
    assert '</script' not in js.lower()
    output = f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="color-scheme" content="light"><title>AI 工程师 · 离线合订本</title><style>{css}</style></head><body><a class="skip" href="#main">跳到正文</a><header class="bar"><div class="bar-inner"><a class="brand" href="#book-contents">AI 工程师 / 合订本</a><div class="reader-tools" role="group" aria-label="阅读设置"><a href="#book-search" aria-label="搜索全书">搜索</a><button data-size="-2" aria-label="减小字号">A−</button><span id="font-value" aria-live="polite">20px</span><button data-size="2" aria-label="增大字号">A＋</button><button class="print" data-print>打印 / PDF</button></div></div><div class="progress" aria-hidden="true"></div></header><div class="reader-layout"><aside class="chapter-toc"><span class="part-label">全书导航</span><nav aria-label="全书目录">{nav}</nav></aside><main id="main" class="reading"><header class="chapter-head" id="book-contents"><span class="edition">阅读本 2.0 · 单文件离线版</span><h1>AI 工程师<br>从原理到项目</h1><p class="deck">18 章主线 · 学习附录 · 6 篇实战补编 · 项目覆盖地图</p><p>本合订文件内嵌正文、重绘图解、练习、样式与搜索，可单独保存后离线阅读。工具循环、公共自行车调度和海洋观测案例均已重新编写。基础概念可先查<a href="#c25-glossary">术语手册</a>，再做<a href="#c25">离线演算</a>；源项目运行不属于打开本文件的前提。</p><p class="meta">案例演算不冒充项目实测，架构候选不冒充已上线能力。外部资料用于可选核验，正文在没有网络时仍可读。</p><details class="mobile-toc"><summary>展开全书目录</summary><nav aria-label="移动版全书目录">{nav}</nav></details></header><section class="book-search" id="book-search"><h2>搜索全书</h2><label for="fulltext-search">关键词（空格分隔表示同时匹配）</label><input id="fulltext-search" class="index-search" type="search" placeholder="例如：审批、KV Cache、Ragent" autocomplete="off" aria-describedby="fulltext-status"><p id="fulltext-status" role="status" aria-live="polite"></p><ol id="fulltext-results"></ol><noscript>脚本已关闭，正文仍完整可读；请用浏览器 Ctrl+F 搜索。</noscript></section>{''.join(volumes)}<footer class="book-footer"><span>AI 工程师 / 阅读本 2.0</span><a href="#book-contents">回到全书目录 ↑</a></footer></main></div><p id="notice" class="sr-only" role="status"></p><script>{js}</script></body></html>'''
    (ROOT / 'book.html').write_text(output)


if __name__ == '__main__':
    build_coverage()
    build_volume()
    print('Built coverage.html, coverage.json, book.html; authored chapters unchanged.')
