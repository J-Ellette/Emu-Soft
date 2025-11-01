"""
Developed by PowerShield, as an alternative to Edge Computing
"""

"""Serverless function deployment utilities for edge platforms.

This module provides utilities for deploying edge functions to various
serverless platforms with configuration management and deployment automation.
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional
from enum import Enum
import json
import os


class DeploymentPlatform(Enum):
    """Supported deployment platforms."""

    CLOUDFLARE = "cloudflare"
    AWS_LAMBDA = "aws_lambda"
    VERCEL = "vercel"
    NETLIFY = "netlify"
    GENERIC = "generic"


@dataclass
class DeploymentConfig:
    """Deployment configuration."""

    platform: DeploymentPlatform
    function_name: str
    runtime: str = "edge"
    memory: int = 128  # MB
    timeout: int = 30  # seconds
    regions: List[str] = field(default_factory=lambda: ["*"])
    environment_vars: Dict[str, str] = field(default_factory=dict)
    routes: List[str] = field(default_factory=lambda: ["/*"])
    triggers: List[str] = field(default_factory=list)
    permissions: List[str] = field(default_factory=list)
    custom_config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DeploymentResult:
    """Result of a deployment operation."""

    success: bool
    function_name: str
    platform: str
    url: Optional[str] = None
    version: Optional[str] = None
    message: Optional[str] = None
    errors: List[str] = field(default_factory=list)


class EdgeDeployment:
    """Edge function deployment manager."""

    def __init__(self, config: DeploymentConfig) -> None:
        """Initialize deployment manager.

        Args:
            config: Deployment configuration
        """
        self.config = config
        self._deployment_history: List[DeploymentResult] = []

    def prepare_deployment(self, code: str) -> Dict[str, Any]:
        """Prepare deployment package.

        Args:
            code: Function code

        Returns:
            Deployment package
        """
        package = {
            "name": self.config.function_name,
            "platform": self.config.platform.value,
            "code": code,
            "config": {
                "runtime": self.config.runtime,
                "memory": self.config.memory,
                "timeout": self.config.timeout,
                "regions": self.config.regions,
                "routes": self.config.routes,
            },
            "environment": self.config.environment_vars,
        }

        # Add platform-specific configuration
        if self.config.platform == DeploymentPlatform.CLOUDFLARE:
            package["cloudflare_config"] = self._prepare_cloudflare_config()
        elif self.config.platform == DeploymentPlatform.AWS_LAMBDA:
            package["lambda_config"] = self._prepare_lambda_config()
        elif self.config.platform == DeploymentPlatform.VERCEL:
            package["vercel_config"] = self._prepare_vercel_config()
        elif self.config.platform == DeploymentPlatform.NETLIFY:
            package["netlify_config"] = self._prepare_netlify_config()

        return package

    def generate_config_file(self) -> str:
        """Generate platform-specific configuration file.

        Returns:
            Configuration file content
        """
        if self.config.platform == DeploymentPlatform.CLOUDFLARE:
            return self._generate_wrangler_config()
        elif self.config.platform == DeploymentPlatform.AWS_LAMBDA:
            return self._generate_lambda_config()
        elif self.config.platform == DeploymentPlatform.VERCEL:
            return self._generate_vercel_config()
        elif self.config.platform == DeploymentPlatform.NETLIFY:
            return self._generate_netlify_config()
        else:
            return self._generate_generic_config()

    def deploy(self, code: str, dry_run: bool = False) -> DeploymentResult:
        """Deploy edge function.

        Args:
            code: Function code
            dry_run: If True, simulate deployment without actually deploying

        Returns:
            Deployment result
        """
        try:
            # Prepare deployment
            package = self.prepare_deployment(code)

            if dry_run:
                result = DeploymentResult(
                    success=True,
                    function_name=self.config.function_name,
                    platform=self.config.platform.value,
                    message="Dry run successful - deployment not executed",
                )
            else:
                # In a real implementation, this would call the platform's API
                result = DeploymentResult(
                    success=True,
                    function_name=self.config.function_name,
                    platform=self.config.platform.value,
                    url=self._get_function_url(),
                    version="1.0.0",
                    message="Deployment successful",
                )

            self._deployment_history.append(result)
            return result

        except Exception as e:
            result = DeploymentResult(
                success=False,
                function_name=self.config.function_name,
                platform=self.config.platform.value,
                message="Deployment failed",
                errors=[str(e)],
            )
            self._deployment_history.append(result)
            return result

    def rollback(self, version: Optional[str] = None) -> DeploymentResult:
        """Rollback to a previous version.

        Args:
            version: Optional specific version to rollback to

        Returns:
            Rollback result
        """
        # In a real implementation, this would call the platform's API
        return DeploymentResult(
            success=True,
            function_name=self.config.function_name,
            platform=self.config.platform.value,
            version=version or "previous",
            message=f"Rolled back to version {version or 'previous'}",
        )

    def get_deployment_history(self) -> List[DeploymentResult]:
        """Get deployment history.

        Returns:
            List of deployment results
        """
        return self._deployment_history

    def _prepare_cloudflare_config(self) -> Dict[str, Any]:
        """Prepare Cloudflare Worker configuration.

        Returns:
            Cloudflare configuration
        """
        return {
            "account_id": self.config.custom_config.get("account_id", ""),
            "workers_dev": True,
            "route": self.config.routes[0] if self.config.routes else "/*",
            "zone_id": self.config.custom_config.get("zone_id", ""),
        }

    def _prepare_lambda_config(self) -> Dict[str, Any]:
        """Prepare Lambda@Edge configuration.

        Returns:
            Lambda configuration
        """
        return {
            "role": self.config.custom_config.get("role_arn", ""),
            "handler": "index.handler",
            "runtime": "nodejs18.x",
            "architectures": ["x86_64"],
        }

    def _prepare_vercel_config(self) -> Dict[str, Any]:
        """Prepare Vercel Edge Function configuration.

        Returns:
            Vercel configuration
        """
        return {
            "runtime": "edge",
            "regions": self.config.regions,
            "maxDuration": self.config.timeout,
        }

    def _prepare_netlify_config(self) -> Dict[str, Any]:
        """Prepare Netlify Edge Function configuration.

        Returns:
            Netlify configuration
        """
        return {
            "path": self.config.routes,
            "cache": "manual",
        }

    def _generate_wrangler_config(self) -> str:
        """Generate wrangler.toml for Cloudflare Workers.

        Returns:
            wrangler.toml content
        """
        config = f"""
name = "{self.config.function_name}"
main = "src/index.js"
compatibility_date = "2024-01-01"

[env.production]
workers_dev = false
"""

        if self.config.routes:
            config += f'route = "{self.config.routes[0]}"\n'

        if self.config.environment_vars:
            config += "\n[vars]\n"
            for key, value in self.config.environment_vars.items():
                config += f'{key} = "{value}"\n'

        return config.strip()

    def _generate_lambda_config(self) -> str:
        """Generate Lambda@Edge configuration.

        Returns:
            Lambda configuration JSON
        """
        config = {
            "FunctionName": self.config.function_name,
            "Runtime": "nodejs18.x",
            "Role": self.config.custom_config.get("role_arn", ""),
            "Handler": "index.handler",
            "MemorySize": self.config.memory,
            "Timeout": self.config.timeout,
            "Environment": {"Variables": self.config.environment_vars},
        }

        return json.dumps(config, indent=2)

    def _generate_vercel_config(self) -> str:
        """Generate vercel.json configuration.

        Returns:
            vercel.json content
        """
        config = {
            "functions": {
                f"api/{self.config.function_name}.js": {
                    "runtime": self.config.runtime,
                    "memory": self.config.memory,
                    "maxDuration": self.config.timeout,
                }
            }
        }

        if self.config.environment_vars:
            config["env"] = self.config.environment_vars

        return json.dumps(config, indent=2)

    def _generate_netlify_config(self) -> str:
        """Generate netlify.toml configuration.

        Returns:
            netlify.toml content
        """
        config = f"""
[[edge_functions]]
function = "{self.config.function_name}"
path = "{self.config.routes[0] if self.config.routes else '/*'}"
"""

        if self.config.environment_vars:
            config += "\n[context.production.environment]\n"
            for key, value in self.config.environment_vars.items():
                config += f'{key} = "{value}"\n'

        return config.strip()

    def _generate_generic_config(self) -> str:
        """Generate generic edge function configuration.

        Returns:
            Generic configuration JSON
        """
        config = {
            "name": self.config.function_name,
            "runtime": self.config.runtime,
            "memory": self.config.memory,
            "timeout": self.config.timeout,
            "regions": self.config.regions,
            "routes": self.config.routes,
            "environment": self.config.environment_vars,
        }

        return json.dumps(config, indent=2)

    def _get_function_url(self) -> str:
        """Get function URL after deployment.

        Returns:
            Function URL
        """
        if self.config.platform == DeploymentPlatform.CLOUDFLARE:
            return f"https://{self.config.function_name}.workers.dev"
        elif self.config.platform == DeploymentPlatform.AWS_LAMBDA:
            region = self.config.regions[0] if self.config.regions else "us-east-1"
            return f"https://{self.config.function_name}.lambda-url.{region}.on.aws/"
        elif self.config.platform == DeploymentPlatform.VERCEL:
            return f"https://{self.config.function_name}.vercel.app"
        elif self.config.platform == DeploymentPlatform.NETLIFY:
            return f"https://{self.config.function_name}.netlify.app"
        else:
            return f"https://{self.config.function_name}.edge-function.example.com"

    def validate_config(self) -> List[str]:
        """Validate deployment configuration.

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        if not self.config.function_name:
            errors.append("Function name is required")

        if self.config.memory < 128 or self.config.memory > 10240:
            errors.append("Memory must be between 128 and 10240 MB")

        if self.config.timeout < 1 or self.config.timeout > 900:
            errors.append("Timeout must be between 1 and 900 seconds")

        # Platform-specific validation
        if self.config.platform == DeploymentPlatform.AWS_LAMBDA:
            if not self.config.custom_config.get("role_arn"):
                errors.append("Lambda requires role_arn in custom_config")

        if self.config.platform == DeploymentPlatform.CLOUDFLARE:
            if not self.config.custom_config.get("account_id"):
                errors.append("Cloudflare requires account_id in custom_config")

        return errors
