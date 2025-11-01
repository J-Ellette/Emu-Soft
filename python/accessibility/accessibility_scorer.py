"""
Developed by PowerShield, as an alternative to Accessibility Testing
"""

"""
Accessibility Scorer

Calculates comprehensive accessibility scores and provides actionable insights.

Inspired by:
- Lighthouse Accessibility Score
- axe DevTools Score
- WAVE Summary Score

Enhanced with:
- WCAG 2.2 compliance checking
- Modern CSS support (HSL, :focus-visible)
- Deprecated ARIA detection
- Live regions support
"""

from typing import Dict, List, Optional
from .wcag_checker import WCAGComplianceChecker
from .color_blindness import ColorBlindnessSimulator
from .screen_reader import ScreenReaderSimulator
from .keyboard_nav import KeyboardNavigationTester
from .contrast import ContrastAnalyzer
from .aria_validator import ARIAValidator


class AccessibilityScorer:
    """
    Calculates comprehensive accessibility scores.

    Scoring categories:
    - WCAG Compliance (40%)
    - Color & Contrast (20%)
    - Keyboard Navigation (20%)
    - Screen Reader Compatibility (15%)
    - ARIA Implementation (5%)
    """

    # Weights for different scoring categories
    CATEGORY_WEIGHTS = {
        "wcag_compliance": 0.40,
        "color_contrast": 0.20,
        "keyboard_navigation": 0.20,
        "screen_reader": 0.15,
        "aria_implementation": 0.05,
    }

    def __init__(self):
        """Initialize the accessibility scorer."""
        self.wcag_checker = WCAGComplianceChecker()
        self.color_sim = ColorBlindnessSimulator()
        self.screen_reader = ScreenReaderSimulator()
        self.keyboard_tester = KeyboardNavigationTester()
        self.contrast_analyzer = ContrastAnalyzer()
        self.aria_validator = ARIAValidator()

    def calculate_score(
        self, html_content: str, css_content: str = "", target_level: str = "AA"
    ) -> Dict:
        """
        Calculate comprehensive accessibility score.

        Args:
            html_content: HTML content to score
            css_content: CSS content to score
            target_level: Target WCAG level

        Returns:
            Dictionary with scores and breakdown
        """
        # Calculate individual category scores
        wcag_score = self._score_wcag_compliance(html_content, css_content, target_level)
        contrast_score = self._score_color_contrast(css_content)
        keyboard_score = self._score_keyboard_navigation(html_content, css_content)
        screen_reader_score = self._score_screen_reader(html_content)
        aria_score = self._score_aria_implementation(html_content)

        # Calculate weighted total score
        total_score = (
            wcag_score["score"] * self.CATEGORY_WEIGHTS["wcag_compliance"]
            + contrast_score["score"] * self.CATEGORY_WEIGHTS["color_contrast"]
            + keyboard_score["score"] * self.CATEGORY_WEIGHTS["keyboard_navigation"]
            + screen_reader_score["score"] * self.CATEGORY_WEIGHTS["screen_reader"]
            + aria_score["score"] * self.CATEGORY_WEIGHTS["aria_implementation"]
        )

        return {
            "total_score": round(total_score, 1),
            "grade": self._get_grade(total_score),
            "level_achieved": self._get_level_achieved(total_score),
            "categories": {
                "wcag_compliance": wcag_score,
                "color_contrast": contrast_score,
                "keyboard_navigation": keyboard_score,
                "screen_reader": screen_reader_score,
                "aria_implementation": aria_score,
            },
            "priorities": self._get_priorities(
                wcag_score, contrast_score, keyboard_score, screen_reader_score, aria_score
            ),
            "recommendations": self._get_recommendations(
                wcag_score, contrast_score, keyboard_score, screen_reader_score, aria_score
            ),
        }

    def _score_wcag_compliance(
        self, html_content: str, css_content: str, target_level: str
    ) -> Dict:
        """Score WCAG compliance."""
        results = self.wcag_checker.check_compliance(html_content, css_content, target_level)

        summary = results["summary"]
        compliance_rate = summary["compliance_rate"]

        return {
            "score": compliance_rate,
            "grade": summary["grade"],
            "errors": summary["errors"],
            "warnings": summary["warnings"],
            "details": f"{summary['errors']} errors, {summary['warnings']} warnings",
        }

    def _score_color_contrast(self, css_content: str) -> Dict:
        """Score color contrast."""
        if not css_content:
            return {"score": 100, "grade": "A", "details": "No CSS to analyze"}

        results = self.contrast_analyzer.analyze_css_colors(css_content)

        if not results:
            return {"score": 100, "grade": "A", "details": "No color combinations found"}

        # Count passes and fails
        aa_passes = sum(1 for r in results if r.get("wcag_aa", {}).get("pass", False))
        total = len(results)

        score = (aa_passes / total * 100) if total > 0 else 100

        fails = total - aa_passes

        return {
            "score": score,
            "grade": self._get_grade(score),
            "passes": aa_passes,
            "fails": fails,
            "details": f"{aa_passes}/{total} color combinations pass WCAG AA",
        }

    def _score_keyboard_navigation(self, html_content: str, css_content: str) -> Dict:
        """Score keyboard navigation."""
        results = self.keyboard_tester.analyze_keyboard_accessibility(html_content)

        score_info = results["score"]

        # Check focus indicators
        focus_issues = (
            self.keyboard_tester.test_focus_indicators(css_content) if css_content else []
        )

        # Deduct for focus issues
        focus_deduction = len(focus_issues) * 5
        adjusted_score = max(0, score_info["score"] - focus_deduction)

        return {
            "score": adjusted_score,
            "grade": score_info["grade"],
            "errors": score_info["errors"],
            "warnings": score_info["warnings"],
            "focusable_elements": results["focusable_elements"],
            "details": f"{score_info['errors']} errors, {score_info['warnings']} warnings",
        }

    def _score_screen_reader(self, html_content: str) -> Dict:
        """Score screen reader compatibility."""
        issues = self.screen_reader.check_accessibility_issues(html_content)

        # Start with perfect score
        score = 100

        # Deduct for issues
        for issue in issues:
            if issue["severity"] == "error":
                score -= 10
            elif issue["severity"] == "warning":
                score -= 5

        score = max(0, score)

        errors = len([i for i in issues if i["severity"] == "error"])
        warnings = len([i for i in issues if i["severity"] == "warning"])

        return {
            "score": score,
            "grade": self._get_grade(score),
            "errors": errors,
            "warnings": warnings,
            "details": f"{errors} errors, {warnings} warnings",
        }

    def _score_aria_implementation(self, html_content: str) -> Dict:
        """Score ARIA implementation."""
        results = self.aria_validator.validate_html(html_content)

        score_info = results["score"]

        return {
            "score": score_info["score"],
            "grade": score_info["grade"],
            "errors": results["errors"],
            "warnings": results["warnings"],
            "elements_checked": results["elements_checked"],
            "details": f"{results['errors']} errors, {results['warnings']} warnings",
        }

    def _get_grade(self, score: float) -> str:
        """Get letter grade for score."""
        if score >= 95:
            return "A+"
        elif score >= 90:
            return "A"
        elif score >= 85:
            return "A-"
        elif score >= 80:
            return "B+"
        elif score >= 75:
            return "B"
        elif score >= 70:
            return "B-"
        elif score >= 65:
            return "C+"
        elif score >= 60:
            return "C"
        elif score >= 50:
            return "D"
        else:
            return "F"

    def _get_level_achieved(self, score: float) -> str:
        """Get WCAG level achieved based on score."""
        if score >= 95:
            return "WCAG 2.1 AAA"
        elif score >= 85:
            return "WCAG 2.1 AA"
        elif score >= 70:
            return "WCAG 2.1 A"
        else:
            return "Non-compliant"

    def _get_priorities(
        self,
        wcag_score: Dict,
        contrast_score: Dict,
        keyboard_score: Dict,
        screen_reader_score: Dict,
        aria_score: Dict,
    ) -> List[str]:
        """Get prioritized list of areas to improve."""
        priorities = []

        # Find lowest scoring categories
        category_scores = [
            ("WCAG Compliance", wcag_score["score"], wcag_score),
            ("Color Contrast", contrast_score["score"], contrast_score),
            ("Keyboard Navigation", keyboard_score["score"], keyboard_score),
            ("Screen Reader", screen_reader_score["score"], screen_reader_score),
            ("ARIA Implementation", aria_score["score"], aria_score),
        ]

        # Sort by score (lowest first)
        category_scores.sort(key=lambda x: x[1])

        # Add top 3 priorities
        for name, score, details in category_scores[:3]:
            if score < 90:
                priorities.append(f"{name}: {score}/100 - {details.get('details', '')}")

        return priorities

    def _get_recommendations(
        self,
        wcag_score: Dict,
        contrast_score: Dict,
        keyboard_score: Dict,
        screen_reader_score: Dict,
        aria_score: Dict,
    ) -> List[str]:
        """Get specific recommendations."""
        recommendations = []

        # WCAG recommendations
        if wcag_score["errors"] > 0:
            recommendations.append(f"Fix {wcag_score['errors']} WCAG compliance errors")

        # Contrast recommendations
        if contrast_score.get("fails", 0) > 0:
            recommendations.append(
                f"Improve contrast for {contrast_score['fails']} color combinations"
            )

        # Keyboard recommendations
        if keyboard_score["errors"] > 0:
            recommendations.append(f"Fix {keyboard_score['errors']} keyboard navigation issues")

        # Screen reader recommendations
        if screen_reader_score["errors"] > 0:
            recommendations.append(
                f"Fix {screen_reader_score['errors']} screen reader compatibility issues"
            )

        # ARIA recommendations
        if aria_score["errors"] > 0:
            recommendations.append(f"Fix {aria_score['errors']} ARIA implementation errors")

        # Add general recommendations
        if not recommendations:
            recommendations.append("Great work! Your content is highly accessible.")

        return recommendations

    def generate_report(
        self, html_content: str, css_content: str = "", target_level: str = "AA"
    ) -> str:
        """
        Generate a comprehensive accessibility score report.

        Args:
            html_content: HTML content to score
            css_content: CSS content to score
            target_level: Target WCAG level

        Returns:
            Formatted text report
        """
        results = self.calculate_score(html_content, css_content, target_level)

        report = []
        report.append("=" * 60)
        report.append("ACCESSIBILITY SCORE REPORT")
        report.append("=" * 60)
        report.append("")

        # Overall score
        report.append(f"Overall Score: {results['total_score']}/100")
        report.append(f"Grade: {results['grade']}")
        report.append(f"Level Achieved: {results['level_achieved']}")
        report.append("")

        # Category breakdown
        report.append("CATEGORY SCORES")
        report.append("-" * 60)
        for category, details in results["categories"].items():
            category_name = category.replace("_", " ").title()
            weight = self.CATEGORY_WEIGHTS[category] * 100
            report.append(
                f"{category_name:30} {details['score']:5.1f}/100 "
                f"(Grade: {details['grade']}) [{weight:.0f}% weight]"
            )
            report.append(f"  {details['details']}")
        report.append("")

        # Priorities
        if results["priorities"]:
            report.append("TOP PRIORITIES")
            report.append("-" * 60)
            for i, priority in enumerate(results["priorities"], 1):
                report.append(f"{i}. {priority}")
            report.append("")

        # Recommendations
        if results["recommendations"]:
            report.append("RECOMMENDATIONS")
            report.append("-" * 60)
            for i, rec in enumerate(results["recommendations"], 1):
                report.append(f"{i}. {rec}")
            report.append("")

        report.append("=" * 60)

        return "\n".join(report)
