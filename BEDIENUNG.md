# claude-guards — Bedienung

Die Guards laufen im Hintergrund; du bedienst sie nicht, du stößt an sie. Diese
Anleitung erklärt, **warum** etwas blockiert wurde und was dann zu tun ist.

> **Stand:** 25.08.2026 · geprüft gegen den Quelltext dieses Repos.

## Was es tut

Zwei Plugins hängen sich in Claude Code ein und ziehen Grenzen, an die sich ein
disziplinierter Entwickler ohnehin halten würde — nur ohne dass du jede Sitzung
überwachen musst.

| Plugin | Hook | Wirkung |
|---|---|---|
| sicherheits-guard | `guard.py` | blockt Zugriffe auf sensible Dateien und gefährliche Befehle |
| dev-guards | `commit-guard.ps1` | blockt `git commit` ohne gestagtes `CHANGELOG.md` |
| dev-guards | `py-check.ps1` | kompiliert jede geänderte `.py` und meldet Syntaxfehler sofort |
| dev-guards | `repeat-guard.py` | erinnert beim dritten identischen Werkzeugaufruf an die Abbruchpunkte-Regel |

Die Hooks registrieren sich bei der Installation selbst — `settings.json` bleibt
unangetastet.

## Wenn etwas blockiert wurde

**„Blockiert: CHANGELOG.md ist nicht gestaged."**
`CHANGELOG.md` steht nicht in `git diff --cached`. Version erhöhen, Changelog
ergänzen, **beides** stagen, dann committen.
(`commit-guard.ps1`: `if ($staged -notcontains 'CHANGELOG.md') {`)

Zwei Fallen dabei:

- `git add` und `git commit` **getrennt** absetzen. In einem verketteten Befehl
  prüft der Hook den Stand *vor* dem `add`.
- Der Hook bezieht sich auf das Repo, auf das sich der Commit bezieht — bei
  `git -C <dir> commit` also auf `<dir>`. Blockiert er trotzdem im falschen
  Verzeichnis, läuft eine veraltete Fassung: siehe „Version prüfen" unten.

**„Vom Sicherheits-Guard geblockt (…)"**
Der Pfad oder Befehl trifft ein Sperrmuster. Erlaubt bleiben ausdrücklich
`.env.example` und Geschwister.

Wie streng verglichen wird, hängt seit 1.2.0 von der Art des Musters ab:

- **Endungen** (`.key`, `.env`, `.sql`, `.pem`) treffen nur an der Wortgrenze.
  `server.key` ist gesperrt, `d.keys()` nicht mehr.
- **Ordner und Namen** (`backups/`, `secrets/`, `id_rsa`) bleiben
  Teilstring-Vergleiche und treffen auch mitten im Pfad.

Was bleibt: Der Vergleich läuft über den **ganzen** Befehlstext. Ein `grep` nach
einem gesperrten Mustertext blockiert deshalb weiterhin. Das ist kein Versehen —
sonst genügte ein Anführungszeichen, um einen Zugriff zu tarnen. Dann den Befehl
umformulieren oder den Suchbegriff aus Teilstücken zusammensetzen.
(`guard.py`: `"Vom Sicherheits-Guard geblockt ({reason}). "`)

**Push auf `main` oder `HEAD` blockiert**
Absicht: Feature-Branch und PR. Namen wie `feat/main-menu` bleiben erlaubt, die
Erkennung ist auf das Wort begrenzt.
(`guard.py`: `PUSH_MAIN_RE = re.compile(`)

**Syntaxfehler nach Edit oder Write**
`py-check` hat die Datei mit dem venv-Python kompiliert und die Fehlerzeilen
ausgegeben. Greift nur, wenn das Projekt eine `.venv` hat — sonst passiert
nichts.
(`py-check.ps1`: `if (-not (Test-Path $py)) { exit 0 }`)

**„Dritter identischer …-Aufruf in dieser Sitzung"**
Kein Block, nur eine Erinnerung, und nur einmal je Signatur. Die Signatur bildet
sich aus Werkzeugname und Kern der Parameter.
(`repeat-guard.py`: `SCHWELLE = 3`)

## Version prüfen

Der `commit-guard` wurde repariert (`-C <dir>` wird ausgewertet, Regex am
Zeilenanfang verankert) — der Fix steckt in **dev-guards 1.0.1**. Eine ältere
Installation prüft `CHANGELOG.md` stattdessen relativ zum Arbeitsverzeichnis der
Shell und blockiert dann Commits in *andere* Repos.

Installierte Fassung: `~/.claude/plugins/cache/claude-guards/dev-guards/<version>/`.
Steht dort `1.0.0`, dann aktualisieren:

```
claude plugin marketplace update claude-guards
claude plugin update dev-guards@claude-guards
```

Danach eine neue Sitzung starten.

## Grenzen

- **`permissions.deny` kann ein Plugin nicht setzen.** Wer die zusätzlichen
  Regeln will, trägt sie von Hand in `settings.json` ein.
- **`repeat-guard` blockt nie** — er erinnert nur und endet immer mit 0.
- **`commit-guard` greift nur** in Projekten mit `CHANGELOG.md`.
- **`py-check` greift nur** in Projekten mit `.venv`.
- **Der Guard sieht nur bekannte Werkzeuge.** Was nicht in `FILE_TOOLS` oder
  `COMMAND_TOOLS` steht, läuft ungeprüft durch.
  (`guard.py`: `COMMAND_TOOLS = {"Bash", "PowerShell"}`)
- **Die Sperrlisten sind statisch.** Neue Datei- oder Befehlsmuster erkennt der
  Guard erst, wenn sie in `guard.py` stehen.
- **Kaputte Eingabe blockiert nicht.** Lässt sich die Hook-Eingabe nicht lesen,
  endet der Guard mit 0 und der Ablauf geht normal weiter — bewusst so, damit
  ein Fehler im Guard nicht die Arbeit lahmlegt.

## Installation

```
claude plugin marketplace add maumke92/claude-guards
claude plugin install dev-guards@claude-guards
claude plugin install sicherheits-guard@claude-guards
```

Danach neue Sitzung. Zum Entwickeln stattdessen den lokalen Klon als
Marketplace angeben.

---

*Erzeugt mit `/anleitung` (Entwurf vom lokalen Qwen, geprüft gegen den
Quelltext und die installierte Fassung).*
