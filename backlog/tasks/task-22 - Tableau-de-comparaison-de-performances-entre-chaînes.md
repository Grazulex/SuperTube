---
id: task-22
title: Tableau de comparaison de performances entre chaînes
status: Done
assignee:
  - '@claude'
created_date: '2025-10-13 22:45'
updated_date: '2025-10-14 21:13'
labels: []
dependencies: []
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Créer une vue comparative des 3 chaînes côte à côte pour identifier les best practices et opportunités d'amélioration
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Vue avec table comparative des 3 chaînes
- [x] #2 Métriques affichées: engagement, croissance, vues moyennes
- [x] #3 Tri par métrique pour voir qui performe le mieux
- [x] #4 Navigation clavier pour basculer entre métriques
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Add ChannelComparison dataclass to models.py with metrics (engagement_rate, growth_rate, avg_views_per_video)
2. Create comparison calculation logic in a new method
3. Create ChannelComparisonPanel widget in widgets.py
4. Display table with channels as rows, metrics as columns
5. Add sorting by metric (press 'm' to cycle through metrics)
6. Integrate into MainViewPanel as "comparison" mode
7. Add keyboard binding ('c' key) to show comparison
8. Test with Docker build
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
# Channel Comparison Implementation - COMPLETED (4/4 AC)

## Architecture

### 1. ChannelComparison Model (src/models.py:515-539)
New dataclass for channel comparison metrics:
- **Fields**: channel_id, channel_name, subscriber_count, video_count, total_views
- **Calculated metrics**: 
  - avg_views_per_video: Total views / video count
  - avg_engagement_rate: Average engagement across all videos
  - subscriber_growth: Absolute subscriber change (30 days)
  - subscriber_growth_percent: Percentage subscriber growth
  - view_growth: Absolute view change
  - view_growth_percent: Percentage view growth
- **performance_score property**: Weighted score (30% engagement + 30% growth + 40% avg views)

### 2. ChannelComparisonPanel Widget (src/widgets.py:1333-1458)
**Displays comparative table of all channels**
- 7-column table: Channel, Subs, Videos, Avg Views, Engagement, Growth, Score
- Color-coded metrics:
  - Engagement: green (>3%), yellow (>1%), white (default)
  - Growth: green (positive), red (negative)
  - Score: green (>=7), yellow (>=4), red (<4)
- Sort by: Performance score, Subscribers, Engagement, Growth, Avg Views
- **cycle_sort_metric()**: Press 'm' to cycle through sort options
- Updates control panel with current sort metric

### 3. MainViewPanel Integration (src/widgets.py)
**Added "comparison" mode**:
- Updated compose(): Added ChannelComparisonPanel (line 1013)
- Updated _update_visibility(): Added comparison display logic (lines 1053-1057)
- Updated refresh_view(): Added comparison case (lines 1072-1073)
- Added _show_comparison_view(): Triggers data loading (lines 1212-1226)

### 4. App Integration (src/app.py)
**Keyboard Binding**: Press 'c' to show channel comparison

**Implementation**:
- Added ChannelComparison, ChannelComparisonPanel imports (lines 17, 21)
- Added 'c' key binding: `Binding("c", "show_comparison", "Compare")` (line 228)
- `action_show_comparison()`: Switches to comparison mode (lines 854-864)
- `load_comparison_data()`: Calculates comparison metrics (lines 1293-1353)
  - Calculates avg views per video
  - Calculates avg engagement rate from all videos
  - Fetches 30-day history for growth calculations
  - Creates ChannelComparison objects for each channel
- Updated `action_cycle_metric()`: Handles 'm' key in comparison mode (lines 901-905)

## Features Implemented

✅ AC#1: Comparative table showing all channels side-by-side
✅ AC#2: Displays engagement rate, growth %, avg views per video
✅ AC#3: Sortable by 5 metrics (performance, subs, engagement, growth, views)
✅ AC#4: Press 'm' to cycle through sort metrics, 'c' to show comparison

## Usage

**In SuperTube TUI:**
1. Press **'c'** to show channel comparison view
2. See all channels compared in a single table
3. Press **'m'** to cycle through sort metrics:
   - Performance Score (default)
   - Subscribers
   - Engagement Rate
   - Growth Rate  
   - Avg Views per Video
4. Press **'d'** to return to dashboard

**Performance Score Interpretation:**
- **Green (>=7.0)**: Excellent performance
- **Yellow (>=4.0)**: Good performance
- **Red (<4.0)**: Needs improvement

**Metrics Explained:**
- **Engagement**: Average engagement rate across all videos
- **Growth**: Subscriber growth % over last 30 days
- **Avg Views**: Average views per video (channel views / video count)
- **Score**: Weighted performance (30% engagement, 30% growth, 40% avg views)

## Files Modified

- **src/models.py**: +25 lines (ChannelComparison dataclass)
- **src/widgets.py**: +152 lines (ChannelComparisonPanel + MainViewPanel updates)
- **src/app.py**: +74 lines (bindings, actions, load_comparison_data)

**Total**: ~251 lines added

## Technical Details

**Comparison Calculation**:
- Fetches historical data from database (30 days)
- Calculates growth metrics by comparing oldest vs newest stats
- Aggregates engagement rate from all videos per channel
- Normalizes metrics for performance score (0-10 scale)

**Performance Score Formula**:
```python
normalized_views = min(avg_views_per_video / 10000, 10.0)  # Cap at 100K
normalized_engagement = min(avg_engagement_rate, 10.0)     # Cap at 10%
normalized_growth = min(abs(growth_percent) / 10, 10.0)    # Cap at 100%

score = (engagement * 0.3) + (growth * 0.3) + (views * 0.4)
```

**Color Coding Logic**:
- Engagement: >3% green, >1% yellow, else white
- Growth: positive green, negative red
- Score: >=7 green, >=4 yellow, <4 red

## Testing

✅ Docker build successful
✅ No syntax errors
✅ All imports resolved
✅ Widget composition correct
✅ Mode switching implemented
✅ Metric cycling functional

System ready for channel comparison insights!
<!-- SECTION:NOTES:END -->
