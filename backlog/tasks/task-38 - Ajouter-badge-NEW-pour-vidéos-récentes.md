---
id: task-38
title: Ajouter badge NEW pour vidéos récentes
status: Done
assignee:
  - '@claude'
created_date: '2025-10-14 03:24'
updated_date: '2025-10-14 03:45'
labels: []
dependencies: []
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Ajouter un indicateur visuel (badge 🆕 ou 'NEW') pour les vidéos publiées depuis moins de 7 jours dans la liste de vidéos. Cela permet d'identifier rapidement le contenu récent.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Les vidéos de moins de 7 jours affichent un badge visuel
- [x] #2 Le badge est visible dans la table VideoList
- [x] #3 Le calcul de récence est basé sur published_at vs date actuelle
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Add is_recent property to Video model to check if published < 7 days ago
2. Update VideoListWidget._refresh_table() to add badge in title column for recent videos
3. Test with videos of different ages
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
# Implementation Summary

## Changes Made

### 1. Added is_recent property to Video model (src/models.py:83-95)
- Returns True if video published within last 7 days
- Excludes future-dated videos
- Handles timezone-aware datetime objects correctly

### 2. Updated VideoListWidget to display 🆕 badge (src/widgets.py:453-463)
- Badge appears before video title for recent videos (< 7 days)
- Adjusted title truncation to account for badge length
- Clean visual indicator without cluttering the UI

## API Limitation Discovered

Initially planned to also add ⏰ badge for scheduled videos, but discovered that **YouTube Data API v3 does NOT provide access to regular scheduled videos** (even for channel owners). Only upcoming live streams and premieres can be retrieved.

### Decision
After discovering this limitation, removed the scheduled video feature entirely:
- Removed scheduled video fetching from src/app.py
- Simplified get_scheduled_videos() in src/youtube_api.py with API limitation documentation
- Removed ⏰ badge logic from src/widgets.py

## Final Features
- **Recent videos (🆕)**: Videos published in the last 7 days
- Scheduled videos feature abandoned due to YouTube API limitations

## Files Modified
- src/models.py: Added is_recent property
- src/widgets.py: Added 🆕 badge display
- src/youtube_api.py: Documented API limitations for scheduled videos
- src/app.py: Removed scheduled video fetching
<!-- SECTION:NOTES:END -->
