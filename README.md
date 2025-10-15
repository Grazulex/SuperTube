# SuperTube 📺

A beautiful terminal user interface (TUI) for monitoring YouTube channel statistics, inspired by lazygit and lazydocker.

Track your YouTube channels' performance with real-time statistics, video analytics, and historical trends - all from your terminal!

## ✨ Features

- 📊 **Multi-channel monitoring**: Track up to 3 YouTube channels simultaneously
- 📈 **Real-time statistics**: Subscribers, views, video count, engagement metrics
- 🎥 **Video analytics**: Monitor individual video performance (views, likes, comments)
- 💾 **Smart caching**: SQLite cache to minimize API quota usage
- 📦 **Data archival**: Automatic archiving with compression for long-term retention (1 year+)
- ⚡ **Fast navigation**: Vim-style keyboard shortcuts
- 🐳 **Docker-ready**: No local Python installation required

## 📋 Prerequisites

1. **Docker & Docker Compose** installed on your system
2. **Google Cloud account** (free tier is sufficient)
3. **YouTube Data API v3** access
4. **YouTube channel(s)** you want to monitor

## 🚀 Quick Start

### 1. Google Cloud Setup

#### Create a Project and Enable YouTube API

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select an existing one)
3. Navigate to **APIs & Services** → **Library**
4. Search for **YouTube Data API v3**
5. Click **Enable**

#### Configure OAuth Consent Screen

1. Go to **APIs & Services** → **OAuth consent screen**
2. Select **External** user type (unless you have a workspace)
3. Fill in required fields:
   - App name: `SuperTube`
   - User support email: Your email
   - Developer contact: Your email
4. Click **Save and Continue**
5. Skip scopes (click **Save and Continue**)
6. Add your email as a test user
7. Click **Save and Continue**

#### Create OAuth 2.0 Credentials

1. Go to **APIs & Services** → **Credentials**
2. Click **Create Credentials** → **OAuth client ID**
3. Select **Desktop app** as application type
4. Name it `SuperTube Client`
5. Click **Create**
6. **Download the JSON file** (this is your `credentials.json`)

### 2. Project Setup

```bash
# Clone or navigate to the SuperTube directory
cd SuperTube

# Copy the example config
cp config/config.yaml.example config/config.yaml

# Place your downloaded credentials.json in the config folder
cp ~/Downloads/client_secret_*.json config/credentials.json
```

### 3. Configure Your Channels

Edit `config/config.yaml` and add your YouTube channel IDs:

```yaml
channels:
  - name: "My Tech Channel"
    channel_id: "UCxxxxxxxxxxxxxxxxxxxxxxxxx"
    description: "Main tech channel"

  - name: "My Gaming Channel"
    channel_id: "UCyyyyyyyyyyyyyyyyyyyyyyyyy"
    description: "Gaming content"

  - name: "My Vlog Channel"
    channel_id: "UCzzzzzzzzzzzzzzzzzzzzzzzzz"
    description: "Personal vlogs"
```

**How to find your Channel ID:**

**Method 1: YouTube Studio**
1. Go to [YouTube Studio](https://studio.youtube.com/)
2. Click **Settings** → **Channel** → **Advanced settings**
3. Copy the **Channel ID**

**Method 2: Channel URL**
1. Go to your channel page
2. Look at the URL:
   - If it's `youtube.com/channel/UCxxx...`, copy the part after `/channel/`
   - If it's `youtube.com/@username`, you'll need to use Method 1

### 4. Run SuperTube

```bash
# Build and run using the convenience script
./run.sh

# Or manually with docker-compose
docker-compose build
docker-compose run --rm supertube

# To also enable automatic data archival (recommended for production):
docker-compose up -d archiver
```

**📦 Data Archival Service (Optional)**

The archiver service runs daily at 3 AM to automatically:
- Archive statistics older than 90 days with compression (~75% space savings)
- Maintain 1-year data retention
- Keep active tables optimized

See [ARCHIVER.md](ARCHIVER.md) for detailed documentation.

### 5. First Run - OAuth Authentication

On first launch, you'll need to authenticate:

1. The app will display a URL in your terminal
2. Copy and paste it into your browser
3. Log in with your Google account
4. Grant permissions to SuperTube
5. The browser will show a success message
6. Return to the terminal - the app should now be running!

The authentication token is saved in `config/token.pickle`, so you won't need to do this again unless you revoke access.

## ⌨️ Keyboard Shortcuts

### Global

| Key | Action |
|-----|--------|
| `q` | Quit application |
| `r` | Refresh data from YouTube |
| `?` | Show help screen |

### Navigation

| Key | Action |
|-----|--------|
| `1` | View Channel 1 details |
| `2` | View Channel 2 details |
| `3` | View Channel 3 details |
| `ESC` | Return to dashboard |

## 📁 Project Structure

```
SuperTube/
├── src/                    # Python source code
│   ├── __init__.py
│   ├── app.py              # Main Textual application
│   ├── config.py           # Configuration loader
│   ├── youtube_api.py      # YouTube API client
│   ├── database.py         # SQLite cache manager
│   └── models.py           # Data models
├── config/                 # Configuration files
│   ├── config.yaml.example # Example configuration
│   ├── config.yaml         # Your configuration (gitignored)
│   └── credentials.json    # OAuth credentials (gitignored)
├── data/                   # SQLite database (gitignored)
│   └── supertube.db
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## 🔧 Configuration

### Application Settings

In `config/config.yaml`, you can adjust:

```yaml
settings:
  # Cache duration in seconds (default: 1 hour)
  cache_ttl: 3600

  # Number of recent videos to fetch per channel
  max_videos: 50

  # Auto-refresh interval in seconds (0 = disabled)
  auto_refresh: 0
```

### Cache Behavior

- Channel statistics are cached for `cache_ttl` seconds
- Videos are fetched once and cached indefinitely
- Historical statistics are saved every time data is refreshed
- Press `r` to force refresh from YouTube API

## 🐛 Troubleshooting

### "Configuration file not found"

Make sure you've copied `config.yaml.example` to `config.yaml`:

```bash
cp config/config.yaml.example config/config.yaml
```

### "Credentials file not found"

Ensure your OAuth credentials are saved as `config/credentials.json`:

```bash
# Check if file exists
ls -l config/credentials.json
```

### "OAuth flow failed"

1. Make sure you've added yourself as a test user in Google Cloud Console
2. Check that the OAuth consent screen is configured
3. Verify the credentials.json file is valid JSON

### "YouTube API quota exceeded"

The YouTube Data API has daily quotas:
- Default quota: 10,000 units per day
- Channel stats request: ~3 units
- Videos list request: ~100 units per channel

SuperTube uses caching to minimize API calls. If you hit quota limits:
1. Increase `cache_ttl` in config.yaml
2. Avoid refreshing too frequently
3. Wait 24 hours for quota reset

### "Channel not found"

1. Verify the channel ID is correct
2. Ensure the channel is public
3. Check you're authenticated with an account that can access the channel

### Docker build issues

```bash
# Clean rebuild
docker-compose build --no-cache
```

## 📊 Statistics Tracked

### Channel Metrics

- **Subscribers**: Total subscriber count
- **Views**: Lifetime view count
- **Videos**: Total number of published videos
- **Growth trends**: Historical data tracking (future feature)

### Video Metrics

- **Views**: Individual video view count
- **Likes**: Like count
- **Comments**: Comment count
- **Published date**: When the video was published
- **Engagement rate**: (Likes + Comments) / Views * 100
- **Like ratio**: Likes / Views * 100

## 🔐 Privacy & Security

- OAuth tokens are stored locally in `config/token.pickle`
- All API credentials stay on your machine (gitignored)
- SuperTube only requests `youtube.readonly` scope (read-only access)
- No data is sent to external servers (except Google APIs)

## 🛠️ Development

### Running without Docker

If you want to run locally:

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the app
python -m src.app
```

### Database Schema

SQLite database at `data/supertube.db` with tables:

- `channels`: Channel information and current stats
- `videos`: Video information and stats
- `stats_history`: Historical snapshots for trend analysis (hot data, 0-90 days)
- `video_stats_history`: Video statistics history (hot data, 0-90 days)
- `stats_history_archive`: Compressed channel stats archives (cold data, 90+ days)
- `video_stats_history_archive`: Compressed video stats archives (cold data, 90+ days)

**Data Retention Strategy:**
- **Hot data** (0-90 days): Stored in regular tables for fast access
- **Cold data** (90+ days): Automatically archived with zlib compression
- **Total retention**: 365 days (1 year)
- **Space savings**: ~75-80% for archived data

See [ARCHIVER.md](ARCHIVER.md) for archival system details.

## 📝 Roadmap

Future enhancements (see backlog for tasks):

- [ ] Enhanced Dashboard with DataTable widget
- [ ] Channel View with ASCII sparkline graphs
- [ ] Video List with sorting and filtering
- [ ] Advanced keyboard navigation (j/k vim-style)
- [ ] Export reports to CSV/JSON
- [ ] Web UI option (complementary to TUI)

## 🤝 Contributing

This is a personal project, but suggestions and improvements are welcome!

## 📄 License

This project is for personal use. YouTube Data API usage must comply with [YouTube's Terms of Service](https://developers.google.com/youtube/terms/api-services-terms-of-service).

## 🙏 Acknowledgments

- Built with [Textual](https://github.com/Textualize/textual) by Textualize
- Inspired by [lazygit](https://github.com/jesseduffield/lazygit) and [lazydocker](https://github.com/jesseduffield/lazydocker)
- Uses [YouTube Data API v3](https://developers.google.com/youtube/v3)

## 📞 Support

If you encounter issues:

1. Check the Troubleshooting section above
2. Verify your Google Cloud setup
3. Check Docker logs: `docker-compose logs`

---

**Happy monitoring! 📈🎉**
