"""
Developed by PowerShield, as an alternative to Django SEO
"""

"""Sitemap generation for search engine optimization."""

from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
import xml.etree.ElementTree as ET


class ChangeFrequency(Enum):
    """Change frequency values for sitemap entries."""

    ALWAYS = "always"
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"
    NEVER = "never"


class SitemapEntry:
    """Represents a single URL entry in a sitemap."""

    def __init__(
        self,
        loc: str,
        lastmod: Optional[datetime] = None,
        changefreq: Optional[ChangeFrequency] = None,
        priority: Optional[float] = None,
    ) -> None:
        """Initialize a sitemap entry.

        Args:
            loc: URL of the page
            lastmod: Last modification date
            changefreq: How frequently the page changes
            priority: Priority relative to other pages (0.0 - 1.0)
        """
        self.loc = loc
        self.lastmod = lastmod
        self.changefreq = changefreq
        self.priority = priority

        if priority is not None and not (0.0 <= priority <= 1.0):
            raise ValueError("Priority must be between 0.0 and 1.0")

    def to_dict(self) -> Dict[str, Any]:
        """Convert entry to dictionary.

        Returns:
            Dictionary representation
        """
        data: Dict[str, Any] = {"loc": self.loc}

        if self.lastmod:
            data["lastmod"] = self.lastmod.strftime("%Y-%m-%d")

        if self.changefreq:
            data["changefreq"] = self.changefreq.value

        if self.priority is not None:
            data["priority"] = f"{self.priority:.1f}"

        return data


class SitemapGenerator:
    """Generate XML sitemaps for search engines.

    This class creates XML sitemaps following the sitemaps.org protocol,
    helping search engines discover and index website content.
    """

    def __init__(self, base_url: str) -> None:
        """Initialize the sitemap generator.

        Args:
            base_url: Base URL of the site (e.g., "https://example.com")
        """
        self.base_url = base_url.rstrip("/")
        self.entries: List[SitemapEntry] = []

    def add_url(
        self,
        path: str,
        lastmod: Optional[datetime] = None,
        changefreq: Optional[ChangeFrequency] = None,
        priority: Optional[float] = None,
    ) -> None:
        """Add a URL to the sitemap.

        Args:
            path: URL path (e.g., "/blog/post-1")
            lastmod: Last modification date
            changefreq: How frequently the page changes
            priority: Priority relative to other pages (0.0 - 1.0)
        """
        # Ensure path starts with /
        if not path.startswith("/"):
            path = "/" + path

        full_url = f"{self.base_url}{path}"
        entry = SitemapEntry(
            loc=full_url,
            lastmod=lastmod,
            changefreq=changefreq,
            priority=priority,
        )
        self.entries.append(entry)

    def add_content(
        self,
        content_items: List[Dict[str, Any]],
        path_field: str = "slug",
        lastmod_field: str = "updated_at",
        default_changefreq: Optional[ChangeFrequency] = None,
        default_priority: Optional[float] = None,
        path_prefix: str = "",
    ) -> int:
        """Add multiple content items to the sitemap.

        Args:
            content_items: List of content dictionaries
            path_field: Field name containing the URL path
            lastmod_field: Field name containing the last modified date
            default_changefreq: Default change frequency for all items
            default_priority: Default priority for all items
            path_prefix: Prefix to add to all paths

        Returns:
            Number of items added
        """
        count = 0
        for item in content_items:
            path = item.get(path_field)
            if not path:
                continue

            # Add prefix if provided
            if path_prefix:
                path = f"{path_prefix.rstrip('/')}/{path.lstrip('/')}"

            lastmod = item.get(lastmod_field)
            if isinstance(lastmod, str):
                try:
                    lastmod = datetime.fromisoformat(lastmod.replace("Z", "+00:00"))
                except (ValueError, AttributeError):
                    lastmod = None

            self.add_url(
                path=path,
                lastmod=lastmod,
                changefreq=default_changefreq,
                priority=default_priority,
            )
            count += 1

        return count

    def generate_xml(self, pretty: bool = True) -> str:
        """Generate XML sitemap.

        Args:
            pretty: Whether to format the XML with indentation

        Returns:
            XML string
        """
        # Create root element with namespace
        urlset = ET.Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")

        # Add each URL entry
        for entry in self.entries:
            url_elem = ET.SubElement(urlset, "url")

            # Location (required)
            loc_elem = ET.SubElement(url_elem, "loc")
            loc_elem.text = entry.loc

            # Last modified (optional)
            if entry.lastmod:
                lastmod_elem = ET.SubElement(url_elem, "lastmod")
                lastmod_elem.text = entry.lastmod.strftime("%Y-%m-%d")

            # Change frequency (optional)
            if entry.changefreq:
                changefreq_elem = ET.SubElement(url_elem, "changefreq")
                changefreq_elem.text = entry.changefreq.value

            # Priority (optional)
            if entry.priority is not None:
                priority_elem = ET.SubElement(url_elem, "priority")
                priority_elem.text = f"{entry.priority:.1f}"

        # Convert to string
        if pretty:
            self._indent_xml(urlset)

        xml_str = ET.tostring(urlset, encoding="unicode", method="xml")
        return f'<?xml version="1.0" encoding="UTF-8"?>\n{xml_str}'

    def generate_index(
        self,
        sitemap_urls: List[str],
        pretty: bool = True,
    ) -> str:
        """Generate a sitemap index for multiple sitemaps.

        Args:
            sitemap_urls: List of sitemap URLs
            pretty: Whether to format the XML with indentation

        Returns:
            XML string for sitemap index
        """
        # Create root element with namespace
        sitemapindex = ET.Element(
            "sitemapindex", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        )

        # Add each sitemap
        for sitemap_url in sitemap_urls:
            sitemap_elem = ET.SubElement(sitemapindex, "sitemap")
            loc_elem = ET.SubElement(sitemap_elem, "loc")
            loc_elem.text = sitemap_url

        # Convert to string
        if pretty:
            self._indent_xml(sitemapindex)

        xml_str = ET.tostring(sitemapindex, encoding="unicode", method="xml")
        return f'<?xml version="1.0" encoding="UTF-8"?>\n{xml_str}'

    def clear(self) -> None:
        """Clear all entries from the sitemap."""
        self.entries.clear()

    def count(self) -> int:
        """Get the number of URLs in the sitemap.

        Returns:
            Number of entries
        """
        return len(self.entries)

    def to_list(self) -> List[Dict[str, Any]]:
        """Convert all entries to a list of dictionaries.

        Returns:
            List of entry dictionaries
        """
        return [entry.to_dict() for entry in self.entries]

    def _indent_xml(self, elem: ET.Element, level: int = 0) -> None:
        """Add indentation to XML elements for pretty printing.

        Args:
            elem: XML element to indent
            level: Current indentation level
        """
        indent = "\n" + "  " * level
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = indent + "  "
            if not elem.tail or not elem.tail.strip():
                elem.tail = indent
            for child in elem:
                self._indent_xml(child, level + 1)
            if not child.tail or not child.tail.strip():
                child.tail = indent
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = indent

    def split_by_count(self, max_urls: int = 50000) -> List["SitemapGenerator"]:
        """Split the sitemap into multiple sitemaps if it exceeds the limit.

        Args:
            max_urls: Maximum URLs per sitemap (default: 50000)

        Returns:
            List of SitemapGenerator instances
        """
        if len(self.entries) <= max_urls:
            return [self]

        sitemaps = []
        for i in range(0, len(self.entries), max_urls):
            sitemap = SitemapGenerator(self.base_url)
            sitemap.entries = self.entries[i : i + max_urls]
            sitemaps.append(sitemap)

        return sitemaps
