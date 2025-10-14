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
from .widgets import (
    DashboardWidget, ChannelDetailWidget, VideoListWidget, TopFlopWidget,
    ChannelsListPanel, VideosListPanel, VideoDetailsPanel, MainViewPanel
)

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

    /* Lazydocker-style panel layout */
    .left-sidebar {
        width: 33%;
        layout: vertical;
        border-right: solid $primary;
    }

    .main-view-panel {
        width: 67%;
        padding: 0 2;
    }

    .channels-panel {
        height: 33%;
        border-bottom: solid $primary;
        padding: 1;
    }

    .videos-panel {
        height: 33%;
        border-bottom: solid $primary;
        padding: 1;
    }

    .details-panel {
        height: 34%;
        padding: 1;
    }

    .panel-title {
        text-align: center;
        padding: 0 0 1 0;
        background: $panel;
    }

    .details-content {
        padding: 1;
    }

    .main-view-content {
        padding: 1;
    }
    """

    TITLE = "SuperTube - YouTube Statistics"
    SUB_TITLE = f"Monitor your YouTube channels - v{VERSION}"

    BINDINGS = [
        Binding("q", "quit", "Quit", priority=True),
        Binding("r", "refresh", "Refresh", priority=True),
        Binding("?", "help", "Help"),
        Binding("tab", "next_panel", "Next Panel"),
        Binding("d", "dashboard", "Dashboard"),
        Binding("s", "cycle_sort", "Sort"),
        Binding("t", "show_topflop", "Top/Flop"),
        Binding("escape", "back", "Back"),
        # Vim-style navigation
        Binding("j", "cursor_down", "Down", show=False),
        Binding("k", "cursor_up", "Up", show=False),
        # Video URL copy
        Binding("y", "copy_video_url", "Copy URL", show=False),
        # Top/Flop controls (shown in context)
        Binding("p", "cycle_period", "Period", show=False),
        Binding("m", "cycle_metric", "Metric", show=False),
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
        # Top/Flop view state
        self.topflop_period = 7  # days
        self.topflop_metric = "views"  # metric

    def compose(self) -> ComposeResult:
        """Create child widgets - Lazydocker-style layout"""
        yield Header()

        # Main horizontal layout: left sidebar (1/3) + main view (2/3)
        with Horizontal(id="main_container"):
            # Left sidebar with 3 panels
            with Vertical(classes="left-sidebar"):
                yield ChannelsListPanel(classes="channels-panel", id="channels_panel")
                yield VideosListPanel(classes="videos-panel", id="videos_panel")
                yield VideoDetailsPanel(classes="details-panel", id="details_panel")

            # Main view panel (right side)
            yield MainViewPanel(classes="main-view-panel", id="main_view_panel")

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
        """Display the main dashboard - Feed data to panels"""
        self.current_view = "dashboard"

        if not self.channels_data:
            # Show error in main view if no data
            try:
                main_panel = self.query_one("#main_view_panel", MainViewPanel)
                main_panel.query_one("#main_view_content").update(
                    "[bold red]No data loaded. Press 'r' to refresh.[/bold red]"
                )
            except:
                pass
            return

        # Feed channels to ChannelsListPanel
        channels_list = list(self.channels_data.values())
        try:
            channels_panel = self.query_one("#channels_panel", ChannelsListPanel)
            channels_panel.update_channels(channels_list)
        except Exception as e:
            self.status_bar.set_status(f"Error loading channels: {e}")

        # Setup watchers for reactive updates
        self._setup_panel_watchers()

    def _setup_panel_watchers(self) -> None:
        """Setup reactive connections between panels"""
        try:
            channels_panel = self.query_one("#channels_panel", ChannelsListPanel)

            # Manually trigger initial selection
            if channels_panel.selected_channel_id:
                self._on_channel_selected(channels_panel.selected_channel_id)

        except Exception as e:
            self.status_bar.set_status(f"Error setting up panels: {e}")

    def _on_channel_selected(self, channel_id: str) -> None:
        """Callback when a channel is selected"""
        try:
            # Load videos for selected channel
            videos = self.videos_data.get(channel_id, [])
            videos_panel = self.query_one("#videos_panel", VideosListPanel)
            videos_panel.update_videos(videos)

            # Update main view with selected channel
            channel = self.channels_data.get(channel_id)
            main_panel = self.query_one("#main_view_panel", MainViewPanel)
            main_panel.update_channel_context(channel)

            # Store current channel
            self.selected_channel_id = channel_id

        except Exception as e:
            self.status_bar.set_status(f"Error loading channel: {e}")

    def _on_video_selected(self, video_id: str, video: Video) -> None:
        """Callback when a video is selected"""
        try:
            details_panel = self.query_one("#details_panel", VideoDetailsPanel)
            details_panel.update_video_details(video)

        except Exception as e:
            self.status_bar.set_status(f"Error showing video details: {e}")

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
  Tab        - Switch between panels (Channels ⇄ Videos)
  ?          - Show this help
  ESC        - Back to previous screen

[bold]New Panel Layout:[/bold]
  Left panels show: Channels → Videos → Video Details
  Right panel shows: Channel stats, Top/Flop analysis, etc.

  Navigation is automatic - just use ↑↓ to select!
  Selected channel → loads videos automatically
  Selected video → shows details automatically

[bold]Panel Commands:[/bold]
  ↑/↓ or j/k - Navigate in current panel (auto-selects)
  Tab        - Switch between Channels and Videos panels
  t          - Show Top/Flop analysis in main view
  d          - Return to Dashboard view in main panel
  y          - Show video URL (when video selected)

[bold]Top/Flop Analysis:[/bold]
  p          - Cycle period (7d → 30d → 90d)
  m          - Cycle metric (views → likes → comments → engagement)
  d          - Back to Dashboard view

[bold]Status Bar:[/bold]
  Shows last update time, current status, and notifications

[bold cyan]💡 Pro Tips:[/bold cyan]
  • Everything is visible at once - no more back/forth!
  • Just navigate with arrows - selection is automatic
  • Use Tab to switch between panels
  • Stats are collected automatically once per day
  • Green notifications show new videos and stat changes

[dim]Press ESC or 'd' to return to dashboard...[/dim]
        """
        container.mount(Static(help_text, classes="box"))

    def action_dashboard(self) -> None:
        """Return to dashboard or switch main panel to dashboard mode"""
        if self.current_view == "dashboard":
            # Already in dashboard - just switch main panel to dashboard mode
            try:
                main_panel = self.query_one("#main_view_panel", MainViewPanel)
                main_panel.update_mode("dashboard")
                self.status_bar.set_status("Dashboard view")
            except:
                pass
        else:
            # Go back to dashboard
            self.show_dashboard()

    def action_next_panel(self) -> None:
        """Navigate to next panel (Tab key)"""
        if self.current_view != "dashboard":
            return

        try:
            from textual.widgets import DataTable

            # Get focused widget
            focused = self.focused

            # Find which table is focused
            channels_table = self.query_one("#channels_panel_table", DataTable)
            videos_table = self.query_one("#videos_panel_table", DataTable)

            # Cycle: Channels → Videos → Channels
            if focused == channels_table:
                videos_table.focus()
            elif focused == videos_table:
                channels_table.focus()
            else:
                # Default: focus channels
                channels_table.focus()

        except Exception as e:
            self.status_bar.set_status(f"Tab navigation error: {e}")

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
        if self.current_view == "help":
            # Return to dashboard from help
            self.show_dashboard()
        elif self.current_view == "dashboard":
            # In dashboard, ESC switches main panel back to dashboard mode
            try:
                main_panel = self.query_one("#main_view_panel", MainViewPanel)
                main_panel.update_mode("dashboard")
                self.status_bar.set_status("Dashboard view")
            except:
                pass

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
        """Cycle through sort options in focused panel"""
        if self.current_view != "dashboard":
            return

        try:
            # Check which panel has focus and sort accordingly
            channels_panel = self.query_one("#channels_panel", ChannelsListPanel)
            videos_panel = self.query_one("#videos_panel", VideosListPanel)

            # Try channels panel first
            try:
                channels_table = channels_panel.query_one("#channels_panel_table")
                if channels_table.has_focus:
                    # Sort channels - we need to implement sorting in ChannelsListPanel
                    self.status_bar.set_status("Channel sorting not yet implemented in panel view")
                    return
            except:
                pass

            # Try videos panel
            try:
                videos_table = videos_panel.query_one("#videos_panel_table")
                if videos_table.has_focus:
                    # Sort videos - we need to implement sorting in VideosListPanel
                    self.status_bar.set_status("Video sorting not yet implemented in panel view")
                    return
            except:
                pass

        except Exception as e:
            self.status_bar.set_status(f"Sort error: {e}")

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

    def action_show_topflop(self) -> None:
        """Show Top/Flop analysis in main panel"""
        if self.current_view != "dashboard":
            return

        try:
            main_panel = self.query_one("#main_view_panel", MainViewPanel)
            main_panel.update_mode("topflop")
            self.status_bar.set_status("Showing Top/Flop analysis (use 'p' and 'm' to cycle period/metric)")
        except Exception as e:
            self.status_bar.set_status(f"Error: {e}")

    def action_cycle_period(self) -> None:
        """Cycle through period options in Top/Flop view"""
        if self.current_view != "topflop":
            return

        periods = [7, 30, 90]
        current_index = periods.index(self.topflop_period) if self.topflop_period in periods else 0
        self.topflop_period = periods[(current_index + 1) % len(periods)]

        # Reload Top/Flop view with new period
        if self.selected_channel_id:
            self.show_topflop_view(self.selected_channel_id)

    def action_cycle_metric(self) -> None:
        """Cycle through metric options in Top/Flop view"""
        if self.current_view != "topflop":
            return

        metrics = ["views", "likes", "comments", "engagement"]
        current_index = metrics.index(self.topflop_metric) if self.topflop_metric in metrics else 0
        self.topflop_metric = metrics[(current_index + 1) % len(metrics)]

        # Reload Top/Flop view with new metric
        if self.selected_channel_id:
            self.show_topflop_view(self.selected_channel_id)

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

    def show_topflop_view(self, channel_id: str) -> None:
        """Show Top/Flop analysis view for a channel"""
        self.current_view = "topflop"
        self.selected_channel_id = channel_id
        container = self.query_one("#main_container", Container)
        container.remove_children()

        channel = self.channels_data.get(channel_id)
        if not channel:
            container.mount(Label(f"Channel {channel_id} not loaded", classes="error"))
            return

        # Create and mount topflop widget
        topflop_widget = TopFlopWidget()
        container.mount(topflop_widget)

        # Load top/flop data asynchronously
        self.load_topflop_data(channel_id, topflop_widget)

    @work(exclusive=False)
    async def load_topflop_data(self, channel_id: str, widget: TopFlopWidget) -> None:
        """Load top and bottom performing videos"""
        if not self.db:
            return

        try:
            channel = self.channels_data.get(channel_id)
            if not channel:
                return

            # Get top and bottom videos
            top_videos = await self.db.get_top_videos_by_growth(
                channel_id,
                days=self.topflop_period,
                metric=self.topflop_metric,
                limit=10
            )

            bottom_videos = await self.db.get_bottom_videos_by_growth(
                channel_id,
                days=self.topflop_period,
                metric=self.topflop_metric,
                limit=10
            )

            # Update widget
            self.call_after_refresh(
                widget.update_data,
                channel.name,
                top_videos,
                bottom_videos,
                self.topflop_period,
                self.topflop_metric
            )
        except Exception as e:
            # Show error
            pass


def main():
    """Entry point for the application"""
    app = SuperTubeApp()
    app.run()


if __name__ == "__main__":
    main()
