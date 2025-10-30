"""
Bandit Emulator - Python Security Linter
Emulates Bandit functionality for security vulnerability detection
"""

from .bandit_emulator import (
    BanditEmulator,
    SecurityIssue,
    ScanResult,
    Severity,
    Confidence,
    BanditTest,
)

__all__ = [
    'BanditEmulator',
    'SecurityIssue',
    'ScanResult',
    'Severity',
    'Confidence',
    'BanditTest',
]

__version__ = '1.0.0'
