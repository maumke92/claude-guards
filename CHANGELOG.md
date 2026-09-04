# Changelog – claude-guards

Eine Überschrift je Lieferung, Neuestes oben; Plugin-Versionen stehen in den
`plugin.json`-Dateien.

## 2026-09-04 – sicherheits-guard 1.2.1, dev-guards 1.1.1

- **Style Guide (Projektrunde):** `ruff.toml` (line-length 88, Regeln E/F/I/B/UP,
  E501 aus), alle vier Python-Dateien formatiert, sieben `.format()`-Aufrufe zu
  f-strings (UP032). Keine Logikänderung; beide Testdateien grün.
- `CLAUDE.md`, `HANDOVER.md`, `.review-gate.json` (Lint- und Testbefehle) angelegt.

## 2026-08-25 – sicherheits-guard 1.2.0, dev-guards 1.1.0

- Stand vor dem Changelog: vier zusätzlich gesperrte Endungen (siehe
  `BEDIENUNG.md`), repeat-guard, py-check, commit-guard.
