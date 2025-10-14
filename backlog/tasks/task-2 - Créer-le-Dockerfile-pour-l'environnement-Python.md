---
id: task-2
title: Créer le Dockerfile pour l'environnement Python
status: Done
assignee:
  - '@jean-marc-strauven'
created_date: '2025-10-13 19:21'
updated_date: '2025-10-13 19:24'
labels: []
dependencies: []
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Créer un Dockerfile optimisé pour exécuter l'application Textual avec support TTY et toutes les dépendances nécessaires pour l'API YouTube.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Dockerfile basé sur python:3.11-slim créé
- [x] #2 Installation de requirements.txt configurée
- [x] #3 Variables d'environnement pour credentials définies
- [x] #4 ENTRYPOINT configuré pour lancer l'application
- [x] #5 Support TTY activé pour Textual
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Choisir image de base Python 3.11 slim
2. Configurer les variables d'environnement nécessaires
3. Installer dépendances système et Python
4. Copier le code et configurer l'entrypoint
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Dockerfile créé avec:
- Base python:3.11-slim pour image légère
- Support TTY avec TERM=xterm-256color
- Installation optimisée des dépendances (cache layers)
- Entrypoint configuré pour lancer src.app
- Dossiers config/ et data/ préparés pour volumes
<!-- SECTION:NOTES:END -->
