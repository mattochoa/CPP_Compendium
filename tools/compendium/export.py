"""Export notes (Header Cards by default) to print-ready PDF.

The Markdown in the vault is canonical; PDFs are disposable derivatives kept in
`CPP Compendium/__RESOURCES__/std-headers-pdf/` (git-ignored). Pipeline:
    note.md -> clean Markdown (no frontmatter, wikilinks flattened, cc directives dropped)
            -> HTML (python-markdown, or a small built-in fallback)
            -> PDF  (Microsoft Edge / Chrome headless `--print-to-pdf`)
"""
from __future__ import annotations

import html
import re
import shutil
import subprocess
from pathlib import Path

from . import paths
from .notes import Note

BROWSERS = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "msedge", "google-chrome", "chromium", "chromium-browser", "chrome",
]
WIKILINK = re.compile(r"\[\[([^\]\|#]+)(?:#[^\]\|]*)?(?:\|([^\]]+))?\]\]")
CALLOUT = re.compile(r"^>\s*\[!([A-Za-z-]+)\][+-]?\s*(.*)$")
DIRECTIVE_LINE = re.compile(r"^\s*//\s*(cc|expect):.*$\n?", re.M)

CSS = """
@page { size: Letter; margin: 16mm 14mm 18mm 14mm; }
body { font: 10.5pt/1.45 'Segoe UI', system-ui, sans-serif; color: #1e293b; }
h1 { font-size: 20pt; color: #0f172a; border-bottom: 3px solid #ca8a04; padding-bottom: 4px; margin-top: 0; }
h2 { font-size: 13.5pt; color: #0f172a; border-bottom: 1px solid #cbd5e1; margin-top: 18px; page-break-after: avoid; }
h3 { font-size: 11.5pt; color: #334155; margin-bottom: 4px; page-break-after: avoid; }
code { font: 9pt Consolas, 'Cascadia Mono', monospace; background: #f1f5f9; padding: 0 2px; border-radius: 3px; }
pre { background: #0f172a; color: #e2e8f0; padding: 8px 10px; border-radius: 6px; overflow-wrap: anywhere;
      white-space: pre-wrap; page-break-inside: avoid; font-size: 8.4pt; line-height: 1.35; }
pre code { background: none; color: inherit; padding: 0; font-size: inherit; }
blockquote { margin: 8px 0; padding: 6px 10px; border-left: 4px solid #94a3b8; background: #f8fafc; }
blockquote.essence { border-color: #ca8a04; background: #fefce8; }
blockquote.standard { border-color: #6366f1; background: #eef2ff; }
blockquote.trap, blockquote.ub { border-color: #dc2626; background: #fef2f2; }
.label { font-weight: 700; text-transform: uppercase; font-size: 8pt; letter-spacing: .06em; color: #64748b; }
table { border-collapse: collapse; font-size: 9pt; } td, th { border: 1px solid #cbd5e1; padding: 3px 6px; }
.footer { margin-top: 24px; font-size: 8pt; color: #94a3b8; border-top: 1px solid #e2e8f0; padding-top: 4px; }
"""


def _browser() -> str | None:
    for b in BROWSERS:
        if Path(b).exists():
            return b
        w = shutil.which(b)
        if w:
            return w
    return None


def clean_markdown(note: Note) -> str:
    body = DIRECTIVE_LINE.sub("", note.body)
    body = WIKILINK.sub(lambda m: m.group(2) or m.group(1), body)
    out, in_fence = [], False
    for ln in body.split("\n"):
        if ln.startswith("```"):
            in_fence = not in_fence
            out.append(ln)
            continue
        if not in_fence:
            m = CALLOUT.match(ln)
            if m:
                kind, title = m.group(1).lower(), m.group(2).strip()
                out += [f"<!--callout:{kind}-->", "", f"> **{title or kind.capitalize()}**", ">"]
                continue
        out.append(ln)
    return "\n".join(out)


def _fallback_html(md: str) -> str:
    """Minimal Markdown -> HTML (headings, fences, lists, quotes, paragraphs, inline code/bold)."""
    def inline(s: str) -> str:
        s = html.escape(s)
        s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
        s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
        s = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", s)
        return s
    out, lines, i = [], md.split("\n"), 0
    while i < len(lines):
        ln = lines[i]
        if ln.startswith("```"):
            j = i + 1
            while j < len(lines) and not lines[j].startswith("```"):
                j += 1
            out.append("<pre><code>" + html.escape("\n".join(lines[i + 1:j])) + "</code></pre>")
            i = j + 1
            continue
        m = re.match(r"^(#{1,4})\s+(.*)", ln)
        if m:
            n = len(m.group(1))
            out.append(f"<h{n}>{inline(m.group(2))}</h{n}>")
        elif ln.startswith(">"):
            block = []
            while i < len(lines) and lines[i].startswith(">"):
                block.append(inline(lines[i].lstrip(">").strip()))
                i += 1
            out.append("<blockquote>" + "<br>".join(block) + "</blockquote>")
            continue
        elif re.match(r"^\s*([-*]|\d+\.)\s+", ln):
            tag = "ol" if re.match(r"^\s*\d+\.", ln) else "ul"
            items = []
            while i < len(lines) and re.match(r"^\s*([-*]|\d+\.)\s+", lines[i]):
                items.append("<li>" + inline(re.sub(r"^\s*([-*]|\d+\.)\s+", "", lines[i])) + "</li>")
                i += 1
            out.append(f"<{tag}>" + "".join(items) + f"</{tag}>")
            continue
        elif ln.strip().startswith("<!--callout:"):
            out.append(ln.strip())
        elif ln.strip():
            out.append("<p>" + inline(ln) + "</p>")
        i += 1
    return "\n".join(out)


def to_html(note: Note) -> str:
    md = clean_markdown(note)
    try:
        import markdown  # type: ignore
        body = markdown.markdown(md, extensions=["fenced_code", "tables", "sane_lists"])
    except ImportError:
        body = _fallback_html(md)
    # attach callout classes: <!--callout:kind--> followed by a blockquote
    body = re.sub(r"<!--callout:([a-z-]+)-->\s*<blockquote>", r'<blockquote class="\1">', body)
    title = html.escape(note.title)
    return (f"<!doctype html><html><head><meta charset='utf-8'><title>{title}</title><style>{CSS}</style></head>"
            f"<body>{body}<div class='footer'>CPP Compendium · {html.escape(str(note.fm.get('type', '')))} card · "
            f"status {html.escape(note.status)} · updated {html.escape(str(note.fm.get('updated', '')))} · "
            f"exported from the vault (Markdown is canonical)</div></body></html>")


def export(note: Note, out_dir: Path | None = None) -> str:
    out_dir = out_dir or paths.HEADER_PDFS
    out_dir.mkdir(parents=True, exist_ok=True)
    work = paths.CACHE / "export"
    work.mkdir(parents=True, exist_ok=True)
    src = work / (note.stem + ".html")
    src.write_text(to_html(note), encoding="utf-8")
    pdf = out_dir / (note.stem + ".pdf")
    exe = _browser()
    if not exe:
        return f"html only (no Edge/Chrome found): {paths.rel(src)}"
    cmd = [exe, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", "--run-all-compositor-stages-before-draw",
           f"--print-to-pdf={pdf}", src.resolve().as_uri()]
    try:
        subprocess.run(cmd, capture_output=True, timeout=120)
    except subprocess.TimeoutExpired:
        return f"timeout exporting {note.stem}"
    return f"pdf: {paths.rel(pdf)}" if pdf.exists() else f"FAILED: {note.stem} (browser produced no file)"
