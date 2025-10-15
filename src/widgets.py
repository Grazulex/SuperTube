"""Custom widgets for SuperTube TUI application"""

from datetime import datetime
from typing import List, Dict, Optional
from textual.app import ComposeResult
from textual.widgets import DataTable, Static, Label
from textual.containers import Container, Vertical, Horizontal
from textual.reactive import reactive

from .models import Channel, Video, Alert, VideoFilter, Comment, VideoSentiment, ChannelSentiment


class DashboardWidget(Static):
    """Main dashboard displaying all channels in a structured table"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.channels: List[Channel] = []
        self.stats_history: Dict[str, List] = {}  # Channel history for trend calculations
        self.sort_key = "subscribers"  # Default sort by subscribers
        self.sort_reverse = True  # Descending by default

    def compose(self) -> ComposeResult:
        """Create child widgets"""
        with Vertical():
            yield Label("[bold cyan]📊 YouTube Channels Overview[/bold cyan]", classes="dashboard-title")
            yield DataTable(id="channels_table", zebra_stripes=True, cursor_type="row")
            yield Static(id="stats_summary", classes="stats-box")

    def on_mount(self) -> None:
        """Initialize the table when widget is mounted"""
        # Table setup is now done in update_channels to avoid duplicate column issues
        pass

    def update_channels(self, channels: List[Channel], history: Dict[str, List] = None) -> None:
        """Update the dashboard with channel data"""
        self.channels = channels
        self.stats_history = history or {}

        # Sort channels before displaying
        self._sort_channels()

        table = self.query_one("#channels_table", DataTable)

        # Clear existing rows (keep columns), but check if columns exist first
        if table.columns:
            table.clear(columns=False)
        else:
            # Initialize columns if they don't exist yet
            table.add_column("Channel", key="channel", width=30)
            table.add_column("Subscribers", key="subs", width=15)
            table.add_column("Total Views", key="views", width=15)
            table.add_column("Videos", key="videos", width=10)
            table.add_column("Trend", key="trend", width=20)
            table.add_column("Growth", key="growth", width=12)
            table.cursor_type = "row"
            table.focus()

        # Add channel data
        for channel in self.channels:
            # Get history for this channel
            channel_history = self.stats_history.get(channel.id, [])

            # Calculate growth indicator from real data
            growth_indicator = self._calculate_growth(channel, channel_history)
            trend_sparkline = self._generate_sparkline(channel, channel_history)

            # Format numbers with separators
            subs = f"{channel.subscriber_count:,}"
            views = f"{channel.view_count:,}"
            videos = f"{channel.video_count:,}"

            # Add row with styled data
            table.add_row(
                channel.name,
                f"[green]{subs}[/green]",
                f"[yellow]{views}[/yellow]",
                f"[blue]{videos}[/blue]",
                trend_sparkline,
                growth_indicator,
                key=channel.id
            )

        # Update summary stats
        self._update_summary()

    def _calculate_growth(self, channel: Channel, history: List) -> str:
        """Calculate growth indicator for a channel based on real historical data"""
        if not history or len(history) < 2:
            return "[dim]—[/dim]"  # Not enough data

        # Get the oldest and newest data points (comparing first and last)
        oldest = history[0]
        newest = history[-1]

        # Calculate subscriber growth percentage
        old_subs = oldest.subscriber_count
        new_subs = newest.subscriber_count

        if old_subs == 0:
            return "[dim]—[/dim]"

        growth_percent = ((new_subs - old_subs) / old_subs) * 100

        # Format with color based on growth
        if growth_percent > 0:
            return f"[green]▲ {growth_percent:+.1f}%[/green]"
        elif growth_percent < 0:
            return f"[red]▼ {growth_percent:+.1f}%[/red]"
        else:
            return "[dim]━ 0.0%[/dim]"

    def _generate_sparkline(self, channel: Channel, history: List) -> str:
        """Generate ASCII sparkline for channel trend from real historical data"""
        sparkline_chars = ['▁', '▂', '▃', '▄', '▅', '▆', '▇', '█']

        if not history or len(history) < 2:
            return "[dim]" + "─" * 15 + "[/dim]"  # Not enough data

        # Use up to 15 most recent data points
        recent_history = history[-15:] if len(history) > 15 else history

        # Extract subscriber counts
        values = [stat.subscriber_count for stat in recent_history]

        # Normalize values to sparkline character indices
        min_val = min(values)
        max_val = max(values)

        if max_val == min_val:
            # All values are the same
            return sparkline_chars[4] * len(values)  # Middle character

        # Map each value to a sparkline character
        points = []
        for val in values:
            # Normalize to 0-1 range
            normalized = (val - min_val) / (max_val - min_val)
            # Map to character index
            idx = int(normalized * (len(sparkline_chars) - 1))
            points.append(sparkline_chars[idx])

        return ''.join(points)

    def _update_summary(self) -> None:
        """Update the summary statistics box"""
        if not self.channels:
            return

        total_subs = sum(c.subscriber_count for c in self.channels)
        total_views = sum(c.view_count for c in self.channels)
        total_videos = sum(c.video_count for c in self.channels)

        summary = self.query_one("#stats_summary", Static)
        summary.update(
            f"[dim]Total across all channels:[/dim] "
            f"[green]{total_subs:,}[/green] subscribers | "
            f"[yellow]{total_views:,}[/yellow] views | "
            f"[blue]{total_videos:,}[/blue] videos"
        )

    def get_selected_channel_id(self) -> Optional[str]:
        """Get the currently selected channel ID"""
        table = self.query_one("#channels_table", DataTable)
        if table.cursor_row >= 0 and table.cursor_row < len(self.channels):
            return self.channels[table.cursor_row].id
        return None

    def _sort_channels(self) -> None:
        """Sort channels by current sort key"""
        sort_keys = {
            "subscribers": lambda c: c.subscriber_count,
            "views": lambda c: c.view_count,
            "videos": lambda c: c.video_count,
            "name": lambda c: c.name.lower()
        }

        if self.sort_key in sort_keys:
            self.channels.sort(key=sort_keys[self.sort_key], reverse=self.sort_reverse)

    def change_sort(self, sort_key: str) -> None:
        """Change the sort key and refresh"""
        if self.sort_key == sort_key:
            # Toggle sort direction
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_key = sort_key
            self.sort_reverse = True

        self._sort_channels()
        self._refresh_table()

    def _refresh_table(self) -> None:
        """Refresh the table with current channel data"""
        table = self.query_one("#channels_table", DataTable)

        # Clear rows and rebuild
        table.clear(columns=False)

        # Add channel data
        for channel in self.channels:
            # Get history for this channel
            channel_history = self.stats_history.get(channel.id, [])

            # Calculate growth indicator from real data
            growth_indicator = self._calculate_growth(channel, channel_history)
            trend_sparkline = self._generate_sparkline(channel, channel_history)

            # Format numbers with separators
            subs = f"{channel.subscriber_count:,}"
            views = f"{channel.view_count:,}"
            videos = f"{channel.video_count:,}"

            # Add row with styled data
            table.add_row(
                channel.name,
                f"[green]{subs}[/green]",
                f"[yellow]{views}[/yellow]",
                f"[blue]{videos}[/blue]",
                trend_sparkline,
                growth_indicator,
                key=channel.id
            )


class ChannelDetailWidget(Static):
    """Detailed view of a single channel with graphs and top videos"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.channel: Optional[Channel] = None
        self.videos: List[Video] = []

    def compose(self) -> ComposeResult:
        """Create child widgets"""
        with Vertical():
            yield Label(id="channel_title", classes="channel-title")
            yield Static(id="channel_stats", classes="stats-box")
            yield Static(id="channel_info", classes="stats-box")
            yield Static(id="channel_graph", classes="graph-box")

    def update_channel(self, channel: Channel, videos: List[Video]) -> None:
        """Update the widget with channel and video data"""
        self.channel = channel
        self.videos = videos

        # Update title
        title = self.query_one("#channel_title", Label)
        title.update(f"[bold cyan]📺 {channel.name}[/bold cyan]")

        # Update main stats
        stats = self.query_one("#channel_stats", Static)
        stats.update(
            f"[green]Subscribers:[/green] {channel.subscriber_count:,} | "
            f"[yellow]Total Views:[/yellow] {channel.view_count:,} | "
            f"[blue]Videos:[/blue] {channel.video_count:,}"
        )

        # Update additional info
        info = self.query_one("#channel_info", Static)
        avg_views_per_video = channel.view_count // max(channel.video_count, 1)
        info.update(
            f"[bold]Channel Information:[/bold]\n"
            f"Average views per video: [yellow]{avg_views_per_video:,}[/yellow]\n"
            f"Total videos: [blue]{len(videos)}[/blue] videos loaded\n\n"
            f"[dim]{channel.description[:200]}{'...' if len(channel.description) > 200 else ''}[/dim]\n\n"
            f"[cyan]Press ENTER to view all videos[/cyan]"
        )

        # Update graph
        self._update_graph()

    def _update_graph(self) -> None:
        """Update the trend graph"""
        graph_box = self.query_one("#channel_graph", Static)

        # For now, show placeholder until we fetch historical data
        graph_box.update(
            "[dim]📈 Statistics Trends (30 days)[/dim]\n"
            "[yellow]Historical data will be displayed after multiple refreshes[/yellow]\n"
            "[dim]Tip: Run 'r' to refresh and collect data points[/dim]"
        )

    async def update_graph_with_history(self, history: list) -> None:
        """Update graph with historical data using plotext"""
        import plotext as plt
        from io import StringIO

        graph_box = self.query_one("#channel_graph", Static)

        if not history or len(history) < 2:
            graph_box.update(
                "[dim]📈 Statistics Trends (30 days)[/dim]\n"
                "[yellow]Not enough data yet. Refresh daily to build history.[/yellow]"
            )
            return

        # Extract data for plotting
        dates = [stat.timestamp.strftime("%m-%d") for stat in history]
        subscribers = [stat.subscriber_count for stat in history]
        views = [stat.view_count for stat in history]

        # Create subscriber graph
        plt.clf()
        plt.title("Subscribers (30 days)")
        plt.plot(dates, subscribers, marker="braille")
        plt.xlabel("Date")
        plt.ylabel("Subscribers")
        plt.theme("dark")
        plt.plotsize(60, 8)

        # Capture the plot as string
        buffer = StringIO()
        plt.show(buffer)
        sub_graph = buffer.getvalue()

        # Create views graph
        plt.clf()
        plt.title("Total Views (30 days)")
        plt.plot(dates, views, marker="braille", color="yellow")
        plt.xlabel("Date")
        plt.ylabel("Views")
        plt.theme("dark")
        plt.plotsize(60, 8)

        buffer = StringIO()
        plt.show(buffer)
        views_graph = buffer.getvalue()

        # Display both graphs
        graph_box.update(
            f"[dim]📈 Statistics Trends (30 days) - {len(history)} data points[/dim]\n\n"
            f"{sub_graph}\n\n{views_graph}"
        )


class VideoListWidget(Static):
    """Scrollable and sortable list of videos"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.all_videos: List[Video] = []  # All videos
        self.videos: List[Video] = []  # Filtered videos
        self.sort_key = "views"
        self.sort_reverse = True
        self.search_text = ""

    def compose(self) -> ComposeResult:
        """Create child widgets"""
        from textual.widgets import Input
        with Vertical():
            yield Static(id="video_list_title", classes="section-title")
            yield Input(placeholder="Search videos... (press / to focus)", id="video_search_input")
            yield DataTable(id="videos_table", zebra_stripes=True, cursor_type="row")

    def on_mount(self) -> None:
        """Initialize the table"""
        # Table setup is now done in _refresh_table to avoid duplicate column issues
        pass

    def update_videos(self, videos: List[Video], channel_name: str = "") -> None:
        """Update the video list"""
        self.all_videos = videos
        self.videos = videos.copy()  # Start with all videos
        self.channel_name = channel_name

        # Update title
        self._update_title()

        # Sort videos
        self._sort_videos()

        # Update table (focus is set inside _refresh_table on first setup)
        self._refresh_table()

    def _update_title(self) -> None:
        """Update the title with current filter info"""
        title = self.query_one("#video_list_title", Static)
        channel_name = getattr(self, 'channel_name', '')
        total = len(self.all_videos)
        filtered = len(self.videos)

        if filtered < total:
            title.update(f"📹 Videos - {channel_name} ({filtered}/{total} videos)")
        else:
            title.update(f"📹 Videos - {channel_name} ({total} videos)")

    def on_input_changed(self, event) -> None:
        """Handle search input changes"""
        from textual.widgets import Input
        if isinstance(event.input, Input) and event.input.id == "video_search_input":
            self.search_text = event.value.lower()
            self._apply_filter()

    def _apply_filter(self) -> None:
        """Apply search filter to videos"""
        if not self.search_text:
            self.videos = self.all_videos.copy()
        else:
            self.videos = [
                video for video in self.all_videos
                if self.search_text in video.title.lower()
            ]

        self._update_title()
        self._sort_videos()
        self._refresh_table()

    def focus_search(self) -> None:
        """Focus the search input"""
        try:
            search_input = self.query_one("#video_search_input")
            search_input.focus()
        except:
            pass

    def _sort_videos(self) -> None:
        """Sort videos by current sort key"""
        sort_keys = {
            "views": lambda v: v.view_count,
            "likes": lambda v: v.like_count,
            "comments": lambda v: v.comment_count,
            "date": lambda v: v.published_at,
            "engagement": lambda v: (v.like_count / max(v.view_count, 1)) * 100
        }

        if self.sort_key in sort_keys:
            self.videos.sort(key=sort_keys[self.sort_key], reverse=self.sort_reverse)

    def _refresh_table(self) -> None:
        """Refresh the table with current video data"""
        table = self.query_one("#videos_table", DataTable)

        # Clear only rows, but check if columns exist first
        if table.columns:
            table.clear(columns=False)
        else:
            # Initialize columns if they don't exist yet
            table.add_column("Title", key="title", width=50)
            table.add_column("Published", key="date", width=12)
            table.add_column("Views", key="views", width=12)
            table.add_column("Likes", key="likes", width=10)
            table.add_column("Comments", key="comments", width=10)
            table.add_column("Engagement", key="engagement", width=10)
            # Enable cursor and focus on first setup
            table.cursor_type = "row"
            table.focus()

        for video in self.videos:
            # Calculate engagement rate (likes/views)
            engagement = (video.like_count / max(video.view_count, 1)) * 100

            # Add badge for recent videos
            title = video.title
            if video.is_recent:
                badge = "🆕 "
                max_title_len = 47
            else:
                badge = ""
                max_title_len = 50

            # Truncate title considering badge
            display_title = badge + (title[:max_title_len] + "..." if len(title) > max_title_len else title)

            table.add_row(
                display_title,
                video.published_at.strftime("%Y-%m-%d"),
                f"[yellow]{video.view_count:,}[/yellow]",
                f"[green]{video.like_count:,}[/green]",
                f"[blue]{video.comment_count:,}[/blue]",
                f"[magenta]{engagement:.2f}%[/magenta]",
                key=video.id
            )

    def get_selected_video(self) -> Optional[Video]:
        """Get the currently selected video"""
        table = self.query_one("#videos_table", DataTable)
        if table.cursor_row >= 0 and table.cursor_row < len(self.videos):
            return self.videos[table.cursor_row]
        return None

    def change_sort(self, sort_key: str) -> None:
        """Change the sort key and refresh"""
        if self.sort_key == sort_key:
            # Toggle sort direction
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_key = sort_key
            self.sort_reverse = True

        self._sort_videos()
        self._refresh_table()

    def on_key(self, event) -> None:
        """Handle key events for this widget"""
        from textual.widgets import Input

        # Handle "/" to focus search
        if event.key == "slash" or event.key == "/":
            self.focus_search()
            event.prevent_default()
            event.stop()
            return

        # Handle "y" to copy video URL
        if event.key == "y":
            # Check if we're typing in the search input
            focused = self.app.focused
            if isinstance(focused, Input):
                # Let the input handle the key
                return

            # Get selected video and post a message to the app
            video = self.get_selected_video()
            if video:
                url = f"https://youtube.com/watch?v={video.id}"
                # Access the app's status bar directly
                if hasattr(self.app, 'status_bar') and self.app.status_bar:
                    self.app.status_bar.set_status(f"Video URL: {url}")
            event.prevent_default()
            event.stop()


class TopFlopWidget(Static):
    """Widget displaying top and bottom performing videos over a period"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.channel_name = ""
        self.period_days = 7
        self.metric = "views"

    def compose(self) -> ComposeResult:
        """Create child widgets"""
        with Vertical():
            yield Static(id="topflop_title", classes="section-title")
            yield Static(id="topflop_controls", classes="stats-box")
            with Horizontal():
                yield DataTable(id="top_videos_table", zebra_stripes=True)
                yield DataTable(id="bottom_videos_table", zebra_stripes=True)

    def on_mount(self) -> None:
        """Initialize the tables"""
        self._setup_tables()

    def _setup_tables(self) -> None:
        """Setup table columns"""
        # Top videos table
        top_table = self.query_one("#top_videos_table", DataTable)
        if not top_table.columns:
            top_table.add_column("🏆 Top Performers", key="title", width=25)
            top_table.add_column("Growth", key="growth", width=10)
            top_table.add_column("Current", key="current", width=10)

        # Bottom videos table
        bottom_table = self.query_one("#bottom_videos_table", DataTable)
        if not bottom_table.columns:
            bottom_table.add_column("📉 Bottom Performers", key="title", width=25)
            bottom_table.add_column("Growth", key="growth", width=10)
            bottom_table.add_column("Current", key="current", width=10)

    def update_data(
        self,
        channel_name: str,
        top_videos: List[tuple[Video, float]],
        bottom_videos: List[tuple[Video, float]],
        period_days: int,
        metric: str
    ) -> None:
        """Update the widget with top/flop video data"""
        self.channel_name = channel_name
        self.period_days = period_days
        self.metric = metric

        # Update title
        title_widget = self.query_one("#topflop_title", Static)
        period_labels = {7: "7 days", 30: "30 days", 90: "90 days"}
        metric_labels = {"views": "Views", "likes": "Likes", "comments": "Comments", "engagement": "Engagement"}
        title_widget.update(
            f"📊 Top/Flop Videos - {channel_name} | "
            f"Period: {period_labels.get(period_days, f'{period_days}d')} | "
            f"Metric: {metric_labels.get(metric, metric)}"
        )

        # Update controls info
        controls = self.query_one("#topflop_controls", Static)
        controls.update(
            "[dim]Press 'p' to cycle period (7d → 30d → 90d) | "
            "Press 'm' to cycle metric (views → likes → comments → engagement) | "
            "ESC to go back[/dim]"
        )

        # Update top videos table
        self._update_top_table(top_videos)

        # Update bottom videos table
        self._update_bottom_table(bottom_videos)

    def _update_top_table(self, videos: List[tuple[Video, float]]) -> None:
        """Update top performers table"""
        table = self.query_one("#top_videos_table", DataTable)

        # Ensure columns exist (in case on_mount wasn't called due to display=False)
        if not table.columns:
            table.add_column("🏆 Top Performers", key="title", width=25)
            table.add_column("Growth", key="growth", width=10)
            table.add_column("Current", key="current", width=10)

        table.clear(columns=False)

        if not videos:
            table.add_row(
                "[dim]Not enough data yet[/dim]",
                "[dim]—[/dim]",
                "[dim]—[/dim]"
            )
            return

        for video, growth in videos:
            # Format growth value based on metric
            if self.metric == "engagement":
                growth_str = f"[green]+{growth:.2f}%[/green]" if growth > 0 else f"[red]{growth:.2f}%[/red]"
            else:
                growth_str = f"[green]+{int(growth):,}[/green]" if growth > 0 else f"[red]{int(growth):,}[/red]"

            # Get current value
            if self.metric == "views":
                current = f"[yellow]{video.view_count:,}[/yellow]"
            elif self.metric == "likes":
                current = f"[green]{video.like_count:,}[/green]"
            elif self.metric == "comments":
                current = f"[blue]{video.comment_count:,}[/blue]"
            else:  # engagement
                eng_rate = video.engagement_rate
                current = f"[magenta]{eng_rate:.2f}%[/magenta]"

            # Truncate title to fit in 25-char column
            title = video.title[:22] + "..." if len(video.title) > 25 else video.title

            table.add_row(title, growth_str, current, key=video.id)

    def _update_bottom_table(self, videos: List[tuple[Video, float]]) -> None:
        """Update bottom performers table"""
        table = self.query_one("#bottom_videos_table", DataTable)

        # Ensure columns exist (in case on_mount wasn't called due to display=False)
        if not table.columns:
            table.add_column("📉 Bottom Performers", key="title", width=25)
            table.add_column("Growth", key="growth", width=10)
            table.add_column("Current", key="current", width=10)

        table.clear(columns=False)

        if not videos:
            table.add_row(
                "[dim]Not enough data yet[/dim]",
                "[dim]—[/dim]",
                "[dim]—[/dim]"
            )
            return

        for video, growth in videos:
            # Format growth value based on metric
            if self.metric == "engagement":
                growth_str = f"[green]+{growth:.2f}%[/green]" if growth > 0 else f"[red]{growth:.2f}%[/red]"
            else:
                growth_str = f"[green]+{int(growth):,}[/green]" if growth > 0 else f"[red]{int(growth):,}[/red]"

            # Get current value
            if self.metric == "views":
                current = f"[yellow]{video.view_count:,}[/yellow]"
            elif self.metric == "likes":
                current = f"[green]{video.like_count:,}[/green]"
            elif self.metric == "comments":
                current = f"[blue]{video.comment_count:,}[/blue]"
            else:  # engagement
                eng_rate = video.engagement_rate
                current = f"[magenta]{eng_rate:.2f}%[/magenta]"

            # Truncate title to fit in 25-char column
            title = video.title[:22] + "..." if len(video.title) > 25 else video.title

            table.add_row(title, growth_str, current, key=video.id)


# ============================================================================
# NEW PANEL-BASED WIDGETS FOR LAZYDOCKER-STYLE LAYOUT
# ============================================================================


class ChannelsListPanel(Static):
    """Left panel showing list of channels (lazydocker-style)"""

    selected_channel_id = reactive(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.channels: List[Channel] = []
        self.can_focus = True
        self.sort_key = "name"  # Default sort by name
        self.sort_reverse = False  # Ascending by default

    def compose(self) -> ComposeResult:
        """Create child widgets"""
        with Vertical():
            yield Label("[bold cyan]📊 Channels[/bold cyan]", classes="panel-title")
            yield DataTable(id="channels_panel_table", zebra_stripes=True, cursor_type="row")

    def on_mount(self) -> None:
        """Initialize the table"""
        table = self.query_one("#channels_panel_table", DataTable)
        table.add_column("Name", key="name", width=20)
        table.add_column("Subs", key="subs", width=10)
        table.focus()

    def update_channels(self, channels: List[Channel]) -> None:
        """Update the channels list"""
        self.channels = channels
        self._sort_channels()
        self._refresh_table()

        # Auto-select first channel
        if self.channels and not self.selected_channel_id:
            self.selected_channel_id = self.channels[0].id

    def _sort_channels(self) -> None:
        """Sort channels by current sort key"""
        sort_keys = {
            "name": lambda c: c.name.lower(),
            "subs": lambda c: c.subscriber_count
        }

        if self.sort_key in sort_keys:
            self.channels.sort(key=sort_keys[self.sort_key], reverse=self.sort_reverse)

    def _refresh_table(self) -> None:
        """Refresh the table with current channel data"""
        table = self.query_one("#channels_panel_table", DataTable)
        table.clear(columns=False)

        for channel in self.channels:
            # Format subscriber count properly
            if channel.subscriber_count >= 1000000:
                subs_display = f"{channel.subscriber_count / 1000000:.1f}M"
            elif channel.subscriber_count >= 1000:
                subs_display = f"{channel.subscriber_count / 1000:.1f}K"
            else:
                subs_display = str(channel.subscriber_count)

            table.add_row(
                channel.name[:18] + ".." if len(channel.name) > 20 else channel.name,
                f"[green]{subs_display}[/green]",
                key=channel.id
            )

    def cycle_sort(self) -> str:
        """Cycle through sort options and return description"""
        sort_options = ["name", "subs"]
        current_index = sort_options.index(self.sort_key) if self.sort_key in sort_options else -1

        # Move to next sort option
        next_index = (current_index + 1) % len(sort_options)
        self.sort_key = sort_options[next_index]

        # Set sensible default direction for each key
        if self.sort_key == "name":
            self.sort_reverse = False  # A-Z
        else:  # subs
            self.sort_reverse = True  # High to low

        self._sort_channels()
        self._refresh_table()

        direction = "↓" if self.sort_reverse else "↑"
        key_names = {"name": "Name", "subs": "Subscribers"}
        return f"Sorted by {key_names[self.sort_key]} {direction}"

    def on_data_table_row_highlighted(self, event) -> None:
        """Auto-select channel on navigation (lazydocker-style)"""
        if event.cursor_row >= 0 and event.cursor_row < len(self.channels):
            self.selected_channel_id = self.channels[event.cursor_row].id
            # Notify app about selection change
            if hasattr(self.app, '_on_channel_selected'):
                self.app._on_channel_selected(self.selected_channel_id)


class VideosListPanel(Static):
    """Left panel showing videos of selected channel (lazydocker-style)"""

    selected_video_id = reactive(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.all_videos: List[Video] = []  # All videos before filtering
        self.videos: List[Video] = []  # Filtered videos
        self.filter: VideoFilter = VideoFilter()  # Active filter
        self.can_focus = True
        self.sort_key = "views"  # Default sort by views
        self.sort_reverse = True  # Descending by default (most views first)

    def compose(self) -> ComposeResult:
        """Create child widgets"""
        with Vertical():
            yield Label("[bold cyan]🎬 Videos[/bold cyan]", classes="panel-title")
            yield DataTable(id="videos_panel_table", zebra_stripes=True, cursor_type="row")

    def on_mount(self) -> None:
        """Initialize the table"""
        table = self.query_one("#videos_panel_table", DataTable)
        table.add_column("Title", key="title", width=18)
        table.add_column("Views", key="views", width=7)
        table.add_column("Likes", key="likes", width=6)

    def update_videos(self, videos: List[Video]) -> None:
        """Update the videos list"""
        self.all_videos = videos
        self._apply_filter()
        self._sort_videos()
        self._refresh_table()

        # Auto-select first video
        if self.videos and not self.selected_video_id:
            self.selected_video_id = self.videos[0].id

    def _apply_filter(self) -> None:
        """Apply current filter to videos"""
        if not self.filter.is_active():
            self.videos = self.all_videos.copy()
        else:
            self.videos = [v for v in self.all_videos if self.filter.matches(v)]

    def set_filter(self, filter: VideoFilter) -> None:
        """Set filter and refresh"""
        self.filter = filter
        self._apply_filter()
        self._sort_videos()
        self._refresh_table()

    def clear_filter(self) -> None:
        """Clear all filters"""
        self.filter = VideoFilter()
        self._apply_filter()
        self._sort_videos()
        self._refresh_table()

    def set_filter_preset(self, preset: str) -> str:
        """Set a predefined filter and return description"""
        from datetime import timedelta, timezone
        # Use UTC timezone to match video timestamps
        today = datetime.now(timezone.utc)

        if preset == "recent":
            # Videos from last 7 days
            self.filter = VideoFilter(date_from=today - timedelta(days=7))
            desc = "Recent videos (7 days)"
        elif preset == "popular":
            # Videos with > 10K views
            self.filter = VideoFilter(views_min=10000)
            desc = "Popular videos (>10K views)"
        elif preset == "high_engagement":
            # Videos with engagement > 5%
            self.filter = VideoFilter(engagement_min=5.0)
            desc = "High engagement (>5%)"
        elif preset == "viral":
            # Videos with > 100K views
            self.filter = VideoFilter(views_min=100000)
            desc = "Viral videos (>100K views)"
        else:
            self.clear_filter()
            desc = "No filter"

        self._apply_filter()
        self._sort_videos()
        self._refresh_table()
        return desc

    def _sort_videos(self) -> None:
        """Sort videos by current sort key"""
        sort_keys = {
            "views": lambda v: v.view_count,
            "date": lambda v: v.published_at
        }

        if self.sort_key in sort_keys:
            self.videos.sort(key=sort_keys[self.sort_key], reverse=self.sort_reverse)

    def _refresh_table(self) -> None:
        """Refresh the table with current video data"""
        table = self.query_one("#videos_panel_table", DataTable)
        table.clear(columns=False)

        for video in self.videos[:50]:  # Limit to 50 most recent
            # Add badge for recent videos
            title = video.title
            if video.is_recent:
                badge = "🆕"
                title = f"{badge} {title}"

            # Truncate title (shorter to accommodate Likes column)
            display_title = title[:15] + ".." if len(title) > 17 else title

            # Format view count properly
            if video.view_count >= 1000000:
                views_display = f"{video.view_count / 1000000:.1f}M"
            elif video.view_count >= 1000:
                views_display = f"{video.view_count / 1000:.1f}K"
            else:
                views_display = str(video.view_count)

            # Format like count properly
            if video.like_count >= 1000000:
                likes_display = f"{video.like_count / 1000000:.1f}M"
            elif video.like_count >= 1000:
                likes_display = f"{video.like_count / 1000:.1f}K"
            else:
                likes_display = str(video.like_count)

            table.add_row(
                display_title,
                f"[yellow]{views_display}[/yellow]",
                f"[green]{likes_display}[/green]",
                key=video.id
            )

    def cycle_sort(self) -> str:
        """Cycle through sort options and return description"""
        sort_options = ["views", "date"]
        current_index = sort_options.index(self.sort_key) if self.sort_key in sort_options else -1

        # Move to next sort option
        next_index = (current_index + 1) % len(sort_options)
        self.sort_key = sort_options[next_index]

        # Set sensible default direction for each key
        if self.sort_key == "views":
            self.sort_reverse = True  # High to low
        else:  # date
            self.sort_reverse = True  # Newest first

        self._sort_videos()
        self._refresh_table()

        direction = "↓" if self.sort_reverse else "↑"
        key_names = {"views": "Views", "date": "Date"}
        return f"Sorted by {key_names[self.sort_key]} {direction}"

    def on_data_table_row_highlighted(self, event) -> None:
        """Auto-select video on navigation (lazydocker-style)"""
        if event.cursor_row >= 0 and event.cursor_row < len(self.videos):
            self.selected_video_id = self.videos[event.cursor_row].id
            # Notify app about selection change
            if hasattr(self.app, '_on_video_selected'):
                self.app._on_video_selected(self.selected_video_id, self.videos[event.cursor_row])


class VideoDetailsPanel(Static):
    """Left panel showing details of selected video (lazydocker-style)"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_video: Optional[Video] = None

    def compose(self) -> ComposeResult:
        """Create child widgets"""
        with Vertical():
            yield Label("[bold cyan]📋 Details[/bold cyan]", classes="panel-title")
            yield Static(id="video_details_content", classes="details-content")

    def update_video_details(self, video: Optional[Video]) -> None:
        """Update the video details display - ALL stats"""
        self.current_video = video
        content = self.query_one("#video_details_content", Static)

        if not video:
            content.update("[dim]No video selected[/dim]")
            return

        # Calculate engagement metrics
        engagement_rate = (video.like_count / max(video.view_count, 1)) * 100
        comments_per_1k = (video.comment_count / max(video.view_count, 1)) * 1000

        # Format counts
        views_fmt = f"{video.view_count:,}"
        likes_fmt = f"{video.like_count:,}"
        comments_fmt = f"{video.comment_count:,}"

        details = f"""[bold]{video.title[:25]}...[/bold]
{video.published_at.strftime('%Y-%m-%d')} | {video.formatted_duration}
[yellow]V:[/yellow]{views_fmt} [green]L:[/green]{likes_fmt} [blue]C:[/blue]{comments_fmt}
[magenta]Rate:[/magenta]{engagement_rate:.1f}% [magenta]C/1k:[/magenta]{comments_per_1k:.0f}"""
        content.update(details)


class MainViewPanel(Static):
    """Main right panel showing contextual views (lazydocker-style)"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_mode = "dashboard"  # "dashboard", "topflop", "temporal", "comparison", "titletag", "projection"
        self.current_channel: Optional[Channel] = None
        self.channel_history: Optional[List] = None

    def compose(self) -> ComposeResult:
        """Create child widgets"""
        with Vertical():
            # Dashboard content (visible in dashboard mode)
            yield Static(id="main_view_content", classes="main-view-content")
            # Top/Flop widget (visible in topflop mode)
            yield TopFlopWidget(id="topflop_widget")
            # Temporal Analysis panel (visible in temporal mode)
            yield TemporalAnalysisPanel(id="temporal_panel")
            # Channel Comparison panel (visible in comparison mode)
            yield ChannelComparisonPanel(id="comparison_panel")
            # Title/Tag Analysis panel (visible in titletag mode)
            yield TitleTagAnalysisPanel(id="titletag_panel")
            # Growth Projection panel (visible in projection mode)
            yield GrowthProjectionPanel(id="projection_panel")

    def on_mount(self) -> None:
        """Initialize widget visibility based on mode"""
        self._update_visibility()

    def update_mode(self, mode: str) -> None:
        """Switch between different view modes"""
        self.current_mode = mode
        self.refresh_view()

    def update_channel_context(self, channel: Optional[Channel], history: Optional[List] = None) -> None:
        """Update which channel is selected"""
        self.current_channel = channel
        self.channel_history = history
        self.refresh_view()

    def _update_visibility(self) -> None:
        """Show/hide widgets based on current mode"""
        try:
            content = self.query_one("#main_view_content", Static)
            topflop = self.query_one("#topflop_widget", TopFlopWidget)
            temporal = self.query_one("#temporal_panel", TemporalAnalysisPanel)
            comparison = self.query_one("#comparison_panel", ChannelComparisonPanel)
            titletag = self.query_one("#titletag_panel", TitleTagAnalysisPanel)
            projection = self.query_one("#projection_panel", GrowthProjectionPanel)

            if self.current_mode == "dashboard":
                content.display = True
                topflop.display = False
                temporal.display = False
                comparison.display = False
                titletag.display = False
                projection.display = False
            elif self.current_mode == "topflop":
                content.display = False
                topflop.display = True
                temporal.display = False
                comparison.display = False
                titletag.display = False
                projection.display = False
            elif self.current_mode == "temporal":
                content.display = False
                topflop.display = False
                temporal.display = True
                comparison.display = False
                titletag.display = False
                projection.display = False
            elif self.current_mode == "comparison":
                content.display = False
                topflop.display = False
                temporal.display = False
                comparison.display = True
                titletag.display = False
                projection.display = False
            elif self.current_mode == "titletag":
                content.display = False
                topflop.display = False
                temporal.display = False
                comparison.display = False
                titletag.display = True
                projection.display = False
            elif self.current_mode == "projection":
                content.display = False
                topflop.display = False
                temporal.display = False
                comparison.display = False
                titletag.display = False
                projection.display = True
        except:
            pass

    def refresh_view(self) -> None:
        """Refresh the main view based on current mode and context"""
        self._update_visibility()

        if self.current_mode == "dashboard":
            content = self.query_one("#main_view_content", Static)
            self._show_dashboard_view(content)
        elif self.current_mode == "topflop":
            self._show_topflop_view()
        elif self.current_mode == "temporal":
            self._show_temporal_view()
        elif self.current_mode == "comparison":
            self._show_comparison_view()
        elif self.current_mode == "titletag":
            self._show_titletag_view()
        elif self.current_mode == "projection":
            self._show_projection_view()
        else:
            content = self.query_one("#main_view_content", Static)
            content.update(f"[dim]Mode: {self.current_mode}[/dim]")

    def _show_dashboard_view(self, content: Static) -> None:
        """Show dashboard stats and graphs for selected channel"""
        if not self.current_channel:
            content.update("[dim]Select a channel to view stats[/dim]")
            return

        ch = self.current_channel
        avg_views = ch.view_count // max(ch.video_count, 1)

        # Build stats section
        stats_section = f"""[bold cyan]📊 {ch.name}[/bold cyan]

[bold yellow]Stats:[/bold yellow]
Subscribers:  [green]{ch.subscriber_count:,}[/green]
Total Views:  [yellow]{ch.view_count:,}[/yellow]
Videos:       [blue]{ch.video_count:,}[/blue]
Avg Views/Vid: [yellow]{avg_views:,}[/yellow]
"""

        # Add graphs if we have history
        if self.channel_history and len(self.channel_history) >= 2:
            graphs = self._generate_channel_graphs()
            dashboard = f"{stats_section}\n{graphs}\n\n[dim]Press 't' for Top/Flop[/dim]"
        else:
            dashboard = f"{stats_section}\n[dim yellow]📈 Graphs:[/dim yellow]\n[dim]Not enough history yet. Refresh daily to build trend graphs.[/dim]\n\n[dim]Press 't' for Top/Flop[/dim]"

        content.update(dashboard)

    def _generate_channel_graphs(self) -> str:
        """Generate ASCII graphs for channel trends"""
        try:
            if not self.channel_history or len(self.channel_history) < 2:
                return "[dim]Not enough data for graphs[/dim]"

            # For small datasets (< 5 points), show simple comparison instead of graph
            if len(self.channel_history) < 5:
                return self._generate_simple_comparison()

            # For larger datasets, use plotext
            import plotext as plt

            # Extract data
            subscribers = [stat.subscriber_count for stat in self.channel_history]
            views = [stat.view_count for stat in self.channel_history]

            # Subscribers graph
            plt.clf()
            plt.title("Subscribers Trend (30d)")
            plt.plot(subscribers, marker="braille", color="green")
            plt.theme("dark")
            plt.plotsize(70, 10)
            subs_graph = plt.build()

            # Views graph
            plt.clf()
            plt.title("Total Views Trend (30d)")
            plt.plot(views, marker="braille", color="yellow")
            plt.theme("dark")
            plt.plotsize(70, 10)
            views_graph = plt.build()

            return f"[dim yellow]📈 Trends ({len(self.channel_history)} pts):[/dim yellow]\n\n{subs_graph}\n{views_graph}"

        except Exception as e:
            return f"[dim red]Error generating graphs: {e}[/dim red]"

    def _generate_simple_comparison(self) -> str:
        """Generate simple text comparison for small datasets"""
        first = self.channel_history[0]
        last = self.channel_history[-1]

        # Calculate changes
        subs_change = last.subscriber_count - first.subscriber_count
        subs_pct = (subs_change / max(first.subscriber_count, 1)) * 100
        views_change = last.view_count - first.view_count
        views_pct = (views_change / max(first.view_count, 1)) * 100

        # Format dates
        first_date = first.timestamp.strftime("%d/%m")
        last_date = last.timestamp.strftime("%d/%m")

        # Format with colors
        subs_color = "green" if subs_change >= 0 else "red"
        views_color = "green" if views_change >= 0 else "red"
        subs_sign = "+" if subs_change >= 0 else ""
        views_sign = "+" if views_change >= 0 else ""

        return f"""[dim yellow]📈 Growth ({len(self.channel_history)} data points):[/dim yellow]

[bold]Subscribers:[/bold]
{first_date}: [green]{first.subscriber_count:,}[/green]  →  {last_date}: [green]{last.subscriber_count:,}[/green]
Change: [{subs_color}]{subs_sign}{subs_change:,}[/{subs_color}] ([{subs_color}]{subs_sign}{subs_pct:.1f}%[/{subs_color}])

[bold]Total Views:[/bold]
{first_date}: [yellow]{first.view_count:,}[/yellow]  →  {last_date}: [yellow]{last.view_count:,}[/yellow]
Change: [{views_color}]{views_sign}{views_change:,}[/{views_color}] ([{views_color}]{views_sign}{views_pct:.1f}%[/{views_color}])

[dim]Tip: More data points will show graphs[/dim]"""

    def _show_topflop_view(self) -> None:
        """Show Top/Flop widget with data"""
        try:
            topflop = self.query_one("#topflop_widget", TopFlopWidget)

            # Trigger data loading from app if we have a channel selected
            if self.current_channel and hasattr(self.app, 'load_topflop_data'):
                self.app.load_topflop_data(self.current_channel.id, topflop)
            else:
                # No channel selected - show placeholder
                topflop.query_one("#topflop_title", Static).update(
                    "[bold cyan]📈 Top/Flop Analysis[/bold cyan]"
                )
                topflop.query_one("#topflop_controls", Static).update(
                    "[yellow]Select a channel to view Top/Flop analysis[/yellow]"
                )
        except Exception:
            pass

    def _show_temporal_view(self) -> None:
        """Show Temporal Analysis panel with data"""
        try:
            temporal = self.query_one("#temporal_panel", TemporalAnalysisPanel)

            # Trigger data loading from app if we have a channel selected
            if self.current_channel and hasattr(self.app, 'load_temporal_data'):
                self.app.load_temporal_data(self.current_channel.id, temporal)
            else:
                # No channel selected - show placeholder
                temporal.query_one("#temporal_content", Static).update(
                    "[yellow]Select a channel to view temporal analysis[/yellow]"
                )
        except Exception:
            pass

    def _show_comparison_view(self) -> None:
        """Show Channel Comparison panel with data"""
        try:
            comparison = self.query_one("#comparison_panel", ChannelComparisonPanel)

            # Trigger data loading from app
            if hasattr(self.app, 'load_comparison_data'):
                self.app.load_comparison_data(comparison)
            else:
                # Show placeholder
                comparison.query_one("#comparison_controls", Static).update(
                    "[yellow]Loading comparison data...[/yellow]"
                )
        except Exception:
            pass

    def _show_titletag_view(self) -> None:
        """Show Title/Tag Analysis panel with data"""
        try:
            titletag = self.query_one("#titletag_panel", TitleTagAnalysisPanel)

            # Trigger data loading from app if we have a channel selected
            if self.current_channel and hasattr(self.app, 'load_titletag_data'):
                self.app.load_titletag_data(self.current_channel.id, titletag)
            else:
                # No channel selected - show placeholder
                titletag.query_one("#titletag_content", Static).update(
                    "[yellow]Select a channel to view title/tag analysis[/yellow]"
                )
        except Exception:
            pass

    def _show_projection_view(self) -> None:
        """Show Growth Projection panel with data"""
        try:
            projection = self.query_one("#projection_panel", GrowthProjectionPanel)

            # Trigger data loading from app if we have a channel selected
            if self.current_channel and hasattr(self.app, 'load_projection_data'):
                self.app.load_projection_data(self.current_channel.id, projection)
            else:
                # No channel selected - show placeholder
                projection.query_one("#projection_content", Static).update(
                    "[yellow]Select a channel to view growth projections[/yellow]"
                )
        except Exception:
            pass


class AlertsPanel(Static):
    """Panel showing recent alerts and notifications"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.alerts: List[Alert] = []

    def compose(self) -> ComposeResult:
        """Create child widgets"""
        with Vertical():
            yield Label("[bold cyan]🔔 Alerts[/bold cyan]", classes="panel-title")
            yield Static(id="alerts_content", classes="details-content")

    def update_alerts(self, alerts: List[Alert]) -> None:
        """Update the alerts display"""
        self.alerts = alerts
        content = self.query_one("#alerts_content", Static)

        if not alerts:
            content.update("[dim]No alerts[/dim]")
            return

        # Build alert list (limit to 10 most recent)
        alert_lines = []
        for alert in alerts[:10]:
            # Icon based on alert type
            if alert.alert_type == "success":
                icon = "✅"
                color = "green"
            elif alert.alert_type == "warning":
                icon = "⚠️"
                color = "yellow"
            else:  # danger
                icon = "🔴"
                color = "red"

            # Format message
            alert_lines.append(f"[{color}]{icon}[/{color}] {alert.message}")

        content.update("\n".join(alert_lines))


class TemporalAnalysisPanel(Static):
    """Panel showing temporal patterns and publication recommendations"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_channel_name = ""
        self.day_patterns = []
        self.hour_patterns = []
        self.month_patterns = []
        self.recommendations = None

    def compose(self) -> ComposeResult:
        """Create child widgets"""
        with Vertical():
            yield Label("[bold cyan]⏰ Temporal Analysis[/bold cyan]", classes="panel-title")
            yield Static(id="temporal_content", classes="details-content")

    def update_patterns(
        self,
        channel_name: str,
        day_patterns: List,
        hour_patterns: List,
        month_patterns: List,
        recommendations
    ) -> None:
        """Update the temporal analysis display"""
        self.current_channel_name = channel_name
        self.day_patterns = day_patterns
        self.hour_patterns = hour_patterns
        self.month_patterns = month_patterns
        self.recommendations = recommendations

        content = self.query_one("#temporal_content", Static)

        # Build display
        sections = []

        # Publication recommendations
        if recommendations:
            sections.append(
                f"[bold yellow]📌 Best Publishing Times:[/bold yellow]\n"
                f"Day: [green]{recommendations.best_day}[/green] (Score: {recommendations.best_day_score:.1f})\n"
                f"Hour: [green]{recommendations.best_hour:02d}:00[/green] (Score: {recommendations.best_hour_score:.1f})\n"
                f"Month: [green]{recommendations.best_month}[/green] (Score: {recommendations.best_month_score:.1f})"
            )

        # Day of week patterns (show top 3)
        valid_days = [p for p in day_patterns if p.video_count > 0]
        if valid_days:
            sorted_days = sorted(valid_days, key=lambda p: p.performance_score, reverse=True)
            top_days = sorted_days[:3]
            day_lines = ["[bold]🗓️  Top Days:[/bold]"]
            for i, pattern in enumerate(top_days, 1):
                day_lines.append(
                    f"{i}. {pattern.day_name}: {pattern.video_count} videos, "
                    f"avg {pattern.avg_views:,.0f} views (Score: {pattern.performance_score:.1f})"
                )
            sections.append("\n".join(day_lines))

        # Hour of day patterns (show top 3)
        valid_hours = [p for p in hour_patterns if p.video_count > 0]
        if valid_hours:
            sorted_hours = sorted(valid_hours, key=lambda p: p.performance_score, reverse=True)
            top_hours = sorted_hours[:3]
            hour_lines = ["[bold]🕐 Top Hours:[/bold]"]
            for i, pattern in enumerate(top_hours, 1):
                hour_lines.append(
                    f"{i}. {pattern.hour:02d}:00: {pattern.video_count} videos, "
                    f"avg {pattern.avg_views:,.0f} views (Score: {pattern.performance_score:.1f})"
                )
            sections.append("\n".join(hour_lines))

        # Monthly patterns (show top 3)
        valid_months = [p for p in month_patterns if p.video_count > 0]
        if valid_months:
            sorted_months = sorted(valid_months, key=lambda p: p.performance_score, reverse=True)
            top_months = sorted_months[:3]
            month_lines = ["[bold]📅 Top Months:[/bold]"]
            for i, pattern in enumerate(top_months, 1):
                month_lines.append(
                    f"{i}. {pattern.month_name}: {pattern.video_count} videos, "
                    f"avg {pattern.avg_views:,.0f} views (Score: {pattern.performance_score:.1f})"
                )
            sections.append("\n".join(month_lines))

        if sections:
            content.update("\n\n".join(sections))
        else:
            content.update("[dim]Not enough data for temporal analysis[/dim]")


class ChannelComparisonPanel(Static):
    """Panel showing side-by-side comparison of all channels"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.comparisons: List = []
        self.sort_metric = "performance"  # Default sort by performance score

    def compose(self) -> ComposeResult:
        """Create child widgets"""
        with Vertical():
            yield Label("[bold cyan]📊 Channel Comparison[/bold cyan]", classes="panel-title")
            yield Static(id="comparison_controls", classes="stats-box")
            yield DataTable(id="comparison_table", zebra_stripes=True)

    def on_mount(self) -> None:
        """Initialize the table"""
        table = self.query_one("#comparison_table", DataTable)
        # Setup columns
        table.add_column("Channel", key="channel", width=20)
        table.add_column("Subs", key="subs", width=10)
        table.add_column("Videos", key="videos", width=8)
        table.add_column("Avg Views", key="avg_views", width=12)
        table.add_column("Engagement", key="engagement", width=12)
        table.add_column("Growth", key="growth", width=12)
        table.add_column("Score", key="score", width=8)

    def update_comparisons(self, comparisons: List) -> None:
        """Update the comparison table with channel data"""
        self.comparisons = comparisons
        self._sort_comparisons()
        self._refresh_table()

        # Update controls
        controls = self.query_one("#comparison_controls", Static)
        sort_labels = {
            "performance": "Performance Score",
            "subs": "Subscribers",
            "engagement": "Engagement Rate",
            "growth": "Growth Rate",
            "views": "Avg Views"
        }
        controls.update(
            f"[dim]Sorted by: [yellow]{sort_labels.get(self.sort_metric, 'Performance')}[/yellow] | "
            f"Press 'm' to cycle sort metric | Press 'd' to return to dashboard[/dim]"
        )

    def _sort_comparisons(self) -> None:
        """Sort comparisons by current metric"""
        sort_keys = {
            "performance": lambda c: c.performance_score,
            "subs": lambda c: c.subscriber_count,
            "engagement": lambda c: c.avg_engagement_rate,
            "growth": lambda c: c.subscriber_growth_percent,
            "views": lambda c: c.avg_views_per_video
        }

        if self.sort_metric in sort_keys:
            self.comparisons.sort(key=sort_keys[self.sort_metric], reverse=True)

    def _refresh_table(self) -> None:
        """Refresh the table with current comparison data"""
        table = self.query_one("#comparison_table", DataTable)
        table.clear(columns=False)

        for comp in self.comparisons:
            # Format numbers
            subs_fmt = f"{comp.subscriber_count / 1000000:.1f}M" if comp.subscriber_count >= 1000000 else f"{comp.subscriber_count / 1000:.1f}K"
            videos_fmt = str(comp.video_count)
            avg_views_fmt = f"{comp.avg_views_per_video / 1000:.1f}K" if comp.avg_views_per_video >= 1000 else f"{comp.avg_views_per_video:.0f}"

            # Growth with color
            growth_color = "green" if comp.subscriber_growth_percent >= 0 else "red"
            growth_fmt = f"[{growth_color}]{comp.subscriber_growth_percent:+.1f}%[/{growth_color}]"

            # Engagement with color (green if > 3%, yellow if > 1%, else white)
            if comp.avg_engagement_rate >= 3.0:
                eng_color = "green"
            elif comp.avg_engagement_rate >= 1.0:
                eng_color = "yellow"
            else:
                eng_color = "white"
            eng_fmt = f"[{eng_color}]{comp.avg_engagement_rate:.2f}%[/{eng_color}]"

            # Performance score with color
            score = comp.performance_score
            if score >= 7.0:
                score_color = "green"
            elif score >= 4.0:
                score_color = "yellow"
            else:
                score_color = "red"
            score_fmt = f"[{score_color}]{score:.1f}[/{score_color}]"

            table.add_row(
                comp.channel_name[:18] + ".." if len(comp.channel_name) > 20 else comp.channel_name,
                f"[green]{subs_fmt}[/green]",
                f"[blue]{videos_fmt}[/blue]",
                f"[yellow]{avg_views_fmt}[/yellow]",
                eng_fmt,
                growth_fmt,
                score_fmt,
                key=comp.channel_id
            )

    def cycle_sort_metric(self) -> str:
        """Cycle through sort metrics and return description"""
        metrics = ["performance", "subs", "engagement", "growth", "views"]
        current_index = metrics.index(self.sort_metric) if self.sort_metric in metrics else 0
        next_index = (current_index + 1) % len(metrics)
        self.sort_metric = metrics[next_index]

        self._sort_comparisons()
        self._refresh_table()

        # Update controls display
        self.update_comparisons(self.comparisons)

        metric_labels = {
            "performance": "Performance Score",
            "subs": "Subscribers",
            "engagement": "Engagement Rate",
            "growth": "Growth Rate",
            "views": "Avg Views"
        }
        return f"Sorted by {metric_labels[self.sort_metric]}"


class TitleTagAnalysisPanel(Static):
    """Panel showing title and tag analysis insights"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.insights = None

    def compose(self) -> ComposeResult:
        """Create child widgets"""
        with Vertical():
            yield Label("[bold cyan]📝 Title & Tag Analysis[/bold cyan]", classes="panel-title")
            yield Static(id="titletag_content", classes="details-content")

    def update_insights(self, insights) -> None:
        """Update the title/tag analysis display"""
        self.insights = insights
        content = self.query_one("#titletag_content", Static)

        if not insights or insights.analyzed_video_count == 0:
            content.update("[dim]Not enough data for title/tag analysis[/dim]")
            return

        # Build display sections
        sections = []

        # Title patterns section
        pattern = insights.title_pattern
        sections.append(
            f"[bold yellow]📊 Title Patterns ({insights.analyzed_video_count} videos analyzed):[/bold yellow]\n"
            f"Average Length: [cyan]{pattern.avg_length:.0f}[/cyan] characters\n"
            f"Average Words: [cyan]{pattern.avg_word_count:.0f}[/cyan] words\n"
            f"Best Length: [green]{pattern.length_correlation.title()}[/green] titles perform better"
        )

        # Top keywords section
        if pattern.top_keywords:
            kw_lines = ["[bold]🔑 Top Performing Keywords:[/bold]"]
            for i, (keyword, score) in enumerate(pattern.top_keywords[:10], 1):
                # Color code by score
                if score >= 7.0:
                    color = "green"
                elif score >= 4.0:
                    color = "yellow"
                else:
                    color = "white"
                kw_lines.append(f"{i:2d}. [{color}]{keyword}[/{color}] (Score: {score:.1f})")
            sections.append("\n".join(kw_lines))

        # Common words section (most frequent)
        if pattern.common_words:
            common_lines = ["[bold]💬 Most Common Words:[/bold]"]
            for i, (word, count) in enumerate(pattern.common_words[:8], 1):
                common_lines.append(f"{i}. {word} ({count}x)")
            sections.append("\n".join(common_lines))

        # Suggested keywords
        if insights.suggested_keywords:
            suggested = ", ".join(insights.suggested_keywords[:8])
            sections.append(f"[bold green]✨ Suggested Keywords:[/bold green]\n{suggested}")

        content.update("\n\n".join(sections))


class GrowthProjectionPanel(Static):
    """Panel showing growth projections and milestone predictions"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.channel_name = ""
        self.subscriber_projection = None
        self.view_projection = None
        self.milestones = []

    def compose(self) -> ComposeResult:
        """Create child widgets"""
        with Vertical():
            yield Label("[bold cyan]📈 Growth Projections[/bold cyan]", classes="panel-title")
            yield Static(id="projection_content", classes="details-content")

    def update_projections(
        self,
        channel_name: str,
        subscriber_projection,
        view_projection,
        milestones: List
    ) -> None:
        """Update the projections display"""
        self.channel_name = channel_name
        self.subscriber_projection = subscriber_projection
        self.view_projection = view_projection
        self.milestones = milestones

        content = self.query_one("#projection_content", Static)

        # Check if we have enough data
        if not subscriber_projection or subscriber_projection.confidence == 0.0:
            content.update(
                f"[bold]{channel_name}[/bold]\n\n"
                "[yellow]Not enough historical data for projections.[/yellow]\n"
                "[dim]Refresh daily to build history (minimum 2 data points required).[/dim]"
            )
            return

        # Build display sections
        sections = []

        # Subscribers projection
        sub_proj = subscriber_projection
        sub_conf_color = self._get_confidence_color(sub_proj.confidence)
        sections.append(
            f"[bold green]📊 Subscribers Projection:[/bold green]\n"
            f"Current: [green]{sub_proj.current_value:,}[/green]\n"
            f"30 days:  [green]{sub_proj.projected_30d:,}[/green] ([cyan]+{sub_proj.growth_30d:,}[/cyan])\n"
            f"60 days:  [green]{sub_proj.projected_60d:,}[/green] ([cyan]+{sub_proj.growth_60d:,}[/cyan])\n"
            f"90 days:  [green]{sub_proj.projected_90d:,}[/green] ([cyan]+{sub_proj.growth_90d:,}[/cyan])\n"
            f"Daily rate: [yellow]{sub_proj.daily_growth_rate:+.1f}[/yellow] subs/day\n"
            f"Confidence: [{sub_conf_color}]{sub_proj.get_confidence_label()}[/{sub_conf_color}] "
            f"[dim]({sub_proj.confidence:.1%})[/dim]"
        )

        # Views projection
        view_proj = view_projection
        view_conf_color = self._get_confidence_color(view_proj.confidence)
        sections.append(
            f"[bold yellow]📺 Views Projection:[/bold yellow]\n"
            f"Current: [yellow]{view_proj.current_value:,}[/yellow]\n"
            f"30 days:  [yellow]{view_proj.projected_30d:,}[/yellow] ([cyan]+{view_proj.growth_30d:,}[/cyan])\n"
            f"60 days:  [yellow]{view_proj.projected_60d:,}[/yellow] ([cyan]+{view_proj.growth_60d:,}[/cyan])\n"
            f"90 days:  [yellow]{view_proj.projected_90d:,}[/yellow] ([cyan]+{view_proj.growth_90d:,}[/cyan])\n"
            f"Daily rate: [yellow]{view_proj.daily_growth_rate:+,.0f}[/yellow] views/day\n"
            f"Confidence: [{view_conf_color}]{view_proj.get_confidence_label()}[/{view_conf_color}] "
            f"[dim]({view_proj.confidence:.1%})[/dim]"
        )

        # Milestones (next 3 achievable)
        achievable_milestones = [m for m in milestones if m.achievable and m.days_until and m.days_until > 0]
        if achievable_milestones:
            milestone_lines = ["[bold magenta]🎯 Next Milestones:[/bold magenta]"]
            for i, milestone in enumerate(achievable_milestones[:3], 1):
                conf_color = self._get_confidence_color(milestone.confidence)
                if milestone.estimated_date:
                    date_str = milestone.estimated_date.strftime("%Y-%m-%d")
                    days_str = f"{milestone.days_until} days"
                    milestone_lines.append(
                        f"{i}. [{conf_color}]{milestone.threshold:,}[/{conf_color}] {milestone.metric}: "
                        f"[cyan]{date_str}[/cyan] ([dim]{days_str}[/dim])"
                    )
            sections.append("\n".join(milestone_lines))
        else:
            sections.append("[dim]🎯 Milestones: No upcoming milestones (negative/flat growth)[/dim]")

        content.update("\n\n".join(sections))

    def _get_confidence_color(self, confidence: float) -> str:
        """Get color for confidence level"""
        if confidence >= 0.8:
            return "green"
        elif confidence >= 0.5:
            return "yellow"
        elif confidence >= 0.3:
            return "white"
        else:
            return "red"


class CommentsSentimentPanel(Static):
    """Panel showing comments with sentiment analysis for a video"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.video_title = ""
        self.comments: List[Comment] = []
        self.sentiment_stats: Optional[VideoSentiment] = None

    def compose(self) -> ComposeResult:
        """Create child widgets"""
        with Vertical():
            yield Label("[bold cyan]💬 Comments & Sentiment[/bold cyan]", classes="panel-title")
            yield Static(id="sentiment_summary", classes="stats-box")
            yield DataTable(id="comments_table", zebra_stripes=True, cursor_type="row")

    def on_mount(self) -> None:
        """Initialize the table"""
        table = self.query_one("#comments_table", DataTable)
        table.add_column("Author", key="author", width=20)
        table.add_column("Comment", key="comment", width=50)
        table.add_column("Sentiment", key="sentiment", width=10)
        table.add_column("Likes", key="likes", width=8)

    def update_comments(
        self,
        video_title: str,
        comments: List[Comment],
        sentiment_stats: Optional[VideoSentiment] = None
    ) -> None:
        """Update the comments display"""
        self.video_title = video_title
        self.comments = comments
        self.sentiment_stats = sentiment_stats

        # Update summary
        self._update_summary()

        # Update table
        self._refresh_table()

    def _update_summary(self) -> None:
        """Update the sentiment summary stats"""
        summary = self.query_one("#sentiment_summary", Static)

        if not self.sentiment_stats or self.sentiment_stats.total_comments == 0:
            summary.update(
                f"[bold]{self.video_title[:60]}...[/bold]\n"
                "[dim]No sentiment data available yet[/dim]"
            )
            return

        stats = self.sentiment_stats

        # Get sentiment color based on average
        if stats.avg_sentiment > 0.1:
            sentiment_color = "green"
            sentiment_icon = "😊"
        elif stats.avg_sentiment < -0.1:
            sentiment_color = "red"
            sentiment_icon = "😟"
        else:
            sentiment_color = "yellow"
            sentiment_icon = "😐"

        # Build summary display
        summary_text = f"""[bold]{self.video_title[:60]}...[/bold]

[bold]Sentiment Overview:[/bold]
Total Comments: [cyan]{stats.total_comments}[/cyan]
[green]Positive:[/green] {stats.positive_count} ({stats.positive_percent:.1f}%)
[yellow]Neutral:[/yellow] {stats.neutral_count} ({stats.neutral_percent:.1f}%)
[red]Negative:[/red] {stats.negative_count} ({stats.negative_percent:.1f}%)
Overall: [{sentiment_color}]{sentiment_icon} {stats.sentiment_label.title()}[/{sentiment_color}] ([{sentiment_color}]{stats.avg_sentiment:+.2f}[/{sentiment_color}])"""

        # Add top keywords if available
        if stats.top_keywords:
            keywords = ", ".join([f"{kw} ({count})" for kw, count in stats.top_keywords[:5]])
            summary_text += f"\n\n[bold]Top Keywords:[/bold] [dim]{keywords}[/dim]"

        summary.update(summary_text)

    def _refresh_table(self) -> None:
        """Refresh the comments table"""
        table = self.query_one("#comments_table", DataTable)
        table.clear(columns=False)

        if not self.comments:
            table.add_row(
                "[dim]No comments[/dim]",
                "[dim]No comments available for this video[/dim]",
                "[dim]—[/dim]",
                "[dim]—[/dim]"
            )
            return

        # Sort comments by likes (most liked first)
        sorted_comments = sorted(self.comments, key=lambda c: c.like_count, reverse=True)

        for comment in sorted_comments[:50]:  # Limit to 50 comments
            # Truncate author name
            author = comment.author[:18] + ".." if len(comment.author) > 20 else comment.author

            # Truncate comment text
            text = comment.text.replace("\n", " ")  # Remove line breaks
            display_text = text[:47] + "..." if len(text) > 50 else text

            # Format sentiment with color and icon
            if comment.sentiment_label == "positive":
                sentiment_display = "[green]😊 Pos[/green]"
            elif comment.sentiment_label == "negative":
                sentiment_display = "[red]😟 Neg[/red]"
            else:
                sentiment_display = "[yellow]😐 Neu[/yellow]"

            # Format like count
            if comment.like_count >= 1000:
                likes_display = f"{comment.like_count / 1000:.1f}K"
            else:
                likes_display = str(comment.like_count)

            table.add_row(
                author,
                display_text,
                sentiment_display,
                f"[dim]{likes_display}[/dim]",
                key=comment.id
            )


class ChannelSentimentPanel(Static):
    """Panel showing aggregated sentiment across a channel"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.channel_name = ""
        self.sentiment_stats: Optional[ChannelSentiment] = None

    def compose(self) -> ComposeResult:
        """Create child widgets"""
        with Vertical():
            yield Label("[bold cyan]💭 Channel Sentiment Overview[/bold cyan]", classes="panel-title")
            yield Static(id="channel_sentiment_content", classes="details-content")

    def update_sentiment(
        self,
        channel_name: str,
        sentiment_stats: Optional[ChannelSentiment] = None
    ) -> None:
        """Update the channel sentiment display"""
        self.channel_name = channel_name
        self.sentiment_stats = sentiment_stats

        content = self.query_one("#channel_sentiment_content", Static)

        if not sentiment_stats or sentiment_stats.total_comments == 0:
            content.update(
                f"[bold]{channel_name}[/bold]\n\n"
                "[dim]No sentiment data available yet.\n"
                "Comments will be analyzed on next refresh.[/dim]"
            )
            return

        stats = sentiment_stats

        # Get overall sentiment color
        if stats.avg_sentiment > 0.1:
            sentiment_color = "green"
            sentiment_icon = "😊"
        elif stats.avg_sentiment < -0.1:
            sentiment_color = "red"
            sentiment_icon = "😟"
        else:
            sentiment_color = "yellow"
            sentiment_icon = "😐"

        # Build display
        sections = []

        # Overall stats
        sections.append(
            f"[bold yellow]📊 Sentiment Summary:[/bold yellow]\n"
            f"Videos Analyzed: [cyan]{stats.videos_analyzed}[/cyan]\n"
            f"Total Comments: [cyan]{stats.total_comments:,}[/cyan]\n"
            f"[green]Positive:[/green] {stats.positive_count:,} ({stats.positive_percent:.1f}%)\n"
            f"[yellow]Neutral:[/yellow] {stats.neutral_count:,} ({stats.neutral_percent:.1f}%)\n"
            f"[red]Negative:[/red] {stats.negative_count:,} ({stats.negative_percent:.1f}%)\n"
            f"Overall: [{sentiment_color}]{sentiment_icon} {stats.sentiment_label.title()}[/{sentiment_color}] "
            f"([{sentiment_color}]{stats.avg_sentiment:+.2f}[/{sentiment_color}])"
        )

        # Videos with negative feedback
        if stats.videos_with_negative_feedback:
            sections.append(
                f"[bold red]⚠️  Videos with High Negative Feedback (>40%):[/bold red]\n" +
                "\n".join([
                    f"{i}. Video ID: [dim]{vid_id[:15]}...[/dim] - [red]{neg_pct:.1f}%[/red] negative"
                    for i, (vid_id, neg_pct) in enumerate(stats.videos_with_negative_feedback, 1)
                ])
            )
        else:
            sections.append("[green]✅ No videos with concerning negative feedback[/green]")

        content.update("\n\n".join(sections))

