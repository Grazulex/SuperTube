"""Configuration loader for SuperTube"""

from typing import List, Dict, Any
from dataclasses import dataclass
import yaml
from pathlib import Path


@dataclass
class ChannelConfig:
    """Configuration for a single YouTube channel"""
    name: str
    channel_id: str
    description: str


@dataclass
class AutoRefreshSettings:
    """Auto-refresh configuration"""
    enabled: bool = False
    interval_minutes: int = 30
    quota_limit: int = 10000
    quota_safety_threshold: float = 0.90


@dataclass
class AppSettings:
    """Application settings"""
    cache_ttl: int = 3600
    max_videos: int = 50
    auto_refresh: int = 0  # Legacy field (kept for compatibility)
    auto_refresh_config: AutoRefreshSettings = None


@dataclass
class Config:
    """Main configuration"""
    channels: List[ChannelConfig]
    settings: AppSettings

    @classmethod
    def load(cls, config_path: str = "/app/config/config.yaml") -> 'Config':
        """
        Load configuration from YAML file

        Args:
            config_path: Path to config.yaml

        Returns:
            Config object

        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If config is invalid
        """
        if not Path(config_path).exists():
            raise FileNotFoundError(
                f"Configuration file not found: {config_path}\n"
                "Please copy config.yaml.example to config.yaml and fill in your channel IDs."
            )

        with open(config_path, 'r') as f:
            data = yaml.safe_load(f)

        # Parse channels
        channels = []
        for ch_data in data.get('channels', []):
            channels.append(ChannelConfig(
                name=ch_data['name'],
                channel_id=ch_data['channel_id'],
                description=ch_data.get('description', '')
            ))

        if not channels:
            raise ValueError("No channels configured. Please add at least one channel to config.yaml")

        # Parse settings
        settings_data = data.get('settings', {})

        # Parse auto-refresh config
        auto_refresh_data = settings_data.get('auto_refresh_config', {})
        auto_refresh_config = AutoRefreshSettings(
            enabled=auto_refresh_data.get('enabled', False),
            interval_minutes=auto_refresh_data.get('interval_minutes', 30),
            quota_limit=auto_refresh_data.get('quota_limit', 10000),
            quota_safety_threshold=auto_refresh_data.get('quota_safety_threshold', 0.90)
        )

        settings = AppSettings(
            cache_ttl=settings_data.get('cache_ttl', 3600),
            max_videos=settings_data.get('max_videos', 50),
            auto_refresh=settings_data.get('auto_refresh', 0),
            auto_refresh_config=auto_refresh_config
        )

        return cls(channels=channels, settings=settings)
