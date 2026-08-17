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

# Supply-Chain: Download-Befehl direkt in die Shell gepipet (curl ... | bash).
# Wortgrenzen, damit "confirm"/"firm" (enthaelt "irm") nicht faelschlich blocken.
DOWNLOAD_TOOL_RE = re.compile(
    r"\b(?:curl|wget|iwr|irm|invoke-webrequest|invoke-restmethod)\b")
PIPE_TO_SHELL = re.compile(r"\|\s*(bash|sh|zsh|iex|powershell|pwsh)\b")

# Push auf main oder HEAD: Lieferungen gehen nur ueber Feature-Branch
# + Pull Request (Vorfall HR-Suite 1.135.0 am 17.08.2026 - Push von
# HEAD verdeckte, dass der aktuelle Branch main war). HEAD ist
# branch-blind und deshalb ebenfalls gesperrt. Begrenzt auf das
# jeweilige Befehlssegment ([^;|&]*), damit ein "main" in einem
# verketteten Folgebefehl nicht faelschlich blockt; "main" nur als
# ganzes Wort (Branches wie feat/main-menu bleiben erlaubt).
PUSH_MAIN_RE = re.compile(
    r"git\s+(?:-c\s+\S+\s+)*push\b[^;|&]*\b(?:head\b|main(?![\w-]))")

FILE_TOOLS = {"Read", "Edit", "Write", "NotebookEdit", "MultiEdit"}

# Tools, deren Befehle geprueft werden - PowerShell laeuft sonst am
# Guard vorbei (der HR-Suite-Vorfall passierte ueber das
# PowerShell-Tool, nicht ueber Bash).
COMMAND_TOOLS = {"Bash", "PowerShell"}


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
    if PIPE_TO_SHELL.search(c) and DOWNLOAD_TOOL_RE.search(c):
        return "download | shell"
    # 2b) Push auf main/HEAD - Lieferungen nur per Feature-Branch + PR
    if PUSH_MAIN_RE.search(c):
        return "git push auf main/HEAD - Feature-Branch + PR nutzen"
    # 3) Befehle, die sensible Pfade beruehren (cat .env, copy backups\..., python x.py .env)
    #    Pro Token entscheiden: eine erlaubte Ausnahme (z. B. .env.example) befreit
    #    NUR ihren eigenen Token, nicht den ganzen Befehl - sonst genuegt ein
    #    angehaengtes ".env.example", um das Lesen von ".env" zu tarnen
    #    (cat .env .env.example).
    for token in c.split():
        bare = token.strip("\"'")
        if any(bare.endswith(exc) for exc in ALLOWED_EXCEPTIONS):
            continue
        for pattern in BLOCKED_PATH_PATTERNS:
            if pattern in bare:
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

    elif tool in COMMAND_TOOLS:
        command = tool_input.get("command", "")
        hit = command_is_blocked(command)
        if hit:
            deny(f"{tool}-Befehl, Muster: {hit}")

    # Kein Treffer: keine Entscheidung, normale Berechtigungspruefung laeuft weiter
    sys.exit(0)


if __name__ == "__main__":
    main()
