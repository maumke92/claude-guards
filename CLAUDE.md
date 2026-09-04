# claude-guards – Projektgedächtnis für Claude Code

Antworte und dokumentiere auf Deutsch, Umlaute echt. Bedienung und Blockgründe
für Anwender: `BEDIENUNG.md`; Installation: `README.md`.

## Was das ist

Zwei Claude-Code-Plugins mit Hooks, die Grenzen ziehen:

- `sicherheits-guard/` (`hooks/guard.py`): blockt Lese-/Schreibzugriffe auf
  sensible Dateien (Umgebungsdateien, Backups, DB-Dumps, private Schlüssel) und
  gefährliche Bash-Befehle. Nur Standardbibliothek, Windows und macOS.
- `dev-guards/` (`hooks/`): `commit-guard.ps1` (Commit nur mit gestagtem
  CHANGELOG), `py-check.ps1` (Syntaxprüfung geänderter .py mit der Projekt-venv),
  `repeat-guard.py` (Erinnerung beim dritten identischen Werkzeugaufruf).

Marketplace-Manifest in `.claude-plugin/marketplace.json`, je Plugin ein
`.claude-plugin/plugin.json` mit eigener Version.

## Regeln

1. **Guards sind sicherheitskritisch:** Änderungen an `guard.py` entwirft und
   prüft der Host selbst (kein Qwen-Loop); jede neue Sperre bekommt einen Test in
   `test_guard.py` (positiv: blockt; negativ: harmloser Befehl geht durch).
2. **Fail-closed bei Zweifel, aber keine Substring-Fallen ohne Test:** Muster wie
   `.env` treffen als Teilstring auch `.envrc`-Verwandte und Commit-Messages
   (Memory „git add-Fallen"). Jedes Muster mit einem Gegenbeispiel absichern.
3. **Kein Netz, keine Fremdpakete** in Hooks – sie laufen in jeder Sitzung.
4. Layout ist das Anthropic-Plugin-Layout (`.claude-plugin/`, `hooks/`), nicht
   der Style Guide für Anwendungen; der Guide gilt für die Python-Skripte
   (Ruff-Config `ruff.toml`, Tests neben dem Code).

## Pflichten bei jeder Änderung

1. `ruff check . && ruff format --check .`; Tests:
   `cd sicherheits-guard/hooks && python -m unittest -q test_guard` und
   `cd dev-guards/hooks && python -m unittest -q test_repeat_guard`.
2. Version des betroffenen Plugins in dessen `plugin.json` erhöhen, Eintrag in
   `CHANGELOG.md`, bei neuen Sperren `BEDIENUNG.md` (Fälligkeit über
   `.anleitung.json`).
3. Nach dem Commit die installierten Kopien nachziehen (`claude plugin update`
   bzw. Marketplace-Refresh); die Version in `~/.claude/plugins/` ist der Beleg.
