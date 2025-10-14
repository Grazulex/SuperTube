---
id: task-6
title: Placer les credentials OAuth2 dans le projet
status: Done
assignee:
  - '@claude'
created_date: '2025-10-13 19:21'
updated_date: '2025-10-13 21:00'
labels: []
dependencies: []
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Télécharger le fichier credentials.json depuis Google Cloud Console et le placer dans le dossier config/ du projet pour permettre l'authentification OAuth2.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Fichier credentials.json placé dans config/
- [x] #2 Fichier credentials.json ajouté au .gitignore
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Fichier credentials.json correctement placé dans le projet.

**Réalisé:**
- credentials.json placé dans config/ par l'utilisateur
- Vérifié présence dans .gitignore (ligne 44)

**Fichiers modifiés:**
- Aucun (fichier déjà placé par l'utilisateur)

**Validation:**
- Fichier présent et fonctionnel (authentification réussie)
<!-- SECTION:NOTES:END -->
