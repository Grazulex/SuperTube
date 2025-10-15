#!/usr/bin/env python3
"""
Archiver Cron Service - Automatic data archival for SuperTube

This service runs periodically to archive old statistics data (>90 days)
to compressed archive tables, maintaining long-term data retention while
keeping active tables optimized.

Usage:
    python archiver_cron.py [--days DAYS] [--dry-run]

Options:
    --days DAYS    Archive data older than DAYS (default: 90)
    --dry-run      Simulate archival without making changes
"""

import asyncio
import argparse
import sys
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from database import DatabaseManager


async def run_archival(days: int = 90, dry_run: bool = False):
    """
    Run the archival process

    Args:
        days: Archive data older than this many days
        dry_run: If True, only simulate without making changes
    """
    log_file = Path("/app/data/archive.log")
    log_file.parent.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().isoformat()

    def log(message: str):
        """Log to both console and file"""
        log_line = f"[{timestamp}] {message}"
        print(log_line)
        with open(log_file, "a") as f:
            f.write(log_line + "\n")

    try:
        log(f"{'[DRY RUN] ' if dry_run else ''}Starting archival process (>= {days} days)...")

        # Initialize database
        db = DatabaseManager()
        await db.initialize()

        if dry_run:
            log("DRY RUN MODE - No changes will be made")
            # In dry run, we could query what would be archived
            log("Dry run completed successfully")
            return

        # Run archival
        result = await db.archive_old_data(days=days)

        channel_count = result.get('channel_stats_archived', 0)
        video_count = result.get('video_stats_archived', 0)
        total_count = channel_count + video_count

        log(f"Archival completed successfully:")
        log(f"  - Channel stats archived: {channel_count}")
        log(f"  - Video stats archived: {video_count}")
        log(f"  - Total records archived: {total_count}")

        if total_count == 0:
            log("  - No data to archive (all data is within retention period)")

    except Exception as e:
        log(f"ERROR during archival: {type(e).__name__}: {e}")
        import traceback
        log(f"Traceback:\n{traceback.format_exc()}")
        sys.exit(1)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="SuperTube automatic data archival service"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=90,
        help="Archive data older than DAYS (default: 90)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate archival without making changes"
    )

    args = parser.parse_args()

    # Run async archival
    asyncio.run(run_archival(days=args.days, dry_run=args.dry_run))


if __name__ == "__main__":
    main()
