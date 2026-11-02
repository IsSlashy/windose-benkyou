<#
Copie les voix de KAngel et Ame (générées sur ce PC) dans le dossier voix à côté
d'Exporter-voix.cmd, pour les emporter sur un autre PC avec une clé USB ou un disque.
Installer.cmd les reprend ensuite tout seul.

Les voix restent chez toi : ne mets jamais ce dossier dans le repo ni en ligne.
#>
param([string]$AnkiBase = "$env:APPDATA\Anki2")
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$src = Join-Path $AnkiBase "addons21\windose_benkyou\user_files\voices"
$dst = Join-Path $root "voix"
if (-not (Test-Path $src)) { throw "Aucune voix trouvée dans $src." }
$null = robocopy $src $dst /E /NFL /NDL /NJH /NJS /NP
if ($LASTEXITCODE -ge 8) { throw "La copie a échoué (robocopy $LASTEXITCODE)." }
$files = @(Get-ChildItem $dst -Recurse -Filter *.mp3)
$mb = [math]::Round(($files | Measure-Object Length -Sum).Sum / 1MB)
Write-Host "Voix copiées dans $dst : $($files.Count) clips, $mb Mo." -ForegroundColor Green
Get-ChildItem $dst -Directory | ForEach-Object {
  Write-Host ("   {0} : {1} clips" -f $_.Name, @(Get-ChildItem $_.FullName -Filter *.mp3).Count)
}
Write-Host "Garde ce dossier à côté d'Installer.cmd. Il ne doit jamais aller dans le repo ni en ligne."
