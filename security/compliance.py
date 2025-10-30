"""Compliance features for data protection regulations (GDPR, etc.)."""

from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Dict, Any, List, Optional
import json


class ConsentType(Enum):
    """Types of consent that can be tracked."""

    NECESSARY = "necessary"  # Required for service
    FUNCTIONAL = "functional"  # Enhanced functionality
    ANALYTICS = "analytics"  # Usage analytics
    MARKETING = "marketing"  # Marketing communications
    THIRD_PARTY = "third_party"  # Third-party integrations


@dataclass
class Consent:
    """Represents user consent for data processing."""

    user_id: str
    consent_type: ConsentType
    granted: bool
    timestamp: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert consent to dictionary."""
        return {
            "user_id": self.user_id,
            "consent_type": self.consent_type.value,
            "granted": self.granted,
            "timestamp": self.timestamp.isoformat(),
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "details": self.details,
        }


class ConsentManager:
    """Manager for tracking and managing user consent."""

    def __init__(self) -> None:
        """Initialize consent manager."""
        self._consents: Dict[str, List[Consent]] = {}

    def grant_consent(
        self,
        user_id: str,
        consent_type: ConsentType,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> Consent:
        """Grant consent for a user.

        Args:
            user_id: User ID
            consent_type: Type of consent
            ip_address: IP address of the request
            user_agent: User agent string
            details: Additional details

        Returns:
            Created Consent instance
        """
        consent = Consent(
            user_id=user_id,
            consent_type=consent_type,
            granted=True,
            timestamp=datetime.now(timezone.utc),
            ip_address=ip_address,
            user_agent=user_agent,
            details=details or {},
        )

        if user_id not in self._consents:
            self._consents[user_id] = []

        self._consents[user_id].append(consent)

        return consent

    def revoke_consent(
        self,
        user_id: str,
        consent_type: ConsentType,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Consent:
        """Revoke consent for a user.

        Args:
            user_id: User ID
            consent_type: Type of consent
            ip_address: IP address of the request
            user_agent: User agent string

        Returns:
            Created Consent instance
        """
        consent = Consent(
            user_id=user_id,
            consent_type=consent_type,
            granted=False,
            timestamp=datetime.now(timezone.utc),
            ip_address=ip_address,
            user_agent=user_agent,
        )

        if user_id not in self._consents:
            self._consents[user_id] = []

        self._consents[user_id].append(consent)

        return consent

    def has_consent(self, user_id: str, consent_type: ConsentType) -> bool:
        """Check if user has granted consent.

        Args:
            user_id: User ID
            consent_type: Type of consent

        Returns:
            True if consent is granted, False otherwise
        """
        if user_id not in self._consents:
            # Necessary consent is always granted
            return consent_type == ConsentType.NECESSARY

        # Get most recent consent of this type
        relevant_consents = [c for c in self._consents[user_id] if c.consent_type == consent_type]

        if not relevant_consents:
            return consent_type == ConsentType.NECESSARY

        # Sort by timestamp and get most recent
        latest = sorted(relevant_consents, key=lambda c: c.timestamp)[-1]

        return latest.granted

    def get_consents(self, user_id: str) -> List[Consent]:
        """Get all consents for a user.

        Args:
            user_id: User ID

        Returns:
            List of consents
        """
        return self._consents.get(user_id, [])

    def export_consents(self, user_id: str) -> str:
        """Export user consent history as JSON.

        Args:
            user_id: User ID

        Returns:
            JSON string of consent history
        """
        consents = self.get_consents(user_id)
        return json.dumps([c.to_dict() for c in consents], indent=2)


@dataclass
class DataRetentionPolicy:
    """Policy for data retention."""

    name: str
    data_type: str
    retention_days: int
    description: str = ""

    def is_expired(self, created_at: datetime) -> bool:
        """Check if data has exceeded retention period.

        Args:
            created_at: When the data was created

        Returns:
            True if data should be deleted, False otherwise
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=self.retention_days)
        return created_at < cutoff


class ComplianceManager:
    """Manager for compliance features."""

    def __init__(self) -> None:
        """Initialize compliance manager."""
        self.consent_manager = ConsentManager()
        self._retention_policies: Dict[str, DataRetentionPolicy] = {}
        self._user_data: Dict[str, Dict[str, Any]] = {}

    def add_retention_policy(self, policy: DataRetentionPolicy) -> None:
        """Add a data retention policy.

        Args:
            policy: Data retention policy
        """
        self._retention_policies[policy.data_type] = policy

    def get_retention_policy(self, data_type: str) -> Optional[DataRetentionPolicy]:
        """Get retention policy for a data type.

        Args:
            data_type: Type of data

        Returns:
            Retention policy or None
        """
        return self._retention_policies.get(data_type)

    def should_retain(self, data_type: str, created_at: datetime) -> bool:
        """Check if data should be retained.

        Args:
            data_type: Type of data
            created_at: When the data was created

        Returns:
            True if data should be kept, False if it should be deleted
        """
        policy = self.get_retention_policy(data_type)
        if not policy:
            # No policy means retain indefinitely
            return True

        return not policy.is_expired(created_at)

    def export_user_data(self, user_id: str) -> Dict[str, Any]:
        """Export all data for a user (GDPR right to data portability).

        Args:
            user_id: User ID

        Returns:
            Dictionary containing all user data
        """
        return {
            "user_id": user_id,
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "consents": [c.to_dict() for c in self.consent_manager.get_consents(user_id)],
            "data": self._user_data.get(user_id, {}),
        }

    def delete_user_data(self, user_id: str) -> Dict[str, Any]:
        """Delete all data for a user (GDPR right to erasure).

        Args:
            user_id: User ID

        Returns:
            Summary of deleted data
        """
        deleted = {
            "user_id": user_id,
            "deleted_at": datetime.now(timezone.utc).isoformat(),
            "consents_deleted": len(self.consent_manager.get_consents(user_id)),
            "data_types_deleted": [],
        }

        # Delete consents
        if user_id in self.consent_manager._consents:
            del self.consent_manager._consents[user_id]

        # Delete user data
        if user_id in self._user_data:
            deleted["data_types_deleted"] = list(self._user_data[user_id].keys())
            del self._user_data[user_id]

        return deleted

    def anonymize_user_data(self, user_id: str) -> Dict[str, Any]:
        """Anonymize user data while retaining analytics value.

        Args:
            user_id: User ID

        Returns:
            Summary of anonymized data
        """
        anonymized = {
            "user_id": user_id,
            "anonymized_at": datetime.now(timezone.utc).isoformat(),
            "data_types_anonymized": [],
        }

        if user_id in self._user_data:
            # Replace identifying information with anonymized values
            anonymized["data_types_anonymized"] = list(self._user_data[user_id].keys())
            # In a real implementation, would anonymize specific fields

        return anonymized

    def get_compliance_report(self) -> Dict[str, Any]:
        """Generate compliance report.

        Returns:
            Compliance report data
        """
        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "total_users": len(self._user_data),
            "total_consents": sum(
                len(consents) for consents in self.consent_manager._consents.values()
            ),
            "retention_policies": {
                data_type: {
                    "name": policy.name,
                    "retention_days": policy.retention_days,
                    "description": policy.description,
                }
                for data_type, policy in self._retention_policies.items()
            },
        }
