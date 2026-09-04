# Projektstand & offene Punkte (Übergabe an Claude Code)

## Offene Punkte

- **Lokale Kopien der Guards in Projekten entfernen** (Memory
  „claude-guards-Plugins"): HR-Suite und Projekt-Studio tragen noch eigene
  `.claude/hooks/commit-guard.ps1`-Fassungen aus der Zeit vor dem Plugin. Erledigt,
  wenn dort nur noch die Plugin-Hooks greifen (`.claude/settings.json` ohne
  lokalen Hook-Eintrag) und ein Commit ohne gestagtes CHANGELOG weiterhin blockt.
- **Style Guide (Projektrunde 04.09.2026):** Ruff-Config und Formatierung sind
  drin (sicherheits-guard 1.2.1, dev-guards 1.1.1); Plugin-Layout als bekannte
  Abweichung eingetragen. Nichts weiter offen.

## Bekannte Eigenheiten

- Hooks laufen in jeder Sitzung; ein Fehler in `guard.py` blockt alle
  Bash-/Edit-Aufrufe. Vor dem Nachziehen der installierten Kopie immer beide
  Testdateien laufen lassen.
- Der Sicherheits-Guard prüft Befehlstexte als Teilstring; Dateinamen wie
  `.env` deshalb in Commit-Messages umschreiben („Umgebungsdatei").
