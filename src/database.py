"""Database manager for caching YouTube statistics"""

import json
import zlib
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from pathlib import Path

import aiosqlite

from .models import Channel, Video, ChannelStats, VideoStats, ChangeDetection, Alert, Comment, VideoSentiment, ChannelSentiment


class DatabaseManager:
    """Async SQLite database manager for caching YouTube data"""

    def __init__(self, db_path: str = "/app/data/supertube.db"):
        """
        Initialize database manager

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._ensure_data_dir()

    def _ensure_data_dir(self):
        """Ensure the data directory exists"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

    def _compress_stats_data(self, stats_list: List[Dict[str, Any]]) -> bytes:
        """
        Compress a list of stats dictionaries using zlib

        Args:
            stats_list: List of stat dictionaries to compress

        Returns:
            Compressed data as bytes
        """
        json_data = json.dumps(stats_list)
        compressed = zlib.compress(json_data.encode('utf-8'), level=9)
        return compressed

    def _decompress_stats_data(self, compressed_data: bytes) -> List[Dict[str, Any]]:
        """
        Decompress zlib-compressed stats data

        Args:
            compressed_data: Compressed data bytes

        Returns:
            List of stat dictionaries
        """
        decompressed = zlib.decompress(compressed_data)
        json_data = decompressed.decode('utf-8')
        return json.loads(json_data)

    async def initialize(self):
        """Create database tables if they don't exist"""
        async with aiosqlite.connect(self.db_path) as db:
            # Channels table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS channels (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    custom_url TEXT,
                    description TEXT,
                    subscriber_count INTEGER,
                    view_count INTEGER,
                    video_count INTEGER,
                    published_at TEXT,
                    thumbnail_url TEXT,
                    last_updated TEXT NOT NULL
                )
            """)

            # Videos table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS videos (
                    id TEXT PRIMARY KEY,
                    channel_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    published_at TEXT NOT NULL,
                    view_count INTEGER,
                    like_count INTEGER,
                    comment_count INTEGER,
                    duration TEXT,
                    thumbnail_url TEXT,
                    last_updated TEXT NOT NULL,
                    FOREIGN KEY (channel_id) REFERENCES channels(id)
                )
            """)

            # Stats history table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS stats_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    channel_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    subscriber_count INTEGER,
                    view_count INTEGER,
                    video_count INTEGER,
                    FOREIGN KEY (channel_id) REFERENCES channels(id)
                )
            """)

            # Video stats history table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS video_stats_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    video_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    view_count INTEGER,
                    like_count INTEGER,
                    comment_count INTEGER,
                    FOREIGN KEY (video_id) REFERENCES videos(id)
                )
            """)

            # Archive tables for long-term compressed storage
            await db.execute("""
                CREATE TABLE IF NOT EXISTS stats_history_archive (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    channel_id TEXT NOT NULL,
                    period_start TEXT NOT NULL,
                    period_end TEXT NOT NULL,
                    compressed_data BLOB NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (channel_id) REFERENCES channels(id)
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS video_stats_history_archive (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    video_id TEXT NOT NULL,
                    period_start TEXT NOT NULL,
                    period_end TEXT NOT NULL,
                    compressed_data BLOB NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (video_id) REFERENCES videos(id)
                )
            """)

            # Create indexes for better query performance
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_videos_channel
                ON videos(channel_id)
            """)

            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_stats_channel
                ON stats_history(channel_id, timestamp)
            """)

            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_video_stats
                ON video_stats_history(video_id, timestamp)
            """)

            # Archive table indexes
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_stats_archive
                ON stats_history_archive(channel_id, period_start, period_end)
            """)

            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_video_stats_archive
                ON video_stats_history_archive(video_id, period_start, period_end)
            """)

            # Alerts table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    channel_id TEXT,
                    video_id TEXT,
                    metric TEXT NOT NULL,
                    threshold_value REAL NOT NULL,
                    actual_value REAL NOT NULL,
                    alert_type TEXT NOT NULL,
                    message TEXT NOT NULL,
                    triggered_at TEXT NOT NULL,
                    acknowledged INTEGER DEFAULT 0,
                    FOREIGN KEY (channel_id) REFERENCES channels(id),
                    FOREIGN KEY (video_id) REFERENCES videos(id)
                )
            """)

            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_alerts_channel
                ON alerts(channel_id, triggered_at)
            """)

            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_alerts_acknowledged
                ON alerts(acknowledged, triggered_at)
            """)

            # Comments table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS comments (
                    id TEXT PRIMARY KEY,
                    video_id TEXT NOT NULL,
                    author TEXT NOT NULL,
                    text TEXT NOT NULL,
                    like_count INTEGER DEFAULT 0,
                    published_at TEXT NOT NULL,
                    parent_id TEXT,
                    sentiment_score REAL,
                    sentiment_label TEXT,
                    last_updated TEXT NOT NULL,
                    FOREIGN KEY (video_id) REFERENCES videos(id),
                    FOREIGN KEY (parent_id) REFERENCES comments(id)
                )
            """)

            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_comments_video
                ON comments(video_id, published_at DESC)
            """)

            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_comments_sentiment
                ON comments(video_id, sentiment_label)
            """)

            await db.commit()

    async def save_channel(self, channel: Channel) -> None:
        """
        Save or update channel data

        Args:
            channel: Channel object to save
        """
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR REPLACE INTO channels
                (id, name, custom_url, description, subscriber_count, view_count,
                 video_count, published_at, thumbnail_url, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                channel.id,
                channel.name,
                channel.custom_url,
                channel.description,
                channel.subscriber_count,
                channel.view_count,
                channel.video_count,
                channel.published_at.isoformat(),
                channel.thumbnail_url,
                datetime.utcnow().isoformat()
            ))
            await db.commit()

    async def get_channel(self, channel_id: str) -> Optional[Channel]:
        """
        Get channel data from cache

        Args:
            channel_id: YouTube channel ID

        Returns:
            Channel object if found, None otherwise
        """
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM channels WHERE id = ?", (channel_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return Channel(
                        id=row['id'],
                        name=row['name'],
                        custom_url=row['custom_url'],
                        description=row['description'],
                        subscriber_count=row['subscriber_count'],
                        view_count=row['view_count'],
                        video_count=row['video_count'],
                        published_at=datetime.fromisoformat(row['published_at']),
                        thumbnail_url=row['thumbnail_url']
                    )
        return None

    async def is_channel_cache_valid(self, channel_id: str, ttl_seconds: int = 3600) -> bool:
        """
        Check if cached channel data is still valid

        Args:
            channel_id: YouTube channel ID
            ttl_seconds: Time-to-live in seconds (default 1 hour)

        Returns:
            True if cache is valid, False otherwise
        """
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT last_updated FROM channels WHERE id = ?", (channel_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    last_updated = datetime.fromisoformat(row['last_updated'])
                    age = (datetime.utcnow() - last_updated).total_seconds()
                    return age < ttl_seconds
        return False

    async def has_stats_for_today(self, channel_id: str) -> bool:
        """
        Check if we already have stats collected in the last 12 hours for a given channel

        Args:
            channel_id: YouTube channel ID

        Returns:
            True if stats exist within last 12 hours, False otherwise
        """
        # Check if we have stats from the last 12 hours
        twelve_hours_ago = datetime.utcnow() - timedelta(hours=12)

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT COUNT(*) as count FROM stats_history
                WHERE channel_id = ? AND timestamp >= ?
            """, (channel_id, twelve_hours_ago.isoformat())) as cursor:
                row = await cursor.fetchone()
                return row['count'] > 0 if row else False

    async def save_videos(self, videos: List[Video]) -> None:
        """
        Save or update multiple videos

        Args:
            videos: List of Video objects to save
        """
        async with aiosqlite.connect(self.db_path) as db:
            for video in videos:
                await db.execute("""
                    INSERT OR REPLACE INTO videos
                    (id, channel_id, title, description, published_at, view_count,
                     like_count, comment_count, duration, thumbnail_url, last_updated)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    video.id,
                    video.channel_id,
                    video.title,
                    video.description,
                    video.published_at.isoformat(),
                    video.view_count,
                    video.like_count,
                    video.comment_count,
                    video.duration,
                    video.thumbnail_url,
                    datetime.utcnow().isoformat()
                ))
            await db.commit()

    async def get_channel_videos(self, channel_id: str, limit: int = 50) -> List[Video]:
        """
        Get videos for a channel from cache

        Args:
            channel_id: YouTube channel ID
            limit: Maximum number of videos to return

        Returns:
            List of Video objects, ordered by published date (newest first)
        """
        videos = []
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT * FROM videos
                WHERE channel_id = ?
                ORDER BY published_at DESC
                LIMIT ?
            """, (channel_id, limit)) as cursor:
                async for row in cursor:
                    videos.append(Video(
                        id=row['id'],
                        channel_id=row['channel_id'],
                        title=row['title'],
                        description=row['description'],
                        published_at=datetime.fromisoformat(row['published_at']),
                        view_count=row['view_count'],
                        like_count=row['like_count'],
                        comment_count=row['comment_count'],
                        duration=row['duration'],
                        thumbnail_url=row['thumbnail_url']
                    ))
        return videos

    async def save_channel_stats(self, channel: Channel) -> None:
        """
        Save or update a snapshot of channel statistics to history.
        If an entry exists for today (same calendar day), update it instead of creating a new one.

        Args:
            channel: Channel object with current stats
        """
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row

            # Get today's start/end in local time
            local_today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            local_today_end = local_today_start + timedelta(days=1)

            # Convert to UTC for comparison with DB timestamps
            utc_now = datetime.utcnow()
            local_now = datetime.now()
            utc_offset = local_now - utc_now

            utc_today_start = local_today_start - utc_offset
            utc_today_end = local_today_end - utc_offset

            # Check if entry exists for today
            async with db.execute("""
                SELECT id FROM stats_history
                WHERE channel_id = ? AND timestamp >= ? AND timestamp < ?
                ORDER BY timestamp DESC LIMIT 1
            """, (channel.id, utc_today_start.isoformat(), utc_today_end.isoformat())) as cursor:
                existing = await cursor.fetchone()

            if existing:
                # Update existing entry for today
                await db.execute("""
                    UPDATE stats_history
                    SET timestamp = ?, subscriber_count = ?, view_count = ?, video_count = ?
                    WHERE id = ?
                """, (
                    datetime.utcnow().isoformat(),
                    channel.subscriber_count,
                    channel.view_count,
                    channel.video_count,
                    existing['id']
                ))
            else:
                # Insert new entry
                await db.execute("""
                    INSERT INTO stats_history
                    (channel_id, timestamp, subscriber_count, view_count, video_count)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    channel.id,
                    datetime.utcnow().isoformat(),
                    channel.subscriber_count,
                    channel.view_count,
                    channel.video_count
                ))

            await db.commit()

    async def get_channel_history(self, channel_id: str, days: int = 30) -> List[ChannelStats]:
        """
        Get historical statistics for a channel.
        Queries both active (hot) and archived (cold) data transparently.

        Args:
            channel_id: YouTube channel ID
            days: Number of days of history to retrieve

        Returns:
            List of ChannelStats objects, ordered by timestamp
        """
        stats = []
        since = datetime.utcnow() - timedelta(days=days)

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row

            # Get hot data (active stats)
            async with db.execute("""
                SELECT channel_id, timestamp, subscriber_count, view_count, video_count
                FROM stats_history
                WHERE channel_id = ? AND timestamp >= ?
                ORDER BY timestamp ASC
            """, (channel_id, since.isoformat())) as cursor:
                async for row in cursor:
                    stats.append(ChannelStats(
                        channel_id=row['channel_id'],
                        timestamp=datetime.fromisoformat(row['timestamp']),
                        subscriber_count=row['subscriber_count'],
                        view_count=row['view_count'],
                        video_count=row['video_count']
                    ))

            # Get cold data (archived stats) if period extends beyond active data
            async with db.execute("""
                SELECT channel_id, period_start, period_end, compressed_data
                FROM stats_history_archive
                WHERE channel_id = ? AND period_end >= ?
                ORDER BY period_start ASC
            """, (channel_id, since.isoformat())) as cursor:
                async for row in cursor:
                    # Decompress and add archived stats
                    archived_stats = self._decompress_stats_data(row['compressed_data'])
                    for stat_dict in archived_stats:
                        # Filter by date range
                        stat_timestamp = datetime.fromisoformat(stat_dict['timestamp'])
                        if stat_timestamp >= since:
                            stats.append(ChannelStats(
                                channel_id=row['channel_id'],
                                timestamp=stat_timestamp,
                                subscriber_count=stat_dict['subscriber_count'],
                                view_count=stat_dict['view_count'],
                                video_count=stat_dict['video_count']
                            ))

        # Sort all stats by timestamp
        stats.sort(key=lambda s: s.timestamp)
        return stats

    async def cleanup_old_history(self, days: int = 365) -> int:
        """
        Remove statistics older than specified days.
        Default is 365 days (1 year) to support long-term retention.

        NOTE: This should typically NOT be called directly.
        Use archive_old_data() instead to archive data >90 days,
        and only cleanup archived data >365 days.

        Args:
            days: Keep history for this many days (default: 365)

        Returns:
            Number of rows deleted
        """
        cutoff = datetime.utcnow() - timedelta(days=days)
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                DELETE FROM stats_history
                WHERE timestamp < ?
            """, (cutoff.isoformat(),))
            deleted = cursor.rowcount
            await db.commit()
            return deleted

    async def archive_old_data(self, days: int = 90) -> Dict[str, int]:
        """
        Archive statistics older than specified days to compressed archive tables.
        Groups data by week for efficient compression.

        Args:
            days: Archive data older than this many days (default: 90)

        Returns:
            Dictionary with counts: {'channel_stats_archived': N, 'video_stats_archived': M}
        """
        cutoff = datetime.utcnow() - timedelta(days=days)
        channel_stats_count = 0
        video_stats_count = 0

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row

            # Archive channel stats by channel and weekly periods
            # Get all unique channels with old data
            async with db.execute("""
                SELECT DISTINCT channel_id FROM stats_history
                WHERE timestamp < ?
            """, (cutoff.isoformat(),)) as cursor:
                channel_ids = [row['channel_id'] async for row in cursor]

            for channel_id in channel_ids:
                # Get old stats for this channel
                async with db.execute("""
                    SELECT * FROM stats_history
                    WHERE channel_id = ? AND timestamp < ?
                    ORDER BY timestamp ASC
                """, (channel_id, cutoff.isoformat())) as cursor:
                    stats_rows = await cursor.fetchall()

                if not stats_rows:
                    continue

                # Group by weeks
                weekly_groups = {}
                for row in stats_rows:
                    timestamp = datetime.fromisoformat(row['timestamp'])
                    # Get start of week (Monday)
                    week_start = timestamp - timedelta(days=timestamp.weekday())
                    week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
                    week_key = week_start.isoformat()

                    if week_key not in weekly_groups:
                        weekly_groups[week_key] = []

                    weekly_groups[week_key].append({
                        'timestamp': row['timestamp'],
                        'subscriber_count': row['subscriber_count'],
                        'view_count': row['view_count'],
                        'video_count': row['video_count']
                    })

                # Compress and save each weekly group
                for week_start, stats_list in weekly_groups.items():
                    week_end = (datetime.fromisoformat(week_start) + timedelta(days=7)).isoformat()
                    compressed = self._compress_stats_data(stats_list)

                    await db.execute("""
                        INSERT INTO stats_history_archive
                        (channel_id, period_start, period_end, compressed_data, created_at)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        channel_id,
                        week_start,
                        week_end,
                        compressed,
                        datetime.utcnow().isoformat()
                    ))
                    channel_stats_count += len(stats_list)

            # Archive video stats by video and weekly periods
            # Get all unique videos with old data
            async with db.execute("""
                SELECT DISTINCT video_id FROM video_stats_history
                WHERE timestamp < ?
            """, (cutoff.isoformat(),)) as cursor:
                video_ids = [row['video_id'] async for row in cursor]

            for video_id in video_ids:
                # Get old stats for this video
                async with db.execute("""
                    SELECT * FROM video_stats_history
                    WHERE video_id = ? AND timestamp < ?
                    ORDER BY timestamp ASC
                """, (video_id, cutoff.isoformat())) as cursor:
                    stats_rows = await cursor.fetchall()

                if not stats_rows:
                    continue

                # Group by weeks
                weekly_groups = {}
                for row in stats_rows:
                    timestamp = datetime.fromisoformat(row['timestamp'])
                    # Get start of week (Monday)
                    week_start = timestamp - timedelta(days=timestamp.weekday())
                    week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
                    week_key = week_start.isoformat()

                    if week_key not in weekly_groups:
                        weekly_groups[week_key] = []

                    weekly_groups[week_key].append({
                        'timestamp': row['timestamp'],
                        'view_count': row['view_count'],
                        'like_count': row['like_count'],
                        'comment_count': row['comment_count']
                    })

                # Compress and save each weekly group
                for week_start, stats_list in weekly_groups.items():
                    week_end = (datetime.fromisoformat(week_start) + timedelta(days=7)).isoformat()
                    compressed = self._compress_stats_data(stats_list)

                    await db.execute("""
                        INSERT INTO video_stats_history_archive
                        (video_id, period_start, period_end, compressed_data, created_at)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        video_id,
                        week_start,
                        week_end,
                        compressed,
                        datetime.utcnow().isoformat()
                    ))
                    video_stats_count += len(stats_list)

            # Delete archived data from main tables
            await db.execute("""
                DELETE FROM stats_history
                WHERE timestamp < ?
            """, (cutoff.isoformat(),))

            await db.execute("""
                DELETE FROM video_stats_history
                WHERE timestamp < ?
            """, (cutoff.isoformat(),))

            await db.commit()

        return {
            'channel_stats_archived': channel_stats_count,
            'video_stats_archived': video_stats_count
        }

    async def save_video_stats(self, videos: List[Video]) -> None:
        """
        Save or update snapshots of video statistics to history.
        If an entry exists for today (same calendar day), update it instead of creating a new one.

        Args:
            videos: List of Video objects with current stats
        """
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            timestamp = datetime.utcnow().isoformat()

            # Get today's start/end in local time
            local_today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            local_today_end = local_today_start + timedelta(days=1)

            # Convert to UTC for comparison with DB timestamps
            utc_now = datetime.utcnow()
            local_now = datetime.now()
            utc_offset = local_now - utc_now

            utc_today_start = local_today_start - utc_offset
            utc_today_end = local_today_end - utc_offset

            for video in videos:
                # Check if entry exists for today
                async with db.execute("""
                    SELECT id FROM video_stats_history
                    WHERE video_id = ? AND timestamp >= ? AND timestamp < ?
                    ORDER BY timestamp DESC LIMIT 1
                """, (video.id, utc_today_start.isoformat(), utc_today_end.isoformat())) as cursor:
                    existing = await cursor.fetchone()

                if existing:
                    # Update existing entry for today
                    await db.execute("""
                        UPDATE video_stats_history
                        SET timestamp = ?, view_count = ?, like_count = ?, comment_count = ?
                        WHERE id = ?
                    """, (
                        timestamp,
                        video.view_count,
                        video.like_count,
                        video.comment_count,
                        existing['id']
                    ))
                else:
                    # Insert new entry
                    await db.execute("""
                        INSERT INTO video_stats_history
                        (video_id, timestamp, view_count, like_count, comment_count)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        video.id,
                        timestamp,
                        video.view_count,
                        video.like_count,
                        video.comment_count
                    ))

            await db.commit()

    async def get_video_history(self, video_id: str, days: int = 30) -> List[VideoStats]:
        """
        Get historical statistics for a video.
        Queries both active (hot) and archived (cold) data transparently.

        Args:
            video_id: YouTube video ID
            days: Number of days of history to retrieve

        Returns:
            List of VideoStats objects, ordered by timestamp
        """
        stats = []
        since = datetime.utcnow() - timedelta(days=days)

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row

            # Get hot data (active stats)
            async with db.execute("""
                SELECT video_id, timestamp, view_count, like_count, comment_count
                FROM video_stats_history
                WHERE video_id = ? AND timestamp >= ?
                ORDER BY timestamp ASC
            """, (video_id, since.isoformat())) as cursor:
                async for row in cursor:
                    stats.append(VideoStats(
                        video_id=row['video_id'],
                        timestamp=datetime.fromisoformat(row['timestamp']),
                        view_count=row['view_count'],
                        like_count=row['like_count'],
                        comment_count=row['comment_count']
                    ))

            # Get cold data (archived stats) if period extends beyond active data
            async with db.execute("""
                SELECT video_id, period_start, period_end, compressed_data
                FROM video_stats_history_archive
                WHERE video_id = ? AND period_end >= ?
                ORDER BY period_start ASC
            """, (video_id, since.isoformat())) as cursor:
                async for row in cursor:
                    # Decompress and add archived stats
                    archived_stats = self._decompress_stats_data(row['compressed_data'])
                    for stat_dict in archived_stats:
                        # Filter by date range
                        stat_timestamp = datetime.fromisoformat(stat_dict['timestamp'])
                        if stat_timestamp >= since:
                            stats.append(VideoStats(
                                video_id=row['video_id'],
                                timestamp=stat_timestamp,
                                view_count=stat_dict['view_count'],
                                like_count=stat_dict['like_count'],
                                comment_count=stat_dict['comment_count']
                            ))

        # Sort all stats by timestamp
        stats.sort(key=lambda s: s.timestamp)
        return stats

    async def detect_changes(self, channel_id: str, new_channel: Channel, new_videos: List[Video]) -> ChangeDetection:
        """
        Detect changes in channel and video data since last check

        Args:
            channel_id: YouTube channel ID
            new_channel: New channel data
            new_videos: New video list

        Returns:
            ChangeDetection object with all detected changes
        """
        # Get old channel data
        old_channel = await self.get_channel(channel_id)
        old_videos = await self.get_channel_videos(channel_id, limit=1000)

        # Create lookup for old videos
        old_videos_dict = {v.id: v for v in old_videos}

        # Detect new videos
        new_video_list = []
        for video in new_videos:
            if video.id not in old_videos_dict:
                new_video_list.append(video)

        # Detect updated videos (significant stat changes)
        updated_videos = []
        for video in new_videos:
            if video.id in old_videos_dict:
                old = old_videos_dict[video.id]
                changes = {}

                # Check for significant view changes (>10 views or >1%)
                view_diff = video.view_count - old.view_count
                if abs(view_diff) > 10 and abs(view_diff) / max(old.view_count, 1) > 0.01:
                    changes['views'] = view_diff

                # Check for like changes
                like_diff = video.like_count - old.like_count
                if like_diff != 0:
                    changes['likes'] = like_diff

                # Check for comment changes
                comment_diff = video.comment_count - old.comment_count
                if comment_diff != 0:
                    changes['comments'] = comment_diff

                if changes:
                    updated_videos.append((video, changes))

        # Detect channel changes
        channel_changes = {}
        if old_channel:
            sub_diff = new_channel.subscriber_count - old_channel.subscriber_count
            if sub_diff != 0:
                channel_changes['subscribers'] = sub_diff

            view_diff = new_channel.view_count - old_channel.view_count
            if view_diff != 0:
                channel_changes['views'] = view_diff

        return ChangeDetection(
            new_videos=new_video_list,
            updated_videos=updated_videos,
            channel_changes=channel_changes
        )

    async def get_top_videos_by_growth(
        self,
        channel_id: str,
        days: int = 7,
        metric: str = "views",
        limit: int = 10
    ) -> List[tuple[Video, float]]:
        """
        Get top performing videos by growth rate over a period

        Args:
            channel_id: YouTube channel ID
            days: Number of days to calculate growth over
            metric: Metric to rank by ('views', 'likes', 'comments', 'engagement')
            limit: Number of top videos to return

        Returns:
            List of (Video, growth_value) tuples, ordered by growth (descending)
        """
        since = datetime.utcnow() - timedelta(days=days)

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row

            # Get videos for channel
            videos = await self.get_channel_videos(channel_id, limit=1000)

            video_growth = []
            for video in videos:
                # Get oldest and newest stats in the period
                async with db.execute("""
                    SELECT view_count, like_count, comment_count, timestamp
                    FROM video_stats_history
                    WHERE video_id = ? AND timestamp >= ?
                    ORDER BY timestamp ASC
                """, (video.id, since.isoformat())) as cursor:
                    stats_list = await cursor.fetchall()

                    if len(stats_list) >= 2:
                        oldest = stats_list[0]
                        newest = stats_list[-1]

                        if metric == "views":
                            growth = newest['view_count'] - oldest['view_count']
                        elif metric == "likes":
                            growth = newest['like_count'] - oldest['like_count']
                        elif metric == "comments":
                            growth = newest['comment_count'] - oldest['comment_count']
                        elif metric == "engagement":
                            # Calculate engagement rate growth
                            old_engagement = (oldest['like_count'] + oldest['comment_count']) / max(oldest['view_count'], 1)
                            new_engagement = (newest['like_count'] + newest['comment_count']) / max(newest['view_count'], 1)
                            growth = (new_engagement - old_engagement) * 100  # Percentage
                        else:
                            growth = 0

                        video_growth.append((video, growth))

            # Sort by growth (descending) and return top N
            video_growth.sort(key=lambda x: x[1], reverse=True)
            return video_growth[:limit]

    async def get_bottom_videos_by_growth(
        self,
        channel_id: str,
        days: int = 7,
        metric: str = "views",
        limit: int = 10
    ) -> List[tuple[Video, float]]:
        """
        Get bottom performing videos by growth rate over a period

        Args:
            channel_id: YouTube channel ID
            days: Number of days to calculate growth over
            metric: Metric to rank by ('views', 'likes', 'comments', 'engagement')
            limit: Number of bottom videos to return

        Returns:
            List of (Video, growth_value) tuples, ordered by growth (ascending)
        """
        since = datetime.utcnow() - timedelta(days=days)

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row

            # Get videos for channel
            videos = await self.get_channel_videos(channel_id, limit=1000)

            video_growth = []
            for video in videos:
                # Get oldest and newest stats in the period
                async with db.execute("""
                    SELECT view_count, like_count, comment_count, timestamp
                    FROM video_stats_history
                    WHERE video_id = ? AND timestamp >= ?
                    ORDER BY timestamp ASC
                """, (video.id, since.isoformat())) as cursor:
                    stats_list = await cursor.fetchall()

                    if len(stats_list) >= 2:
                        oldest = stats_list[0]
                        newest = stats_list[-1]

                        if metric == "views":
                            growth = newest['view_count'] - oldest['view_count']
                        elif metric == "likes":
                            growth = newest['like_count'] - oldest['like_count']
                        elif metric == "comments":
                            growth = newest['comment_count'] - oldest['comment_count']
                        elif metric == "engagement":
                            # Calculate engagement rate growth
                            old_engagement = (oldest['like_count'] + oldest['comment_count']) / max(oldest['view_count'], 1)
                            new_engagement = (newest['like_count'] + newest['comment_count']) / max(newest['view_count'], 1)
                            growth = (new_engagement - old_engagement) * 100  # Percentage
                        else:
                            growth = 0

                        video_growth.append((video, growth))

            # Sort by growth (ascending) and return bottom N
            video_growth.sort(key=lambda x: x[1])
            return video_growth[:limit]

    async def save_alert(self, alert: Alert) -> int:
        """
        Save an alert to the database

        Args:
            alert: Alert object to save

        Returns:
            ID of the saved alert
        """
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                INSERT INTO alerts
                (channel_id, video_id, metric, threshold_value, actual_value,
                 alert_type, message, triggered_at, acknowledged)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                alert.channel_id,
                alert.video_id,
                alert.metric,
                alert.threshold_value,
                alert.actual_value,
                alert.alert_type,
                alert.message,
                alert.triggered_at.isoformat() if alert.triggered_at else datetime.utcnow().isoformat(),
                1 if alert.acknowledged else 0
            ))
            await db.commit()
            return cursor.lastrowid

    async def get_alerts(
        self,
        channel_id: Optional[str] = None,
        acknowledged: Optional[bool] = None,
        limit: int = 50
    ) -> List[Alert]:
        """
        Get alerts from database

        Args:
            channel_id: Filter by channel ID (optional)
            acknowledged: Filter by acknowledged status (optional)
            limit: Maximum number of alerts to return

        Returns:
            List of Alert objects, ordered by triggered_at (newest first)
        """
        alerts = []
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row

            # Build query based on filters
            query = "SELECT * FROM alerts WHERE 1=1"
            params = []

            if channel_id is not None:
                query += " AND channel_id = ?"
                params.append(channel_id)

            if acknowledged is not None:
                query += " AND acknowledged = ?"
                params.append(1 if acknowledged else 0)

            query += " ORDER BY triggered_at DESC LIMIT ?"
            params.append(limit)

            async with db.execute(query, params) as cursor:
                async for row in cursor:
                    alerts.append(Alert(
                        id=row['id'],
                        channel_id=row['channel_id'],
                        video_id=row['video_id'],
                        metric=row['metric'],
                        threshold_value=row['threshold_value'],
                        actual_value=row['actual_value'],
                        alert_type=row['alert_type'],
                        message=row['message'],
                        triggered_at=datetime.fromisoformat(row['triggered_at']),
                        acknowledged=bool(row['acknowledged'])
                    ))
        return alerts

    async def get_alert_history(
        self,
        days: int = 7,
        channel_id: Optional[str] = None
    ) -> List[Alert]:
        """
        Get alert history for a period

        Args:
            days: Number of days of history to retrieve
            channel_id: Filter by channel ID (optional)

        Returns:
            List of Alert objects, ordered by triggered_at (newest first)
        """
        since = datetime.utcnow() - timedelta(days=days)
        alerts = []

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row

            if channel_id:
                query = """
                    SELECT * FROM alerts
                    WHERE channel_id = ? AND triggered_at >= ?
                    ORDER BY triggered_at DESC
                """
                params = (channel_id, since.isoformat())
            else:
                query = """
                    SELECT * FROM alerts
                    WHERE triggered_at >= ?
                    ORDER BY triggered_at DESC
                """
                params = (since.isoformat(),)

            async with db.execute(query, params) as cursor:
                async for row in cursor:
                    alerts.append(Alert(
                        id=row['id'],
                        channel_id=row['channel_id'],
                        video_id=row['video_id'],
                        metric=row['metric'],
                        threshold_value=row['threshold_value'],
                        actual_value=row['actual_value'],
                        alert_type=row['alert_type'],
                        message=row['message'],
                        triggered_at=datetime.fromisoformat(row['triggered_at']),
                        acknowledged=bool(row['acknowledged'])
                    ))
        return alerts

    async def acknowledge_alert(self, alert_id: int) -> None:
        """
        Mark an alert as acknowledged

        Args:
            alert_id: ID of the alert to acknowledge
        """
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE alerts
                SET acknowledged = 1
                WHERE id = ?
            """, (alert_id,))
            await db.commit()

    async def acknowledge_all_alerts(self, channel_id: Optional[str] = None) -> int:
        """
        Mark all alerts as acknowledged

        Args:
            channel_id: Filter by channel ID (optional)

        Returns:
            Number of alerts acknowledged
        """
        async with aiosqlite.connect(self.db_path) as db:
            if channel_id:
                cursor = await db.execute("""
                    UPDATE alerts
                    SET acknowledged = 1
                    WHERE channel_id = ? AND acknowledged = 0
                """, (channel_id,))
            else:
                cursor = await db.execute("""
                    UPDATE alerts
                    SET acknowledged = 1
                    WHERE acknowledged = 0
                """)
            await db.commit()
            return cursor.rowcount

    async def clear_old_alerts(self, days: int = 30) -> int:
        """
        Remove alerts older than specified days

        Args:
            days: Keep alerts for this many days

        Returns:
            Number of alerts deleted
        """
        cutoff = datetime.utcnow() - timedelta(days=days)
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                DELETE FROM alerts
                WHERE triggered_at < ?
            """, (cutoff.isoformat(),))
            await db.commit()
            return cursor.rowcount

    async def save_comments(self, comments: List[Comment]) -> None:
        """
        Save or update multiple comments

        Args:
            comments: List of Comment objects to save
        """
        async with aiosqlite.connect(self.db_path) as db:
            for comment in comments:
                await db.execute("""
                    INSERT OR REPLACE INTO comments
                    (id, video_id, author, text, like_count, published_at,
                     parent_id, sentiment_score, sentiment_label, last_updated)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    comment.id,
                    comment.video_id,
                    comment.author,
                    comment.text,
                    comment.like_count,
                    comment.published_at.isoformat(),
                    comment.parent_id,
                    comment.sentiment_score,
                    comment.sentiment_label,
                    datetime.utcnow().isoformat()
                ))
            await db.commit()

    async def get_video_comments(self, video_id: str, limit: int = 100) -> List[Comment]:
        """
        Get comments for a video from cache

        Args:
            video_id: YouTube video ID
            limit: Maximum number of comments to return

        Returns:
            List of Comment objects, ordered by published date (newest first)
        """
        comments = []
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT * FROM comments
                WHERE video_id = ?
                ORDER BY published_at DESC
                LIMIT ?
            """, (video_id, limit)) as cursor:
                async for row in cursor:
                    comments.append(Comment(
                        id=row['id'],
                        video_id=row['video_id'],
                        author=row['author'],
                        text=row['text'],
                        like_count=row['like_count'],
                        published_at=datetime.fromisoformat(row['published_at']),
                        parent_id=row['parent_id'],
                        sentiment_score=row['sentiment_score'],
                        sentiment_label=row['sentiment_label']
                    ))
        return comments

    async def get_video_sentiment(self, video_id: str) -> Optional[VideoSentiment]:
        """
        Get aggregated sentiment statistics for a video

        Args:
            video_id: YouTube video ID

        Returns:
            VideoSentiment object if comments exist, None otherwise
        """
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row

            # Get sentiment counts
            async with db.execute("""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN sentiment_label = 'positive' THEN 1 ELSE 0 END) as positive,
                    SUM(CASE WHEN sentiment_label = 'neutral' THEN 1 ELSE 0 END) as neutral,
                    SUM(CASE WHEN sentiment_label = 'negative' THEN 1 ELSE 0 END) as negative,
                    AVG(sentiment_score) as avg_sentiment
                FROM comments
                WHERE video_id = ? AND sentiment_score IS NOT NULL
            """, (video_id,)) as cursor:
                row = await cursor.fetchone()

                if not row or row['total'] == 0:
                    return None

                # Get top keywords (simple word frequency)
                async with db.execute("""
                    SELECT text FROM comments
                    WHERE video_id = ? AND sentiment_label IS NOT NULL
                    LIMIT 100
                """, (video_id,)) as text_cursor:
                    word_freq = {}
                    async for text_row in text_cursor:
                        words = text_row['text'].lower().split()
                        for word in words:
                            # Filter out short words and common stop words
                            if len(word) > 3 and word not in ['this', 'that', 'with', 'from', 'have', 'been', 'were']:
                                word_freq[word] = word_freq.get(word, 0) + 1

                    # Get top 5 keywords
                    top_keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:5]

                return VideoSentiment(
                    video_id=video_id,
                    total_comments=row['total'],
                    positive_count=row['positive'] or 0,
                    neutral_count=row['neutral'] or 0,
                    negative_count=row['negative'] or 0,
                    avg_sentiment=row['avg_sentiment'] or 0.0,
                    top_keywords=top_keywords
                )

    async def get_channel_sentiment(self, channel_id: str, limit_videos: int = 20) -> Optional[ChannelSentiment]:
        """
        Get aggregated sentiment statistics for a channel

        Args:
            channel_id: YouTube channel ID
            limit_videos: Number of recent videos to analyze

        Returns:
            ChannelSentiment object if comments exist, None otherwise
        """
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row

            # Get recent videos for this channel
            async with db.execute("""
                SELECT id FROM videos
                WHERE channel_id = ?
                ORDER BY published_at DESC
                LIMIT ?
            """, (channel_id, limit_videos)) as cursor:
                video_ids = [row['id'] async for row in cursor]

            if not video_ids:
                return None

            # Get sentiment counts across all videos
            placeholders = ','.join('?' * len(video_ids))
            async with db.execute(f"""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN sentiment_label = 'positive' THEN 1 ELSE 0 END) as positive,
                    SUM(CASE WHEN sentiment_label = 'neutral' THEN 1 ELSE 0 END) as neutral,
                    SUM(CASE WHEN sentiment_label = 'negative' THEN 1 ELSE 0 END) as negative,
                    AVG(sentiment_score) as avg_sentiment
                FROM comments
                WHERE video_id IN ({placeholders}) AND sentiment_score IS NOT NULL
            """, video_ids) as cursor:
                row = await cursor.fetchone()

                if not row or row['total'] == 0:
                    return None

                # Find videos with high negative feedback (>40% negative)
                videos_with_negative = []
                for vid_id in video_ids:
                    async with db.execute("""
                        SELECT
                            COUNT(*) as total,
                            SUM(CASE WHEN sentiment_label = 'negative' THEN 1 ELSE 0 END) as negative
                        FROM comments
                        WHERE video_id = ? AND sentiment_label IS NOT NULL
                    """, (vid_id,)) as vid_cursor:
                        vid_row = await vid_cursor.fetchone()
                        if vid_row and vid_row['total'] > 0:
                            negative_percent = (vid_row['negative'] / vid_row['total']) * 100
                            if negative_percent > 40:
                                videos_with_negative.append((vid_id, negative_percent))

                # Sort by negative percentage
                videos_with_negative.sort(key=lambda x: x[1], reverse=True)

                return ChannelSentiment(
                    channel_id=channel_id,
                    total_comments=row['total'],
                    positive_count=row['positive'] or 0,
                    neutral_count=row['neutral'] or 0,
                    negative_count=row['negative'] or 0,
                    avg_sentiment=row['avg_sentiment'] or 0.0,
                    videos_analyzed=len(video_ids),
                    videos_with_negative_feedback=videos_with_negative[:5]  # Top 5
                )

    async def export_database(self, output_path: str) -> Dict[str, Any]:
        """
        Export complete database to a SQL file for backup.

        Args:
            output_path: Path where to save the export file

        Returns:
            Dictionary with export metadata
        """
        import shutil
        from pathlib import Path

        # Create backup directory if needed
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Copy database file
        shutil.copy2(self.db_path, output_path)

        # Get database stats
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row

            stats = {}

            # Count records in each table
            for table in ['channels', 'videos', 'stats_history', 'video_stats_history',
                         'stats_history_archive', 'video_stats_history_archive',
                         'alerts', 'comments']:
                async with db.execute(f"SELECT COUNT(*) as count FROM {table}") as cursor:
                    row = await cursor.fetchone()
                    stats[f'{table}_count'] = row['count']

            # Get database size
            db_size = Path(self.db_path).stat().st_size
            export_size = Path(output_path).stat().st_size

            return {
                'export_path': output_path,
                'export_timestamp': datetime.utcnow().isoformat(),
                'database_size_bytes': db_size,
                'export_size_bytes': export_size,
                'tables_stats': stats
            }

    async def purge_old_data(self,
                           purge_stats_days: Optional[int] = None,
                           purge_archive_days: Optional[int] = None,
                           purge_alerts_days: Optional[int] = None) -> Dict[str, int]:
        """
        Manual purge of old data with granular control.

        Args:
            purge_stats_days: Delete stats older than this many days (optional)
            purge_archive_days: Delete archives older than this many days (optional)
            purge_alerts_days: Delete alerts older than this many days (optional)

        Returns:
            Dictionary with deletion counts for each table
        """
        deleted_counts = {}

        async with aiosqlite.connect(self.db_path) as db:
            # Purge old stats
            if purge_stats_days is not None:
                cutoff = datetime.utcnow() - timedelta(days=purge_stats_days)

                cursor = await db.execute("""
                    DELETE FROM stats_history
                    WHERE timestamp < ?
                """, (cutoff.isoformat(),))
                deleted_counts['stats_history'] = cursor.rowcount

                cursor = await db.execute("""
                    DELETE FROM video_stats_history
                    WHERE timestamp < ?
                """, (cutoff.isoformat(),))
                deleted_counts['video_stats_history'] = cursor.rowcount

            # Purge old archives
            if purge_archive_days is not None:
                cutoff = datetime.utcnow() - timedelta(days=purge_archive_days)

                cursor = await db.execute("""
                    DELETE FROM stats_history_archive
                    WHERE period_end < ?
                """, (cutoff.isoformat(),))
                deleted_counts['stats_history_archive'] = cursor.rowcount

                cursor = await db.execute("""
                    DELETE FROM video_stats_history_archive
                    WHERE period_end < ?
                """, (cutoff.isoformat(),))
                deleted_counts['video_stats_history_archive'] = cursor.rowcount

            # Purge old alerts
            if purge_alerts_days is not None:
                cutoff = datetime.utcnow() - timedelta(days=purge_alerts_days)

                cursor = await db.execute("""
                    DELETE FROM alerts
                    WHERE triggered_at < ?
                """, (cutoff.isoformat(),))
                deleted_counts['alerts'] = cursor.rowcount

            await db.commit()

        return deleted_counts
