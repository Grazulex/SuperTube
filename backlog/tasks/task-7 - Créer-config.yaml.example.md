---
id: task-7
title: Créer config.yaml.example
status: Done
assignee:
  - '@jean-marc-strauven'
created_date: '2025-10-13 19:21'
updated_date: '2025-10-13 19:26'
labels: []
dependencies: []
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Créer un fichier de configuration exemple qui servira de template pour l'utilisateur. Il contiendra la structure pour définir les 3 chaînes YouTube à surveiller.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Fichier config.yaml.example créé dans config/
- [x] #2 Structure YAML définie avec liste de chaînes
- [x] #3 Chaque chaîne a : name, channel_id, description
- [x] #4 Commentaires explicatifs ajoutés dans le fichier
- [x] #5 Exemple avec 3 chaînes placeholder
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Créer la structure YAML avec liste de chaînes
2. Ajouter des commentaires explicatifs
3. Inclure des instructions pour trouver les IDs
4. Ajouter des settings supplémentaires (cache, refresh)
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
config.yaml.example créé avec:
- Structure YAML claire pour 3 chaînes (name, channel_id, description)
- Instructions détaillées pour trouver les Channel IDs
- Section settings avec cache_ttl, max_videos, auto_refresh
- Commentaires explicatifs complets
L'utilisateur doit copier vers config.yaml et remplir ses vrais IDs
<!-- SECTION:NOTES:END -->
