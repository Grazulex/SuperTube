---
id: task-40
title: Refonte layout multi-panneaux style lazydocker/lazygit
status: In Progress
assignee:
  - '@claude'
created_date: '2025-10-14 18:58'
updated_date: '2025-10-14 19:06'
labels: []
dependencies: []
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Refactoriser le layout actuel pour adopter une interface multi-panneaux inspirée de lazydocker/lazygit. Colonne gauche (1/3 largeur) avec panneaux Chaînes/Vidéos/Détails, colonne droite (2/3 largeur) pour stats/graphs. Navigation Tab entre panneaux, flèches pour sélection.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Créer layout 2 colonnes : gauche 1/3 width, droite 2/3 width
- [ ] #2 Diviser colonne gauche en 3 panneaux adaptatifs : Chaînes, Vidéos, Détails
- [ ] #3 Créer panneau principal droit (100% hauteur) pour stats/graphs
- [ ] #4 Implémenter navigation Tab entre panneaux gauche
- [ ] #5 Mettre à jour Panel 4 (stats) selon sélection active
- [ ] #6 Adapter tous les bindings clavier au nouveau système
- [ ] #7 Tester responsive sur différentes tailles de terminal
- [ ] #8 Navigation ↑↓ sélectionne automatiquement (pas de Enter nécessaire)
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Create 4 new panel widgets (ChannelsListPanel, VideosListPanel, VideoDetailsPanel, MainViewPanel)
2. Import new widgets in app.py
3. Add CSS for lazydocker-style layout (1/3 left sidebar, 2/3 main view)
4. Modify compose() to create Horizontal layout with panels
5. Implement reactive connections between panels (channel selection → videos update)
6. Add Tab navigation between panels
7. Adapt keyboard bindings (s, t, d, etc.)
8. Test and polish borders/styles
<!-- SECTION:PLAN:END -->
