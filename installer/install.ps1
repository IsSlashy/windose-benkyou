<#
Installe d'un coup : Anki, Onigiri, l'add-on Windose Benkyou et les paquets
Kaishi 1.5k FR et JLPT Tango FR (N4, N3, N2). Lancé par Installer.cmd.

Sans danger sur un PC déjà installé :
  - les réglages (meta.json) et les voix (user_files) de l'add-on ne sont jamais touchés ;
  - Onigiri déjà présent est laissé tel quel ;
  - un paquet déjà présent dans Anki n'est pas importé une seconde fois ;
  - chaque collection existante est copiée dans <Anki2>\sauvegarde-installeur avant tout.

Options (pour les tests) :
  -AnkiBase <dossier>  dossier de données d'Anki (par défaut %APPDATA%\Anki2)
  -SkipAnkiInstall     ne pas installer Anki s'il manque
  -NoLaunch            ne pas lancer Anki à la fin
  -Yes                 ne poser aucune question
#>
param(
  [string]$AnkiBase = "$env:APPDATA\Anki2",
  [switch]$SkipAnkiInstall,
  [switch]$NoLaunch,
  [switch]$Yes
)
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$AnkiExe = "$env:LOCALAPPDATA\Programs\Anki\anki.exe"
$AnkiVersion = "26.9.3"   # la version testée avec l'add-on
$OnigiriId = "1011095603"

function Step($text) { Write-Host ""; Write-Host "== $text" -ForegroundColor Magenta }
function Say($text) { Write-Host "   $text" }

$addonSrc = Join-Path $root "addon\windose_benkyou"
$onigiriSrc = Join-Path $root "onigiri\$OnigiriId"
$decksSrc = Join-Path $root "paquets"
$voixSrc = Join-Path $root "voix"
if (-not (Test-Path "$addonSrc\__init__.py")) {
  throw "Le dossier addon\windose_benkyou est introuvable à côté de Installer.cmd. Décompresse tout le zip avant de lancer l'installation."
}
# Fichiers venus d'internet : on enlève la marque « téléchargé » pour qu'Anki puisse les lire sans alerte.
Get-ChildItem $root -Recurse -File -ErrorAction SilentlyContinue | Unblock-File -ErrorAction SilentlyContinue

Write-Host "べんきょう.exe : installation de Windose Benkyou" -ForegroundColor Magenta

# ── 1. Anki ──────────────────────────────────────────────────────────────────
Step "1/5 Anki"
if (Test-Path $AnkiExe) {
  Say "Anki est déjà installé."
} elseif ($SkipAnkiInstall) {
  Say "Anki n'est pas installé, étape sautée (-SkipAnkiInstall)."
} else {
  if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
    throw "winget est introuvable. Installe Anki depuis https://apps.ankiweb.net puis relance Installer.cmd."
  }
  Say "Installation d'Anki $AnkiVersion avec winget…"
  winget install --id Anki.Anki -e --version $AnkiVersion --accept-source-agreements --accept-package-agreements
  if (-not (Test-Path $AnkiExe)) {
    Say "La version $AnkiVersion n'est pas disponible, j'installe la dernière version."
    winget install --id Anki.Anki -e --accept-source-agreements --accept-package-agreements
  }
  if (-not (Test-Path $AnkiExe)) {
    throw "Anki ne s'est pas installé. Installe-le depuis https://apps.ankiweb.net puis relance Installer.cmd."
  }
  Say "Anki est installé."
}

# Anki doit être fermé pendant la copie.
$running = Get-Process anki -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowHandle -ne 0 }
if ($running) {
  if (-not $Yes) {
    $answer = Read-Host "   Anki est ouvert. Je le ferme pour installer ? (O/N)"
    if ($answer -notmatch '^[oOyY]') { throw "Installation annulée : ferme Anki puis relance Installer.cmd." }
  }
  foreach ($p in $running) { $null = $p.CloseMainWindow(); $null = $p.WaitForExit(30000) }
  if (Get-Process anki -ErrorAction SilentlyContinue) { throw "Anki ne s'est pas fermé. Ferme-le puis relance Installer.cmd." }
  Say "Anki est fermé."
}

# ── 2. Sauvegarde ────────────────────────────────────────────────────────────
Step "2/5 Sauvegarde des collections existantes"
New-Item -ItemType Directory -Force $AnkiBase | Out-Null
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$backupDir = Join-Path $AnkiBase "sauvegarde-installeur"
$saved = 0
Get-ChildItem $AnkiBase -Directory | Where-Object { Test-Path (Join-Path $_.FullName "collection.anki2") } | ForEach-Object {
  New-Item -ItemType Directory -Force $backupDir | Out-Null
  foreach ($suffix in @("", "-wal")) {
    $src = Join-Path $_.FullName "collection.anki2$suffix"
    if (Test-Path $src) { Copy-Item $src (Join-Path $backupDir "$($_.Name)-$stamp.anki2$suffix") }
  }
  $saved++
}
if ($saved) { Say "$saved profil(s) copié(s) dans $backupDir" } else { Say "Aucune collection existante : rien à sauvegarder." }

# ── 3. Add-ons ───────────────────────────────────────────────────────────────
Step "3/5 Add-ons"
$addons = Join-Path $AnkiBase "addons21"
New-Item -ItemType Directory -Force $addons | Out-Null

$oni = Join-Path $addons $OnigiriId
if (Test-Path "$oni\__init__.py") {
  Say "Onigiri est déjà installé, je n'y touche pas."
} elseif (Test-Path "$onigiriSrc\__init__.py") {
  Copy-Item $onigiriSrc $oni -Recurse -Force
  Say "Onigiri installé."
} else {
  Say "Onigiri manque dans le zip : à installer depuis Outils > Modules, code $OnigiriId."
}

$wb = Join-Path $addons "windose_benkyou"
New-Item -ItemType Directory -Force $wb | Out-Null
# Tout est remplacé sauf user_files (les voix) et meta.json (tes réglages).
Get-ChildItem $wb -Force | Where-Object { $_.Name -notin @("user_files", "meta.json") } | Remove-Item -Recurse -Force
Get-ChildItem $addonSrc -Force | Where-Object { $_.Name -notin @("user_files", "meta.json", "__pycache__") } |
  Copy-Item -Destination $wb -Recurse -Force
New-Item -ItemType Directory -Force "$wb\user_files" | Out-Null
Say "Windose Benkyou installé."

# ── 4. Paquets de cartes ─────────────────────────────────────────────────────
Step "4/5 Paquets de cartes"
$setup = Join-Path $wb "user_files\setup"
New-Item -ItemType Directory -Force $setup | Out-Null
Remove-Item (Join-Path $setup "done.json") -ErrorAction SilentlyContinue
$decks = @(Get-ChildItem $decksSrc -Filter *.apkg -ErrorAction SilentlyContinue)
foreach ($d in $decks) { Copy-Item $d.FullName $setup -Force; Say "$($d.Name) prêt." }
if ($decks.Count) {
  Say "Anki les importera tout seul au premier lancement (environ une minute)."
  Say "Un paquet déjà présent dans Anki n'est pas importé une seconde fois."
} else {
  Say "Aucun paquet dans le dossier paquets : étape sautée."
}

# ── 5. Voix ──────────────────────────────────────────────────────────────────
Step "5/5 Voix de KAngel et Ame"
if (Test-Path $voixSrc) {
  $null = robocopy $voixSrc (Join-Path $wb "user_files\voices") /E /XC /XN /XO /NFL /NDL /NJH /NJS /NP
  if ($LASTEXITCODE -ge 8) { throw "La copie des voix a échoué (robocopy $LASTEXITCODE)." }
  $n = @(Get-ChildItem (Join-Path $wb "user_files\voices") -Recurse -Filter *.mp3).Count
  Say "Voix copiées depuis le dossier voix : $n clips en place."
} else {
  Say "Pas de dossier voix à côté de l'installeur : les cartes gardent l'audio d'origine."
  Say "Les voix ne sont jamais dans le repo. Sur l'ancien PC, lance Exporter-voix.cmd,"
  Say "puis copie le dossier voix ici (clé USB ou disque) et relance Installer.cmd."
}

Write-Host ""
Write-Host "C'est prêt." -ForegroundColor Green
if (-not $NoLaunch -and (Test-Path $AnkiExe)) {
  Say "Je lance Anki. Au premier lancement, choisis le français si Anki demande la langue."
  Start-Process $AnkiExe
}
