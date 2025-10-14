---
id: task-37
title: Add sort functionality to dashboard like video list
status: Done
assignee:
  - '@claude'
created_date: '2025-10-14 03:17'
updated_date: '2025-10-14 03:18'
labels: []
dependencies: []
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Currently, the video list has a sort feature (press 's' to cycle through different sort orders). The dashboard should have the same functionality to sort channels by different metrics (subscribers, views, videos, etc.).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Dashboard supports sorting by pressing 's' key
- [x] #2 Sort cycles through: subscribers, views, video count, alphabetical
- [x] #3 Status bar shows current sort order when changed
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Add sorting state to DashboardWidget (sort_key, sort_reverse attributes)
2. Add _sort_channels() method to DashboardWidget
3. Add change_sort() method to DashboardWidget
4. Update update_channels() to apply sorting before displaying
5. Modify action_cycle_sort() in app.py to handle dashboard view
6. Test sorting functionality in dashboard
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
# Implementation Summary

## Changes Made

### 1. Added sorting state to DashboardWidget (src/widgets.py:20-21)
- Added sort_key attribute (default: "subscribers")
- Added sort_reverse attribute (default: True for descending order)

### 2. Added sorting methods to DashboardWidget (src/widgets.py:169-223)
- _sort_channels(): Sorts channels by current sort_key (subscribers, views, videos, or name)
- change_sort(): Changes sort key and refreshes the table
- _refresh_table(): Rebuilds table with sorted channel data

### 3. Updated update_channels() method (src/widgets.py:40-41)
- Added call to _sort_channels() before displaying channels
- Ensures channels are always displayed in current sort order

### 4. Enhanced action_cycle_sort() in app.py (src/app.py:531-581)
- Extended to handle both dashboard and video list views
- Dashboard cycles through: subscribers → views → videos → name
- Video list keeps existing behavior: views → likes → comments → date → engagement
- Status bar shows current sort order with descriptive names

### 5. Updated help screen (src/app.py:396)
- Added documentation for 's' key in Dashboard section
- Shows available sort orders for dashboard

## Testing
- Sorting functionality mirrors the existing video list implementation
- Press 's' on dashboard to cycle through sort orders
- Status bar displays current sort order
- Default sort is by subscribers (descending)

## Files Modified
- src/widgets.py: Added sorting state and methods to DashboardWidget
- src/app.py: Extended action_cycle_sort() and updated help text
<!-- SECTION:NOTES:END -->
