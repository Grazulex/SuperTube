"""Sentiment analysis for YouTube comments using TextBlob"""

from typing import List
from textblob import TextBlob

from .models import Comment


class SentimentAnalyzer:
    """Analyzer for determining sentiment of text comments"""

    @staticmethod
    def analyze_comment(comment: Comment) -> Comment:
        """
        Analyze sentiment of a single comment and update its sentiment fields

        Args:
            comment: Comment object to analyze

        Returns:
            Comment object with updated sentiment_score and sentiment_label
        """
        try:
            # Use TextBlob for sentiment analysis
            blob = TextBlob(comment.text)
            polarity = blob.sentiment.polarity  # Range: -1.0 (negative) to 1.0 (positive)

            # Determine sentiment label based on polarity
            if polarity > 0.1:
                label = "positive"
            elif polarity < -0.1:
                label = "negative"
            else:
                label = "neutral"

            # Update comment with sentiment data
            comment.sentiment_score = polarity
            comment.sentiment_label = label

        except Exception:
            # If analysis fails, mark as neutral
            comment.sentiment_score = 0.0
            comment.sentiment_label = "neutral"

        return comment

    @staticmethod
    def analyze_comments(comments: List[Comment]) -> List[Comment]:
        """
        Analyze sentiment for multiple comments

        Args:
            comments: List of Comment objects to analyze

        Returns:
            List of Comment objects with updated sentiment data
        """
        return [SentimentAnalyzer.analyze_comment(comment) for comment in comments]

    @staticmethod
    def get_sentiment_summary(comments: List[Comment]) -> dict:
        """
        Get summary statistics for a list of comments

        Args:
            comments: List of Comment objects with sentiment data

        Returns:
            Dictionary with sentiment statistics
        """
        if not comments:
            return {
                'total': 0,
                'positive': 0,
                'neutral': 0,
                'negative': 0,
                'avg_score': 0.0
            }

        # Filter comments that have been analyzed
        analyzed = [c for c in comments if c.sentiment_score is not None]

        if not analyzed:
            return {
                'total': len(comments),
                'positive': 0,
                'neutral': 0,
                'negative': 0,
                'avg_score': 0.0
            }

        positive_count = sum(1 for c in analyzed if c.sentiment_label == 'positive')
        neutral_count = sum(1 for c in analyzed if c.sentiment_label == 'neutral')
        negative_count = sum(1 for c in analyzed if c.sentiment_label == 'negative')
        avg_score = sum(c.sentiment_score for c in analyzed) / len(analyzed)

        return {
            'total': len(analyzed),
            'positive': positive_count,
            'neutral': neutral_count,
            'negative': negative_count,
            'avg_score': avg_score,
            'positive_percent': (positive_count / len(analyzed)) * 100,
            'neutral_percent': (neutral_count / len(analyzed)) * 100,
            'negative_percent': (negative_count / len(analyzed)) * 100
        }
