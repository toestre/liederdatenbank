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
         hinweis: "<kurze Beobachtung, z. B. Chor-Aufnahme des Lieds>"
   ```

   - Keine Treffer oder Suche scheitert: Eintrag mit `vorschlaege: []` und zusätzlichem Feld `hinweis: "keine Treffer"` auf Eintragsebene – dann weiter mit dem nächsten Lied.
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
