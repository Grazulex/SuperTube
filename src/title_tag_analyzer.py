"""Title and tag analysis for video optimization"""

from typing import List, Dict
from collections import Counter
import re

from .models import Video, TitlePattern, TagAnalysis, TitleTagInsights


class TitleTagAnalyzer:
    """Analyze video titles and tags to identify successful patterns"""

    # Common stop words to filter out (English and French)
    STOP_WORDS = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be',
        'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
        'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this',
        'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they',
        # French stop words
        'le', 'la', 'les', 'un', 'une', 'des', 'de', 'du', 'et', 'ou', 'mais',
        'pour', 'dans', 'sur', 'avec', 'par', 'est', 'sont', 'a', 'ai', 'as',
        'ont', 'ce', 'cette', 'ces', 'qui', 'que', 'quoi', 'où', 'comment'
    }

    def __init__(self, videos: List[Video], performance_threshold_percentile: float = 0.6):
        """
        Initialize analyzer with list of videos

        Args:
            videos: List of Video objects to analyze
            performance_threshold_percentile: Consider top X% as "successful" (default: 60%)
        """
        self.videos = videos
        self.performance_threshold_percentile = performance_threshold_percentile

    def _calculate_performance_score(self, video: Video) -> float:
        """Calculate weighted performance score for a video"""
        # Normalize metrics (0-10 scale)
        normalized_views = min(video.view_count / 10000, 10.0)
        normalized_engagement = min(video.engagement_rate, 10.0)
        normalized_likes = min(video.like_ratio, 10.0)

        # Weighted score: 50% views, 30% engagement, 20% likes
        return (normalized_views * 0.5) + (normalized_engagement * 0.3) + (normalized_likes * 0.2)

    def _extract_keywords(self, title: str) -> List[str]:
        """Extract meaningful keywords from a title"""
        # Convert to lowercase
        title = title.lower()

        # Remove special characters, keep only alphanumeric and spaces
        title = re.sub(r'[^\w\s]', ' ', title)

        # Split into words
        words = title.split()

        # Filter out stop words and very short words
        keywords = [
            word for word in words
            if len(word) > 2 and word not in self.STOP_WORDS
        ]

        return keywords

    def analyze_title_patterns(self) -> TitlePattern:
        """Analyze patterns in video titles"""
        if not self.videos:
            return TitlePattern(
                avg_length=0.0,
                avg_word_count=0.0,
                common_words=[],
                top_keywords=[],
                length_correlation="medium"
            )

        # Calculate performance scores for all videos
        video_scores = [(v, self._calculate_performance_score(v)) for v in self.videos]

        # Determine threshold for "successful" videos
        scores = sorted([score for _, score in video_scores], reverse=True)
        threshold_index = int(len(scores) * self.performance_threshold_percentile)
        threshold_score = scores[threshold_index] if threshold_index < len(scores) else 0

        # Filter successful videos
        successful_videos = [v for v, score in video_scores if score >= threshold_score]

        # Analyze title lengths
        title_lengths = [len(v.title) for v in successful_videos]
        avg_length = sum(title_lengths) / len(title_lengths)

        # Analyze word counts
        word_counts = [len(v.title.split()) for v in successful_videos]
        avg_word_count = sum(word_counts) / len(word_counts)

        # Extract and count keywords
        all_keywords = []
        keyword_scores: Dict[str, List[float]] = {}

        for video in successful_videos:
            keywords = self._extract_keywords(video.title)
            all_keywords.extend(keywords)

            score = self._calculate_performance_score(video)
            for keyword in keywords:
                if keyword not in keyword_scores:
                    keyword_scores[keyword] = []
                keyword_scores[keyword].append(score)

        # Most common words
        word_freq = Counter(all_keywords)
        common_words = word_freq.most_common(20)

        # Keywords with best average performance
        keyword_avg_scores = {
            kw: sum(scores) / len(scores)
            for kw, scores in keyword_scores.items()
            if len(scores) >= 2  # Only keywords that appear in at least 2 videos
        }
        top_keywords = sorted(keyword_avg_scores.items(), key=lambda x: x[1], reverse=True)[:15]

        # Determine best length category
        # Group by length: short (<40), medium (40-70), long (>70)
        length_groups = {"short": [], "medium": [], "long": []}
        for video, score in video_scores:
            title_len = len(video.title)
            if title_len < 40:
                length_groups["short"].append(score)
            elif title_len <= 70:
                length_groups["medium"].append(score)
            else:
                length_groups["long"].append(score)

        # Calculate average score for each group
        length_avg_scores = {
            group: (sum(scores) / len(scores) if scores else 0)
            for group, scores in length_groups.items()
        }
        length_correlation = max(length_avg_scores.items(), key=lambda x: x[1])[0]

        return TitlePattern(
            avg_length=avg_length,
            avg_word_count=avg_word_count,
            common_words=common_words,
            top_keywords=top_keywords,
            length_correlation=length_correlation
        )

    def generate_insights(self, channel_name: str) -> TitleTagInsights:
        """Generate comprehensive insights from title and tag analysis"""
        title_pattern = self.analyze_title_patterns()

        # Extract top keywords as suggestions
        suggested_keywords = [kw for kw, _ in title_pattern.top_keywords[:10]]

        # For tags, we would need tag data from YouTube API
        # Since we don't have it readily available, we'll use an empty list
        top_tags: List[TagAnalysis] = []
        suggested_tags: List[str] = []

        return TitleTagInsights(
            channel_name=channel_name,
            analyzed_video_count=len(self.videos),
            title_pattern=title_pattern,
            top_tags=top_tags,
            suggested_tags=suggested_tags,
            suggested_keywords=suggested_keywords
        )
