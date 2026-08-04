$in = [Console]::In.ReadToEnd() | ConvertFrom-Json
$f = "$($in.tool_input.file_path)"
if ($f -notmatch '\.py$') { exit 0 }
$py = Join-Path (Get-Location) '.venv\Scripts\python.exe'
if (-not (Test-Path $py)) { exit 0 }
$out = & $py -m py_compile $f 2>&1
if ($LASTEXITCODE -ne 0) {
  $out | ForEach-Object { [Console]::Error.WriteLine("$_") }
  exit 2
}
exit 0
