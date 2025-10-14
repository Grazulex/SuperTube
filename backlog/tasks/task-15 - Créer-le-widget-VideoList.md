---
id: task-15
title: Créer le widget VideoList
status: Done
assignee: []
created_date: '2025-10-13 19:21'
updated_date: '2025-10-13 22:15'
labels: []
dependencies: []
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Créer une liste scrollable et filtrable des vidéos d'une chaîne avec leurs statistiques (vues, likes, commentaires, date de publication). Permettre le tri par différents critères.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Widget VideoList créé avec DataTable scrollable
- [x] #2 Colonnes : titre, date, vues, likes, commentaires, ratio like/vue
- [x] #3 Tri par vues/likes/date (clic sur header ou raccourci)
- [x] #4 Recherche/filtre par titre (raccourci '/')
- [x] #5 Navigation j/k style vim
- [x] #6 Copie d'URL vidéo vers clipboard (raccourci 'y')
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Fonctionnalités de recherche et copie d'URL implémentées.
- Input de recherche avec filtrage en temps réel
- Raccourci '/' pour focus la recherche
- Raccourci 'y' pour afficher l'URL de la vidéo (status bar)
- Compteur vidéos filtrées/total
- Navigation j/k intégrée
<!-- SECTION:NOTES:END -->
