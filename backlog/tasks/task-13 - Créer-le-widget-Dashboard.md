---
id: task-13
title: Créer le widget Dashboard
status: Done
assignee:
  - '@claude'
created_date: '2025-10-13 19:21'
updated_date: '2025-10-13 21:06'
labels: []
dependencies: []
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Créer l'écran principal affichant une vue d'ensemble des 3 chaînes avec leurs stats principales et comparaisons. Utiliser des DataTable et Sparklines pour visualiser les données.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Widget Dashboard créé héritant de Static
- [x] #2 DataTable avec les 3 chaînes (nom, abonnés, vues, vidéos)
- [x] #3 Graphique ASCII sparkline pour tendance abonnés
- [x] #4 Indicateurs de croissance (%, ▲/▼)
- [x] #5 Sélection d'une chaîne pour voir les détails
- [x] #6 Raccourci 'r' pour rafraîchir les données
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Ajouter plotext aux dépendances pour les graphiques
2. Créer le fichier src/widgets.py avec 3 widgets:
   - DashboardWidget: DataTable avec colonnes structurées
   - ChannelDetailWidget: Vue détaillée d'une chaîne
   - VideoListWidget: Liste triable des vidéos
3. Implémenter les sparklines ASCII pour les tendances
4. Ajouter les indicateurs de croissance (%, ▲/▼)
5. Intégrer les widgets dans app.py
6. Ajouter la navigation interactive (Enter, ESC, v, d)
7. Mettre à jour le CSS pour styliser les DataTables
8. Reconstruire l'image Docker avec les nouvelles dépendances
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Dashboard dynamique créé avec succès avec DataTable, sparklines et navigation interactive.

**Fichiers créés:**
- src/widgets.py (nouveau fichier avec 3 widgets)

**Fichiers modifiés:**
- requirements.txt: ajout de plotext==5.2.8
- src/app.py: intégration des widgets, nouvelles actions de navigation, CSS mis à jour

**Fonctionnalités implémentées:**

1. **DashboardWidget:**
   - DataTable avec 6 colonnes: Channel, Subscribers, Total Views, Videos, Trend, Growth
   - Sparklines ASCII (15 caractères) pour visualiser les tendances
   - Indicateurs de croissance avec couleurs (▲ vert/jaune selon %)
   - Statistiques sommaires en bas (totaux agrégés)
   - Sélection interactive avec curseur

2. **ChannelDetailWidget:**
   - Vue détaillée d'une chaîne avec stats complètes
   - Top 10 vidéos dans une DataTable
   - Placeholder pour graphiques historiques (à implémenter avec données réelles)

3. **VideoListWidget:**
   - Liste complète et triable des vidéos
   - Colonnes: Title, Published, Views, Likes, Comments, Engagement%
   - Tri dynamique par critère (views/likes/comments/date/engagement)

**Navigation:**
- Enter: voir détails de la chaîne sélectionnée
- v: voir toutes les vidéos
- d: retour au dashboard
- ESC: retour arrière
- r: rafraîchir les données

**CSS:**
- Styles pour DataTable (headers, curseur, zebra stripes)
- Classes pour widgets (dashboard-title, stats-box, graph-box)
- Thème cohérent avec couleurs Textual

**Build Docker:**
- Image reconstruite avec plotext installé
- Prêt pour le déploiement
<!-- SECTION:NOTES:END -->
