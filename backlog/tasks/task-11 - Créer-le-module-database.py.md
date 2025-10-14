---
id: task-11
title: Créer le module database.py
status: Done
assignee:
  - '@jean-marc-strauven'
created_date: '2025-10-13 19:21'
updated_date: '2025-10-13 19:34'
labels: []
dependencies: []
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Implémenter une couche de cache SQLite asynchrone pour stocker l'historique des stats et éviter de consommer trop de quota API YouTube. Permettre de voir les tendances dans le temps.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Schéma SQLite créé (tables channels, videos, stats_history)
- [x] #2 Classe DatabaseManager créée avec méthodes async
- [x] #3 Méthode save_channel_stats() implémentée
- [x] #4 Méthode get_channel_history() implémentée
- [x] #5 Méthode get_cached_stats() avec TTL configurable
- [x] #6 Index créés pour optimiser les requêtes
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Créer schéma SQLite (tables channels, videos, stats_history)
2. Implémenter DatabaseManager avec méthodes async
3. Ajouter save/get pour channels et videos
4. Implémenter historique de stats avec get_channel_history()
5. Ajouter cache TTL avec is_channel_cache_valid()
6. Créer index pour optimisation
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
database.py créé avec cache SQLite complet:
- 3 tables: channels, videos, stats_history
- DatabaseManager avec méthodes async (aiosqlite)
- save_channel/get_channel avec cache TTL
- save_videos/get_channel_videos (tri par date)
- save_channel_stats pour historique
- get_channel_history(days) pour trends
- Index sur channel_id pour performance
- cleanup_old_history() pour maintenance
<!-- SECTION:NOTES:END -->
