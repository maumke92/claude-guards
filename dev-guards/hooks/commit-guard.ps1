$in = [Console]::In.ReadToEnd() | ConvertFrom-Json
$cmd = "$($in.tool_input.command)"
# Nur echte commit-Aufrufe am Zeilenanfang (nicht z. B. echo "git commit").
if ($cmd -notmatch '^\s*git(\s+-C\s+(?<dir>\S+))?\s+commit\b') { exit 0 }
# Auf das Repo beziehen, auf das sich der commit bezieht (git -C <dir>),
# sonst werden CHANGELOG-Existenz und Diff im falschen Verzeichnis geprueft.
$dir = $Matches['dir']
if ($dir) { $dir = $dir.Trim('"' + "'") }
$changelog = if ($dir) { Join-Path $dir 'CHANGELOG.md' } else { 'CHANGELOG.md' }
if (-not (Test-Path $changelog)) { exit 0 }
if ($dir) { $staged = git -C $dir diff --cached --name-only }
else      { $staged = git diff --cached --name-only }
if ($staged -notcontains 'CHANGELOG.md') {
  [Console]::Error.WriteLine("Blockiert: CHANGELOG.md ist nicht gestaged. Erst VERSION erhoehen und CHANGELOG.md ergaenzen, beides stagen, dann committen (Versionierungspflicht des Projekts).")
  exit 2
}
exit 0
