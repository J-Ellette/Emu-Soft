"""Edge rendering support for serverless and edge-based content delivery.

This module provides edge-compatible code generation, CDN integration for edge computing,
serverless function deployment utilities, edge caching strategies, geographic routing logic,
and Workers/Lambda function adapters.

Inspired by:
- Cloudflare Workers
- AWS Lambda@Edge
- Vercel Edge Functions
- Netlify Edge Functions
"""

from mycms.edge.renderer import EdgeRenderer, RenderConfig, RenderMode
from mycms.edge.cache import EdgeCache, CacheStrategy, GeoCache
from mycms.edge.router import GeoRouter, RoutingStrategy, EdgeLocation, RoutingRule
from mycms.edge.adapters import (
    CloudflareWorkerAdapter,
    LambdaEdgeAdapter,
    GenericEdgeAdapter,
    EdgeRequest,
    EdgeResponse,
)
from mycms.edge.deployment import EdgeDeployment, DeploymentConfig, DeploymentPlatform

__all__ = [
    "EdgeRenderer",
    "RenderConfig",
    "RenderMode",
    "EdgeCache",
    "CacheStrategy",
    "GeoCache",
    "GeoRouter",
    "RoutingStrategy",
    "EdgeLocation",
    "RoutingRule",
    "CloudflareWorkerAdapter",
    "LambdaEdgeAdapter",
    "GenericEdgeAdapter",
    "EdgeRequest",
    "EdgeResponse",
    "EdgeDeployment",
    "DeploymentConfig",
    "DeploymentPlatform",
]
