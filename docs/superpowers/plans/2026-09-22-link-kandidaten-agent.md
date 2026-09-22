# Link-Kandidaten-Agent Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Repo-Skill für opencode, der per YouTube-Websuche Link-Kandidaten für Lieder ohne geprüften Link sammelt und nach `candidates.yaml` schreibt.

**Architecture:** Eine neue Skill-Datei `.opencode/skills/link-kandidaten/SKILL.md` (oprojekt-skill, wird von opencode automatisch gefunden) beschreibt den Agent-Ablauf. Der Agent nutzt seine eigenen Tools (read/bash/webfetch), kein eigenes Python-Skript, kein API-Key. Der Platzhalter `scripts/fetch_links.py` wird gelöscht, README angepasst.

**Tech Stack:** Markdown (Skill), YAML (`candidates.yaml`), bestehendes `scripts/validate.py`.

## Global Constraints

- Agent schreibt nie in `data/songs/*.yaml` und setzt nie `geprueft: true` (Spec: „Nicht-Tun").
- Nur `youtube.com/watch`-URLs als Kandidaten (kein youtu.be, keine Shorts), max. 3 pro Lied.
- `candidates.yaml` liegt im Repo-Root und wird committet.
- Suche: Suchbegriff `"<titel> Einklang"`, Fallback `"<titel> Chor"`.
- Standard-Batch: `--anzahl 10`, aufsteigende Nummer ab `--ab-nummer 1`.
- Repo-Doku ist deutsch (README, Skill-Datei auf Deutsch, Frontmatter-Beschreibung deutsch ok).

---

### Task 1: Skill-Datei anlegen

**Files:**
- Create: `.opencode/skills/link-kandidaten/SKILL.md`

**Interfaces:**
- Produces: aufrufbarer opencode-Skill `link-kandidaten`; Ausgabedatei `candidates.yaml` (Root) mit Einträgen `{buch, nummer, titel, status, vorschlaege: [{url, suche, hinweis}]}`.

- [ ] **Step 1: SKILL.md schreiben**

```markdown
---
name: link-kandidaten
description: Sucht YouTube-Link-Kandidaten für Lieder ohne geprüften Link und schreibt sie nach candidates.yaml. Nutze wenn jemand Link-Kandidaten sucht, leere Links vorbefüllen will oder einen Agent-Durchlauf für die Liederdatenbank will ("fetch links", "Kandidaten suchen").
---

# Link-Kandidaten-Agent

Sammelt YouTube-Link-Kandidaten für Lieder ohne geprüften Link. Der Agent
entscheidet nicht – er liefert Kandidaten nach `candidates.yaml`. Das
Pflegen in `data/songs/*.yaml` und `geprueft: true` bleibt
Maintainer-Arbeit.

## Argumente

Aus dem Nutzer-Wortlaut entnehmen (alle optional):

- `--buch <id>`: Liederbuch-ID aus `data/books.yaml` (Default: alle Bücher durchgehen)
- `--anzahl N`: wie viele Lieder dieser Lauf bearbeitet (Default 10)
- `--ab-nummer N`: Nummer, ab der gesucht wird (Default 1)

## Ablauf

1. Buchliste bestimmen: `--buch` oder alle `id`s aus `data/books.yaml`.
2. Pro Buch `data/songs/<id>.yaml` laden. Kandidaten-Lieder = Einträge,
   die **keinen** Link mit `geprueft: true` haben.
3. `candidates.yaml` laden (falls Datei existiert; wenn kaputt: Nutzer
   warnen, dann frisch anlegen). Bereits gelistete Lieder (gleiches
   `buch` + `nummer`, egal welcher `status`) überspringen.
4. Batch: die ersten N Kandidaten-Lieder aufsteigender Nummer ab
   `--ab-nummer`.
5. Pro Lied YouTube-Suche mit webfetch/websearch:
   - Suchbegriff: `"<titel> Einklang"`. Wenn keine brauchbaren Treffer:
     Fallback `"<titel> Chor"`.
   - Max. 3 Kandidaten pro Lied.
   - Nur `https://www.youtube.com/watch?v=...`-URLs (kein youtu.be, keine
     Shorts, keine reinen Playlist-URLs).
   - Sucht die erste Trefferseite; auf Kanalnamen/Video-Titel achten, die
     zum Lied passen (Chor, Gesangbuch, Chorsatz) – nicht blind die Top-3.
6. Eintrag an `candidates.yaml` anhängen:

   ```yaml
   - buch: einklang
     nummer: 6
     titel: "Liedtitel wie in der songs-Datei"
     status: offen
     vorschlaege:
       - url: "https://www.youtube.com/watch?v=..."
         suche: "<nutzter Suchbegriff>"
         hinweis: "<kurze Beobachtung, z. B. Chor-Aufnahme des Lieds"
   ```

   - Keine Treffer oder Suche scheitert: Eintrag mit `vorschlaege: []`
     und `hinweis: "keine Treffer"` unter `status`-Zeile als eigenes Feld
     `hinweis: "keine Treffer"` – dann weiter mit dem nächsten Lied.
   - Die Status-Werte `offen | uebernommen | verworfen` vergibt nur der
     Maintainer beim Review; der Agent schreibt immer `offen`.
7. YAML schreiben (sauber, doppelte Anführungszeichen für Strings,
   UTF-8).
8. Selbsttest: `python3 -c "import yaml; yaml.safe_load(open('candidates.yaml'))"`.
9. `python3 scripts/validate.py` – muss 0 Fehler melden.
10. Committen: `agent: N Link-Kandidaten für <buch>`. Nicht pushen ohne
    Aufforderung.
11. Kurze Zusammenfassung an den Nutzer: wie viele Lieder, wie viele
    mit/ohne Treffer, wie viele übersprungen.

## Nicht-Tun

- Nie `data/songs/*.yaml` ändern.
- Nie `geprueft: true` setzen.
- Keine Audio-/Embed-Prüfung – Kandidaten sind unverbindliche Vorschläge.
- Kein Duplikat-Suchen für Lieder, die schon in `candidates.yaml` stehen.
```

- [ ] **Step 2: Frontmatter-Syntax prüfen**

Run: `python3 -c "import re; t=open('.opencode/skills/link-kandidaten/SKILL.md').read(); m=re.match(r'^---\n(.*?)\n---\n', t, re.S); assert m and 'name: link-kandidaten' in m.group(1) and 'description:' in m.group(1), 'frontmatter defekt'"`
Expected: kein AssertionError.

- [ ] **Step 3: Commit**

```bash
git add .opencode/skills/link-kandidaten/SKILL.md
git commit -m "feat: opencode-Skill link-kandidaten für YouTube-Kandidatensuche"
```

Hinweis für den Nutzer: Skill wird erst nach Neustart von opencode im laufenden Session-Kontext registriert (Config wird beim Start geladen).

---

### Task 2: fetch_links.py löschen, README umschreiben

**Files:**
- Delete: `scripts/fetch_links.py`
- Modify: `README.md` (Abschnitt „Agent-gestützte Linksuche (Maintainer)", Zeilen ~84-86; Struktur-Baum Zeilen ~26-28)

**Interfaces:**
- Consumes: Task-1-Skill (Referenz in README).
- Produces: keine.

- [ ] **Step 1: fetch_links.py löschen**

```bash
git rm scripts/fetch_links.py
```

- [ ] **Step 2: README-Struktur-Baum anpassen**

In `README.md` diese Zeile:

```
│   ├── fetch_links.py           # Agent: sucht Link-Kandidaten (YouTube/Spotify)
```

Zeile komplett entfernen und dafür im Strukturbaum ergänzen (nach `└── .github/`-Block, vor `scripts/`-Block einordnen – Reihenfolge alphabetisch vor `data/` nicht nötig, einfach als eigenen Zweig):

```
├── .opencode/
│   └── skills/
│       └── link-kandidaten/     # Agent-Skill: YouTube-Kandidatensuche
```

- [ ] **Step 3: README-Abschnitt „Agent-gestützte Linksuche" umschreiben**

Alten Absatz:

> `scripts/fetch_links.py --book einklang` durchsucht YouTube/Spotify-APIs nach Kandidaten für Lieder ohne geprüften Link und schreibt die Treffer nach `candidates.yaml`. **Der Agent entscheidet nicht – er liefert Kandidaten.** Jeder Kandidat wird von Hand angehört, dann erst `geprueft: true`.

ersetzen durch:

> Der Agent ist ein opencode-Skill (`.opencode/skills/link-kandidaten/`). Aufruf in opencode, z. B. »Link-Kandidaten für einklang suchen, 10 Lieder« – er durchsucht YouTube für Lieder ohne geprüften Link und schreibt die Treffer nach `candidates.yaml`. **Der Agent entscheidet nicht – er liefert Kandidaten.** Jeder Kandidat wird von Hand angehört, dann erst `geprueft: true`.

- [ ] **Step 4: Validate läuft weiterhin**

Run: `python3 scripts/validate.py`
Expected: `0 Fehler` (fetch_links.py wird von nichts importiert – vor dem Löschen prüfen: `grep -rn "fetch_links" scripts/ .github/` darf nur README-Treffer zeigen).

- [ ] **Step 5: Commit**

```bash
git add README.md scripts/fetch_links.py
git commit -m "docs: README auf link-kandidaten-Skill umgestellt, fetch_links.py entfernt"
```

---

### Task 3: Probelauf (Anzahl 3, einklang)

**Files:**
- Create: `candidates.yaml`

**Interfaces:**
- Consumes: Task-1-Skill-Ablauf, `data/songs/einklang.yaml`, `scripts/validate.py`.
- Produces: `candidates.yaml` mit 3 Einträgen (Format siehe Task 1 Step 6).

- [ ] **Step 1: Kandidaten-Lieder bestimmen**

Run: `python3 -c "import yaml; songs=yaml.safe_load(open('data/songs/einklang.yaml')); c=[s['nummer'] for s in songs if not any(l.get('geprueft') for l in s.get('links') or [])]; print(c[:5])"`
Expected: Liste aufsteigender Nummern (aktuell beginnt sie bei 5).

- [ ] **Step 2: Die ersten 3 Lieder per webfetch/websearch suchen**

Pro Lied Suchbegriff `"<titel> Einklang"`, Fallback `"<titel> Chor"`, max. 3 `youtube.com/watch`-URLs. Treffer notieren.

- [ ] **Step 3: candidates.yaml schreiben**

Drei Einträge nach dem Format aus Task 1 Step 6 (`status: offen`).

- [ ] **Step 4: Selbsttests**

Run: `python3 -c "import yaml; d=yaml.safe_load(open('candidates.yaml')); assert len(d)==3 and all(e['status']=='offen' for e in d)"`
Expected: kein AssertionError.
Run: `python3 scripts/validate.py`
Expected: `0 Fehler`.

- [ ] **Step 5: Commit**

```bash
git add candidates.yaml
git commit -m "agent: 3 Link-Kandidaten für einklang (Probelauf)"
```

- [ ] **Step 6: Nutzer Ergebnis zeigen**

Kurze Tabelle: Nr., Titel, Anzahl Vorschläge. Nutzer hört die Kandidaten an; Übernahme in `data/songs/einklang.yaml` (inkl. `status: uebernommen` in candidates.yaml) folgt auf Zuruf – nicht automatisch.
