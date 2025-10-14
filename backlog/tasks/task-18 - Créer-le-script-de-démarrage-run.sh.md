---
id: task-18
title: Créer le script de démarrage run.sh
status: Done
assignee:
  - '@jean-marc-strauven'
created_date: '2025-10-13 19:21'
updated_date: '2025-10-13 19:38'
labels: []
dependencies: []
priority: low
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Créer un script bash simple pour lancer l'application avec Docker Compose en gérant les cas de première exécution et les erreurs courantes.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Script run.sh créé et exécutable (chmod +x)
- [x] #2 Vérification de docker et docker-compose installés
- [x] #3 Build de l'image si nécessaire
- [x] #4 Message d'aide si config.yaml ou credentials.json manquants
- [x] #5 Lancement avec docker-compose run --rm supertube
- [x] #6 Gestion propre du Ctrl+C
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Créer script bash avec shebang
2. Ajouter vérifications Docker/Docker Compose
3. Vérifier config.yaml et credentials.json
4. Gérer le build d'image (auto + --rebuild flag)
5. Afficher messages clairs avec couleurs
6. Lancer avec docker-compose run
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
run.sh créé avec toutes les vérifications:
- Check Docker et Docker Compose installés
- Check Docker daemon running
- Check config.yaml existe (warning si manquant)
- Check credentials.json existe (warning si manquant)
- Build automatique de l'image si nécessaire
- Flag --rebuild pour forcer rebuild
- Messages colorés (rouge/vert/jaune/bleu)
- Gestion Ctrl+C gracieuse
- Instructions claires si config manquante
Script rendu exécutable avec chmod +x
<!-- SECTION:NOTES:END -->
