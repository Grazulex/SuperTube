---
id: task-41
title: Auto-refresh intelligent en arrière-plan
status: In Progress
assignee:
  - '@claude'
created_date: '2025-10-15 16:51'
updated_date: '2025-10-15 17:30'
labels: []
dependencies: []
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Implémenter un système de refresh automatique intelligent qui collecte les données en arrière-plan, avec priorité sur les chaînes actives et mode watch pour monitoring temps réel
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Ajouter option de configuration pour activer/désactiver auto-refresh
- [x] #2 Implémenter refresh automatique en arrière-plan (non-bloquant)
- [x] #3 Système de priorité: refresh plus fréquent pour chaînes actives
- [x] #4 Mode 'watch' pour monitoring temps réel d'une chaîne
- [x] #5 Indicateur visuel du dernier refresh et prochain refresh
- [x] #6 Gestion intelligente des quotas API (ne pas gaspiller)
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Analyser le code actuel pour comprendre le système de refresh existant
2. Créer quota_manager.py pour tracking des quotas API
3. Créer auto_refresh.py avec AutoRefreshManager
4. Ajouter configuration dans config (ou créer config.py si nécessaire)
5. Intégrer AutoRefreshManager dans app.py
6. Ajouter indicateurs visuels dans status bar
7. Implémenter le mode watch (touche w)
8. Tester le système complet
<!-- SECTION:PLAN:END -->
