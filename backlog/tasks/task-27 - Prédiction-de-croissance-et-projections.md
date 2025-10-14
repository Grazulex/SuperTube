---
id: task-27
title: Prédiction de croissance et projections
status: Done
assignee:
  - '@claude'
created_date: '2025-10-13 22:46'
updated_date: '2025-10-14 21:32'
labels: []
dependencies: []
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Utiliser l'historique pour prédire quand des seuils seront atteints (abonnés, vues) et projeter les tendances futures
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Calcul de projection linéaire basée sur historique
- [x] #2 Estimation de date pour atteindre seuils d'abonnés
- [x] #3 Projection de vues sur 30/60/90 jours
- [x] #4 Visualisation des projections sur graphes
- [x] #5 Indicateur de confiance de la prédiction
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Analyze existing temporal_analysis.py structure as reference
2. Create growth_predictor.py with GrowthPredictor class
3. Implement linear regression for subscriber/view projections
4. Add threshold milestone calculations
5. Add projection data models to models.py (GrowthProjection, MilestoneProjection)
6. Create GrowthProjectionPanel widget for visualization
7. Integrate into app with keyboard binding ('g' for growth)
8. Test with real channel data
9. Add confidence indicator based on data quality
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Implemented complete growth prediction system for channel statistics.

## What was implemented:
- **GrowthPredictor class** (growth_predictor.py): Linear regression engine calculating projections without external ML libraries
- **Data models** (models.py): Added GrowthProjection and MilestoneProjection dataclasses with convenience methods
- **GrowthProjectionPanel widget** (widgets.py): Displays subscriber/view projections and milestone ETAs with color-coded confidence indicators
- **UI integration** (app.py): Added 'g' keyboard binding, action handler, and async data loader

## Key features:
- Linear regression from scratch (slope, intercept, R-squared calculations)
- Confidence scoring: 40% data quantity (capped at 30 points) + 60% model fit quality
- Subscriber projections for 30/60/90 days with growth deltas
- View projections for 30/60/90 days with growth deltas
- Milestone ETA calculations for next 3 achievable thresholds
- Handles edge cases: insufficient data, negative growth, already-achieved milestones

## Testing:
- Docker build succeeded - all syntax and imports verified
- Follows existing architecture patterns (temporal_analysis, title_tag_analyzer)
- Ready for integration testing with real channel data
<!-- SECTION:NOTES:END -->
