# SEO Tools

Search Engine Optimization tools for improving visibility and ranking.

## What This Emulates

**Emulates:** SEO optimization tools, Google Analytics, meta tag generators, sitemap generators
**Purpose:** Search engine visibility and optimization

## Features

- Meta tag management (SEO, Open Graph, Twitter Cards)
- XML sitemap generation
- URL optimization and slug generation
- Analytics integration (Google Analytics, Google Tag Manager)
- Schema.org structured data
- Social media integration

## Components

### Meta Tags
- **meta.py** - Meta tag management
  - SEO meta tags (title, description, keywords)
  - Open Graph tags for Facebook/LinkedIn
  - Twitter Card tags
  - Schema.org structured data (JSON-LD)
  - Canonical URLs
  - Robots meta tags
  - Custom meta tags

### Sitemap Generation
- **sitemap.py** - XML sitemap generation
  - Automatic sitemap creation
  - URL priority settings (0.0-1.0)
  - Change frequency (always, hourly, daily, weekly, monthly, yearly, never)
  - Last modification dates
  - Multi-language sitemap support
  - Sitemap index for large sites
  - Google News sitemap
  - Image and video sitemaps

### URL Optimization
- **url.py** - URL optimization
  - SEO-friendly slug generation
  - URL canonicalization
  - URL encoding/decoding
  - Duplicate URL prevention
  - Clean URL generation
  - URL structure validation

### Analytics Integration
- **analytics.py** - Analytics integration
  - Google Analytics tracking code generation
  - Google Tag Manager integration
  - Custom event tracking
  - E-commerce tracking
  - User tracking
  - Conversion tracking
  - Privacy-compliant tracking

## Usage Examples

### Meta Tag Management
```python
from seo.meta import MetaTagManager

manager = MetaTagManager()

# Add SEO meta tags
manager.add_meta("title", "My Awesome Page")
manager.add_meta("description", "This is a great page about...")
manager.add_meta("keywords", "python, seo, tools")

# Add Open Graph tags
manager.add_open_graph("og:title", "My Awesome Page")
manager.add_open_graph("og:description", "Share description")
manager.add_open_graph("og:image", "https://example.com/image.jpg")
manager.add_open_graph("og:url", "https://example.com/page")

# Add Twitter Card tags
manager.add_twitter_card("twitter:card", "summary_large_image")
manager.add_twitter_card("twitter:title", "My Awesome Page")
manager.add_twitter_card("twitter:image", "https://example.com/image.jpg")

# Generate HTML
html = manager.generate_html()
```

### Sitemap Generation
```python
from seo.sitemap import SitemapGenerator, ChangeFrequency

generator = SitemapGenerator()

# Add URLs to sitemap
generator.add_url(
    loc="https://example.com/",
    priority=1.0,
    changefreq=ChangeFrequency.DAILY
)

generator.add_url(
    loc="https://example.com/about",
    priority=0.8,
    changefreq=ChangeFrequency.WEEKLY
)

generator.add_url(
    loc="https://example.com/blog/post-1",
    priority=0.6,
    changefreq=ChangeFrequency.MONTHLY,
    lastmod="2024-01-15"
)

# Generate XML sitemap
xml = generator.generate()

# Save to file
generator.save("sitemap.xml")
```

### URL Optimization
```python
from seo.url import URLOptimizer

optimizer = URLOptimizer()

# Generate SEO-friendly slug
slug = optimizer.slugify("This is My Blog Post! #123")
# Result: "this-is-my-blog-post-123"

# Canonicalize URL
canonical = optimizer.canonicalize("https://example.com/page?utm_source=twitter")
# Result: "https://example.com/page"

# Clean URL
clean = optimizer.clean_url("https://example.com//page///subpage")
# Result: "https://example.com/page/subpage"
```

### Analytics Integration
```python
from seo.analytics import AnalyticsIntegration

analytics = AnalyticsIntegration()

# Add Google Analytics
analytics.add_tracking_code("google_analytics", "UA-12345678-1")

# Add Google Tag Manager
analytics.add_tracking_code("google_tag_manager", "GTM-XXXXXX")

# Generate tracking scripts
ga_script = analytics.generate_google_analytics_script()
gtm_script = analytics.generate_google_tag_manager_script()

# Track custom event
event = analytics.track_event("button_click", {
    "category": "engagement",
    "label": "subscribe_button"
})
```

## SEO Best Practices

### Meta Tags
- Unique titles for each page (50-60 characters)
- Compelling descriptions (150-160 characters)
- Relevant keywords (but avoid keyword stuffing)
- Canonical URLs to prevent duplicate content
- Proper Open Graph tags for social sharing
- Twitter Card tags for Twitter previews

### Sitemap
- Include all important pages
- Set appropriate priorities
- Update change frequencies accurately
- Keep lastmod dates current
- Submit to search engines
- Update regularly

### URL Structure
- Use descriptive, keyword-rich URLs
- Keep URLs short and readable
- Use hyphens (not underscores) as separators
- Avoid special characters
- Use lowercase letters
- Implement proper redirects

### Analytics
- Track important user actions
- Set up conversion goals
- Monitor user flow
- Analyze traffic sources
- Respect user privacy
- Comply with GDPR/CCPA

## Schema.org Structured Data

Supported types:
- **Article** - Blog posts, news articles
- **Product** - E-commerce products
- **Organization** - Company information
- **Person** - Author profiles
- **Event** - Events and conferences
- **Recipe** - Cooking recipes
- **Review** - Product/service reviews

## Social Media Integration

### Open Graph (Facebook/LinkedIn)
- og:title
- og:description
- og:image
- og:url
- og:type
- og:site_name

### Twitter Cards
- twitter:card (summary, summary_large_image)
- twitter:title
- twitter:description
- twitter:image
- twitter:site
- twitter:creator

## Integration

Works with:
- Web framework (framework/ module)
- Template engine (templates/ module)
- Admin interface (admin/ module)
- Frontend system (frontend/ module)

## Why This Was Created

Part of the CIV-ARCOS project to provide comprehensive SEO capabilities without external SEO tools, improving search visibility and social media integration while maintaining self-containment.
