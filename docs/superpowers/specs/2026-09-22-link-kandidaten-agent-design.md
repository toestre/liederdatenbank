# Design: Agent-Skill „link-kandidaten"

Datum: 2026-09-22
Status: vom Nutzer genehmigt

## Ziel

Ein manuell aufrufbarer Agent-Durchlauf, der für Liederbücher Lieder ohne geprüften Link per YouTube-Websuche Link-Kandidaten sammelt und diese nach `candidates.yaml` schreibt. Der Agent entscheidet nicht – er liefert Kandidaten. Das Einpflegen in `data/songs/*.yaml` und `geprueft: true` bleibt Maintainer-Arbeit.

## Umfeld / Entscheidungen

- Laufumgebung: manuell via opencode (Projekt-Skill im Repo), kein API-Key, keine CI.
- Quellen: nur YouTube (Websuche via Webfetch).
- Ausgabe: `candidates.yaml` im Repo-Root, committet.
- Batch-Größe pro Aufruf vorgebbar (`--anzahl N`, Default 10), zusätzlich `--ab-nummer` zum Überspringen.
- Ersatz für den leeren Platzhalter `scripts/fetch_links.py` (wird gelöscht; README-Abschnitt wird auf den Skill umgeschrieben).

## Komponenten

1. `.opencode/skills/link-kandidaten/SKILL.md` – einzige neue Codedatei. Enthält Ablauf, Argumente, `candidates.yaml`-Format, Nicht-Tun-Regeln, Selbsttest.
2. `candidates.yaml` – Ausgabedatei (Agent erzeugt/ergänzt sie, wird committet).
3. `scripts/fetch_links.py` – löschen.
4. `README.md` – Abschnitt „Agent-gestützte Linksuche (Maintainer)" umschreiben: Aufruf über opencode-Skill, keine API-Keys, Ausgabe `candidates.yaml`.

## Ablauf pro Aufruf

1. `data/songs/<buch>.yaml` laden; Lieder bestimmen, die **keinen** Link mit `geprueft: true` haben. Lieder, die bereits mit `status: offen` in `candidates.yaml` stehen (oder dort Vorschläge haben), werden übersprungen.
2. Batch bestimmen: `--anzahl N` (Default 10), aufsteigende Nummer ab `--ab-nummer` (Default 1).
3. Pro Lied YouTube-Suche via Webfetch: `"<titel> Einklang"`, Fallback `"<titel> Chor"`. Max. 3 Kandidaten pro Lied; nur `youtube.com/watch`-URLs (kein youtu.be, keine Shorts).
4. `candidates.yaml` ergänzen (Format unten). Bereits gelistete Lieder nicht neu suchen.
5. Selbsttest: geschriebene Datei mit `yaml.safe_load` laden.
6. `python scripts/validate.py` (stellt nebenbei sicher, dass songs-Dateien unberührt sind).
7. Committen: `agent: N Link-Kandidaten für <buch>`. Kein Push ohne Aufforderung.

## Format `candidates.yaml`

```yaml
- buch: einklang
  nummer: 6
  titel: "..."
  status: offen          # offen | uebernommen | verworfen
  vorschlaege:
    - url: "https://www.youtube.com/watch?v=..."
      suche: "<nutzter Suchbegriff>"
      hinweis: "<kurze Beobachtung, z. B. Chor-Aufnahme"
```

- `status: offen` beim Anlegen. Maintainer setzt `uebernommen` bzw. `verworfen` beim Review – so bleibt die Historie erhalten und der Agent sucht verworfene Lieder nicht erneut.

## Nicht-Tun (im Skill fixiert)

- Agent schreibt nie in `data/songs/*.yaml`.
- Agent setzt nie `geprueft: true`.
- Kein Embed-Prüfen/Abspielen; Kandidaten sind unverbindliche Vorschläge.

## Fehlerbehandlung

- Webfetch scheitert oder keine Treffer → Eintrag mit `vorschlaege: []` und `hinweis: "keine Treffer"`; weiter mit nächstem Lied.
- `candidates.yaml` unlesbar/kaputt → vor Neuanlage Nutzer warnen, dann frisch anlegen.

## Test

Nach Anlage ein Probelauf mit `--anzahl 3`: `validate.py` grün, `candidates.yaml` per `yaml.safe_load` ladbar, Ergebnis dem Nutzer gezeigt. Kein Testframework (Datenformat wird vom Agent-Selbsttest abgedeckt).
