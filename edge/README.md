# Edge Rendering Support

Comprehensive edge rendering support for serverless and edge-based content delivery, enabling faster global performance through distributed edge computing.

## Overview

This module provides complete edge rendering capabilities including:

- **Edge-Compatible Code Generation**: Generate optimized code for various edge platforms
- **CDN Integration for Edge Computing**: Seamless integration with CDN providers
- **Serverless Function Deployment Utilities**: Deploy to multiple platforms
- **Edge Caching Strategies**: Sophisticated caching with multiple strategies
- **Geographic Routing Logic**: Intelligent request routing based on location
- **Workers/Lambda Function Adapters**: Platform-specific adapters

## Inspired By

- Cloudflare Workers
- AWS Lambda@Edge
- Vercel Edge Functions
- Netlify Edge Functions

## Features

### 1. Edge Renderer

Generate edge-compatible code for various platforms with optimized rendering.

**Capabilities:**
- Static, dynamic, hybrid, and incremental rendering modes
- HTML/CSS/JS minification
- ETag generation
- Cache header management
- Platform-specific code generation (Cloudflare, Lambda, Vercel, Netlify)

### 2. Edge Cache

Sophisticated caching system optimized for edge locations.

**Strategies:**
- LRU (Least Recently Used)
- LFU (Least Frequently Used)
- TTL (Time To Live)
- Geographic-based caching
- Adaptive caching

**Features:**
- Tag-based invalidation
- Pattern-based invalidation
- Multi-region support
- Cache statistics and monitoring

### 3. Geographic Router

Intelligent routing to optimal edge locations.

**Routing Strategies:**
- Geographic proximity
- Latency-based
- Load-balanced
- Failover
- Random distribution
- Custom rule-based

### 4. Platform Adapters

Adapters for popular edge computing platforms.

**Supported Platforms:**
- Cloudflare Workers
- AWS Lambda@Edge
- Vercel Edge Functions
- Netlify Edge Functions
- Generic edge functions

### 5. Deployment Manager

Comprehensive deployment utilities.

**Features:**
- Platform-specific configuration generation
- Deployment validation
- Rollback support
- Deployment history tracking

## Installation

The edge rendering module is part of the FoundryCore CMS:

```bash
from edge import (
    EdgeRenderer,
    EdgeCache,
    GeoRouter,
    CloudflareWorkerAdapter,
    EdgeDeployment
)
```

## Quick Start

### Basic Edge Rendering

```python
from edge import EdgeRenderer, RenderConfig, RenderMode

# Initialize renderer
config = RenderConfig(
    mode=RenderMode.STATIC,
    cache_ttl=3600,
    max_age=300,
    minify_html=True
)

renderer = EdgeRenderer(config)

# Generate static HTML
template = "<h1>{{title}}</h1><p>{{content}}</p>"
context = {"title": "Welcome", "content": "Hello World"}

html = renderer.generate_static(template, context)

# Get cache headers
headers = renderer.get_cache_headers()
```

### Generate Edge Function Code

```python
from edge import EdgeRenderer

renderer = EdgeRenderer()

# Generate Cloudflare Worker
template = "<h1>Hello from Edge</h1>"
code = renderer.generate_code(template, {}, target="cloudflare")

# Generate Lambda@Edge function
code = renderer.generate_code(template, {}, target="lambda")

# Generate generic edge function
code = renderer.generate_code(template, {}, target="generic")
```

### Edge Caching

```python
from edge import EdgeCache, CacheStrategy

# Initialize cache with LRU strategy
cache = EdgeCache(
    strategy=CacheStrategy.LRU,
    max_size=1000,
    default_ttl=3600
)

# Set values
cache.set("key1", "value1", ttl=7200)
cache.set("key2", "value2", tags={"user", "profile"})

# Get values
value = cache.get("key1")

# Invalidate by tag
cache.invalidate_by_tag("user")

# Invalidate by pattern
cache.invalidate_by_pattern("user:*:profile")

# Get statistics
stats = cache.get_stats()
```

### Geographic Caching

```python
from edge import GeoCache

# Initialize geo-aware cache
cache = GeoCache(regions=["us-east", "us-west", "eu-west", "ap-southeast"])

# Set value in specific region
cache.set("key1", "value1", regions=["us-east"])

# Set value in all regions
cache.set("key2", "value2")

# Get value from specific region
value = cache.get("key1", "us-east")

# Invalidate across regions
cache.invalidate("key1", regions=["us-east", "us-west"])
```

### Geographic Routing

```python
from edge import GeoRouter, RoutingStrategy, EdgeLocation

# Initialize router
router = GeoRouter(strategy=RoutingStrategy.GEOGRAPHIC)

# Register edge locations
router.register_location(EdgeLocation(
    id="us-east-1",
    region="us-east",
    latitude=39.0,
    longitude=-77.0,
    capacity=100
))

router.register_location(EdgeLocation(
    id="eu-west-1",
    region="eu-west",
    latitude=53.0,
    longitude=-8.0,
    capacity=100
))

# Route request
request_info = {
    "latitude": 40.0,
    "longitude": -74.0
}

location = router.route_request(request_info)
print(f"Routed to: {location.id}")
```

### Custom Routing Rules

```python
from edge import GeoRouter, RoutingRule

router = GeoRouter()

# Add custom rule
rule = RoutingRule(
    condition=lambda req: req.get("country") == "UK",
    target_region="eu-west",
    priority=1
)

router.add_routing_rule(rule)

# Route with custom rule
location = router.route_request({"country": "UK"})
```

### Platform Adapters

```python
from edge import CloudflareWorkerAdapter, LambdaEdgeAdapter, EdgeRequest, EdgeResponse

# Cloudflare Worker Adapter
cf_adapter = CloudflareWorkerAdapter()

# Parse platform-specific request
event = {
    "request": {
        "method": "GET",
        "url": "https://example.com/test",
        "headers": {"user-agent": "test"}
    }
}

request = cf_adapter.parse_request(event)

# Format response
response = EdgeResponse(
    status=200,
    headers={"content-type": "text/html"},
    body="<h1>Test</h1>"
)

formatted = cf_adapter.format_response(response)

# Lambda@Edge Adapter
lambda_adapter = LambdaEdgeAdapter()

# Create handler wrapper
async def app_handler(request: EdgeRequest) -> EdgeResponse:
    return EdgeResponse(
        status=200,
        headers={"content-type": "text/html"},
        body="<h1>Hello from Lambda</h1>"
    )

handler = lambda_adapter.create_handler(app_handler)
```

### Deployment

```python
from edge import EdgeDeployment, DeploymentConfig, DeploymentPlatform

# Configure deployment
config = DeploymentConfig(
    platform=DeploymentPlatform.CLOUDFLARE,
    function_name="my-edge-function",
    runtime="edge",
    memory=128,
    timeout=30,
    regions=["*"],
    environment_vars={
        "API_KEY": "secret",
        "DEBUG": "false"
    }
)

# Initialize deployment
deployment = EdgeDeployment(config)

# Validate configuration
errors = deployment.validate_config()
if errors:
    print("Configuration errors:", errors)

# Generate config file
config_content = deployment.generate_config_file()
print(config_content)

# Deploy (dry run)
code = """
export default async function handler(request) {
    return new Response('Hello World', {
        status: 200,
        headers: { 'content-type': 'text/plain' }
    });
}
"""

result = deployment.deploy(code, dry_run=True)
print(f"Deployment result: {result.message}")

# Get deployment history
history = deployment.get_deployment_history()
```

## Complete Example: Edge-Rendered Blog

```python
from edge import (
    EdgeRenderer,
    RenderConfig,
    RenderMode,
    EdgeCache,
    CacheStrategy,
    GeoRouter,
    RoutingStrategy,
    EdgeLocation,
    CloudflareWorkerAdapter,
    EdgeDeployment,
    DeploymentConfig,
    DeploymentPlatform
)

# Step 1: Setup Edge Renderer
config = RenderConfig(
    mode=RenderMode.STATIC,
    cache_ttl=3600,
    max_age=300,
    stale_while_revalidate=60,
    minify_html=True,
    compression=True
)

renderer = EdgeRenderer(config)

# Step 2: Setup Edge Cache
cache = EdgeCache(
    strategy=CacheStrategy.ADAPTIVE,
    max_size=10000,
    default_ttl=3600
)

# Step 3: Setup Geographic Router
router = GeoRouter(strategy=RoutingStrategy.GEOGRAPHIC)

# Register edge locations
router.register_location(EdgeLocation(
    id="us-east-1",
    region="us-east",
    latitude=39.0,
    longitude=-77.0,
    capacity=1000
))

router.register_location(EdgeLocation(
    id="eu-west-1",
    region="eu-west",
    latitude=53.0,
    longitude=-8.0,
    capacity=1000
))

# Step 4: Create blog post rendering function
def render_blog_post(post_id: str, region: str = "us-east"):
    # Try cache first
    cache_key = f"post:{post_id}:{region}"
    cached = cache.get(cache_key, region)
    
    if cached:
        return cached
    
    # Render blog post
    template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>{{title}}</title>
        <meta name="description" content="{{description}}">
    </head>
    <body>
        <article>
            <h1>{{title}}</h1>
            <p>{{content}}</p>
        </article>
    </body>
    </html>
    """
    
    context = {
        "title": f"Blog Post {post_id}",
        "description": "An awesome blog post",
        "content": "This is the post content..."
    }
    
    html = renderer.generate_static(template, context)
    
    # Cache the result
    cache.set(cache_key, html, region=region, tags={"blog", f"post:{post_id}"})
    
    return html

# Step 5: Generate edge function code
template = render_blog_post("123", "us-east")
edge_code = renderer.generate_code(template, {}, target="cloudflare")

# Step 6: Deploy to Cloudflare
deployment_config = DeploymentConfig(
    platform=DeploymentPlatform.CLOUDFLARE,
    function_name="blog-edge-function",
    runtime="edge",
    regions=["*"],
    environment_vars={"BLOG_API": "https://api.example.com"}
)

deployment = EdgeDeployment(deployment_config)
result = deployment.deploy(edge_code, dry_run=True)

print(f"Deployment: {result.message}")
print(f"Function URL: {result.url}")
```

## Advanced Features

### Incremental Static Regeneration (ISR)

```python
from edge import EdgeRenderer, RenderConfig, RenderMode

config = RenderConfig(
    mode=RenderMode.INCREMENTAL,
    cache_ttl=3600,
    stale_while_revalidate=60
)

renderer = EdgeRenderer(config)

def render_with_isr(cache_key: str):
    def generator():
        # Fetch fresh data
        return "<h1>Fresh Content</h1>"
    
    # Render with cache, regenerate after TTL
    return renderer.render_with_cache(cache_key, generator)
```

### Multi-Region Deployment

```python
from edge import EdgeDeployment, DeploymentConfig, DeploymentPlatform

# Deploy to multiple regions
regions = ["us-east-1", "us-west-2", "eu-west-1", "ap-southeast-1"]

config = DeploymentConfig(
    platform=DeploymentPlatform.AWS_LAMBDA,
    function_name="global-edge-function",
    regions=regions,
    custom_config={
        "role_arn": "arn:aws:iam::123456789:role/lambda-edge-role"
    }
)

deployment = EdgeDeployment(config)
result = deployment.deploy(code)
```

### Load-Balanced Routing with Failover

```python
from edge import GeoRouter, RoutingStrategy, EdgeLocation

# Primary router with load balancing
router = GeoRouter(strategy=RoutingStrategy.LOAD_BALANCED)

# Register locations with health status
locations = [
    EdgeLocation(id="us-east-1", region="us-east", 
                 latitude=39.0, longitude=-77.0, 
                 capacity=1000, current_load=500, available=True),
    EdgeLocation(id="us-east-2", region="us-east",
                 latitude=39.5, longitude=-76.0,
                 capacity=1000, current_load=200, available=True),
    EdgeLocation(id="us-west-1", region="us-west",
                 latitude=37.0, longitude=-122.0,
                 capacity=1000, current_load=800, available=False)
]

for location in locations:
    router.register_location(location)

# Route request - will select us-east-2 (lowest load, available)
location = router.route_request({})

# Update load dynamically
router.update_load("us-east-1", 600)
router.set_availability("us-west-1", True)
```

## Configuration Reference

### RenderConfig

```python
RenderConfig(
    mode=RenderMode.STATIC,        # Rendering mode
    cache_ttl=3600,                 # Cache TTL in seconds
    max_age=300,                    # Browser cache max-age
    stale_while_revalidate=60,      # SWR window
    regions=["*"],                  # Target regions
    compression=True,               # Enable compression
    minify_html=True,               # Minify HTML
    minify_css=True,                # Minify CSS
    minify_js=True,                 # Minify JavaScript
    preload_links=True,             # Add preload headers
    streaming=False,                # Enable streaming
    extra_headers={}                # Extra headers
)
```

### DeploymentConfig

```python
DeploymentConfig(
    platform=DeploymentPlatform.CLOUDFLARE,  # Platform
    function_name="my-function",              # Function name
    runtime="edge",                           # Runtime
    memory=128,                               # Memory in MB
    timeout=30,                               # Timeout in seconds
    regions=["*"],                            # Regions
    environment_vars={},                      # Environment variables
    routes=["/*"],                            # Routes
    triggers=[],                              # Triggers
    permissions=[],                           # Permissions
    custom_config={}                          # Platform-specific config
)
```

## Best Practices

1. **Use Appropriate Cache Strategy**: Choose LRU for general content, TTL for time-sensitive data, GEO for regional content

2. **Implement Proper Cache Invalidation**: Use tags for related content, patterns for bulk invalidation

3. **Monitor Edge Performance**: Track cache hit rates, latency, and load distribution

4. **Configure TTLs Wisely**: Balance freshness and performance with appropriate TTL values

5. **Use Geographic Routing**: Route users to nearest edge location for best performance

6. **Enable Compression**: Always enable compression for text-based content

7. **Implement Failover**: Configure failover locations for high availability

8. **Test Edge Functions**: Use dry_run mode to test deployments before going live

## Performance Tips

- **Enable HTML Minification**: Reduces payload size by 20-30%
- **Use Stale-While-Revalidate**: Serve stale content while fetching fresh
- **Implement Incremental Static Regeneration**: Balance static and dynamic
- **Optimize Cache Size**: Monitor and adjust max_size based on memory
- **Use Adaptive Caching**: Let the system learn optimal caching patterns
- **Distribute Across Regions**: Deploy to multiple regions for global coverage

## Troubleshooting

### Cache Not Working

1. Check TTL configuration
2. Verify cache key uniqueness
3. Monitor cache eviction
4. Check cache size limits

### Routing Issues

1. Verify location availability
2. Check routing strategy
3. Validate custom rules
4. Monitor location load

### Deployment Failures

1. Validate configuration
2. Check platform credentials
3. Verify function code syntax
4. Review platform limits

## API Reference

See individual module documentation:
- [EdgeRenderer API](renderer.py)
- [EdgeCache API](cache.py)
- [GeoRouter API](router.py)
- [Adapters API](adapters.py)
- [Deployment API](deployment.py)

## Testing

Run tests with:

```bash
python -m pytest tests/test_edge_rendering.py -v
```

## License

MIT License - Part of FoundryCore CMS
