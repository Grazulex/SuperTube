#!/usr/bin/env python3
"""Standalone authentication script for SuperTube - Run OUTSIDE Docker"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from youtube_api import YouTubeClient

def main():
    """Run authentication flow"""
    print("\n" + "="*80)
    print("SuperTube - YouTube Authentication")
    print("="*80 + "\n")

    # Use local paths (not Docker paths)
    credentials_path = "config/credentials.json"
    token_path = "config/token.pickle"

    if not os.path.exists(credentials_path):
        print(f"❌ Error: {credentials_path} not found!")
        print("Please download OAuth2 credentials from Google Cloud Console.")
        sys.exit(1)

    try:
        client = YouTubeClient(
            credentials_path=credentials_path,
            token_path=token_path
        )
        client.authenticate()

        print("\n✅ Authentication successful!")
        print(f"Token saved to: {token_path}")
        print("\nYou can now run SuperTube with: ./run.sh")

    except Exception as e:
        print(f"\n❌ Authentication failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
