---
id: task-3
title: Créer le docker-compose.yml
status: Done
assignee:
  - '@jean-marc-strauven'
created_date: '2025-10-13 19:21'
updated_date: '2025-10-13 19:25'
labels: []
dependencies: []
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Créer un fichier docker-compose.yml pour faciliter le lancement de l'application avec les bons volumes montés et configuration TTY.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Service 'supertube' défini dans docker-compose.yml
- [x] #2 Volume pour ./config monté vers /app/config
- [x] #3 Volume pour ./data monté vers /app/data (cache SQLite)
- [x] #4 Configuration stdin_open et tty activées
- [x] #5 Variable d'environnement TERM définie
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Définir le service supertube
2. Configurer stdin_open et tty pour l'interactivité
3. Monter les volumes pour config et data
4. Configurer les variables d'environnement
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
docker-compose.yml créé avec:
- Service supertube configuré avec build depuis Dockerfile
- Support TTY activé (stdin_open + tty) pour Textual
- Volume ./config monté en lecture seule
- Volume ./data monté pour le cache SQLite
- Variable TERM définie pour support couleurs
- restart: no (app interactive)
<!-- SECTION:NOTES:END -->
