$in = [Console]::In.ReadToEnd() | ConvertFrom-Json
$cmd = "$($in.tool_input.command)"
if ($cmd -notmatch 'git(\s+-C\s+\S+)?\s+commit') { exit 0 }
if (-not (Test-Path 'CHANGELOG.md')) { exit 0 }
$staged = git diff --cached --name-only
if ($staged -notcontains 'CHANGELOG.md') {
  [Console]::Error.WriteLine("Blockiert: CHANGELOG.md ist nicht gestaged. Erst VERSION erhoehen und CHANGELOG.md ergaenzen, beides stagen, dann committen (Versionierungspflicht des Projekts).")
  exit 2
}
exit 0
