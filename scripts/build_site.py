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
