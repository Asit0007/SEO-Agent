# KPI dashboard: blogs.asitminz.com

Created 2026-10-05. Review weekly for the first 30 days, then monthly.

| KPI | Source | Baseline (date) | Target (date) | Latest | Notes |
|---|---|---|---|---|---|
| Indexed pages | Search Console → Pages | unknown, no access (2026-10-05) | 6/6 (2026-11-05) | | Every new post indexed within 7 days |
| Impressions / clicks / CTR per post | Search Console → Performance | no baseline yet | trend up month over month | | Judge titles by CTR once a post has ≥100 impressions |
| Queries per post | Search Console → Performance → Queries | none | ≥1 relevant query per post (2026-12-31) | | Confirms the title/keyword mapping |
| Visits and referrers | Cloudflare Web Analytics | none installed (2026-10-05) | baseline after 30 days | | LinkedIn/X vs search vs GitHub |
| Lighthouse mobile performance | `npx lighthouse` | home 87, quantbot 93, cloudpulse 70 (2026-10-05) | all ≥ 90 | | Lab data |
| LCP / CLS (lab) | Lighthouse | home 3.1 s / 0; quantbot 3.0 s / 0.001; cloudpulse 5.7 s / 0.166 | ≤ 2.5 s / ≤ 0.1 | | Switch to field data when Cloudflare RUM has volume |
| Accessibility | Lighthouse | home 82, quantbot 93, cloudpulse 90 | all ≥ 90 | | |
| Referring domains | Search Console → Links | unknown | +5 relevant in 90 days | | Earned only |
| Pages with OG image / JSON-LD / canonical | `make page` | 1 / 0 / 2 of 6 | 6 / 6 / 6 | | |

## Log
| Date | What changed | What moved |
|---|---|---|
| 2026-10-05 | Audit | — |
| 2026-10-05 | Blogs `452e3db` on branch `seo/7-day-fixes` (awaiting merge): sitemap, robots.txt, canonicals, titles and meta (#2, #6, #7). Repo description and homepage set (#12) | — |
