# claude-guards — Schutz-Hooks für Claude Code

Lokaler Plugin-Marketplace mit zwei Plugins. Die Hooks registrieren sich
bei der Installation automatisch — kein Eingriff in settings.json nötig.

## Installation

```
claude plugin marketplace add C:\KI-Tools\Claude\claude-guards
claude plugin install dev-guards@claude-guards
claude plugin install sicherheits-guard@claude-guards
```

Danach neue Claude-Code-Session starten.

## dev-guards

- **commit-guard** (PreToolUse/Bash): blockiert `git commit`, solange
  CHANGELOG.md nicht gestaged ist. Greift nur in Projekten, die ein
  CHANGELOG.md im Arbeitsordner haben — alle anderen bleiben unbehelligt.
- **py-check** (PostToolUse/Edit|Write): kompiliert jede geänderte
  .py-Datei mit `.venv\Scripts\python.exe -m py_compile` und meldet
  Syntaxfehler sofort. Greift nur, wenn das Projekt eine `.venv` hat.
- **repeat-guard** (PostToolUse, alle Tools): zählt identische
  Werkzeugaufrufe je Sitzung und erinnert beim dritten Mal einmalig an die
  Abbruchpunkte-Regel („zweimal am selben Symptom gescheitert heißt
  anhalten"). Danach bleibt dieselbe Signatur stumm. Blockt nie, bei
  kaputter Eingabe Exit 0. Zustand liegt je Sitzung im Temp-Ordner.
  Selbsttest: `python dev-guards/hooks/test_repeat_guard.py`.

## sicherheits-guard

- **guard.py** (PreToolUse, alle Datei-Tools + Bash): blockt Zugriffe auf
  sensible Dateien (.env, backups/, media/, *.sql, *.pem, private
  Schlüssel …) und gefährliche Bash-Befehle (`git add -A`, `rm -rf /` …).
  Benötigt nur Python (Standardbibliothek) im PATH.
- Hinweis: Die zusätzlichen permissions-Deny-Regeln kann ein Plugin nicht
  setzen. Wer sie zusätzlich möchte (Gürtel + Hosenträger), nutzt weiterhin
  `C:\KI-Tools\Claude\guard-setup\Guard-Installieren.cmd`.

## Herkunft

Extrahiert aus den projektlokalen Hooks von hr-suite und
claude-projekt-studio sowie aus guard-setup (C:\KI-Tools\Claude).
