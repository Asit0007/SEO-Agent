# Action plan: blogs.asitminz.com

Created 2026-10-05. Impact and effort are estimates. Nothing here guarantees rankings or traffic.
Every change below is to the `Asit0007/Blogs` repo or to Cloudflare. Pushing to `main` deploys.
Leave the "$0/month" correction in `posts/quantbot/` alone (`Blogs/CLAUDE.md`).

## Prioritised tasks

| # | Priority | Task | Finding | Expected impact | Confidence | Effort | Owner | How |
|---|---|---|---|---|---|---|---|---|
| 1 | P0 | Verify a **Domain property** for `asitminz.com` in Search Console | 1, 2 | Lets you see indexing and queries at all | high | S | Asit | search.google.com/search-console → Add property → Domain → add the TXT record in Cloudflare DNS → Verify |
| 2 | P0 | Add `sitemap.xml` (6 URLs with `lastmod`) and a `robots.txt` with a `Sitemap:` line; submit the sitemap | 3 | Faster discovery of each new post | high | S | Claude can draft | Static file at the repo root; Cloudflare's managed robots.txt merges with yours, so check the live file after deploy |
| 3 | P0 | Request indexing for all 6 URLs; read the Pages report | 2 | Confirms or fixes the "not in index" finding | med | S | Asit | Search Console → URL Inspection → Request indexing |
| 4 | P0 | Add Cloudflare Web Analytics (free, cookie-less, no consent banner) | 1 | Visits, referrers and real-user CWV | high | S | Asit | Cloudflare → Analytics & Logs → Web Analytics → enable for the zone (no code change when proxied) |
| 5 | P1 | Redirect http → https | 4 | One canonical version per URL | high | S | Asit | Cloudflare → SSL/TLS → Edge Certificates → Always Use HTTPS |
| 6 | P1 | Add `<link rel="canonical">` to the 4 posts | 5 | Consolidates signals | high | S | Claude can apply | One line in each post's `<head>` |
| 7 | P1 | Apply the titles and meta descriptions in `metadata.toml` (lint clean) | 6, 7 | Relevance for real queries and better snippet CTR | med | S | Claude can apply; Asit approves wording | Edit `<title>` and `<meta name="description">` only; the H1s stay |
| 8 | P1 | Open Graph and Twitter tags on every page, plus a per-post 1200×630 image from `assets/og/template.html` | 8 | Proper cards on LinkedIn/X | high | M | Claude drafts, Asit screenshots the images | Copy crypto-dex's tag block; also closes the BRAND.md `og-default.png` TODO |
| 9 | P1 | BlogPosting JSON-LD on posts (headline, datePublished from `<time>`, author Person with `sameAs`: GitHub, LinkedIn, asitminz.com); WebSite + Person on home | 10 | Clear dates and author entity; E-E-A-T | med | S | Claude can apply | One `<script type="application/ld+json">` per page; check in the Rich Results Test |
| 10 | P1 | "Read next" links between posts, plus in-body links where the topics touch (QuantBot ↔ CloudPulse on $0 infra, Crypto-DEX ↔ QuantBot on trusting your own numbers) | 9 | Readers and crawlers go deeper | med | S | Claude can draft | Two links per post, with descriptive anchors |
| 11 | P1 | Convert the CloudPulse `dashboard.png` (514 KB) to WebP at ~1400 px, and add `width`/`height` to every `<img>` | 11, 15 | Cloudpulse LCP and CLS into the "good" range (est.) | med | S | Claude can apply | `cwebp -q 80 -resize 1400 0`; keep the PNG as a fallback only if needed |
| 12 | P1 | Fix the `Asit0007/Blogs` repo description and set its website to `https://blogs.asitminz.com` | 12 | The repo sends visitors to the site | med | S | Claude can apply | `gh repo edit Asit0007/Blogs --description "…" --homepage https://blogs.asitminz.com` |
| 13 | P2 | Make Google Fonts non-blocking (preload + `display=swap`, fewer weights) or self-host them | 13 | ~0.5–1.4 s off home LCP on mobile (Lighthouse est.) | med | M | Claude can apply | Self-hosting also removes a third-party request |
| 14 | P2 | Cloudflare cache rule: `/assets/*` Edge and Browser TTL 1 month | 14 | Faster repeat visits | med | S | Asit | Rules → Cache Rules |
| 15 | P2 | Fix contrast tokens, underline links in text, and fix the h2 → h4 jumps | 15, 16 | Accessibility score ≥ 90 | med | S | Claude can apply | Check against `tokens.css`; BRAND.md colours stay |
| 16 | P2 | Fill the 3 QuantBot screenshot slots | 17 | First-hand proof (E-E-A-T) | low | S | Asit | Drop the files at the paths in the comments and uncomment |

## 7-day plan (quick wins)
- [ ] #1 Search Console Domain property (15 min)
- [ ] #4 Cloudflare Web Analytics, #5 Always Use HTTPS (10 min)
- [ ] #2 sitemap + robots.txt, #6 canonicals, #7 titles and meta. One commit, which Claude can prepare for review
- [ ] #3 Submit the sitemap and request indexing
- [ ] #12 Repo description and homepage

## 30-day plan
- [ ] #8 OG images and tags; #9 JSON-LD; #10 internal links; #11 image fixes
- [ ] Read the Search Console Pages and Performance reports. Note the queries each post shows for, and
      adjust titles only where a post is getting impressions with a low CTR
- [ ] Share each post again on LinkedIn/X once previews work (distribution is the main source of links)

## 90-day plan
- [ ] #13–#16 performance and accessibility
- [ ] Write one pillar-2 or pillar-4 post aimed at a gap from `keyword_strategy.csv` (e.g. *cloud engineer
      to AI engineer* told through your own arc, or *Moralis alternatives* from experience). Write a
      content brief first
- [ ] Earn links: submit the QuantBot and Crypto-DEX posts where those communities read (relevant
      subreddits, Hacker News "Show HN" for the repos, the wagmi/viem discussions). Answer real questions
      with a link only where the post answers them
- [ ] Re-run this audit (`make page` on every URL, Lighthouse) and compare with the KPI baselines
