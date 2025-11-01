# MultiEnv - Multi-Environment Config Validator

A comprehensive tool for managing and validating configuration across multiple environments with drift detection capabilities.

## Features

- **Multi-Environment Support**: Manage configurations for dev, staging, production, and custom environments
- **Drift Detection**: Automatically detect configuration differences across environments
- **Validation Rules**: Define and enforce configuration validation rules
- **File Format Support**: Load from JSON and .env files
- **Severity Levels**: Automatic severity classification (INFO, WARNING, ERROR, CRITICAL)
- **Comparison Tools**: Compare configurations between specific environments
- **Configuration Hashing**: Track configuration changes with SHA-256 hashes
- **Baseline Export**: Export environment configurations as baselines
- **Detailed Reports**: Generate text and JSON format reports

## What It Does

MultiEnv helps teams manage configuration across multiple environments by:

1. **Loading Configurations**: Import from files or add programmatically
2. **Validating Rules**: Check required keys, types, patterns, and allowed values
3. **Detecting Drift**: Identify configuration differences across environments
4. **Severity Classification**: Automatically classify drift severity based on key patterns
5. **Generating Reports**: Create detailed reports of configuration drift

## Usage

### Basic Setup

```python
from MultiEnv import MultiEnv, ValidationRule, DriftSeverity

# Create validator
validator = MultiEnv()

# Add environments
validator.add_environment('dev', {
    'database': 'localhost',
    'port': 5432,
    'debug': True,
    'api_key': 'dev-key-123'
})

validator.add_environment('production', {
    'database': 'prod-server',
    'port': 5432,
    'debug': False,
    'api_key': 'prod-key-456'
})
```

### Loading from Files

```python
# Load from JSON file
validator.load_from_file('staging', 'config/staging.json', format='json')

# Load from .env file
validator.load_from_file('dev', '.env.development', format='env')
```

### Validation Rules

```python
# Add validation rules
validator.add_validation_rule(ValidationRule(
    key='database',
    required=True,
    value_type=str
))

validator.add_validation_rule(ValidationRule(
    key='port',
    required=True,
    value_type=int
))

validator.add_validation_rule(ValidationRule(
    key='environment',
    allowed_values=['dev', 'staging', 'production']
))

validator.add_validation_rule(ValidationRule(
    key='email',
    pattern=r'^[\w\.-]+@[\w\.-]+\.\w+$'
))

# Environment-specific rules
validator.add_validation_rule(ValidationRule(
    key='ssl_enabled',
    required=True,
    environments=['production']
))

# Validate all environments
errors = validator.validate_all()
for env, error_list in errors.items():
    print(f"{env}: {error_list}")
```

### Drift Detection

```python
# Detect drift across all environments
drifts = validator.detect_drift()

for drift in drifts:
    print(f"[{drift.severity.value.upper()}] {drift.key}")
    print(f"  {drift.message}")
    print(f"  Environments: {', '.join(drift.environments)}")
    for env, value in drift.values.items():
        print(f"    {env}: {value}")
    print()
```

### Drift Summary

```python
# Get drift summary
summary = validator.get_drift_summary()
print(f"Total Drifts: {summary['total']}")
print(f"Critical: {summary['critical']}")
print(f"Error: {summary['error']}")
print(f"Warning: {summary['warning']}")
```

### Compare Specific Environments

```python
# Compare two environments
comparison = validator.compare_environments('dev', 'production')

print(f"Differences: {len(comparison['differences'])}")
print(f"Only in dev: {comparison['only_in_dev']}")
print(f"Only in production: {comparison['only_in_production']}")
print(f"Identical keys: {len(comparison['identical'])}")

# Show differences
for diff in comparison['differences']:
    print(f"{diff['key']}: dev={diff['dev']}, production={diff['production']}")
```

### Generate Reports

```python
# Text report
text_report = validator.generate_report(format='text')
print(text_report)

# JSON report
json_report = validator.generate_report(format='json')
print(json_report)
```

### Configuration Hashing

```python
# Compute configuration hash
dev_hash = validator.compute_config_hash('dev')
prod_hash = validator.compute_config_hash('production')

print(f"Dev config hash: {dev_hash}")
print(f"Production config hash: {prod_hash}")

# Check if configurations match
if dev_hash == prod_hash:
    print("Configurations are identical")
```

### Export Baseline

```python
# Export production as baseline
validator.export_baseline('production', 'baseline-prod.json')

# Load baseline later for comparison
import json
with open('baseline-prod.json', 'r') as f:
    baseline = json.load(f)
    print(f"Baseline from {baseline['exported_at']}")
```

### Key Analysis

```python
# Get all keys in an environment
dev_keys = validator.get_environment_keys('dev')
print(f"Dev keys: {dev_keys}")

# Get keys common to all environments
common_keys = validator.get_common_keys()
print(f"Common keys: {common_keys}")

# Get keys unique to one environment
unique_keys = validator.get_unique_keys('dev')
print(f"Dev-only keys: {unique_keys}")
```

## Examples

### Complete Configuration Management

```python
from MultiEnv import MultiEnv, ValidationRule

# Initialize validator
validator = MultiEnv()

# Load environments
validator.load_from_file('dev', 'config/dev.json', format='json')
validator.load_from_file('staging', 'config/staging.json', format='json')
validator.load_from_file('production', 'config/production.json', format='json')

# Define validation rules
rules = [
    ValidationRule(key='database_url', required=True, value_type=str),
    ValidationRule(key='api_key', required=True, value_type=str),
    ValidationRule(key='port', required=True, value_type=int),
    ValidationRule(key='debug', required=True, value_type=bool),
    ValidationRule(
        key='environment',
        required=True,
        allowed_values=['dev', 'staging', 'production']
    ),
    ValidationRule(
        key='ssl_enabled',
        required=True,
        environments=['production']
    )
]

for rule in rules:
    validator.add_validation_rule(rule)

# Validate all environments
validation_errors = validator.validate_all()
if validation_errors:
    print("Validation Errors:")
    for env, errors in validation_errors.items():
        print(f"\n{env}:")
        for error in errors:
            print(f"  - {error}")
else:
    print("All environments passed validation!")

# Detect drift
print("\nDrift Detection:")
drifts = validator.detect_drift()

if drifts:
    critical_drifts = [d for d in drifts if d.severity.value == 'critical']
    if critical_drifts:
        print("\nCRITICAL DRIFTS DETECTED!")
        for drift in critical_drifts:
            print(f"  {drift.key}: {drift.message}")
else:
    print("No drift detected!")

# Generate full report
print("\n" + validator.generate_report(format='text'))
```

### CI/CD Pipeline Integration

```python
from MultiEnv import MultiEnv, DriftSeverity
import sys

def check_config_drift():
    """Check configuration drift in CI/CD pipeline"""
    validator = MultiEnv()
    
    # Load environment configs
    try:
        validator.load_from_file('staging', 'config/staging.json')
        validator.load_from_file('production', 'config/production.json')
    except Exception as e:
        print(f"Error loading configs: {e}")
        sys.exit(1)
    
    # Detect drift
    drifts = validator.detect_drift()
    
    # Check for critical drifts
    critical_drifts = [d for d in drifts if d.severity == DriftSeverity.CRITICAL]
    error_drifts = [d for d in drifts if d.severity == DriftSeverity.ERROR]
    
    if critical_drifts:
        print("CRITICAL drift detected! Failing build.")
        for drift in critical_drifts:
            print(f"  {drift.key}: {drift.message}")
        sys.exit(1)
    
    if error_drifts:
        print("WARNING: Error-level drift detected")
        for drift in error_drifts:
            print(f"  {drift.key}: {drift.message}")
    
    # Generate report
    with open('drift-report.json', 'w') as f:
        f.write(validator.generate_report(format='json'))
    
    print("Configuration check complete. Report saved to drift-report.json")
    return 0

if __name__ == '__main__':
    sys.exit(check_config_drift())
```

### Configuration Sync Checker

```python
from MultiEnv import MultiEnv

def ensure_config_sync(baseline_env, target_envs, required_keys):
    """Ensure specific keys are synced across environments"""
    validator = MultiEnv()
    
    # Load environments
    for env in [baseline_env] + target_envs:
        validator.load_from_file(env, f'config/{env}.json')
    
    # Check each required key
    baseline_config = validator.environments[baseline_env]['config']
    
    sync_issues = []
    for key in required_keys:
        if key not in baseline_config:
            sync_issues.append(f"Key '{key}' missing in baseline ({baseline_env})")
            continue
        
        baseline_value = baseline_config[key]
        
        for target_env in target_envs:
            target_config = validator.environments[target_env]['config']
            
            if key not in target_config:
                sync_issues.append(f"Key '{key}' missing in {target_env}")
            elif target_config[key] != baseline_value:
                sync_issues.append(
                    f"Key '{key}' differs: "
                    f"{baseline_env}={baseline_value}, "
                    f"{target_env}={target_config[key]}"
                )
    
    return sync_issues

# Example usage
issues = ensure_config_sync(
    baseline_env='production',
    target_envs=['staging', 'dev'],
    required_keys=['api_version', 'service_name', 'region']
)

if issues:
    print("Sync issues found:")
    for issue in issues:
        print(f"  - {issue}")
else:
    print("All required keys are in sync!")
```

### Environment Promotion Checker

```python
from MultiEnv import MultiEnv

def check_promotion_readiness(source_env, target_env):
    """Check if source environment is ready for promotion to target"""
    validator = MultiEnv()
    
    validator.load_from_file(source_env, f'config/{source_env}.json')
    validator.load_from_file(target_env, f'config/{target_env}.json')
    
    comparison = validator.compare_environments(source_env, target_env)
    
    issues = []
    
    # Check for keys in source that aren't in target
    if comparison[f'only_in_{source_env}']:
        issues.append(f"New keys in {source_env}: {comparison[f'only_in_{source_env}']}")
    
    # Check for removed keys
    if comparison[f'only_in_{target_env}']:
        issues.append(f"Keys removed from {source_env}: {comparison[f'only_in_{target_env}']}")
    
    # Report differences
    if comparison['differences']:
        print(f"Configuration changes ({len(comparison['differences'])} keys):")
        for diff in comparison['differences']:
            print(f"  {diff['key']}: {diff[source_env]} -> {diff[target_env]}")
    
    if issues:
        print("\nPromotion blockers:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    
    print(f"\n{source_env} is ready for promotion to {target_env}")
    return True

# Check if staging is ready for production
ready = check_promotion_readiness('staging', 'production')
```

## API Reference

### MultiEnv Class

**Methods:**

- `add_environment(name, config, source='')` - Add an environment configuration
- `load_from_file(name, filepath, format='json')` - Load configuration from file
- `add_validation_rule(rule)` - Add a validation rule
- `validate_environment(environment)` - Validate a single environment
- `validate_all()` - Validate all environments
- `detect_drift()` - Detect configuration drift
- `get_drift_summary()` - Get summary of drift by severity
- `compare_environments(env1, env2)` - Compare two environments
- `generate_report(format='text')` - Generate drift report
- `export_baseline(environment, filepath)` - Export environment as baseline
- `compute_config_hash(environment)` - Compute SHA-256 hash of configuration
- `get_environment_keys(environment)` - Get all keys in environment
- `get_common_keys()` - Get keys common to all environments
- `get_unique_keys(environment)` - Get keys unique to one environment

### ValidationRule Class

**Parameters:**

- `key` (str) - Configuration key to validate
- `required` (bool) - Whether key is required (default: False)
- `allowed_values` (List[Any]) - List of allowed values (optional)
- `value_type` (type) - Expected type of value (optional)
- `pattern` (str) - Regex pattern for string values (optional)
- `environments` (List[str]) - Specific environments for this rule (optional)

### DriftReport Class

**Attributes:**

- `severity` (DriftSeverity) - Drift severity level
- `key` (str) - Configuration key with drift
- `environments` (List[str]) - Affected environments
- `values` (Dict[str, Any]) - Values per environment
- `message` (str) - Description of drift
- `timestamp` (str) - ISO format timestamp

### DriftSeverity Enum

- `INFO` - Informational
- `WARNING` - Warning level
- `ERROR` - Error level
- `CRITICAL` - Critical (security-related keys)

## Severity Classification

MultiEnv automatically classifies drift severity based on key patterns:

**CRITICAL:**
- Keys containing: password, secret, api_key, token, database, db

**ERROR:**
- Keys containing: url, endpoint, host, port

**WARNING:**
- All other keys

## File Formats

### JSON Format

```json
{
  "database": "localhost",
  "port": 5432,
  "debug": true,
  "api_key": "secret-123"
}
```

### ENV Format

```env
DATABASE_URL=postgres://localhost/mydb
API_KEY=secret-123
PORT=8080
DEBUG=true
```

## Use Cases

- **Configuration Management**: Manage configs across development, staging, and production
- **CI/CD Integration**: Validate configurations in deployment pipelines
- **Drift Monitoring**: Continuously monitor for configuration drift
- **Environment Promotion**: Verify configurations before promoting to production
- **Security Compliance**: Ensure security-related configs are properly set
- **Team Collaboration**: Track and communicate configuration changes
- **Documentation**: Generate documentation of environment differences

## Limitations

- No support for nested configuration validation (flat keys only)
- Pattern matching limited to string values
- No automatic synchronization between environments
- No integration with configuration management tools (Consul, etcd, etc.)
- No encryption for sensitive values in reports

## Testing

Run the test suite:

```bash
python test_MultiEnv.py
```

Tests cover:
- Environment management
- File loading (JSON and .env)
- Validation rules
- Drift detection
- Configuration comparison
- Report generation
- Hash computation
- Key analysis

## Dependencies

- Python 3.7+
- No external dependencies (uses only standard library)

## License

Part of the Emu-Soft project - see main repository LICENSE.
