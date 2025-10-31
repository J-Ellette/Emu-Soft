"""
Safety Emulator - Python Dependency Vulnerability Scanner
Emulates Safety functionality for checking dependencies for known security vulnerabilities
"""

from .safety_emulator import (
    SafetyEmulator,
    VulnerabilityDatabase,
    Vulnerability,
    VulnerabilitySeverity,
    InsecurePackage,
    ScanResult,
)

__all__ = [
    'SafetyEmulator',
    'VulnerabilityDatabase',
    'Vulnerability',
    'VulnerabilitySeverity',
    'InsecurePackage',
    'ScanResult',
]

__version__ = '1.0.0'
