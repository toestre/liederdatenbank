# Liederdatenbank

Eine datengetriebene Sammlung von Liedquellen für unsere Gemeindecliederbücher (aktuell: **Einklang**, Gemeindeheft, Loseblattsammlung). Aus den Daten hier wird automatisch die öffentliche Liederseite generiert.

---

## Idee

- **Git-Repo = Single Source of Truth.** Alles – Liednummern, Titel, Links – liegt versioniert in diesem Repo.
- **Die Webseite ist nur ein Ausdruck der Daten.** Sie wird bei jedem Merge automatisch neu gebaut und deployed.
- **Jeder kann beitragen**, ohne Git-Kenntnisse: über Editier-Links auf der Seite, Issue-Vorlagen oder ein Bookmarklet.

## Repository-Struktur

```
.
├── data/
│   ├── books.yaml              # Liederbücher (Metadaten)
│   └── songs/
│       ├── einklang.yaml       # Lieder des Einklang-Liederbuchs
│       ├── gemeindeheft.yaml   # Lieder des Gemeindehefts
│       └── loseblatt-2025.yaml # Loseblattsammlung
├── scripts/
│   ├── import_toc.py           # Einmaliger Import: Inhaltsverzeichnis → YAML
│   ├── fetch_links.py          # Agent: sucht Link-Kandidaten (YouTube/Spotify)
│   ├── add_link.py             # Ergänzt einen Link zu einem Lied (für Bookmarklet/CLI)
│   └── validate.py             # Prüft Datenintegrität (läuft auch in CI)
├── site/                       # Statischer Seitengenerator (Hugo/Eleventy/Astro)
└── .github/
    ├── workflows/deploy.yml    # CI: validieren → bauen → deployen
    └── ISSUE_TEMPLATE/
        └── link-vorschlagen.md # Für Beiträge ohne Git-Zugang
```

## Datenmodell

### `data/books.yaml` – die Liederbücher

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

Nur `id` und `titel` sind Pflichtfelder – alles andere ist optional. Ein neues Liederbuch anlegen = ein neuer Eintrag hier plus eine neue Datei unter `data/songs/`.

### `data/songs/<buch-id>.yaml` – die Lieder

```yaml
- nummer: 42
  titel: "Großer Gott, wir loben dich"
  alternative_nummer: 12        # optional: Nummer im Gemeindeheft
  links:
    - typ: youtube              # youtube | spotify | tidal | bandcamp | andere
      url: https://www.youtube.com/watch?v=...
      geprueft: true            # wurde der Link von Hand gehört und freigegeben?
      bemerkung: "Gute Aufnahme mit Orgel"
```

**Regeln:**

- Eine Datei pro Liederbuch, benannt nach der `id` des Buchs.
- `nummer` ist nur im Kontext des jeweiligen Buchs eindeutig. Bei der Loseblattsammlung: fortlaufende Eingangsnummer.
- Mehrere Links pro Lied sind erlaubt und erwünscht (YouTube fürs Ansehen, Spotify fürs Hören, …).
- Links werden erst mit `geprueft: true` auf der öffentlichen Seite prominent angezeigt.

## Mitwirken

### »Ich habe einen guten Link gefunden«

Drei Wege – nimm den, der dir am leichtesten fällt:

1. **Issue-Vorlage:** [Neues Issue »Link vorschlagen«](../../issues/new?template=link-vorschlagen.md) öffnen, Liednummer + Link eintragen. Ein Maintainer pflegt es ein.
2. **Auf der Webseite:** Jede Liedseite hat einen »Bearbeiten«-Link, der direkt die YAML-Datei in der GitHub-Weboberfläche öffnet – ändern, PR erstellen, fertig.
3. **Bookmarklet/CLI** (für regelmäßige Beitragende): `scripts/add_link.py --book einklang --nummer 42 --url "…" ` – prüft, ergänzt und committet.

### Agent-gestützte Linksuche (Maintainer)

`scripts/fetch_links.py --book einklang` durchsucht YouTube/Spotify-APIs nach Kandidaten für Lieder ohne geprüften Link und schreibt die Treffer nach `candidates.yaml`. **Der Agent entscheidet nicht – er liefert Kandidaten.** Jeder Kandidat wird von Hand angehört, dann erst `geprueft: true`.

### Datenänderungen

Jede Änderung läuft über Pull Request (auch eigene, über die Weboberfläche). Ein Maintainer merged, CI deployed automatisch. Direkte Pushes auf `main` sind gesperrt.

## Qualitätssicherung (CI)

Bei jedem PR und Push auf `main` läuft `scripts/validate.py`:

- Nummern innerhalb eines Buchs eindeutig
- Jeder Eintrag referenziert ein existierendes Buch
- URLs wohlgeformt, nur erlaubte Link-Typen
- Kein Duplikat-Titel innerhalb eines Buchs (Warnung)

Zusätzlich prüft der Seitengenerator per Titel-Matching auf Duplikate **über Bücher hinweg** und verlinkt auf den Liedseiten: »Dieses Lied steht auch in: Gemeindeheft Nr. 12«.

## Webseite bauen & deployen

```bash
# Abhängigkeiten (Beispiel Eleventy)
npm install

# Lokal entwickeln
npm run dev

# Bauen
npm run build   # → site/_site/
```

Deployment: Bei jedem Merge auf `main` baut GitHub Actions die Seite neu und veröffentlicht sie über **GitHub Pages**. Kein Server, keine Kosten, kein manueller Schritt.

## Rechtliches

- **Liedtexte und Noten werden hier nicht veröffentlicht** – nur Metadaten (Nummer, Titel) und Links zu legalen Quellen. Veröffentliche keine kopierten Texte/Auszüge in Issues oder Kommentaren.
- Eingebettete Player (iframe) verweisen auf YouTube/Spotify-Plattformen; die Lizenzsituation regelt die jeweilige Plattform.
- Bei Unsicherheiten (z. B. Frage zur CCLI/Gema-Abrechnung) vor dem Veröffentlichen kurz mit den Verantwortlichen klären.

## Roadmap

- [x] Datenmodell für mehrere Liederbücher
- [ ] Import des Einklang-Inhaltsverzeichnisses
- [ ] Erster Agent-Durchlauf für Link-Kandidaten (Einklang)
- [ ] Gemeindeheft & Loseblattsammlung erfassen
- [ ] Suche & Filter (Nummer, Titel, Buch) auf der Seite
- [ ] Ggf. Migration auf kanonisches Lied-Modell (ein Lied, mehrere Vorkommen), wenn das Titel-Matching sich bewährt hat

---

*Fragen? Öffne ein Issue oder sprich die Verantwor­tlichen für die Liederseite an.*
