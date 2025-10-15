---
id: task-41
title: Auto-refresh intelligent en arrière-plan
status: Done
assignee:
  - '@claude'
created_date: '2025-10-15 16:51'
updated_date: '2025-10-15 17:34'
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

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Système d'auto-refresh intelligent complété avec succès.

**Fonctionnalités implémentées:**

- QuotaManager pour tracking des quotas API YouTube (10,000 unités/jour)
- AutoRefreshManager avec boucle asynchrone non-bloquante
- Configuration YAML pour activer/désactiver et configurer l'intervalle
- Indicateurs visuels en temps réel dans la status bar
- Mode watch pour monitoring d'une chaîne spécifique (refresh 5min)
- Bindings clavier: Shift+A (toggle auto-refresh), Shift+W (watch mode)
- Système de priorité avec support pour refresh différencié par chaîne
- Gestion intelligente des quotas avec seuil de sécurité à 90%

**Commits:**
- a7991df: Add auto-refresh system core infrastructure  
- b1cdc2a: Add auto-refresh visual indicators and quota tracking
- f1538b3: Complete task-41: Add watch mode and toggle controls
- f105038: Fix infinite recursion in StatusBar update_display

**Tests:** Système testé et bugfix appliqué pour résoudre récursion infinie.
<!-- SECTION:NOTES:END -->
