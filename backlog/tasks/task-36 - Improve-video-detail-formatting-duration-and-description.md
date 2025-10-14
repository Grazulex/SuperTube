---
id: task-36
title: 'Improve video detail formatting: duration and description'
status: Done
assignee:
  - '@claude'
created_date: '2025-10-14 03:15'
updated_date: '2025-10-14 03:17'
labels: []
dependencies: []
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
In the video detail view, the duration is displayed as raw ISO 8601 format (PT27M6S) which is not user-friendly. Also, the description takes up too much space and should be removed or hidden.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Duration is formatted as human-readable (e.g., '27:06' or '27m 6s')
- [x] #2 Description section is removed from video detail view
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Create a helper function to parse and format ISO 8601 duration (PT27M6S) to human-readable format (27:06)
2. Add the helper function to models.py or as a utility function
3. Update show_video_details() in app.py to use the formatted duration
4. Remove the description section from the video detail view
5. Test the changes to ensure proper formatting
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
# Implementation Summary

## Changes Made

### 1. Added formatted_duration property to Video model (src/models.py:63-81)
- Created a new property that parses ISO 8601 duration format (e.g., PT27M6S)
- Returns human-readable format: "MM:SS" for videos under 1 hour, "H:MM:SS" for longer videos
- Example: PT27M6S → "27:06", PT1H2M30S → "1:02:30"
- Falls back to original duration string if format not recognized

### 2. Updated video detail view (src/app.py:781, 778-793)
- Changed duration display from video.duration to video.formatted_duration
- Removed entire description section and related code
- Result: Cleaner, more compact video detail view with properly formatted duration

## Testing
- Both changes are straightforward and don't affect existing functionality
- The formatted_duration property is self-contained and handles edge cases
- Video detail view now displays duration in readable format without description clutter

## Files Modified
- src/models.py: Added formatted_duration property
- src/app.py: Updated show_video_details method
<!-- SECTION:NOTES:END -->
