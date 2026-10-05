# Audit report: blogs.asitminz.com

Audited 2026-10-05. Module: Website (technical, on-page, off-page lite). Data seen: the live HTML of all 6
pages, robots.txt, HTTP behaviour, the repo source, local Lighthouse 12 (mobile emulation, lab data),
Google autocomplete, and one web search. **Not seen:** Search Console, analytics, backlinks and CrUX field
data. The PageSpeed API refused requests without a key (429).
Raw captures are in `research/` (gitignored).

## Summary
The pages are technically clean: Lighthouse SEO scores 100 on every page tested, every page returns 200,
every page has one H1 and descriptive alt text, and nothing is noindexed. Search engines have little help
finding and understanding the site, though. **There is no sitemap, no structured data, no canonicals on
the posts and no analytics, and the post titles name no searchable topic.** The one web search engine I
could query returned the GitHub repo, not the blog. The highest-leverage work is verification and
measurement (P0), then titles, meta, previews and internal links. None of it needs a redesign.

## Findings

| # | Area | Finding | Evidence | Impact | Priority |
|---|---|---|---|---|---|
| 1 | Measurement | No analytics on any page; Search Console status unknown | No gtag/Plausible/Cloudflare-insights/verification tag in any page; no access given | Nothing can be measured or diagnosed, including whether Google has indexed the posts | **P0** |
| 2 | Indexing | Blog pages absent from the one search index checked; the GitHub repo shows instead | WebSearch `blogs.asitminz.com`, 2026-10-05: top result `github.com/Asit0007/Blogs`, no blog URL | Possibly not indexed or not ranking (*requires verification* in Search Console) | **P0** |
| 3 | Crawl | No XML sitemap | `/sitemap.xml` → 404; robots.txt (Cloudflare-managed, comments only) has no `Sitemap:` line | Slower discovery of new posts; nothing to submit in Search Console | **P0** |
| 4 | Duplicates | `http://` serves the page with 200 instead of redirecting to https | `curl http://blogs.asitminz.com/` → 200, 19 KB | Two crawlable copies of every URL; split signals | P1 |
| 5 | Canonical | No `rel=canonical` on any of the 4 posts (home and about have one) | page snapshots | Combined with #4 and `/index.html` duplicates, Google picks the canonical itself | P1 |
| 6 | Titles | Post titles are hooks with no search term: "The Backtest That Lied", "Engineering for Zero", "The SDK That Vanished" | snapshots; about is 17 chars ("About — Asit Minz") | Little relevance for queries like *trading bot backtest*, *AWS free tier usage*, *Moralis alternative* | P1 |
| 7 | Meta descriptions | 3 too long (193, 239, 324 chars), 1 missing (magento) | snapshots | Truncated or rewritten snippets; the hook is lost | P1 |
| 8 | Share previews | Only crypto-dex has `og:image`; about and the other 3 posts have no Open Graph tags at all; home has OG without an image | tag grep per page | Bare link cards on LinkedIn/X, the brand's main distribution | P1 |
| 9 | Internal links | 0 links between posts; every post links only to nav pages | link grep: no `/posts/...` hrefs in any post | No topical clustering; readers and crawlers stop after one post | P1 |
| 10 | Structured data | No JSON-LD anywhere | snapshots | No BlogPosting dates or author entity for Google; weaker E-E-A-T signals | P1 |
| 11 | Speed (cloudpulse) | Lighthouse mobile: performance 70, LCP 5.7 s, CLS 0.166 | `dashboard.png` is 514 KB, 2472×1524 RGBA PNG, no `width`/`height`; est. savings 407 KiB (modern format) + 473 KiB (responsive) | Fails LCP and CLS thresholds in lab data; likely poor field data on mobile | P1 |
| 12 | Off-page | The `Asit0007/Blogs` GitHub repo has an off-brand description ("A no-nonsense stash of tech ramblings…") and no website URL | `gh repo view`, 2026-10-05 | The repo outranks the site and sends no visitors to it | P1 |
| 13 | Speed (all) | Google Fonts CSS is render-blocking | Lighthouse home: est. 1.38 s saving; LCP 3.1 s (home), 3.0 s (quantbot) | LCP just over the 2.5 s "good" line on mobile | P2 |
| 14 | Caching | `cache-control: max-age=600` on HTML and assets; Cloudflare `DYNAMIC` | response headers | Repeat visits re-download images and fonts | P2 |
| 15 | Accessibility | Colour-contrast failures (home a11y 82); links in text not distinguishable; unsized images (quantbot, cloudpulse) | Lighthouse | Accessibility, plus CLS from the unsized images | P2 |
| 16 | Headings | h2 → h4 jumps in cloudpulse ("The operational lesson…") and magento (the 6 lessons) | snapshots | Outline and accessibility; minor for ranking | P2 |
| 17 | Content | QuantBot has 3 commented-out screenshot slots (OCI console, Actions deploy, Telegram alerts) | `posts/quantbot/index.html` lines ~1311–1345 | First-hand proof is E-E-A-T; worth filling | P2 |

**Not problems:** no broken links or images (every href/src checked; the 3 missing quantbot images are
inside HTML comments); robots.txt allows everything; https works; trailing-slash URLs 301 correctly;
every page has `lang`, a viewport and one H1; all images have descriptive alt text; the posts run
2,000–5,200 words, deep enough for their topics.

## Technical checklist
- [x] robots.txt allows crawling: Cloudflare-managed file with comments only, so nothing is disallowed
- [ ] XML sitemap exists and is submitted: missing (#3)
- [x] no accidental noindex: no meta robots or X-Robots-Tag on any page
- [ ] canonicals correct: missing on 4 posts (#5)
- [ ] HTTPS everywhere: https works, but http isn't redirected (#4)
- [x] mobile-friendly: viewport set; Lighthouse SEO 100
- [ ] Core Web Vitals pass: lab LCP 3.0–5.7 s and cloudpulse CLS 0.166 fail; no field data yet
- [ ] structured data valid: none present (#10)
- [x] no broken links (404s): all internal and external hrefs and srcs return 2xx/3xx
- [x] 301s for moved pages, no chains: `/posts/quantbot` → `/posts/quantbot/` (one hop)
- [x] pagination handled: n/a (6 pages)
- [x] hreflang: n/a (English only)

## Opportunities
- **Search demand that matches posts you already have** (Google autocomplete, 2026-10-05):
  - "backtest overfitting" and "look ahead bias example" fit QuantBot's correction story.
  - "aws free tier usage alerts" fits CloudPulse.
  - "moralis alternatives" and "moralis api alternative" fit Crypto-DEX.
  - "cloud engineer to ai engineer" and "ai systems engineer roadmap" fit About and a future pillar-4 post.
- **Unclaimed queries.** Autocomplete returned nothing for "moralis to wagmi", "magento lemp stack" and
  "oracle cloud always free trading bot". The demand there is small (*requires verification*), but a
  well-titled post can own those queries.
- **The SERP for "backtest lying"** is full of generic listicles (Medium, dev.to). A real incident with
  real numbers (+90.7% → +13.7%) is a differentiated angle.

## Not checked, and why
- Indexing, impressions and queries: no Search Console access.
- Backlinks: no backlink tool access. The Search Console "Links" report can fill this in.
- Field Core Web Vitals: the site has too little traffic for CrUX, and the PageSpeed API returned a
  quota error.
