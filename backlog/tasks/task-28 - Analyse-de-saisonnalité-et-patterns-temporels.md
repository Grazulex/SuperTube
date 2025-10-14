---
id: task-28
title: Analyse de saisonnalité et patterns temporels
status: Done
assignee:
  - '@claude'
created_date: '2025-10-13 22:46'
updated_date: '2025-10-14 20:59'
labels: []
dependencies: []
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Identifier les patterns temporels de performance (jours, heures, saisons) pour optimiser les publications
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Détection de meilleurs jours/heures de publication
- [x] #2 Analyse de performance par jour de la semaine
- [x] #3 Identification de patterns saisonniers (vacances, événements)
- [x] #4 Recommandations de timing de publication
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Add temporal pattern models to models.py (DayOfWeekPattern, HourOfDayPattern, SeasonalPattern, PublicationRecommendation)
2. Create temporal_analysis.py with TemporalAnalyzer class
3. Analyzer methods: analyze_day_of_week(), analyze_hour_of_day(), analyze_seasonal_patterns(), generate_recommendations()
4. Use existing Video.published_at timestamps for analysis
5. Create TemporalAnalysisPanel widget for displaying patterns
6. Integrate into app.py layout
7. Test with Docker build
8. Note: Analysis uses video publication times and performance metrics (views, engagement)
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
# Temporal Analysis Implementation - COMPLETED (4/4 AC)

## Architecture

### 1. Temporal Pattern Models (src/models.py:434-512)
Four new dataclasses for temporal analysis:
- **DayOfWeekPattern**: Performance by day (Monday-Sunday)
  - day_name, day_index, video_count, avg_views, avg_engagement, avg_like_ratio
  - performance_score property: weighted score (40% views, 40% engagement, 20% like ratio)
- **HourOfDayPattern**: Performance by hour (0-23)
  - hour, video_count, metrics, performance_score
- **SeasonalPattern**: Performance by month (1-12)
  - month, month_name, video_count, metrics, performance_score
- **PublicationRecommendation**: Best/worst timing recommendations
  - best_day, best_hour, best_month with scores
  - worst_day, worst_hour, worst_month with scores

### 2. Temporal Analyzer (src/temporal_analysis.py, 206 lines)
**TemporalAnalyzer class** analyzes video publication patterns:
```python
analyzer = TemporalAnalyzer(videos)
day_patterns = analyzer.analyze_day_of_week()    # Group by weekday
hour_patterns = analyzer.analyze_hour_of_day()   # Group by hour
month_patterns = analyzer.analyze_seasonal_patterns()  # Group by month
recommendations = analyzer.generate_recommendations()  # Best/worst times
```

**Analysis Methods:**
- `analyze_day_of_week()`: Returns 7 DayOfWeekPattern objects (Mon-Sun)
- `analyze_hour_of_day()`: Returns 24 HourOfDayPattern objects (0-23h)
- `analyze_seasonal_patterns()`: Returns 12 SeasonalPattern objects (Jan-Dec)
- `generate_recommendations()`: Returns PublicationRecommendation with optimal timing

**Performance Scoring:** Weighted formula normalized to 10 points:
- 40% normalized views (capped at 100K = 10 points)
- 40% engagement rate
- 20% like ratio

### 3. Temporal Analysis Panel (src/widgets.py:1214-1302)
**TemporalAnalysisPanel widget** displays temporal insights:
- Publication recommendations (best day/hour/month)
- Top 3 performing days with video counts and avg views
- Top 3 performing hours with video counts and avg views  
- Top 3 performing months with video counts and avg views
- Performance scores shown for each pattern

### 4. App Integration (src/app.py)
**Keyboard Binding:** Press 'a' to view temporal analysis
**Implementation:**
- Added TemporalAnalyzer and TemporalAnalysisPanel imports (lines 21-24)
- Added 'a' key binding: `Binding("a", "show_temporal", "Temporal")` (line 227)
- `action_show_temporal()`: Switches main panel to temporal mode (lines 801-811)
- `load_temporal_data()`: Analyzes videos and updates panel (lines 1202-1233)
- MainViewPanel supports "temporal" mode alongside "dashboard" and "topflop"

### 5. Widget Updates (src/widgets.py)
**MainViewPanel enhancements:**
- Added temporal mode support (line 998)
- Added TemporalAnalysisPanel to compose (line 1010)
- Updated visibility management for 3 modes (lines 1027-1047)
- Added `_show_temporal_view()` method (lines 1182-1196)

## Features Implemented

✅ AC#1: Best day/hour detection via analyze_day_of_week() and analyze_hour_of_day()
✅ AC#2: Day of week performance analysis (7 patterns with metrics)
✅ AC#3: Seasonal patterns via analyze_seasonal_patterns() (12 monthly patterns)
✅ AC#4: Publication timing recommendations with best/worst analysis

## Usage

**In SuperTube TUI:**
1. Select a channel from the channels panel
2. Press 'a' to view temporal analysis
3. View recommendations for best publication times:
   - Best day of week to publish
   - Best hour of day to publish
   - Best month to publish
4. See top 3 performing days/hours/months with statistics
5. Press 'd' to return to dashboard view

**Performance Score Interpretation:**
- Higher score = better performance for that time period
- Considers views, engagement rate, and like ratio
- Helps identify optimal publishing windows

## Files Modified

- **src/models.py**: +79 lines (4 new temporal pattern dataclasses)
- **src/temporal_analysis.py**: +206 lines (new file, TemporalAnalyzer class)
- **src/widgets.py**: +107 lines (TemporalAnalysisPanel + MainViewPanel updates)
- **src/app.py**: +33 lines (bindings, action, load_temporal_data method)

**Total**: ~425 lines added

## Technical Details

**Analysis Approach:**
- Uses video.published_at timestamps to group videos temporally
- Calculates aggregate metrics (avg views, engagement, like ratio) per time bucket
- Ranks time periods by performance score
- Identifies best/worst patterns for recommendations

**Data Requirements:**
- Requires videos with published_at timestamps
- Works with any number of videos (more = better accuracy)
- Empty time buckets show 0 counts (no videos published then)

**Integration Pattern:**
- Follows existing TopFlopWidget pattern
- Async data loading via @work decorator
- Reactive display updates via call_after_refresh()
- Clean mode switching in MainViewPanel

## Testing

✅ Docker build successful
✅ No syntax errors
✅ All imports resolved
✅ Widget composition correct
✅ Mode switching implemented
✅ Performance score calculation tested

System ready for temporal insights!
<!-- SECTION:NOTES:END -->
