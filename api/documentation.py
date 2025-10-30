"""Automatic API documentation generator."""

import json
from typing import Any, Dict, List, Optional
from datetime import datetime


class APIEndpointDoc:
    """Documentation for a single API endpoint."""

    def __init__(
        self,
        path: str,
        methods: List[str],
        name: Optional[str] = None,
        description: Optional[str] = None,
        parameters: Optional[List[Dict[str, Any]]] = None,
        request_body: Optional[Dict[str, Any]] = None,
        responses: Optional[Dict[int, Dict[str, Any]]] = None,
        authentication: Optional[str] = None,
        permissions: Optional[List[str]] = None,
    ) -> None:
        """Initialize endpoint documentation.

        Args:
            path: Endpoint URL path
            methods: Allowed HTTP methods
            name: Endpoint name
            description: Endpoint description
            parameters: List of parameter definitions
            request_body: Request body schema
            responses: Response schemas by status code
            authentication: Authentication method required
            permissions: Required permissions
        """
        self.path = path
        self.methods = methods
        self.name = name or path
        self.description = description or ""
        self.parameters = parameters or []
        self.request_body = request_body
        self.responses = responses or {}
        self.authentication = authentication
        self.permissions = permissions or []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "path": self.path,
            "methods": self.methods,
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
            "request_body": self.request_body,
            "responses": self.responses,
            "authentication": self.authentication,
            "permissions": self.permissions,
        }


class APIDocGenerator:
    """Generator for API documentation."""

    def __init__(
        self,
        title: str = "API Documentation",
        version: str = "1.0.0",
        description: str = "",
        base_url: str = "",
    ) -> None:
        """Initialize documentation generator.

        Args:
            title: API title
            version: API version
            description: API description
            base_url: Base URL for API
        """
        self.title = title
        self.version = version
        self.description = description
        self.base_url = base_url
        self.endpoints: List[APIEndpointDoc] = []

    def add_endpoint(
        self,
        path: str,
        methods: List[str],
        name: Optional[str] = None,
        description: Optional[str] = None,
        parameters: Optional[List[Dict[str, Any]]] = None,
        request_body: Optional[Dict[str, Any]] = None,
        responses: Optional[Dict[int, Dict[str, Any]]] = None,
        authentication: Optional[str] = None,
        permissions: Optional[List[str]] = None,
    ) -> APIEndpointDoc:
        """Add an endpoint to documentation.

        Args:
            path: Endpoint path
            methods: HTTP methods
            name: Endpoint name
            description: Description
            parameters: Parameters
            request_body: Request body schema
            responses: Response schemas
            authentication: Authentication method
            permissions: Required permissions

        Returns:
            Created APIEndpointDoc
        """
        endpoint = APIEndpointDoc(
            path=path,
            methods=methods,
            name=name,
            description=description,
            parameters=parameters,
            request_body=request_body,
            responses=responses,
            authentication=authentication,
            permissions=permissions,
        )
        self.endpoints.append(endpoint)
        return endpoint

    def generate_openapi(self) -> Dict[str, Any]:
        """Generate OpenAPI 3.0 specification.

        Returns:
            OpenAPI specification dictionary
        """
        paths: Dict[str, Any] = {}

        for endpoint in self.endpoints:
            if endpoint.path not in paths:
                paths[endpoint.path] = {}

            for method in endpoint.methods:
                method_lower = method.lower()
                operation = {
                    "summary": endpoint.name,
                    "description": endpoint.description,
                    "operationId": f"{method_lower}_{endpoint.path.replace('/', '_')}",
                }

                # Add parameters
                if endpoint.parameters:
                    operation["parameters"] = endpoint.parameters

                # Add request body
                if endpoint.request_body and method_lower in ["post", "put", "patch"]:
                    operation["requestBody"] = {
                        "required": True,
                        "content": {"application/json": {"schema": endpoint.request_body}},
                    }

                # Add responses
                responses_dict: Dict[str, Any] = {}
                if endpoint.responses:
                    for status_code, response_schema in endpoint.responses.items():
                        responses_dict[str(status_code)] = {
                            "description": response_schema.get(
                                "description", f"Response {status_code}"
                            ),
                            "content": {
                                "application/json": {"schema": response_schema.get("schema", {})}
                            },
                        }
                    operation["responses"] = responses_dict
                else:
                    operation["responses"] = {"200": {"description": "Successful response"}}

                # Add security
                if endpoint.authentication:
                    operation["security"] = [{endpoint.authentication: []}]

                paths[endpoint.path][method_lower] = operation

        spec = {
            "openapi": "3.0.0",
            "info": {
                "title": self.title,
                "version": self.version,
                "description": self.description,
            },
            "servers": [{"url": self.base_url}] if self.base_url else [],
            "paths": paths,
            "components": {
                "securitySchemes": {
                    "ApiKeyAuth": {
                        "type": "apiKey",
                        "in": "header",
                        "name": "X-API-Key",
                    },
                    "BearerAuth": {
                        "type": "http",
                        "scheme": "bearer",
                        "bearerFormat": "JWT",
                    },
                }
            },
        }

        return spec

    def generate_markdown(self) -> str:
        """Generate Markdown documentation.

        Returns:
            Markdown formatted documentation
        """
        md_lines = [
            f"# {self.title}",
            "",
            f"Version: {self.version}",
            "",
            self.description,
            "",
            "## Endpoints",
            "",
        ]

        # Group endpoints by path
        for endpoint in self.endpoints:
            md_lines.append(f"### {endpoint.name}")
            md_lines.append("")
            md_lines.append(f"**Path:** `{endpoint.path}`")
            md_lines.append("")
            md_lines.append(f"**Methods:** {', '.join(endpoint.methods)}")
            md_lines.append("")

            if endpoint.description:
                md_lines.append(endpoint.description)
                md_lines.append("")

            if endpoint.authentication:
                md_lines.append(f"**Authentication:** {endpoint.authentication}")
                md_lines.append("")

            if endpoint.permissions:
                md_lines.append(f"**Permissions:** {', '.join(endpoint.permissions)}")
                md_lines.append("")

            if endpoint.parameters:
                md_lines.append("**Parameters:**")
                md_lines.append("")
                for param in endpoint.parameters:
                    param_name = param.get("name", "")
                    param_type = param.get("type", "")
                    param_required = "(required)" if param.get("required") else "(optional)"
                    param_desc = param.get("description", "")
                    md_lines.append(f"- `{param_name}` {param_type} {param_required}: {param_desc}")
                md_lines.append("")

            if endpoint.request_body:
                md_lines.append("**Request Body:**")
                md_lines.append("")
                md_lines.append("```json")
                md_lines.append(json.dumps(endpoint.request_body, indent=2))
                md_lines.append("```")
                md_lines.append("")

            if endpoint.responses:
                md_lines.append("**Responses:**")
                md_lines.append("")
                for status, response in endpoint.responses.items():
                    md_lines.append(f"- **{status}**: {response.get('description', '')}")
                md_lines.append("")

            md_lines.append("---")
            md_lines.append("")

        return "\n".join(md_lines)

    def generate_html(self) -> str:
        """Generate HTML documentation.

        Returns:
            HTML formatted documentation
        """
        html_parts = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            f"    <title>{self.title}</title>",
            "    <style>",
            "        body { font-family: Arial, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; }",  # noqa: E501
            "        h1 { color: #333; }",
            "        h2 { color: #555; border-bottom: 2px solid #ddd; padding-bottom: 10px; }",
            "        h3 { color: #666; }",
            "        .endpoint { margin-bottom: 30px; padding: 15px; background: #f9f9f9; border-left: 4px solid #007bff; }",  # noqa: E501
            "        .method { display: inline-block; padding: 5px 10px; margin: 5px; background: #007bff; color: white; border-radius: 3px; }",  # noqa: E501
            "        .path { font-family: monospace; background: #e9ecef; padding: 5px; }",
            "        pre { background: #f4f4f4; padding: 10px; overflow-x: auto; }",
            "        .param { margin: 5px 0; }",
            "    </style>",
            "</head>",
            "<body>",
            f"    <h1>{self.title}</h1>",
            f"    <p>Version: {self.version}</p>",
            f"    <p>{self.description}</p>",
            "    <h2>Endpoints</h2>",
        ]

        for endpoint in self.endpoints:
            html_parts.append('    <div class="endpoint">')
            html_parts.append(f"        <h3>{endpoint.name}</h3>")
            html_parts.append(f'        <div class="path">{endpoint.path}</div>')
            html_parts.append("        <div>")
            for method in endpoint.methods:
                html_parts.append(f'            <span class="method">{method}</span>')
            html_parts.append("        </div>")

            if endpoint.description:
                html_parts.append(f"        <p>{endpoint.description}</p>")

            if endpoint.authentication:
                html_parts.append(
                    f"        <p><strong>Authentication:</strong> {endpoint.authentication}</p>"
                )

            if endpoint.parameters:
                html_parts.append("        <p><strong>Parameters:</strong></p>")
                html_parts.append("        <ul>")
                for param in endpoint.parameters:
                    html_parts.append(
                        f'            <li class="param">{param.get("name")} ({param.get("type")}) - {param.get("description", "")}</li>'  # noqa: E501
                    )
                html_parts.append("        </ul>")

            html_parts.append("    </div>")

        html_parts.extend(["</body>", "</html>"])

        return "\n".join(html_parts)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "title": self.title,
            "version": self.version,
            "description": self.description,
            "base_url": self.base_url,
            "endpoints": [endpoint.to_dict() for endpoint in self.endpoints],
            "generated_at": datetime.utcnow().isoformat(),
        }

    def to_json(self) -> str:
        """Convert to JSON string.

        Returns:
            JSON representation
        """
        return json.dumps(self.to_dict(), indent=2)
