---
id: task-16
title: Implémenter la navigation clavier complète
status: Done
assignee: []
created_date: '2025-10-13 19:21'
updated_date: '2025-10-13 22:11'
labels: []
dependencies: []
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Implémenter tous les raccourcis clavier pour une navigation fluide style vim/lazygit : navigation, refresh, quit, et actions contextuelles selon l'écran actif.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Raccourcis globaux : q (quit), r (refresh), ? (help)
- [x] #2 Navigation Dashboard : j/k (haut/bas), Enter (détails chaîne)
- [x] #3 Navigation ChannelView : ESC (retour), v (voir vidéos)
- [x] #4 Navigation VideoList : j/k (scroll), / (recherche), s (tri)
- [x] #5 Tabs 1/2/3 pour switcher entre chaînes directement
- [x] #6 Écran d'aide (?) listant tous les raccourcis
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Raccourcis clavier complets implémentés.
- j/k pour navigation vim-style dans toutes les tables
- 1/2/3 pour accès rapide aux chaînes
- s pour changer le tri dans VideoList
- Écran d'aide mis à jour avec tous les raccourcis
- Navigation fluide et intuitive
<!-- SECTION:NOTES:END -->
