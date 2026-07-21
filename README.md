# pogo-cal-de

Gefilterter, deutscher Pokémon-GO-Eventkalender. Post-processing für
[othyn/go-calendar](https://github.com/othyn/go-calendar) (Daten: Leek Duck
via ScrapedDuck).

**Warum:** Der Upstream-Kalender ist alles-oder-nichts pro Kategorie und nur
auf Englisch. Neue Kategorien (hallo, `[MB]`) tauchen als *neue* Split-Kalender
auf, die man nicht abonniert hat — man verpasst sie lautlos. Dieses Repo dreht
das um: **Blocklist statt Allowlist.** Alles Neue erscheint standardmäßig;
Uninteressantes fliegt explizit raus.

## Abonnieren

```
webcal://<user>.github.io/pogo-cal-de/gocal-de.ics
```

Funktioniert in Proton Calendar, Google Calendar, Apple Calendar etc. —
öffentliche URL, kein Auth-Header im Weg.

## Wie es funktioniert

1. GitHub Action (alle 6 h) lädt das released `gocal.ics` vom Upstream
2. `translate.py` entfernt VEVENTs, deren Tag in `blocklist.txt` steht
3. Titel/Beschreibungen werden übersetzt:
   - **Spezies-Namen** (inkl. Mega-Formen) aus
     [pogo-filter-workshop](https://github.com/JesperDramsch/pogo-filter-workshop)
     `src/locales/pokemon-names.json` (live geladen, Snapshot als Fallback)
   - **Event-Vokabular** aus `phrases_de.json` (handkuratiert:
     Rampenlichtstunde, Raid-Stunde, Max-Montag, Superliga …)
4. Ergebnis landet in `docs/gocal-de.ics`, GitHub Pages serviert es

**Datums-/Zeitfelder werden nie angefasst.** Die Upstream-Floating-Local-Times
(bewusst ohne Timezone, siehe deren README) laufen byte-identisch durch —
Rampenlichtstunde bleibt 18:00, egal wo dein Kalender-Client steht.

## Anpassen

- **Kategorie ausblenden:** Tag in `blocklist.txt` eintragen (`MM`, `GBL`, …)
- **Übersetzung ergänzen/fixen:** Pattern in `phrases_de.json` — geordnete
  `[Regex, Ersetzung]`-Paare, von oben nach unten angewendet, *nach* der
  Spezies-Übersetzung
- Push auf eine der Config-Dateien triggert den Build sofort

## Bekannte Grenzen

- Redaktionelle Eventnamen ("Ozone Ascent", "Arctic Embers") haben keine
  offizielle deutsche Quelle in den Leek-Duck-Daten und bleiben Englisch.
  Wer mag, ergänzt Einzelfälle in `phrases_de.json`.
- Das Phrasen-Vokabular ist handkuratiert und best-effort an Niantics
  deutschen Begriffen orientiert — Korrekturen willkommen.

## Setup (einmalig)

1. Repo anlegen, Dateien pushen
2. Settings → Pages → Source: `main` branch, `/docs` folder
3. Action einmal manuell laufen lassen (`workflow_dispatch`)

## Credits

- Events: [Leek Duck](https://leekduck.com/events/) via
  [bigfoott/ScrapedDuck](https://github.com/bigfoott/ScrapedDuck)
- ICS-Generierung & Timezone-Handling: [othyn/go-calendar](https://github.com/othyn/go-calendar) (MIT)
- Deutsche Namen: Community-Sheet via pogo-filter-workshop

Lizenz: MIT. Pokémon © Nintendo/Creatures/GAME FREAK; keine Affiliation.
