---
id: task-12
title: Créer l'interface TUI principale (app.py)
status: Done
assignee:
  - '@jean-marc-strauven'
created_date: '2025-10-13 19:21'
updated_date: '2025-10-13 19:36'
labels: []
dependencies: []
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Créer l'application Textual principale avec la structure de base, le layout, et l'orchestration des différentes vues. Intégrer le système de navigation entre les écrans.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Classe SuperTubeApp héritant de textual.app.App créée
- [x] #2 Layout principal avec header/footer défini
- [x] #3 Header affichant titre et raccourcis clavier
- [x] #4 Footer affichant le statut (dernière MAJ, quota API restant)
- [x] #5 Gestion du routing entre Dashboard et ChannelView
- [x] #6 Chargement de la configuration au démarrage
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Créer module config.py pour charger YAML
2. Créer SuperTubeApp héritant de textual.App
3. Définir layout avec Header/Footer/StatusBar
4. Implémenter on_mount avec init DB et YouTube
5. Ajouter load_data() avec cache/API logic
6. Implémenter routing (dashboard, channel details, help)
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
app.py créé avec application Textual complète:
- Config loader (config.py) pour charger YAML
- SuperTubeApp avec layout Header/Content/StatusBar/Footer
- Initialisation OAuth2 et DB au démarrage
- load_data() async avec cache TTL
- Dashboard simple affichant 3 chaînes + stats
- Navigation clavier: q (quit), r (refresh), 1/2/3 (channels), ? (help)
- StatusBar montrant last update et status
- Gestion erreurs (config manquante, auth failed)
- Channel details view avec top 10 vidéos
<!-- SECTION:NOTES:END -->
