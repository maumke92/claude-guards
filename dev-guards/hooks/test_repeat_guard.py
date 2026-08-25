#!/usr/bin/env python3
"""Selbsttest fuer repeat-guard.py (ohne Framework): python test_repeat_guard.py

Prueft die drei Zusagen des Guards:
- drei identische Aufrufe -> genau eine Erinnerung, danach Ruhe
- verschiedene Aufrufe -> keine Erinnerung
- kaputte oder leere Eingabe -> Exit 0, keine Ausgabe (Hook darf nie stoeren)
"""
import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HIER = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("repeat_guard", HIER / "repeat-guard.py")
rg = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rg)


def check(name, cond):
    assert cond, "FEHLGESCHLAGEN: {}".format(name)
    print("ok  {}".format(name))


def lauf(nutzlast):
    """Ruft den Hook als echten Prozess auf und liefert (Exit-Code, stdout)."""
    p = subprocess.run([sys.executable, str(HIER / "repeat-guard.py")],
                       input=nutzlast, capture_output=True, text=True)
    return p.returncode, p.stdout.strip()


# --- Signaturen ---------------------------------------------------------
check("gleicher Bash-Befehl trotz anderer Leerzeichen gleiche Signatur",
      rg.signature("Bash", {"command": "ls  -la"})
      == rg.signature("Bash", {"command": "ls -la"}))
check("anderer Bash-Befehl andere Signatur",
      rg.signature("Bash", {"command": "ls -la"})
      != rg.signature("Bash", {"command": "ls -l"}))
check("Read auf gleiche Datei ist gleich, egal ab welcher Zeile",
      rg.signature("Read", {"file_path": "a.py", "offset": 1})
      == rg.signature("Read", {"file_path": "a.py", "offset": 500}))
check("Edit mit anderem old_string andere Signatur",
      rg.signature("Edit", {"file_path": "a.py", "old_string": "x"})
      != rg.signature("Edit", {"file_path": "a.py", "old_string": "y"}))
check("leerer Befehl liefert keine Signatur",
      rg.signature("Bash", {"command": "   "}) is None)
check("fehlendes tool_input liefert keine Signatur",
      rg.signature("Read", None) is None)
check("unbekanntes Werkzeug bekommt trotzdem eine Signatur",
      rg.signature("Irgendwas", {"a": 1}) is not None)

# --- Zaehlwerk ----------------------------------------------------------
z = {}
sig = rg.signature("Bash", {"command": "pytest"})
check("erster Aufruf erinnert nicht", rg.zaehle(z, sig) is False)
check("zweiter Aufruf erinnert nicht", rg.zaehle(z, sig) is False)
check("dritter Aufruf erinnert", rg.zaehle(z, sig) is True)
check("vierter Aufruf bleibt stumm", rg.zaehle(z, sig) is False)
check("fuenfter Aufruf bleibt stumm", rg.zaehle(z, sig) is False)

z2 = {}
check("drei verschiedene Aufrufe erinnern nie", not any(
    rg.zaehle(z2, rg.signature("Bash", {"command": c}))
    for c in ("ls", "pwd", "whoami")))

# --- Statusdatei --------------------------------------------------------
check("Sitzungskennung wird fuer den Dateinamen entschaerft",
      ".." not in rg.statusdatei("../../boese").name
      and "/" not in rg.statusdatei("a/b").name)
check("fehlende Sitzungskennung faellt auf einen festen Namen zurueck",
      rg.statusdatei(None).name.endswith(".json"))
check("fehlende Statusdatei wird verworfen statt zu werfen",
      rg.lade(Path(tempfile.gettempdir()) / "gibt-es-nicht-42.json") == {})

# Review-Befund 24.08.: verbogene Werte durften nicht bis ins int() durchkommen
kaputt = Path(tempfile.gettempdir()) / "claude-guards" / "repeat-kaputt-test.json"
kaputt.parent.mkdir(parents=True, exist_ok=True)
kaputt.write_text('{"aaa": "keine Zahl", "bbb": 2}', encoding="utf-8")
gelesen = rg.lade(kaputt)
check("Nicht-Zahlen werden beim Laden aussortiert", gelesen == {"bbb": 2})
check("Zaehlen laeuft danach ohne Ausnahme durch",
      rg.zaehle(gelesen, "aaa") is False)
kaputt.write_text("[1, 2, 3]", encoding="utf-8")
check("JSON ohne Objekt wird verworfen", rg.lade(kaputt) == {})
kaputt.unlink(missing_ok=True)

# --- Ende zu Ende -------------------------------------------------------
code, aus = lauf("kein json")
check("kaputte Eingabe: Exit 0 ohne Ausgabe", code == 0 and aus == "")
code, aus = lauf("")
check("leere Eingabe: Exit 0 ohne Ausgabe", code == 0 and aus == "")
code, aus = lauf(json.dumps({"session_id": "t", "tool_name": "Bash",
                             "tool_input": {"command": "   "}}))
check("Aufruf ohne Inhalt: Exit 0 ohne Ausgabe", code == 0 and aus == "")

sitzung = "selbsttest-{}".format(id(object()))
rg.statusdatei(sitzung).unlink(missing_ok=True)
nutzlast = json.dumps({"session_id": sitzung, "tool_name": "Read",
                       "tool_input": {"file_path": "app.py"}})
ausgaben = [lauf(nutzlast) for _ in range(4)]
check("echter Hook meldet sich genau einmal",
      [bool(a) for _, a in ausgaben] == [False, False, True, False])
check("alle Laeufe enden mit Exit 0", all(c == 0 for c, _ in ausgaben))
antwort = json.loads(ausgaben[2][1])
check("Ausgabe traegt Kontext fuer das Modell",
      "Abbruchpunkte" in antwort["hookSpecificOutput"]["additionalContext"])
check("Ausgabe blockt nicht (kein decision-Feld)", "decision" not in antwort)
check("kein Temp-Rest nach atomarem Schreiben",
      not list(rg.statusdatei(sitzung).parent.glob("repeat-{}*.tmp".format(sitzung))))
rg.statusdatei(sitzung).unlink(missing_ok=True)

print("\nAlle Repeat-Guard-Tests bestanden.")
