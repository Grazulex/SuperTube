"""YouTube API Quota Management System"""

from typing import Dict
from datetime import datetime, timedelta


class QuotaManager:
    """
    Manages YouTube Data API v3 quota consumption

    Default daily limit: 10,000 units
    Cost reference:
    - channels().list = 1 unit
    - videos().list = 1 unit
    - playlistItems().list = 1 unit
    - search().list = 100 units
    - commentThreads().list = 1 unit
    - comments().list = 1 unit
    """

    # API operation costs
    COSTS = {
        'channel_stats': 1,      # channels().list
        'channel_videos': 1,     # playlistItems().list per request
        'video_details': 1,      # videos().list per batch (50 videos)
        'video_comments': 1,     # commentThreads().list per request
        'search': 100            # search().list (expensive!)
    }

    def __init__(self, daily_limit: int = 10000, safety_threshold: float = 0.90):
        """
        Initialize quota manager

        Args:
            daily_limit: Maximum API units per day (default 10,000)
            safety_threshold: Stop refreshing at this % of quota (default 90%)
        """
        self.daily_limit = daily_limit
        self.safety_threshold = safety_threshold
        self.current_usage = 0
        self.last_reset = datetime.now()
        self.usage_history: Dict[str, int] = {}  # Track usage by operation type

    def reset_if_needed(self) -> None:
        """Reset quota if we've crossed into a new day (UTC)"""
        now = datetime.now()
        if now.date() > self.last_reset.date():
            self.current_usage = 0
            self.usage_history = {}
            self.last_reset = now

    def record_usage(self, operation: str, cost: int = None) -> None:
        """
        Record API usage

        Args:
            operation: Type of operation (e.g., 'channel_stats')
            cost: Cost in units (if None, lookup from COSTS dict)
        """
        self.reset_if_needed()

        if cost is None:
            cost = self.COSTS.get(operation, 1)

        self.current_usage += cost

        # Track by operation type
        if operation in self.usage_history:
            self.usage_history[operation] += cost
        else:
            self.usage_history[operation] = cost

    def can_refresh(self, estimated_cost: int = None) -> bool:
        """
        Check if we can perform a refresh operation

        Args:
            estimated_cost: Estimated cost of the operation

        Returns:
            True if we have quota available, False otherwise
        """
        self.reset_if_needed()

        # Use estimated cost, or default to a typical refresh cost
        # Typical refresh: 1 (channel) + 1 (playlist) + ~2 (videos batch) = ~4 units
        if estimated_cost is None:
            estimated_cost = 4

        safe_limit = int(self.daily_limit * self.safety_threshold)
        return (self.current_usage + estimated_cost) < safe_limit

    def get_remaining_quota(self) -> int:
        """Get remaining quota for today"""
        self.reset_if_needed()
        return max(0, self.daily_limit - self.current_usage)

    def get_usage_percentage(self) -> float:
        """Get current usage as percentage of daily limit"""
        self.reset_if_needed()
        return (self.current_usage / self.daily_limit) * 100

    def estimate_channel_refresh_cost(self, max_videos: int = 50) -> int:
        """
        Estimate cost of refreshing a single channel

        Args:
            max_videos: Number of videos to fetch

        Returns:
            Estimated cost in API units
        """
        cost = 0
        cost += self.COSTS['channel_stats']  # 1 unit
        cost += self.COSTS['channel_videos']  # 1 unit for playlist

        # Video details are batched 50 per request
        video_batches = (max_videos + 49) // 50
        cost += video_batches * self.COSTS['video_details']

        return cost

    def get_status_summary(self) -> str:
        """Get human-readable status summary"""
        self.reset_if_needed()

        usage_pct = self.get_usage_percentage()
        remaining = self.get_remaining_quota()

        if usage_pct < 50:
            status = "🟢 Good"
        elif usage_pct < 80:
            status = "🟡 Moderate"
        elif usage_pct < 90:
            status = "🟠 High"
        else:
            status = "🔴 Critical"

        return f"{status} | Used: {self.current_usage:,}/{self.daily_limit:,} ({usage_pct:.1f}%) | Remaining: {remaining:,}"
