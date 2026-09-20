# Minimal End-to-End Liederdatenbank Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Empty repo skeleton → working end-to-end system: YAML data → validation → static site → GitHub Pages deploy.

**Architecture:** Pure-Python build pipeline. `data/*.yaml` is the single source of truth. `scripts/validate.py` checks integrity (CI gate), `scripts/build_site.py` renders `_site/` (index, book pages, song pages, JSON for client-side search). GitHub Actions runs validate on every PR/push, builds + deploys to Pages on `main`.

**Tech Stack:** Python 3.14 stdlib + PyYAML (only dependency). No Node, no JS framework, no test framework (exit codes + build existence checks per spec).

## Global Constraints

- Song YAML schema (from spec, verbatim): fields `nummer` (int, required), `titel` (str, required), `alternative_nummer` (int, optional), `links` (list, optional); link fields `typ` ∈ `youtube | spotify | tidal | bandcamp | andere`, `url` (http/https), `geprueft` (bool), `bemerkung` (optional).
- Book YAML: only `id` + `titel` mandatory, everything else optional.
- One YAML file per book under `data/songs/<book-id>.yaml`.
- Unverified links (`geprueft: false`) shown de-emphasized, never hidden.
- Duplikat-Titel within a book = warning (exit 0), all other violations = error (exit != 0).
- All UI text in German.
- No song lyrics/notes published anywhere — metadata + links only.
- `_site/` output is gitignored (already in `.gitignore`).

---

### Task 1: Placeholder data files

**Files:**
- Create: `data/books.yaml`
- Create: `data/songs/einklang.yaml`
- Create: `data/songs/gemeindeheft.yaml`
- Create: `data/songs/loseblatt-2025.yaml`

**Interfaces:**
- Produces: YAML structure consumed by `validate.py` and `build_site.py` (Tasks 2-3): `books.yaml` = list of `{id, titel, beschreibung?, typ?}`; `songs/<id>.yaml` = list of `{nummer, titel, alternative_nummer?, links: [{typ, url, geprueft, bemerkung?}]}`.
- Placeholder requirements from spec: ~6 songs per book, 2-3 identical titles across books (cross-ref test), mix of `geprueft: true/false`, 1-2 links per song, plausible YouTube URLs.

- [ ] **Step 1: Write `data/books.yaml`**

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

- [ ] **Step 2: Write `data/songs/einklang.yaml`** (placeholder data; „Großer Gott, wir loben dich" and „Lobe den Herren" appear in gemeindeheft too → cross-refs)

```yaml
- nummer: 1
  titel: "Großer Gott, wir loben dich"
  links:
    - typ: youtube
      url: https://www.youtube.com/watch?v=dQw4w9WgXcQ
      geprueft: true
      bemerkung: "Platzhalter – gute Orgel-Aufnahme"

- nummer: 2
  titel: "Lobe den Herren, den mächtigen König der Ehren"
  alternative_nummer: 3
  links:
    - typ: youtube
      url: https://www.youtube.com/watch?v=dQw4w9WgXcQ
      geprueft: false

- nummer: 3
  titel: "Danke für diesen guten Morgen"
  links:
    - typ: spotify
      url: https://open.spotify.com/track/placeholder
      geprueft: true
    - typ: youtube
      url: https://www.youtube.com/watch?v=dQw4w9WgXcQ
      geprueft: false

- nummer: 4
  titel: "Ich will dir Dank opfern"
  links: []

- nummer: 5
  titel: "Komm, Heiliger Geist"
  links:
    - typ: youtube
      url: https://www.youtube.com/watch?v=dQw4w9WgXcQ
      geprueft: false

- nummer: 6
  titel: "Sonne der Gerechtigkeit"
  links: []
```

- [ ] **Step 3: Write `data/songs/gemeindeheft.yaml`** (same titles as einklang 1 and 2, own numbering; `alternative_nummer` points the other way)

```yaml
- nummer: 1
  titel: "Großer Gott, wir loben dich"
  alternative_nummer: 1
  links:
    - typ: youtube
      url: https://www.youtube.com/watch?v=dQw4w9WgXcQ
      geprueft: true

- nummer: 3
  titel: "Lobe den Herren, den mächtigen König der Ehren"
  links:
    - typ: youtube
      url: https://www.youtube.com/watch?v=dQw4w9WgXcQ
      geprueft: false

- nummer: 7
  titel: "In dir ist Freude"
  links:
    - typ: bandcamp
      url: https://example.bandcamp.com/track/placeholder
      geprueft: true

- nummer: 8
  titel: "Vertraut den neuen Wegen"
  links: []

- nummer: 9
  titel: "Erd und Himmel sollen singen"
  links:
    - typ: tidal
      url: https://tidal.com/browse/track/placeholder
      geprueft: false

- nummer: 10
  titel: "Bewahre uns, Gott"
  links: []
```

- [ ] **Step 4: Write `data/songs/loseblatt-2025.yaml`** (fortlaufende Eingangsnummern; one more cross-ref title)

```yaml
- nummer: 1
  titel: "Sonne der Gerechtigkeit"
  links: []

- nummer: 2
  titel: "Dein Wort ist wie Licht in der Nacht"
  links:
    - typ: youtube
      url: https://www.youtube.com/watch?v=dQw4w9WgXcQ
      geprueft: false

- nummer: 3
  titel: "Meine Zeit steht in deinen Händen"
  links:
    - typ: youtube
      url: https://www.youtube.com/watch?v=dQw4w9WgXcQ
      geprueft: true

- nummer: 4
  titel: "Weit, weit weg von hier"
  links:
    - typ: andere
      url: https://example.org/audio/placeholder
      geprueft: true

- nummer: 5
  titel: "Wie soll ich dich empfangen"
  links: []

- nummer: 6
  titel: "Großer Gott, wir loben dich"
  links: []
```

- [ ] **Step 5: Sanity-parse the YAML**

Run: `python3 -c "import yaml,glob; [yaml.safe_load(open(f)) for f in glob.glob('data/**/*.yaml', recursive=True)]; print('ok')"`
Expected: `ok` (if PyYAML missing: `pip install pyyaml` first)

- [ ] **Step 6: Commit**

```bash
git add data/
git commit -m "data: placeholder books and songs for all three songbooks"
```

---

### Task 2: `scripts/validate.py`

**Files:**
- Create: `scripts/validate.py`
- Test: `scripts/validate.py` self-check via `__main__` on repo data (no framework, per spec)

**Interfaces:**
- Consumes: YAML files from Task 1.
- Produces (used by Task 3's build and Task 4's CI): `validate_all(data_dir: str) -> list[str]` returning formatted error/warning lines prefixed `FEHLER:` or `WARNUNG:`; `main() -> int` exit code (0 = no errors, 1 = errors). Build script calls `validate_all` and aborts if any line starts with `FEHLER:`.

**Checks (spec, verbatim):** Nummern je Buch eindeutig; Song-Datei referenziert existierendes Buch; URLs wohlgeformt, nur erlaubte Link-Typen; Duplikat-Titel innerhalb eines Buchs = Warnung.

- [ ] **Step 1: Write `scripts/validate.py`**

```python
#!/usr/bin/env python3
"""Prüft Datenintegrität der Liederdatenbank. Läuft lokal und in CI."""
import sys
from pathlib import Path

import yaml

ALLOWED_TYPES = {"youtube", "spotify", "tidal", "bandcamp", "andere"}


def load_yaml(path):
    try:
        return yaml.safe_load(Path(path).read_text(encoding="utf-8")) or []
    except yaml.YAMLError as e:
        raise SystemExit(f"FEHLER: Ungültiges YAML in {path}: {e}")


def validate_book(book, songs):
    """Liefert Liste von 'FEHLER:'/'WARNUNG:'-Zeilen für ein Buch."""
    issues = []
    seen_nummern = {}
    seen_titel = {}
    for song in songs:
        nr = song.get("nummer")
        titel = song.get("titel")
        if not isinstance(nr, int):
            issues.append(f"FEHLER: {book['id']}: 'nummer' fehlt oder ist keine Zahl: {song}")
            continue
        if not titel or not isinstance(titel, str):
            issues.append(f"FEHLER: {book['id']} Nr. {nr}: 'titel' fehlt")
            continue
        if nr in seen_nummern:
            issues.append(f"FEHLER: {book['id']}: Nummer {nr} doppelt ({seen_nummern[nr]} und {titel})")
        seen_nummern[nr] = titel
        if titel in seen_titel:
            issues.append(f"WARNUNG: {book['id']}: Doppelter Titel: {titel}")
        seen_titel[titel] = nr
        for link in song.get("links") or []:
            typ = link.get("typ")
            url = link.get("url", "")
            if typ not in ALLOWED_TYPES:
                issues.append(f"FEHLER: {book['id']} Nr. {nr}: unbekannter Link-Typ: {typ!r}")
            if not url.startswith(("http://", "https://")) or "/" not in url.split("//", 1)[-1] and "." not in url:
                issues.append(f"FEHLER: {book['id']} Nr. {nr}: URL nicht wohlgeformt: {url!r}")
            if not isinstance(link.get("geprueft"), bool):
                issues.append(f"FEHLER: {book['id']} Nr. {nr}: 'geprueft' fehlt oder ist kein Boolean")
    return issues


def validate_all(data_dir="data"):
    issues = []
    books = load_yaml(Path(data_dir) / "books.yaml")
    book_ids = {b["id"] for b in books if "id" in b}
    for b in books:
        if "id" not in b or "titel" not in b:
            issues.append(f"FEHLER: books.yaml: Eintrag ohne id/titel: {b}")
    songs_dir = Path(data_dir) / "songs"
    for song_file in sorted(songs_dir.glob("*.yaml")):
        book_id = song_file.stem
        if book_id not in book_ids:
            issues.append(f"FEHLER: {song_file}: Song-Datei ohne Eintrag in books.yaml")
            continue
        book = next(b for b in books if b["id"] == book_id)
        issues.extend(validate_book(book, load_yaml(song_file)))
    return issues


def main():
    issues = validate_all()
    for line in issues:
        print(line)
    errors = [i for i in issues if i.startswith("FEHLER:")]
    print(f"\n{len(errors)} Fehler, {len(issues) - len(errors)} Warnungen")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Run it on the placeholder data — must pass (0 errors)**

Run: `python3 scripts/validate.py`
Expected: `0 Fehler, 0 Warnungen`, exit code 0

- [ ] **Step 3: Negative check — temporarily break data, verify failure**

```bash
cp data/songs/einklang.yaml /tmp/einklang.bak
printf '\n- nummer: 1\n  titel: "Duplikat"\n' >> data/songs/einklang.yaml
python3 scripts/validate.py; echo "exit=$?"
mv /tmp/einklang.bak data/songs/einklang.yaml
python3 scripts/validate.py; echo "exit=$?"
```
Expected: first run prints `FEHLER: einklang: Nummer 1 doppelt …`, `exit=1`; after restore `exit=0`

- [ ] **Step 4: Commit**

```bash
git add scripts/validate.py
git commit -m "feat: validate data integrity (unique numbers, link types, URLs)"
```

---

### Task 3: `scripts/build_site.py`

**Files:**
- Create: `scripts/build_site.py`
- Output (gitignored): `_site/`

**Interfaces:**
- Consumes: YAML from Task 1, `validate_all` from Task 2 (`from validate import validate_all` — run with cwd `scripts/` or path insert).
- Produces: `_site/index.html`, `_site/<book>/index.html`, `_site/<book>/<nummer>-<slug>.html`, `_site/songs.json`, all UTF-8. `songs.json` = `[{"nummer", "titel", "buch", "buch_titel", "url"}]` (url = relative path to song page, no leading slash). Edit link target: `https://github.com/<repo>/edit/main/data/songs/<book>.yaml` where `<repo>` = env `GITHUB_REPOSITORY` or fallback from `git remote get-url origin`.
- Cross-refs: exact title match across books → „Dieses Lied steht auch in: <Buch> Nr. <nummer>".

- [ ] **Step 1: Write `scripts/build_site.py`**

```python
#!/usr/bin/env python3
"""Baut die statische Liederseite aus data/ nach _site/. Stdlib + PyYAML."""
import html
import json
import os
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from validate import validate_all  # noqa: E402

ROOT = Path(__file__).parent.parent
SITE = ROOT / "_site"

PAGE = """<!DOCTYPE html>
<html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} – Liederdatenbank</title>
<link rel="stylesheet" href="/style.css"></head>
<body><nav><a href="/">Liederdatenbank</a>{crumbs}</nav>
<main>{body}</main>
<script src="/search.js" defer></script></body></html>"""


def repo_slug():
    if os.environ.get("GITHUB_REPOSITORY"):
        return os.environ["GITHUB_REPOSITORY"]
    try:
        url = subprocess.check_output(["git", "remote", "get-url", "origin"], text=True).strip()
        return re.sub(r"[^/:]+[:/]([^/:]+/[^/]+?)(\.git)?$", r"\1", url)
    except Exception:
        return "OWNER/liederdatenbank"


def slugify(titel):
    return re.sub(r"-{2,}", "-", re.sub(r"[^\w äöüÄÖÜß-]+", "", titel).strip().replace(" ", "-").lower()) or "lied"


def load_all():
    import yaml
    books = yaml.safe_load((ROOT / "data" / "books.yaml").read_text(encoding="utf-8"))
    songs = {}
    for book in books:
        f = ROOT / "data" / "songs" / f"{book['id']}.yaml"
        if f.exists():
            songs[book["id"]] = yaml.safe_load(f.read_text(encoding="utf-8")) or []
    return books, songs


def esc(x):
    return html.escape(str(x), quote=True)


def render_song_page(song, book, others, slug):
    parts = [f"<h1>{esc(song['nummer'])}. {esc(song['titel'])}</h1>",
             f"<p>Buch: <a href='../index.html'>{esc(book['titel'])}</a> (Nr. {esc(song['nummer'])})</p>"]
    if song.get("alternative_nummer"):
        parts.append(f"<p>Alternative Nummer: {esc(song['alternative_nummer'])}</p>")
    links = song.get("links") or []
    if links:
        parts.append("<h2>Links</h2><ul>")
        for link in links:
            verified = link.get("geprueft")
            css = "" if verified else " class='ungeprueft'"
            note = f" – {esc(link['bemerkung'])}" if link.get("bemerkung") else ""
            parts.append(f"<li{css}><a href='{esc(link['url'])}' target='_blank' rel='noopener'>{esc(link['typ'].upper())}</a>"
                         f"{' ✅' if verified else ' <small>(noch nicht geprüft)</small>'}{note}</li>")
        parts.append("</ul>")
    else:
        parts.append("<p>Noch keine Links – <a href='../../issues/new?template=link-vorschlagen.md'>Link vorschlagen</a>.</p>")
    if others:
        refs = ", ".join(f"{esc(b['titel'])} Nr. {esc(o['nummer'])}" for b, o in others)
        parts.append(f"<p><em>Dieses Lied steht auch in: {refs}</em></p>")
    edit = f"https://github.com/{repo_slug()}/edit/main/data/songs/{book['id']}.yaml"
    parts.append(f"<p><a href='{edit}'>✏️ In GitHub bearbeiten</a></p>")
    return PAGE.format(title=f"{song['nummer']} – {song['titel']}", crumbs=f" › <a href='../index.html'>{esc(book['titel'])}</a>", body="\n".join(parts))


def build():
    issues = validate_all(str(ROOT / "data"))
    errors = [i for i in issues if i.startswith("FEHLER:")]
    if errors:
        print("\n".join(errors)); sys.exit("Abbruch: Daten ungültig, Build verweigert.")
    books, songs = load_all()
    SITE.mkdir(exist_ok=True)

    style = ":root{color-scheme:light}body{font-family:system-ui,sans-serif;margin:0 auto;max-width:48rem;padding:1rem}"
    style += ".ungeprueft a{color:#888}nav{margin-bottom:2rem}table{border-collapse:collapse;width:100%}"
    style += "td,th{border-bottom:1px solid #ddd;padding:.4rem;text-align:left}input{width:100%;padding:.5rem;margin:.5rem 0}"
    (SITE / "style.css").write_text(style, encoding="utf-8")

    search = """document.querySelectorAll('[data-search]').forEach(function(input){
  var table=document.querySelector('table');
  input.addEventListener('input',function(){
    var q=input.value.toLowerCase();
    table.querySelectorAll('tbody tr').forEach(function(tr){
      tr.style.display=tr.textContent.toLowerCase().indexOf(q)>-1?'':'none';});});});"""
    (SITE / "search.js").write_text(search, encoding="utf-8")

    index = ["<h1>Liederdatenbank</h1><p>Lieder unserer Gemeinde – Nummern, Titel und Links zu legalen Quellen.</p><ul>"]
    json_index = []
    for book in books:
        b_songs = songs.get(book["id"], [])
        (SITE / book["id"]).mkdir(exist_ok=True)
        desc = f"<p>{esc(book['beschreibung'])}</p>" if book.get("beschreibung") else ""
        index.append(f"<li><a href='{book['id']}/'>{esc(book['titel'])}</a> ({len(b_songs)} Lieder)</li>")
        rows = []
        for song in sorted(b_songs, key=lambda s: s["nummer"]):
            others = [(b, o) for b in books if b["id"] != book["id"]
                       for o in songs.get(b["id"], []) if o["titel"] == song["titel"]]
            slug = f"{song['nummer']}-{slugify(song['titel'])}"
            (SITE / book["id"] / f"{slug}.html").write_text(render_song_page(song, book, others, slug), encoding="utf-8")
            badge = " ✅" if any(l.get("geprueft") for l in song.get("links") or []) else ""
            rows.append(f"<tr><td>{esc(song['nummer'])}</td><td><a href='{slug}.html'>{esc(song['titel'])}</a>{badge}</td></tr>")
            json_index.append({"nummer": song["nummer"], "titel": song["titel"], "buch": book["id"],
                               "buch_titel": book["titel"], "url": f"{book['id']}/{slug}.html"})
        body = f"<h1>{esc(book['titel'])}</h1>{desc}<input data-search placeholder='Suchen (Nummer oder Titel)…'>"
        body += "<table><thead><tr><th>Nr.</th><th>Titel</th></tr></thead><tbody>" + "".join(rows) + "</tbody></table>"
        (SITE / book["id"] / "index.html").write_text(PAGE.format(title=book["titel"], crumbs="", body=body), encoding="utf-8")
    index.append("</ul>")
    (SITE / "index.html").write_text(PAGE.format(title="Start", crumbs="", body="\n".join(index)), encoding="utf-8")
    (SITE / "songs.json").write_text(json.dumps(json_index, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Build ok: {len(json_index)} Lieder, {len(books)} Bücher → {SITE}/")


if __name__ == "__main__":
    build()
```

- [ ] **Step 2: Run the build**

Run: `python3 scripts/build_site.py`
Expected: `Build ok: 18 Lieder, 3 Bücher → …/_site/`

- [ ] **Step 3: Existence check (per spec)**

```bash
test -f _site/index.html && test -f _site/einklang/index.html && test -f _site/einklang/1-grosser-gott-wir-loben-dich.html && test -f _site/gemeindeheft/1-grosser-gott-wir-loben-dich.html && test -f _site/songs.json && test -f _site/style.css && test -f _site/search.js && echo ALLES DA
```
Expected: `ALLES DA`

- [ ] **Step 4: Content spot-checks**

```bash
grep -c "steht auch in" _site/einklang/1-grosser-gott-wir-loben-dich.html _site/gemeindeheft/1-grosser-gott-wir-loben-dich.html
grep -c "ungeprueft" _site/einklang/3-danke-fur-diesen-guten-morgen.html
python3 -c "import json; d=json.load(open('_site/songs.json')); assert len(d)==18 and all('nummer' in s and 'url' in s for s in d); print('json ok')"
```
Expected: cross-ref present in both files (≥1 each); unverified class present; `json ok`

- [ ] **Step 5: Commit**

```bash
git add scripts/build_site.py
git commit -m "feat: static site builder (index, book pages, song pages, JSON search)"
```

---

### Task 4: CI workflow `deploy.yml`

**Files:**
- Create: `.github/workflows/deploy.yml` (file exists but empty — overwrite)

**Interfaces:**
- Consumes: `scripts/validate.py` (Task 2), `scripts/build_site.py` (Task 3).
- Produces: deployed GitHub Pages site on push to `main`; validation-only on PRs.

- [ ] **Step 1: Write `.github/workflows/deploy.yml`**

```yaml
name: Validate & Deploy

on:
  push:
    branches: [main]
  pull_request:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: pages
  cancel-in-progress: true

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: {python-version: "3.13"}
      - run: pip install pyyaml
      - run: python scripts/validate.py
      - run: python scripts/build_site.py
      - if: github.ref == 'refs/heads/main' && github.event_name == 'push'
        uses: actions/upload-pages-artifact@v3
        with: {path: _site}

  deploy:
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    needs: build
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - id: deployment
        uses: actions/deploy-pages@v4
```

- [ ] **Step 2: Syntax check**

Run: `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/deploy.yml')); print('yaml ok')"`
Expected: `yaml ok`

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/deploy.yml
git commit -m "ci: validate on PRs, build and deploy site to GitHub Pages on main"
```

---

### Task 5: README update

**Files:**
- Modify: `README.md` (lines 100-116 area: „Webseite bauen & deployen" section; line 124-131 roadmap)

**Interfaces:**
- Consumes: reality from Tasks 2-4.
- Produces: documentation matching the built system.

- [ ] **Step 1: Replace the „Webseite bauen & deployen" section**

Old (lines ~104-116, `## Webseite bauen & deployen` through the „Deployment:" paragraph) → new:

```markdown
## Webseite bauen & deployen

```bash
# Abhängigkeit
pip install pyyaml

# Daten prüfen
python scripts/validate.py

# Lokal bauen (→ _site/, dann z. B. `python -m http.server -d _site` öffnen)
python scripts/build_site.py
```

Deployment: Bei jedem Merge auf `main` baut GitHub Actions die Seite neu und veröffentlicht sie über **GitHub Pages** (Einstellung: Settings → Pages → Source: GitHub Actions). Kein Server, keine Kosten, kein manueller Schritt.
```

- [ ] **Step 2: Update the repository-structure block** (`site/` line): replace `├── site/                       # Statischer Seitengenerator (Hugo/Eleventy/Astro)` with `├── scripts/build_site.py      # Statischer Seitengenerator (Pure Python)` — insert into the scripts listing, remove the `site/` line and the empty `site/` directory + `.gitkeep`.

- [ ] **Step 3: Update roadmap**

```markdown
- [x] Datenmodell für mehrere Liederbücher
- [x] Platzhalterdaten für alle drei Bücher (echter Import folgt)
- [x] Statische Seite mit Suche & Buch-/Liedseiten, Deployment via GitHub Pages
- [ ] Import des Einklang-Inhaltsverzeichnisses
- [ ] Erster Agent-Durchlauf für Link-Kandidaten (Einklang)
- [ ] Echte Daten für Gemeindeheft & Loseblattsammlung erfassen
- [ ] Ggf. Migration auf kanonisches Lied-Modell (ein Lied, mehrere Vorkommen), wenn das Titel-Matching sich bewährt hat
```

- [ ] **Step 4: Commit (incl. removing `site/`)**

```bash
git rm -r site/ 2>/dev/null || rm -rf site/
git add README.md
git commit -m "docs: README matches Python build pipeline; remove empty site/ dir"
```

---

## Selbst-Review (nach Schreiben ausgeführt)

- **Spec coverage:** Datenmodell+Platzhalter (Task 1), validate Checks inkl. Warnungs-Exit-Code (Task 2), alle Seiten + songs.json + JS-Suche + Cross-Refs + Edit-Link + De-Emphasis (Task 3), CI validate→build→deploy (Task 4), README-Update (Task 5). Lücken: keine.
- **Platzhalter:** keine TBDs; alle Steps enthalten ausführbaren Code/Commands.
- **Typ-Konsistenz:** `validate_all(data_dir: str) -> list[str]` in Task 2 wird in Task 3 exakt so benutzt (`from validate import validate_all`); `FEHLER:`-Präfix in beiden identisch; `songs.json`-Felder decken die JS-Suche (Textfilter über Tabellenzeilen) ab.
