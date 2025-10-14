"""SuperTube - YouTube Channel Statistics TUI Application"""

import asyncio
import sys
from typing import Optional, Dict, List
from datetime import datetime

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, Static, Label
from textual.binding import Binding
from textual import work

from .config import Config
from .youtube_api import YouTubeClient, YouTubeAPIError
from .database import DatabaseManager
from .models import Channel, Video, ChangeDetection
from .widgets import DashboardWidget, ChannelDetailWidget, VideoListWidget

# Version number for deployment tracking
VERSION = "2.4.0"


class StatusBar(Static):
    """Status bar showing last update time and quota info"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.last_update: Optional[datetime] = None
        self.status_message: str = "Ready"

    def on_mount(self) -> None:
        """Update display when mounted"""
        self.update_display()

    def set_status(self, message: str) -> None:
        """Set status message"""
        self.status_message = message
        self.update_display()

    def set_last_update(self, timestamp: datetime) -> None:
        """Set last update timestamp"""
        self.last_update = timestamp
        self.update_display()

    def update_display(self) -> None:
        """Update the status bar display"""
        if self.last_update:
            time_str = self.last_update.strftime("%H:%M:%S")
            self.update(f"[dim]Last update: {time_str} | {self.status_message}[/dim]")
        else:
            self.update(f"[dim]{self.status_message}[/dim]")


class SuperTubeApp(App):
    """Main SuperTube application"""

    CSS = """
    Screen {
        layout: vertical;
    }

    #main_container {
        height: 1fr;
        padding: 1 2;
    }

    #status_bar {
        height: 1;
        background: $panel;
        padding: 0 2;
        color: $text;
    }

    Header {
        background: $accent;
    }

    .box {
        border: solid $primary;
        padding: 1 2;
        margin: 1;
    }

    .error {
        color: $error;
        padding: 1;
    }

    .success {
        color: $success;
        padding: 1;
    }

    .dashboard-title {
        text-align: center;
        padding: 1 0;
        background: $panel;
    }

    .stats-box {
        padding: 1 2;
        background: $panel;
        margin: 1 0;
    }

    .channel-title {
        text-align: center;
        padding: 1 0;
        background: $primary;
    }

    .section-title {
        padding: 1 2;
        background: $primary;
        color: $text;
        text-style: bold;
    }

    .graph-box {
        border: solid $primary;
        padding: 1 2;
        margin: 1 0;
        height: 10;
    }

    #channels_table {
        height: 1fr;
        margin: 1 0;
    }

    #videos_table {
        height: 1fr;
        margin: 1 0;
    }

    DataTable {
        background: $surface;
    }

    DataTable > .datatable--header {
        background: $primary;
        color: $text;
        text-style: bold;
    }

    DataTable > .datatable--cursor {
        background: $accent;
    }

    #video_detail_container {
        layout: horizontal;
        height: 1fr;
    }

    #video_info {
        width: 50%;
        height: 1fr;
    }

    #video_graph {
        width: 50%;
        height: 1fr;
    }
    """

    TITLE = "SuperTube - YouTube Statistics"
    SUB_TITLE = f"Monitor your YouTube channels - v{VERSION}"

    BINDINGS = [
        Binding("q", "quit", "Quit", priority=True),
        Binding("r", "refresh", "Refresh", priority=True),
        Binding("?", "help", "Help"),
        Binding("d", "dashboard", "Dashboard"),
        Binding("enter", "select_channel", show=False),  # Hidden binding for non-DataTable views
        Binding("escape", "back", "Back"),
        # Vim-style navigation
        Binding("j", "cursor_down", "Down", show=False),
        Binding("k", "cursor_up", "Up", show=False),
        # Channel shortcuts
        Binding("1", "goto_channel_1", "Channel 1", show=False),
        Binding("2", "goto_channel_2", "Channel 2", show=False),
        Binding("3", "goto_channel_3", "Channel 3", show=False),
        # Sort shortcut for video list
        Binding("s", "cycle_sort", "Sort", show=False),
        # Video URL copy
        Binding("y", "copy_video_url", "Copy URL", show=False),
        # Note: / is handled in on_key() method
    ]

    def __init__(self):
        super().__init__()
        self.config: Optional[Config] = None
        self.youtube_client: Optional[YouTubeClient] = None
        self.db: Optional[DatabaseManager] = None
        self.channels_data: Dict[str, Channel] = {}
        self.videos_data: Dict[str, List[Video]] = {}
        self.changes_data: Dict[str, ChangeDetection] = {}  # Track changes per channel
        self.status_bar: Optional[StatusBar] = None
        self.current_view: str = "dashboard"  # Track current view
        self.selected_channel_id: Optional[str] = None

    def compose(self) -> ComposeResult:
        """Create child widgets"""
        yield Header()
        yield Container(id="main_container")
        status = StatusBar()
        status.id = "status_bar"
        yield status
        yield Footer()

    async def on_mount(self) -> None:
        """Initialize the application"""
        self.status_bar = self.query_one("#status_bar", StatusBar)
        self.status_bar.set_status("Initializing...")

        # Load configuration
        try:
            self.config = Config.load()
            self.status_bar.set_status(f"Loaded {len(self.config.channels)} channels")
        except (FileNotFoundError, ValueError) as e:
            self.show_error(str(e))
            return

        # Initialize database
        try:
            self.db = DatabaseManager()
            await self.db.initialize()
            self.status_bar.set_status("Database initialized")
        except Exception as e:
            self.show_error(f"Database initialization failed: {e}")
            return

        # Initialize YouTube client
        try:
            self.youtube_client = YouTubeClient()

            # Check if token exists
            import os
            if not os.path.exists(self.youtube_client.token_path):
                self.show_error(
                    "Not authenticated!\n\n"
                    "Please run authentication first:\n"
                    "  docker compose run --rm supertube python -m src.authenticate\n\n"
                    "Then relaunch SuperTube."
                )
                return

            self.status_bar.set_status("Loading credentials...")
            await asyncio.to_thread(self.youtube_client.authenticate)
            self.status_bar.set_status("Authenticated successfully")
        except YouTubeAPIError as e:
            self.show_error(f"YouTube authentication failed: {e}\n\nTry running: docker compose run --rm supertube python -m src.authenticate")
            return

        # Load initial data
        self.load_data()

    @work(exclusive=True)
    async def load_data(self) -> None:
        """Load channel and video data"""
        if not self.config or not self.youtube_client or not self.db:
            return

        self.status_bar.set_status("Loading channel data...")

        for i, channel_config in enumerate(self.config.channels, 1):
            try:
                # Check if we already have stats for today
                has_today_stats = await self.db.has_stats_for_today(channel_config.channel_id)

                if has_today_stats:
                    # Load from cache - we already collected stats today
                    channel = await self.db.get_channel(channel_config.channel_id)
                    videos = await self.db.get_channel_videos(
                        channel_config.channel_id,
                        self.config.settings.max_videos
                    )
                    self.status_bar.set_status(f"Loaded {channel_config.name} (today's stats already collected)")
                else:
                    # Fetch from API - no stats for today yet
                    self.status_bar.set_status(f"Collecting today's stats for {channel_config.name}...")

                    channel = await asyncio.to_thread(
                        self.youtube_client.get_channel_stats,
                        channel_config.channel_id
                    )

                    videos = await asyncio.to_thread(
                        self.youtube_client.get_channel_videos,
                        channel_config.channel_id,
                        self.config.settings.max_videos
                    )

                    # Detect changes before saving
                    changes = await self.db.detect_changes(channel_config.channel_id, channel, videos)
                    self.changes_data[channel.id] = changes

                    # Save to cache and record today's stats
                    await self.db.save_channel(channel)
                    await self.db.save_videos(videos)
                    await self.db.save_channel_stats(channel)
                    await self.db.save_video_stats(videos)

                # Store in memory
                self.channels_data[channel.id] = channel
                self.videos_data[channel.id] = videos

            except YouTubeAPIError as e:
                self.show_error(f"Failed to load {channel_config.name}: {e}")
                continue

        self.status_bar.set_status("Data loaded successfully")
        self.status_bar.set_last_update(datetime.now())

        # Show dashboard
        self.show_dashboard()

    def show_dashboard(self) -> None:
        """Display the main dashboard with DataTable"""
        self.current_view = "dashboard"
        container = self.query_one("#main_container", Container)
        container.remove_children()

        if not self.channels_data:
            container.mount(Label("No data loaded. Press 'r' to refresh.", classes="error"))
            return

        # Show change notifications if any
        if self.changes_data:
            changes_summary = self._build_changes_summary()
            if changes_summary:
                container.mount(Static(changes_summary, classes="success", id="changes_notification"))

        # Create and mount dashboard widget
        dashboard = DashboardWidget()
        container.mount(dashboard)

        # Load historical data and update dashboard
        channels_list = list(self.channels_data.values())
        self.load_dashboard_history(dashboard, channels_list)

    def _build_changes_summary(self) -> str:
        """Build a summary of all changes detected"""
        if not self.changes_data:
            return ""

        all_changes = []
        for channel_id, changes in self.changes_data.items():
            if changes.has_changes():
                channel = self.channels_data.get(channel_id)
                channel_name = channel.name if channel else channel_id
                summary = changes.get_summary()
                all_changes.append(f"  • {channel_name}: {summary}")

        if not all_changes:
            return ""

        header = "[bold green]🎉 Changes Detected Since Last Check![/bold green]\n"
        return header + "\n".join(all_changes)

    def show_error(self, message: str) -> None:
        """Display an error message"""
        container = self.query_one("#main_container", Container)
        container.remove_children()
        container.mount(Label(f"[bold red]Error:[/bold red] {message}", classes="error"))

    def action_refresh(self) -> None:
        """Refresh data from YouTube"""
        # Clear cache validity by setting channels_data to empty
        # This will force a fresh fetch
        self.load_data()

    def action_help(self) -> None:
        """Show help screen"""
        self.current_view = "help"
        container = self.query_one("#main_container", Container)
        container.remove_children()

        help_text = """[bold cyan]📖 SuperTube - Keyboard Shortcuts[/bold cyan]

[bold]Main Navigation:[/bold]
  q          - Quit application
  r          - Refresh data from YouTube (collects today's stats if not done)
  d          - Return to Dashboard
  ESC        - Go back to previous screen
  ?          - Show this help

[bold]Quick Channel Access:[/bold]
  1          - Jump to first channel details
  2          - Jump to second channel details
  3          - Jump to third channel details

[bold]Dashboard:[/bold]
  ↑/↓ or j/k - Navigate between channels (vim-style)
  s          - Cycle sort order (subscribers → views → videos → name)
  ENTER      - View selected channel details

[bold]Channel Details:[/bold]
  ENTER      - View all videos
  ESC        - Back to Dashboard

[bold]Video List:[/bold]
  ↑/↓ or j/k - Navigate through videos (vim-style)
  /          - Focus search input (filter videos by title)
  s          - Cycle sort order (views → likes → comments → date → engagement)
  y          - Show video URL (displayed in status bar for copying)
  ENTER      - View video details
  ESC        - Back to Dashboard

[bold]Video Details:[/bold]
  y          - Show video URL (displayed in status bar for copying)
  ESC        - Back to Video List

[bold]Status Bar:[/bold]
  Shows last update time, current status, and change notifications

[bold cyan]💡 Pro Tips:[/bold cyan]
  • Stats are collected automatically once per day
  • Green notifications show new videos and stat changes
  • Graphs appear after collecting 2+ days of data

[dim]Press ESC to return to dashboard...[/dim]
        """
        container.mount(Static(help_text, classes="box"))

    def action_dashboard(self) -> None:
        """Return to dashboard"""
        self.show_dashboard()

    def action_select_channel(self) -> None:
        """View details of selected channel or video"""
        container = self.query_one("#main_container", Container)

        if self.current_view == "dashboard":
            # Select channel from dashboard
            try:
                dashboard = container.query_one(DashboardWidget)
                channel_id = dashboard.get_selected_channel_id()
                if channel_id:
                    self.show_channel_details(channel_id)
            except:
                pass

        elif self.current_view == "channel_detail":
            # Enter in channel detail goes to video list
            if self.selected_channel_id:
                self.show_video_list(self.selected_channel_id)

        elif self.current_view == "video_list":
            # Show video details
            try:
                video_list = container.query_one(VideoListWidget)
                video = video_list.get_selected_video()
                if video:
                    self.show_video_details(video)
            except:
                pass

    def action_view_videos(self) -> None:
        """View all videos of selected channel"""
        if self.current_view == "dashboard":
            container = self.query_one("#main_container", Container)
            try:
                dashboard = container.query_one(DashboardWidget)
                channel_id = dashboard.get_selected_channel_id()
                if channel_id:
                    self.show_video_list(channel_id)
            except:
                pass
        elif self.current_view == "channel_detail" and self.selected_channel_id:
            self.show_video_list(self.selected_channel_id)

    def action_back(self) -> None:
        """Go back to previous view"""
        if self.current_view == "video_detail" and self.selected_channel_id:
            # Go back to video list
            self.show_video_list(self.selected_channel_id)
        elif self.current_view in ["channel_detail", "video_list"]:
            self.show_dashboard()
        elif self.current_view == "help":
            self.show_dashboard()

    def action_cursor_down(self) -> None:
        """Move cursor down (vim j key)"""
        try:
            # Find any DataTable in focus and move cursor down
            from textual.widgets import DataTable
            tables = self.query(DataTable)
            for table in tables:
                if table.has_focus:
                    table.action_cursor_down()
                    break
        except:
            pass

    def action_cursor_up(self) -> None:
        """Move cursor up (vim k key)"""
        try:
            # Find any DataTable in focus and move cursor up
            from textual.widgets import DataTable
            tables = self.query(DataTable)
            for table in tables:
                if table.has_focus:
                    table.action_cursor_up()
                    break
        except:
            pass

    def action_goto_channel_1(self) -> None:
        """Go to first channel"""
        self._goto_channel_by_index(0)

    def action_goto_channel_2(self) -> None:
        """Go to second channel"""
        self._goto_channel_by_index(1)

    def action_goto_channel_3(self) -> None:
        """Go to third channel"""
        self._goto_channel_by_index(2)

    def _goto_channel_by_index(self, index: int) -> None:
        """Navigate to channel by index"""
        if not self.channels_data:
            return

        channels_list = list(self.channels_data.values())
        if 0 <= index < len(channels_list):
            channel = channels_list[index]
            self.show_channel_details(channel.id)

    def action_cycle_sort(self) -> None:
        """Cycle through sort options in dashboard or video list"""
        try:
            container = self.query_one("#main_container", Container)

            if self.current_view == "dashboard":
                # Handle dashboard sorting
                dashboard = container.query_one(DashboardWidget)

                # Cycle through sort keys
                sort_keys = ["subscribers", "views", "videos", "name"]
                current_key = dashboard.sort_key
                current_index = sort_keys.index(current_key) if current_key in sort_keys else 0
                next_key = sort_keys[(current_index + 1) % len(sort_keys)]

                # Update sort
                dashboard.change_sort(next_key)

                # Show notification
                sort_names = {
                    "subscribers": "Subscribers",
                    "views": "Total Views",
                    "videos": "Video Count",
                    "name": "Name (A-Z)"
                }
                self.status_bar.set_status(f"Dashboard sorted by: {sort_names[next_key]}")

            elif self.current_view == "video_list":
                # Handle video list sorting
                video_list = container.query_one(VideoListWidget)

                # Cycle through sort keys
                sort_keys = ["views", "likes", "comments", "date", "engagement"]
                current_key = video_list.sort_key
                current_index = sort_keys.index(current_key) if current_key in sort_keys else 0
                next_key = sort_keys[(current_index + 1) % len(sort_keys)]

                # Update sort
                video_list.change_sort(next_key)

                # Show notification
                sort_names = {
                    "views": "Views",
                    "likes": "Likes",
                    "comments": "Comments",
                    "date": "Date",
                    "engagement": "Engagement"
                }
                self.status_bar.set_status(f"Sorted by: {sort_names[next_key]}")
        except:
            pass

    def action_focus_search(self) -> None:
        """Focus the search input in video list"""
        if self.current_view != "video_list":
            return

        try:
            container = self.query_one("#main_container", Container)
            video_list = container.query_one(VideoListWidget)
            video_list.focus_search()
        except:
            pass

    def action_copy_video_url(self) -> None:
        """Copy video URL to clipboard (display in status bar)"""
        if self.current_view not in ["video_list", "video_detail"]:
            return

        try:
            video = None

            if self.current_view == "video_list":
                container = self.query_one("#main_container", Container)
                video_list = container.query_one(VideoListWidget)
                video = video_list.get_selected_video()
            elif self.current_view == "video_detail":
                video = getattr(self, 'current_video', None)

            if video:
                url = f"https://youtube.com/watch?v={video.id}"
                self.status_bar.set_status(f"📋 Video URL: {url}")
            else:
                self.status_bar.set_status("No video selected")
        except Exception as e:
            self.status_bar.set_status(f"Error: {e}")

    def on_key(self, event) -> None:
        """Handle key events for special keys like / and y"""
        from textual.widgets import Input

        # Handle / for search in video list
        if event.key == "slash" or event.key == "/":
            if self.current_view == "video_list":
                self.action_focus_search()
                event.prevent_default()
                event.stop()
                return

        # Handle y for URL copy (but not when typing in search input)
        if event.key == "y":
            # Check if we're typing in an input field
            focused = self.focused
            if isinstance(focused, Input):
                # Let the input handle the key
                return

            if self.current_view in ["video_list", "video_detail"]:
                self.action_copy_video_url()
                event.prevent_default()
                event.stop()

    def on_data_table_row_selected(self, event) -> None:
        """Handle Enter key press in DataTables"""
        if self.current_view == "dashboard":
            # Get selected channel from dashboard
            try:
                dashboard = self.query_one(DashboardWidget)
                channel_id = dashboard.get_selected_channel_id()
                if channel_id:
                    self.show_channel_details(channel_id)
            except:
                pass
        elif self.current_view == "channel_detail":
            # Enter in channel detail shows video list
            if self.selected_channel_id:
                self.show_video_list(self.selected_channel_id)
        elif self.current_view == "video_list":
            # Get selected video from video list
            try:
                video_list = self.query_one(VideoListWidget)
                video = video_list.get_selected_video()
                if video:
                    self.show_video_details(video)
            except:
                pass

    def show_channel_details(self, channel_id: str) -> None:
        """Show detailed view of a specific channel"""
        self.current_view = "channel_detail"
        self.selected_channel_id = channel_id
        container = self.query_one("#main_container", Container)
        container.remove_children()

        channel = self.channels_data.get(channel_id)
        if not channel:
            container.mount(Label(f"Channel {channel_id} not loaded", classes="error"))
            return

        videos = self.videos_data.get(channel_id, [])

        # Show detailed changes for this channel if any
        changes = self.changes_data.get(channel_id)
        if changes and changes.has_changes():
            changes_detail = self._build_channel_changes_detail(changes)
            container.mount(Static(changes_detail, classes="success", id="channel_changes"))

        # Create and mount channel detail widget
        channel_view = ChannelDetailWidget()
        container.mount(channel_view)
        self.call_after_refresh(channel_view.update_channel, channel, videos)

        # Load and display historical data
        self.load_channel_history(channel_id, channel_view)

    def _build_channel_changes_detail(self, changes: ChangeDetection) -> str:
        """Build detailed changes information for a channel"""
        parts = ["[bold green]📈 What's New?[/bold green]\n"]

        if changes.new_videos:
            parts.append(f"[yellow]✨ {len(changes.new_videos)} new video(s):[/yellow]")
            for video in changes.new_videos[:5]:  # Show max 5
                parts.append(f"  • {video.title[:60]}{'...' if len(video.title) > 60 else ''}")
            if len(changes.new_videos) > 5:
                parts.append(f"  ... and {len(changes.new_videos) - 5} more")
            parts.append("")

        if changes.updated_videos:
            parts.append(f"[cyan]📊 {len(changes.updated_videos)} video(s) with updated stats:[/cyan]")
            for video, change_dict in changes.updated_videos[:3]:  # Show max 3
                change_text = []
                if 'views' in change_dict:
                    change_text.append(f"+{change_dict['views']:,} views")
                if 'likes' in change_dict:
                    change_text.append(f"+{change_dict['likes']:,} likes")
                if 'comments' in change_dict:
                    change_text.append(f"+{change_dict['comments']:,} comments")
                parts.append(f"  • {video.title[:50]}... ({', '.join(change_text)})")
            if len(changes.updated_videos) > 3:
                parts.append(f"  ... and {len(changes.updated_videos) - 3} more")
            parts.append("")

        if changes.channel_changes:
            parts.append(f"[green]🎯 Channel growth:[/green]")
            if 'subscribers' in changes.channel_changes:
                diff = changes.channel_changes['subscribers']
                parts.append(f"  • Subscribers: {diff:+,}")
            if 'views' in changes.channel_changes:
                diff = changes.channel_changes['views']
                parts.append(f"  • Total views: {diff:+,}")

        return "\n".join(parts)

    @work(exclusive=False)
    async def load_channel_history(self, channel_id: str, widget: ChannelDetailWidget) -> None:
        """Load historical statistics for a channel and update the graph"""
        if not self.db:
            return

        try:
            history = await self.db.get_channel_history(channel_id, days=30)
            if history:
                await widget.update_graph_with_history(history)
        except Exception as e:
            # Silently fail if history loading fails
            pass

    @work(exclusive=False)
    async def load_dashboard_history(self, dashboard: DashboardWidget, channels: List[Channel]) -> None:
        """Load historical statistics for all channels and update dashboard"""
        if not self.db:
            # No database, just update without history
            self.call_after_refresh(dashboard.update_channels, channels, {})
            return

        try:
            # Load history for all channels
            history_dict = {}
            for channel in channels:
                history = await self.db.get_channel_history(channel.id, days=30)
                if history:
                    history_dict[channel.id] = history

            # Update dashboard with channels and history
            self.call_after_refresh(dashboard.update_channels, channels, history_dict)
        except Exception as e:
            # If history loading fails, just update without history
            self.call_after_refresh(dashboard.update_channels, channels, {})

    def show_video_list(self, channel_id: str) -> None:
        """Show list of all videos for a channel"""
        self.current_view = "video_list"
        self.selected_channel_id = channel_id
        container = self.query_one("#main_container", Container)
        container.remove_children()

        channel = self.channels_data.get(channel_id)
        if not channel:
            container.mount(Label(f"Channel {channel_id} not loaded", classes="error"))
            return

        videos = self.videos_data.get(channel_id, [])

        # Create and mount video list widget
        video_list = VideoListWidget()
        container.mount(video_list)
        self.call_after_refresh(video_list.update_videos, videos, channel.name)

    def show_video_details(self, video: Video) -> None:
        """Show detailed view of a specific video"""
        self.current_view = "video_detail"
        self.current_video = video  # Track current video for URL copy
        container = self.query_one("#main_container", Container)
        container.remove_children()

        # Calculate engagement metrics
        engagement_rate = (video.like_count / max(video.view_count, 1)) * 100
        comments_per_view = (video.comment_count / max(video.view_count, 1)) * 1000  # per 1000 views

        content = f"""[bold cyan]🎬 {video.title[:80]}{'...' if len(video.title) > 80 else ''}[/bold cyan]

[bold]Published:[/bold] {video.published_at.strftime('%Y-%m-%d %H:%M')}
[bold]Duration:[/bold] {video.formatted_duration}

[bold yellow]📊 Statistics:[/bold yellow]
  Views:     [yellow]{video.view_count:,}[/yellow]
  Likes:     [green]{video.like_count:,}[/green]
  Comments:  [blue]{video.comment_count:,}[/blue]

[bold magenta]📈 Engagement:[/bold magenta]
  Like Rate:       [magenta]{engagement_rate:.2f}%[/magenta]
  Comments/1k:     [magenta]{comments_per_view:.2f}[/magenta]

[dim]Press 'y' for URL | ESC to go back[/dim]
"""

        # Create horizontal layout container
        detail_container = Horizontal(id="video_detail_container")
        container.mount(detail_container)

        # Left column: video info
        info_widget = Static(content, classes="box", id="video_info")
        detail_container.mount(info_widget)

        # Right column: graph placeholder
        graph_widget = Static(id="video_graph", classes="box")
        detail_container.mount(graph_widget)

        # Load historical data and update graph
        self.load_video_history(video.id, graph_widget)

    @work(exclusive=False)
    async def load_video_history(self, video_id: str, widget: Static) -> None:
        """Load historical statistics for a video and update the graph"""
        if not self.db:
            return

        try:
            history = await self.db.get_video_history(video_id, days=30)
            if history and len(history) >= 2:
                await self._update_video_graph(widget, history)
            else:
                widget.update(
                    "[dim]📊 Video Statistics Trends[/dim]\n"
                    "[yellow]Not enough data yet. Check back after collecting more daily snapshots.[/yellow]"
                )
        except Exception as e:
            widget.update(
                "[dim]📊 Video Statistics Trends[/dim]\n"
                f"[red]Error loading history: {e}[/red]"
            )

    async def _update_video_graph(self, widget: Static, history: list) -> None:
        """Update widget with video statistics graph"""
        try:
            import plotext as plt
            from io import StringIO

            # Extract data for plotting
            dates = [stat.timestamp.strftime("%m-%d") for stat in history]
            views = [stat.view_count for stat in history]
            likes = [stat.like_count for stat in history]
            comments = [stat.comment_count for stat in history]

            # Create views graph (smaller size for 50% width column)
            plt.clf()
            plt.title("Views (30d)")
            plt.plot(dates, views, marker="braille", color="yellow")
            plt.xlabel("Date")
            plt.ylabel("Views")
            plt.theme("dark")
            plt.plotsize(50, 8)

            buffer = StringIO()
            plt.show(buffer)
            views_graph = buffer.getvalue()

            # Create engagement graph (likes + comments)
            plt.clf()
            plt.title("Engagement (30d)")
            plt.plot(dates, likes, marker="braille", color="green", label="Likes")
            plt.plot(dates, comments, marker="braille", color="blue", label="Comments")
            plt.xlabel("Date")
            plt.ylabel("Count")
            plt.theme("dark")
            plt.plotsize(50, 8)

            buffer = StringIO()
            plt.show(buffer)
            engagement_graph = buffer.getvalue()

            # Display both graphs
            widget.update(
                f"[dim]📊 Stats - {len(history)} pts[/dim]\n\n"
                f"{views_graph}\n\n{engagement_graph}"
            )
        except Exception as e:
            widget.update(
                "[dim]📊 Video Statistics Trends[/dim]\n"
                f"[red]Error rendering graph: {e}[/red]"
            )



def main():
    """Entry point for the application"""
    app = SuperTubeApp()
    app.run()


if __name__ == "__main__":
    main()
