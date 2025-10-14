#!/usr/bin/env python3
"""Standalone authentication - NO Textual, pure terminal"""

import os
import sys
import pickle
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/youtube.readonly']

def authenticate():
    credentials_path = "/app/config/credentials.json"
    token_path = "/app/config/token.pickle"

    print("\n" + "="*80)
    print("🔐 SuperTube - YouTube Authentication")
    print("="*80 + "\n")

    # Check credentials exist
    if not os.path.exists(credentials_path):
        print(f"❌ Error: {credentials_path} not found!")
        print("Please place your OAuth2 credentials.json in the config/ folder")
        sys.exit(1)

    credentials = None

    # Load existing token
    if os.path.exists(token_path):
        print("Found existing token, checking validity...")
        with open(token_path, 'rb') as token_file:
            credentials = pickle.load(token_file)

    # Check if valid
    if credentials and credentials.valid:
        print("✅ Already authenticated!")
        print(f"Token is valid until: {credentials.expiry}")
        return

    # Refresh if expired
    if credentials and credentials.expired and credentials.refresh_token:
        print("Token expired, refreshing...")
        try:
            credentials.refresh(Request())
            print("✅ Token refreshed successfully!")
        except Exception as e:
            print(f"❌ Failed to refresh: {e}")
            credentials = None

    # Need new auth
    if not credentials:
        print("\n" + "="*80)
        print("🔐 AUTHENTICATION REQUIRED")
        print("="*80 + "\n")

        try:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            flow.redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'
            auth_url, _ = flow.authorization_url(prompt='consent')

            print("1. Please visit this URL in your browser:\n")
            print(f"   {auth_url}\n")
            print("2. After authorization, Google will show you a code")
            print("3. Copy that code and paste it below\n")
            print("-"*80)

            code = input("\nEnter the authorization code: ").strip()

            print("\nExchanging code for token...")
            flow.fetch_token(code=code)
            credentials = flow.credentials

            print("✅ Authentication successful!")

        except KeyboardInterrupt:
            print("\n\n❌ Authentication cancelled by user")
            sys.exit(1)
        except Exception as e:
            print(f"\n❌ Authentication failed: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

    # Save token
    with open(token_path, 'wb') as token_file:
        pickle.dump(credentials, token_file)
    print(f"\n💾 Token saved to: {token_path}")

    # Test the API
    print("\n🔍 Testing API connection...")
    try:
        service = build('youtube', 'v3', credentials=credentials)
        request = service.channels().list(part='snippet', mine=True)
        response = request.execute()
        print(f"✅ API connection successful! Found {len(response.get('items', []))} channels")
    except Exception as e:
        print(f"⚠️  Warning: API test failed: {e}")

    print("\n" + "="*80)
    print("✅ All done! You can now launch SuperTube:")
    print("   ./run.sh")
    print("="*80 + "\n")

if __name__ == "__main__":
    authenticate()
