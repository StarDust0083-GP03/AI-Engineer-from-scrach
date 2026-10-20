#!/usr/bin/env bash
# Optional rendered checks: requires the agent-browser CLI and its Chromium.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
export AGENT_BROWSER_SESSION="$(agent-browser session id --scope worktree --prefix ebook-check)"
b() { agent-browser "$@"; }
trap 'b close >/dev/null 2>&1 || true' EXIT
BASE="$(python3 -c 'from pathlib import Path; import sys; print(Path(sys.argv[1]).as_uri())' "$ROOT")"

b open "$BASE/index.html"
b set viewport 390 844
for page in "$ROOT"/*.html; do
  b open "$BASE/$(basename "$page")"
  b eval '(() => {
    const check = (ok, message) => { if (!ok) throw Error(message); };
    check(document.querySelector("h1"), "Missing heading");
    check(document.documentElement.scrollWidth <= innerWidth, "Page overflow");
    const figures = [...document.querySelectorAll("figure")];
    if (!location.pathname.endsWith("index.html")) check(figures.length > 0, "Missing diagram");
    figures.forEach(f => {
      check(f.scrollWidth <= f.clientWidth, "Clipped diagram");
      check(f.querySelectorAll("li, dt, table, pre, svg").length > 0, "Empty diagram");
    });
    return "PASS mobile: " + location.pathname.split("/").pop();
  })()'
done

b open "$BASE/04.html"
for viewport in '800 1200' '1200 800'; do
  read -r width height <<< "$viewport"
  b set viewport "$width" "$height"
  b eval '(() => { if(document.documentElement.scrollWidth > innerWidth) throw Error("Surface overflow"); return "PASS Surface " + innerWidth; })()'
done
b click '[data-size="2"]'
b click '[data-size="2"]'
b eval '(() => {
  if(getComputedStyle(document.querySelector(".reading")).fontSize !== "24px") throw Error("Font size");
  if(!document.querySelector("[data-size=\"2\"]").disabled) throw Error("Font bound");
  document.querySelector("#code").scrollIntoView();
  return "PASS font bounds; scroll to RAG code section";
})()'
b wait --fn 'JSON.parse(localStorage.getItem("ai-book:bookmark") || "null")?.section === "code"'
b open "$BASE/index.html"
b eval '(() => {
  const a=document.querySelector("#resume");
  if(a.hidden || a.getAttribute("href") !== "04.html#code") throw Error("Wrong resume chapter");
  return "PASS cross-chapter resume";
})()'
b fill '#chapter-search' 'not-a-real-chapter-zzz'
b eval '(() => {
  const count=()=>document.querySelectorAll(".chapter:not([hidden])").length;
  if(count() !== 0 || !document.querySelector("#search-status").textContent.includes("没有匹配")) throw Error("Empty search");
  dispatchEvent(new Event("beforeprint"));
  if(count() !== 25) throw Error("Print lost filtered chapters");
  dispatchEvent(new Event("afterprint"));
  if(count() !== 0) throw Error("Print did not restore filter");
  return "PASS empty search and print filter restoration";
})()'
b fill '#chapter-search' 'RAG'
b eval '(() => {
  const count=document.querySelectorAll(".chapter:not([hidden])").length;
  if(count !== 5) throw Error("Expected five RAG results, got " + count);
  localStorage.setItem("ai-book:bookmark", JSON.stringify({file:"https://example.com",section:"read"}));
  return "PASS search: 5 results";
})()'
b open "$BASE/index.html"
b eval '(() => { if(!document.querySelector("#resume").hidden) throw Error("Untrusted resume target"); return "PASS invalid saved target ignored"; })()'
b open "$BASE/react.html"
b eval '(() => {
  const count=()=>document.querySelectorAll("article details[open]").length;
  const previous=count();
  dispatchEvent(new Event("beforeprint"));
  if(count() !== document.querySelectorAll("article details").length) throw Error("Print supplements missing");
  dispatchEvent(new Event("afterprint"));
  if(count() !== previous) throw Error("Print changed reading state");
  return "PASS print supplements restored";
})()'
b open "$BASE/04.html"
b set viewport 390 844
b click '#note-ref-2'
b eval '(() => {
  if(location.hash !== "#note-2") throw Error("Footnote destination");
  const note=document.querySelector("#note-2");
  if(note.textContent.trim().length < 35 || !note.querySelector(".note-back")) throw Error("Incomplete footnote");
  if(note.getBoundingClientRect().top < 60 || note.getBoundingClientRect().top > innerHeight) throw Error("Footnote obscured");
  return "PASS footnote destination and visibility";
})()'
b click '#note-2 .note-back'
b eval '(() => { if(location.hash !== "#note-ref-2") throw Error("Footnote return"); return "PASS footnote backlink"; })()'
b open "$BASE/book.html"
b set viewport 375 812
b fill '#fulltext-search' '审批'
b wait --fn 'document.querySelectorAll("#fulltext-results li").length > 0'
b eval '(() => {
  const links = [...document.querySelectorAll("#fulltext-results a")];
  if(!links.some(a => a.hash === "#c22-teams")) throw Error("Missing body search result");
  links.forEach(a => { if(!document.getElementById(a.hash.slice(1))) throw Error("Broken search target"); });
  if(document.documentElement.scrollWidth > innerWidth) throw Error("Volume mobile overflow");
  if(performance.getEntriesByType("resource").some(r => /^https?:/.test(r.name))) throw Error("External dependency");
  return "PASS full-text search, anchors, offline resources and 375px";
})()'
b fill '#fulltext-search' '<img src=x onerror=alert(1)>'
b press Enter
b eval '(() => {
  if(document.querySelectorAll("#fulltext-results img").length) throw Error("Search injected markup");
  if(!document.querySelector("#fulltext-status").textContent.includes("没有匹配")) throw Error("Volume empty state");
  dispatchEvent(new Event("beforeprint"));
  if(document.querySelector(".inventory-files[open]")) throw Error("Print expanded file inventory");
  dispatchEvent(new Event("afterprint"));
  return "PASS safe search and bounded print appendix";
})()'
b fill '#fulltext-search' '无效关键词zzz'
b press Escape
b eval '(() => { if(document.querySelector("#fulltext-search").value) throw Error("Escape failed"); return "PASS Escape clears search"; })()'
b open "$BASE/24.html#gateway"
b eval 'document.querySelector("#gateway").scrollIntoView()'
b wait --fn 'JSON.parse(localStorage.getItem("ai-book:bookmark") || "null")?.section === "gateway"'
b open "$BASE/index.html"
b eval '(() => { if(document.querySelector("#resume").getAttribute("href") !== "24.html#gateway") throw Error("New section bookmark failed"); return "PASS arbitrary chapter section resume"; })()'
printf '\nAll ebook browser checks passed.\n'
