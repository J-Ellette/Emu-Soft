"""
SchemReg - Event Schema Registry with Versioning

A schema registry for managing event schemas with version control,
compatibility checking, and validation.
"""

import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


class CompatibilityMode(Enum):
    """Schema compatibility modes"""
    BACKWARD = "backward"
    FORWARD = "forward"
    FULL = "full"
    NONE = "none"


@dataclass
class SchemaVersion:
    """Represents a schema version"""
    version: int
    schema: Dict[str, Any]
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    created_by: Optional[str] = None


@dataclass
class SchemaMetadata:
    """Metadata for a schema"""
    subject: str
    compatibility_mode: CompatibilityMode
    latest_version: int
    versions: List[SchemaVersion] = field(default_factory=list)


class SchemReg:
    """Event Schema Registry with Versioning"""
    
    def __init__(self):
        """Initialize schema registry"""
        self.schemas: Dict[str, SchemaMetadata] = {}
        self.default_compatibility = CompatibilityMode.BACKWARD
    
    def register_schema(
        self,
        subject: str,
        schema: Dict[str, Any],
        created_by: Optional[str] = None
    ) -> int:
        """Register a new schema version"""
        if subject not in self.schemas:
            # New subject
            metadata = SchemaMetadata(
                subject=subject,
                compatibility_mode=self.default_compatibility,
                latest_version=1,
                versions=[]
            )
            self.schemas[subject] = metadata
        else:
            metadata = self.schemas[subject]
            
            # Check compatibility
            if not self._check_compatibility(metadata, schema):
                raise ValueError(f"Schema incompatible with {metadata.compatibility_mode.value} mode")
            
            metadata.latest_version += 1
        
        version = metadata.latest_version
        schema_version = SchemaVersion(
            version=version,
            schema=schema,
            created_by=created_by
        )
        
        metadata.versions.append(schema_version)
        return version
    
    def get_schema(self, subject: str, version: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Get schema by subject and version"""
        if subject not in self.schemas:
            return None
        
        metadata = self.schemas[subject]
        
        if version is None:
            version = metadata.latest_version
        
        for sv in metadata.versions:
            if sv.version == version:
                return sv.schema
        
        return None
    
    def get_latest_version(self, subject: str) -> Optional[int]:
        """Get latest version number"""
        if subject not in self.schemas:
            return None
        return self.schemas[subject].latest_version
    
    def list_subjects(self) -> List[str]:
        """List all subjects"""
        return list(self.schemas.keys())
    
    def list_versions(self, subject: str) -> List[int]:
        """List all versions for a subject"""
        if subject not in self.schemas:
            return []
        return [sv.version for sv in self.schemas[subject].versions]
    
    def set_compatibility(self, subject: str, mode: CompatibilityMode) -> None:
        """Set compatibility mode for a subject"""
        if subject in self.schemas:
            self.schemas[subject].compatibility_mode = mode
    
    def _check_compatibility(self, metadata: SchemaMetadata, new_schema: Dict[str, Any]) -> bool:
        """Check schema compatibility"""
        if not metadata.versions:
            return True
        
        mode = metadata.compatibility_mode
        
        if mode == CompatibilityMode.NONE:
            return True
        
        latest_schema = metadata.versions[-1].schema
        
        if mode == CompatibilityMode.BACKWARD:
            return self._is_backward_compatible(latest_schema, new_schema)
        elif mode == CompatibilityMode.FORWARD:
            return self._is_forward_compatible(latest_schema, new_schema)
        elif mode == CompatibilityMode.FULL:
            return (self._is_backward_compatible(latest_schema, new_schema) and
                    self._is_forward_compatible(latest_schema, new_schema))
        
        return True
    
    def _is_backward_compatible(self, old_schema: Dict, new_schema: Dict) -> bool:
        """Check backward compatibility (new schema can read old data)"""
        old_fields = set(old_schema.get('properties', {}).keys())
        new_fields = set(new_schema.get('properties', {}).keys())
        
        # New schema must contain all old fields or have defaults
        removed_fields = old_fields - new_fields
        
        if removed_fields:
            # Check if removed fields have defaults in new schema
            for field in removed_fields:
                if 'default' not in new_schema.get('properties', {}).get(field, {}):
                    return False
        
        return True
    
    def _is_forward_compatible(self, old_schema: Dict, new_schema: Dict) -> bool:
        """Check forward compatibility (old schema can read new data)"""
        old_fields = set(old_schema.get('properties', {}).keys())
        new_fields = set(new_schema.get('properties', {}).keys())
        
        # New fields must have defaults
        added_fields = new_fields - old_fields
        
        for field in added_fields:
            field_schema = new_schema.get('properties', {}).get(field, {})
            if 'default' not in field_schema:
                return False
        
        return True
    
    def validate(self, subject: str, data: Dict[str, Any], version: Optional[int] = None) -> bool:
        """Validate data against schema"""
        schema = self.get_schema(subject, version)
        
        if not schema:
            return False
        
        # Simple validation - check required fields and types
        required = schema.get('required', [])
        properties = schema.get('properties', {})
        
        # Check required fields
        for field in required:
            if field not in data:
                return False
        
        # Check types
        for field, value in data.items():
            if field in properties:
                expected_type = properties[field].get('type')
                if expected_type and not self._check_type(value, expected_type):
                    return False
        
        return True
    
    def _check_type(self, value: Any, expected_type: str) -> bool:
        """Check if value matches expected type"""
        type_map = {
            'string': str,
            'number': (int, float),
            'integer': int,
            'boolean': bool,
            'array': list,
            'object': dict
        }
        
        expected_python_type = type_map.get(expected_type)
        if expected_python_type:
            return isinstance(value, expected_python_type)
        
        return True
    
    def delete_subject(self, subject: str) -> bool:
        """Delete a subject and all its versions"""
        if subject in self.schemas:
            del self.schemas[subject]
            return True
        return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get registry statistics"""
        total_versions = sum(len(meta.versions) for meta in self.schemas.values())
        
        return {
            'total_subjects': len(self.schemas),
            'total_versions': total_versions,
            'subjects': list(self.schemas.keys())
        }
