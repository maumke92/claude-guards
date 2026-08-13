#!/usr/bin/env python3
"""
Claude Code PreToolUse-Guard
Blockt Zugriffe auf sensible Dateien und gefaehrliche Bash-Befehle.

Registriert in: %USERPROFILE%\\.claude\\settings.json (PreToolUse-Hook)
Funktioniert unter Windows und macOS identisch (nur Python-Standardbibliothek).
"""

import json
import re
import sys

# ---------------------------------------------------------------------------
# Konfiguration: Diese Muster werden geblockt (Kleinschreibung, Teilstring-Match
# auf normalisierte Pfade mit "/"-Trennern).
# ---------------------------------------------------------------------------

# Dateien/Ordner, die Claude weder lesen noch schreiben darf
BLOCKED_PATH_PATTERNS = [
    ".env",          # trifft .env, .env.prod, deploy/.env ...
    "backups/",      # Datenbank-Backups mit echten Personaldaten
    "media/",        # hochgeladene Dokumente (Personalakten etc.)
    ".sql.gz",       # DB-Dumps
    ".sql",          # unkomprimierte Dumps
    ".pem",          # Zertifikate / private Schluessel
    ".key",
    "id_rsa",
    "id_ed25519",
    "secrets/",
]

# Ausnahmen: Diese duerfen trotz Treffer oben bearbeitet werden
ALLOWED_EXCEPTIONS = [
    ".env.example",
    ".env.sample",
    ".env.template",
]

# Bash-Befehle, die unabhaengig von Pfaden geblockt werden
BLOCKED_COMMAND_PATTERNS = [
    "git add -a",       # trifft "git add -A" (wir vergleichen kleingeschrieben)
    "git add .",        # pauschales Stagen -> Gefahr, Sensibles zu committen
    "git add --all",
    "rm -rf /",
    "format c:",
    "--dangerously-skip-permissions",  # Agent ohne Permission-Schranken starten
]

# Supply-Chain: Download-Befehl direkt in die Shell gepipet (curl ... | bash)
DOWNLOAD_TOOLS = ["curl", "wget", "iwr", "irm", "invoke-webrequest", "invoke-restmethod"]
PIPE_TO_SHELL = re.compile(r"\|\s*(bash|sh|zsh|iex|powershell|pwsh)\b")

FILE_TOOLS = {"Read", "Edit", "Write", "NotebookEdit", "MultiEdit"}


def normalize(path: str) -> str:
    return path.replace("\\", "/").lower()


def path_is_blocked(path: str) -> str | None:
    """Gibt das getroffene Muster zurueck oder None."""
    p = normalize(path)
    for exc in ALLOWED_EXCEPTIONS:
        if p.endswith(exc):
            return None
    for pattern in BLOCKED_PATH_PATTERNS:
        if pattern in p:
            return pattern
    return None


def command_is_blocked(command: str) -> str | None:
    c = normalize(command)
    # 1) Explizit verbotene Befehle
    for pattern in BLOCKED_COMMAND_PATTERNS:
        if pattern in c:
            return pattern
    # 2) Download direkt in die Shell gepipet (Supply-Chain-Risiko)
    if PIPE_TO_SHELL.search(c) and any(t in c for t in DOWNLOAD_TOOLS):
        return "download | shell"
    # 3) Befehle, die sensible Pfade beruehren (cat .env, copy backups\..., python x.py .env)
    for exc in ALLOWED_EXCEPTIONS:
        if exc in c:
            return None
    for pattern in BLOCKED_PATH_PATTERNS:
        if pattern in c:
            return pattern
    return None


def deny(reason: str) -> None:
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                f"Vom Sicherheits-Guard geblockt ({reason}). "
                "Sensible Dateien (.env, Backups, Personaldaten) sind fuer "
                "Claude Code gesperrt. Falls der Zugriff wirklich noetig ist, "
                "muss der Nutzer guard.py anpassen."
            ),
        }
    }))
    sys.exit(0)


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        # Eingabe nicht lesbar -> keine Entscheidung, normaler Ablauf
        sys.exit(0)

    tool = data.get("tool_name", "")
    tool_input = data.get("tool_input", {}) or {}

    if tool in FILE_TOOLS:
        path = tool_input.get("file_path") or tool_input.get("path") or ""
        hit = path_is_blocked(path)
        if hit:
            deny(f"Datei-Zugriff, Muster: {hit}")

    elif tool == "Bash":
        command = tool_input.get("command", "")
        hit = command_is_blocked(command)
        if hit:
            deny(f"Bash-Befehl, Muster: {hit}")

    # Kein Treffer: keine Entscheidung, normale Berechtigungspruefung laeuft weiter
    sys.exit(0)


if __name__ == "__main__":
    main()
