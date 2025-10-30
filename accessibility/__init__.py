"""
Accessibility Simulation Tools

This module provides comprehensive accessibility testing and simulation tools
to preview sites as seen by users with visual impairments or screen readers.

Inspired by:
- axe DevTools
- WAVE (Web Accessibility Evaluation Tool)
- Pa11y
- Lighthouse Accessibility Audits

Key Features:
- Color blindness simulation filters
- Screen reader preview mode
- Keyboard navigation testing
- Contrast ratio analyzer
- ARIA attribute validator
- WCAG compliance checker
- Accessibility score calculator
"""

from .color_blindness import ColorBlindnessSimulator
from .screen_reader import ScreenReaderSimulator
from .keyboard_nav import KeyboardNavigationTester
from .contrast import ContrastAnalyzer
from .aria_validator import ARIAValidator
from .wcag_checker import WCAGComplianceChecker
from .accessibility_scorer import AccessibilityScorer

__all__ = [
    "ColorBlindnessSimulator",
    "ScreenReaderSimulator",
    "KeyboardNavigationTester",
    "ContrastAnalyzer",
    "ARIAValidator",
    "WCAGComplianceChecker",
    "AccessibilityScorer",
]

__version__ = "1.0.0"
