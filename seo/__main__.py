"""Command line: python -m seo {new,page,lint}

  new <slug>           scaffold projects/<slug>/ from templates/
  page <url> [--json]  on-page + technical snapshot of one URL
  lint <slug|file>     check a project's metadata.toml; exit 1 on any error
  outliers <json> [--min 2.0]
                       rank videos by views over their own channel's median (input: a list of
                       {channel,title,views,url} or the JSON of `yt-dlp --flat-playlist -J`)
  retention <csv> [--duration S] [--srt FILE]
                       hook leak, cliffs and slide from a YouTube Studio retention export
"""

import argparse
import json
import shutil
import sys
from datetime import date
from pathlib import Path

from . import lint, page, youtube

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


def cmd_outliers(args) -> int:
    data = json.loads(Path(args.file).read_text())
    if isinstance(data, dict) and "entries" in data:
        rows = youtube.rows_from_ytdlp(data)
    else:
        rows = data.get("videos", []) if isinstance(data, dict) else data
    found, thin = youtube.outliers(rows, args.min)
    if args.json:
        print(json.dumps({"outliers": found, "skipped_thin_channels": thin}, indent=1))
    else:
        print(youtube.outliers_markdown(found, thin, len(rows), args.min), end="")
    return 0


def cmd_retention(args) -> int:
    cues = youtube.load_srt(Path(args.srt)) if args.srt else None
    try:
        r = youtube.retention(youtube.load_retention_csv(Path(args.file)), args.duration, cues)
    except ValueError as e:
        print(e, file=sys.stderr)
        return 2
    print(json.dumps(r, indent=1) if args.json else youtube.retention_markdown(r), end="\n" if args.json else "")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="python -m seo", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    n = sub.add_parser("new"); n.add_argument("slug"); n.set_defaults(fn=cmd_new)
    pg = sub.add_parser("page"); pg.add_argument("url"); pg.add_argument("--json", action="store_true")
    pg.set_defaults(fn=cmd_page)
    li = sub.add_parser("lint"); li.add_argument("target"); li.set_defaults(fn=cmd_lint)
    ou = sub.add_parser("outliers"); ou.add_argument("file"); ou.add_argument("--min", type=float, default=2.0)
    ou.add_argument("--json", action="store_true"); ou.set_defaults(fn=cmd_outliers)
    re_ = sub.add_parser("retention"); re_.add_argument("file"); re_.add_argument("--duration", type=float)
    re_.add_argument("--srt"); re_.add_argument("--json", action="store_true"); re_.set_defaults(fn=cmd_retention)
    args = ap.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
