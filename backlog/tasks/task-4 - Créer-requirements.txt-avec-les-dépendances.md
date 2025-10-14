---
id: task-4
title: Créer requirements.txt avec les dépendances
status: Done
assignee:
  - '@jean-marc-strauven'
created_date: '2025-10-13 19:21'
updated_date: '2025-10-13 19:26'
labels: []
dependencies: []
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Définir toutes les dépendances Python nécessaires pour l'application : Textual pour le TUI, google-api-python-client pour YouTube API, et autres bibliothèques utiles.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 textual (dernière version) ajouté
- [x] #2 google-api-python-client ajouté
- [x] #3 google-auth-oauthlib ajouté pour OAuth2
- [x] #4 google-auth-httplib2 ajouté
- [x] #5 pyyaml ajouté pour la configuration
- [x] #6 aiosqlite ajouté pour le cache async
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Ajouter Textual pour le TUI
2. Ajouter les packages Google pour YouTube API
3. Ajouter PyYAML pour la config
4. Ajouter aiosqlite pour le cache async
5. Ajouter utilitaires (dateutil)
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
requirements.txt créé avec toutes les dépendances:
- textual 0.47.1 pour l'interface TUI
- google-api-python-client, google-auth-oauthlib pour YouTube API
- pyyaml pour lire config.yaml
- aiosqlite pour cache SQLite asynchrone
- python-dateutil pour gestion des dates
Versions fixées pour reproductibilité
<!-- SECTION:NOTES:END -->
