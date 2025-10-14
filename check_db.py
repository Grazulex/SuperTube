#!/usr/bin/env python3
"""Check database contents"""
import sqlite3
import sys

conn = sqlite3.connect('/app/data/supertube.db')
c = conn.cursor()

# Check stats_history table
c.execute('SELECT COUNT(*) FROM stats_history')
count = c.fetchone()[0]
print(f'Total stats records: {count}')

if count > 0:
    c.execute('SELECT channel_id, timestamp, subscriber_count, view_count FROM stats_history ORDER BY timestamp DESC LIMIT 5')
    print('\nLast 5 stats entries:')
    for row in c.fetchall():
        print(f'  Channel: {row[0][:20]}... | Time: {row[1]} | Subs: {row[2]:,} | Views: {row[3]:,}')

# Check channels table
c.execute('SELECT COUNT(*) FROM channels')
channel_count = c.fetchone()[0]
print(f'\nTotal channels: {channel_count}')

if channel_count > 0:
    c.execute('SELECT id, name, subscriber_count FROM channels')
    print('\nChannels:')
    for row in c.fetchall():
        print(f'  {row[1]}: {row[2]:,} subscribers')

conn.close()
