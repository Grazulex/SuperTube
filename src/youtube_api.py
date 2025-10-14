"""YouTube API client for fetching channel and video statistics"""

import os
import pickle
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from .models import Channel, Video


# Scopes required for YouTube Data API
SCOPES = ['https://www.googleapis.com/auth/youtube.readonly']


class YouTubeAPIError(Exception):
    """Custom exception for YouTube API errors"""
    pass


class YouTubeClient:
    """Client for interacting with YouTube Data API v3"""

    def __init__(self, credentials_path: str = "/app/config/credentials.json",
                 token_path: str = "/app/config/token.pickle"):
        """
        Initialize YouTube API client

        Args:
            credentials_path: Path to OAuth2 credentials JSON file
            token_path: Path to save/load access token
        """
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.credentials: Optional[Credentials] = None
        self.service = None

    def authenticate(self) -> None:
        """
        Authenticate with YouTube API using OAuth2

        This will:
        1. Try to load existing token from token_path
        2. Refresh token if expired
        3. Run OAuth flow if no valid token exists
        """
        # Load existing token if available
        if os.path.exists(self.token_path):
            with open(self.token_path, 'rb') as token_file:
                self.credentials = pickle.load(token_file)

        # Refresh or get new credentials
        if not self.credentials or not self.credentials.valid:
            if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                # Refresh expired token
                try:
                    self.credentials.refresh(Request())
                except Exception as e:
                    raise YouTubeAPIError(f"Failed to refresh token: {e}")
            else:
                # Run OAuth flow
                if not os.path.exists(self.credentials_path):
                    raise YouTubeAPIError(
                        f"Credentials file not found: {self.credentials_path}\n"
                        "Please download OAuth2 credentials from Google Cloud Console."
                    )

                try:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_path, SCOPES)

                    # Manual OAuth flow for Docker (no browser available)
                    print("\n" + "="*80)
                    print("🔐 AUTHENTICATION REQUIRED")
                    print("="*80)

                    # Get authorization URL
                    flow.redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'
                    auth_url, _ = flow.authorization_url(prompt='consent')

                    print("\n1. Please visit this URL in your browser:\n")
                    print(f"   {auth_url}\n")
                    print("2. After authorization, you will see a code")
                    print("3. Copy that code and paste it below\n")
                    print("-"*80)

                    # Get authorization code from user
                    code = input("Enter the authorization code: ").strip()

                    # Exchange code for credentials
                    flow.fetch_token(code=code)
                    self.credentials = flow.credentials

                    print("\n" + "="*80)
                    print("✅ Authentication successful!")
                    print("="*80 + "\n")
                except Exception as e:
                    raise YouTubeAPIError(f"OAuth flow failed: {e}")

            # Save credentials for future use
            with open(self.token_path, 'wb') as token_file:
                pickle.dump(self.credentials, token_file)

        # Build YouTube service
        try:
            self.service = build('youtube', 'v3', credentials=self.credentials)
        except Exception as e:
            raise YouTubeAPIError(f"Failed to build YouTube service: {e}")

    def get_channel_stats(self, channel_id: str) -> Channel:
        """
        Get statistics for a YouTube channel

        Args:
            channel_id: The YouTube channel ID

        Returns:
            Channel object with statistics

        Raises:
            YouTubeAPIError: If API request fails
        """
        if not self.service:
            raise YouTubeAPIError("Not authenticated. Call authenticate() first.")

        try:
            request = self.service.channels().list(
                part="snippet,statistics,contentDetails",
                id=channel_id
            )
            response = request.execute()

            if not response.get('items'):
                raise YouTubeAPIError(f"Channel not found: {channel_id}")

            item = response['items'][0]
            snippet = item['snippet']
            statistics = item['statistics']

            return Channel(
                id=channel_id,
                name=snippet['title'],
                custom_url=snippet.get('customUrl'),
                description=snippet['description'],
                subscriber_count=int(statistics.get('subscriberCount', 0)),
                view_count=int(statistics.get('viewCount', 0)),
                video_count=int(statistics.get('videoCount', 0)),
                published_at=datetime.fromisoformat(snippet['publishedAt'].replace('Z', '+00:00')),
                thumbnail_url=snippet['thumbnails']['high']['url']
            )

        except HttpError as e:
            raise YouTubeAPIError(f"YouTube API error: {e}")
        except (KeyError, ValueError) as e:
            raise YouTubeAPIError(f"Failed to parse API response: {e}")

    def get_channel_videos(self, channel_id: str, max_results: int = 50) -> List[Video]:
        """
        Get recent videos from a YouTube channel

        Args:
            channel_id: The YouTube channel ID
            max_results: Maximum number of videos to fetch (default 50)

        Returns:
            List of Video objects

        Raises:
            YouTubeAPIError: If API request fails
        """
        if not self.service:
            raise YouTubeAPIError("Not authenticated. Call authenticate() first.")

        try:
            # Step 1: Get the uploads playlist ID
            request = self.service.channels().list(
                part="contentDetails",
                id=channel_id
            )
            response = request.execute()

            if not response.get('items'):
                raise YouTubeAPIError(f"Channel not found: {channel_id}")

            uploads_playlist_id = response['items'][0]['contentDetails']['relatedPlaylists']['uploads']

            # Step 2: Get video IDs from the playlist
            video_ids = []
            next_page_token = None

            while len(video_ids) < max_results:
                request = self.service.playlistItems().list(
                    part="contentDetails",
                    playlistId=uploads_playlist_id,
                    maxResults=min(50, max_results - len(video_ids)),
                    pageToken=next_page_token
                )
                response = request.execute()

                for item in response.get('items', []):
                    video_ids.append(item['contentDetails']['videoId'])

                next_page_token = response.get('nextPageToken')
                if not next_page_token:
                    break

            # Step 3: Get video details (need to batch this - API allows 50 IDs per request)
            videos = []
            for i in range(0, len(video_ids), 50):
                batch_ids = video_ids[i:i+50]
                videos.extend(self._get_video_details(batch_ids, channel_id))

            return videos

        except HttpError as e:
            raise YouTubeAPIError(f"YouTube API error: {e}")
        except (KeyError, ValueError) as e:
            raise YouTubeAPIError(f"Failed to parse API response: {e}")

    def _get_video_details(self, video_ids: List[str], channel_id: str) -> List[Video]:
        """
        Get detailed statistics for a batch of videos

        Args:
            video_ids: List of video IDs
            channel_id: Channel ID (for the Video object)

        Returns:
            List of Video objects
        """
        request = self.service.videos().list(
            part="snippet,statistics,contentDetails",
            id=','.join(video_ids)
        )
        response = request.execute()

        videos = []
        for item in response.get('items', []):
            snippet = item['snippet']
            statistics = item.get('statistics', {})
            content_details = item['contentDetails']

            videos.append(Video(
                id=item['id'],
                channel_id=channel_id,
                title=snippet['title'],
                description=snippet['description'],
                published_at=datetime.fromisoformat(snippet['publishedAt'].replace('Z', '+00:00')),
                view_count=int(statistics.get('viewCount', 0)),
                like_count=int(statistics.get('likeCount', 0)),
                comment_count=int(statistics.get('commentCount', 0)),
                duration=content_details['duration'],
                thumbnail_url=snippet['thumbnails']['high']['url']
            ))

        return videos

    def get_quota_usage(self) -> Optional[Dict[str, Any]]:
        """
        Get current API quota usage (if available)

        Note: YouTube API doesn't provide direct quota info,
        this is a placeholder for future implementation
        """
        # YouTube Data API v3 doesn't expose quota usage directly
        # Quota is managed in Google Cloud Console
        # Each request costs different units (e.g., list=1, search=100)
        return None
