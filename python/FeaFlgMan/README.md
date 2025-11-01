# FeaFlgMan - Feature Flag Management System

A comprehensive tool for managing feature flags in applications, with support for various targeting rules, environments, and rollout strategies.

## Features

- **Multiple Rollout Strategies**: All users, percentage-based, whitelist, gradual, and custom
- **Targeting Rules**: Target users based on attributes, groups, or custom conditions
- **Multi-Environment Support**: Different flag states for dev, staging, production
- **Consistent Hashing**: Percentage rollouts use consistent hashing for user stability
- **Custom Evaluators**: Register custom evaluation functions for complex logic
- **Import/Export**: Save and load flag configurations
- **Statistics**: Track flag usage and status
- **Whitelist Management**: Manage user whitelists for early access

## What It Does

FeaFlgMan helps teams manage feature releases by:

1. **Creating Flags**: Define feature flags with various strategies
2. **Targeting Users**: Target specific users or groups
3. **Gradual Rollout**: Release features to a percentage of users
4. **Environment Control**: Different settings per environment
5. **Evaluation**: Check if flags are enabled for specific users/contexts

## Usage

### Basic Setup

```python
from FeaFlgMan import FeaFlgMan, RolloutStrategy

# Initialize manager
manager = FeaFlgMan(storage_path='.feature-flags')

# Create a feature flag
manager.create_flag(
    'new_dashboard',
    description='New dashboard redesign',
    enabled=True,
    rollout_strategy=RolloutStrategy.PERCENTAGE,
    rollout_percentage=25,
    tags=['frontend', 'beta']
)
```

### Rollout Strategies

```python
# All users
manager.create_flag(
    'stable_feature',
    enabled=True,
    rollout_strategy=RolloutStrategy.ALL_USERS
)

# Percentage-based
manager.create_flag(
    'gradual_feature',
    enabled=True,
    rollout_strategy=RolloutStrategy.PERCENTAGE,
    rollout_percentage=50
)

# Whitelist only
manager.create_flag(
    'beta_feature',
    enabled=True,
    rollout_strategy=RolloutStrategy.WHITELIST
)
manager.add_to_whitelist('beta_feature', 'user123')
manager.add_to_whitelist('beta_feature', 'user456')
```

### Checking Flag Status

```python
# Check if flag is enabled
if manager.is_enabled('new_dashboard', user_id='user123'):
    # Show new dashboard
    pass

# Check with context
context = {
    'country': 'US',
    'plan': 'premium',
    'age': 25
}

if manager.is_enabled('geo_feature', user_id='user123', context=context):
    # Enable geo-specific feature
    pass
```

### Targeting Rules

```python
# Create flag with targeting rules
manager.create_flag('premium_feature', enabled=True)

# Target users from specific country
manager.add_targeting_rule(
    'premium_feature',
    rule_type='attribute',
    operator='equals',
    key='country',
    value='US'
)

# Target premium users
manager.add_targeting_rule(
    'premium_feature',
    rule_type='attribute',
    operator='equals',
    key='plan',
    value='premium'
)

# Check with context
enabled = manager.is_enabled(
    'premium_feature',
    user_id='user123',
    context={'country': 'US', 'plan': 'premium'}
)
```

### Custom Evaluators

```python
# Register custom evaluator
def premium_plus_evaluator(user_id, context):
    return (
        context.get('plan') == 'premium' and
        context.get('account_age_days', 0) > 30
    )

manager.create_flag('vip_feature', enabled=True)
manager.register_custom_evaluator('vip_feature', premium_plus_evaluator)

# Evaluate
enabled = manager.is_enabled(
    'vip_feature',
    user_id='user123',
    context={'plan': 'premium', 'account_age_days': 45}
)
```

### Multi-Environment Management

```python
# Create flag enabled for all environments
manager.create_flag('multi_env_feature', enabled=True)

# Disable for production
manager.disable_for_environment('multi_env_feature', 'production')

# Set current environment
manager.set_environment('production')

# Check status (will be False in production)
enabled = manager.is_enabled('multi_env_feature')

# Switch to development
manager.set_environment('development')
enabled = manager.is_enabled('multi_env_feature')  # True
```

### Flag Management

```python
# Update flag
manager.update_flag(
    'my_feature',
    enabled=True,
    rollout_percentage=75
)

# Get flag details
status = manager.get_flag_status('my_feature', user_id='user123')
print(f"Enabled: {status['enabled']}")
print(f"Strategy: {status['rollout_strategy']}")
print(f"Enabled for user: {status['enabled_for_user']}")

# List flags
all_flags = manager.list_flags()
beta_flags = manager.list_flags(tag='beta')
prod_flags = manager.list_flags(environment='production')

# Delete flag
manager.delete_flag('old_feature')
```

### Import/Export

```python
# Export all flags
manager.export_flags('flags-backup.json')

# Import flags
manager.import_flags('flags-backup.json')

# Get statistics
stats = manager.get_statistics()
print(f"Total flags: {stats['total_flags']}")
print(f"Enabled: {stats['enabled_flags']}")
print(f"By strategy: {stats['flags_by_strategy']}")
```

## Examples

### A/B Testing

```python
# Create A/B test flag
manager.create_flag(
    'button_color_test',
    description='A/B test for button colors',
    enabled=True,
    rollout_strategy=RolloutStrategy.PERCENTAGE,
    rollout_percentage=50
)

# In your code
def get_button_color(user_id):
    if manager.is_enabled('button_color_test', user_id=user_id):
        return 'blue'  # Variant A
    return 'green'    # Variant B
```

### Progressive Rollout

```python
# Day 1: 10% rollout
manager.create_flag(
    'new_search',
    enabled=True,
    rollout_strategy=RolloutStrategy.PERCENTAGE,
    rollout_percentage=10
)

# Day 3: Increase to 25%
manager.update_flag('new_search', rollout_percentage=25)

# Day 7: Increase to 50%
manager.update_flag('new_search', rollout_percentage=50)

# Day 14: Full rollout
manager.update_flag('new_search', rollout_strategy=RolloutStrategy.ALL_USERS)
```

### Beta Program

```python
# Create beta-only feature
manager.create_flag(
    'beta_ai_assistant',
    description='AI assistant for beta users',
    enabled=True,
    rollout_strategy=RolloutStrategy.WHITELIST,
    tags=['beta', 'ai']
)

# Add beta users
beta_users = ['user1', 'user2', 'user3']
for user_id in beta_users:
    manager.add_to_whitelist('beta_ai_assistant', user_id)

# Check access
def show_ai_assistant(user_id):
    return manager.is_enabled('beta_ai_assistant', user_id=user_id)
```

### Geographic Targeting

```python
# Create geo-targeted feature
manager.create_flag('eu_privacy_mode', enabled=True)

# Add targeting rule for EU countries
eu_countries = ['DE', 'FR', 'IT', 'ES', 'UK']
manager.add_targeting_rule(
    'eu_privacy_mode',
    rule_type='attribute',
    operator='in',
    key='country',
    value=eu_countries
)

# Check with user's country
def get_privacy_settings(user_id, user_country):
    enhanced = manager.is_enabled(
        'eu_privacy_mode',
        user_id=user_id,
        context={'country': user_country}
    )
    
    return {
        'strict_mode': enhanced,
        'cookie_consent': enhanced,
        'data_retention_days': 30 if enhanced else 90
    }
```

## API Reference

### FeaFlgMan Class

**Methods:**

- `create_flag(name, description, enabled, rollout_strategy, rollout_percentage, tags, created_by)` - Create flag
- `update_flag(name, enabled, rollout_strategy, rollout_percentage, description)` - Update flag
- `add_targeting_rule(flag_name, rule_type, operator, key, value)` - Add targeting rule
- `remove_targeting_rule(flag_name, rule_index)` - Remove targeting rule
- `add_to_whitelist(flag_name, user_id)` - Add user to whitelist
- `remove_from_whitelist(flag_name, user_id)` - Remove user from whitelist
- `is_enabled(flag_name, user_id, context)` - Check if flag is enabled
- `register_custom_evaluator(flag_name, evaluator)` - Register custom evaluator
- `get_flag(name)` - Get flag configuration
- `get_metadata(name)` - Get flag metadata
- `list_flags(status, tag, environment)` - List flags
- `delete_flag(name)` - Delete flag
- `set_environment(environment)` - Set current environment
- `enable_for_environment(flag_name, environment)` - Enable for environment
- `disable_for_environment(flag_name, environment)` - Disable for environment
- `get_flag_status(flag_name, user_id)` - Get detailed flag status
- `export_flags(filepath)` - Export flags to file
- `import_flags(filepath)` - Import flags from file
- `get_statistics()` - Get statistics

### RolloutStrategy Enum

- `ALL_USERS` - Enable for all users
- `PERCENTAGE` - Enable for percentage of users
- `WHITELIST` - Enable only for whitelisted users
- `GRADUAL` - Gradual rollout
- `CUSTOM` - Custom evaluator function

### FlagStatus Enum

- `ACTIVE` - Active flag
- `INACTIVE` - Inactive flag
- `ARCHIVED` - Archived flag

### Targeting Rule Operators

- `equals` - Exact match
- `not_equals` - Not equal to
- `contains` - Contains substring
- `not_contains` - Does not contain
- `in` - In list
- `not_in` - Not in list
- `greater_than` - Greater than
- `less_than` - Less than
- `greater_or_equal` - Greater or equal
- `less_or_equal` - Less or equal

## Use Cases

- **Feature Rollouts**: Gradually release features to users
- **A/B Testing**: Test different variations
- **Beta Programs**: Give early access to select users
- **Geographic Targeting**: Enable features by region
- **Customer Tiers**: Different features for different plans
- **Canary Releases**: Test with small user percentage
- **Emergency Toggles**: Quickly disable problematic features
- **Development Testing**: Different settings per environment

## Testing

Run the test suite:

```bash
python test_FeaFlgMan.py
```

Tests cover:
- Flag creation and management
- Rollout strategies
- Targeting rules
- Whitelist management
- Environment management
- Custom evaluators
- Import/export
- Statistics

## Dependencies

- Python 3.7+
- No external dependencies (uses only standard library)

## License

Part of the Emu-Soft project - see main repository LICENSE.
