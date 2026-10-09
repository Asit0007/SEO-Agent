PY := python3

.PHONY: help new page lint outliers retention test

help:
	@echo "make new P=<slug>          scaffold projects/<slug>/ from templates/"
	@echo "make page URL=<url>        on-page + technical snapshot of one URL (JSON=1 for JSON)"
	@echo "make lint P=<slug>         check projects/<slug>/metadata.toml against platform limits"
	@echo "make outliers F=<json>     niche outliers: views over each channel's own median (MIN=2.0)"
	@echo "make retention F=<csv> DUR=<sec> [SRT=<file>]   hook leak, cliffs, slide from a Studio export"
	@echo "make test                  run the unit tests (no network)"

new:
	@test -n "$(P)" || (echo "usage: make new P=<slug>" && exit 2)
	$(PY) -m seo new $(P)

page:
	@test -n "$(URL)" || (echo "usage: make page URL=https://..." && exit 2)
	$(PY) -m seo page "$(URL)" $(if $(JSON),--json,)

lint:
	@test -n "$(P)" || (echo "usage: make lint P=<slug>" && exit 2)
	$(PY) -m seo lint $(P)

outliers:
	@test -n "$(F)" || (echo "usage: make outliers F=collected.json [MIN=2.0]" && exit 2)
	$(PY) -m seo outliers "$(F)" --min $(or $(MIN),2.0)

retention:
	@test -n "$(F)" || (echo "usage: make retention F=retention.csv DUR=<seconds> [SRT=captions.srt]" && exit 2)
	$(PY) -m seo retention "$(F)" $(if $(DUR),--duration $(DUR),) $(if $(SRT),--srt "$(SRT)",)

test:
	$(PY) -m unittest discover -s tests -t . -v
