<#
Construit dist\WindoseBenkyou-Setup.zip (tout ce qu'il faut pour Installer.cmd) et,
avec -Upload, le met dans une Release du repo privé GitHub.

Le zip contient : Installer.cmd, Exporter-voix.cmd, installer\, addon\, onigiri\
(copié depuis l'Anki de ce PC, sans tes stats perso) et paquets\ (les deux .apkg).
Il ne contient jamais les voix : elles restent sur tes disques.

Exemple :
  .\tools\release.ps1 -Kaishi <Kaishi.1.5k.fr.apkg> -Tango <jlpt_tango_fr.apkg> -Version v1.0.0 -Upload
#>
param(
  [Parameter(Mandatory = $true)][string]$Kaishi,
  [Parameter(Mandatory = $true)][string]$Tango,
  [string]$Onigiri = "$env:APPDATA\Anki2\addons21\1011095603",
  [string]$Version = "v1.0.0",
  [string]$Repo = "IsSlashy/windose-benkyou",
  [switch]$Upload
)
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$dist = Join-Path $root "dist"
$out = Join-Path $dist "WindoseBenkyou-Setup"
$zip = Join-Path $dist "WindoseBenkyou-Setup.zip"
foreach ($f in @($Kaishi, $Tango, "$Onigiri\__init__.py")) { if (-not (Test-Path $f)) { throw "Introuvable : $f" } }

Remove-Item $out, $zip -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force "$out\paquets", "$out\onigiri" | Out-Null
Copy-Item "$root\Installer.cmd", "$root\Exporter-voix.cmd", "$root\installer\LISEZMOI.txt" $out
Copy-Item "$root\installer" $out -Recurse
Remove-Item "$out\installer\LISEZMOI.txt"
Copy-Item "$root\addon" $out -Recurse
Get-ChildItem "$out\addon" -Recurse -Force | Where-Object { $_.Name -in @("__pycache__", "user_files", "meta.json") } |
  Remove-Item -Recurse -Force

# Onigiri tel qu'il tourne ici, sans les stats perso ni le cache.
Copy-Item $Onigiri "$out\onigiri\1011095603" -Recurse
$oniUser = "$out\onigiri\1011095603\user_files"
Get-ChildItem $oniUser -Force -ErrorAction SilentlyContinue |
  Where-Object { $_.Name -like "gamification_*" -or $_.Name -eq "_qss_icon_cache" } | Remove-Item -Recurse -Force
Get-ChildItem "$out\onigiri" -Recurse -Directory -Filter __pycache__ | Remove-Item -Recurse -Force
# Réglages Onigiri : le profil s'appelle « Utilisateur 1 » en français, « User 1 » en anglais.
$prof = Join-Path $oniUser "settings_Utilisateur 1.json"
if (Test-Path $prof) { Copy-Item $prof (Join-Path $oniUser "settings_User 1.json") }

Copy-Item $Kaishi "$out\paquets\Kaishi.1.5k.fr.apkg"
Copy-Item $Tango "$out\paquets\jlpt_tango_fr.apkg"

# Garde-fou : aucune voix dans le zip.
# (les clips s'appellent <20 caractères hexa>.mp3 et vivent dans voices\ ; Onigiri a ses propres petits sons)
$leak = @(Get-ChildItem $out -Recurse -Force | Where-Object {
  ($_.PSIsContainer -and $_.Name -in @("voices", "voix")) -or $_.Name -match '^[0-9a-f]{20}\.mp3$' })
if ($leak.Count) { throw "Des voix se sont glissées dans le zip ($($leak.Count) éléments) : arrêt." }

Push-Location $dist
try { tar -a -c -f "WindoseBenkyou-Setup.zip" "WindoseBenkyou-Setup" } finally { Pop-Location }
if ($LASTEXITCODE -ne 0) { throw "La création du zip a échoué." }
$mb = [math]::Round((Get-Item $zip).Length / 1MB)
Write-Host "Zip prêt : $zip ($mb Mo)"

if ($Upload) {
  $notes = "Installation en un clic : télécharge WindoseBenkyou-Setup.zip, décompresse-le, double-clique Installer.cmd. Les voix ne sont pas incluses."
  gh release view $Version --repo $Repo *> $null
  if ($LASTEXITCODE -eq 0) {
    gh release upload $Version $zip --repo $Repo --clobber
  } else {
    gh release create $Version $zip --repo $Repo --title "Windose Benkyou $Version" --notes $notes
  }
  if ($LASTEXITCODE -ne 0) { throw "L'envoi sur GitHub a échoué." }
  Write-Host "Release $Version à jour sur $Repo."
}
