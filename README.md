# pogo-cal-de

Gefilterter, deutscher Pokémon-GO-Eventkalender. Post-processing für
[othyn/go-calendar](https://github.com/othyn/go-calendar) (Daten: Leek Duck
via ScrapedDuck).

**Warum:** Der Upstream-Kalender ist alles-oder-nichts pro Kategorie und nur
auf Englisch. Neue Kategorien (hallo, `[MB]`) tauchen als *neue* Split-Kalender
auf, die man nicht abonniert hat — man verpasst sie lautlos. Dieses Repo dreht
das um: **Blocklist statt Allowlist.** Alles Neue erscheint standardmäßig;
Uninteressantes fliegt explizit raus.

Seit dem Umstieg auf `feeds.yaml` gibt es dabei nicht nur *einen* Kalender:
jeder Eintrag in `feeds.yaml` ist ein eigener übersetzter Feed mit eigener
Blocklist.

## Abonnieren

| Feed | URL | Inhalt |
| --- | --- | --- |
| `jesper` | `webcal://<user>.github.io/pogo-cal-de/gocal-de.ics` | Kuratiert (ohne Max Monday, GBL, Season, Raids …) |
| `all` | `webcal://<user>.github.io/pogo-cal-de/gocal-de-all.ics` | Alle Events, nur übersetzt — nichts gefiltert |

Weitere Feeds landen unter `gocal-de-<key>.ics`. Funktioniert in Proton
Calendar, Google Calendar, Apple Calendar etc. — öffentliche URL, kein
Auth-Header im Weg.

## Wie es funktioniert

1. GitHub Action (alle 6 h) lädt das released `gocal.ics` vom Upstream
2. `translate.py` übersetzt einmal alles und schreibt dann pro Feed aus
   `feeds.yaml` ein eigenes `.ics`, gefiltert nach dessen Blocklist
3. Titel/Beschreibungen werden übersetzt:
   - **Spezies-Namen** (inkl. Mega-Formen) aus
     [pogo-filter-workshop](https://github.com/JesperDramsch/pogo-filter-workshop)
     `src/locales/pokemon-names.json` (live geladen, Snapshot als Fallback)
   - **Event-Vokabular** aus `phrases_de.json` (handkuratiert:
     Rampenlichtstunde, Raid-Stunde, Max-Montag, Superliga …)
4. Ergebnisse landen in `docs/`, GitHub Pages serviert sie

**Datums-/Zeitfelder werden nie angefasst.** Die Upstream-Floating-Local-Times
(bewusst ohne Timezone, siehe deren README) laufen byte-identisch durch —
Rampenlichtstunde bleibt 18:00, egal wo dein Kalender-Client steht.

## Anpassen

- **Kategorie ausblenden:** Tag in die `blocklist` des eigenen Feeds in
  `feeds.yaml` eintragen (`MM`, `GBL`, …)
- **Eigenen Feed hinzufügen:** Block in `feeds.yaml` kopieren, eindeutigen
  Key wählen, Blocklist anpassen, PR aufmachen — die Datei landet unter
  `docs/gocal-de-<key>.ics` (überschreibbar via `file:`)
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
