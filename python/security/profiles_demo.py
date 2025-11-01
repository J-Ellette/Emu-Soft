"""
Developed by PowerShield, as an alternative to Django Security
"""

"""Example application demonstrating security hardening profiles.

This example shows how to use the security hardening profiles feature including:
- Applying predefined security profiles
- Validating profile configurations
- Comparing different profiles
- Creating custom profiles
- Checking compliance requirements
"""

from security.profiles import (
    ProfileManager,
    ProfileFactory,
    SecurityProfile,
    SecuritySettings,
    ProfileType,
    ComplianceStandard,
    CompliancePresets,
    get_profile_manager,
)


def main():
    """Demonstrate security hardening profiles."""
    print("=" * 80)
    print("Security Hardening Profiles Demo")
    print("=" * 80)
    print()

    # Get the global profile manager
    manager = get_profile_manager()

    # 1. List available profiles
    print("1. Available Security Profiles:")
    print("-" * 80)
    for profile_name in manager.list_profiles():
        profile = manager.get_profile(profile_name)
        print(f"   - {profile_name} ({profile.profile_type.value})")
        print(f"     {profile.description}")
    print()

    # 2. View profile details
    print("2. Public Website Profile Details:")
    print("-" * 80)
    public_profile = manager.get_profile("Public Website")
    if public_profile:
        print(f"   Name: {public_profile.name}")
        print(f"   Type: {public_profile.profile_type.value}")
        print(f"   Description: {public_profile.description}")
        print(f"   Min Password Length: {public_profile.settings.min_password_length}")
        print(f"   Require 2FA: {public_profile.settings.require_2fa}")
        print(f"   Session Timeout: {public_profile.settings.session_timeout_minutes} min")
        print(f"   Audit Log Retention: {public_profile.settings.audit_log_retention_days} days")
        print(
            f"   Rate Limit: {public_profile.settings.max_requests} req/{public_profile.settings.rate_limit_window_seconds}s"
        )
        print(
            f"   Compliance Standards: {', '.join(s.value for s in public_profile.compliance_standards)}"
        )
    print()

    # 3. Apply a profile
    print("3. Applying Healthcare/HIPAA Profile:")
    print("-" * 80)
    result = manager.apply_profile("Healthcare/HIPAA")
    print(f"   Success: {result['success']}")
    print(f"   Profile: {result['profile']}")
    print(f"   Type: {result['profile_type']}")
    print(f"   Description: {result['description']}")
    print(f"   Compliance Standards: {', '.join(result['compliance_standards'])}")
    print()

    # 4. Validate a profile
    print("4. Validating Healthcare/HIPAA Profile:")
    print("-" * 80)
    validation = manager.validate_profile("Healthcare/HIPAA")
    print(f"   Valid: {validation['valid']}")
    if validation["errors"]:
        print("   Errors:")
        for error in validation["errors"]:
            print(f"      - {error}")
    if validation["warnings"]:
        print("   Warnings:")
        for warning in validation["warnings"]:
            print(f"      - {warning}")
    if validation["recommendations"]:
        print("   Recommendations:")
        for rec in validation["recommendations"]:
            print(f"      - {rec}")
    if not validation["errors"] and not validation["warnings"]:
        print("   No errors or warnings found!")
    print()

    # 5. Compare profiles
    print("5. Comparing Public Website vs Government/Federal:")
    print("-" * 80)
    comparison = manager.compare_profiles("Public Website", "Government/Federal")
    print(f"   Total differences: {comparison['total_differences']}")
    print("   Key differences:")
    for diff in comparison["differences"][:10]:  # Show first 10
        print(f"      - {diff['setting']}:")
        print(f"        Public Website: {diff['Public Website']}")
        print(f"        Government/Federal: {diff['Government/Federal']}")
    if len(comparison["differences"]) > 10:
        print(f"      ... and {len(comparison['differences']) - 10} more")
    print()

    # 6. View compliance requirements
    print("6. HIPAA Compliance Requirements:")
    print("-" * 80)
    hipaa_req = CompliancePresets.get_hipaa_requirements()
    print(f"   Standard: {hipaa_req.standard.value.upper()}")
    print(f"   Documentation: {hipaa_req.documentation_url}")
    print("   Key Requirements:")
    for req in hipaa_req.requirements[:5]:  # Show first 5
        print(f"      - {req}")
    print("   Mandatory Settings:")
    for key, value in list(hipaa_req.mandatory_settings.items())[:5]:
        print(f"      - {key}: {value}")
    print()

    # 7. Create a custom profile
    print("7. Creating Custom Profile:")
    print("-" * 80)
    custom_settings = SecuritySettings(
        min_password_length=14,
        require_2fa=True,
        session_timeout_minutes=25,
        audit_enabled=True,
        audit_log_retention_days=730,  # 2 years
        max_requests=75,
        rate_limit_window_seconds=60,
        require_2fa_for_roles={"admin", "manager", "editor"},
    )
    custom_profile = SecurityProfile(
        name="Custom Corporate Profile",
        profile_type=ProfileType.CUSTOM,
        description="Custom profile for corporate environment with specific requirements",
        settings=custom_settings,
        compliance_standards=[ComplianceStandard.SOC2, ComplianceStandard.GDPR],
    )
    manager.add_custom_profile(custom_profile)
    print(f"   Created: {custom_profile.name}")
    print(f"   Type: {custom_profile.profile_type.value}")
    print(f"   Description: {custom_profile.description}")

    # Validate the custom profile
    custom_validation = manager.validate_profile("Custom Corporate Profile")
    print(f"   Valid: {custom_validation['valid']}")
    if custom_validation["errors"]:
        print("   Errors:")
        for error in custom_validation["errors"]:
            print(f"      - {error}")
    print()

    # 8. Export and import a profile
    print("8. Exporting and Importing Profile:")
    print("-" * 80)
    json_export = manager.export_profile("Custom Corporate Profile")
    print(f"   Exported profile size: {len(json_export)} characters")
    print("   First 200 characters:")
    print(f"   {json_export[:200]}...")
    print()

    # 9. Show all profiles with their security levels
    print("9. Security Profile Comparison Matrix:")
    print("-" * 80)
    print(f"{'Profile':<25} {'2FA':<8} {'PW Len':<8} {'Session':<10} {'Audit Days':<12}")
    print("-" * 80)
    for profile_name in manager.list_profiles():
        profile = manager.get_profile(profile_name)
        if profile:
            print(
                f"{profile.name:<25} "
                f"{'Yes' if profile.settings.require_2fa else 'No':<8} "
                f"{profile.settings.min_password_length:<8} "
                f"{profile.settings.session_timeout_minutes} min{'':<5} "
                f"{profile.settings.audit_log_retention_days:<12}"
            )
    print()

    # 10. Show compliance standards summary
    print("10. Compliance Standards Summary:")
    print("-" * 80)
    standards = [
        ComplianceStandard.HIPAA,
        ComplianceStandard.PCI_DSS,
        ComplianceStandard.GDPR,
        ComplianceStandard.SOC2,
    ]
    for standard in standards:
        req = (
            CompliancePresets.get_hipaa_requirements()
            if standard == ComplianceStandard.HIPAA
            else (
                CompliancePresets.get_pci_dss_requirements()
                if standard == ComplianceStandard.PCI_DSS
                else (
                    CompliancePresets.get_gdpr_requirements()
                    if standard == ComplianceStandard.GDPR
                    else CompliancePresets.get_soc2_requirements()
                )
            )
        )
        print(f"   {standard.value.upper()}:")
        print(f"      Requirements: {len(req.requirements)}")
        print(f"      Mandatory Settings: {len(req.mandatory_settings)}")
        print(f"      Recommended Settings: {len(req.recommended_settings)}")
    print()

    print("=" * 80)
    print("Demo Complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()
