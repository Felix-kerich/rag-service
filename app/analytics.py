import os
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter
import statistics
from pathlib import Path


@dataclass
class QueryMetrics:
    """Metrics for a single query"""
    query_id: str
    user_id: str
    query_text: str
    response_time_ms: float
    retrieval_time_ms: float
    generation_time_ms: float
    retrieved_contexts: int
    context_relevance_scores: List[float]
    response_length: int
    timestamp: str
    endpoint: str
    success: bool
    error_message: Optional[str] = None
    user_feedback: Optional[int] = None  # 1-5 rating
    conversation_id: Optional[str] = None


@dataclass
class UserSession:
    """User session analytics"""
    user_id: str
    session_start: str
    queries_count: int
    avg_response_time: float
    total_session_time: float
    satisfaction_score: Optional[float] = None


class AnalyticsCollector:
    """Collects and analyzes RAG system performance metrics"""
    
    def __init__(self, analytics_dir: str = "data/analytics"):
        self.analytics_dir = Path(analytics_dir)
        self.analytics_dir.mkdir(parents=True, exist_ok=True)
        
        self.metrics_file = self.analytics_dir / "query_metrics.jsonl"
        self.sessions_file = self.analytics_dir / "user_sessions.jsonl"
        self.daily_stats_file = self.analytics_dir / "daily_stats.json"
        
        # In-memory cache for current session
        self.current_sessions: Dict[str, Dict] = {}
        self.query_cache: List[QueryMetrics] = []
        
    def start_query_tracking(self, query_id: str, user_id: str, query_text: str, endpoint: str) -> Dict[str, Any]:
        """Start tracking a query"""
        return {
            "query_id": query_id,
            "user_id": user_id,
            "query_text": query_text,
            "endpoint": endpoint,
            "start_time": time.time(),
            "retrieval_start": None,
            "generation_start": None
        }
    
    def mark_retrieval_start(self, tracking_data: Dict[str, Any]):
        """Mark the start of retrieval phase"""
        tracking_data["retrieval_start"] = time.time()
    
    def mark_generation_start(self, tracking_data: Dict[str, Any]):
        """Mark the start of generation phase"""
        tracking_data["generation_start"] = time.time()
    
    def complete_query_tracking(self, tracking_data: Dict[str, Any], 
                              retrieved_contexts: List[Dict], 
                              response: str, 
                              success: bool = True, 
                              error_message: Optional[str] = None,
                              conversation_id: Optional[str] = None):
        """Complete query tracking and save metrics"""
        end_time = time.time()
        start_time = tracking_data["start_time"]
        
        # Calculate timing metrics
        total_time = (end_time - start_time) * 1000  # Convert to ms
        retrieval_time = 0
        generation_time = 0
        
        if tracking_data.get("retrieval_start"):
            if tracking_data.get("generation_start"):
                retrieval_time = (tracking_data["generation_start"] - tracking_data["retrieval_start"]) * 1000
                generation_time = (end_time - tracking_data["generation_start"]) * 1000
            else:
                retrieval_time = (end_time - tracking_data["retrieval_start"]) * 1000
        
        # Calculate context relevance scores
        context_scores = [ctx.get("score", 0.0) for ctx in retrieved_contexts]
        
        # Create metrics object
        metrics = QueryMetrics(
            query_id=tracking_data["query_id"],
            user_id=tracking_data["user_id"],
            query_text=tracking_data["query_text"],
            response_time_ms=total_time,
            retrieval_time_ms=retrieval_time,
            generation_time_ms=generation_time,
            retrieved_contexts=len(retrieved_contexts),
            context_relevance_scores=context_scores,
            response_length=len(response),
            timestamp=datetime.utcnow().isoformat(),
            endpoint=tracking_data["endpoint"],
            success=success,
            error_message=error_message,
            conversation_id=conversation_id
        )
        
        # Save metrics
        self._save_query_metrics(metrics)
        self._update_user_session(tracking_data["user_id"], metrics)
        
        return metrics
    
    def record_user_feedback(self, query_id: str, rating: int):
        """Record user feedback for a query"""
        # Update the metrics file with feedback
        self._update_query_feedback(query_id, rating)
    
    def _save_query_metrics(self, metrics: QueryMetrics):
        """Save query metrics to file"""
        with open(self.metrics_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(metrics)) + "\n")
    
    def _update_user_session(self, user_id: str, metrics: QueryMetrics):
        """Update user session data"""
        if user_id not in self.current_sessions:
            self.current_sessions[user_id] = {
                "session_start": metrics.timestamp,
                "queries": [],
                "total_time": 0
            }
        
        session = self.current_sessions[user_id]
        session["queries"].append(metrics.response_time_ms)
        session["total_time"] += metrics.response_time_ms
        
        # Save session periodically
        if len(session["queries"]) % 5 == 0:
            self._save_user_session(user_id)
    
    def _save_user_session(self, user_id: str):
        """Save user session to file"""
        if user_id not in self.current_sessions:
            return
            
        session_data = self.current_sessions[user_id]
        user_session = UserSession(
            user_id=user_id,
            session_start=session_data["session_start"],
            queries_count=len(session_data["queries"]),
            avg_response_time=statistics.mean(session_data["queries"]) if session_data["queries"] else 0,
            total_session_time=session_data["total_time"]
        )
        
        with open(self.sessions_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(user_session)) + "\n")
    
    def _update_query_feedback(self, query_id: str, rating: int):
        """Update query metrics with user feedback"""
        # This is a simplified implementation
        # In production, you'd want to use a proper database
        pass
    
    def get_performance_insights(self, days: int = 7) -> Dict[str, Any]:
        """Get performance insights for the last N days"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        metrics = self._load_recent_metrics(cutoff_date)
        if not metrics:
            return {"message": "No data available for the specified period"}
        
        # Calculate insights
        total_queries = len(metrics)
        successful_queries = sum(1 for m in metrics if m.success)
        success_rate = (successful_queries / total_queries) * 100 if total_queries > 0 else 0
        
        response_times = [m.response_time_ms for m in metrics if m.success]
        avg_response_time = statistics.mean(response_times) if response_times else 0
        p95_response_time = statistics.quantiles(response_times, n=20)[18] if len(response_times) > 20 else 0
        
        # Context analysis
        context_counts = [m.retrieved_contexts for m in metrics]
        avg_contexts = statistics.mean(context_counts) if context_counts else 0
        
        # Relevance analysis
        all_scores = []
        for m in metrics:
            all_scores.extend(m.context_relevance_scores)
        avg_relevance = statistics.mean(all_scores) if all_scores else 0
        
        # Query patterns
        query_lengths = [len(m.query_text.split()) for m in metrics]
        avg_query_length = statistics.mean(query_lengths) if query_lengths else 0
        
        # Error analysis
        errors = [m.error_message for m in metrics if not m.success and m.error_message]
        error_patterns = Counter(errors)
        
        # User engagement
        unique_users = len(set(m.user_id for m in metrics))
        queries_per_user = total_queries / unique_users if unique_users > 0 else 0
        
        return {
            "period_days": days,
            "total_queries": total_queries,
            "unique_users": unique_users,
            "success_rate_percent": round(success_rate, 2),
            "performance": {
                "avg_response_time_ms": round(avg_response_time, 2),
                "p95_response_time_ms": round(p95_response_time, 2),
                "avg_contexts_retrieved": round(avg_contexts, 2),
                "avg_context_relevance": round(avg_relevance, 3)
            },
            "user_engagement": {
                "queries_per_user": round(queries_per_user, 2),
                "avg_query_length_words": round(avg_query_length, 1)
            },
            "top_errors": dict(error_patterns.most_common(5)),
            "recommendations": self._generate_recommendations(metrics)
        }
    
    def _load_recent_metrics(self, cutoff_date: datetime) -> List[QueryMetrics]:
        """Load metrics from the specified date onwards"""
        metrics = []
        
        if not self.metrics_file.exists():
            return metrics
            
        with open(self.metrics_file, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    data = json.loads(line.strip())
                    metric_date = datetime.fromisoformat(data["timestamp"])
                    if metric_date >= cutoff_date:
                        metrics.append(QueryMetrics(**data))
                except (json.JSONDecodeError, KeyError, ValueError):
                    continue
        
        return metrics
    
    def _generate_recommendations(self, metrics: List[QueryMetrics]) -> List[str]:
        """Generate performance recommendations based on metrics"""
        recommendations = []
        
        if not metrics:
            return ["Insufficient data for recommendations"]
        
        # Response time analysis
        response_times = [m.response_time_ms for m in metrics if m.success]
        if response_times:
            avg_time = statistics.mean(response_times)
            if avg_time > 3000:  # 3 seconds
                recommendations.append("Response times are high. Consider optimizing retrieval or generation models.")
            elif avg_time > 1500:  # 1.5 seconds
                recommendations.append("Response times are moderate. Monitor for further increases.")
        
        # Success rate analysis
        success_rate = (sum(1 for m in metrics if m.success) / len(metrics)) * 100
        if success_rate < 95:
            recommendations.append("Success rate is below 95%. Investigate error patterns and improve error handling.")
        
        # Context relevance analysis
        all_scores = []
        for m in metrics:
            all_scores.extend(m.context_relevance_scores)
        
        if all_scores:
            avg_relevance = statistics.mean(all_scores)
            if avg_relevance < 0.5:
                recommendations.append("Context relevance is low. Consider improving embedding model or document quality.")
            elif avg_relevance < 0.7:
                recommendations.append("Context relevance is moderate. Fine-tune retrieval parameters.")
        
        # Context count analysis
        context_counts = [m.retrieved_contexts for m in metrics]
        if context_counts:
            avg_contexts = statistics.mean(context_counts)
            if avg_contexts < 2:
                recommendations.append("Low number of contexts retrieved. Consider increasing k parameter or improving document coverage.")
        
        # User engagement analysis
        unique_users = len(set(m.user_id for m in metrics))
        queries_per_user = len(metrics) / unique_users if unique_users > 0 else 0
        if queries_per_user < 2:
            recommendations.append("Low user engagement. Consider improving response quality or user experience.")
        
        if not recommendations:
            recommendations.append("System performance looks good. Continue monitoring key metrics.")
        
        return recommendations
    
    def get_user_analytics(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """Get analytics for a specific user"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        metrics = self._load_recent_metrics(cutoff_date)
        
        user_metrics = [m for m in metrics if m.user_id == user_id]
        
        if not user_metrics:
            return {"message": f"No data found for user {user_id} in the last {days} days"}
        
        # User-specific analytics
        total_queries = len(user_metrics)
        successful_queries = sum(1 for m in user_metrics if m.success)
        success_rate = (successful_queries / total_queries) * 100
        
        response_times = [m.response_time_ms for m in user_metrics if m.success]
        avg_response_time = statistics.mean(response_times) if response_times else 0
        
        # Query patterns
        query_texts = [m.query_text for m in user_metrics]
        avg_query_length = statistics.mean([len(q.split()) for q in query_texts])
        
        # Most common query topics (simplified)
        common_words = Counter()
        for query in query_texts:
            words = [word.lower() for word in query.split() if len(word) > 3]
            common_words.update(words)
        
        return {
            "user_id": user_id,
            "period_days": days,
            "total_queries": total_queries,
            "success_rate_percent": round(success_rate, 2),
            "avg_response_time_ms": round(avg_response_time, 2),
            "avg_query_length_words": round(avg_query_length, 1),
            "top_query_topics": dict(common_words.most_common(10)),
            "recent_activity": [
                {
                    "timestamp": m.timestamp,
                    "query": m.query_text[:100] + "..." if len(m.query_text) > 100 else m.query_text,
                    "success": m.success,
                    "response_time_ms": round(m.response_time_ms, 2)
                }
                for m in sorted(user_metrics, key=lambda x: x.timestamp, reverse=True)[:10]
            ]
        }
    
    def export_analytics_report(self, days: int = 30) -> Dict[str, Any]:
        """Export comprehensive analytics report"""
        performance_insights = self.get_performance_insights(days)
        
        # Additional detailed analysis
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        metrics = self._load_recent_metrics(cutoff_date)
        
        # Endpoint analysis
        endpoint_stats = defaultdict(list)
        for m in metrics:
            endpoint_stats[m.endpoint].append(m)
        
        endpoint_performance = {}
        for endpoint, endpoint_metrics in endpoint_stats.items():
            success_rate = (sum(1 for m in endpoint_metrics if m.success) / len(endpoint_metrics)) * 100
            response_times = [m.response_time_ms for m in endpoint_metrics if m.success]
            avg_time = statistics.mean(response_times) if response_times else 0
            
            endpoint_performance[endpoint] = {
                "total_requests": len(endpoint_metrics),
                "success_rate_percent": round(success_rate, 2),
                "avg_response_time_ms": round(avg_time, 2)
            }
        
        # Time-based analysis (hourly patterns)
        hourly_patterns = defaultdict(int)
        for m in metrics:
            hour = datetime.fromisoformat(m.timestamp).hour
            hourly_patterns[hour] += 1
        
        return {
            "report_generated": datetime.utcnow().isoformat(),
            "performance_insights": performance_insights,
            "endpoint_performance": endpoint_performance,
            "hourly_usage_patterns": dict(hourly_patterns),
            "system_health": {
                "total_metrics_collected": len(metrics),
                "data_quality_score": self._calculate_data_quality_score(metrics)
            }
        }
    
    def _calculate_data_quality_score(self, metrics: List[QueryMetrics]) -> float:
        """Calculate a data quality score based on completeness and consistency"""
        if not metrics:
            return 0.0
        
        score = 0.0
        total_checks = 0
        
        for m in metrics:
            # Check for required fields
            if m.query_text and m.user_id and m.timestamp:
                score += 1
            total_checks += 1
            
            # Check for reasonable response times
            if 0 < m.response_time_ms < 30000:  # 30 seconds max
                score += 1
            total_checks += 1
            
            # Check for context relevance scores
            if m.context_relevance_scores:
                score += 1
            total_checks += 1
        
        return (score / total_checks) * 100 if total_checks > 0 else 0.0


# Global analytics instance
analytics = AnalyticsCollector()
