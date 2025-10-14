"""Custom widgets for SuperTube TUI application"""

from datetime import datetime
from typing import List, Dict, Optional
from textual.app import ComposeResult
from textual.widgets import DataTable, Static, Label
from textual.containers import Container, Vertical, Horizontal
from textual.reactive import reactive

from .models import Channel, Video


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
            top_table.add_column("🏆 Top Performers", key="title", width=40)
            top_table.add_column("Growth", key="growth", width=15)
            top_table.add_column("Current", key="current", width=15)

        # Bottom videos table
        bottom_table = self.query_one("#bottom_videos_table", DataTable)
        if not bottom_table.columns:
            bottom_table.add_column("📉 Bottom Performers", key="title", width=40)
            bottom_table.add_column("Growth", key="growth", width=15)
            bottom_table.add_column("Current", key="current", width=15)

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

            # Truncate title
            title = video.title[:37] + "..." if len(video.title) > 40 else video.title

            table.add_row(title, growth_str, current, key=video.id)

    def _update_bottom_table(self, videos: List[tuple[Video, float]]) -> None:
        """Update bottom performers table"""
        table = self.query_one("#bottom_videos_table", DataTable)
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

            # Truncate title
            title = video.title[:37] + "..." if len(video.title) > 40 else video.title

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
        current_index = sort_options.index(self.sort_key) if self.sort_key in sort_options else 0

        # If same key, toggle direction
        if self.sort_key == sort_options[current_index]:
            self.sort_reverse = not self.sort_reverse
        else:
            # New key, start ascending
            self.sort_key = sort_options[(current_index + 1) % len(sort_options)]
            self.sort_reverse = False

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
        self.videos: List[Video] = []
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
        table.add_column("Title", key="title", width=25)
        table.add_column("Views", key="views", width=8)

    def update_videos(self, videos: List[Video]) -> None:
        """Update the videos list"""
        self.videos = videos
        self._sort_videos()
        self._refresh_table()

        # Auto-select first video
        if self.videos and not self.selected_video_id:
            self.selected_video_id = self.videos[0].id

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

            # Truncate title
            display_title = title[:23] + ".." if len(title) > 25 else title

            # Format view count properly
            if video.view_count >= 1000000:
                views_display = f"{video.view_count / 1000000:.1f}M"
            elif video.view_count >= 1000:
                views_display = f"{video.view_count / 1000:.1f}K"
            else:
                views_display = str(video.view_count)

            table.add_row(
                display_title,
                f"[yellow]{views_display}[/yellow]",
                key=video.id
            )

    def cycle_sort(self) -> str:
        """Cycle through sort options and return description"""
        sort_options = ["views", "date"]
        current_index = sort_options.index(self.sort_key) if self.sort_key in sort_options else 0

        # If same key, toggle direction
        if self.sort_key == sort_options[current_index]:
            self.sort_reverse = not self.sort_reverse
        else:
            # New key, start descending (most views/newest first)
            self.sort_key = sort_options[(current_index + 1) % len(sort_options)]
            self.sort_reverse = True

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
        """Update the video details display"""
        self.current_video = video
        content = self.query_one("#video_details_content", Static)

        if not video:
            content.update("[dim]No video selected[/dim]")
            return

        # Calculate engagement
        engagement_rate = (video.like_count / max(video.view_count, 1)) * 100

        details = f"""[bold]{video.title[:30]}...[/bold]

[dim]Published:[/dim]
{video.published_at.strftime('%Y-%m-%d')}

[dim]Duration:[/dim]
{video.formatted_duration}

[yellow]Views:[/yellow] {video.view_count:,}
[green]Likes:[/green] {video.like_count:,}
[blue]Comments:[/blue] {video.comment_count:,}

[magenta]Engagement:[/magenta]
{engagement_rate:.2f}%
"""
        content.update(details)


class MainViewPanel(Static):
    """Main right panel showing contextual views (lazydocker-style)"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_mode = "dashboard"  # "dashboard", "topflop", etc.
        self.current_channel: Optional[Channel] = None

    def compose(self) -> ComposeResult:
        """Create child widgets"""
        with Vertical():
            yield Static(id="main_view_content", classes="main-view-content")

    def update_mode(self, mode: str) -> None:
        """Switch between different view modes"""
        self.current_mode = mode
        self.refresh_view()

    def update_channel_context(self, channel: Optional[Channel]) -> None:
        """Update which channel is selected"""
        self.current_channel = channel
        self.refresh_view()

    def refresh_view(self) -> None:
        """Refresh the main view based on current mode and context"""
        content = self.query_one("#main_view_content", Static)

        if self.current_mode == "dashboard":
            self._show_dashboard_view(content)
        elif self.current_mode == "topflop":
            self._show_topflop_view(content)
        else:
            content.update(f"[dim]Mode: {self.current_mode}[/dim]")

    def _show_dashboard_view(self, content: Static) -> None:
        """Show dashboard stats for selected channel"""
        if not self.current_channel:
            content.update("[dim]Select a channel to view stats[/dim]")
            return

        ch = self.current_channel
        avg_views = ch.view_count // max(ch.video_count, 1)

        dashboard = f"""[bold cyan]📊 Channel Statistics[/bold cyan]

[bold]{ch.name}[/bold]

[bold yellow]Overview:[/bold yellow]
  Subscribers:  [green]{ch.subscriber_count:,}[/green]
  Total Views:  [yellow]{ch.view_count:,}[/yellow]
  Videos:       [blue]{ch.video_count:,}[/blue]

[bold magenta]Performance:[/bold magenta]
  Avg Views/Video:  [yellow]{avg_views:,}[/yellow]

[bold cyan]Description:[/bold cyan]
{ch.description[:300]}{'...' if len(ch.description) > 300 else ''}

[dim]Press 't' for Top/Flop analysis[/dim]
"""
        content.update(dashboard)

    def _show_topflop_view(self, content: Static) -> None:
        """Show Top/Flop placeholder"""
        content.update(
            "[bold cyan]📈 Top/Flop Analysis[/bold cyan]\n\n"
            "[yellow]Top/Flop widget will be integrated here[/yellow]\n"
            "[dim]Press 'd' to return to dashboard[/dim]"
        )
