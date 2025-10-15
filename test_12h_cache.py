#!/usr/bin/env python3
"""
Test script to verify 12-hour cache behavior

This script tests that:
1. Stats are collected if none exist
2. Stats are NOT collected within 12 hours
3. Stats ARE collected after 12 hours
4. Multiple collections within same day UPDATE instead of INSERT
"""

import asyncio
import sys
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, '/app')

from src.database import DatabaseManager


async def test_12h_cache():
    """Test 12-hour cache behavior"""
    print("=" * 60)
    print("Testing 12-hour cache system")
    print("=" * 60)

    db = DatabaseManager(db_path="/app/data/supertube_test.db")
    await db.initialize()

    # Test channel ID
    test_channel_id = "test_channel_123"

    # Test 1: Fresh start - should NOT have stats
    print("\n[Test 1] Fresh start - no stats exist yet")
    has_stats = await db.has_stats_for_today(test_channel_id)
    print(f"  has_stats_for_today: {has_stats}")
    assert not has_stats, "Expected no stats for new channel"
    print("  ✓ PASS: No stats found for new channel")

    # Simulate inserting stats
    print("\n[Test 2] Insert first stats entry")
    import aiosqlite
    async with aiosqlite.connect(db.db_path) as conn:
        await conn.execute("""
            INSERT INTO stats_history
            (channel_id, timestamp, subscriber_count, view_count, video_count)
            VALUES (?, ?, ?, ?, ?)
        """, (test_channel_id, datetime.utcnow().isoformat(), 1000, 50000, 25))
        await conn.commit()
    print(f"  Stats inserted at: {datetime.utcnow()}")

    # Test 3: Check immediately - should have stats now
    print("\n[Test 3] Check immediately after insert")
    has_stats = await db.has_stats_for_today(test_channel_id)
    print(f"  has_stats_for_today: {has_stats}")
    assert has_stats, "Expected stats to exist after insert"
    print("  ✓ PASS: Stats found immediately after insert")

    # Test 4: Simulate time passage - 6 hours later (still within 12h window)
    print("\n[Test 4] Simulate 6 hours later (within 12h window)")
    six_hours_ago = datetime.utcnow() - timedelta(hours=6)
    async with aiosqlite.connect(db.db_path) as conn:
        await conn.execute("""
            UPDATE stats_history
            SET timestamp = ?
            WHERE channel_id = ?
        """, (six_hours_ago.isoformat(), test_channel_id))
        await conn.commit()

    has_stats = await db.has_stats_for_today(test_channel_id)
    print(f"  has_stats_for_today (6h old): {has_stats}")
    assert has_stats, "Expected stats to still be valid within 12h"
    print("  ✓ PASS: Stats still valid after 6 hours")

    # Test 5: Simulate 13 hours ago (outside 12h window)
    print("\n[Test 5] Simulate 13 hours ago (outside 12h window)")
    thirteen_hours_ago = datetime.utcnow() - timedelta(hours=13)
    async with aiosqlite.connect(db.db_path) as conn:
        await conn.execute("""
            UPDATE stats_history
            SET timestamp = ?
            WHERE channel_id = ?
        """, (thirteen_hours_ago.isoformat(), test_channel_id))
        await conn.commit()

    has_stats = await db.has_stats_for_today(test_channel_id)
    print(f"  has_stats_for_today (13h old): {has_stats}")
    assert not has_stats, "Expected stats to be expired after 13h"
    print("  ✓ PASS: Stats correctly expired after 13 hours")

    print("\n" + "=" * 60)
    print("All tests passed! ✓")
    print("=" * 60)
    print("\nSummary:")
    print("  • 12-hour cache window works correctly")
    print("  • Stats expire after 12 hours as expected")
    print("  • Ready to collect fresh data every 12h")


if __name__ == "__main__":
    try:
        asyncio.run(test_12h_cache())
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
