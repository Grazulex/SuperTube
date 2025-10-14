"""Growth prediction and projection module for channel statistics"""

from typing import List, Optional, Tuple
from datetime import datetime, timedelta

from .models import ChannelStats, GrowthProjection, MilestoneProjection


class GrowthPredictor:
    """Predicts future growth based on historical data"""

    def __init__(self, history: List[ChannelStats]):
        """
        Initialize predictor with historical data

        Args:
            history: List of ChannelStats objects, ordered by timestamp
        """
        self.history = sorted(history, key=lambda s: s.timestamp)

    def _calculate_confidence(self, data_points: int, r_squared: float) -> float:
        """
        Calculate confidence score based on data quality

        Args:
            data_points: Number of historical data points
            r_squared: R-squared value from regression (0.0 to 1.0)

        Returns:
            Confidence score (0.0 to 1.0)
        """
        # Confidence based on:
        # - Data points: more points = higher confidence (capped at 30 points)
        # - R-squared: how well the line fits the data

        data_score = min(data_points / 30.0, 1.0)
        fit_score = r_squared

        # Weighted average: 40% data points, 60% fit quality
        confidence = (data_score * 0.4) + (fit_score * 0.6)
        return max(0.0, min(1.0, confidence))

    def _linear_regression(self, x: List[float], y: List[float]) -> Tuple[float, float, float]:
        """
        Calculate linear regression: y = slope * x + intercept

        Args:
            x: Independent variable (e.g., day numbers)
            y: Dependent variable (e.g., subscriber counts)

        Returns:
            Tuple of (slope, intercept, r_squared)
        """
        if len(x) < 2 or len(y) < 2 or len(x) != len(y):
            return (0.0, 0.0, 0.0)

        n = len(x)

        # Calculate means
        x_mean = sum(x) / n
        y_mean = sum(y) / n

        # Calculate slope
        numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))

        if denominator == 0:
            return (0.0, y_mean, 0.0)

        slope = numerator / denominator
        intercept = y_mean - (slope * x_mean)

        # Calculate R-squared
        y_predicted = [slope * x[i] + intercept for i in range(n)]
        ss_total = sum((y[i] - y_mean) ** 2 for i in range(n))
        ss_residual = sum((y[i] - y_predicted[i]) ** 2 for i in range(n))

        if ss_total == 0:
            r_squared = 0.0
        else:
            r_squared = 1.0 - (ss_residual / ss_total)
            r_squared = max(0.0, min(1.0, r_squared))

        return (slope, intercept, r_squared)

    def project_subscribers(self, days_ahead: int = 90) -> GrowthProjection:
        """
        Project subscriber growth

        Args:
            days_ahead: Maximum days to project (default 90)

        Returns:
            GrowthProjection for subscribers
        """
        if len(self.history) < 2:
            # Not enough data
            current = self.history[0].subscriber_count if self.history else 0
            return GrowthProjection(
                metric="subscribers",
                current_value=current,
                projected_30d=current,
                projected_60d=current,
                projected_90d=current,
                daily_growth_rate=0.0,
                confidence=0.0
            )

        # Prepare data for regression
        start_date = self.history[0].timestamp
        x_days = [(stat.timestamp - start_date).days for stat in self.history]
        y_subs = [stat.subscriber_count for stat in self.history]

        # Calculate regression
        slope, intercept, r_squared = self._linear_regression(x_days, y_subs)

        # Current values
        current_day = x_days[-1]
        current_subs = y_subs[-1]

        # Project future values
        projected_30d = int(slope * (current_day + 30) + intercept)
        projected_60d = int(slope * (current_day + 60) + intercept)
        projected_90d = int(slope * (current_day + 90) + intercept)

        # Ensure projections don't go negative
        projected_30d = max(current_subs, projected_30d)
        projected_60d = max(current_subs, projected_60d)
        projected_90d = max(current_subs, projected_90d)

        # Calculate confidence
        confidence = self._calculate_confidence(len(self.history), r_squared)

        return GrowthProjection(
            metric="subscribers",
            current_value=current_subs,
            projected_30d=projected_30d,
            projected_60d=projected_60d,
            projected_90d=projected_90d,
            daily_growth_rate=slope,
            confidence=confidence
        )

    def project_views(self, days_ahead: int = 90) -> GrowthProjection:
        """
        Project view count growth

        Args:
            days_ahead: Maximum days to project (default 90)

        Returns:
            GrowthProjection for views
        """
        if len(self.history) < 2:
            # Not enough data
            current = self.history[0].view_count if self.history else 0
            return GrowthProjection(
                metric="views",
                current_value=current,
                projected_30d=current,
                projected_60d=current,
                projected_90d=current,
                daily_growth_rate=0.0,
                confidence=0.0
            )

        # Prepare data for regression
        start_date = self.history[0].timestamp
        x_days = [(stat.timestamp - start_date).days for stat in self.history]
        y_views = [stat.view_count for stat in self.history]

        # Calculate regression
        slope, intercept, r_squared = self._linear_regression(x_days, y_views)

        # Current values
        current_day = x_days[-1]
        current_views = y_views[-1]

        # Project future values
        projected_30d = int(slope * (current_day + 30) + intercept)
        projected_60d = int(slope * (current_day + 60) + intercept)
        projected_90d = int(slope * (current_day + 90) + intercept)

        # Ensure projections don't go negative
        projected_30d = max(current_views, projected_30d)
        projected_60d = max(current_views, projected_60d)
        projected_90d = max(current_views, projected_90d)

        # Calculate confidence
        confidence = self._calculate_confidence(len(self.history), r_squared)

        return GrowthProjection(
            metric="views",
            current_value=current_views,
            projected_30d=projected_30d,
            projected_60d=projected_60d,
            projected_90d=projected_90d,
            daily_growth_rate=slope,
            confidence=confidence
        )

    def calculate_milestone_eta(self, threshold: int, metric: str = "subscribers") -> MilestoneProjection:
        """
        Calculate when a milestone will be reached

        Args:
            threshold: Target value to reach
            metric: "subscribers" or "views"

        Returns:
            MilestoneProjection with ETA
        """
        if len(self.history) < 2:
            # Not enough data
            current = self.history[0].subscriber_count if metric == "subscribers" else self.history[0].view_count if self.history else 0
            return MilestoneProjection(
                metric=metric,
                threshold=threshold,
                current_value=current,
                estimated_date=None,
                days_until=None,
                confidence=0.0,
                achievable=False
            )

        # Prepare data for regression
        start_date = self.history[0].timestamp
        x_days = [(stat.timestamp - start_date).days for stat in self.history]

        if metric == "subscribers":
            y_values = [stat.subscriber_count for stat in self.history]
        else:  # views
            y_values = [stat.view_count for stat in self.history]

        # Calculate regression
        slope, intercept, r_squared = self._linear_regression(x_days, y_values)

        # Current values
        current_day = x_days[-1]
        current_value = y_values[-1]
        current_date = self.history[-1].timestamp

        # Check if milestone already reached
        if current_value >= threshold:
            return MilestoneProjection(
                metric=metric,
                threshold=threshold,
                current_value=current_value,
                estimated_date=current_date,
                days_until=0,
                confidence=1.0,
                achievable=True
            )

        # Check if growth is positive
        if slope <= 0:
            return MilestoneProjection(
                metric=metric,
                threshold=threshold,
                current_value=current_value,
                estimated_date=None,
                days_until=None,
                confidence=0.0,
                achievable=False
            )

        # Calculate days until threshold is reached
        # threshold = slope * (current_day + days_until) + intercept
        # Solve for days_until:
        days_until = (threshold - intercept - slope * current_day) / slope
        days_until = int(days_until)

        if days_until < 0:
            days_until = 0

        estimated_date = current_date + timedelta(days=days_until)

        # Calculate confidence
        confidence = self._calculate_confidence(len(self.history), r_squared)

        return MilestoneProjection(
            metric=metric,
            threshold=threshold,
            current_value=current_value,
            estimated_date=estimated_date,
            days_until=days_until,
            confidence=confidence,
            achievable=True
        )

    def get_common_milestones(self, metric: str = "subscribers") -> List[MilestoneProjection]:
        """
        Calculate ETA for common milestones

        Args:
            metric: "subscribers" or "views"

        Returns:
            List of MilestoneProjections for common thresholds
        """
        if metric == "subscribers":
            # Common subscriber milestones
            thresholds = [1_000, 5_000, 10_000, 50_000, 100_000, 500_000, 1_000_000]
        else:  # views
            # Common view milestones
            thresholds = [10_000, 50_000, 100_000, 500_000, 1_000_000, 5_000_000, 10_000_000]

        # Get current value
        if len(self.history) == 0:
            return []

        if metric == "subscribers":
            current_value = self.history[-1].subscriber_count
        else:
            current_value = self.history[-1].view_count

        # Filter thresholds above current value
        relevant_thresholds = [t for t in thresholds if t > current_value]

        # Calculate projections for next 3 milestones
        milestones = []
        for threshold in relevant_thresholds[:3]:
            milestone = self.calculate_milestone_eta(threshold, metric)
            milestones.append(milestone)

        return milestones
