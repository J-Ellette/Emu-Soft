"""Analytics integration for tracking and measuring SEO performance."""

from typing import Dict, Any, Optional, List
from datetime import datetime, timezone


class AnalyticsIntegration:
    """Integrate with analytics platforms for SEO tracking.

    This class provides utilities for generating tracking codes and
    managing analytics integrations for popular platforms like
    Google Analytics, Google Tag Manager, and custom analytics.
    """

    def __init__(self) -> None:
        """Initialize analytics integration."""
        self._tracking_codes: Dict[str, str] = {}
        self._custom_events: List[Dict[str, Any]] = []

    def add_tracking_code(self, platform: str, tracking_id: str) -> None:
        """Add a tracking code for an analytics platform.

        Args:
            platform: Platform name (e.g., "google_analytics", "google_tag_manager")
            tracking_id: Tracking ID or measurement ID
        """
        self._tracking_codes[platform] = tracking_id

    def get_tracking_code(self, platform: str) -> Optional[str]:
        """Get tracking code for a platform.

        Args:
            platform: Platform name

        Returns:
            Tracking ID or None if not set
        """
        return self._tracking_codes.get(platform)

    def generate_google_analytics_script(
        self,
        measurement_id: Optional[str] = None,
    ) -> str:
        """Generate Google Analytics 4 (GA4) tracking script.

        Args:
            measurement_id: GA4 measurement ID (e.g., "G-XXXXXXXXXX")
                          If not provided, uses stored tracking code

        Returns:
            HTML script tag for GA4
        """
        tracking_id = measurement_id or self._tracking_codes.get("google_analytics", "")

        if not tracking_id:
            return ""

        return f"""<!-- Google Analytics -->
<script async src="https://www.googletagmanager.com/gtag/js?id={tracking_id}"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', '{tracking_id}');
</script>
<!-- End Google Analytics -->"""

    def generate_google_tag_manager_script(
        self,
        container_id: Optional[str] = None,
    ) -> Dict[str, str]:
        """Generate Google Tag Manager scripts.

        Args:
            container_id: GTM container ID (e.g., "GTM-XXXXXXX")
                        If not provided, uses stored tracking code

        Returns:
            Dictionary with 'head' and 'body' script tags
        """
        tracking_id = container_id or self._tracking_codes.get("google_tag_manager", "")

        if not tracking_id:
            return {"head": "", "body": ""}

        head_script = f"""<!-- Google Tag Manager -->
<script>(function(w,d,s,l,i){{w[l]=w[l]||[];w[l].push({{'gtm.start':
new Date().getTime(),event:'gtm.js'}});var f=d.getElementsByTagName(s)[0],
j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=
'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);
}})(window,document,'script','dataLayer','{tracking_id}');</script>
<!-- End Google Tag Manager -->"""

        body_script = f"""<!-- Google Tag Manager (noscript) -->
<noscript><iframe src="https://www.googletagmanager.com/ns.html?id={tracking_id}"
height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript>
<!-- End Google Tag Manager (noscript) -->"""

        return {"head": head_script, "body": body_script}

    def generate_meta_verification_tags(
        self,
        google: Optional[str] = None,
        bing: Optional[str] = None,
        yandex: Optional[str] = None,
        pinterest: Optional[str] = None,
    ) -> str:
        """Generate site verification meta tags for search engines.

        Args:
            google: Google Search Console verification code
            bing: Bing Webmaster Tools verification code
            yandex: Yandex Webmaster verification code
            pinterest: Pinterest site verification code

        Returns:
            HTML meta tags for verification
        """
        tags = []

        if google:
            tags.append(f'<meta name="google-site-verification" content="{google}">')

        if bing:
            tags.append(f'<meta name="msvalidate.01" content="{bing}">')

        if yandex:
            tags.append(f'<meta name="yandex-verification" content="{yandex}">')

        if pinterest:
            tags.append(f'<meta name="p:domain_verify" content="{pinterest}">')

        return "\n".join(tags)

    def track_page_view(
        self,
        url: str,
        title: str,
        referrer: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a page view event for tracking.

        Args:
            url: Page URL
            title: Page title
            referrer: Referrer URL
            user_id: User identifier

        Returns:
            Page view event dictionary
        """
        event = {
            "event_type": "page_view",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "url": url,
            "title": title,
        }

        if referrer:
            event["referrer"] = referrer

        if user_id:
            event["user_id"] = user_id

        self._custom_events.append(event)
        return event

    def track_search(
        self,
        query: str,
        results_count: int,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a search event for tracking.

        Args:
            query: Search query
            results_count: Number of results returned
            user_id: User identifier

        Returns:
            Search event dictionary
        """
        event = {
            "event_type": "search",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "query": query,
            "results_count": results_count,
        }

        if user_id:
            event["user_id"] = user_id

        self._custom_events.append(event)
        return event

    def track_custom_event(
        self,
        event_name: str,
        properties: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a custom event for tracking.

        Args:
            event_name: Name of the event
            properties: Event properties
            user_id: User identifier

        Returns:
            Custom event dictionary
        """
        event = {
            "event_type": "custom",
            "event_name": event_name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        if properties:
            event["properties"] = properties

        if user_id:
            event["user_id"] = user_id

        self._custom_events.append(event)
        return event

    def get_events(
        self,
        event_type: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Get tracked events.

        Args:
            event_type: Filter by event type
            limit: Maximum number of events to return

        Returns:
            List of event dictionaries
        """
        events = self._custom_events

        if event_type:
            events = [e for e in events if e.get("event_type") == event_type]

        if limit:
            events = events[-limit:]

        return events

    def clear_events(self) -> None:
        """Clear all tracked events."""
        self._custom_events.clear()

    def generate_structured_data(
        self,
        type_: str,
        properties: Dict[str, Any],
    ) -> str:
        """Generate JSON-LD structured data for rich snippets.

        Args:
            type_: Schema.org type (e.g., "Article", "Organization")
            properties: Properties for the structured data

        Returns:
            HTML script tag with JSON-LD
        """
        import json

        data = {
            "@context": "https://schema.org",
            "@type": type_,
            **properties,
        }

        json_str = json.dumps(data, indent=2)
        return f'<script type="application/ld+json">\n{json_str}\n</script>'

    def generate_article_structured_data(
        self,
        headline: str,
        author: str,
        date_published: str,
        date_modified: Optional[str] = None,
        image: Optional[str] = None,
        description: Optional[str] = None,
    ) -> str:
        """Generate structured data for an article.

        Args:
            headline: Article headline
            author: Author name
            date_published: Publication date (ISO 8601 format)
            date_modified: Last modified date (ISO 8601 format)
            image: Article image URL
            description: Article description

        Returns:
            HTML script tag with Article structured data
        """
        properties = {
            "headline": headline,
            "author": {"@type": "Person", "name": author},
            "datePublished": date_published,
        }

        if date_modified:
            properties["dateModified"] = date_modified

        if image:
            properties["image"] = image

        if description:
            properties["description"] = description

        return self.generate_structured_data("Article", properties)

    def generate_organization_structured_data(
        self,
        name: str,
        url: str,
        logo: Optional[str] = None,
        social_profiles: Optional[List[str]] = None,
    ) -> str:
        """Generate structured data for an organization.

        Args:
            name: Organization name
            url: Organization URL
            logo: Logo URL
            social_profiles: List of social media profile URLs

        Returns:
            HTML script tag with Organization structured data
        """
        properties = {
            "name": name,
            "url": url,
        }

        if logo:
            properties["logo"] = logo

        if social_profiles:
            properties["sameAs"] = social_profiles

        return self.generate_structured_data("Organization", properties)
