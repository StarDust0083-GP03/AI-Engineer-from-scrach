# AI 工程师阅读本 2.0

## 直接打开哪个文件

**推荐 `book.html`：单文件离线合订本。** 正文、图解、样式、脚本、全文搜索和覆盖地图全部内嵌，可单独复制到其他目录或设备。不需要源代码仓库、网络、服务器或安装依赖。外部论文链接只是选读。

- `index.html`：分章目录，适合短时阅读；复制时保留整个 `ebook/` 文件夹。
- `25.html`：不读代码的全书推演与术语手册，适合初次阅读或复习。
- `coverage.html`：项目材料到 HTML 讲解的映射与覆盖口径。

## 内容

18 章主线（01–18，02 的文件名是 `react.html`）、学习附录 19、实战补编 20–25：

| 文件 | 新增内容 |
| --- | --- |
| `20.html` | Agentic RAG 三幕轨迹、多库路由、Naive 对比、模拟和失败边界 |
| `21.html` | 多 Agent 架构实验、分层报告、框架实践、质量门、HITL、Agent Ops |
| `22.html` | learn-claude-code s01–s20：工具、权限、上下文、任务、后台、团队、Worktree、MCP |
| `23.html` | 六个 Electron Harness 项目、PIV / Ralph、Ragent 平台主链路 |
| `24.html` | Hermes 01–09：Prompt、环境、Cron、记忆 Provider、Gateway、Eval |
| `25.html` | 全书纸上实验、计算例子、LLM 十个台阶、CI / Python / Shell / Linux 与术语 |

阅读主线不要求读源码或执行练习，代码块与原材料链接仅用于可选追溯。项目实现、教学模拟、设计笔记和编辑推演分别标注；纸上数字不是实测指标。

覆盖清单基于当前 Git 跟踪源文件，按材料单元分组；大型引入项目覆盖模块职责与主要流程，不是逐行源码或全部 API 的替代手册。翻译、图像、导出文件、课程展示站等按所属主题合并。文件归属完整，不等于运行验证完整。

Hermes 的剪枝学习副本不可直接运行；部分 demo 需要仓库外的完整源码。没有在本轮运行所有项目、连接聊天平台或调用收费模型 API。

## 阅读功能

- 合订本全文搜索匹配小节正文；空格分隔多个关键词表示同时包含；最多展示 40 项。Esc 清空，搜索不隐藏正文。
- 分章目录搜索匹配标题、简介与素材路径。
- 字号为 18 / 20 / 22 / 24px；窄屏目录可展开，流程图纵向排列。
- 脚注可双向跳转；分章末尾有前后篇导航。
- 阅读进度保存在当前浏览器，记录篇章与小节；目录页提供续读链接。不跨设备同步。
- 浏览器打印或 Ctrl+P 可输出 PDF；正文答案自动展开，庞大的文件追溯清单不参与打印。
- `file://` 的 localStorage 是否跨文件共享由浏览器决定。需要稳定跨章续读时可在仓库根目录运行 `python3 -m http.server 8000 --bind 127.0.0.1`，打开 `http://127.0.0.1:8000/ebook/`。合订本阅读与搜索不依赖这个服务。

## 维护与检查

手工维护 `01.html`、`react.html`、`03.html`–`25.html`、`index.html` 和共享阅读器。`build_book.py` **只生成** `book.html`、`coverage.html`、`coverage.json`，不会覆盖手工章节。

```bash
python3 ebook/build_book.py
python3 ebook/test_book.py
node --check ebook/reader.js
node --check ebook/book-search.js
bash ebook/test_browser.sh  # 需 agent-browser 与 Chromium
```

静态检查覆盖 28 页的链接、唯一锚点、脚注双向链接、合订本资源内嵌、正文齐备及源文件映射。浏览器检查覆盖移动端、Surface 视口、字号边界、续读、搜索、打印恢复与离线资源。视口模拟不是实际 Surface 硬件测试。
