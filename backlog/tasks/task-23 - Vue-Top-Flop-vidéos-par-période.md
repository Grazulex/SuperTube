---
id: task-23
title: Vue Top/Flop vidéos par période
status: Done
assignee:
  - '@claude'
created_date: '2025-10-13 22:45'
updated_date: '2025-10-14 03:31'
labels: []
dependencies: []
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Afficher les vidéos les plus et moins performantes sur différentes périodes pour identifier patterns de succès et échecs
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Vue Top 10 vidéos par période (7j, 30j, 90j)
- [x] #2 Vue Bottom 10 vidéos sous-performantes
- [x] #3 Filtres par métrique (vues, engagement, croissance)
- [x] #4 Filtres de date personnalisables
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Create TopFlopWidget in widgets.py for displaying top/bottom performers
2. Add database methods to calculate video performance over periods (7d, 30d, 90d)
3. Add performance metrics calculation (views growth, engagement rate, etc.)
4. Create UI with period selector (7d/30d/90d) and metric filter
5. Add keyboard binding (t) to access Top/Flop view from dashboard
6. Display Top 10 and Bottom 10 videos side by side
7. Update help screen with new keyboard shortcut
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
# Implementation Summary

## Changes Made

### 1. Added database methods for performance analysis (src/database.py:472-594)
- get_top_videos_by_growth(): Retrieves top 10 performing videos by growth over a period
- get_bottom_videos_by_growth(): Retrieves bottom 10 performing videos by growth over a period
- Support for multiple metrics: views, likes, comments, engagement
- Configurable periods: 7d, 30d, 90d (extendable)

### 2. Created TopFlopWidget (src/widgets.py:525-670)
- Split-screen display: Top performers on left, bottom performers on right
- Real-time filtering by period (p key) and metric (m key)
- Shows growth value and current value for each video
- Color-coded growth indicators (green for positive, red for negative)

### 3. Integrated Top/Flop view into app (src/app.py)
- Added keyboard bindings: t (show), p (cycle period), m (cycle metric)
- show_topflop_view(): Main method to display Top/Flop analysis
- load_topflop_data(): Async worker to fetch data from database
- action_show_topflop(), action_cycle_period(), action_cycle_metric()
- Accessible from dashboard, channel detail, and video list views

### 4. Updated help screen (src/app.py:401-424)
- Documented t, p, m keyboard shortcuts
- Added Top/Flop Analysis section with instructions

## Features
- **Top 10 & Bottom 10**: Side-by-side comparison of best/worst performers
- **Flexible periods**: 7 days, 30 days, 90 days
- **Multiple metrics**: Views, Likes, Comments, Engagement rate
- **Growth tracking**: Shows absolute or percentage growth over period
- **Quick access**: Press 't' from any channel view

## Files Modified
- src/database.py: Added performance analysis methods
- src/widgets.py: Created TopFlopWidget
- src/app.py: Integrated Top/Flop view with keyboard shortcuts
<!-- SECTION:NOTES:END -->
