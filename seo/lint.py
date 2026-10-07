"""Check a project's metadata.toml against platform limits.

The limits are the "Platform facts" table in CLAUDE.md, dated there; change both together.
'error' = the platform rejects it or silently drops the feature; 'warn' = likely to hurt.
"""

import re
import tomllib
from pathlib import Path

# Websites (Google truncates by width; these are working targets, not limits)
TITLE_MAX, TITLE_MIN = 60, 20
META_MAX, META_MIN = 160, 70

# YouTube
YT_TITLE_MAX, YT_TITLE_VISIBLE = 100, 60
YT_DESC_MAX = 5000
YT_TAGS_MAX_CHARS = 500
YT_HASHTAGS_IGNORED_ABOVE = 60
YT_CHAPTER_MIN_COUNT, YT_CHAPTER_MIN_SEC = 3, 10

# Amazon KDP
KDP_TITLE_SUBTITLE_MAX = 199  # "fewer than 200 characters" combined
KDP_DESC_MAX = 4000
KDP_KEYWORD_BOXES, KDP_KEYWORD_MAX = 7, 50
KDP_CATEGORIES_MAX = 3
KDP_BANNED = ["free", "bestseller", "best seller", "bestselling", "best-selling", "#1",
              "kindle unlimited", "on sale", "new release", "discount"]

PLACEHOLDER = "<<FILL"  # also matches <<FILL: hint>>
TIMESTAMP = re.compile(r"^\s*((?:\d{1,2}:)?\d{1,2}:\d{2})\b")
HASHTAG = re.compile(r"(?<![\w&])#(\w+)")
SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def _seconds(ts: str) -> int:
    total = 0
    for part in ts.split(":"):
        total = total * 60 + int(part)
    return total


# Small words Amazon ignores in matching; repeating them across fields costs nothing worth flagging.
STOPWORDS = {"for", "and", "the", "with", "from", "your", "you", "are", "into", "its"}
# Category levels that say nothing about the subject.
GENERIC_LEVELS = {"nonfiction", "fiction", "books", "kindle store", "kindle ebooks"}


def _words(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9']+", text.lower()) if len(w) > 2 and w not in STOPWORDS}


def _category_words(cats: list[str]) -> set[str]:
    """Words of each category's most specific named level (KDP: don't repeat category words)."""
    out = set()
    for cat in cats:
        levels = [lv.strip() for lv in re.split(r"[›>]", cat) if lv.strip()]
        named = [lv for lv in levels if lv.lower() not in GENERIC_LEVELS]
        if named:
            out |= _words(named[-1])
    return out


def _has_keyword(text: str, keyword: str) -> bool:
    return bool(keyword) and keyword.lower() in text.lower()


def _banned(text: str) -> list[str]:
    low = text.lower()
    return [b for b in KDP_BANNED if re.search(rf"(?<![\w-]){re.escape(b)}(?![\w-])", low)]


def lint_website(item: dict) -> list[tuple[str, str]]:
    out = []
    title, meta = item.get("title", ""), item.get("meta_description", "")
    kw = item.get("primary_keyword", "")
    if not title:
        out.append(("error", "title is empty"))
    elif len(title) > TITLE_MAX:
        out.append(("warn", f"title {len(title)} chars > ~{TITLE_MAX} (truncates)"))
    elif len(title) < TITLE_MIN:
        out.append(("warn", f"title only {len(title)} chars"))
    if kw and title and not _has_keyword(title, kw):
        out.append(("warn", f"title lacks primary keyword '{kw}'"))
    if not meta:
        out.append(("warn", "meta_description is empty"))
    elif len(meta) > META_MAX:
        out.append(("warn", f"meta_description {len(meta)} chars > ~{META_MAX} (truncates)"))
    elif len(meta) < META_MIN:
        out.append(("warn", f"meta_description only {len(meta)} chars"))
    slug = item.get("slug")
    if slug and not SLUG.match(slug):
        out.append(("warn", f"slug '{slug}' is not lowercase-hyphenated"))
    return out


def chapters(description: str) -> list[int]:
    return [_seconds(m.group(1)) for line in description.splitlines() if (m := TIMESTAMP.match(line))]


def lint_youtube(item: dict) -> list[tuple[str, str]]:
    out = []
    title, desc = item.get("title", ""), item.get("description", "")
    kw = item.get("primary_keyword", "")
    if not title:
        out.append(("error", "title is empty"))
    elif len(title) > YT_TITLE_MAX:
        out.append(("error", f"title {len(title)} chars > {YT_TITLE_MAX} (YouTube rejects it)"))
    elif len(title) > YT_TITLE_VISIBLE:
        out.append(("warn", f"title {len(title)} chars; the hook should sit in the first ~{YT_TITLE_VISIBLE}"))
    if kw and title and not _has_keyword(title[:YT_TITLE_VISIBLE], kw):
        out.append(("warn", f"primary keyword '{kw}' not in the first {YT_TITLE_VISIBLE} chars of the title"))
    if len(desc) > YT_DESC_MAX:
        out.append(("error", f"description {len(desc)} chars > {YT_DESC_MAX}"))
    first_lines = " ".join(desc.strip().splitlines()[:2])
    if kw and desc and not _has_keyword(first_lines, kw):
        out.append(("warn", f"primary keyword '{kw}' not in the description's first two lines"))
    tags = item.get("tags", [])
    tag_chars = sum(len(t) for t in tags) + max(len(tags) - 1, 0)  # commas count
    if tag_chars > YT_TAGS_MAX_CHARS:
        out.append(("error", f"tags total {tag_chars} chars > {YT_TAGS_MAX_CHARS}"))
    hashtags = HASHTAG.findall(desc) + HASHTAG.findall(title)
    if len(hashtags) > YT_HASHTAGS_IGNORED_ABOVE:
        out.append(("error", f"{len(hashtags)} hashtags > {YT_HASHTAGS_IGNORED_ABOVE}: YouTube ignores all of them"))
    elif len(hashtags) > 5:
        out.append(("warn", f"{len(hashtags)} hashtags; 3-5 relevant ones read better"))
    ch = chapters(desc)
    if ch:
        if ch[0] != 0:
            out.append(("error", "first chapter timestamp is not 0:00; chapters will not show"))
        if len(ch) < YT_CHAPTER_MIN_COUNT:
            out.append(("error", f"only {len(ch)} timestamps; chapters need at least {YT_CHAPTER_MIN_COUNT}"))
        for a, b in zip(ch, ch[1:]):
            if b <= a:
                out.append(("error", "chapter timestamps are not ascending"))
                break
            if b - a < YT_CHAPTER_MIN_SEC:
                out.append(("error", f"chapter at {b}s is under {YT_CHAPTER_MIN_SEC}s after the previous one"))
                break
        dur = item.get("duration_sec")
        if dur and ch[-1] > dur - YT_CHAPTER_MIN_SEC:
            out.append(("error", f"last chapter starts within {YT_CHAPTER_MIN_SEC}s of the end (or after it)"))
    else:
        out.append(("warn", "no chapters in the description"))
    thumb = item.get("thumbnail_text", "")
    if thumb and len(thumb.split()) > 5:
        out.append(("warn", f"thumbnail text is {len(thumb.split())} words; 3-5 read at phone size"))
    return out


def lint_amazon(item: dict) -> list[tuple[str, str]]:
    out = []
    title, sub = item.get("title", ""), item.get("subtitle", "")
    combined = len(title) + len(sub)
    if not title:
        out.append(("error", "title is empty"))
    if combined > KDP_TITLE_SUBTITLE_MAX:
        out.append(("error", f"title + subtitle {combined} chars; KDP needs fewer than 200"))
    for field_name, text in (("title", title), ("subtitle", sub)):
        if hits := _banned(text):
            out.append(("error", f"{field_name} contains {hits} (promotional terms are not allowed)"))
    desc = item.get("description", "")
    if len(desc) > KDP_DESC_MAX:
        out.append(("error", f"description {len(desc)} chars > {KDP_DESC_MAX}"))
    kws = item.get("keywords", [])
    if len(kws) > KDP_KEYWORD_BOXES:
        out.append(("error", f"{len(kws)} keyword boxes > {KDP_KEYWORD_BOXES}"))
    elif len([k for k in kws if k.strip()]) < KDP_KEYWORD_BOXES:
        out.append(("warn", f"{len([k for k in kws if k.strip()])} of {KDP_KEYWORD_BOXES} keyword boxes used"))
    title_words = _words(title + " " + sub)
    cat_words = _category_words(item.get("categories", []))
    seen: dict[str, int] = {}
    for i, kw in enumerate(kws, 1):
        if len(kw) > KDP_KEYWORD_MAX:
            out.append(("error", f"keyword box {i} is {len(kw)} chars > {KDP_KEYWORD_MAX}"))
        if hits := _banned(kw):
            out.append(("error", f"keyword box {i} contains {hits}"))
        if '"' in kw or "," in kw:
            out.append(("warn", f"keyword box {i} has quotes or commas; write a phrase in reader word order"))
        for w in _words(kw):
            if w in title_words:
                out.append(("warn", f"keyword box {i} repeats '{w}' from the title/subtitle"))
            elif w in cat_words:
                out.append(("warn", f"keyword box {i} repeats '{w}' from a category"))
            elif w in seen:
                out.append(("warn", f"'{w}' appears in keyword boxes {seen[w]} and {i}"))
            seen.setdefault(w, i)
    cats = item.get("categories", [])
    if len(cats) > KDP_CATEGORIES_MAX:
        out.append(("error", f"{len(cats)} categories > {KDP_CATEGORIES_MAX} per format"))
    elif not cats:
        out.append(("warn", "no categories chosen"))
    return out


CHECKS = {"website": lint_website, "youtube": lint_youtube, "amazon": lint_amazon}


def _placeholders(value, path: str) -> list[str]:
    if isinstance(value, str):
        return [path] if PLACEHOLDER in value else []
    if isinstance(value, list):
        return [p for i, v in enumerate(value) for p in _placeholders(v, f"{path}[{i}]")]
    if isinstance(value, dict):
        return [p for k, v in value.items() for p in _placeholders(v, f"{path}.{k}")]
    return []


def lint_data(data: dict) -> list[tuple[str, str, str]]:
    """(level, where, message) for every item in every [[website]] / [[youtube]] / [[amazon]] table."""
    out = []
    for kind, check in CHECKS.items():
        for i, item in enumerate(data.get(kind, [])):
            where = f"{kind}[{i}] {item.get('name') or item.get('title', '')[:40]!r}"
            for p in _placeholders(item, kind):
                out.append(("error", where, f"unfilled placeholder at {p}"))
            out += [(level, where, msg) for level, msg in check(item)]
    if not any(data.get(k) for k in CHECKS):
        out.append(("error", "file", "no [[website]], [[youtube]] or [[amazon]] entries"))
    return out


def lint_file(path: Path) -> list[tuple[str, str, str]]:
    with open(path, "rb") as f:
        return lint_data(tomllib.load(f))
