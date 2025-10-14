#!/usr/bin/env python3
"""Standalone authentication script for SuperTube"""

import sys
from youtube_api import YouTubeClient

def main():
    """Run authentication flow"""
    print("\n" + "="*80)
    print("SuperTube - YouTube Authentication")
    print("="*80 + "\n")

    try:
        client = YouTubeClient()
        client.authenticate()

        print("\n✅ Authentication successful!")
        print("You can now run SuperTube with: docker compose run --rm supertube")

    except Exception as e:
        print(f"\n❌ Authentication failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
