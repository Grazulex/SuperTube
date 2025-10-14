---
id: task-20
title: Tester l'authentification OAuth2 YouTube
status: Done
assignee:
  - '@claude'
created_date: '2025-10-13 19:21'
updated_date: '2025-10-13 20:58'
labels: []
dependencies: []
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Lancer l'application et compléter le flow OAuth2 pour vérifier que l'authentification fonctionne et que les tokens sont correctement sauvegardés pour les prochains lancements.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Flow OAuth2 se lance et affiche l'URL de consentement
- [x] #2 Après autorisation, token sauvegardé dans config/token.pickle
- [x] #3 Second lancement utilise le token sans redemander auth
- [x] #4 Première requête API réussit et retourne des données
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Résolu le problème d'authentification OAuth2 YouTube.

**Problème identifié:**
- Le volume config était monté en lecture seule (:ro) dans docker-compose.yml
- Empêchait l'écriture du token.pickle après authentification

**Solution:**
- Modifié docker-compose.yml ligne 15 pour retirer le flag :ro
- Permet maintenant l'écriture du token dans /app/config/token.pickle

**Validation:**
- Flow OAuth2 réussi avec affichage de l'URL de consentement
- Token sauvegardé correctement après autorisation
- Authentification confirmée fonctionnelle par l'utilisateur
<!-- SECTION:NOTES:END -->
