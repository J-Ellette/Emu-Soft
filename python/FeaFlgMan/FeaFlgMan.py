"""
Feature Flag Management System

A comprehensive tool for managing feature flags in applications,
with support for various targeting rules, environments, and rollout strategies.
"""

import json
import os
from typing import Dict, List, Set, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import hashlib


class FlagStatus(Enum):
    """Status of a feature flag"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class RolloutStrategy(Enum):
    """Rollout strategy for feature flags"""
    ALL_USERS = "all_users"
    PERCENTAGE = "percentage"
    WHITELIST = "whitelist"
    GRADUAL = "gradual"
    CUSTOM = "custom"


@dataclass
class TargetingRule:
    """Targeting rule for feature flags"""
    rule_type: str  # 'user', 'group', 'attribute', 'percentage'
    operator: str   # 'equals', 'contains', 'greater_than', 'less_than', 'in'
    key: str
    value: Any
    enabled: bool = True


@dataclass
class FlagMetadata:
    """Metadata for a feature flag"""
    name: str
    description: str
    status: FlagStatus
    created_at: str
    updated_at: Optional[str] = None
    created_by: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    environments: Dict[str, bool] = field(default_factory=dict)


@dataclass
class FlagConfig:
    """Configuration for a feature flag"""
    name: str
    enabled: bool
    rollout_strategy: RolloutStrategy
    rollout_percentage: int = 100
    whitelist_users: List[str] = field(default_factory=list)
    targeting_rules: List[TargetingRule] = field(default_factory=list)
    default_value: Any = False


class FeaFlgMan:
    """
    Feature Flag Management System
    
    Manages feature flags with support for targeting, rollout strategies,
    and multiple environments.
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        """
        Initialize FeaFlgMan
        
        Args:
            storage_path: Path to store flag configurations
        """
        self.storage_path = storage_path or os.path.join(os.getcwd(), '.feature-flags')
        self.flags: Dict[str, FlagConfig] = {}
        self.metadata: Dict[str, FlagMetadata] = {}
        self.environments: Set[str] = {'development', 'staging', 'production'}
        self.current_environment: str = 'development'
        self.evaluators: Dict[str, Callable] = {}
        
        os.makedirs(self.storage_path, exist_ok=True)
    
    def create_flag(
        self,
        name: str,
        description: str = "",
        enabled: bool = False,
        rollout_strategy: RolloutStrategy = RolloutStrategy.ALL_USERS,
        rollout_percentage: int = 100,
        tags: Optional[List[str]] = None,
        created_by: Optional[str] = None
    ) -> FlagConfig:
        """
        Create a new feature flag
        
        Args:
            name: Flag name
            description: Flag description
            enabled: Initial enabled state
            rollout_strategy: Rollout strategy
            rollout_percentage: Percentage for gradual rollout
            tags: Tags for categorization
            created_by: Creator identifier
            
        Returns:
            FlagConfig object
        """
        if name in self.flags:
            raise ValueError(f"Flag '{name}' already exists")
        
        now = datetime.utcnow().isoformat()
        
        config = FlagConfig(
            name=name,
            enabled=enabled,
            rollout_strategy=rollout_strategy,
            rollout_percentage=rollout_percentage
        )
        
        metadata = FlagMetadata(
            name=name,
            description=description,
            status=FlagStatus.ACTIVE,
            created_at=now,
            created_by=created_by,
            tags=tags or [],
            environments={env: enabled for env in self.environments}
        )
        
        self.flags[name] = config
        self.metadata[name] = metadata
        
        return config
    
    def update_flag(
        self,
        name: str,
        enabled: Optional[bool] = None,
        rollout_strategy: Optional[RolloutStrategy] = None,
        rollout_percentage: Optional[int] = None,
        description: Optional[str] = None
    ) -> None:
        """
        Update a feature flag
        
        Args:
            name: Flag name
            enabled: New enabled state
            rollout_strategy: New rollout strategy
            rollout_percentage: New rollout percentage
            description: New description
        """
        if name not in self.flags:
            raise ValueError(f"Flag '{name}' not found")
        
        config = self.flags[name]
        metadata = self.metadata[name]
        
        if enabled is not None:
            config.enabled = enabled
        if rollout_strategy is not None:
            config.rollout_strategy = rollout_strategy
        if rollout_percentage is not None:
            config.rollout_percentage = rollout_percentage
        if description is not None:
            metadata.description = description
        
        metadata.updated_at = datetime.utcnow().isoformat()
    
    def add_targeting_rule(
        self,
        flag_name: str,
        rule_type: str,
        operator: str,
        key: str,
        value: Any
    ) -> None:
        """
        Add a targeting rule to a flag
        
        Args:
            flag_name: Flag name
            rule_type: Type of rule ('user', 'group', 'attribute', 'percentage')
            operator: Operator ('equals', 'contains', 'greater_than', 'less_than', 'in')
            key: Attribute key
            value: Value to match
        """
        if flag_name not in self.flags:
            raise ValueError(f"Flag '{flag_name}' not found")
        
        rule = TargetingRule(
            rule_type=rule_type,
            operator=operator,
            key=key,
            value=value
        )
        
        self.flags[flag_name].targeting_rules.append(rule)
    
    def remove_targeting_rule(self, flag_name: str, rule_index: int) -> None:
        """
        Remove a targeting rule from a flag
        
        Args:
            flag_name: Flag name
            rule_index: Index of rule to remove
        """
        if flag_name not in self.flags:
            raise ValueError(f"Flag '{flag_name}' not found")
        
        if 0 <= rule_index < len(self.flags[flag_name].targeting_rules):
            self.flags[flag_name].targeting_rules.pop(rule_index)
        else:
            raise IndexError("Invalid rule index")
    
    def add_to_whitelist(self, flag_name: str, user_id: str) -> None:
        """
        Add a user to flag whitelist
        
        Args:
            flag_name: Flag name
            user_id: User identifier
        """
        if flag_name not in self.flags:
            raise ValueError(f"Flag '{flag_name}' not found")
        
        if user_id not in self.flags[flag_name].whitelist_users:
            self.flags[flag_name].whitelist_users.append(user_id)
    
    def remove_from_whitelist(self, flag_name: str, user_id: str) -> None:
        """
        Remove a user from flag whitelist
        
        Args:
            flag_name: Flag name
            user_id: User identifier
        """
        if flag_name not in self.flags:
            raise ValueError(f"Flag '{flag_name}' not found")
        
        if user_id in self.flags[flag_name].whitelist_users:
            self.flags[flag_name].whitelist_users.remove(user_id)
    
    def is_enabled(
        self,
        flag_name: str,
        user_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Check if a flag is enabled for a user/context
        
        Args:
            flag_name: Flag name
            user_id: User identifier
            context: Additional context for evaluation
            
        Returns:
            True if flag is enabled
        """
        if flag_name not in self.flags:
            return False
        
        config = self.flags[flag_name]
        
        # Check if flag is globally disabled
        if not config.enabled:
            return False
        
        # Check environment-specific state
        metadata = self.metadata[flag_name]
        if self.current_environment in metadata.environments:
            if not metadata.environments[self.current_environment]:
                return False
        
        # Evaluate targeting rules first if they exist
        if config.targeting_rules and context:
            if not self._evaluate_targeting_rules(config.targeting_rules, user_id, context):
                return False
        
        # Evaluate based on rollout strategy
        if config.rollout_strategy == RolloutStrategy.ALL_USERS:
            return True
        
        elif config.rollout_strategy == RolloutStrategy.WHITELIST:
            return user_id in config.whitelist_users if user_id else False
        
        elif config.rollout_strategy == RolloutStrategy.PERCENTAGE:
            if user_id:
                return self._user_in_percentage(user_id, config.rollout_percentage)
            return False
        
        elif config.rollout_strategy == RolloutStrategy.CUSTOM:
            if flag_name in self.evaluators:
                return self.evaluators[flag_name](user_id, context or {})
            return False
        
        return True
    
    def _user_in_percentage(self, user_id: str, percentage: int) -> bool:
        """
        Determine if user falls within percentage rollout
        
        Uses consistent hashing to ensure same user always gets same result
        """
        user_hash = int(hashlib.md5(user_id.encode()).hexdigest(), 16)
        bucket = user_hash % 100
        return bucket < percentage
    
    def _evaluate_targeting_rules(
        self,
        rules: List[TargetingRule],
        user_id: Optional[str],
        context: Dict[str, Any]
    ) -> bool:
        """Evaluate all targeting rules (AND logic)"""
        for rule in rules:
            if not rule.enabled:
                continue
            
            if not self._evaluate_single_rule(rule, user_id, context):
                return False
        
        return True
    
    def _evaluate_single_rule(
        self,
        rule: TargetingRule,
        user_id: Optional[str],
        context: Dict[str, Any]
    ) -> bool:
        """Evaluate a single targeting rule"""
        # Get value from context
        if rule.key == 'user_id':
            actual_value = user_id
        else:
            actual_value = context.get(rule.key)
        
        if actual_value is None:
            return False
        
        # Evaluate based on operator
        if rule.operator == 'equals':
            return actual_value == rule.value
        elif rule.operator == 'not_equals':
            return actual_value != rule.value
        elif rule.operator == 'contains':
            return rule.value in str(actual_value)
        elif rule.operator == 'not_contains':
            return rule.value not in str(actual_value)
        elif rule.operator == 'in':
            return actual_value in rule.value
        elif rule.operator == 'not_in':
            return actual_value not in rule.value
        elif rule.operator == 'greater_than':
            return float(actual_value) > float(rule.value)
        elif rule.operator == 'less_than':
            return float(actual_value) < float(rule.value)
        elif rule.operator == 'greater_or_equal':
            return float(actual_value) >= float(rule.value)
        elif rule.operator == 'less_or_equal':
            return float(actual_value) <= float(rule.value)
        
        return False
    
    def register_custom_evaluator(self, flag_name: str, evaluator: Callable) -> None:
        """
        Register a custom evaluator function for a flag
        
        Args:
            flag_name: Flag name
            evaluator: Function that takes (user_id, context) and returns bool
        """
        if flag_name not in self.flags:
            raise ValueError(f"Flag '{flag_name}' not found")
        
        self.evaluators[flag_name] = evaluator
        self.flags[flag_name].rollout_strategy = RolloutStrategy.CUSTOM
    
    def get_flag(self, name: str) -> Optional[FlagConfig]:
        """Get flag configuration"""
        return self.flags.get(name)
    
    def get_metadata(self, name: str) -> Optional[FlagMetadata]:
        """Get flag metadata"""
        return self.metadata.get(name)
    
    def list_flags(
        self,
        status: Optional[FlagStatus] = None,
        tag: Optional[str] = None,
        environment: Optional[str] = None
    ) -> List[str]:
        """
        List flags with optional filtering
        
        Args:
            status: Filter by status
            tag: Filter by tag
            environment: Filter by environment
            
        Returns:
            List of flag names
        """
        result = []
        
        for name, metadata in self.metadata.items():
            # Filter by status
            if status and metadata.status != status:
                continue
            
            # Filter by tag
            if tag and tag not in metadata.tags:
                continue
            
            # Filter by environment
            if environment:
                if environment not in metadata.environments:
                    continue
                if not metadata.environments[environment]:
                    continue
            
            result.append(name)
        
        return result
    
    def delete_flag(self, name: str) -> bool:
        """
        Delete a flag (archives it first)
        
        Args:
            name: Flag name
            
        Returns:
            True if deleted
        """
        if name not in self.flags:
            return False
        
        # Archive first
        self.metadata[name].status = FlagStatus.ARCHIVED
        
        # Then remove
        del self.flags[name]
        del self.metadata[name]
        
        if name in self.evaluators:
            del self.evaluators[name]
        
        return True
    
    def set_environment(self, environment: str) -> None:
        """
        Set current environment
        
        Args:
            environment: Environment name
        """
        if environment not in self.environments:
            self.environments.add(environment)
        self.current_environment = environment
    
    def enable_for_environment(self, flag_name: str, environment: str) -> None:
        """
        Enable flag for specific environment
        
        Args:
            flag_name: Flag name
            environment: Environment name
        """
        if flag_name not in self.flags:
            raise ValueError(f"Flag '{flag_name}' not found")
        
        self.metadata[flag_name].environments[environment] = True
    
    def disable_for_environment(self, flag_name: str, environment: str) -> None:
        """
        Disable flag for specific environment
        
        Args:
            flag_name: Flag name
            environment: Environment name
        """
        if flag_name not in self.flags:
            raise ValueError(f"Flag '{flag_name}' not found")
        
        self.metadata[flag_name].environments[environment] = False
    
    def get_flag_status(self, flag_name: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get detailed status of a flag
        
        Args:
            flag_name: Flag name
            user_id: User identifier (for user-specific evaluation)
            
        Returns:
            Dictionary with flag status details
        """
        if flag_name not in self.flags:
            return {'exists': False}
        
        config = self.flags[flag_name]
        metadata = self.metadata[flag_name]
        
        result = {
            'exists': True,
            'name': flag_name,
            'enabled': config.enabled,
            'rollout_strategy': config.rollout_strategy.value,
            'rollout_percentage': config.rollout_percentage,
            'status': metadata.status.value,
            'description': metadata.description,
            'environments': metadata.environments,
            'tags': metadata.tags,
            'targeting_rules_count': len(config.targeting_rules),
            'whitelist_count': len(config.whitelist_users)
        }
        
        if user_id:
            result['enabled_for_user'] = self.is_enabled(flag_name, user_id)
        
        return result
    
    def export_flags(self, filepath: str) -> None:
        """
        Export all flags to a JSON file
        
        Args:
            filepath: Path to export file
        """
        data = {
            'flags': {},
            'metadata': {},
            'environments': list(self.environments),
            'exported_at': datetime.utcnow().isoformat()
        }
        
        for name, config in self.flags.items():
            data['flags'][name] = {
                'name': config.name,
                'enabled': config.enabled,
                'rollout_strategy': config.rollout_strategy.value,
                'rollout_percentage': config.rollout_percentage,
                'whitelist_users': config.whitelist_users,
                'targeting_rules': [
                    {
                        'rule_type': r.rule_type,
                        'operator': r.operator,
                        'key': r.key,
                        'value': r.value,
                        'enabled': r.enabled
                    }
                    for r in config.targeting_rules
                ],
                'default_value': config.default_value
            }
        
        for name, metadata in self.metadata.items():
            data['metadata'][name] = {
                'name': metadata.name,
                'description': metadata.description,
                'status': metadata.status.value,
                'created_at': metadata.created_at,
                'updated_at': metadata.updated_at,
                'created_by': metadata.created_by,
                'tags': metadata.tags,
                'environments': metadata.environments
            }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    def import_flags(self, filepath: str) -> None:
        """
        Import flags from a JSON file
        
        Args:
            filepath: Path to import file
        """
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        # Import environments
        if 'environments' in data:
            self.environments.update(data['environments'])
        
        # Import flags
        for name, flag_data in data.get('flags', {}).items():
            config = FlagConfig(
                name=flag_data['name'],
                enabled=flag_data['enabled'],
                rollout_strategy=RolloutStrategy(flag_data['rollout_strategy']),
                rollout_percentage=flag_data.get('rollout_percentage', 100),
                whitelist_users=flag_data.get('whitelist_users', []),
                targeting_rules=[
                    TargetingRule(
                        rule_type=r['rule_type'],
                        operator=r['operator'],
                        key=r['key'],
                        value=r['value'],
                        enabled=r.get('enabled', True)
                    )
                    for r in flag_data.get('targeting_rules', [])
                ],
                default_value=flag_data.get('default_value', False)
            )
            self.flags[name] = config
        
        # Import metadata
        for name, meta_data in data.get('metadata', {}).items():
            metadata = FlagMetadata(
                name=meta_data['name'],
                description=meta_data['description'],
                status=FlagStatus(meta_data['status']),
                created_at=meta_data['created_at'],
                updated_at=meta_data.get('updated_at'),
                created_by=meta_data.get('created_by'),
                tags=meta_data.get('tags', []),
                environments=meta_data.get('environments', {})
            )
            self.metadata[name] = metadata
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about flags
        
        Returns:
            Dictionary with statistics
        """
        total_flags = len(self.flags)
        enabled_flags = sum(1 for f in self.flags.values() if f.enabled)
        
        flags_by_status = {}
        for metadata in self.metadata.values():
            status = metadata.status.value
            flags_by_status[status] = flags_by_status.get(status, 0) + 1
        
        flags_by_strategy = {}
        for config in self.flags.values():
            strategy = config.rollout_strategy.value
            flags_by_strategy[strategy] = flags_by_strategy.get(strategy, 0) + 1
        
        return {
            'total_flags': total_flags,
            'enabled_flags': enabled_flags,
            'disabled_flags': total_flags - enabled_flags,
            'flags_by_status': flags_by_status,
            'flags_by_strategy': flags_by_strategy,
            'total_environments': len(self.environments)
        }
