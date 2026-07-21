#!/usr/bin/env python3
"""Filter and translate the go-calendar Pokémon GO ICS feed into German.

Consumes the released ``gocal.ics`` from othyn/go-calendar, drops events
whose category tag is blocklisted, translates event titles/descriptions
into German, and writes the result to ``docs/gocal-de.ics``.

Date/time properties are never touched, so the upstream floating local
times (deliberately timezone-free, see othyn/go-calendar README) pass
through unchanged.

Usage:
    python translate.py [--in PATH_OR_URL] [--out PATH]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request
from pathlib import Path

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


def load_blocklist() -> set[str]:
    path = ROOT / "blocklist.txt"
    tags = set()
    for line in path.read_text().splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            tags.add(line.upper().strip("[]"))
    return tags


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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="src", default=UPSTREAM_ICS)
    ap.add_argument("--out", dest="out", default=ROOT / "docs" / "gocal-de.ics")
    args = ap.parse_args()

    blocklist = load_blocklist()
    phrases = load_phrases()
    species = load_species_map()

    if str(args.src).startswith(("http://", "https://")):
        ics = fetch(str(args.src))
    else:
        ics = Path(args.src).read_bytes()

    cal = Calendar.from_ical(ics)
    cal["NAME"] = cal["X-WR-CALNAME"] = "GO Kalender (DE)"
    cal["DESCRIPTION"] = cal["X-WR-CALDESC"] = (
        "Pokémon GO Events auf Deutsch, in lokaler Zeit. "
        "Gefiltert und übersetzt aus othyn/go-calendar (Daten: Leek Duck)."
    )

    kept = dropped = 0
    for event in list(cal.walk("VEVENT")):
        summary = str(event.get("SUMMARY", ""))
        match = TAG_RE.match(summary)
        tag = match.group(1) if match else ""
        if tag in blocklist:
            cal.subcomponents.remove(event)
            dropped += 1
            continue
        kept += 1
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

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(cal.to_ical())
    print(f"kept {kept}, dropped {dropped} (blocklist: {sorted(blocklist)})")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
