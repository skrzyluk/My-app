"""Render chat text (markdown-ish) to safe HTML for QLabel bubbles.

Obsluguje:
- escaping HTML (bezpieczenstwo),
- klikalne URL-e (http/https, youtu.be, www),
- klikalne tytuly filmow -> link do YouTube (mapowanie title->url z kontekstu),
- podzbior Markdown: **pogrubienie**, *kursywa* / _kursywa_, `kod`,
  listy punktowane (-, *, •) i numerowane (1. 2. ...),
- lamanie linii (\\n -> <br>).

Uzycie:
    html = to_html(reply_text, title_urls={"Tytul filmu": "https://youtu.be/ID"})
    label.setTextFormat(Qt.TextFormat.RichText)
    label.setText(html)
"""

from __future__ import annotations

import html as _html
import re

# URL: http(s)://... albo www.... albo youtu.be/... (do bialego znaku / nawiasu)
_URL_RE = re.compile(
    r"""(?<![\w@/])(
        (?:https?://|www\.)[^\s<>()]+[^\s<>().,!?;:'"]   # zwykly URL
        |
        youtu\.be/[^\s<>()]+                             # short YouTube
    )""",
    re.VERBOSE | re.IGNORECASE,
)

# Token chroniacy fragment przed dalszym formatowaniem (kod, gotowe <a>)
_TOKEN = "\x00{}\x00"

_BULLET_RE = re.compile(r"^\s*[-*•]\s+(.*)$")
_NUMBER_RE = re.compile(r"^\s*\d+[.)]\s+(.*)$")


def _linkify_urls(text: str, protected: list[str]) -> str:
    def repl(m: re.Match) -> str:
        raw = m.group(1)
        href = raw if raw.lower().startswith("http") else "https://" + raw
        anchor = f'<a href="{_html.escape(href, quote=True)}">{raw}</a>'
        protected.append(anchor)
        return _TOKEN.format(len(protected) - 1)
    return _URL_RE.sub(repl, text)


def _linkify_titles(text: str, title_urls: dict[str, str], protected: list[str]) -> str:
    # Dluzsze tytuly najpierw, by nie linkowac fragmentow
    for title in sorted(title_urls, key=len, reverse=True):
        if not title or len(title.strip()) < 4:
            continue
        url = title_urls[title]
        escaped_title = _html.escape(title)
        pattern = re.compile(re.escape(escaped_title))

        def repl(m: re.Match, _url=url) -> str:
            anchor = (
                f'<a href="{_html.escape(_url, quote=True)}">{m.group(0)}</a>'
            )
            protected.append(anchor)
            return _TOKEN.format(len(protected) - 1)

        # tylko pierwsze wystapienie kazdego tytulu
        text = pattern.sub(repl, text, count=1)
    return text


def _inline(text: str, title_urls: dict[str, str] | None, protected: list[str]) -> str:
    # 1) kod `...` -> chroniony token (nie formatujemy w srodku)
    def code_repl(m: re.Match) -> str:
        protected.append(f"<code>{m.group(1)}</code>")
        return _TOKEN.format(len(protected) - 1)
    text = re.sub(r"`([^`]+)`", code_repl, text)

    # 2) linki URL (przed tytulami)
    text = _linkify_urls(text, protected)

    # 3) klikalne tytuly filmow
    if title_urls:
        text = _linkify_titles(text, title_urls, protected)

    # 4) pogrubienie **...**
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    # 5) kursywa *...* oraz _..._ (bez zjadania ** i srodka slow)
    text = re.sub(r"(?<!\*)\*(?!\s)(.+?)(?<!\s)\*(?!\*)", r"<i>\1</i>", text)
    text = re.sub(r"(?<![\w_])_(?!\s)(.+?)(?<!\s)_(?![\w_])", r"<i>\1</i>", text)

    return text


def _restore(text: str, protected: list[str]) -> str:
    for i, frag in enumerate(protected):
        text = text.replace(_TOKEN.format(i), frag)
    return text


def to_html(text: str, title_urls: dict[str, str] | None = None) -> str:
    """Zamien tekst (markdown-ish) na bezpieczny HTML dla QLabel."""
    if not text:
        return ""

    protected: list[str] = []
    escaped = _html.escape(text)

    # Budujemy bloki: kazdy blok to ("text", linia) albo ("list", html_listy)
    blocks: list[tuple[str, str]] = []
    list_buf: list[str] = []
    list_tag: str | None = None

    def flush_list():
        nonlocal list_tag
        if list_buf and list_tag:
            items = "".join(f"<li>{li}</li>" for li in list_buf)
            blocks.append(
                ("list", f"<{list_tag} style='margin:2px 0 2px 16px;'>{items}</{list_tag}>")
            )
        list_buf.clear()
        list_tag = None

    for line in escaped.split("\n"):
        mb = _BULLET_RE.match(line)
        mn = _NUMBER_RE.match(line)
        if mb:
            if list_tag not in (None, "ul"):
                flush_list()
            list_tag = "ul"
            list_buf.append(_inline(mb.group(1), title_urls, protected))
        elif mn:
            if list_tag not in (None, "ol"):
                flush_list()
            list_tag = "ol"
            list_buf.append(_inline(mn.group(1), title_urls, protected))
        else:
            flush_list()
            blocks.append(("text", _inline(line, title_urls, protected)))

    flush_list()

    # Sklejamy: kolejne linie tekstu <br>, listy jako osobne bloki
    parts: list[str] = []
    prev_kind: str | None = None
    for kind, content in blocks:
        if kind == "text" and prev_kind == "text":
            parts.append("<br>")
        parts.append(content)
        prev_kind = kind

    return _restore("".join(parts), protected)
