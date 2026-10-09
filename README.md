# SEO-Agent

A Claude Code workspace that acts as an **SEO Specialist Agent** for websites, YouTube and Amazon
books. Open Claude Code in this folder: `CLAUDE.md` holds the agent's instructions, rules and
workflow. Created 2026-10-05.

```bash
make new P=<slug>            # scaffold projects/<slug>/ from templates/
make page URL=https://…      # on-page + technical snapshot of one URL (JSON=1 for JSON)
make lint P=<slug>           # check projects/<slug>/metadata.toml against platform limits
make outliers F=<json>       # YouTube niche outliers: views over each channel's own median
make retention F=<csv> DUR=<sec> [SRT=<srt>]   # hook leak, cliffs, slide from a Studio export
make test                    # 21 unit tests, no network
```

Python 3.11+ standard library only.

| Path | What |
|---|---|
| `CLAUDE.md` | Agent instructions: hard rules, tools, workflow, the three modules, dated platform facts |
| `templates/` | intake, audit report, keyword strategy, competitor analysis, content brief, metadata, action plan, KPI dashboard |
| `seo/page.py` | Fetches one URL plus its robots.txt and sitemap. Reports title, meta, robots, canonical, headings, hreflang, JSON-LD, alts, links and findings |
| `seo/lint.py` | Checks website, YouTube and KDP metadata limits: title lengths, chapters, hashtags, tag budget, title/thumbnail pairing, 7×50 keyword boxes, banned promo words, ≤3 categories |
| `seo/youtube.py` | Niche outliers (views ÷ own-channel median) and audience-retention leaks; methods adapted from the MIT [youtube-agent-skill](https://github.com/Jakeschincariol/youtube-agent-skill), code our own |
| `projects/<slug>/` | One folder per engagement; `research/` is gitignored |
| `projects/blogs-asitminz/` | Worked example: the 2026-10-05 audit of blogs.asitminz.com |

Some things are out of reach without the owner's access or paid tools: Core Web Vitals field data,
backlinks, search volumes, and Search Console, YouTube Studio or KDP data. The agent marks those as
*requires verification* rather than guessing.

## Licence

Apache License 2.0. See `LICENSE` and `NOTICE`.
