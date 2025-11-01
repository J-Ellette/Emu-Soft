"""
Developed by PowerShield, as an alternative to Edge Computing
"""

"""Adapters for various edge computing platforms (Workers, Lambda, etc.).

This module provides platform-specific adapters for deploying edge functions
to popular serverless and edge computing platforms.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional
import json


@dataclass
class EdgeRequest:
    """Normalized edge request."""

    method: str
    url: str
    headers: Dict[str, str]
    body: Optional[str] = None
    query_params: Dict[str, str] = None
    path_params: Dict[str, str] = None
    client_ip: Optional[str] = None
    region: Optional[str] = None


@dataclass
class EdgeResponse:
    """Normalized edge response."""

    status: int
    headers: Dict[str, str]
    body: str
    is_base64_encoded: bool = False


class EdgeAdapter(ABC):
    """Abstract base class for edge platform adapters."""

    @abstractmethod
    def parse_request(self, event: Any) -> EdgeRequest:
        """Parse platform-specific request into normalized format.

        Args:
            event: Platform-specific event

        Returns:
            Normalized edge request
        """
        pass

    @abstractmethod
    def format_response(self, response: EdgeResponse) -> Any:
        """Format normalized response into platform-specific format.

        Args:
            response: Normalized edge response

        Returns:
            Platform-specific response
        """
        pass

    @abstractmethod
    def create_handler(self, app_handler: Callable) -> Callable:
        """Create platform-specific handler wrapper.

        Args:
            app_handler: Application handler function

        Returns:
            Platform-specific handler
        """
        pass


class CloudflareWorkerAdapter(EdgeAdapter):
    """Adapter for Cloudflare Workers."""

    def parse_request(self, event: Any) -> EdgeRequest:
        """Parse Cloudflare Worker request.

        Args:
            event: Cloudflare Worker event

        Returns:
            Normalized edge request
        """
        # In Cloudflare Workers, event is the Request object
        request = event.get("request", {})

        return EdgeRequest(
            method=request.get("method", "GET"),
            url=request.get("url", ""),
            headers=dict(request.get("headers", {})),
            body=event.get("body"),
            client_ip=request.get("headers", {}).get("cf-connecting-ip"),
            region=request.get("cf", {}).get("colo"),  # Cloudflare datacenter
        )

    def format_response(self, response: EdgeResponse) -> Any:
        """Format response for Cloudflare Worker.

        Args:
            response: Normalized edge response

        Returns:
            Cloudflare Worker response
        """
        return {
            "status": response.status,
            "statusText": self._get_status_text(response.status),
            "headers": response.headers,
            "body": response.body,
        }

    def create_handler(self, app_handler: Callable) -> Callable:
        """Create Cloudflare Worker handler.

        Args:
            app_handler: Application handler

        Returns:
            Cloudflare Worker handler
        """

        async def worker_handler(event):
            # Parse request
            request = self.parse_request(event)

            # Call application handler
            response = await app_handler(request)

            # Format response
            return self.format_response(response)

        return worker_handler

    def generate_worker_script(self, handler_code: str) -> str:
        """Generate Cloudflare Worker script.

        Args:
            handler_code: Handler code

        Returns:
            Complete worker script
        """
        return f"""
addEventListener('fetch', event => {{
  event.respondWith(handleRequest(event))
}})

async function handleRequest(event) {{
  const request = event.request;
  
  {handler_code}
}}

// Helper to get CORS headers
function getCORSHeaders() {{
  return {{
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
  }}
}}
"""

    def _get_status_text(self, status: int) -> str:
        """Get status text for HTTP status code.

        Args:
            status: HTTP status code

        Returns:
            Status text
        """
        status_texts = {
            200: "OK",
            201: "Created",
            204: "No Content",
            301: "Moved Permanently",
            302: "Found",
            304: "Not Modified",
            400: "Bad Request",
            401: "Unauthorized",
            403: "Forbidden",
            404: "Not Found",
            500: "Internal Server Error",
            502: "Bad Gateway",
            503: "Service Unavailable",
        }
        return status_texts.get(status, "Unknown")


class LambdaEdgeAdapter(EdgeAdapter):
    """Adapter for AWS Lambda@Edge."""

    def parse_request(self, event: Any) -> EdgeRequest:
        """Parse Lambda@Edge request.

        Args:
            event: Lambda@Edge event

        Returns:
            Normalized edge request
        """
        request = event.get("Records", [{}])[0].get("cf", {}).get("request", {})

        # Parse headers
        headers = {}
        for key, values in request.get("headers", {}).items():
            if values:
                headers[key] = values[0].get("value", "")

        # Parse query string
        query_params = {}
        query_string = request.get("querystring", "")
        if query_string:
            for param in query_string.split("&"):
                if "=" in param:
                    key, value = param.split("=", 1)
                    query_params[key] = value

        return EdgeRequest(
            method=request.get("method", "GET"),
            url=request.get("uri", ""),
            headers=headers,
            body=request.get("body", {}).get("data"),
            query_params=query_params,
            client_ip=request.get("clientIp"),
        )

    def format_response(self, response: EdgeResponse) -> Any:
        """Format response for Lambda@Edge.

        Args:
            response: Normalized edge response

        Returns:
            Lambda@Edge response
        """
        # Convert headers to Lambda@Edge format
        headers = {}
        for key, value in response.headers.items():
            headers[key.lower()] = [{"key": key, "value": value}]

        return {
            "status": str(response.status),
            "statusDescription": self._get_status_description(response.status),
            "headers": headers,
            "body": response.body,
            "bodyEncoding": "base64" if response.is_base64_encoded else "text",
        }

    def create_handler(self, app_handler: Callable) -> Callable:
        """Create Lambda@Edge handler.

        Args:
            app_handler: Application handler

        Returns:
            Lambda@Edge handler
        """

        async def lambda_handler(event, context):
            # Parse request
            request = self.parse_request(event)

            # Call application handler
            response = await app_handler(request)

            # Format response
            return self.format_response(response)

        return lambda_handler

    def generate_lambda_function(self, handler_code: str) -> str:
        """Generate Lambda@Edge function code.

        Args:
            handler_code: Handler code

        Returns:
            Complete Lambda function
        """
        return f"""
exports.handler = async (event, context) => {{
    const request = event.Records[0].cf.request;
    
    {handler_code}
    
    return response;
}};
"""

    def _get_status_description(self, status: int) -> str:
        """Get status description for HTTP status code.

        Args:
            status: HTTP status code

        Returns:
            Status description
        """
        descriptions = {
            200: "OK",
            201: "Created",
            204: "No Content",
            301: "Moved Permanently",
            302: "Found",
            304: "Not Modified",
            400: "Bad Request",
            401: "Unauthorized",
            403: "Forbidden",
            404: "Not Found",
            500: "Internal Server Error",
            502: "Bad Gateway",
            503: "Service Unavailable",
        }
        return descriptions.get(status, "Unknown")


class GenericEdgeAdapter(EdgeAdapter):
    """Generic adapter for standard edge functions."""

    def parse_request(self, event: Any) -> EdgeRequest:
        """Parse generic edge request.

        Args:
            event: Generic edge event

        Returns:
            Normalized edge request
        """
        if isinstance(event, dict):
            return EdgeRequest(
                method=event.get("method", "GET"),
                url=event.get("url", ""),
                headers=event.get("headers", {}),
                body=event.get("body"),
                query_params=event.get("query", {}),
                path_params=event.get("params", {}),
                client_ip=event.get("ip"),
                region=event.get("region"),
            )

        # If event is already an EdgeRequest
        if isinstance(event, EdgeRequest):
            return event

        # Default fallback
        return EdgeRequest(
            method="GET", url="/", headers={}, body=None, query_params={}, path_params={}
        )

    def format_response(self, response: EdgeResponse) -> Any:
        """Format generic edge response.

        Args:
            response: Normalized edge response

        Returns:
            Generic edge response dict
        """
        return {
            "statusCode": response.status,
            "headers": response.headers,
            "body": response.body,
            "isBase64Encoded": response.is_base64_encoded,
        }

    def create_handler(self, app_handler: Callable) -> Callable:
        """Create generic edge handler.

        Args:
            app_handler: Application handler

        Returns:
            Generic edge handler
        """

        async def edge_handler(event):
            # Parse request
            request = self.parse_request(event)

            # Call application handler
            response = await app_handler(request)

            # Format response
            return self.format_response(response)

        return edge_handler

    def generate_edge_function(self, handler_code: str) -> str:
        """Generate generic edge function code.

        Args:
            handler_code: Handler code

        Returns:
            Complete edge function
        """
        return f"""
export default async function handler(request) {{
    {handler_code}
    
    return new Response(body, {{
        status: status,
        headers: headers
    }});
}}
"""


class VercelEdgeAdapter(GenericEdgeAdapter):
    """Adapter for Vercel Edge Functions."""

    def generate_edge_function(self, handler_code: str) -> str:
        """Generate Vercel Edge Function code.

        Args:
            handler_code: Handler code

        Returns:
            Vercel Edge Function
        """
        return f"""
import {{ NextRequest, NextResponse }} from 'next/server'

export const config = {{
  runtime: 'edge',
}}

export default async function middleware(request: NextRequest) {{
    {handler_code}
    
    return NextResponse.json(data, {{
        status: status,
        headers: headers
    }})
}}
"""


class NetlifyEdgeAdapter(GenericEdgeAdapter):
    """Adapter for Netlify Edge Functions."""

    def generate_edge_function(self, handler_code: str) -> str:
        """Generate Netlify Edge Function code.

        Args:
            handler_code: Handler code

        Returns:
            Netlify Edge Function
        """
        return f"""
export default async (request: Request, context: Context) => {{
    {handler_code}
    
    return new Response(body, {{
        status: status,
        headers: headers
    }})
}}

export const config = {{
    path: "/*"
}}
"""
