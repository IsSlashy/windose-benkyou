**Windose Benkyou**, réglages (redémarrer Anki après un changement)

- `simple_mode` : cache les boutons avancés (Difficile, Facile, options). `false` pour tout réafficher.
- `character` : `"kangel"` ou `"ame"`. Se change aussi avec le bouton ⇄ de la fenêtre de live ou le menu Démarrer.
- `window_pos` : position des fenêtres du live et du chat, enregistrée quand tu les déplaces par leur barre de titre. Double-clic sur la barre de titre pour remettre une fenêtre à sa place.
- `voice` : `"character"` pour que KAngel ou Ame lise le mot et la phrase de chaque carte (voix générées en local avec tes propres modèles GPT-SoVITS de KAngel et Ame, dans D:\TTS), `"original"` pour les enregistrements d'origine (NHK, JLPT Tango). Se change aussi dans le menu Démarrer. Une carte dont la voix n'est pas encore générée garde la voix d'origine.
- `quiz` : avant la correction, tape le sens en français et la lecture en romaji (changée en hiragana). `false` pour revenir à « Afficher la réponse ».
- `quiz_fields` : les champs de la note utilisés pour vérifier et pour l'explication (Kaishi : Word, Word Meaning, Word Reading, Sentence, Sentence Furigana, Sentence Meaning, Notes). Les cartes JLPT Tango (type « Japanese sentences ») ont leurs propres champs, réglés dans le module : la carte montre une phrase, et on donne le sens et la lecture du mot en rose. Pour un mot à plusieurs lectures (開く : あく ou ひらく), chacune est acceptée.
- « Je ne sais pas », ou Entrée sans rien écrire, donne l'état orange « À apprendre » : KAngel ou Ame explique la carte, et Entrée la remet pour plus tard. Une réponse écrite mais fausse reste en rouge « Pas tout à fait ».
- `wallpaper` : `"windose"` (le bureau du jeu) ou `"nso"` (le fond de ton thème Chrome Needy Streamer Overload clair).
- `taskbar` : la barre des tâches Windose en bas de l'accueil.
- `stream` : la fenêtre de live avec KAngel et les statistiques du jour pendant les révisions.
- `chat` : les commentaires du chat (japonais avec la traduction).
- `sounds` : les sons du pack GX. `sound_files` choisit quel son pour quel moment, parmi : piporo, poko, sippai, Tetehen, status_up, status_down, result_start, kari (`learn` sert pour « À apprendre »).
- `window_chrome` : barre de titre, menu et icône aux couleurs de Windose.
- `window_title` : le titre de la fenêtre.
- `rename_default_deck_to` : nom donné au paquet Kaishi s'il est arrivé dans « Par défaut ».
- « Étudier » dans le menu Démarrer ouvre le dernier paquet choisi (Kaishi 1.5k ou JLPT Tango). Clique un paquet dans la liste pour changer.
- JLPT Tango : sens et phrases traduits en français, l'anglais d'origine reste dans la case « English » au dos. Les mots que Kaishi enseigne déjà sont suspendus avec l'étiquette doublon_kaishi (Parcourir, tag:doublon_kaishi, Réactiver pour les remettre).

Images, polices et sons viennent du jeu et de ton pack GX : usage personnel, ne pas partager ce dossier.

Voix : tes modèles GPT-SoVITS personnels (KAngel, Ame), générés en local. Usage strictement personnel, ne pas republier. Les fichiers sont dans user_files/voices (hors de collection.media, donc jamais synchronisés). Chaque dossier a un _report.txt (Kaishi) et un _report_tango.txt (JLPT Tango) : les clips refusés au contrôle gardent la voix d'origine.
