---
id: task-8
title: Configurer les IDs des 3 chaînes YouTube
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
Copier config.yaml.example vers config.yaml et remplir les vrais IDs des 3 chaînes YouTube à surveiller. Les IDs peuvent être trouvés dans l'URL des chaînes ou via YouTube Studio.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Fichier config.yaml créé à partir de l'exemple
- [x] #2 IDs des 3 chaînes YouTube remplis
- [x] #3 Noms descriptifs donnés à chaque chaîne
- [x] #4 Fichier config.yaml ajouté au .gitignore
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Configuration des chaînes YouTube terminée.

**Réalisé par l'utilisateur:**
- config.yaml créé dans config/
- 3 chaînes YouTube configurées avec leurs IDs:
  1. Dreamy & Psychedelic Chill (UCcgPbwx-dix51ylCktB6-Qw)
  2. World in Numbers (UC0u-skG-CxV0NAk87ioIMqA)
  3. ChronikA – L'Histoire autrement (UCu-e0vJqOGFF2__Y2kObl5Q)
- Noms descriptifs ajoutés pour chaque chaîne
- Fichier vérifié dans .gitignore (ligne 46)

**Settings configurés:**
- Cache TTL: 3600s (1h)
- Max videos: 50 par chaîne
- Auto-refresh: désactivé

**Validation:**
- Fichier config.yaml valide et prêt à l'utilisation
<!-- SECTION:NOTES:END -->
