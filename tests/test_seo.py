import tempfile
import tomllib
import unittest
from pathlib import Path
from unittest import mock

from seo import __main__ as cli
from seo import lint, page

ROOT = Path(__file__).resolve().parent.parent

GOOD_HTML = """<!doctype html><html lang="en"><head>
<title>Zero-Permission Apps: How Your Phone Gets Hijacked</title>
<meta name="description" content="A plain-English story of how an app with no permissions took over a phone, and the three settings that would have stopped it.">
<meta name="viewport" content="width=device-width">
<meta property="og:title" content="x"><meta property="og:image" content="/og.png">
<link rel="canonical" href="https://example.com/post">
<link rel="alternate" hreflang="en" href="/post">
<script type="application/ld+json">{"@context":"https://schema.org","@graph":[{"@type":"Article"},{"@type":["BreadcrumbList"]}]}</script>
</head><body>
<h1>Hijacked</h1><h2>How</h2><h3>Step</h3>
<img src="a.png" alt="phone"><img src="b.png">
<a href="/about">About</a><a href="https://other.org" rel="nofollow">x</a><a href="#top">top</a>
</body></html>"""


def levels(results):
    return [r[0] for r in results]


class PageTests(unittest.TestCase):
    def test_parses_core_fields(self):
        p = page.parse_html(GOOD_HTML, "https://example.com/post")
        self.assertTrue(p.title.startswith("Zero-Permission"))
        self.assertEqual(p.lang, "en")
        self.assertEqual(p.canonical, "https://example.com/post")
        self.assertEqual(p.hreflang, {"en": "https://example.com/post"})
        self.assertEqual(p.jsonld_types, ["Article", "BreadcrumbList"])
        self.assertEqual((p.images, p.images_missing_alt), (2, 1))
        self.assertEqual((p.links_internal, p.links_external, p.links_nofollow), (1, 1, 1))
        self.assertEqual([h[0] for h in p.headings], [1, 2, 3])
        msgs = " ".join(m for _, m in p.findings)
        self.assertNotIn("noindex", msgs)
        self.assertIn("1 of 2 images have no alt", msgs)
        self.assertNotIn("error", levels(p.findings))

    def test_flags_blocking_problems(self):
        html = ('<html><head><meta name="robots" content="noindex,follow">'
                '<script type="application/ld+json">{bad json</script></head>'
                '<body><h1>a</h1><h1>b</h1><h4>skip</h4></body></html>')
        p = page.parse_html(html, "https://example.com/", {"X-Robots-Tag": "noarchive"})
        msgs = [m for _, m in p.findings]
        self.assertTrue(any("noindex" in m for m in msgs))
        self.assertTrue(any("no <title>" in m for m in msgs))
        self.assertTrue(any("no meta viewport" in m for m in msgs))
        self.assertTrue(any("2 <h1>" in m for m in msgs))
        self.assertTrue(any("h1 to h4" in m for m in msgs))
        self.assertEqual(p.jsonld_errors, 1)

    def test_x_robots_header_noindex(self):
        p = page.parse_html(GOOD_HTML, "https://example.com/post", {"X-Robots-Tag": "noindex"})
        self.assertIn("error", levels(p.findings))

    def test_canonical_elsewhere_warns(self):
        p = page.parse_html(GOOD_HTML, "https://example.com/other")
        self.assertTrue(any("canonical points elsewhere" in m for _, m in p.findings))

    def test_snapshot_reads_robots_and_sitemap(self):
        robots = "User-agent: *\nDisallow: /private\nSitemap: https://example.com/sm.xml\n"

        def fake_get(url, opener=None):
            if url.endswith("/robots.txt"):
                return 200, url, {}, robots
            return 200, url, {}, GOOD_HTML

        with mock.patch.object(page, "_get", side_effect=fake_get):
            p = page.snapshot("https://example.com/post")
        self.assertTrue(p.robots_allows)
        self.assertEqual(p.sitemaps, ["https://example.com/sm.xml"])
        md = page.to_markdown(p)
        self.assertIn("| Sitemaps | https://example.com/sm.xml |", md)
        self.assertNotIn("robots_txt", page.to_json(p))


class YouTubeLintTests(unittest.TestCase):
    DESC = "How a zero permission app took over a phone.\nThe settings that stop it.\n\n0:00 Intro\n0:45 Attack\n3:10 Fix\n\n#cybersecurity #android #privacy"

    def test_clean_video_passes(self):
        item = {"title": "Zero permission app hijacked this phone", "primary_keyword": "zero permission app",
                "description": self.DESC, "tags": ["zero permission app"], "duration_sec": 600}
        self.assertEqual(lint.lint_youtube(item), [])

    def test_chapter_rules(self):
        bad_start = self.DESC.replace("0:00 Intro", "0:05 Intro")
        self.assertTrue(any("0:00" in m for _, m in lint.lint_youtube({"title": "t" * 30, "description": bad_start})))
        too_close = "0:00 a\n0:05 b\n1:00 c"
        self.assertTrue(any("under 10s" in m for _, m in lint.lint_youtube({"title": "t" * 30, "description": too_close})))
        two = "0:00 a\n1:00 b"
        self.assertTrue(any("at least 3" in m for _, m in lint.lint_youtube({"title": "t" * 30, "description": two})))
        backwards = "0:00 a\n2:00 b\n1:00 c"
        self.assertTrue(any("not ascending" in m for _, m in lint.lint_youtube({"title": "t" * 30, "description": backwards})))
        past_end = {"title": "t" * 30, "description": "0:00 a\n1:00 b\n9:55 c", "duration_sec": 600}
        self.assertTrue(any("of the end" in m for _, m in lint.lint_youtube(past_end)))
        self.assertEqual(lint.chapters("1:02:03 long\n0:00 a"), [3723, 0])

    def test_limits(self):
        out = lint.lint_youtube({"title": "x" * 101, "description": "d" * 5001,
                                 "tags": ["t" * 100] * 5})
        msgs = " ".join(m for _, m in out)
        self.assertIn("> 100", msgs)
        self.assertIn("> 5000", msgs)
        self.assertIn("tags total 504", msgs)
        many = " ".join(f"#tag{i}" for i in range(61))
        self.assertTrue(any("ignores all" in m for _, m in lint.lint_youtube({"title": "t" * 30, "description": many})))
        self.assertIn("error", levels(lint.lint_youtube({"title": "", "description": ""})))

    def test_keyword_placement(self):
        out = lint.lint_youtube({"title": "A" * 61 + " zero permission app", "primary_keyword": "zero permission app",
                                 "description": "line one\nline two\n\n0:00 a\n1:00 b\n2:00 c"})
        msgs = " ".join(m for _, m in out)
        self.assertIn("not in the first 60", msgs)
        self.assertIn("first two lines", msgs)


class AmazonLintTests(unittest.TestCase):
    def test_clean_listing_passes(self):
        item = {"title": "The Calm Budget Workbook", "subtitle": "Track Spending in Ten Minutes a Week",
                "description": "x", "categories": ["Books > Business & Money > Personal Finance > Budgeting"],
                "keywords": ["money planner for couples", "debt payoff tracker", "expense log",
                             "savings challenge", "monthly bill organizer", "financial goals journal",
                             "frugal living guide"]}
        self.assertEqual(lint.lint_amazon(item), [])

    def test_violations(self):
        item = {"title": "Bestselling Budget Book", "subtitle": "x" * 180,
                "description": "d" * 4001, "categories": ["a", "b", "c", "d"],
                "keywords": ["free budget template", "k" * 51, "budget tracker", '"quoted", list',
                             "a", "b", "c", "d"]}
        out = lint.lint_amazon(item)
        msgs = " ".join(m for _, m in out)
        for expected in ("fewer than 200", "['bestselling']", "> 4000", "8 keyword boxes",
                         "box 2 is 51 chars", "box 1 contains ['free']", "repeats 'budget'",
                         "quotes or commas", "4 categories"):
            self.assertIn(expected, msgs)

    def test_banned_word_boundaries(self):
        self.assertEqual(lint._banned("sugar-free baking"), [])
        self.assertEqual(lint._banned("the #1 guide"), ["#1"])
        self.assertEqual(lint._banned("freedom journal"), [])

    def test_duplicate_words_across_boxes(self):
        out = lint.lint_amazon({"title": "T", "keywords": ["anxiety journal", "anxiety workbook"],
                                "categories": ["c"]})
        self.assertTrue(any("boxes 1 and 2" in m for _, m in out))


class WebsiteAndFileTests(unittest.TestCase):
    def test_website(self):
        ok = {"title": "Zero-Permission Apps: How Phones Get Hijacked", "primary_keyword": "zero-permission apps",
              "meta_description": "A plain-English story of how an app with no permissions took over a phone, and what stops it.",
              "slug": "zero-permission-apps"}
        self.assertEqual(lint.lint_website(ok), [])
        bad = lint.lint_website({"title": "x" * 70, "primary_keyword": "kw", "meta_description": "short",
                                 "slug": "Bad_Slug"})
        msgs = " ".join(m for _, m in bad)
        for expected in ("70 chars", "lacks primary keyword", "only 5 chars", "lowercase-hyphenated"):
            self.assertIn(expected, msgs)

    def test_template_is_valid_toml_and_flags_placeholders(self):
        with open(ROOT / "templates" / "metadata.toml", "rb") as f:
            data = tomllib.load(f)
        self.assertEqual(set(data), {"website", "youtube", "amazon"})
        out = lint.lint_data(data)
        self.assertTrue(any("placeholder at website.title" in m for _, _, m in out))
        self.assertEqual(lint.lint_data({})[0][0], "error")

    def test_new_scaffolds_and_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(cli, "PROJECTS", Path(tmp)):
            self.assertEqual(cli.main(["new", "demo"]), 0)
            folder = Path(tmp) / "demo"
            names = {p.name for p in folder.iterdir()}
            self.assertEqual(names, {p.name for p in (ROOT / "templates").iterdir()} | {"research"})
            self.assertNotIn("<<CREATED>>", (folder / "intake.md").read_text())
            self.assertEqual(cli.main(["new", "demo"]), 1)
            self.assertEqual(cli.main(["lint", "demo"]), 1)


if __name__ == "__main__":
    unittest.main()
