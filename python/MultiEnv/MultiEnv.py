"""
Multi-Environment Config Validator with Drift Detection

A tool for managing and validating configuration across multiple environments
with drift detection capabilities.
"""

import json
import os
import hashlib
from typing import Dict, List, Set, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


class DriftSeverity(Enum):
    """Severity levels for configuration drift"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ConfigValue:
    """Represents a configuration value"""
    key: str
    value: Any
    environment: str
    source: str = ""
    last_modified: Optional[str] = None


@dataclass
class DriftReport:
    """Report of configuration drift"""
    severity: DriftSeverity
    key: str
    environments: List[str]
    values: Dict[str, Any]
    message: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class ValidationRule:
    """Configuration validation rule"""
    key: str
    required: bool = False
    allowed_values: Optional[List[Any]] = None
    value_type: Optional[type] = None
    pattern: Optional[str] = None
    environments: Optional[List[str]] = None


class MultiEnv:
    """
    Multi-Environment Configuration Validator with Drift Detection
    
    Manages configuration across multiple environments and detects drift.
    """
    
    def __init__(self):
        """Initialize the MultiEnv validator"""
        self.environments: Dict[str, Dict[str, Any]] = {}
        self.validation_rules: List[ValidationRule] = []
        self.drift_threshold: DriftSeverity = DriftSeverity.WARNING
        self.config_history: List[Dict[str, Any]] = []
    
    def add_environment(self, name: str, config: Dict[str, Any], source: str = "") -> None:
        """
        Add an environment configuration
        
        Args:
            name: Environment name (e.g., 'dev', 'staging', 'production')
            config: Configuration dictionary
            source: Source of the configuration (file path, URL, etc.)
        """
        if not name:
            raise ValueError("Environment name cannot be empty")
        
        self.environments[name] = {
            'config': config,
            'source': source,
            'loaded_at': datetime.utcnow().isoformat()
        }
    
    def load_from_file(self, name: str, filepath: str, format: str = 'json') -> None:
        """
        Load environment configuration from a file
        
        Args:
            name: Environment name
            filepath: Path to configuration file
            format: File format ('json', 'env')
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Configuration file not found: {filepath}")
        
        with open(filepath, 'r') as f:
            if format == 'json':
                config = json.load(f)
            elif format == 'env':
                config = self._parse_env_file(f.read())
            else:
                raise ValueError(f"Unsupported format: {format}")
        
        self.add_environment(name, config, source=filepath)
    
    def _parse_env_file(self, content: str) -> Dict[str, str]:
        """Parse .env file format"""
        config = {}
        for line in content.split('\n'):
            line = line.strip()
            if line and not line.startswith('#'):
                if '=' in line:
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip().strip('"').strip("'")
        return config
    
    def add_validation_rule(self, rule: ValidationRule) -> None:
        """
        Add a validation rule
        
        Args:
            rule: ValidationRule object
        """
        self.validation_rules.append(rule)
    
    def validate_environment(self, environment: str) -> List[str]:
        """
        Validate a single environment against rules
        
        Args:
            environment: Environment name
            
        Returns:
            List of validation error messages
        """
        if environment not in self.environments:
            return [f"Environment '{environment}' not found"]
        
        errors = []
        config = self.environments[environment]['config']
        
        for rule in self.validation_rules:
            # Check if rule applies to this environment
            if rule.environments and environment not in rule.environments:
                continue
            
            # Check if required key exists
            if rule.required and rule.key not in config:
                errors.append(f"Required key '{rule.key}' missing in {environment}")
                continue
            
            # Skip further checks if key doesn't exist
            if rule.key not in config:
                continue
            
            value = config[rule.key]
            
            # Check value type
            if rule.value_type and not isinstance(value, rule.value_type):
                errors.append(
                    f"Key '{rule.key}' in {environment} has wrong type. "
                    f"Expected {rule.value_type.__name__}, got {type(value).__name__}"
                )
            
            # Check allowed values
            if rule.allowed_values and value not in rule.allowed_values:
                errors.append(
                    f"Key '{rule.key}' in {environment} has invalid value. "
                    f"Must be one of: {rule.allowed_values}"
                )
            
            # Check pattern (for strings)
            if rule.pattern and isinstance(value, str):
                import re
                if not re.match(rule.pattern, value):
                    errors.append(
                        f"Key '{rule.key}' in {environment} doesn't match pattern: {rule.pattern}"
                    )
        
        return errors
    
    def validate_all(self) -> Dict[str, List[str]]:
        """
        Validate all environments
        
        Returns:
            Dictionary mapping environment names to lists of errors
        """
        results = {}
        for env_name in self.environments.keys():
            errors = self.validate_environment(env_name)
            if errors:
                results[env_name] = errors
        return results
    
    def detect_drift(self) -> List[DriftReport]:
        """
        Detect configuration drift across environments
        
        Returns:
            List of DriftReport objects
        """
        if len(self.environments) < 2:
            return []
        
        drift_reports = []
        
        # Collect all unique keys across environments
        all_keys: Set[str] = set()
        for env_data in self.environments.values():
            all_keys.update(env_data['config'].keys())
        
        # Check each key for drift
        for key in all_keys:
            env_values = {}
            envs_with_key = []
            envs_without_key = []
            
            for env_name, env_data in self.environments.items():
                config = env_data['config']
                if key in config:
                    env_values[env_name] = config[key]
                    envs_with_key.append(env_name)
                else:
                    envs_without_key.append(env_name)
            
            # Check if key is missing in some environments
            if envs_without_key:
                drift_reports.append(DriftReport(
                    severity=DriftSeverity.WARNING,
                    key=key,
                    environments=envs_with_key + envs_without_key,
                    values=env_values,
                    message=f"Key '{key}' missing in: {', '.join(envs_without_key)}"
                ))
            
            # Check if values differ across environments
            unique_values = set(str(v) for v in env_values.values())
            if len(unique_values) > 1:
                severity = self._determine_drift_severity(key, env_values)
                drift_reports.append(DriftReport(
                    severity=severity,
                    key=key,
                    environments=list(env_values.keys()),
                    values=env_values,
                    message=f"Value differs across environments"
                ))
        
        return drift_reports
    
    def _determine_drift_severity(self, key: str, values: Dict[str, Any]) -> DriftSeverity:
        """Determine the severity of a drift"""
        # Critical keys (security, database, etc.)
        critical_patterns = ['password', 'secret', 'api_key', 'token', 'database', 'db']
        if any(pattern in key.lower() for pattern in critical_patterns):
            return DriftSeverity.CRITICAL
        
        # Error level for important config
        error_patterns = ['url', 'endpoint', 'host', 'port']
        if any(pattern in key.lower() for pattern in error_patterns):
            return DriftSeverity.ERROR
        
        return DriftSeverity.WARNING
    
    def get_drift_summary(self) -> Dict[str, int]:
        """
        Get a summary of drift by severity
        
        Returns:
            Dictionary with counts by severity level
        """
        drifts = self.detect_drift()
        summary = {
            'critical': 0,
            'error': 0,
            'warning': 0,
            'info': 0,
            'total': len(drifts)
        }
        
        for drift in drifts:
            summary[drift.severity.value] += 1
        
        return summary
    
    def compare_environments(self, env1: str, env2: str) -> Dict[str, Any]:
        """
        Compare two specific environments
        
        Args:
            env1: First environment name
            env2: Second environment name
            
        Returns:
            Comparison report
        """
        if env1 not in self.environments:
            raise ValueError(f"Environment '{env1}' not found")
        if env2 not in self.environments:
            raise ValueError(f"Environment '{env2}' not found")
        
        config1 = self.environments[env1]['config']
        config2 = self.environments[env2]['config']
        
        all_keys = set(config1.keys()) | set(config2.keys())
        
        differences = []
        only_in_env1 = []
        only_in_env2 = []
        identical = []
        
        for key in all_keys:
            if key not in config2:
                only_in_env1.append(key)
            elif key not in config1:
                only_in_env2.append(key)
            elif config1[key] == config2[key]:
                identical.append(key)
            else:
                differences.append({
                    'key': key,
                    env1: config1[key],
                    env2: config2[key]
                })
        
        return {
            'differences': differences,
            'only_in_' + env1: only_in_env1,
            'only_in_' + env2: only_in_env2,
            'identical': identical,
            'total_keys': len(all_keys),
            'drift_count': len(differences) + len(only_in_env1) + len(only_in_env2)
        }
    
    def generate_report(self, format: str = 'text') -> str:
        """
        Generate a drift detection report
        
        Args:
            format: Output format ('text', 'json')
            
        Returns:
            Formatted report string
        """
        drifts = self.detect_drift()
        summary = self.get_drift_summary()
        
        if format == 'json':
            return json.dumps({
                'summary': summary,
                'drifts': [
                    {
                        'severity': d.severity.value,
                        'key': d.key,
                        'environments': d.environments,
                        'values': d.values,
                        'message': d.message,
                        'timestamp': d.timestamp
                    }
                    for d in drifts
                ],
                'environments': list(self.environments.keys())
            }, indent=2)
        
        # Text format
        lines = []
        lines.append("=" * 70)
        lines.append("Multi-Environment Configuration Drift Report")
        lines.append("=" * 70)
        lines.append(f"Environments: {', '.join(self.environments.keys())}")
        lines.append(f"Timestamp: {datetime.utcnow().isoformat()}")
        lines.append("")
        lines.append("Summary:")
        lines.append(f"  Total Drifts: {summary['total']}")
        lines.append(f"  Critical: {summary['critical']}")
        lines.append(f"  Error: {summary['error']}")
        lines.append(f"  Warning: {summary['warning']}")
        lines.append(f"  Info: {summary['info']}")
        lines.append("")
        
        if drifts:
            lines.append("Detected Drifts:")
            lines.append("-" * 70)
            
            for drift in sorted(drifts, key=lambda d: d.severity.value):
                lines.append(f"\n[{drift.severity.value.upper()}] {drift.key}")
                lines.append(f"  Message: {drift.message}")
                lines.append(f"  Environments: {', '.join(drift.environments)}")
                lines.append("  Values:")
                for env, val in drift.values.items():
                    lines.append(f"    {env}: {val}")
        else:
            lines.append("No drift detected - all environments are in sync!")
        
        lines.append("\n" + "=" * 70)
        
        return "\n".join(lines)
    
    def export_baseline(self, environment: str, filepath: str) -> None:
        """
        Export an environment configuration as baseline
        
        Args:
            environment: Environment to export
            filepath: Output file path
        """
        if environment not in self.environments:
            raise ValueError(f"Environment '{environment}' not found")
        
        baseline = {
            'environment': environment,
            'exported_at': datetime.utcnow().isoformat(),
            'config': self.environments[environment]['config'],
            'source': self.environments[environment].get('source', '')
        }
        
        with open(filepath, 'w') as f:
            json.dump(baseline, f, indent=2)
    
    def compute_config_hash(self, environment: str) -> str:
        """
        Compute hash of environment configuration
        
        Args:
            environment: Environment name
            
        Returns:
            SHA-256 hash of the configuration
        """
        if environment not in self.environments:
            raise ValueError(f"Environment '{environment}' not found")
        
        config = self.environments[environment]['config']
        config_str = json.dumps(config, sort_keys=True)
        return hashlib.sha256(config_str.encode()).hexdigest()
    
    def get_environment_keys(self, environment: str) -> List[str]:
        """Get all keys in an environment"""
        if environment not in self.environments:
            raise ValueError(f"Environment '{environment}' not found")
        return list(self.environments[environment]['config'].keys())
    
    def get_common_keys(self) -> List[str]:
        """Get keys that exist in all environments"""
        if not self.environments:
            return []
        
        key_sets = [set(env_data['config'].keys()) for env_data in self.environments.values()]
        return list(set.intersection(*key_sets))
    
    def get_unique_keys(self, environment: str) -> List[str]:
        """Get keys that only exist in one environment"""
        if environment not in self.environments:
            raise ValueError(f"Environment '{environment}' not found")
        
        env_keys = set(self.environments[environment]['config'].keys())
        other_keys = set()
        
        for env_name, env_data in self.environments.items():
            if env_name != environment:
                other_keys.update(env_data['config'].keys())
        
        return list(env_keys - other_keys)
