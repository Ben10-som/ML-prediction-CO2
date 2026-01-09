# Note de Synthèse — Analyse Spatiale et Temporelle des Émissions de GES à Seattle

**Date :** 7 janvier 2026  
**Source :** Notebook 5 - Analyse spatiale et temporelle  
**Auteur :** Équipe d'analyse énergétique



## Objectif

Comprendre comment l'époque de construction, la localisation géographique, les infrastructures énergétiques et les certifications environnementales influencent les émissions de CO₂ des bâtiments non résidentiels de Seattle, en vue d'orienter la modélisation prédictive.



## Principaux Constats

### 1. Déterminants structurels des émissions

Quatre facteurs clés expliquent les variations d'émissions :

- **Surface (GFA)** : Principal moteur du volume global des émissions
- **Réseau de vapeur (Steam)** : Multiplie l'intensité carbone par un facteur significatif
- **Certification ENERGY STAR** : Réduit substantiellement l'intensité des émissions, même pour les bâtiments anciens
- **Époque de construction** : Influence non linéaire — les bâtiments récents sont plus efficaces au m², mais souvent plus grands

### 2. Dynamique temporelle

- **Les bâtiments pré-1950** affichent la plus forte intensité d'émissions (mauvaise isolation, systèmes obsolètes)
- **Les années 2000-2009** présentent paradoxalement les émissions totales les plus élevées en raison de la construction de grandes structures (tours, centres de données)
- **Les constructions 2010-2016** montrent l'intensité carbone la plus faible, confirmant l'impact des normes récentes

### 3. Concentration spatiale

- **Downtown et l'axe Est-Centre** concentrent les émissions les plus importantes
- Le quartier **EAST** présente les émissions moyennes les plus élevées
- Les quartiers périphériques (Southwest, North) affichent des intensités nettement plus faibles

### 4. Impact critique du réseau de vapeur

Les bâtiments raccordés au réseau de vapeur urbain (infrastructure historique, combustibles fossiles) présentent une **intensité d'émissions médiane nettement supérieure** aux bâtiments utilisant l'électricité ou le gaz naturel.

### 5. Efficacité de la certification ENERGY STAR

La certification réduit significativement l'intensité des émissions dans toutes les périodes de construction, mais ne compense pas totalement les contraintes structurelles des bâtiments anciens.



## Recommandations pour la Modélisation

**Variables prédictives prioritaires :**

- Surface totale, type d'usage, année de construction
- Utilisation du réseau de vapeur (variable fortement discriminante)
- Statut de certification ENERGY STAR
- Localisation (quartier/coordonnées géographiques)

**Ne pas utiliser :** Les données de consommation énergétique future (objectif métier : prédire dès la déclaration administrative)

---

## Leviers d'Action Publique

Pour atteindre la neutralité carbone d'ici 2050, cibler en priorité :

1. **Bâtiments du Downtown** (densité + super-émetteurs)
2. **Transition hors du réseau de vapeur** (infrastructure à forte intensité carbone)
3. **Rénovation des bâtiments anciens non certifiés** (potentiel d'amélioration maximal)

---

## Conclusion

Les émissions ne sont pas uniformément réparties mais répondent à des déterminants structurels clairs. La phase de modélisation devra intégrer ces variables explicatives pour produire des prédictions robustes et orienter efficacement les politiques de transition énergétique de Seattle.

---

**Document généré le 7 janvier 2026**