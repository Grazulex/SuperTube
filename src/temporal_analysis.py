"""Temporal analysis for video publication patterns"""

from typing import List, Dict
from collections import defaultdict
from datetime import datetime
import calendar

from .models import (
    Video,
    DayOfWeekPattern,
    HourOfDayPattern,
    SeasonalPattern,
    PublicationRecommendation
)


class TemporalAnalyzer:
    """Analyze video publication patterns and performance by time"""

    def __init__(self, videos: List[Video]):
        """Initialize analyzer with list of videos"""
        self.videos = videos

    def analyze_day_of_week(self) -> List[DayOfWeekPattern]:
        """Analyze video performance by day of week"""
        # Group videos by day of week
        day_data: Dict[int, List[Video]] = defaultdict(list)

        for video in self.videos:
            # Get day of week (0 = Monday, 6 = Sunday)
            day_idx = video.published_at.weekday()
            day_data[day_idx].append(video)

        # Calculate patterns for each day
        patterns = []
        for day_idx in range(7):
            videos_on_day = day_data[day_idx]
            day_name = calendar.day_name[day_idx]

            if not videos_on_day:
                # No videos on this day
                patterns.append(DayOfWeekPattern(
                    day_name=day_name,
                    day_index=day_idx,
                    video_count=0,
                    avg_views=0.0,
                    avg_engagement=0.0,
                    avg_like_ratio=0.0,
                    total_views=0
                ))
                continue

            # Calculate metrics
            total_views = sum(v.view_count for v in videos_on_day)
            avg_views = total_views / len(videos_on_day)
            avg_engagement = sum(v.engagement_rate for v in videos_on_day) / len(videos_on_day)
            avg_like_ratio = sum(v.like_ratio for v in videos_on_day) / len(videos_on_day)

            patterns.append(DayOfWeekPattern(
                day_name=day_name,
                day_index=day_idx,
                video_count=len(videos_on_day),
                avg_views=avg_views,
                avg_engagement=avg_engagement,
                avg_like_ratio=avg_like_ratio,
                total_views=total_views
            ))

        return patterns

    def analyze_hour_of_day(self) -> List[HourOfDayPattern]:
        """Analyze video performance by hour of day"""
        # Group videos by hour
        hour_data: Dict[int, List[Video]] = defaultdict(list)

        for video in self.videos:
            hour = video.published_at.hour
            hour_data[hour].append(video)

        # Calculate patterns for each hour
        patterns = []
        for hour in range(24):
            videos_at_hour = hour_data[hour]

            if not videos_at_hour:
                # No videos at this hour
                patterns.append(HourOfDayPattern(
                    hour=hour,
                    video_count=0,
                    avg_views=0.0,
                    avg_engagement=0.0,
                    avg_like_ratio=0.0,
                    total_views=0
                ))
                continue

            # Calculate metrics
            total_views = sum(v.view_count for v in videos_at_hour)
            avg_views = total_views / len(videos_at_hour)
            avg_engagement = sum(v.engagement_rate for v in videos_at_hour) / len(videos_at_hour)
            avg_like_ratio = sum(v.like_ratio for v in videos_at_hour) / len(videos_at_hour)

            patterns.append(HourOfDayPattern(
                hour=hour,
                video_count=len(videos_at_hour),
                avg_views=avg_views,
                avg_engagement=avg_engagement,
                avg_like_ratio=avg_like_ratio,
                total_views=total_views
            ))

        return patterns

    def analyze_seasonal_patterns(self) -> List[SeasonalPattern]:
        """Analyze video performance by month (seasonal patterns)"""
        # Group videos by month
        month_data: Dict[int, List[Video]] = defaultdict(list)

        for video in self.videos:
            month = video.published_at.month
            month_data[month].append(video)

        # Calculate patterns for each month
        patterns = []
        for month in range(1, 13):
            videos_in_month = month_data[month]
            month_name = calendar.month_name[month]

            if not videos_in_month:
                # No videos in this month
                patterns.append(SeasonalPattern(
                    month=month,
                    month_name=month_name,
                    video_count=0,
                    avg_views=0.0,
                    avg_engagement=0.0,
                    avg_like_ratio=0.0,
                    total_views=0
                ))
                continue

            # Calculate metrics
            total_views = sum(v.view_count for v in videos_in_month)
            avg_views = total_views / len(videos_in_month)
            avg_engagement = sum(v.engagement_rate for v in videos_in_month) / len(videos_in_month)
            avg_like_ratio = sum(v.like_ratio for v in videos_in_month) / len(videos_in_month)

            patterns.append(SeasonalPattern(
                month=month,
                month_name=month_name,
                video_count=len(videos_in_month),
                avg_views=avg_views,
                avg_engagement=avg_engagement,
                avg_like_ratio=avg_like_ratio,
                total_views=total_views
            ))

        return patterns

    def generate_recommendations(self) -> PublicationRecommendation:
        """Generate publication timing recommendations based on patterns"""
        day_patterns = self.analyze_day_of_week()
        hour_patterns = self.analyze_hour_of_day()
        month_patterns = self.analyze_seasonal_patterns()

        # Filter out patterns with no data
        valid_day_patterns = [p for p in day_patterns if p.video_count > 0]
        valid_hour_patterns = [p for p in hour_patterns if p.video_count > 0]
        valid_month_patterns = [p for p in month_patterns if p.video_count > 0]

        # Find best and worst patterns
        if valid_day_patterns:
            best_day = max(valid_day_patterns, key=lambda p: p.performance_score)
            worst_day = min(valid_day_patterns, key=lambda p: p.performance_score)
        else:
            # Default values if no data
            best_day = DayOfWeekPattern("Monday", 0, 0, 0.0, 0.0, 0.0, 0)
            worst_day = DayOfWeekPattern("Sunday", 6, 0, 0.0, 0.0, 0.0, 0)

        if valid_hour_patterns:
            best_hour = max(valid_hour_patterns, key=lambda p: p.performance_score)
            worst_hour = min(valid_hour_patterns, key=lambda p: p.performance_score)
        else:
            # Default values if no data
            best_hour = HourOfDayPattern(12, 0, 0.0, 0.0, 0.0, 0)
            worst_hour = HourOfDayPattern(0, 0, 0.0, 0.0, 0.0, 0)

        if valid_month_patterns:
            best_month = max(valid_month_patterns, key=lambda p: p.performance_score)
            worst_month = min(valid_month_patterns, key=lambda p: p.performance_score)
        else:
            # Default values if no data
            best_month = SeasonalPattern(1, "January", 0, 0.0, 0.0, 0.0, 0)
            worst_month = SeasonalPattern(12, "December", 0, 0.0, 0.0, 0.0, 0)

        return PublicationRecommendation(
            best_day=best_day.day_name,
            best_day_score=best_day.performance_score,
            best_hour=best_hour.hour,
            best_hour_score=best_hour.performance_score,
            best_month=best_month.month_name,
            best_month_score=best_month.performance_score,
            worst_day=worst_day.day_name,
            worst_day_score=worst_day.performance_score,
            worst_hour=worst_hour.hour,
            worst_hour_score=worst_hour.performance_score,
            worst_month=worst_month.month_name,
            worst_month_score=worst_month.performance_score
        )
