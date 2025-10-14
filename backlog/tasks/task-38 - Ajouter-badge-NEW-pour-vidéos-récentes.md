---
id: task-38
title: Ajouter badge NEW pour vidéos récentes
status: Done
assignee:
  - '@claude'
created_date: '2025-10-14 03:24'
updated_date: '2025-10-14 03:26'
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

### 1. Added video status properties to Video model (src/models.py:83-101)
- is_recent property: Returns True if video published within last 7 days (excludes future/scheduled videos)
- is_scheduled property: Returns True if video publication date is in the future
- Both properties handle timezone-aware datetime objects correctly

### 2. Updated VideoListWidget to display badges (src/widgets.py:453-464)
- 🆕 badge for recent videos (< 7 days old)
- ⏰ badge for scheduled videos (future publication)
- Adjusted title truncation to account for badge length
- Badges appear before video title in the list

## Features
- **Recent videos (🆕)**: Videos published in the last 7 days
- **Scheduled videos (⏰)**: Videos with future publication date
- Clean visual indicators that don't clutter the UI

## Files Modified
- src/models.py: Added is_recent and is_scheduled properties
- src/widgets.py: Updated _refresh_table to display badges
<!-- SECTION:NOTES:END -->
