#!/usr/bin/env python3
"""Test script to verify new features: video stats history and change detection"""
import asyncio
import sys
from datetime import datetime

sys.path.insert(0, '/app')
from src.database import DatabaseManager
from src.models import Video, Channel, ChangeDetection

async def test_features():
    print("=" * 80)
    print("Testing New Features: Video Stats History & Change Detection")
    print("=" * 80)

    db = DatabaseManager('/app/data/supertube.db')
    await db.initialize()

    # Get all channels
    import aiosqlite
    async with aiosqlite.connect(db.db_path) as conn:
        conn.row_factory = aiosqlite.Row
        async with conn.execute('SELECT id, name FROM channels') as cursor:
            channels = await cursor.fetchall()

    print(f"\n📺 Found {len(channels)} channel(s)\n")

    for channel_row in channels:
        channel_id = channel_row['id']
        channel_name = channel_row['name']

        print(f"\n{'─' * 80}")
        print(f"Channel: {channel_name}")
        print(f"{'─' * 80}")

        # 1. Test video stats history table exists
        async with aiosqlite.connect(db.db_path) as conn:
            async with conn.execute("""
                SELECT COUNT(*) as count FROM video_stats_history
                WHERE video_id IN (SELECT id FROM videos WHERE channel_id = ?)
            """, (channel_id,)) as cursor:
                row = await cursor.fetchone()
                video_stats_count = row[0]

        print(f"\n📊 Video Stats History:")
        print(f"  Total video stat snapshots: {video_stats_count}")

        if video_stats_count > 0:
            # Get some examples
            async with aiosqlite.connect(db.db_path) as conn:
                conn.row_factory = aiosqlite.Row
                async with conn.execute("""
                    SELECT v.title, vsh.timestamp, vsh.view_count, vsh.like_count
                    FROM video_stats_history vsh
                    JOIN videos v ON v.id = vsh.video_id
                    WHERE v.channel_id = ?
                    ORDER BY vsh.timestamp DESC
                    LIMIT 3
                """, (channel_id,)) as cursor:
                    rows = await cursor.fetchall()
                    print(f"  Recent snapshots:")
                    for row in rows:
                        print(f"    • {row['title'][:40]}... at {row['timestamp'][:10]}: {row['view_count']:,} views, {row['like_count']:,} likes")
        else:
            print(f"  ⚠️  No video stats history yet - will be collected on next API fetch")

        # 2. Test change detection
        print(f"\n🔍 Change Detection Test:")

        # Get current channel and videos
        channel = await db.get_channel(channel_id)
        videos = await db.get_channel_videos(channel_id, limit=100)

        if channel and videos:
            # Run change detection
            changes = await db.detect_changes(channel_id, channel, videos)

            print(f"  Has changes: {changes.has_changes()}")
            if changes.has_changes():
                print(f"  Summary: {changes.get_summary()}")

                if changes.new_videos:
                    print(f"\n  ✨ New Videos ({len(changes.new_videos)}):")
                    for video in changes.new_videos[:3]:
                        print(f"    • {video.title[:60]}")

                if changes.updated_videos:
                    print(f"\n  📈 Updated Videos ({len(changes.updated_videos)}):")
                    for video, change_dict in changes.updated_videos[:3]:
                        print(f"    • {video.title[:50]}: {change_dict}")

                if changes.channel_changes:
                    print(f"\n  🎯 Channel Changes:")
                    for metric, diff in changes.channel_changes.items():
                        print(f"    • {metric}: {diff:+,}")
            else:
                print(f"  ℹ️  No changes detected (this is normal on subsequent runs)")

        # 3. Test video history retrieval
        if videos:
            test_video = videos[0]
            history = await db.get_video_history(test_video.id, days=30)

            print(f"\n📈 Video History Example ('{test_video.title[:40]}...'):")
            print(f"  Data points available: {len(history)}")
            if history:
                print(f"  First snapshot: {history[0].timestamp.strftime('%Y-%m-%d')} - {history[0].view_count:,} views")
                print(f"  Latest snapshot: {history[-1].timestamp.strftime('%Y-%m-%d')} - {history[-1].view_count:,} views")
                if len(history) > 1:
                    view_growth = history[-1].view_count - history[0].view_count
                    print(f"  Growth: {view_growth:+,} views")
            else:
                print(f"  ⚠️  No history yet - graphs will appear after collecting data over time")

    print(f"\n{'=' * 80}")
    print("✅ Feature Test Complete!")
    print("=" * 80)
    print("\nNotes:")
    print("  • Video stats history is collected automatically once per day")
    print("  • Change detection shows new videos and stat changes since last check")
    print("  • Graphs will display after 2+ days of data collection")
    print()

if __name__ == '__main__':
    asyncio.run(test_features())
