"""Command line: python -m seo {new,page,lint}

  new <slug>           scaffold projects/<slug>/ from templates/
  page <url> [--json]  on-page + technical snapshot of one URL
  lint <slug|file>     check a project's metadata.toml; exit 1 on any error
"""

import argparse
import shutil
import sys
from datetime import date
from pathlib import Path

from . import lint, page

ROOT = Path(__file__).resolve().parent.parent
PROJECTS = ROOT / "projects"
TEMPLATES = ROOT / "templates"


def cmd_new(args) -> int:
    folder = PROJECTS / args.slug
    if folder.exists():
        print(f"{folder} already exists; not touching it", file=sys.stderr)
        return 1
    (folder / "research").mkdir(parents=True)
    for src in sorted(TEMPLATES.iterdir()):
        if src.is_file():
            text = src.read_text().replace("<<CREATED>>", date.today().isoformat())
            (folder / src.name).write_text(text)
    print(folder)
    return 0


def cmd_page(args) -> int:
    p = page.snapshot(args.url)
    print(page.to_json(p) if args.json else page.to_markdown(p), end="")
    return 0


def cmd_lint(args) -> int:
    target = Path(args.target)
    path = target if target.is_file() else PROJECTS / args.target / "metadata.toml"
    if not path.exists():
        print(f"{path} not found", file=sys.stderr)
        return 2
    results = lint.lint_file(path)
    for level, where, msg in results:
        print(f"{level.upper():5} {where}: {msg}")
    errors = sum(1 for r in results if r[0] == "error")
    warns = len(results) - errors
    print(f"\n{path}: {errors} error(s), {warns} warning(s)")
    return 1 if errors else 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="python -m seo", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    n = sub.add_parser("new"); n.add_argument("slug"); n.set_defaults(fn=cmd_new)
    pg = sub.add_parser("page"); pg.add_argument("url"); pg.add_argument("--json", action="store_true")
    pg.set_defaults(fn=cmd_page)
    li = sub.add_parser("lint"); li.add_argument("target"); li.set_defaults(fn=cmd_lint)
    args = ap.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
