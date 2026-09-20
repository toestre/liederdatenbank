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
