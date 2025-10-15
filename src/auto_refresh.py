"""Auto-Refresh Manager for SuperTube"""

import asyncio
from typing import Optional, Dict, List, Callable
from datetime import datetime, timedelta

from .quota_manager import QuotaManager
from .models import Channel


class AutoRefreshManager:
    """
    Manages intelligent background refresh of YouTube data

    Features:
    - Non-blocking background refresh
    - Priority-based refresh (active channels get refreshed more often)
    - Quota-aware (doesn't refresh if quota is low)
    - Watch mode for real-time monitoring
    """

    def __init__(
        self,
        refresh_callback: Callable,
        quota_manager: QuotaManager,
        default_interval_minutes: int = 30
    ):
        """
        Initialize auto-refresh manager

        Args:
            refresh_callback: Async function to call for refreshing data
            quota_manager: QuotaManager instance for quota tracking
            default_interval_minutes: Default refresh interval in minutes
        """
        self.refresh_callback = refresh_callback
        self.quota_manager = quota_manager
        self.default_interval = default_interval_minutes * 60  # Convert to seconds

        self.enabled = False
        self.watch_mode = False
        self.watch_channel_id: Optional[str] = None
        self.refresh_task: Optional[asyncio.Task] = None

        self.last_refresh: Optional[datetime] = None
        self.next_refresh: Optional[datetime] = None

        # Channel-specific refresh priorities
        self.channel_priorities: Dict[str, int] = {}  # channel_id -> priority (seconds)

    async def start(self) -> None:
        """Start auto-refresh in background"""
        if self.enabled:
            return  # Already running

        self.enabled = True
        self.last_refresh = datetime.now()
        self._calculate_next_refresh()

        # Start background task
        self.refresh_task = asyncio.create_task(self._refresh_loop())

    async def stop(self) -> None:
        """Stop auto-refresh"""
        self.enabled = False
        if self.refresh_task:
            self.refresh_task.cancel()
            try:
                await self.refresh_task
            except asyncio.CancelledError:
                pass
            self.refresh_task = None

    async def enable_watch_mode(self, channel_id: str) -> None:
        """
        Enable watch mode for a specific channel (refresh every 5 min)

        Args:
            channel_id: Channel to monitor in watch mode
        """
        self.watch_mode = True
        self.watch_channel_id = channel_id
        self._calculate_next_refresh()

    async def disable_watch_mode(self) -> None:
        """Disable watch mode, return to normal intervals"""
        self.watch_mode = False
        self.watch_channel_id = None
        self._calculate_next_refresh()

    def set_channel_priority(self, channel_id: str, priority: str) -> None:
        """
        Set refresh priority for a channel

        Args:
            channel_id: Channel ID
            priority: Priority level ("high", "normal", "low")
        """
        priority_intervals = {
            "high": 15 * 60,      # 15 minutes
            "normal": 30 * 60,    # 30 minutes
            "low": 60 * 60        # 60 minutes
        }

        self.channel_priorities[channel_id] = priority_intervals.get(priority, self.default_interval)

    def calculate_channel_priority(self, channel: Channel) -> str:
        """
        Automatically determine channel priority based on activity

        Args:
            channel: Channel object

        Returns:
            Priority level ("high", "normal", "low")
        """
        # This would need video data to determine last upload
        # For now, return "normal" - can be enhanced later
        return "normal"

    def _calculate_next_refresh(self) -> None:
        """Calculate when next refresh should occur"""
        if not self.last_refresh:
            self.last_refresh = datetime.now()

        if self.watch_mode:
            # Watch mode: refresh every 5 minutes
            interval = 5 * 60
        else:
            # Normal mode: use default interval
            interval = self.default_interval

        self.next_refresh = self.last_refresh + timedelta(seconds=interval)

    def get_time_until_next_refresh(self) -> Optional[int]:
        """
        Get seconds until next refresh

        Returns:
            Seconds until next refresh, or None if not scheduled
        """
        if not self.next_refresh:
            return None

        remaining = (self.next_refresh - datetime.now()).total_seconds()
        return max(0, int(remaining))

    def get_status_display(self) -> str:
        """
        Get status display string for UI

        Returns:
            Status string (e.g., "🟢 Auto: ON | Next: 5m")
        """
        if not self.enabled:
            return "🔴 Auto: OFF"

        time_until = self.get_time_until_next_refresh()
        if time_until is None:
            return "🟡 Auto: ON"

        # Format time
        if time_until < 60:
            time_str = f"{time_until}s"
        else:
            minutes = time_until // 60
            time_str = f"{minutes}m"

        if self.watch_mode:
            return f"🔴 WATCH MODE | Next: {time_str}"
        else:
            return f"🟢 Auto: ON | Next: {time_str}"

    async def _refresh_loop(self) -> None:
        """Main refresh loop running in background"""
        while self.enabled:
            try:
                # Check if it's time to refresh
                if self.next_refresh and datetime.now() >= self.next_refresh:
                    # Check quota before refreshing
                    if self.quota_manager.can_refresh():
                        # Perform refresh
                        await self.refresh_callback()
                        self.last_refresh = datetime.now()
                        self._calculate_next_refresh()
                    else:
                        # Quota exhausted, wait 1 hour
                        self.next_refresh = datetime.now() + timedelta(hours=1)

                # Sleep for 10 seconds before checking again
                await asyncio.sleep(10)

            except asyncio.CancelledError:
                break
            except Exception:
                # Silently continue on errors
                await asyncio.sleep(60)  # Wait 1 min on error

    def force_refresh_now(self) -> None:
        """Force an immediate refresh (resets timer)"""
        self.last_refresh = datetime.now() - timedelta(hours=1)  # Set in past
        self.next_refresh = datetime.now()  # Trigger immediately
