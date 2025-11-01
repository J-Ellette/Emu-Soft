"""
Developed by PowerShield, as an alternative to Django SEO
"""

"""Meta tag management for SEO optimization."""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field


@dataclass
class MetaTags:
    """Container for meta tags."""

    title: Optional[str] = None
    description: Optional[str] = None
    keywords: List[str] = field(default_factory=list)
    author: Optional[str] = None
    robots: Optional[str] = None
    canonical_url: Optional[str] = None
    og_tags: Dict[str, str] = field(default_factory=dict)
    twitter_tags: Dict[str, str] = field(default_factory=dict)
    custom_tags: Dict[str, str] = field(default_factory=dict)


class MetaTagManager:
    """Manage meta tags for pages and content.

    This class provides functionality for generating and managing
    HTML meta tags for SEO optimization, including Open Graph and
    Twitter Card tags.
    """

    def __init__(self) -> None:
        """Initialize the meta tag manager."""
        self._default_tags: MetaTags = MetaTags()

    def set_defaults(
        self,
        title: Optional[str] = None,
        description: Optional[str] = None,
        keywords: Optional[List[str]] = None,
        author: Optional[str] = None,
        robots: Optional[str] = None,
    ) -> None:
        """Set default meta tags.

        Args:
            title: Default page title
            description: Default description
            keywords: Default keywords list
            author: Default author name
            robots: Default robots directive
        """
        if title:
            self._default_tags.title = title
        if description:
            self._default_tags.description = description
        if keywords:
            self._default_tags.keywords = keywords
        if author:
            self._default_tags.author = author
        if robots:
            self._default_tags.robots = robots

    def create_meta_tags(
        self,
        title: Optional[str] = None,
        description: Optional[str] = None,
        keywords: Optional[List[str]] = None,
        author: Optional[str] = None,
        robots: Optional[str] = None,
        canonical_url: Optional[str] = None,
        og_tags: Optional[Dict[str, str]] = None,
        twitter_tags: Optional[Dict[str, str]] = None,
        custom_tags: Optional[Dict[str, str]] = None,
    ) -> MetaTags:
        """Create a MetaTags object with provided values or defaults.

        Args:
            title: Page title
            description: Page description
            keywords: Keywords list
            author: Author name
            robots: Robots directive (e.g., "index,follow" or "noindex,nofollow")
            canonical_url: Canonical URL for the page
            og_tags: Open Graph tags
            twitter_tags: Twitter Card tags
            custom_tags: Custom meta tags

        Returns:
            MetaTags object
        """
        return MetaTags(
            title=title or self._default_tags.title,
            description=description or self._default_tags.description,
            keywords=keywords or self._default_tags.keywords,
            author=author or self._default_tags.author,
            robots=robots or self._default_tags.robots,
            canonical_url=canonical_url,
            og_tags=og_tags or {},
            twitter_tags=twitter_tags or {},
            custom_tags=custom_tags or {},
        )

    def generate_html(self, tags: MetaTags) -> str:
        """Generate HTML meta tags from a MetaTags object.

        Args:
            tags: MetaTags object

        Returns:
            HTML string containing meta tags
        """
        html_lines: List[str] = []

        # Title
        if tags.title:
            html_lines.append(f"<title>{self._escape_html(tags.title)}</title>")

        # Standard meta tags
        if tags.description:
            html_lines.append(
                f'<meta name="description" content="{self._escape_html(tags.description)}">'
            )

        if tags.keywords:
            keywords_str = ", ".join(tags.keywords)
            html_lines.append(f'<meta name="keywords" content="{self._escape_attr(keywords_str)}">')

        if tags.author:
            html_lines.append(f'<meta name="author" content="{self._escape_attr(tags.author)}">')

        if tags.robots:
            html_lines.append(f'<meta name="robots" content="{self._escape_attr(tags.robots)}">')

        # Canonical URL
        if tags.canonical_url:
            html_lines.append(
                f'<link rel="canonical" href="{self._escape_attr(tags.canonical_url)}">'
            )

        # Open Graph tags
        for key, value in tags.og_tags.items():
            html_lines.append(f'<meta property="og:{key}" content="{self._escape_attr(value)}">')

        # Twitter Card tags
        for key, value in tags.twitter_tags.items():
            html_lines.append(f'<meta name="twitter:{key}" content="{self._escape_attr(value)}">')

        # Custom tags
        for name, content in tags.custom_tags.items():
            html_lines.append(
                f'<meta name="{self._escape_attr(name)}" content="{self._escape_attr(content)}">'
            )

        return "\n".join(html_lines)

    def create_open_graph_tags(
        self,
        title: str,
        type_: str,
        url: str,
        image: Optional[str] = None,
        description: Optional[str] = None,
        site_name: Optional[str] = None,
        locale: str = "en_US",
    ) -> Dict[str, str]:
        """Create Open Graph meta tags.

        Args:
            title: Page title
            type_: Content type (e.g., "website", "article")
            url: Page URL
            image: Image URL
            description: Page description
            site_name: Site name
            locale: Locale (default: en_US)

        Returns:
            Dictionary of Open Graph tags
        """
        og_tags = {
            "title": title,
            "type": type_,
            "url": url,
            "locale": locale,
        }

        if image:
            og_tags["image"] = image
        if description:
            og_tags["description"] = description
        if site_name:
            og_tags["site_name"] = site_name

        return og_tags

    def create_twitter_card_tags(
        self,
        card_type: str,
        title: str,
        description: Optional[str] = None,
        image: Optional[str] = None,
        site: Optional[str] = None,
        creator: Optional[str] = None,
    ) -> Dict[str, str]:
        """Create Twitter Card meta tags.

        Args:
            card_type: Card type (e.g., "summary", "summary_large_image")
            title: Card title
            description: Card description
            image: Image URL
            site: Site Twitter handle
            creator: Content creator Twitter handle

        Returns:
            Dictionary of Twitter Card tags
        """
        twitter_tags = {
            "card": card_type,
            "title": title,
        }

        if description:
            twitter_tags["description"] = description
        if image:
            twitter_tags["image"] = image
        if site:
            twitter_tags["site"] = site
        if creator:
            twitter_tags["creator"] = creator

        return twitter_tags

    def extract_from_content(self, content: Dict[str, Any]) -> MetaTags:
        """Extract meta tags from content object.

        Args:
            content: Content dictionary with meta fields

        Returns:
            MetaTags object
        """
        return self.create_meta_tags(
            title=content.get("meta_title") or content.get("title"),
            description=content.get("meta_description") or content.get("excerpt"),
            keywords=(
                content.get("meta_keywords", "").split(",") if content.get("meta_keywords") else []
            ),
            canonical_url=content.get("canonical_url"),
        )

    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters.

        Args:
            text: Text to escape

        Returns:
            Escaped text
        """
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#x27;")
        )

    def _escape_attr(self, text: str) -> str:
        """Escape attribute special characters.

        Args:
            text: Text to escape

        Returns:
            Escaped text
        """
        return text.replace('"', "&quot;").replace("'", "&#x27;")
