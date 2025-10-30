"""Tests for security hardening profiles."""

import pytest
import json
from security.profiles import (
    SecurityProfile,
    SecuritySettings,
    ProfileType,
    ProfileFactory,
    ProfileManager,
    ComplianceStandard,
    ComplianceRequirements,
    CompliancePresets,
    get_profile_manager,
)


# SecuritySettings Tests


def test_security_settings_creation():
    """Test creating security settings."""
    settings = SecuritySettings(
        csp_policy="default-src 'self'",
        hsts_max_age=31536000,
        min_password_length=12,
    )

    assert settings.csp_policy == "default-src 'self'"
    assert settings.hsts_max_age == 31536000
    assert settings.min_password_length == 12


def test_security_settings_to_dict():
    """Test converting settings to dictionary."""
    settings = SecuritySettings(
        min_password_length=12,
        require_2fa=True,
    )

    settings_dict = settings.to_dict()

    assert settings_dict["min_password_length"] == 12
    assert settings_dict["require_2fa"] is True
    assert isinstance(settings_dict["allowed_file_extensions"], list)


def test_security_settings_to_json():
    """Test converting settings to JSON."""
    settings = SecuritySettings(
        min_password_length=12,
        require_2fa=True,
    )

    json_str = settings.to_json()

    assert "min_password_length" in json_str
    assert "require_2fa" in json_str
    parsed = json.loads(json_str)
    assert parsed["min_password_length"] == 12


# SecurityProfile Tests


def test_security_profile_creation():
    """Test creating a security profile."""
    settings = SecuritySettings(min_password_length=12)
    profile = SecurityProfile(
        name="Test Profile",
        profile_type=ProfileType.PUBLIC,
        description="Test profile description",
        settings=settings,
        compliance_standards=[ComplianceStandard.GDPR],
    )

    assert profile.name == "Test Profile"
    assert profile.profile_type == ProfileType.PUBLIC
    assert profile.description == "Test profile description"
    assert profile.settings.min_password_length == 12
    assert ComplianceStandard.GDPR in profile.compliance_standards


def test_security_profile_to_dict():
    """Test converting profile to dictionary."""
    settings = SecuritySettings(min_password_length=12)
    profile = SecurityProfile(
        name="Test Profile",
        profile_type=ProfileType.PUBLIC,
        description="Test profile",
        settings=settings,
    )

    profile_dict = profile.to_dict()

    assert profile_dict["name"] == "Test Profile"
    assert profile_dict["profile_type"] == "public"
    assert "settings" in profile_dict


def test_security_profile_to_json():
    """Test converting profile to JSON."""
    settings = SecuritySettings(min_password_length=12)
    profile = SecurityProfile(
        name="Test Profile",
        profile_type=ProfileType.PUBLIC,
        description="Test profile",
        settings=settings,
    )

    json_str = profile.to_json()

    assert "Test Profile" in json_str
    parsed = json.loads(json_str)
    assert parsed["name"] == "Test Profile"


# ProfileFactory Tests


def test_create_public_profile():
    """Test creating public profile."""
    profile = ProfileFactory.create_public_profile()

    assert profile.name == "Public Website"
    assert profile.profile_type == ProfileType.PUBLIC
    assert profile.settings.min_password_length == 10
    assert profile.settings.enable_cors is True
    assert ComplianceStandard.GDPR in profile.compliance_standards


def test_create_intranet_profile():
    """Test creating intranet profile."""
    profile = ProfileFactory.create_intranet_profile()

    assert profile.name == "Internal Intranet"
    assert profile.profile_type == ProfileType.INTRANET
    assert profile.settings.min_password_length == 12
    assert profile.settings.ip_restrictions_enabled is True
    assert ComplianceStandard.SOC2 in profile.compliance_standards


def test_create_government_profile():
    """Test creating government profile."""
    profile = ProfileFactory.create_government_profile()

    assert profile.name == "Government/Federal"
    assert profile.profile_type == ProfileType.GOVERNMENT
    assert profile.settings.min_password_length == 16
    assert profile.settings.require_2fa is True
    assert profile.settings.session_timeout_minutes == 15
    assert profile.settings.audit_log_retention_days == 2555
    assert ComplianceStandard.FISMA in profile.compliance_standards
    assert ComplianceStandard.FEDRAMP in profile.compliance_standards


def test_create_healthcare_profile():
    """Test creating healthcare profile."""
    profile = ProfileFactory.create_healthcare_profile()

    assert profile.name == "Healthcare/HIPAA"
    assert profile.profile_type == ProfileType.HEALTHCARE
    assert profile.settings.min_password_length == 14
    assert profile.settings.require_2fa is True
    assert profile.settings.audit_log_retention_days == 2555
    assert profile.settings.encrypt_sensitive_data is True
    assert ComplianceStandard.HIPAA in profile.compliance_standards


# CompliancePresets Tests


def test_get_hipaa_requirements():
    """Test getting HIPAA compliance requirements."""
    req = CompliancePresets.get_hipaa_requirements()

    assert req.standard == ComplianceStandard.HIPAA
    assert len(req.requirements) > 0
    assert "require_2fa" in req.mandatory_settings
    assert req.mandatory_settings["require_2fa"] is True
    assert req.mandatory_settings["audit_log_retention_days"] == 2555
    assert "documentation_url" in req.to_dict()


def test_get_pci_dss_requirements():
    """Test getting PCI-DSS compliance requirements."""
    req = CompliancePresets.get_pci_dss_requirements()

    assert req.standard == ComplianceStandard.PCI_DSS
    assert len(req.requirements) > 0
    assert "min_password_length" in req.mandatory_settings
    assert req.mandatory_settings["min_password_length"] == 12
    assert req.mandatory_settings["password_expiry_days"] == 90


def test_get_gdpr_requirements():
    """Test getting GDPR compliance requirements."""
    req = CompliancePresets.get_gdpr_requirements()

    assert req.standard == ComplianceStandard.GDPR
    assert len(req.requirements) > 0
    assert "audit_enabled" in req.mandatory_settings
    assert req.mandatory_settings["audit_enabled"] is True


def test_get_soc2_requirements():
    """Test getting SOC2 compliance requirements."""
    req = CompliancePresets.get_soc2_requirements()

    assert req.standard == ComplianceStandard.SOC2
    assert len(req.requirements) > 0
    assert "require_2fa" in req.mandatory_settings
    assert req.mandatory_settings["require_2fa"] is True


# ProfileManager Tests


def test_profile_manager_initialization():
    """Test profile manager initialization."""
    manager = ProfileManager()

    profiles = manager.list_profiles()
    assert len(profiles) == 4
    assert "Public Website" in profiles
    assert "Internal Intranet" in profiles
    assert "Government/Federal" in profiles
    assert "Healthcare/HIPAA" in profiles


def test_profile_manager_get_profile():
    """Test getting a profile by name."""
    manager = ProfileManager()

    profile = manager.get_profile("Public Website")
    assert profile is not None
    assert profile.name == "Public Website"

    profile = manager.get_profile("Nonexistent")
    assert profile is None


def test_profile_manager_get_profile_details():
    """Test getting profile details."""
    manager = ProfileManager()

    details = manager.get_profile_details("Public Website")
    assert details is not None
    assert details["name"] == "Public Website"
    assert "settings" in details

    details = manager.get_profile_details("Nonexistent")
    assert details is None


def test_profile_manager_apply_profile():
    """Test applying a security profile."""
    manager = ProfileManager()

    result = manager.apply_profile("Public Website")

    assert result["success"] is True
    assert result["profile"] == "Public Website"
    assert result["profile_type"] == "public"
    assert "settings_applied" in result
    assert "compliance_standards" in result

    active = manager.get_active_profile()
    assert active is not None
    assert active.name == "Public Website"


def test_profile_manager_apply_nonexistent_profile():
    """Test applying a nonexistent profile raises error."""
    manager = ProfileManager()

    with pytest.raises(ValueError, match="Profile 'Nonexistent' not found"):
        manager.apply_profile("Nonexistent")


def test_profile_manager_add_custom_profile():
    """Test adding a custom profile."""
    manager = ProfileManager()

    settings = SecuritySettings(min_password_length=15)
    custom_profile = SecurityProfile(
        name="Custom Profile",
        profile_type=ProfileType.CUSTOM,
        description="Custom security profile",
        settings=settings,
    )

    manager.add_custom_profile(custom_profile)

    profile = manager.get_profile("Custom Profile")
    assert profile is not None
    assert profile.name == "Custom Profile"
    assert profile.settings.min_password_length == 15


def test_profile_manager_get_compliance_requirements():
    """Test getting compliance requirements."""
    manager = ProfileManager()

    req = manager.get_compliance_requirements(ComplianceStandard.HIPAA)
    assert req is not None
    assert req.standard == ComplianceStandard.HIPAA

    req = manager.get_compliance_requirements(ComplianceStandard.PCI_DSS)
    assert req is not None
    assert req.standard == ComplianceStandard.PCI_DSS


def test_profile_manager_validate_profile():
    """Test validating a profile."""
    manager = ProfileManager()

    # Validate a good profile
    result = manager.validate_profile("Government/Federal")

    assert "valid" in result
    assert "errors" in result
    assert "warnings" in result
    assert "recommendations" in result


def test_profile_manager_validate_nonexistent_profile():
    """Test validating a nonexistent profile."""
    manager = ProfileManager()

    result = manager.validate_profile("Nonexistent")

    assert result["valid"] is False
    assert "error" in result


def test_profile_manager_validate_weak_profile():
    """Test validating a profile with weak settings."""
    manager = ProfileManager()

    # Create a weak profile
    settings = SecuritySettings(
        min_password_length=6,  # Too short
        session_timeout_minutes=120,  # Too long
        audit_enabled=False,  # Should be enabled
    )
    weak_profile = SecurityProfile(
        name="Weak Profile",
        profile_type=ProfileType.CUSTOM,
        description="Weak profile",
        settings=settings,
    )

    manager.add_custom_profile(weak_profile)
    result = manager.validate_profile("Weak Profile")

    assert result["valid"] is False
    assert len(result["errors"]) > 0
    assert len(result["warnings"]) > 0


def test_profile_manager_compare_profiles():
    """Test comparing two profiles."""
    manager = ProfileManager()

    result = manager.compare_profiles("Public Website", "Government/Federal")

    assert result["profile1"] == "Public Website"
    assert result["profile2"] == "Government/Federal"
    assert "differences" in result
    assert len(result["differences"]) > 0
    assert result["total_differences"] > 0


def test_profile_manager_compare_nonexistent_profile():
    """Test comparing with a nonexistent profile."""
    manager = ProfileManager()

    with pytest.raises(ValueError, match="Profile 'Nonexistent' not found"):
        manager.compare_profiles("Public Website", "Nonexistent")


def test_profile_manager_export_profile():
    """Test exporting a profile as JSON."""
    manager = ProfileManager()

    json_str = manager.export_profile("Public Website")

    assert "Public Website" in json_str
    parsed = json.loads(json_str)
    assert parsed["name"] == "Public Website"
    assert "settings" in parsed


def test_profile_manager_export_nonexistent_profile():
    """Test exporting a nonexistent profile raises error."""
    manager = ProfileManager()

    with pytest.raises(ValueError, match="Profile 'Nonexistent' not found"):
        manager.export_profile("Nonexistent")


def test_profile_manager_import_profile():
    """Test importing a profile from JSON."""
    manager = ProfileManager()

    # Export a profile first
    json_str = manager.export_profile("Public Website")

    # Modify the name
    data = json.loads(json_str)
    data["name"] = "Imported Profile"
    json_str = json.dumps(data)

    # Import it
    profile = manager.import_profile(json_str)

    assert profile.name == "Imported Profile"
    assert profile.profile_type == ProfileType.PUBLIC

    # Verify it was added to the manager
    imported = manager.get_profile("Imported Profile")
    assert imported is not None


def test_profile_manager_import_invalid_json():
    """Test importing invalid JSON raises error."""
    manager = ProfileManager()

    with pytest.raises(ValueError, match="Invalid profile JSON"):
        manager.import_profile("invalid json")


def test_get_profile_manager_singleton():
    """Test getting global profile manager instance."""
    manager1 = get_profile_manager()
    manager2 = get_profile_manager()

    assert manager1 is manager2  # Should be the same instance


# Validation Tests


def test_validate_government_profile_requires_2fa():
    """Test that government profile requires 2FA."""
    manager = ProfileManager()

    # Create a government profile without 2FA
    settings = SecuritySettings(
        min_password_length=16,
        require_2fa=False,  # This should trigger an error
    )
    profile = SecurityProfile(
        name="Bad Government Profile",
        profile_type=ProfileType.GOVERNMENT,
        description="Government profile without 2FA",
        settings=settings,
    )

    manager.add_custom_profile(profile)
    result = manager.validate_profile("Bad Government Profile")

    assert result["valid"] is False
    assert any("2FA" in err for err in result["errors"])


def test_validate_healthcare_profile_requires_2fa():
    """Test that healthcare profile requires 2FA."""
    manager = ProfileManager()

    # Create a healthcare profile without 2FA
    settings = SecuritySettings(
        min_password_length=14,
        require_2fa=False,  # This should trigger an error
    )
    profile = SecurityProfile(
        name="Bad Healthcare Profile",
        profile_type=ProfileType.HEALTHCARE,
        description="Healthcare profile without 2FA",
        settings=settings,
    )

    manager.add_custom_profile(profile)
    result = manager.validate_profile("Bad Healthcare Profile")

    assert result["valid"] is False
    assert any("2FA" in err for err in result["errors"])


def test_validate_hipaa_compliance():
    """Test validating HIPAA compliance requirements."""
    manager = ProfileManager()

    # Create a profile claiming HIPAA compliance but missing requirements
    settings = SecuritySettings(
        require_2fa=False,  # HIPAA requires 2FA
        audit_log_retention_days=30,  # HIPAA requires 7 years
    )
    profile = SecurityProfile(
        name="Bad HIPAA Profile",
        profile_type=ProfileType.CUSTOM,
        description="Non-compliant HIPAA profile",
        settings=settings,
        compliance_standards=[ComplianceStandard.HIPAA],
    )

    manager.add_custom_profile(profile)
    result = manager.validate_profile("Bad HIPAA Profile")

    assert result["valid"] is False
    assert len(result["errors"]) > 0


def test_validate_tls_version():
    """Test validating TLS version."""
    manager = ProfileManager()

    # Create a profile with old TLS version
    settings = SecuritySettings(
        tls_version="1.0",  # Too old
    )
    profile = SecurityProfile(
        name="Old TLS Profile",
        profile_type=ProfileType.CUSTOM,
        description="Profile with old TLS",
        settings=settings,
    )

    manager.add_custom_profile(profile)
    result = manager.validate_profile("Old TLS Profile")

    assert result["valid"] is False
    assert any("TLS" in err for err in result["errors"])


# Integration Tests


def test_full_profile_lifecycle():
    """Test complete profile lifecycle: create, apply, validate, export, import."""
    manager = ProfileManager()

    # 1. Create a custom profile
    settings = SecuritySettings(
        min_password_length=14,
        require_2fa=True,
        session_timeout_minutes=20,
        audit_enabled=True,
    )
    profile = SecurityProfile(
        name="Test Lifecycle Profile",
        profile_type=ProfileType.CUSTOM,
        description="Profile for lifecycle test",
        settings=settings,
    )

    # 2. Add it to the manager
    manager.add_custom_profile(profile)

    # 3. Apply it
    result = manager.apply_profile("Test Lifecycle Profile")
    assert result["success"] is True

    # 4. Validate it
    validation = manager.validate_profile("Test Lifecycle Profile")
    assert validation["valid"] is True

    # 5. Export it
    json_str = manager.export_profile("Test Lifecycle Profile")
    assert "Test Lifecycle Profile" in json_str

    # 6. Modify and import it
    data = json.loads(json_str)
    data["name"] = "Imported Lifecycle Profile"
    imported_profile = manager.import_profile(json.dumps(data))

    # 7. Verify the imported profile
    assert imported_profile.name == "Imported Lifecycle Profile"
    assert manager.get_profile("Imported Lifecycle Profile") is not None


def test_profile_comparison_shows_differences():
    """Test that profile comparison identifies key differences."""
    manager = ProfileManager()

    result = manager.compare_profiles("Public Website", "Healthcare/HIPAA")

    # Should show differences in password length, 2FA, audit retention, etc.
    differences = result["differences"]
    settings_with_differences = {d["setting"] for d in differences}

    assert "min_password_length" in settings_with_differences
    assert "require_2fa" in settings_with_differences
    assert "audit_log_retention_days" in settings_with_differences
