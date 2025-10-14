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
