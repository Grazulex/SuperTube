"""Alert system for threshold-based notifications"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import operator as op

from .models import Alert, AlertThreshold, Channel, Video, ChannelStats


class AlertManager:
    """Manages alert thresholds and triggers alerts when conditions are met"""

    # Operator mapping
    OPERATORS = {
        ">=": op.ge,
        "<=": op.le,
        ">": op.gt,
        "<": op.lt,
        "==": op.eq,
    }

    def __init__(self, thresholds: List[AlertThreshold]):
        """
        Initialize alert manager with thresholds

        Args:
            thresholds: List of alert threshold configurations
        """
        self.thresholds = [t for t in thresholds if t.enabled]

    def check_channel_alerts(self, channel: Channel, previous_stats: Optional[ChannelStats] = None) -> List[Alert]:
        """
        Check if channel metrics exceed any thresholds

        Args:
            channel: Current channel data
            previous_stats: Previous channel stats for comparison (optional)

        Returns:
            List of triggered alerts
        """
        alerts = []

        for threshold in self.thresholds:
            # Skip video-specific thresholds
            if threshold.metric in ["engagement_rate", "like_ratio", "views_per_day"]:
                continue

            # Get current metric value
            current_value = self._get_channel_metric(channel, threshold.metric)
            if current_value is None:
                continue

            # Calculate growth if comparing with previous stats
            if previous_stats and threshold.metric.endswith("_growth"):
                base_metric = threshold.metric.replace("_growth", "")
                previous_value = self._get_channel_metric_from_stats(previous_stats, base_metric)
                if previous_value and previous_value > 0:
                    current_value = ((current_value - previous_value) / previous_value) * 100
                else:
                    continue

            # Check threshold
            if self._check_threshold(current_value, threshold):
                alert = Alert(
                    channel_id=channel.id,
                    metric=threshold.metric,
                    threshold_value=threshold.value,
                    actual_value=current_value,
                    alert_type=threshold.alert_type,
                    message=self._format_message(threshold.message, channel.name, current_value, threshold.value),
                    triggered_at=datetime.now()
                )
                alerts.append(alert)

        return alerts

    def check_video_alerts(self, video: Video, channel_name: str) -> List[Alert]:
        """
        Check if video metrics exceed any thresholds

        Args:
            video: Video data
            channel_name: Name of the channel (for message formatting)

        Returns:
            List of triggered alerts
        """
        alerts = []

        for threshold in self.thresholds:
            # Get current metric value
            current_value = self._get_video_metric(video, threshold.metric)
            if current_value is None:
                continue

            # Check threshold
            if self._check_threshold(current_value, threshold):
                alert = Alert(
                    channel_id=video.channel_id,
                    video_id=video.id,
                    metric=threshold.metric,
                    threshold_value=threshold.value,
                    actual_value=current_value,
                    alert_type=threshold.alert_type,
                    message=self._format_message(threshold.message, video.title, current_value, threshold.value),
                    triggered_at=datetime.now()
                )
                alerts.append(alert)

        return alerts

    def _get_channel_metric(self, channel: Channel, metric: str) -> Optional[float]:
        """Extract metric value from channel"""
        metric_map = {
            "subscribers": channel.subscriber_count,
            "subscriber_count": channel.subscriber_count,
            "views": channel.view_count,
            "view_count": channel.view_count,
            "videos": channel.video_count,
            "video_count": channel.video_count,
        }
        return float(metric_map.get(metric, 0)) if metric in metric_map else None

    def _get_channel_metric_from_stats(self, stats: ChannelStats, metric: str) -> Optional[float]:
        """Extract metric value from channel stats"""
        metric_map = {
            "subscribers": stats.subscriber_count,
            "subscriber_count": stats.subscriber_count,
            "views": stats.view_count,
            "view_count": stats.view_count,
            "videos": stats.video_count,
            "video_count": stats.video_count,
        }
        return float(metric_map.get(metric, 0)) if metric in metric_map else None

    def _get_video_metric(self, video: Video, metric: str) -> Optional[float]:
        """Extract metric value from video"""
        metric_map = {
            "views": video.view_count,
            "view_count": video.view_count,
            "likes": video.like_count,
            "like_count": video.like_count,
            "comments": video.comment_count,
            "comment_count": video.comment_count,
            "engagement_rate": video.engagement_rate,
            "like_ratio": video.like_ratio,
        }
        return float(metric_map.get(metric, 0)) if metric in metric_map else None

    def _check_threshold(self, value: float, threshold: AlertThreshold) -> bool:
        """Check if value meets threshold condition"""
        operator_func = self.OPERATORS.get(threshold.operator)
        if not operator_func:
            return False
        return operator_func(value, threshold.value)

    def _format_message(self, template: str, name: str, actual: float, threshold: float) -> str:
        """Format alert message with actual values"""
        return template.format(
            name=name,
            actual=actual,
            threshold=threshold,
            actual_int=int(actual),
            threshold_int=int(threshold)
        )

    @staticmethod
    def get_default_thresholds() -> List[AlertThreshold]:
        """Get default alert thresholds"""
        return [
            # Channel subscriber milestones (success alerts)
            AlertThreshold(
                metric="subscribers",
                operator=">=",
                value=1000,
                alert_type="success",
                message="🎉 {name} reached {actual_int:,} subscribers!",
                enabled=True
            ),
            AlertThreshold(
                metric="subscribers",
                operator=">=",
                value=10000,
                alert_type="success",
                message="🎉 {name} reached {actual_int:,} subscribers!",
                enabled=True
            ),
            AlertThreshold(
                metric="subscribers",
                operator=">=",
                value=100000,
                alert_type="success",
                message="🎉🎉 {name} reached {actual_int:,} subscribers!",
                enabled=True
            ),

            # Video view milestones (success alerts)
            AlertThreshold(
                metric="views",
                operator=">=",
                value=10000,
                alert_type="success",
                message="📈 Video '{name}' reached {actual_int:,} views!",
                enabled=True
            ),
            AlertThreshold(
                metric="views",
                operator=">=",
                value=100000,
                alert_type="success",
                message="🔥 Video '{name}' reached {actual_int:,} views!",
                enabled=True
            ),

            # Engagement warnings (low engagement)
            AlertThreshold(
                metric="engagement_rate",
                operator="<",
                value=1.0,
                alert_type="warning",
                message="⚠️ Low engagement on '{name}': {actual:.2f}%",
                enabled=True
            ),

            # High engagement (success)
            AlertThreshold(
                metric="engagement_rate",
                operator=">=",
                value=5.0,
                alert_type="success",
                message="✨ High engagement on '{name}': {actual:.2f}%",
                enabled=True
            ),
        ]
