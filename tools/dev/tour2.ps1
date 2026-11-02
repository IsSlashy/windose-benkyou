param([string]$Tag = "w1", [switch]$Install, [string]$Deck = "go")
# Closes Anki, optionally installs the scratchpad build of windose_benkyou
# (moving the old vaporwave_benkyou out of addons21), then runs the dev tour
# and captures the Anki window at each phase.
$s = "C:\Users\Slashy\AppData\Local\Temp\claude\E--Spout\833300c1-4689-401b-add4-b9a74deccf32\scratchpad"
$addons = "$env:APPDATA\Anki2\addons21"
$addon = "$addons\windose_benkyou"
$p = Get-Process anki -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowHandle -ne 0 } | Select-Object -First 1
if ($p) { $null = $p.CloseMainWindow(); $null = $p.WaitForExit(30000) }
if (Get-Process anki -ErrorAction SilentlyContinue) { "Anki still running"; exit 1 }
if ($Install) {
  if (Test-Path "$addons\vaporwave_benkyou") {
    Remove-Item "$s\backup_vaporwave_benkyou" -Recurse -Force -ErrorAction SilentlyContinue
    Move-Item "$addons\vaporwave_benkyou" "$s\backup_vaporwave_benkyou"
  }
  # user_files holds the generated voices (possibly being written right now):
  # replace everything else and never touch it.
  New-Item -ItemType Directory -Force $addon | Out-Null
  # meta.json holds Ramy's own settings (character, voice, window positions): keep it too.
  Get-ChildItem $addon -Force | Where-Object { $_.Name -notin @("user_files", "meta.json") } | Remove-Item -Recurse -Force
  Get-ChildItem "$s\windose_benkyou" -Force | Where-Object { $_.Name -ne "user_files" } |
    Copy-Item -Destination $addon -Recurse -Force
}
Remove-Item "$addon\dev" -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force "$addon\dev" | Out-Null
Set-Content "$addon\dev_tour.flag" $Deck -Encoding utf8
Start-Process -FilePath "$env:LOCALAPPDATA\Programs\Anki\Anki.exe"
$last = ""
$deadline = (Get-Date).AddSeconds(150)
while ((Get-Date) -lt $deadline) {
  Start-Sleep -Milliseconds 700
  $ph = (Get-Content "$addon\dev\phase.txt" -ErrorAction SilentlyContinue) -join ""
  if ($ph -and $ph -ne $last) {
    $last = $ph
    if ($ph -eq "done") { break }
    Start-Sleep -Milliseconds 1500
    & "$s\capture-anki.ps1" -Out "$s\shot-$Tag-$ph.png"
  }
}
"phases done: $last"
Get-Content "$addon\dev\log.txt" -ErrorAction SilentlyContinue
