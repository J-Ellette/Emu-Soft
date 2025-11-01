"""
Developed by PowerShield, as an alternative to Django SEO
"""

"""URL optimization utilities for SEO-friendly URLs."""

import re
from typing import Optional
from urllib.parse import quote, unquote


class URLOptimizer:
    """Optimize URLs for SEO.

    This class provides utilities for creating clean, SEO-friendly URLs
    by slugifying text, handling special characters, and managing redirects.
    """

    def __init__(self, max_length: int = 100) -> None:
        """Initialize the URL optimizer.

        Args:
            max_length: Maximum URL slug length (default: 100)
        """
        self.max_length = max_length

    def slugify(
        self,
        text: str,
        separator: str = "-",
        lowercase: bool = True,
        max_length: Optional[int] = None,
    ) -> str:
        """Convert text to a URL-safe slug.

        Args:
            text: Text to convert to slug
            separator: Character to use as separator (default: "-")
            lowercase: Convert to lowercase (default: True)
            max_length: Maximum length (default: from initialization)

        Returns:
            URL-safe slug

        Examples:
            >>> optimizer = URLOptimizer()
            >>> optimizer.slugify("Hello World!")
            'hello-world'
            >>> optimizer.slugify("My Article Title", separator="_")
            'my_article_title'
        """
        if not text:
            return ""

        # Convert to lowercase if requested
        if lowercase:
            text = text.lower()

        # Remove non-alphanumeric characters except spaces and hyphens
        text = re.sub(r"[^\w\s-]", "", text)

        # Replace spaces with separator
        text = re.sub(r"[\s_]+", separator, text)

        # Remove multiple separators
        text = re.sub(f"{re.escape(separator)}+", separator, text)

        # Trim separators from ends
        text = text.strip(separator)

        # Limit length
        length = max_length or self.max_length
        if len(text) > length:
            text = text[:length].rstrip(separator)

        return text

    def generate_unique_slug(
        self,
        text: str,
        existing_slugs: list[str],
        separator: str = "-",
    ) -> str:
        """Generate a unique slug by appending a number if needed.

        Args:
            text: Text to convert to slug
            existing_slugs: List of existing slugs to check against
            separator: Character to use as separator

        Returns:
            Unique slug

        Examples:
            >>> optimizer = URLOptimizer()
            >>> optimizer.generate_unique_slug("hello", ["hello", "hello-2"])
            'hello-3'
        """
        base_slug = self.slugify(text, separator=separator)

        if base_slug not in existing_slugs:
            return base_slug

        # Try appending numbers
        counter = 2
        while True:
            new_slug = f"{base_slug}{separator}{counter}"
            if new_slug not in existing_slugs:
                return new_slug
            counter += 1

    def clean_path(self, path: str) -> str:
        """Clean a URL path by removing redundant slashes and normalizing.

        Args:
            path: URL path to clean

        Returns:
            Cleaned path

        Examples:
            >>> optimizer = URLOptimizer()
            >>> optimizer.clean_path("//blog//posts//")
            '/blog/posts'
        """
        # Remove multiple slashes
        path = re.sub(r"/+", "/", path)

        # Remove trailing slash (except for root)
        if len(path) > 1 and path.endswith("/"):
            path = path[:-1]

        # Ensure starts with slash
        if not path.startswith("/"):
            path = "/" + path

        return path

    def encode_path_segment(self, segment: str) -> str:
        """Encode a URL path segment safely.

        Args:
            segment: Path segment to encode

        Returns:
            Encoded segment

        Examples:
            >>> optimizer = URLOptimizer()
            >>> optimizer.encode_path_segment("hello world")
            'hello%20world'
        """
        return quote(segment, safe="")

    def decode_path_segment(self, segment: str) -> str:
        """Decode a URL path segment.

        Args:
            segment: Encoded path segment

        Returns:
            Decoded segment
        """
        return unquote(segment)

    def is_valid_slug(self, slug: str) -> bool:
        """Check if a slug is valid (contains only allowed characters).

        Args:
            slug: Slug to validate

        Returns:
            True if valid, False otherwise

        Examples:
            >>> optimizer = URLOptimizer()
            >>> optimizer.is_valid_slug("hello-world")
            True
            >>> optimizer.is_valid_slug("hello world!")
            False
        """
        # Slug should only contain lowercase letters, numbers, and hyphens
        pattern = r"^[a-z0-9-]+$"
        return bool(re.match(pattern, slug))

    def optimize_for_keywords(
        self,
        title: str,
        keywords: list[str],
        separator: str = "-",
    ) -> str:
        """Create an optimized slug that includes important keywords.

        Args:
            title: Page title
            keywords: List of important keywords
            separator: Character to use as separator

        Returns:
            Optimized slug

        Examples:
            >>> optimizer = URLOptimizer()
            >>> optimizer.optimize_for_keywords("My Article", ["python", "tutorial"])
            'my-article-python-tutorial'
        """
        # Start with the title
        slug = self.slugify(title, separator=separator)

        # Add keywords that aren't already in the slug
        slug_words = set(slug.split(separator))
        for keyword in keywords:
            keyword_slug = self.slugify(keyword, separator=separator)
            if keyword_slug and keyword_slug not in slug_words:
                slug = f"{slug}{separator}{keyword_slug}"

        # Ensure it's not too long
        if len(slug) > self.max_length:
            slug = slug[: self.max_length].rstrip(separator)

        return slug

    def get_breadcrumb_path(self, path: str) -> list[tuple[str, str]]:
        """Generate breadcrumb structure from a URL path.

        Args:
            path: URL path

        Returns:
            List of (name, path) tuples for breadcrumbs

        Examples:
            >>> optimizer = URLOptimizer()
            >>> optimizer.get_breadcrumb_path("/blog/2024/my-post")
            [('blog', '/blog'), ('2024', '/blog/2024'), ('my-post', '/blog/2024/my-post')]
        """
        path = self.clean_path(path)
        parts = [p for p in path.split("/") if p]

        breadcrumbs = []
        current_path = ""
        for part in parts:
            current_path += "/" + part
            breadcrumbs.append((part, current_path))

        return breadcrumbs

    def create_canonical_url(
        self,
        base_url: str,
        path: str,
        remove_query: bool = True,
    ) -> str:
        """Create a canonical URL for a page.

        Args:
            base_url: Base URL (e.g., "https://example.com")
            path: Page path
            remove_query: Remove query parameters (default: True)

        Returns:
            Canonical URL

        Examples:
            >>> optimizer = URLOptimizer()
            >>> optimizer.create_canonical_url("https://example.com", "/blog/post-1")
            'https://example.com/blog/post-1'
        """
        # Clean the base URL
        base_url = base_url.rstrip("/")

        # Clean the path
        path = self.clean_path(path)

        # Remove query string if requested
        if remove_query and "?" in path:
            path = path.split("?")[0]

        return f"{base_url}{path}"
