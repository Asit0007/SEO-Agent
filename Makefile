PY := python3

.PHONY: help new page lint test

help:
	@echo "make new P=<slug>          scaffold projects/<slug>/ from templates/"
	@echo "make page URL=<url>        on-page + technical snapshot of one URL (JSON=1 for JSON)"
	@echo "make lint P=<slug>         check projects/<slug>/metadata.toml against platform limits"
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

test:
	$(PY) -m unittest discover -s tests -t . -v
