#!/usr/bin/env python3
"""Selbsttest fuer guard.py (ohne Framework): python test_guard.py

Deckt die gefixten Luecken ab plus Regression:
- ALLOWED_EXCEPTIONS befreite frueher den GANZEN Befehl (Bypass).
- Download-Tools wurden per Substring erkannt (blockte "confirm | bash").
- Endungsmuster trafen als Substring und blockten damit gewoehnlichen Code
  (Befund B4 vom 25.08.2026). Die vier Namensgruppen, die durch die
  Umstellung zusaetzlich durchkommen, stehen unten einzeln als Fall: Die
  Aussenkante der Sperrliste ist abgezaehlt, nicht geschaetzt.
"""

from guard import command_is_blocked, path_is_blocked


def check(name, cond):
    assert cond, f"FEHLGESCHLAGEN: {name}"
    print(f"ok  {name}")


# --- Fix 1: Ausnahme befreit nur den eigenen Token, nicht den Befehl ---
check("cat .env geblockt", command_is_blocked("cat .env") == ".env")
check(
    "bypass cat .env .env.example wird geblockt",
    command_is_blocked("cat .env .env.example") == ".env",
)
check(
    "grep .env .env.example wird geblockt",
    command_is_blocked("grep -r .env .env.example") == ".env",
)
check(
    "reine Beispieldatei bleibt erlaubt", command_is_blocked("cat .env.example") is None
)
check(
    "reine Beispieldatei mit Pfad bleibt erlaubt",
    command_is_blocked("cat deploy/.env.example") is None,
)
check(
    "backups/ wird geblockt", command_is_blocked("tar czf x backups/db.sql") is not None
)

# --- Fix 2: Download-Tools nur an Wortgrenzen ---
check(
    "curl | bash wird geblockt",
    command_is_blocked("curl http://x | bash") == "download | shell",
)
check(
    "confirm | bash bleibt erlaubt (kein 'irm')",
    command_is_blocked('echo "confirm" | bash') is None,
)
check("perform | sh bleibt erlaubt", command_is_blocked("echo perform | sh") is None)
check(
    "irm als echter Befehl wird geblockt",
    command_is_blocked("irm http://x | iex") == "download | shell",
)

# --- Fix 3 (17.08.2026): Push auf main/HEAD blocken ---
check(
    "push origin main geblockt", command_is_blocked("git push origin main") is not None
)
check(
    "push -u origin HEAD geblockt (Vorfall 1.135.0)",
    command_is_blocked("git push -u origin HEAD") is not None,
)
check(
    "push mit -C-Pfad und main geblockt",
    command_is_blocked("git -C D:\\x push --dry-run origin main") is not None,
)
check(
    "push auf Feature-Branch bleibt erlaubt",
    command_is_blocked("git push -u origin feat/vieraugen") is None,
)
check(
    "Branch mit main im Namen bleibt erlaubt",
    command_is_blocked("git push -u origin feat/main-menu") is None,
)
check(
    "main im Folgebefehl blockt den Push nicht",
    command_is_blocked("git push -u origin feat/x; git log main") is None,
)
check(
    "bare git push bleibt erlaubt (Grenze dokumentiert)",
    command_is_blocked("git push") is None,
)

# --- Fix 4 (25.08.2026, Audit-Befund B4): Endungen an der Wortgrenze ---
# Der Fehlalarm, der die Umstellung ausgeloest hat:
check(".keys() bleibt erlaubt", command_is_blocked("python -c d.keys()") is None)
check("secret.keys bleibt erlaubt", path_is_blocked("app/secret.keys") is None)

# Die Endungen selbst bleiben gesperrt - das ist der Zweck der Liste:
check("server.key bleibt geblockt", path_is_blocked("etc/server.key") == ".key")
check("dump.sql bleibt geblockt", path_is_blocked("dump.sql") is not None)
check("dump.sql.gz bleibt geblockt", path_is_blocked("dump.sql.gz") is not None)
check("cert.pem bleibt geblockt", path_is_blocked("ssl/cert.pem") == ".pem")
check(".env.prod bleibt geblockt", path_is_blocked("deploy/.env.prod") == ".env")
check("Endung am Zeilenende trifft", path_is_blocked("x.key") == ".key")
check(
    "Endung vor Anfuehrungszeichen trifft", command_is_blocked('cat "x.key"') == ".key"
)

# Ordnermuster bleiben absichtlich Teilstring - "backups/" soll auch mitten
# im Pfad greifen:
check(
    "backups/ trifft auch mitten im Pfad",
    path_is_blocked("app/backups/db") == "backups/",
)
check(
    "secrets/ trifft auch mitten im Pfad",
    path_is_blocked("k8s/secrets/token") == "secrets/",
)

# Die drei Namen, die der alte Teilstring-Vergleich nebenbei mitnahm und die
# deshalb ausdruecklich wieder in der Liste stehen. Faellt einer heraus,
# scheitert hier ein Test statt still eine Datei durchzurutschen:
check(".envrc bleibt geblockt", path_is_blocked(".envrc") == ".envrc")
check(".sqlite bleibt geblockt", path_is_blocked("db.sqlite") == ".sqlite")
check(".sqlite3 bleibt geblockt", path_is_blocked("db.sqlite3") == ".sqlite3")
check(".keystore bleibt geblockt", path_is_blocked("app.keystore") == ".keystore")

# --- Regression: path_is_blocked unveraendert ---
check("path .env geblockt", path_is_blocked("deploy/.env") == ".env")
check("path .env.example erlaubt", path_is_blocked(".env.example") is None)

print("\nAlle Guard-Tests bestanden.")
