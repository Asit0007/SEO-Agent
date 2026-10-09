"""YouTube research helpers: niche outliers and audience-retention leaks.

Methods adapted from the MIT-licensed youtube-agent-skill by Jake Schincariol
(github.com/Jakeschincariol/youtube-agent-skill, commit a2feb21, read 2026-10-08); the code here is
our own.

outliers   Rank videos by views as a multiple of their OWN channel's median, so a niche is read
           by which ideas beat their channel, not by which channel is biggest. A median needs at
           least four videos per channel; thinner channels are skipped and reported.
retention  Read a YouTube Studio "Audience retention" export and name three different problems:
           the HOOK LEAK (lost in the first 30 s), CLIFFS (moments people left at) and the SLIDE
           (steady loss across the middle). With captions it quotes what was said at each cliff.
"""

import csv
import re
import statistics
from pathlib import Path

MIN_VIDEOS_PER_CHANNEL = 4
HOOK_SECONDS = 30.0
HOOK_HEALTHY, HOOK_SEVERE = 25.0, 40.0  # percentage points lost in the first 30 s
CLIFF_MIN_DROP = 1.0                    # percentage points between two samples
CLIFF_RATE_FACTOR = 3.0                 # a cliff loses viewers this many times faster than the median
END_SCREEN_SHARE = 0.05                 # the last 5% always drops (end screen); never a cliff
CLIFF_CONTEXT_SEC = 4.0


# --- outliers -------------------------------------------------------------------------------------

def rows_from_ytdlp(data: dict) -> list[dict]:
    """Rows from `yt-dlp --flat-playlist -J <channel>/videos`; entries without a view count are dropped."""
    channel = data.get("channel") or data.get("uploader") or data.get("title") or "?"
    rows = []
    for e in data.get("entries") or []:
        if not isinstance(e, dict) or e.get("view_count") is None:
            continue
        url = e.get("url") or (f"https://www.youtube.com/watch?v={e['id']}" if e.get("id") else "")
        rows.append({"channel": e.get("channel") or channel, "title": e.get("title", ""),
                     "views": int(e["view_count"]), "url": url, "duration": e.get("duration")})
    return rows


def outliers(rows: list[dict], min_multiple: float = 2.0) -> tuple[list[dict], list[tuple[str, int]]]:
    """(videos at or above min_multiple of their channel's median, best first; skipped thin channels)."""
    by_channel: dict[str, list[dict]] = {}
    for r in rows:
        by_channel.setdefault(r.get("channel") or "?", []).append(r)
    out, thin = [], []
    for channel, videos in by_channel.items():
        if len(videos) < MIN_VIDEOS_PER_CHANNEL:
            thin.append((channel, len(videos)))
            continue
        median = statistics.median(float(v.get("views") or 0) for v in videos)
        if median <= 0:
            continue
        for v in videos:
            multiple = float(v.get("views") or 0) / median
            if multiple >= min_multiple:
                out.append({"channel": channel, "title": v.get("title", ""), "views": int(v.get("views") or 0),
                            "median": int(median), "multiple": round(multiple, 2), "url": v.get("url", ""),
                            "duration": v.get("duration")})
    out.sort(key=lambda r: -r["multiple"])
    return out, thin


def outliers_markdown(found: list[dict], thin: list[tuple[str, int]], total: int, min_multiple: float) -> str:
    lines = [f"{total} videos read; outliers at {min_multiple}x their own channel's median or better.", ""]
    if found:
        lines += ["| multiple | views | channel median | channel | title |", "|---:|---:|---:|---|---|"]
        lines += [f"| {r['multiple']:.2f}x | {r['views']:,} | {r['median']:,} | {r['channel']} | {r['title']} |"
                  for r in found[:25]]
    else:
        lines.append("Nothing cleared the threshold: collect more videos per channel or lower --min.")
    if thin:
        lines += ["", f"Skipped (fewer than {MIN_VIDEOS_PER_CHANNEL} videos, so no meaningful median): "
                  + ", ".join(f"{c} ({n})" for c, n in thin)]
    return "\n".join(lines) + "\n"


# --- retention ------------------------------------------------------------------------------------

def load_retention_csv(path: Path) -> list[tuple[float, float]]:
    """(position, % still watching) from the first two numeric cells of each row; headers are skipped."""
    rows = []
    with open(path, newline="", encoding="utf-8-sig", errors="replace") as fh:
        for record in csv.reader(fh):
            nums = []
            for cell in record:
                try:
                    nums.append(float(cell.strip().replace("%", "").replace(",", "")))
                except ValueError:
                    pass
            if len(nums) >= 2:
                rows.append((nums[0], nums[1]))
    return rows


_SRT_TIME = re.compile(r"(\d+):(\d{2}):(\d{2})[,.](\d{3})\s*-->\s*(\d+):(\d{2}):(\d{2})[,.](\d{3})")


def load_srt(path: Path) -> list[tuple[float, float, str]]:
    """(start s, end s, text) per cue of an .srt or .vtt file."""
    cues, current = [], None
    for line in Path(path).read_text(encoding="utf-8", errors="replace").splitlines():
        m = _SRT_TIME.search(line)
        if m:
            g = [int(x) for x in m.groups()]
            current = [g[0] * 3600 + g[1] * 60 + g[2] + g[3] / 1000, g[4] * 3600 + g[5] * 60 + g[6] + g[7] / 1000, []]
            cues.append(current)
        elif current is not None and line.strip() and not line.strip().isdigit():
            current[2].append(line.strip())
        elif not line.strip():
            current = None
    return [(a, b, " ".join(t)) for a, b, t in cues]


def _value_at(points: list[tuple[float, float]], x: float) -> float:
    """Linear interpolation of % still watching at position x (seconds)."""
    if x <= points[0][0]:
        return points[0][1]
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        if x0 <= x <= x1:
            return y0 if x1 == x0 else y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    return points[-1][1]


def retention(rows: list[tuple[float, float]], duration_sec: float | None = None,
              cues: list[tuple[float, float, str]] | None = None) -> dict:
    """Hook leak, cliffs and slide. A 0-100 position axis is a percentage and needs duration_sec."""
    if len(rows) < 8:
        raise ValueError("need at least 8 data points from the retention export")
    rows = sorted(rows)
    percent_axis = rows[-1][0] <= 100.5
    if percent_axis and not duration_sec:
        raise ValueError("the export's position axis is a percentage: pass the video's duration in seconds")
    pts = [((x / 100.0 * duration_sec) if percent_axis else x, y) for x, y in rows]
    length = duration_sec or pts[-1][0]
    start = pts[0][1]
    hook_leak = start - _value_at(pts, min(HOOK_SECONDS, length))

    steps = [(x0, x1, y0 - y1) for (x0, y0), (x1, y1) in zip(pts, pts[1:]) if x1 > x0]
    rates = [d / (x1 - x0) for x0, x1, d in steps if d > 0]
    median_rate = statistics.median(rates) if rates else 0.0
    cliffs = []
    for x0, x1, d in steps:
        if x0 < HOOK_SECONDS or x0 >= length * (1 - END_SCREEN_SHARE) or d < CLIFF_MIN_DROP:
            continue
        if median_rate and d / (x1 - x0) < CLIFF_RATE_FACTOR * median_rate:
            continue
        said = ""
        if cues:
            said = " ".join(t for a, b, t in cues if a <= x0 + CLIFF_CONTEXT_SEC and b >= x0 - CLIFF_CONTEXT_SEC)
        cliffs.append({"at_sec": round(x0, 1), "lost": round(d, 2), "said": said[:200]})
    cliffs = sorted(cliffs, key=lambda c: -c["lost"])[:5]

    mid_from, mid_to = HOOK_SECONDS, length * (1 - END_SCREEN_SHARE)
    slide = 0.0
    if mid_to > mid_from:
        slide = (_value_at(pts, mid_from) - _value_at(pts, mid_to)) / ((mid_to - mid_from) / 60.0)
    verdict = "healthy" if hook_leak < HOOK_HEALTHY else "leaking" if hook_leak < HOOK_SEVERE else "severe"
    return {"points": len(pts), "start": round(start, 2), "end": round(pts[-1][1], 2),
            "hook_leak": round(hook_leak, 2), "hook_verdict": verdict, "cliffs": cliffs,
            "slide_per_min": round(slide, 2)}


def retention_markdown(r: dict) -> str:
    lines = [f"{r['points']} points, {r['start']:.1f}% -> {r['end']:.1f}% still watching.", "",
             f"- **Hook leak:** {r['hook_leak']:.1f} points lost in the first {HOOK_SECONDS:.0f} s "
             f"({r['hook_verdict']}; under {HOOK_HEALTHY:.0f} is healthy). Fixed in the script's first 15 s, never the edit."]
    if r["cliffs"]:
        lines.append("- **Cliffs** (moments people left at):")
        for c in r["cliffs"]:
            m, s = divmod(int(c["at_sec"]), 60)
            lines.append(f"  - {m}:{s:02d}, -{c['lost']:.1f} points" + (f': "{c["said"]}"' if c["said"] else ""))
    else:
        lines.append("- **Cliffs:** none; the loss is all slide, not moments.")
    lines.append(f"- **Slide:** {r['slide_per_min']:.2f} points a minute across the middle. A steady slide is "
                 "pacing: cut the middle, do not rewrite it.")
    return "\n".join(lines) + "\n"
