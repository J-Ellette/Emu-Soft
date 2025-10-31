"""Template performance optimization system.

This module provides utilities for optimizing template rendering performance,
including caching, pre-compilation, and performance monitoring.
"""

from typing import Dict, Any, Optional, List, Tuple
import time
import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timedelta


@dataclass
class RenderMetrics:
    """Metrics for a template render operation."""

    template_name: str
    render_time: float
    cache_hit: bool
    timestamp: datetime = field(default_factory=datetime.now)
    context_size: int = 0
    output_size: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "template_name": self.template_name,
            "render_time": self.render_time,
            "cache_hit": self.cache_hit,
            "timestamp": self.timestamp.isoformat(),
            "context_size": self.context_size,
            "output_size": self.output_size,
        }


class TemplateCache:
    """Cache for compiled templates and rendered output."""

    def __init__(self, max_size: int = 1000, ttl: int = 3600) -> None:
        """Initialize the template cache.

        Args:
            max_size: Maximum number of cached items
            ttl: Time to live in seconds
        """
        self.max_size = max_size
        self.ttl = ttl
        self._cache: Dict[str, Tuple[str, datetime]] = {}
        self._access_count: Dict[str, int] = {}

    def _generate_key(self, template_name: str, context: Dict[str, Any]) -> str:
        """Generate a cache key.

        Args:
            template_name: Template name
            context: Render context

        Returns:
            Cache key string
        """
        import json

        context_str = json.dumps(context, sort_keys=True, default=str)
        return hashlib.md5(f"{template_name}:{context_str}".encode()).hexdigest()

    def get(self, template_name: str, context: Dict[str, Any]) -> Optional[str]:
        """Get cached rendered template.

        Args:
            template_name: Template name
            context: Render context

        Returns:
            Cached output or None
        """
        key = self._generate_key(template_name, context)

        if key in self._cache:
            content, timestamp = self._cache[key]
            # Check if expired
            if datetime.now() - timestamp > timedelta(seconds=self.ttl):
                del self._cache[key]
                if key in self._access_count:
                    del self._access_count[key]
                return None

            # Track access
            self._access_count[key] = self._access_count.get(key, 0) + 1
            return content

        return None

    def set(self, template_name: str, context: Dict[str, Any], output: str) -> None:
        """Cache rendered template output.

        Args:
            template_name: Template name
            context: Render context
            output: Rendered output
        """
        key = self._generate_key(template_name, context)

        # Evict if at capacity
        if len(self._cache) >= self.max_size:
            self._evict_lru()

        self._cache[key] = (output, datetime.now())
        self._access_count[key] = 1

    def _evict_lru(self) -> None:
        """Evict least recently used item."""
        if not self._cache:
            return

        # Find key with lowest access count
        lru_key = min(self._access_count, key=self._access_count.get)
        del self._cache[lru_key]
        del self._access_count[lru_key]

    def clear(self) -> None:
        """Clear the cache."""
        self._cache.clear()
        self._access_count.clear()

    def size(self) -> int:
        """Get current cache size.

        Returns:
            Number of cached items
        """
        return len(self._cache)


class TemplateOptimizer:
    """Optimizer for template performance."""

    def __init__(self) -> None:
        """Initialize the template optimizer."""
        self.cache = TemplateCache()
        self.metrics: List[RenderMetrics] = []
        self._max_metrics = 10000

    def optimize_template(self, template_str: str) -> str:
        """Optimize a template string.

        Args:
            template_str: Template to optimize

        Returns:
            Optimized template
        """
        # Remove extra whitespace
        optimized = self._remove_extra_whitespace(template_str)

        # Combine adjacent text nodes
        optimized = self._combine_text_nodes(optimized)

        return optimized

    def _remove_extra_whitespace(self, template_str: str) -> str:
        """Remove unnecessary whitespace.

        Args:
            template_str: Template string

        Returns:
            Template with reduced whitespace
        """
        import re

        # Don't remove whitespace in <pre> or <code> tags
        lines = template_str.split("\n")
        optimized_lines = []

        for line in lines:
            # Keep lines with template tags
            if "{%" in line or "{{" in line:
                optimized_lines.append(line)
            else:
                # Reduce multiple spaces to single space
                line = re.sub(r"\s+", " ", line.strip())
                if line:
                    optimized_lines.append(line)

        return "\n".join(optimized_lines)

    def _combine_text_nodes(self, template_str: str) -> str:
        """Combine adjacent text nodes.

        Args:
            template_str: Template string

        Returns:
            Template with combined text
        """
        # For now, just return as-is
        # In a real implementation, this would use AST parsing
        return template_str

    def track_render(
        self,
        template_name: str,
        render_time: float,
        cache_hit: bool,
        context: Optional[Dict[str, Any]] = None,
        output: Optional[str] = None,
    ) -> None:
        """Track a render operation.

        Args:
            template_name: Name of template
            render_time: Time taken to render
            cache_hit: Whether result came from cache
            context: Render context
            output: Rendered output
        """
        context_size = len(str(context)) if context else 0
        output_size = len(output) if output else 0

        metrics = RenderMetrics(
            template_name=template_name,
            render_time=render_time,
            cache_hit=cache_hit,
            context_size=context_size,
            output_size=output_size,
        )

        self.metrics.append(metrics)

        # Keep metrics list bounded
        if len(self.metrics) > self._max_metrics:
            self.metrics = self.metrics[-self._max_metrics :]

    def get_performance_report(self) -> Dict[str, Any]:
        """Generate a performance report.

        Returns:
            Performance report dictionary
        """
        if not self.metrics:
            return {"message": "No metrics available"}

        total_renders = len(self.metrics)
        cache_hits = sum(1 for m in self.metrics if m.cache_hit)
        cache_hit_rate = (cache_hits / total_renders * 100) if total_renders > 0 else 0

        avg_render_time = sum(m.render_time for m in self.metrics) / total_renders
        max_render_time = max(m.render_time for m in self.metrics)
        min_render_time = min(m.render_time for m in self.metrics)

        # Group by template
        template_stats: Dict[str, List[float]] = {}
        for metric in self.metrics:
            if metric.template_name not in template_stats:
                template_stats[metric.template_name] = []
            template_stats[metric.template_name].append(metric.render_time)

        slowest_templates = [
            {
                "template": name,
                "avg_time": sum(times) / len(times),
                "renders": len(times),
            }
            for name, times in template_stats.items()
        ]
        slowest_templates.sort(key=lambda x: x["avg_time"], reverse=True)

        return {
            "total_renders": total_renders,
            "cache_hit_rate": round(cache_hit_rate, 2),
            "avg_render_time": round(avg_render_time * 1000, 2),  # Convert to ms
            "max_render_time": round(max_render_time * 1000, 2),
            "min_render_time": round(min_render_time * 1000, 2),
            "slowest_templates": slowest_templates[:10],
            "cache_size": self.cache.size(),
        }

    def get_optimization_suggestions(self) -> List[Dict[str, str]]:
        """Get optimization suggestions based on metrics.

        Returns:
            List of suggestion dictionaries
        """
        suggestions = []

        if not self.metrics:
            return suggestions

        report = self.get_performance_report()

        # Check cache hit rate
        if report["cache_hit_rate"] < 50:
            suggestions.append(
                {
                    "type": "caching",
                    "message": f"Low cache hit rate ({report['cache_hit_rate']}%). "
                    "Consider increasing cache size or TTL.",
                    "severity": "high",
                }
            )

        # Check render times
        if report["avg_render_time"] > 100:  # 100ms
            suggestions.append(
                {
                    "type": "performance",
                    "message": f"High average render time ({report['avg_render_time']}ms). "
                    "Consider optimizing template complexity.",
                    "severity": "medium",
                }
            )

        # Check for slow templates
        if report["slowest_templates"]:
            slowest = report["slowest_templates"][0]
            if slowest["avg_time"] > 0.2:  # 0.2 seconds (200ms)
                suggestions.append(
                    {
                        "type": "template",
                        "message": f"Template '{slowest['template']}' is slow "
                        f"({slowest['avg_time'] * 1000:.2f}ms avg). "
                        "Consider breaking it into smaller components.",
                        "severity": "high",
                    }
                )

        return suggestions

    def clear_metrics(self) -> None:
        """Clear all metrics."""
        self.metrics.clear()


class OptimizedTemplateEngine:
    """Template engine wrapper with optimization."""

    def __init__(self, engine: Any) -> None:
        """Initialize with a template engine.

        Args:
            engine: Base template engine
        """
        self.engine = engine
        self.optimizer = TemplateOptimizer()

    def render(self, template_str: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Render a template with optimization.

        Args:
            template_str: Template string
            context: Render context

        Returns:
            Rendered output
        """
        ctx = context or {}
        template_hash = hashlib.md5(template_str.encode()).hexdigest()[:8]

        # Check cache
        cached = self.optimizer.cache.get(template_hash, ctx)
        if cached is not None:
            self.optimizer.track_render(
                template_name=template_hash,
                render_time=0.0,
                cache_hit=True,
                context=ctx,
                output=cached,
            )
            return cached

        # Render with timing
        start_time = time.time()
        output = self.engine.render(template_str, ctx)
        render_time = time.time() - start_time

        # Cache result
        self.optimizer.cache.set(template_hash, ctx, output)

        # Track metrics
        self.optimizer.track_render(
            template_name=template_hash,
            render_time=render_time,
            cache_hit=False,
            context=ctx,
            output=output,
        )

        return output

    def render_template(self, template_name: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Render a named template with optimization.

        Args:
            template_name: Template name
            context: Render context

        Returns:
            Rendered output
        """
        ctx = context or {}

        # Check cache
        cached = self.optimizer.cache.get(template_name, ctx)
        if cached is not None:
            self.optimizer.track_render(
                template_name=template_name,
                render_time=0.0,
                cache_hit=True,
                context=ctx,
                output=cached,
            )
            return cached

        # Render with timing
        start_time = time.time()
        output = self.engine.render_template(template_name, ctx)
        render_time = time.time() - start_time

        # Cache result
        self.optimizer.cache.set(template_name, ctx, output)

        # Track metrics
        self.optimizer.track_render(
            template_name=template_name,
            render_time=render_time,
            cache_hit=False,
            context=ctx,
            output=output,
        )

        return output

    def get_performance_report(self) -> Dict[str, Any]:
        """Get performance report.

        Returns:
            Performance report
        """
        return self.optimizer.get_performance_report()

    def get_optimization_suggestions(self) -> List[Dict[str, str]]:
        """Get optimization suggestions.

        Returns:
            List of suggestions
        """
        return self.optimizer.get_optimization_suggestions()
