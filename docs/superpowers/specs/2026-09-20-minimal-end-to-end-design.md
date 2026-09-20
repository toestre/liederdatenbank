# Design: Minimal End-to-End Liederdatenbank

Datum: 2026-09-20
Status: vom Nutzer genehmigt (Brainstorming-Session)

## Ziel

Das Repo von leeren Platzhalter-Dateien zu einem funktionierenden End-to-End-System
bringen: Daten → Validierung → statische Seite → Deployment via GitHub Pages.
Minimaler Scope, alles Weitere (Agent-Linksuche, CLI-Tools, kanonisches Lied-Modell)
wird bewusst auf später verschoben.

## Entscheidungen

| Thema | Entscheidung | Begründung |
|-------|--------------|------------|
| Site-Generator | Pure-Python-Skript (`scripts/build_site.py`), stdlib + PyYAML | Kein Node auf dem Arbeitsrechner; null/kaum Abhängigkeiten; upgrade-fähig |
| Daten | Platzhalterdaten (3 Bücher, ~6 Lieder je Buch) | Realer Import kommt später via `import_toc.py` |
| Suche | Client-side JS (~30 Zeilen) auf Basis von `songs.json` | Klein genug, kein Framework nötig |
| CI | validate → build → GitHub Pages via offizielle Actions | Push auf `main` = Deployment, kein manueller Schritt |

Einzige Abhängigkeit: **PyYAML** (lokal `pip install pyyaml`, CI ebenso).

## Komponenten

### 1. Datenmodell (vorgegeben durch README, wird jetzt befüllt)

`data/books.yaml`:

```yaml
- id: einklang
  titel: "Einklang"
  beschreibung: "Gesangbuch mit über 400 Liedern, vierstimmigem Notensatz und Gitarrengriffen"
- id: gemeindeheft
  titel: "Unser Gemeindeheft"
- id: loseblatt-2025
  titel: "Loseblattsammlung 2025"
  typ: loseblatt
```

Nur `id` + `titel` Pflicht. Neue Datei `data/songs/<id>.yaml` je Buch.

`data/songs/<buch>.yaml` (Platzhalter, ~6 Lieder pro Buch):

```yaml
- nummer: 42
  titel: "Großer Gott, wir loben dich"
  alternative_nummer: 12   # optional
  links:
    - typ: youtube         # youtube | spotify | tidal | bandcamp | andere
      url: https://...
      geprueft: true
      bemerkung: "Gute Aufnahme mit Orgel"   # optional
```

Platzhalter-Anforderungen:
- 2-3 identische Titel über Bücher hinweg (z. B. „Großer Gott, wir loben dich"
  in einklang + gemeindeheft), um „steht auch in"-Querverweise zu testen.
- Mix aus `geprueft: true/false`-Links.
- Je Lied 1-2 Links, YouTube-URLs als Beispiel-Platzhalter.

### 2. `scripts/validate.py`

Prüft (gemäß README):
- Nummern je Buch eindeutig → Fehler
- Song-Datei referenziert existierendes Buch (implizit via Dateiname) → Fehler
- URLs wohlgeformt, nur erlaubte Link-Typen → Fehler
- Duplikat-Titel innerhalb eines Buchs → Warnung

Exit-Code: != 0 bei Fehlern, 0 bei Warnungen. Läuft lokal und in CI.

### 3. `scripts/build_site.py`

- Liest `books.yaml` + alle `data/songs/*.yaml`.
- Rendert nach `_site/` (gitignored):
  - `index.html` – Buchübersicht
  - `<buch>/index.html` – Liedtabelle mit Suchfeld
  - `<buch>/<nummer>-<slug>.html` – Liedseite: Links (unverifizierte visuell
    de-emphasisiert), „Bearbeiten"-Link zur YAML-Datei in der GitHub-Weboberfläche,
    „steht auch in"-Querverweise per exaktem Titel-Matching über Bücher hinweg
- Schreibt `_site/songs.json` + ~30 Zeilen Inline-JS: Filter nach Nummer/Titel/Buch.
- HTML über f-strings/string.Template, ein kleines eingebettetes CSS.
- Ruft vor dem Bauen `validate.py` auf (Build bricht bei ungültigen Daten ab).

### 4. `.github/workflows/deploy.yml`

- PR + Push: `pip install pyyaml` → `python scripts/validate.py`
- Push auf `main`: zusätzlich `python scripts/build_site.py` →
  `actions/configure-pages`, `actions/upload-pages-artifact`, `actions/deploy-pages`
- Einmalige manuelle Nutzeraktion: Repo Settings → Pages → Source: GitHub Actions.

### 5. README-Update

- Build/Deploy-Abschnitt: Eleventy-Beispiel-Befehle → Python-Realität
- Roadmap-Häkchen anpassen (Datenmodell fertig, Rest offen)

## Fehlerbehandlung

- `validate.py` sammelt alle Fehler (nicht nur den ersten) und gibt sie mit
  Buch/Lied-Nummer aus; Build verweigert bei Fehlern den Start.
- Fehlende optionale Felder (alternative_nummer, bemerkung) sind kein Fehler.
- Ungültiges YAML: klare Fehlermeldung mit Dateiname.

## Testing

- `validate.py`: prüfbare Struktur (Funktionen statt Skript-Spaghetti), damit
  die Checks in CI iterativ laufen; ein minimaler Smoke-Check
  (`python scripts/validate.py` auf den Platzhalterdaten muss durchgehen).
- `build_site.py`: nach Build-Existenzcheck der erwarteten Dateien
  (Index, mind. eine Buchseite, mind. eine Liedseite, songs.json).
- Kein Test-Framework nötig – Exit-Codes + Build-Check genügen für diesen Scope.

## Nicht im Scope (bewusst verschoben)

- `scripts/fetch_links.py` (Agent-Linksuche, YouTube/Spotify-APIs)
- `scripts/add_link.py` (CLI/Bookmarklet)
- `scripts/import_toc.py` (echter Einklang-Import)
- Issue-Vorlage `link-vorschlagen.md` (inhaltsleer, kann bleiben oder später)
- Kanonisches Lied-Modell (Migration erst wenn Titel-Matching sich bewährt)
- iframe-Player-Einbettung (nur Links)

## Architektur-Überblick

```
data/*.yaml ──> validate.py ──> build_site.py ──> _site/ ──> GitHub Pages
                     │                                  │
                     └── CI (PR + push)                 └── CI (push auf main)
```
