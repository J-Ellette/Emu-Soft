"""
Developed by PowerShield, as an alternative to Edge Computing
"""

"""Edge-compatible code generation and rendering for serverless environments.

This module provides edge-compatible rendering capabilities, optimized for
serverless and edge computing environments.
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional
from enum import Enum
import json
import hashlib


class RenderMode(Enum):
    """Edge rendering modes."""

    STATIC = "static"  # Pre-rendered static content
    DYNAMIC = "dynamic"  # Dynamic server-side rendering
    HYBRID = "hybrid"  # Mix of static and dynamic
    INCREMENTAL = "incremental"  # Incremental static regeneration


@dataclass
class RenderConfig:
    """Configuration for edge rendering."""

    mode: RenderMode = RenderMode.STATIC
    cache_ttl: int = 3600  # Cache TTL in seconds
    max_age: int = 300  # Browser cache max-age
    stale_while_revalidate: int = 60  # Stale-while-revalidate window
    regions: Optional[List[str]] = None  # Target edge regions
    compression: bool = True  # Enable compression (gzip/brotli)
    minify_html: bool = True  # Minify HTML output
    minify_css: bool = True  # Minify CSS
    minify_js: bool = True  # Minify JavaScript
    preload_links: bool = True  # Add preload headers
    streaming: bool = False  # Enable streaming responses
    extra_headers: Dict[str, str] = field(default_factory=dict)


class EdgeRenderer:
    """Edge-compatible renderer for serverless environments."""

    def __init__(self, config: Optional[RenderConfig] = None) -> None:
        """Initialize edge renderer.

        Args:
            config: Rendering configuration
        """
        self.config = config or RenderConfig()
        self._cache: Dict[str, Any] = {}
        self._generators: Dict[str, Callable] = {}

    def register_generator(self, name: str, generator: Callable) -> None:
        """Register a content generator function.

        Args:
            name: Generator name
            generator: Generator function
        """
        self._generators[name] = generator

    def generate_static(self, content: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Generate static HTML from content.

        Args:
            content: Content to render
            context: Optional context data

        Returns:
            Rendered HTML
        """
        context = context or {}

        # Simple template variable replacement
        rendered = content
        for key, value in context.items():
            placeholder = f"{{{{{key}}}}}"
            rendered = rendered.replace(placeholder, str(value))

        # Apply optimizations
        if self.config.minify_html:
            rendered = self._minify_html(rendered)

        return rendered

    def generate_code(
        self, template: str, data: Dict[str, Any], target: str = "generic"
    ) -> str:
        """Generate edge-compatible code for a specific platform.

        Args:
            template: Template content
            data: Data to render
            target: Target platform (cloudflare, lambda, generic)

        Returns:
            Edge-compatible code
        """
        if target == "cloudflare":
            return self._generate_cloudflare_code(template, data)
        elif target == "lambda":
            return self._generate_lambda_code(template, data)
        else:
            return self._generate_generic_code(template, data)

    def _generate_cloudflare_code(self, template: str, data: Dict[str, Any]) -> str:
        """Generate Cloudflare Worker compatible code.

        Args:
            template: Template content
            data: Data to render

        Returns:
            Cloudflare Worker code
        """
        rendered_content = self.generate_static(template, data)

        code = f"""
addEventListener('fetch', event => {{
  event.respondWith(handleRequest(event.request))
}})

async function handleRequest(request) {{
  const html = `{self._escape_js_string(rendered_content)}`;
  
  return new Response(html, {{
    status: 200,
    headers: {{
      'content-type': 'text/html;charset=UTF-8',
      'cache-control': 'public, max-age={self.config.max_age}, s-maxage={self.config.cache_ttl}',
      {self._format_extra_headers()}
    }}
  }})
}}
"""
        return code.strip()

    def _generate_lambda_code(self, template: str, data: Dict[str, Any]) -> str:
        """Generate Lambda@Edge compatible code.

        Args:
            template: Template content
            data: Data to render

        Returns:
            Lambda@Edge code
        """
        rendered_content = self.generate_static(template, data)

        code = f"""
exports.handler = async (event) => {{
    const response = {{
        status: '200',
        statusDescription: 'OK',
        headers: {{
            'content-type': [{{
                key: 'Content-Type',
                value: 'text/html; charset=utf-8'
            }}],
            'cache-control': [{{
                key: 'Cache-Control',
                value: 'public, max-age={self.config.max_age}, s-maxage={self.config.cache_ttl}'
            }}],
            {self._format_lambda_headers()}
        }},
        body: `{self._escape_js_string(rendered_content)}`
    }};
    
    return response;
}};
"""
        return code.strip()

    def _generate_generic_code(self, template: str, data: Dict[str, Any]) -> str:
        """Generate generic edge-compatible code.

        Args:
            template: Template content
            data: Data to render

        Returns:
            Generic edge function code
        """
        rendered_content = self.generate_static(template, data)

        code = f"""
export default async function handler(request) {{
    const html = `{self._escape_js_string(rendered_content)}`;
    
    return new Response(html, {{
        status: 200,
        headers: {{
            'Content-Type': 'text/html; charset=utf-8',
            'Cache-Control': 'public, max-age={self.config.max_age}, s-maxage={self.config.cache_ttl}',
            {self._format_extra_headers()}
        }}
    }});
}}
"""
        return code.strip()

    def get_cache_headers(self) -> Dict[str, str]:
        """Get cache control headers for edge response.

        Returns:
            Dictionary of cache headers
        """
        headers = {
            "Cache-Control": (
                f"public, max-age={self.config.max_age}, "
                f"s-maxage={self.config.cache_ttl}, "
                f"stale-while-revalidate={self.config.stale_while_revalidate}"
            )
        }

        if self.config.compression:
            headers["Content-Encoding"] = "gzip"

        if self.config.preload_links:
            headers["Link"] = self._generate_preload_links()

        headers.update(self.config.extra_headers)

        return headers

    def compute_etag(self, content: str) -> str:
        """Compute ETag for content.

        Args:
            content: Content to hash

        Returns:
            ETag value
        """
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        return f'"{content_hash[:16]}"'

    def _minify_html(self, html: str) -> str:
        """Minify HTML content.

        Args:
            html: HTML to minify

        Returns:
            Minified HTML
        """
        # Simple minification - remove extra whitespace
        import re

        # Remove comments
        html = re.sub(r"<!--.*?-->", "", html, flags=re.DOTALL)
        # Remove extra whitespace
        html = re.sub(r"\s+", " ", html)
        # Remove whitespace around tags
        html = re.sub(r">\s+<", "><", html)

        return html.strip()

    def _escape_js_string(self, content: str) -> str:
        """Escape string for JavaScript template literal.

        Args:
            content: Content to escape

        Returns:
            Escaped content
        """
        return content.replace("\\", "\\\\").replace("`", "\\`").replace("$", "\\$")

    def _format_extra_headers(self) -> str:
        """Format extra headers for JavaScript code.

        Returns:
            Formatted header string
        """
        if not self.config.extra_headers:
            return ""

        headers = []
        for key, value in self.config.extra_headers.items():
            headers.append(f"      '{key}': '{value}'")

        return ",\n".join(headers)

    def _format_lambda_headers(self) -> str:
        """Format extra headers for Lambda@Edge code.

        Returns:
            Formatted header string
        """
        if not self.config.extra_headers:
            return ""

        headers = []
        for key, value in self.config.extra_headers.items():
            headers.append(
                f"""            '{key}': [{{
                key: '{key}',
                value: '{value}'
            }}]"""
            )

        return ",\n".join(headers)

    def _generate_preload_links(self) -> str:
        """Generate Link header for preloading resources.

        Returns:
            Link header value
        """
        # Default preload links for common resources
        return "</static/css/main.css>; rel=preload; as=style, </static/js/main.js>; rel=preload; as=script"

    def create_edge_function(
        self, name: str, handler: Callable, platform: str = "generic"
    ) -> Dict[str, Any]:
        """Create an edge function definition.

        Args:
            name: Function name
            handler: Handler function
            platform: Target platform

        Returns:
            Edge function definition
        """
        return {
            "name": name,
            "handler": handler,
            "platform": platform,
            "config": {
                "runtime": "edge",
                "regions": self.config.regions or ["*"],
                "memory": 128,
                "timeout": 30,
            },
        }

    def render_with_cache(
        self, cache_key: str, generator: Callable, ttl: Optional[int] = None
    ) -> str:
        """Render content with caching.

        Args:
            cache_key: Cache key
            generator: Content generator function
            ttl: Optional TTL override

        Returns:
            Rendered content
        """
        # Check cache
        if cache_key in self._cache:
            return self._cache[cache_key]

        # Generate content
        content = generator()

        # Cache content
        self._cache[cache_key] = content

        return content

    def invalidate_cache(self, cache_key: Optional[str] = None) -> None:
        """Invalidate cached content.

        Args:
            cache_key: Optional specific key to invalidate, None for all
        """
        if cache_key:
            self._cache.pop(cache_key, None)
        else:
            self._cache.clear()
