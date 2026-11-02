# べんきょう.exe : Windose Benkyou

Mon Anki pour apprendre le japonais, du JLPT N5 au N2, habillé en Windose 20 avec les vrais éléments de NEEDY GIRL OVERDOSE. KAngel ou Ame m'accompagnent pendant les révisions.

Repo privé, usage personnel uniquement : les images et les sons viennent du jeu. Il ne doit jamais devenir public.

## Installer sur un PC

1. Sur la page [Releases](../../releases) du repo, télécharge `WindoseBenkyou-Setup.zip` (connecté à GitHub, puisque le repo est privé).
2. Décompresse tout le zip, puis double-clique `Installer.cmd`.
3. Anki se lance et importe les paquets tout seul, en une minute environ.

Avec la ligne de commande GitHub (`gh`) déjà connectée, une seule commande PowerShell suffit :

```powershell
$d = "$env:TEMP\windose"; gh release download --repo IsSlashy/windose-benkyou --pattern "*.zip" --dir $d --clobber; Expand-Archive "$d\WindoseBenkyou-Setup.zip" $d -Force; & "$d\WindoseBenkyou-Setup\Installer.cmd"
```

Ce que fait `Installer.cmd` :

- installe Anki 26.9.3 avec winget s'il manque ;
- copie chaque collection existante dans `%APPDATA%\Anki2\sauvegarde-installeur` ;
- installe Onigiri 2.0.2 avec mes réglages (seulement s'il n'est pas déjà là) et l'add-on Windose Benkyou ;
- pose les paquets dans `windose_benkyou\user_files\setup`. Au premier lancement, l'add-on importe ce qui manque (`first_run.py`), donne à JLPT Tango son propre rythme (10 nouvelles cartes par jour) et met de côté les mots que Kaishi enseigne déjà (étiquette `doublon_kaishi`) ;
- reprend les voix si un dossier `voix` est posé à côté de `Installer.cmd`.

Relancer `Installer.cmd` met l'add-on à jour sans toucher aux réglages (`meta.json`), aux voix (`user_files`) ni aux cartes déjà là.

## Les voix de KAngel et Ame

Elles sont générées sur mon PC avec mes propres modèles GPT-SoVITS (`D:\TTS`). Elles ne quittent jamais la maison : jamais dans ce repo, jamais en ligne, et le `.gitignore` les bloque.

Pour les emporter : `Exporter-voix.cmd` les copie dans un dossier `voix`. Ce dossier voyage sur une clé USB ou un disque, et `Installer.cmd` le reprend sur l'autre PC. Sans lui, les cartes jouent l'audio d'origine.

Pour les régénérer : `tools/voicegen/sovits_voicegen.py`, lancé dans le venv GPT-SoVITS à basse priorité avec `D:\TTS\tools\scripts\run-low.ps1`, jamais pendant que l'appli de voix en direct tourne.

## Contenu

| Dossier | Rôle |
| --- | --- |
| `addon/windose_benkyou` | l'add-on : thème, quiz « こたえ.exe », stream et chat, voix, premier lancement |
| `installer` | `install.ps1`, `export-voices.ps1`, le texte du zip |
| `tools/release.ps1` | construit `WindoseBenkyou-Setup.zip` et le publie dans une Release privée |
| `tools/tango` | construction du paquet JLPT Tango FR (traductions dans `tr_out`) |
| `tools/assets` | extraction des images du jeu avec UnityPy |
| `tools/voicegen` | génération des voix |
| `tools/tests` | test de l'import du premier lancement |
| `tools/dev` | visite automatique de l'interface et captures de la fenêtre Anki |

Les paquets `.apkg` (plus de 100 Mo chacun) et Onigiri ne sont pas dans le code : ils sont dans le zip de la Release.

## Publier une nouvelle version

```powershell
.\tools\release.ps1 -Kaishi <Kaishi.1.5k.fr.apkg> -Tango <jlpt_tango_fr.apkg> -Version v1.0.1 -Upload
```

## Sources des cartes

- Kaishi 1.5k FR v1.0.1 : [khmskhmskhms/kaishi-FR](https://github.com/khmskhmskhms/kaishi-FR/releases), téléchargé le 2 novembre 2026.
- JLPT Tango N4, N3, N2 : Ankidrone Essentials V9 (fichier daté du 22 août 2026, téléchargé le 2 novembre 2026). Sens et phrases traduits en français par IA et relus sur un échantillon seulement. L'anglais d'origine reste au dos de la carte, dans la case « English ».
