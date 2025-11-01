"""
Developed by PowerShield, as an alternative to Accessibility Testing
"""

"""
Keyboard Navigation Tester

Tests and validates keyboard navigation accessibility,
ensuring all interactive elements are keyboard accessible.

Inspired by:
- axe Keyboard Testing
- Chrome DevTools Accessibility Testing
- Accessibility Insights Keyboard Testing
"""

from typing import Dict, List, Set, Optional, Tuple
from html.parser import HTMLParser
import re


class KeyboardNavigationTester(HTMLParser):
    """
    Tests keyboard navigation accessibility.

    Validates:
    - Tab order and focus management
    - Keyboard traps
    - Skip links
    - Focus indicators
    - ARIA keyboard patterns
    - Interactive element accessibility
    """

    # Elements that should be keyboard accessible
    INTERACTIVE_ELEMENTS = {
        "a",
        "button",
        "input",
        "select",
        "textarea",
        "details",
        "summary",
        "video",
        "audio",
    }

    # Elements that can receive tabindex
    FOCUSABLE_ELEMENTS = INTERACTIVE_ELEMENTS | {"div", "span", "li", "td", "th"}

    # ARIA roles that should be keyboard accessible
    INTERACTIVE_ROLES = {
        "button",
        "link",
        "checkbox",
        "radio",
        "tab",
        "menuitem",
        "menuitemcheckbox",
        "menuitemradio",
        "option",
        "switch",
        "textbox",
        "searchbox",
        "combobox",
        "slider",
        "spinbutton",
        "listbox",
        "grid",
        "tree",
        "treegrid",
    }

    def __init__(self):
        """Initialize the keyboard navigation tester."""
        super().__init__()
        self.focusable_elements = []
        self.tab_order = []
        self.skip_links = []
        self.keyboard_traps = []
        self.issues = []
        self.element_stack = []
        self.current_tabindex = 0

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]):
        """Handle opening tags."""
        attrs_dict = dict(attrs)

        # Check if element is or should be focusable
        is_interactive = tag in self.INTERACTIVE_ELEMENTS
        has_interactive_role = attrs_dict.get("role") in self.INTERACTIVE_ROLES
        has_onclick = "onclick" in attrs_dict
        has_tabindex = "tabindex" in attrs_dict

        tabindex_value = attrs_dict.get("tabindex", "0" if is_interactive else None)

        # Parse tabindex
        try:
            tabindex = int(tabindex_value) if tabindex_value else None
        except (ValueError, TypeError):
            tabindex = None

        # Check if element should be in tab order
        should_be_focusable = is_interactive or has_interactive_role or has_onclick or has_tabindex

        if should_be_focusable:
            element_info = {
                "tag": tag,
                "id": attrs_dict.get("id", ""),
                "class": attrs_dict.get("class", ""),
                "role": attrs_dict.get("role", ""),
                "tabindex": tabindex,
                "aria_label": attrs_dict.get("aria-label", ""),
                "onclick": has_onclick,
                "href": attrs_dict.get("href", ""),
                "disabled": "disabled" in attrs_dict,
                "aria_hidden": attrs_dict.get("aria-hidden") == "true",
            }

            self.focusable_elements.append(element_info)

            # Build tab order
            if (
                tabindex is not None
                and not element_info["disabled"]
                and not element_info["aria_hidden"]
            ):
                if tabindex >= 0:
                    self.tab_order.append(
                        {
                            "element": element_info,
                            "tabindex": tabindex,
                            "natural_order": len(self.focusable_elements),
                        }
                    )

        # Check for skip links
        if tag == "a" and attrs_dict.get("href", "").startswith("#"):
            link_text = attrs_dict.get("aria-label", "")
            if "skip" in link_text.lower() or attrs_dict.get("class", "").find("skip") >= 0:
                self.skip_links.append(
                    {
                        "href": attrs_dict.get("href"),
                        "text": link_text,
                        "id": attrs_dict.get("id", ""),
                    }
                )

        # Check for potential keyboard traps
        if has_tabindex and tabindex == -1 and is_interactive:
            self.keyboard_traps.append(
                {
                    "tag": tag,
                    "id": attrs_dict.get("id", ""),
                    "reason": 'Interactive element with tabindex="-1"',
                }
            )

        self.element_stack.append(tag)

    def handle_endtag(self, tag: str):
        """Handle closing tags."""
        if self.element_stack and self.element_stack[-1] == tag:
            self.element_stack.pop()

    def analyze_keyboard_accessibility(self, html_content: str) -> Dict:
        """
        Analyze keyboard accessibility of HTML content.

        Args:
            html_content: HTML content to analyze

        Returns:
            Dictionary with analysis results
        """
        # Reset state
        self.focusable_elements = []
        self.tab_order = []
        self.skip_links = []
        self.keyboard_traps = []
        self.issues = []
        self.element_stack = []

        # Parse HTML
        self.feed(html_content)

        # Analyze results
        self._check_tab_order()
        self._check_focusable_elements()
        self._check_skip_links()
        self._check_keyboard_traps()

        return {
            "focusable_elements": len(self.focusable_elements),
            "tab_order": self._get_sorted_tab_order(),
            "skip_links": self.skip_links,
            "issues": self.issues,
            "score": self._calculate_score(),
        }

    def _get_sorted_tab_order(self) -> List[Dict]:
        """Get tab order sorted by tabindex and natural order."""
        # Sort by tabindex (positive first), then by natural order
        positive_tabindex = sorted(
            [item for item in self.tab_order if item["tabindex"] > 0],
            key=lambda x: (x["tabindex"], x["natural_order"]),
        )

        natural_order = sorted(
            [item for item in self.tab_order if item["tabindex"] == 0],
            key=lambda x: x["natural_order"],
        )

        return positive_tabindex + natural_order

    def _check_tab_order(self):
        """Check for tab order issues."""
        sorted_order = self._get_sorted_tab_order()

        # Check for positive tabindex (generally not recommended)
        positive_tabindex = [item for item in sorted_order if item["tabindex"] > 0]
        if positive_tabindex:
            self.issues.append(
                {
                    "type": "positive_tabindex",
                    "severity": "warning",
                    "message": f"Found {len(positive_tabindex)} elements with positive tabindex",
                    "detail": "Positive tabindex values can create confusing tab order",
                    "wcag": "WCAG 2.1 Level A - 2.4.3 Focus Order",
                    "count": len(positive_tabindex),
                }
            )

        # Check for large tabindex gaps
        if len(positive_tabindex) > 1:
            tabindices = [item["tabindex"] for item in positive_tabindex]
            for i in range(len(tabindices) - 1):
                if tabindices[i + 1] - tabindices[i] > 10:
                    self.issues.append(
                        {
                            "type": "tabindex_gap",
                            "severity": "warning",
                            "message": f"Large gap in tabindex values: {tabindices[i]} to {tabindices[i+1]}",
                            "wcag": "WCAG 2.1 Level A - 2.4.3 Focus Order",
                        }
                    )

    def _check_focusable_elements(self):
        """Check focusable elements for accessibility issues."""
        for element in self.focusable_elements:
            # Check for onclick without keyboard handler
            if element["onclick"] and element["tag"] not in self.INTERACTIVE_ELEMENTS:
                if element["tabindex"] is None or element["tabindex"] < 0:
                    self.issues.append(
                        {
                            "type": "non_keyboard_accessible",
                            "severity": "error",
                            "message": f"{element['tag']} with onclick is not keyboard accessible",
                            "element": element,
                            "wcag": "WCAG 2.1 Level A - 2.1.1 Keyboard",
                        }
                    )

            # Check for links without href
            if element["tag"] == "a" and not element["href"]:
                self.issues.append(
                    {
                        "type": "link_without_href",
                        "severity": "error",
                        "message": "Link without href attribute is not keyboard accessible",
                        "element": element,
                        "wcag": "WCAG 2.1 Level A - 2.1.1 Keyboard",
                    }
                )

            # Check for buttons without accessible name
            if element["tag"] == "button" and not element["aria_label"]:
                self.issues.append(
                    {
                        "type": "button_without_label",
                        "severity": "warning",
                        "message": "Button without accessible label",
                        "element": element,
                        "wcag": "WCAG 2.1 Level A - 4.1.2 Name, Role, Value",
                    }
                )

            # Check for hidden interactive elements
            if element["aria_hidden"] and element["tabindex"] != -1:
                self.issues.append(
                    {
                        "type": "hidden_focusable",
                        "severity": "error",
                        "message": "Element with aria-hidden='true' is still focusable",
                        "element": element,
                        "wcag": "WCAG 2.1 Level A - 4.1.2 Name, Role, Value",
                    }
                )

    def _check_skip_links(self):
        """Check for skip link presence and validity."""
        if not self.skip_links:
            self.issues.append(
                {
                    "type": "missing_skip_link",
                    "severity": "warning",
                    "message": "No skip link found for keyboard navigation",
                    "detail": "Skip links help keyboard users bypass repetitive content",
                    "wcag": "WCAG 2.1 Level A - 2.4.1 Bypass Blocks",
                }
            )

        # Check if skip link targets exist
        target_ids = set()
        for element in self.focusable_elements:
            if element["id"]:
                target_ids.add(element["id"])

        for skip_link in self.skip_links:
            target = skip_link["href"].lstrip("#")
            if target and target not in target_ids:
                self.issues.append(
                    {
                        "type": "invalid_skip_link",
                        "severity": "error",
                        "message": f"Skip link target not found: #{target}",
                        "wcag": "WCAG 2.1 Level A - 2.4.1 Bypass Blocks",
                    }
                )

    def _check_keyboard_traps(self):
        """Check for potential keyboard traps."""
        # Keyboard traps are complex to detect statically
        # We check for suspicious patterns

        if self.keyboard_traps:
            for trap in self.keyboard_traps:
                self.issues.append(
                    {
                        "type": "potential_keyboard_trap",
                        "severity": "warning",
                        "message": trap["reason"],
                        "element": trap,
                        "wcag": "WCAG 2.1 Level A - 2.1.2 No Keyboard Trap",
                    }
                )

    def _calculate_score(self) -> Dict:
        """Calculate keyboard accessibility score."""
        total_score = 100
        deductions = 0

        # Deduct points for issues
        for issue in self.issues:
            if issue["severity"] == "error":
                deductions += 10
            elif issue["severity"] == "warning":
                deductions += 5

        score = max(0, total_score - deductions)

        # Determine grade
        if score >= 90:
            grade = "A"
        elif score >= 80:
            grade = "B"
        elif score >= 70:
            grade = "C"
        elif score >= 60:
            grade = "D"
        else:
            grade = "F"

        return {
            "score": score,
            "grade": grade,
            "total_issues": len(self.issues),
            "errors": len([i for i in self.issues if i["severity"] == "error"]),
            "warnings": len([i for i in self.issues if i["severity"] == "warning"]),
        }

    def get_tab_sequence(self, html_content: str) -> List[str]:
        """
        Get the tab sequence as strings describing each focusable element.

        Args:
            html_content: HTML content to analyze

        Returns:
            List of strings describing tab sequence
        """
        result = self.analyze_keyboard_accessibility(html_content)

        sequence = []
        for item in result["tab_order"]:
            element = item["element"]
            desc = f"{element['tag']}"
            if element["id"]:
                desc += f"#{element['id']}"
            if element["aria_label"]:
                desc += f" ({element['aria_label']})"
            elif element["role"]:
                desc += f" [role={element['role']}]"
            sequence.append(desc)

        return sequence

    def test_focus_indicators(self, css_content: str) -> List[Dict]:
        """
        Test for focus indicator styles.

        Args:
            css_content: CSS content to analyze

        Returns:
            List of issues with focus indicators
        """
        issues = []

        # Check for :focus styles
        has_focus_styles = ":focus" in css_content.lower()
        has_focus_visible = ":focus-visible" in css_content.lower()
        has_outline_none = re.search(r"outline\s*:\s*none", css_content, re.IGNORECASE)
        has_custom_focus = re.search(
            r":focus\s*{[^}]*(border|box-shadow|background)", css_content, re.IGNORECASE
        )

        if has_outline_none and not has_custom_focus and not has_focus_visible:
            issues.append(
                {
                    "type": "missing_focus_indicator",
                    "severity": "error",
                    "message": "outline:none used without custom focus styles",
                    "wcag": "WCAG 2.1 Level AA - 2.4.7 Focus Visible",
                }
            )

        if not has_focus_styles and not has_focus_visible:
            issues.append(
                {
                    "type": "no_focus_styles",
                    "severity": "warning",
                    "message": "No :focus or :focus-visible styles found in CSS",
                    "wcag": "WCAG 2.1 Level AA - 2.4.7 Focus Visible",
                }
            )
        
        # Recommend using :focus-visible for better UX
        if has_focus_styles and not has_focus_visible:
            issues.append(
                {
                    "type": "missing_focus_visible",
                    "severity": "info",
                    "message": "Consider using :focus-visible for better mouse/keyboard UX distinction",
                    "wcag": "Best Practice - Enhanced Focus Indicators",
                }
            )

        return issues

    def check_target_size(self, html_content: str, css_content: str = "") -> List[Dict]:
        """
        Check for adequate target sizes for interactive elements (WCAG 2.2).
        
        WCAG 2.2 - 2.5.8 Target Size (Minimum) Level AA:
        Interactive elements should be at least 24x24 CSS pixels.
        
        Args:
            html_content: HTML content to analyze
            css_content: CSS content for size checking (optional)
            
        Returns:
            List of issues with target sizes
        """
        issues = []
        
        # This is a basic check - in practice would need actual rendered sizes
        # We'll check for explicit width/height in inline styles as a heuristic
        small_targets = re.findall(
            r'<(button|a|input)[^>]*style=["\'][^"\']*(?:width|height)\s*:\s*([0-9.]+)(?:px|rem|em)[^"\']*["\']',
            html_content,
            re.IGNORECASE
        )
        
        for tag, size_str in small_targets:
            try:
                size = float(size_str)
                if size < 24:
                    issues.append({
                        "type": "small_target_size",
                        "severity": "warning",
                        "message": f"Interactive element ({tag}) may be smaller than 24px minimum",
                        "wcag": "WCAG 2.2 Level AA - 2.5.8 Target Size (Minimum)",
                        "size": size
                    })
            except ValueError:
                pass
        
        return issues
