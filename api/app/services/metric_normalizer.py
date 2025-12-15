"""
MPIS Dashboard API - Metric Normalization Service

Service for normalizing metrics across different social media channels.
"""
from typing import Dict, Any, Optional


class MetricNormalizer:
    """Normalizes channel-specific metrics to standard schema."""
    
    @staticmethod
    def normalize_metrics(channel: str, raw_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize channel-specific metrics to standard schema.
        
        Args:
            channel: Channel name (telegram, instagram, tiktok, youtube)
            raw_metrics: Raw metrics from channel API
        
        Returns:
            Normalized metrics dictionary with standard keys
        """
        normalizer_map = {
            "telegram": MetricNormalizer._normalize_telegram,
            "instagram": MetricNormalizer._normalize_instagram,
            "tiktok": MetricNormalizer._normalize_tiktok,
            "youtube": MetricNormalizer._normalize_youtube,
        }
        
        normalizer = normalizer_map.get(channel.lower())
        if not normalizer:
            # For unknown channels, return as-is with minimal normalization
            return {
                "views": raw_metrics.get("views"),
                "reactions": raw_metrics.get("reactions") or raw_metrics.get("likes"),
                "comments": raw_metrics.get("comments"),
                "shares": raw_metrics.get("shares"),
            }
        
        normalized = normalizer(raw_metrics)
        
        # Calculate engagement rate
        engagement_rate = MetricNormalizer.calculate_engagement_rate(normalized)
        if engagement_rate is not None:
            normalized["engagement_rate"] = engagement_rate
        
        return normalized
    
    @staticmethod
    def _normalize_telegram(raw: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize Telegram metrics."""
        reactions_count = 0
        if isinstance(raw.get("reactions"), dict):
            # Sum all reaction emojis
            reactions_count = sum(raw["reactions"].values())
        elif isinstance(raw.get("reactions"), int):
            reactions_count = raw["reactions"]
        
        return {
            "views": raw.get("views"),
            "reactions": reactions_count,
            "shares": raw.get("forwards"),  # Telegram calls it "forwards"
            "comments": raw.get("comments"),
        }
    
    @staticmethod
    def _normalize_instagram(raw: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize Instagram metrics."""
        return {
            "impressions": raw.get("impressions"),
            "reach": raw.get("reach"),
            "reactions": raw.get("likes"),  # Map likes to reactions
            "comments": raw.get("comments"),
            "shares": raw.get("shares"),
            "saves": raw.get("saves"),
        }
    
    @staticmethod
    def _normalize_tiktok(raw: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize TikTok metrics."""
        return {
            "views": raw.get("views"),
            "reactions": raw.get("likes"),  # Map likes to reactions
            "comments": raw.get("comments"),
            "shares": raw.get("shares"),
        }
    
    @staticmethod
    def _normalize_youtube(raw: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize YouTube metrics."""
        return {
            "views": raw.get("views"),
            "reactions": raw.get("likes"),  # Map likes to reactions
            "comments": raw.get("comments"),
            "shares": raw.get("shares"),
        }
    
    @staticmethod
    def calculate_engagement_rate(normalized_metrics: Dict[str, Any]) -> Optional[float]:
        """
        Calculate engagement rate from normalized metrics.
        
        Formula: (reactions + comments + shares) / max(reach, views)
        Returns None if no denominator (reach or views) is available.
        
        Args:
            normalized_metrics: Normalized metrics dictionary
        
        Returns:
            Engagement rate (0.0 to 1.0) or None if cannot calculate
        """
        reactions = normalized_metrics.get("reactions") or 0
        comments = normalized_metrics.get("comments") or 0
        shares = normalized_metrics.get("shares") or 0
        
        total_engagement = reactions + comments + shares
        
        # Use reach if available, otherwise use views
        denominator = normalized_metrics.get("reach") or normalized_metrics.get("views") or 0
        
        if denominator <= 0:
            return None
        
        engagement_rate = total_engagement / denominator
        return round(engagement_rate, 4)
