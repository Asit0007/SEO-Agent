"""One-URL on-page and technical snapshot, standard library only.

parse_html() is pure (tested without network); snapshot() fetches and adds robots.txt, sitemap and
redirect facts. Findings are evidence for the audit, not a verdict: rendering-dependent issues
(JavaScript-built content, Core Web Vitals) need the browser and PageSpeed Insights.
"""

import json
import urllib.error
import urllib.request
import urllib.robotparser
from dataclasses import asdict, dataclass, field
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

UA = "Mozilla/5.0 (compatible; SEO-Agent/1.0; owner audit)"
TIMEOUT = 20


@dataclass
class Page:
    url: str
    status: int | None = None
    final_url: str | None = None
    redirects: list[str] = field(default_factory=list)
    x_robots_tag: str | None = None
    lang: str | None = None
    title: str | None = None
    meta_description: str | None = None
    meta_robots: str | None = None
    canonical: str | None = None
    viewport: bool = False
    hreflang: dict[str, str] = field(default_factory=dict)
    headings: list[tuple[int, str]] = field(default_factory=list)
    images: int = 0
    images_missing_alt: int = 0
    links_internal: int = 0
    links_external: int = 0
    links_nofollow: int = 0
    jsonld_types: list[str] = field(default_factory=list)
    jsonld_errors: int = 0
    og: dict[str, str] = field(default_factory=dict)
    robots_txt: str | None = None
    robots_allows: bool | None = None
    sitemaps: list[str] = field(default_factory=list)
    findings: list[tuple[str, str]] = field(default_factory=list)


class _Parser(HTMLParser):
    def __init__(self, base: str):
        super().__init__(convert_charrefs=True)
        self.base = base
        self.host = urlparse(base).netloc.lower()
        self.p = Page(url=base)
        self._in_title = False
        self._heading: int | None = None
        self._text: list[str] = []
        self._jsonld: list[str] | None = None

    def handle_starttag(self, tag, attrs):
        a = {k.lower(): (v or "") for k, v in attrs}
        p = self.p
        if tag == "html" and a.get("lang"):
            p.lang = a["lang"]
        elif tag == "title" and p.title is None:
            self._in_title, self._text = True, []
        elif tag == "meta":
            name = (a.get("name") or a.get("property") or "").lower()
            content = a.get("content", "")
            if name == "description" and p.meta_description is None:
                p.meta_description = content.strip()
            elif name in ("robots", "googlebot") and content:
                p.meta_robots = ", ".join(filter(None, [p.meta_robots, content.strip()]))
            elif name == "viewport":
                p.viewport = True
            elif name.startswith("og:"):
                p.og.setdefault(name, content)
        elif tag == "link":
            rel = a.get("rel", "").lower().split()
            href = a.get("href", "")
            if "canonical" in rel and p.canonical is None:
                p.canonical = urljoin(self.base, href)
            elif "alternate" in rel and a.get("hreflang"):
                p.hreflang[a["hreflang"]] = urljoin(self.base, href)
        elif tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self._heading, self._text = int(tag[1]), []
        elif tag == "img":
            p.images += 1
            if "alt" not in a:
                p.images_missing_alt += 1
        elif tag == "a" and a.get("href"):
            href = a["href"]
            if href.startswith(("#", "mailto:", "tel:", "javascript:")):
                return
            netloc = urlparse(urljoin(self.base, href)).netloc.lower()
            if netloc == self.host:
                p.links_internal += 1
            else:
                p.links_external += 1
            if "nofollow" in a.get("rel", "").lower():
                p.links_nofollow += 1
        elif tag == "script" and a.get("type", "").lower() == "application/ld+json":
            self._jsonld = []

    def handle_endtag(self, tag):
        if tag == "title" and self._in_title:
            self.p.title = " ".join("".join(self._text).split())
            self._in_title = False
        elif self._heading and tag == f"h{self._heading}":
            self.p.headings.append((self._heading, " ".join("".join(self._text).split())))
            self._heading = None
        elif tag == "script" and self._jsonld is not None:
            self._read_jsonld("".join(self._jsonld))
            self._jsonld = None

    def handle_data(self, data):
        if self._in_title or self._heading:
            self._text.append(data)
        if self._jsonld is not None:
            self._jsonld.append(data)

    def _read_jsonld(self, raw: str):
        try:
            data = json.loads(raw)
        except ValueError:
            self.p.jsonld_errors += 1
            return
        stack = data if isinstance(data, list) else [data]
        while stack:
            node = stack.pop(0)
            if isinstance(node, dict):
                t = node.get("@type")
                for name in t if isinstance(t, list) else [t] if t else []:
                    if name not in self.p.jsonld_types:
                        self.p.jsonld_types.append(name)
                stack.extend(node.get("@graph", []))


def parse_html(html: str, url: str, headers: dict[str, str] | None = None) -> Page:
    parser = _Parser(url)
    parser.feed(html)
    parser.close()
    page = parser.p
    page.x_robots_tag = (headers or {}).get("X-Robots-Tag")
    page.findings = findings(page)
    return page


def findings(p: Page) -> list[tuple[str, str]]:
    """(level, message) pairs; level is 'error' (blocks indexing or is plainly broken) or 'warn'."""
    out = []
    robots = " ".join(filter(None, [p.meta_robots, p.x_robots_tag])).lower()
    if "noindex" in robots:
        out.append(("error", f"noindex is set ({robots}); the page will not be indexed"))
    if p.robots_allows is False:
        out.append(("error", "robots.txt disallows Googlebot from this URL"))
    if p.status and p.status >= 400:
        out.append(("error", f"HTTP {p.status}"))
    if len(p.redirects) > 1:
        out.append(("warn", f"redirect chain of {len(p.redirects)} hops; link to the final URL"))
    if not p.title:
        out.append(("error", "no <title>"))
    elif len(p.title) > 60:
        out.append(("warn", f"title is {len(p.title)} chars; Google likely truncates past ~60"))
    elif len(p.title) < 20:
        out.append(("warn", f"title is only {len(p.title)} chars"))
    if not p.meta_description:
        out.append(("warn", "no meta description (Google will pick a snippet itself)"))
    elif len(p.meta_description) > 160:
        out.append(("warn", f"meta description is {len(p.meta_description)} chars; truncates past ~160"))
    elif len(p.meta_description) < 70:
        out.append(("warn", f"meta description is only {len(p.meta_description)} chars"))
    h1 = [t for level, t in p.headings if level == 1]
    if len(h1) != 1:
        out.append(("warn", f"{len(h1)} <h1> elements; use exactly one"))
    levels = [level for level, _ in p.headings]
    for prev, cur in zip(levels, levels[1:]):
        if cur > prev + 1:
            out.append(("warn", f"heading jumps from h{prev} to h{cur}"))
            break
    target = p.final_url or p.url
    if p.canonical and p.canonical.rstrip("/") != target.rstrip("/"):
        out.append(("warn", f"canonical points elsewhere: {p.canonical}"))
    if not p.canonical:
        out.append(("warn", "no canonical link"))
    if not p.viewport:
        out.append(("error", "no meta viewport; not mobile-friendly"))
    if not p.lang:
        out.append(("warn", "no <html lang>"))
    if p.images_missing_alt:
        out.append(("warn", f"{p.images_missing_alt} of {p.images} images have no alt attribute"))
    if p.jsonld_errors:
        out.append(("error", f"{p.jsonld_errors} JSON-LD block(s) are not valid JSON"))
    if not p.jsonld_types:
        out.append(("warn", "no JSON-LD structured data"))
    if p.robots_txt is None and p.status is not None:
        out.append(("warn", "no robots.txt"))
    if p.status is not None and not p.sitemaps:
        out.append(("warn", "no sitemap found (robots.txt Sitemap: line or /sitemap.xml)"))
    if not p.og.get("og:title") or not p.og.get("og:image"):
        out.append(("warn", "missing og:title or og:image (share previews)"))
    return out


class _Recorder(urllib.request.HTTPRedirectHandler):
    def __init__(self):
        self.hops: list[str] = []

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        self.hops.append(f"{code} {newurl}")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _get(url: str, opener=None) -> tuple[int, str, dict[str, str], str]:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with (opener or urllib.request.build_opener()).open(req, timeout=TIMEOUT) as r:
            charset = r.headers.get_content_charset() or "utf-8"
            return r.status, r.geturl(), dict(r.headers), r.read().decode(charset, "replace")
    except urllib.error.HTTPError as e:
        return e.code, url, dict(e.headers or {}), ""


def snapshot(url: str) -> Page:
    rec = _Recorder()
    status, final, headers, html = _get(url, urllib.request.build_opener(rec))
    page = parse_html(html, final, headers)
    page.url, page.status, page.final_url, page.redirects = url, status, final, rec.hops

    origin = "{0.scheme}://{0.netloc}".format(urlparse(final))
    r_status, _, _, r_body = _get(origin + "/robots.txt")
    if r_status == 200:
        page.robots_txt = r_body
        rp = urllib.robotparser.RobotFileParser()
        rp.parse(r_body.splitlines())
        page.robots_allows = rp.can_fetch("Googlebot", final)
        page.sitemaps = [line.split(":", 1)[1].strip() for line in r_body.splitlines()
                         if line.lower().startswith("sitemap:")]
    if not page.sitemaps:
        s_status, _, _, _ = _get(origin + "/sitemap.xml")
        if s_status == 200:
            page.sitemaps = [origin + "/sitemap.xml"]
    page.findings = findings(page)
    return page


def to_markdown(p: Page) -> str:
    def row(k, v):
        return f"| {k} | {v if v not in (None, '', [], {}) else '—'} |"

    lines = [f"# Page snapshot: {p.url}", "", "| Field | Value |", "|---|---|",
             row("Status", p.status), row("Final URL", p.final_url),
             row("Redirects", " → ".join(p.redirects)),
             row("Title", f"{p.title} ({len(p.title)} chars)" if p.title else None),
             row("Meta description",
                 f"{p.meta_description} ({len(p.meta_description)} chars)" if p.meta_description else None),
             row("Meta robots / X-Robots-Tag", " / ".join(filter(None, [p.meta_robots, p.x_robots_tag]))),
             row("Canonical", p.canonical), row("Lang", p.lang), row("Viewport", p.viewport),
             row("hreflang", ", ".join(f"{k}={v}" for k, v in p.hreflang.items())),
             row("JSON-LD types", ", ".join(p.jsonld_types)),
             row("Images (no alt)", f"{p.images} ({p.images_missing_alt})"),
             row("Links internal / external / nofollow",
                 f"{p.links_internal} / {p.links_external} / {p.links_nofollow}"),
             row("robots.txt allows Googlebot", p.robots_allows),
             row("Sitemaps", ", ".join(p.sitemaps)), "", "## Headings", ""]
    lines += [f"{'  ' * (level - 1)}- h{level}: {text}" for level, text in p.headings] or ["(none)"]
    lines += ["", "## Findings", ""]
    lines += [f"- **{level}**: {msg}" for level, msg in p.findings] or ["- none"]
    lines += ["", "Not covered here: rendered (JavaScript) content, Core Web Vitals, backlinks. "
              "Use the browser, PageSpeed Insights and Search Console."]
    return "\n".join(lines) + "\n"


def to_json(p: Page) -> str:
    d = asdict(p)
    d.pop("robots_txt")
    return json.dumps(d, indent=2, ensure_ascii=False)
