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
- Color blindness simulation filters (with HSL support)
- Screen reader preview mode (with ARIA live regions)
- Keyboard navigation testing (with WCAG 2.2 target size)
- Contrast ratio analyzer (extended color names)
- ARIA attribute validator (deprecated attribute detection)
- WCAG 2.1 and 2.2 compliance checker
- Accessibility score calculator

Enhanced Beyond Original Tools:
- HSL/HSLA color format support for color blindness simulation
- ARIA live regions detection and politeness tracking
- Modern CSS :focus-visible pseudo-class detection
- WCAG 2.2 target size checking (24x24px minimum)
- Extended named CSS colors (38+ colors)
- Deprecated ARIA attributes warning (aria-grabbed, aria-dropeffect)
- Prohibited ARIA role combination detection
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
