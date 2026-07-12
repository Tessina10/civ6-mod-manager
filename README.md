# Civ6 Mod Bridge

Une application pour partager et installer des mods Civilization VI entre un
ami en version **Steam** et un ami en version **Epic Games** (ou toute autre
version), sans passer par un serveur — le partage se fait via un lien
généré automatiquement (upload sur [Pixeldrain](https://pixeldrain.com)),
avec des méthodes manuelles de secours (JSON, presse-papiers, archive `.zip`).

> Anciennement "Civ 6 Mod Manager", composé de deux outils Tkinter séparés.
> Fusionné en une seule application PySide6, bilingue FR/EN. Voir `CLAUDE.md`
> pour le détail de l'architecture.

## Utilisation

L'application a deux onglets :

- **Envoyer** — à utiliser sur le PC qui a la version **Steam**. Scanne les
  mods souscrits via le Steam Workshop et permet de les envoyer
  automatiquement à un ami via un simple lien, ou de zipper les fichiers
  manuellement / d'exporter une liste JSON / des liens Workshop à transmettre
  soi-même (bouton "Options avancées" sous les onglets).
- **Recevoir** — à utiliser sur n'importe quelle installation. Colle le lien
  reçu et clique sur "Installer les mods" pour tout télécharger et installer
  automatiquement dans le dossier Mods ; permet aussi de voir les mods déjà
  installés ou d'importer une archive `.zip` reçue à la main.

La langue (français/anglais) se change à tout moment via le sélecteur dans le
coin des onglets, sans redémarrer l'application.

### Configurer l'envoi par lien (Pixeldrain)

1. Crée un compte gratuit sur https://pixeldrain.com (bouton "Register").
2. Une fois connecté, va sur https://pixeldrain.com/user/api_keys et génère
   une clé API.
3. Dans l'onglet "Envoyer", ouvre "Options avancées" → "Pixeldrain" → "Clé
   API...", colle la clé, "Enregistrer". Elle est stockée localement et
   n'est utile que pour l'envoi — la personne qui reçoit n'a besoin d'aucun
   compte.
4. Les fichiers envoyés sont conservés 60 jours (délai prolongé à chaque
   téléchargement), jusqu'à 20 Go par fichier en version gratuite. Le menu
   "Options avancées" → "Pixeldrain" → "Gérer mes envois..." permet de
   lister/supprimer les fichiers déjà envoyés sur le compte.

Note : le téléchargement automatique via SteamCMD a été envisagé puis
abandonné — le Workshop de Civilization VI nécessite une clé de
déchiffrement liée à un compte Steam possédant réellement le jeu, ce qui
rend le login anonyme inutilisable pour ce jeu.

## Développement

```
pip install -r requirements.txt -r requirements-dev.txt
cd app && python main.py              # lancer l'application
cd app && pytest                      # tests (logique pure uniquement)
ruff check .                          # lint
cd app && pyinstaller Civ6ModBridge.spec  # build de l'exécutable Windows
```

Voir `CLAUDE.md` pour le détail de l'architecture et des conventions.

## Licence

Ce projet est distribué sous licence [MIT](LICENSE) : utilisation, modification
et redistribution libres (y compris commerciales), à condition de conserver la
mention de copyright d'origine.
