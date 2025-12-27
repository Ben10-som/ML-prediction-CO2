# Data du projet

Ce dossier contient l’ensemble des données utilisées dans le projet.  
Les fichiers de données brutes ne sont pas versionnés avec DVC afin de limiter la complexité du projet et 
de concentrer nos éforts sur les aspect de modelisation.  
Seuls les scripts de traitement et de transformation sont versionnés par git pour garantir la traçabilité et la reproductibilité.

## Structure

- raw/ : données brutes, non modifiées
- interim/ : données intermédiaires générées lors des étapes de nettoyage
- processed/ : données finales prêtes pour l’analyse et la modélisation (feature ingeniering)

## Règles

- Les fichiers bruts doivent être placés uniquement dans `raw/`.
- Toute transformation ou nettoyage doit être effectuée via les scripts du répertoire `src/data`.
- Les résultats intermédiaires doivent être stockés dans `interim/`.
- Les données finales validées doivent être placées dans `processed/`.
- Les scripts, et non les fichiers de données, assurent la reproductibilité et sont versionnés dans le dépôt.
