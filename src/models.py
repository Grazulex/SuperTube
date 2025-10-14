"""Data models for SuperTube"""

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional, List, Dict, Any


@dataclass
class Channel:
    """YouTube channel information and statistics"""
    id: str
    name: str
    custom_url: Optional[str]
    description: str
    subscriber_count: int
    view_count: int
    video_count: int
    published_at: datetime
    thumbnail_url: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data['published_at'] = self.published_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Channel':
        """Create from dictionary"""
        if isinstance(data['published_at'], str):
            data['published_at'] = datetime.fromisoformat(data['published_at'])
        return cls(**data)


@dataclass
class Video:
    """YouTube video information and statistics"""
    id: str
    channel_id: str
    title: str
    description: str
    published_at: datetime
    view_count: int
    like_count: int
    comment_count: int
    duration: str  # ISO 8601 duration format (e.g., "PT4M13S")
    thumbnail_url: Optional[str] = None

    @property
    def engagement_rate(self) -> float:
        """Calculate engagement rate (likes + comments) / views"""
        if self.view_count == 0:
            return 0.0
        return ((self.like_count + self.comment_count) / self.view_count) * 100

    @property
    def like_ratio(self) -> float:
        """Calculate like ratio (likes / views)"""
        if self.view_count == 0:
            return 0.0
        return (self.like_count / self.view_count) * 100

    @property
    def formatted_duration(self) -> str:
        """Format ISO 8601 duration to human-readable format (HH:MM:SS or MM:SS)"""
        import re

        # Parse ISO 8601 duration format (e.g., PT1H2M30S, PT45M12S, PT30S)
        match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', self.duration)
        if not match:
            return self.duration  # Return as-is if format not recognized

        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        seconds = int(match.group(3) or 0)

        # Format based on length
        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes}:{seconds:02d}"

    @property
    def is_recent(self) -> bool:
        """Check if video was published within the last 7 days (not scheduled for future)"""
        from datetime import datetime, timedelta
        now = datetime.now(self.published_at.tzinfo) if self.published_at.tzinfo else datetime.now()

        # Don't mark future/scheduled videos as recent
        if self.published_at > now:
            return False

        seven_days_ago = now - timedelta(days=7)
        return self.published_at >= seven_days_ago

    @property
    def is_scheduled(self) -> bool:
        """Check if video is scheduled for future publication"""
        from datetime import datetime
        now = datetime.now(self.published_at.tzinfo) if self.published_at.tzinfo else datetime.now()
        return self.published_at > now

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data['published_at'] = self.published_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Video':
        """Create from dictionary"""
        if isinstance(data['published_at'], str):
            data['published_at'] = datetime.fromisoformat(data['published_at'])
        return cls(**data)


@dataclass
class ChannelStats:
    """Historical statistics for a channel"""
    channel_id: str
    timestamp: datetime
    subscriber_count: int
    view_count: int
    video_count: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChannelStats':
        """Create from dictionary"""
        if isinstance(data['timestamp'], str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


@dataclass
class ChannelTrend:
    """Trend analysis for a channel over a period"""
    channel_id: str
    period_days: int
    subscriber_growth: int
    subscriber_growth_percent: float
    view_growth: int
    view_growth_percent: float
    video_growth: int
    avg_daily_views: float

    @classmethod
    def calculate(cls, channel_id: str, history: List[ChannelStats], period_days: int = 7) -> 'ChannelTrend':
        """Calculate trend from historical data"""
        if len(history) < 2:
            return cls(
                channel_id=channel_id,
                period_days=period_days,
                subscriber_growth=0,
                subscriber_growth_percent=0.0,
                view_growth=0,
                view_growth_percent=0.0,
                video_growth=0,
                avg_daily_views=0.0
            )

        # Sort by timestamp
        history = sorted(history, key=lambda s: s.timestamp)
        oldest = history[0]
        newest = history[-1]

        # Calculate growth
        sub_growth = newest.subscriber_count - oldest.subscriber_count
        sub_growth_pct = (sub_growth / oldest.subscriber_count * 100) if oldest.subscriber_count > 0 else 0.0

        view_growth = newest.view_count - oldest.view_count
        view_growth_pct = (view_growth / oldest.view_count * 100) if oldest.view_count > 0 else 0.0

        video_growth = newest.video_count - oldest.video_count

        # Calculate average daily views
        days_diff = (newest.timestamp - oldest.timestamp).days
        avg_daily = view_growth / days_diff if days_diff > 0 else 0.0

        return cls(
            channel_id=channel_id,
            period_days=period_days,
            subscriber_growth=sub_growth,
            subscriber_growth_percent=sub_growth_pct,
            view_growth=view_growth,
            view_growth_percent=view_growth_pct,
            video_growth=video_growth,
            avg_daily_views=avg_daily
        )


@dataclass
class VideoStats:
    """Historical statistics for a video"""
    video_id: str
    timestamp: datetime
    view_count: int
    like_count: int
    comment_count: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VideoStats':
        """Create from dictionary"""
        if isinstance(data['timestamp'], str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


@dataclass
class ChangeDetection:
    """Detected changes in channel and video data"""
    new_videos: List[Video]
    updated_videos: List[tuple[Video, Dict[str, int]]]  # (video, changes_dict)
    channel_changes: Dict[str, int]  # metric -> change

    def has_changes(self) -> bool:
        """Check if there are any changes"""
        return bool(self.new_videos or self.updated_videos or self.channel_changes)

    def get_summary(self) -> str:
        """Get a human-readable summary of changes"""
        parts = []

        if self.new_videos:
            parts.append(f"{len(self.new_videos)} new video{'s' if len(self.new_videos) > 1 else ''}")

        if self.updated_videos:
            parts.append(f"{len(self.updated_videos)} video{'s' if len(self.updated_videos) > 1 else ''} updated")

        if self.channel_changes:
            channel_parts = []
            if 'subscribers' in self.channel_changes:
                diff = self.channel_changes['subscribers']
                channel_parts.append(f"{diff:+,} subscribers")
            if 'views' in self.channel_changes:
                diff = self.channel_changes['views']
                channel_parts.append(f"{diff:+,} views")
            if channel_parts:
                parts.append(", ".join(channel_parts))

        return " | ".join(parts) if parts else "No changes"


@dataclass
class AlertThreshold:
    """Configuration for an alert threshold"""
    metric: str  # e.g., "subscribers", "views", "engagement_rate"
    operator: str  # e.g., ">=", "<=", ">", "<", "=="
    value: float  # threshold value
    alert_type: str  # "success", "warning", "danger"
    message: str  # custom message template
    enabled: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AlertThreshold':
        """Create from dictionary"""
        return cls(**data)


@dataclass
class Alert:
    """An alert that was triggered"""
    id: Optional[int] = None
    channel_id: Optional[str] = None
    video_id: Optional[str] = None
    metric: str = ""
    threshold_value: float = 0.0
    actual_value: float = 0.0
    alert_type: str = "success"  # "success", "warning", "danger"
    message: str = ""
    triggered_at: Optional[datetime] = None
    acknowledged: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        if self.triggered_at:
            data['triggered_at'] = self.triggered_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Alert':
        """Create from dictionary"""
        if isinstance(data.get('triggered_at'), str):
            data['triggered_at'] = datetime.fromisoformat(data['triggered_at'])
        return cls(**data)


@dataclass
class VideoFilter:
    """Filter criteria for video lists"""
    # Date range filter
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None

    # Views range filter
    views_min: Optional[int] = None
    views_max: Optional[int] = None

    # Likes range filter
    likes_min: Optional[int] = None
    likes_max: Optional[int] = None

    # Comments range filter
    comments_min: Optional[int] = None
    comments_max: Optional[int] = None

    # Engagement rate filter
    engagement_min: Optional[float] = None
    engagement_max: Optional[float] = None

    # Text search
    search_text: Optional[str] = None

    def is_active(self) -> bool:
        """Check if any filter is active"""
        return any([
            self.date_from is not None,
            self.date_to is not None,
            self.views_min is not None,
            self.views_max is not None,
            self.likes_min is not None,
            self.likes_max is not None,
            self.comments_min is not None,
            self.comments_max is not None,
            self.engagement_min is not None,
            self.engagement_max is not None,
            self.search_text is not None and self.search_text != ""
        ])

    def matches(self, video: Video) -> bool:
        """Check if video matches all filter criteria"""
        # Date range
        if self.date_from and video.published_at < self.date_from:
            return False
        if self.date_to and video.published_at > self.date_to:
            return False

        # Views range
        if self.views_min is not None and video.view_count < self.views_min:
            return False
        if self.views_max is not None and video.view_count > self.views_max:
            return False

        # Likes range
        if self.likes_min is not None and video.like_count < self.likes_min:
            return False
        if self.likes_max is not None and video.like_count > self.likes_max:
            return False

        # Comments range
        if self.comments_min is not None and video.comment_count < self.comments_min:
            return False
        if self.comments_max is not None and video.comment_count > self.comments_max:
            return False

        # Engagement rate
        if self.engagement_min is not None and video.engagement_rate < self.engagement_min:
            return False
        if self.engagement_max is not None and video.engagement_rate > self.engagement_max:
            return False

        # Text search
        if self.search_text and self.search_text.lower() not in video.title.lower():
            return False

        return True

    def get_summary(self) -> str:
        """Get human-readable summary of active filters"""
        parts = []

        if self.date_from or self.date_to:
            if self.date_from and self.date_to:
                parts.append(f"Date: {self.date_from.strftime('%Y-%m-%d')} to {self.date_to.strftime('%Y-%m-%d')}")
            elif self.date_from:
                parts.append(f"Date: from {self.date_from.strftime('%Y-%m-%d')}")
            else:
                parts.append(f"Date: until {self.date_to.strftime('%Y-%m-%d')}")

        if self.views_min or self.views_max:
            if self.views_min and self.views_max:
                parts.append(f"Views: {self.views_min:,}-{self.views_max:,}")
            elif self.views_min:
                parts.append(f"Views: ≥{self.views_min:,}")
            else:
                parts.append(f"Views: ≤{self.views_max:,}")

        if self.likes_min or self.likes_max:
            if self.likes_min and self.likes_max:
                parts.append(f"Likes: {self.likes_min:,}-{self.likes_max:,}")
            elif self.likes_min:
                parts.append(f"Likes: ≥{self.likes_min:,}")
            else:
                parts.append(f"Likes: ≤{self.likes_max:,}")

        if self.comments_min or self.comments_max:
            if self.comments_min and self.comments_max:
                parts.append(f"Comments: {self.comments_min:,}-{self.comments_max:,}")
            elif self.comments_min:
                parts.append(f"Comments: ≥{self.comments_min:,}")
            else:
                parts.append(f"Comments: ≤{self.comments_max:,}")

        if self.engagement_min or self.engagement_max:
            if self.engagement_min and self.engagement_max:
                parts.append(f"Engagement: {self.engagement_min:.1f}%-{self.engagement_max:.1f}%")
            elif self.engagement_min:
                parts.append(f"Engagement: ≥{self.engagement_min:.1f}%")
            else:
                parts.append(f"Engagement: ≤{self.engagement_max:.1f}%")

        if self.search_text:
            parts.append(f"Search: '{self.search_text}'")

        return " | ".join(parts) if parts else "No filters"


@dataclass
class DayOfWeekPattern:
    """Performance pattern for a specific day of the week"""
    day_name: str  # Monday, Tuesday, etc.
    day_index: int  # 0 = Monday, 6 = Sunday
    video_count: int
    avg_views: float
    avg_engagement: float
    avg_like_ratio: float
    total_views: int

    @property
    def performance_score(self) -> float:
        """Calculate overall performance score for this day"""
        if self.video_count == 0:
            return 0.0
        # Weighted score: 40% views, 40% engagement, 20% like ratio
        normalized_views = min(self.avg_views / 10000, 10.0)  # Cap at 100K views = 10 points
        return (normalized_views * 0.4) + (self.avg_engagement * 0.4) + (self.avg_like_ratio * 0.2)


@dataclass
class HourOfDayPattern:
    """Performance pattern for a specific hour of the day"""
    hour: int  # 0-23
    video_count: int
    avg_views: float
    avg_engagement: float
    avg_like_ratio: float
    total_views: int

    @property
    def performance_score(self) -> float:
        """Calculate overall performance score for this hour"""
        if self.video_count == 0:
            return 0.0
        normalized_views = min(self.avg_views / 10000, 10.0)
        return (normalized_views * 0.4) + (self.avg_engagement * 0.4) + (self.avg_like_ratio * 0.2)


@dataclass
class SeasonalPattern:
    """Performance pattern for a specific month or season"""
    month: int  # 1-12
    month_name: str
    video_count: int
    avg_views: float
    avg_engagement: float
    avg_like_ratio: float
    total_views: int

    @property
    def performance_score(self) -> float:
        """Calculate overall performance score for this month"""
        if self.video_count == 0:
            return 0.0
        normalized_views = min(self.avg_views / 10000, 10.0)
        return (normalized_views * 0.4) + (self.avg_engagement * 0.4) + (self.avg_like_ratio * 0.2)


@dataclass
class PublicationRecommendation:
    """Recommendation for optimal publication timing"""
    best_day: str
    best_day_score: float
    best_hour: int
    best_hour_score: float
    best_month: str
    best_month_score: float
    worst_day: str
    worst_day_score: float
    worst_hour: int
    worst_hour_score: float
    worst_month: str
    worst_month_score: float

    def get_summary(self) -> str:
        """Get human-readable summary of recommendations"""
        return f"Best: {self.best_day} at {self.best_hour}:00 (Score: {self.best_day_score:.1f}) | Worst: {self.worst_day} at {self.worst_hour}:00"


@dataclass
class ChannelComparison:
    """Comparison metrics for a channel"""
    channel_id: str
    channel_name: str
    subscriber_count: int
    video_count: int
    total_views: int
    avg_views_per_video: float
    avg_engagement_rate: float
    subscriber_growth: int
    subscriber_growth_percent: float
    view_growth: int
    view_growth_percent: float

    @property
    def performance_score(self) -> float:
        """Calculate overall performance score"""
        # Weighted score based on key metrics
        # 30% engagement, 30% growth rate, 40% views per video (normalized)
        normalized_views = min(self.avg_views_per_video / 10000, 10.0)  # Cap at 100K = 10 points
        normalized_engagement = min(self.avg_engagement_rate, 10.0)
        normalized_growth = min(abs(self.subscriber_growth_percent) / 10, 10.0)  # Cap at 100% = 10 points

        return (normalized_engagement * 0.3) + (normalized_growth * 0.3) + (normalized_views * 0.4)


@dataclass
class TitlePattern:
    """Analysis of title patterns from successful videos"""
    avg_length: float  # Average title length in characters
    avg_word_count: float  # Average number of words
    common_words: List[tuple[str, int]]  # (word, frequency) tuples
    top_keywords: List[tuple[str, float]]  # (keyword, avg_performance_score) tuples
    length_correlation: str  # "short", "medium", "long" - best performing length

    def get_summary(self) -> str:
        """Get human-readable summary"""
        top_3_keywords = ", ".join([kw for kw, _ in self.top_keywords[:3]])
        return f"Avg length: {self.avg_length:.0f} chars, {self.avg_word_count:.0f} words | Top keywords: {top_3_keywords}"


@dataclass
class TagAnalysis:
    """Analysis of tag usage and performance"""
    tag: str
    frequency: int  # Number of videos with this tag
    avg_views: float  # Average views for videos with this tag
    avg_engagement: float  # Average engagement rate
    performance_score: float  # Weighted performance score

    def __lt__(self, other):
        """Enable sorting by performance score"""
        return self.performance_score < other.performance_score


@dataclass
class TitleTagInsights:
    """Combined insights from title and tag analysis"""
    channel_name: str
    analyzed_video_count: int
    title_pattern: TitlePattern
    top_tags: List[TagAnalysis]  # Top performing tags
    suggested_tags: List[str]  # Suggested tags based on high-performing videos
    suggested_keywords: List[str]  # Suggested keywords for titles

    def get_summary(self) -> str:
        """Get human-readable summary"""
        return f"Analyzed {self.analyzed_video_count} videos | {self.title_pattern.get_summary()}"
