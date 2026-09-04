#!/usr/bin/env python3
"""
Claude Code PostToolUse-Guard: erkennt Schleifen.

Zaehlt identische Werkzeugaufrufe je Sitzung. Beim dritten Mal wird einmalig
an die Abbruchpunkte-Regel erinnert (CLAUDE.md, "Zwei-Schritte-zurueck").
Danach bleibt dieselbe Signatur stumm.

Blockt nie. Bei kaputter oder leerer Eingabe: Exit 0, keine Ausgabe.
Vorbild: packages/guard/repeat-tool-reminder aus deepseek-ai/deepseek-harness.
"""

import hashlib
import json
import os
import re
import sys
import tempfile
from pathlib import Path

SCHWELLE = 3  # ab dem wievielten identischen Aufruf erinnert wird
MAX_SIGNATUREN = 300  # Notbremse gegen unbegrenzt wachsende Statusdateien

ERINNERUNG = (
    "Dritter identischer {tool}-Aufruf in dieser Sitzung. Abbruchpunkte-Regel: "
    "zweimal am selben Symptom gescheitert heisst anhalten. Kein dritter "
    "Versuch aus dem Stand - betroffene Datei ganz lesen, Aufrufer pruefen, "
    "die falsche Annahme benennen. Ist etwas unklar, dem User sagen was unklar "
    "ist, statt zu raten."
)


def signature(tool_name, tool_input):
    """Stabile Kurzsignatur eines Aufrufs; None, wenn nichts Kennzeichnendes da ist."""
    ti = tool_input if isinstance(tool_input, dict) else {}
    if tool_name in ("Bash", "PowerShell"):
        kern = " ".join(str(ti.get("command", "")).split())
    elif tool_name in ("Edit", "MultiEdit"):
        kern = "{}|{}".format(
            ti.get("file_path", ""), str(ti.get("old_string", ""))[:200]
        )
    elif tool_name in ("Grep", "Glob"):
        kern = "{}|{}".format(ti.get("pattern", ""), ti.get("path", ""))
    elif tool_name in ("Read", "Write", "NotebookEdit"):
        kern = str(ti.get("file_path") or ti.get("notebook_path") or "")
    else:
        kern = json.dumps(ti, sort_keys=True, ensure_ascii=False)[:400]
    if not kern.strip():
        return None
    roh = f"{tool_name}\x00{kern}"
    return hashlib.sha1(roh.encode("utf-8", "replace")).hexdigest()[:16]


def zaehle(zaehler, sig):
    """Erhoeht den Zaehler. True genau beim Erreichen der Schwelle, sonst False."""
    n = int(zaehler.get(sig, 0)) + 1
    zaehler[sig] = n
    return n == SCHWELLE


def statusdatei(session_id):
    sicher = re.sub(r"[^A-Za-z0-9_-]", "_", str(session_id))[:64] or "ohne-sitzung"
    ordner = Path(tempfile.gettempdir()) / "claude-guards"
    return ordner / f"repeat-{sicher}.json"


def lade(pfad):
    try:
        daten = json.loads(pfad.read_text(encoding="utf-8"))
    except Exception:
        return {}
    if not isinstance(daten, dict) or len(daten) > MAX_SIGNATUREN:
        return {}
    # Nur echte Zaehlerwerte uebernehmen: eine von Hand oder von fremder Seite
    # verbogene Datei darf spaeter kein int() zum Werfen bringen (Exit 0 gilt).
    return {k: v for k, v in daten.items() if isinstance(v, int)}


def speichere(pfad, zaehler):
    """Schreibt atomar, damit ein paralleler Lauf keine halbe Datei liest.

    Nicht abgedeckt: zwei Laeufe, die gleichzeitig lesen und schreiben, koennen
    sich gegenseitig ueberschreiben. Fuer eine reine Erinnerung akzeptiert -
    eine Sperrdatei waere teurer als der Schaden.
    """
    try:
        pfad.parent.mkdir(parents=True, exist_ok=True)
        vorlaeufig = pfad.with_suffix(f".{os.getpid()}.tmp")
        vorlaeufig.write_text(json.dumps(zaehler), encoding="utf-8")
        os.replace(vorlaeufig, pfad)
    except Exception:
        pass  # Statusverlust ist harmlos, ein blockierter Hook waere es nicht


def main():
    try:
        daten = json.load(sys.stdin)
    except Exception:
        return 0
    if not isinstance(daten, dict):
        return 0

    tool = str(daten.get("tool_name", ""))
    sig = signature(tool, daten.get("tool_input"))
    if not sig:
        return 0

    pfad = statusdatei(daten.get("session_id"))
    zaehler = lade(pfad)
    erinnern = zaehle(zaehler, sig)
    speichere(pfad, zaehler)

    if erinnern:
        text = ERINNERUNG.format(tool=tool or "Werkzeug")
        print(
            json.dumps(
                {
                    "systemMessage": "Schleifen-Guard: dritter identischer {}-Aufruf.".format(
                        tool or "Werkzeug"
                    ),
                    "hookSpecificOutput": {
                        "hookEventName": "PostToolUse",
                        "additionalContext": text,
                    },
                },
                ensure_ascii=False,
            )
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
