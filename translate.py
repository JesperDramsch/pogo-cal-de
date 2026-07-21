#!/usr/bin/env python3
"""Filter and translate the go-calendar Pokémon GO ICS feed into German.

Consumes the released ``gocal.ics`` from othyn/go-calendar, translates
event titles/descriptions into German once, then emits one .ics per feed
defined in ``feeds.yaml`` — each with its own blocklist of category tags.

Date/time properties are never touched, so the upstream floating local
times (deliberately timezone-free, see othyn/go-calendar README) pass
through unchanged.

Usage:
    python translate.py [--in PATH_OR_URL] [--out-dir PATH] [--feed KEY ...]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request
from pathlib import Path

import yaml
from icalendar import Calendar

UPSTREAM_ICS = (
    "https://github.com/othyn/go-calendar/releases/latest/download/gocal.ics"
)
POKEMON_NAMES = (
    "https://raw.githubusercontent.com/JesperDramsch/pogo-filter-workshop"
    "/main/src/locales/pokemon-names.json"
)
ROOT = Path(__file__).parent
TAG_RE = re.compile(r"^\[([A-Z]+)\]\s*")


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "pogo-cal-de"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read()


def load_feeds() -> list[dict]:
    raw = yaml.safe_load((ROOT / "feeds.yaml").read_text())
    entries = (raw or {}).get("feeds") or {}
    if not entries:
        raise SystemExit("feeds.yaml: no feeds defined")
    feeds, files = [], set()
    for key, cfg in entries.items():
        cfg = cfg or {}
        fname = cfg.get("file", f"gocal-de-{key}.ics")
        if fname in files:
            raise SystemExit(f"feeds.yaml: duplicate output file {fname!r}")
        files.add(fname)
        feeds.append(
            {
                "key": key,
                "name": cfg.get("name", f"GO Kalender (DE) – {key}"),
                "description": str(cfg.get("description", "")).strip(),
                "file": fname,
                "blocklist": {
                    str(tag).upper().strip("[]")
                    for tag in cfg.get("blocklist") or []
                },
            }
        )
    return feeds


def load_species_map() -> list[tuple[str, str]]:
    """EN -> DE species names, longest first so multi-word names win."""
    try:
        raw = json.loads(fetch(POKEMON_NAMES))
    except OSError as exc:  # network hiccup: fall back to vendored snapshot
        print(f"warn: live fetch failed ({exc}), using snapshot", file=sys.stderr)
        raw = json.loads((ROOT / "snapshots" / "pokemon-names.json").read_text())
    pairs = [
        (entry["en"], entry["de"])
        for entry in raw.values()
        if entry.get("en") and entry.get("de") and entry["en"] != entry["de"]
    ]
    pairs.sort(key=lambda p: len(p[0]), reverse=True)
    return pairs


def load_phrases() -> list[tuple[re.Pattern[str], str]]:
    """Ordered regex -> replacement pairs from phrases_de.json."""
    raw = json.loads((ROOT / "phrases_de.json").read_text())
    return [(re.compile(pat), repl) for pat, repl in raw["patterns"]]


def translate_text(
    text: str,
    phrases: list[tuple[re.Pattern[str], str]],
    species: list[tuple[str, str]],
) -> str:
    # Species first: phrase patterns may hyphenate prefixes onto names
    # (Mega Sceptile -> Mega-Gewaldro), which would defeat the boundary
    # guards below if run in the other order.
    for en, de in species:
        text = re.sub(rf"(?<![\w-]){re.escape(en)}(?![\w-])", de, text)
    for pattern, repl in phrases:
        text = pattern.sub(repl, text)
    return text


def translate_calendar(ics: bytes) -> bytes:
    """Translate every event in the upstream ICS, keeping all of them."""
    phrases = load_phrases()
    species = load_species_map()
    cal = Calendar.from_ical(ics)
    for event in cal.walk("VEVENT"):
        for key in ("SUMMARY", "DESCRIPTION"):
            if key in event:
                translated = translate_text(str(event[key]), phrases, species)
                del event[key]
                event.add(key, translated)
        for alarm in event.walk("VALARM"):
            if "DESCRIPTION" in alarm:
                translated = translate_text(
                    str(alarm["DESCRIPTION"]), phrases, species
                )
                del alarm["DESCRIPTION"]
                alarm.add("DESCRIPTION", translated)
    return cal.to_ical()


def build_feed(translated: bytes, feed: dict, out_dir: Path) -> None:
    cal = Calendar.from_ical(translated)
    cal["NAME"] = cal["X-WR-CALNAME"] = feed["name"]
    if feed["description"]:
        cal["DESCRIPTION"] = cal["X-WR-CALDESC"] = feed["description"]

    kept = dropped = 0
    for event in list(cal.walk("VEVENT")):
        summary = str(event.get("SUMMARY", ""))
        match = TAG_RE.match(summary)
        tag = match.group(1) if match else ""
        if tag in feed["blocklist"]:
            cal.subcomponents.remove(event)
            dropped += 1
        else:
            kept += 1

    out = out_dir / feed["file"]
    out.write_bytes(cal.to_ical())
    print(
        f"[{feed['key']}] kept {kept}, dropped {dropped} "
        f"(blocklist: {sorted(feed['blocklist'])}) -> {out}"
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="src", default=UPSTREAM_ICS)
    ap.add_argument("--out-dir", dest="out_dir", default=ROOT / "docs")
    ap.add_argument(
        "--feed",
        dest="only",
        action="append",
        help="build only this feed key (repeatable); default: all feeds",
    )
    args = ap.parse_args()

    feeds = load_feeds()
    if args.only:
        known = {f["key"] for f in feeds}
        unknown = set(args.only) - known
        if unknown:
            raise SystemExit(
                f"unknown feed(s) {sorted(unknown)}; defined: {sorted(known)}"
            )
        feeds = [f for f in feeds if f["key"] in args.only]

    if str(args.src).startswith(("http://", "https://")):
        ics = fetch(str(args.src))
    else:
        ics = Path(args.src).read_bytes()

    translated = translate_calendar(ics)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    for feed in feeds:
        build_feed(translated, feed, out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
