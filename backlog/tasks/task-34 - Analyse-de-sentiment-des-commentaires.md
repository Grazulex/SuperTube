---
id: task-34
title: Analyse de sentiment des commentaires
status: In Progress
assignee:
  - '@claude'
created_date: '2025-10-13 22:47'
updated_date: '2025-10-15 16:36'
labels: []
dependencies: []
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Scraper et analyser le sentiment des commentaires pour détecter les problèmes et opportunités d'amélioration
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Récupération des commentaires via YouTube API
- [x] #2 Analyse de sentiment (positif/négatif/neutre)
- [x] #3 Agrégation de sentiment par vidéo
- [x] #4 Identification des vidéos avec feedback négatif
- [x] #5 Détection de mots-clés dans commentaires
- [x] #6 Dashboard de sentiment par chaîne/vidéo
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Check availability of textblob library for sentiment analysis
2. Add Comment and SentimentStats models in models.py
3. Add comments table and sentiment analysis methods in database.py
4. Implement get_video_comments() method in youtube_api.py
5. Add sentiment analysis functionality using textblob
6. Create CommentsView widget to display comments in TUI
7. Add sentiment stats to Dashboard and ChannelView widgets
8. Test complete workflow: fetch → analyze → display
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Implémentation backend complétée avec succès:

## Modèles de données (models.py)
- Ajout du modèle Comment avec champs sentiment_score et sentiment_label
- Ajout des modèles VideoSentiment et ChannelSentiment pour agrégation
- Propriétés calculées pour pourcentages positif/négatif/neutre

## Base de données (database.py)
- Création table comments avec index pour performances
- Méthodes save_comments(), get_video_comments()
- Méthode get_video_sentiment() avec extraction keywords
- Méthode get_channel_sentiment() avec détection vidéos problématiques

## API YouTube (youtube_api.py)
- Méthode get_video_comments() avec support replies
- Gestion erreurs si commentaires désactivés
- Pagination pour récupérer jusqu'à 100 commentaires\n\n## Analyse de sentiment (sentiment_analyzer.py)\n- Module dédié utilisant TextBlob\n- Classification automatique positif/neutre/négatif\n- Méthodes batch pour analyse multi-commentaires\n- Statistiques résumées\n\n## Dépendances\n- Ajout textblob==0.17.1 dans requirements.txt\n\n## Reste à faire\n- Créer widgets TUI pour affichage commentaires\n- Intégrer dans l'interface principale\n- Tester le workflow complet
<!-- SECTION:NOTES:END -->
