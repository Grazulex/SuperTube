#!/usr/bin/env python3
"""Test script to verify daily stats detection logic"""
import asyncio
import sys
from datetime import datetime

sys.path.insert(0, '/app')
from src.database import DatabaseManager

async def test_daily_stats():
    db = DatabaseManager('/app/data/supertube.db')
    await db.initialize()

    # Get all channels from DB
    import aiosqlite
    async with aiosqlite.connect(db.db_path) as conn:
        conn.row_factory = aiosqlite.Row
        async with conn.execute('SELECT id, name FROM channels') as cursor:
            channels = await cursor.fetchall()

    print(f"Testing daily stats detection - Today: {datetime.utcnow().strftime('%Y-%m-%d')}")
    print("=" * 80)

    for channel in channels:
        channel_id = channel['id']
        channel_name = channel['name']

        has_today = await db.has_stats_for_today(channel_id)

        # Get the latest stat timestamp
        async with aiosqlite.connect(db.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.execute(
                'SELECT timestamp FROM stats_history WHERE channel_id = ? ORDER BY timestamp DESC LIMIT 1',
                (channel_id,)
            ) as cursor:
                row = await cursor.fetchone()
                last_stat = row['timestamp'] if row else 'None'

        status = "✓ YES" if has_today else "✗ NO"
        print(f"\nChannel: {channel_name}")
        print(f"  Has stats for today: {status}")
        print(f"  Last stat timestamp: {last_stat}")

if __name__ == '__main__':
    asyncio.run(test_daily_stats())
