"""
Developed by PowerShield, as an alternative to Accessibility Testing
"""

"""
ARIA Attribute Validator

Validates ARIA (Accessible Rich Internet Applications) attributes for proper usage.

Inspired by:
- axe-core ARIA rules
- Chrome DevTools Accessibility Audits
- ARIA Authoring Practices Guide (APG)
"""

from typing import Dict, List, Set, Optional, Tuple
from html.parser import HTMLParser
import re


class ARIAValidator(HTMLParser):
    """
    Validates ARIA attributes for accessibility compliance.

    Validates:
    - Valid ARIA roles
    - Valid ARIA attributes
    - Required ARIA attributes for roles
    - ARIA attribute values
    - Implicit vs explicit roles
    - ARIA landmarks
    """

    # Valid ARIA roles
    VALID_ROLES = {
        # Widget roles
        "button",
        "checkbox",
        "gridcell",
        "link",
        "menuitem",
        "menuitemcheckbox",
        "menuitemradio",
        "option",
        "progressbar",
        "radio",
        "scrollbar",
        "searchbox",
        "slider",
        "spinbutton",
        "switch",
        "tab",
        "tabpanel",
        "textbox",
        "treeitem",
        # Composite roles
        "combobox",
        "grid",
        "listbox",
        "menu",
        "menubar",
        "radiogroup",
        "tablist",
        "tree",
        "treegrid",
        # Document structure roles
        "article",
        "cell",
        "columnheader",
        "definition",
        "directory",
        "document",
        "feed",
        "figure",
        "group",
        "heading",
        "img",
        "list",
        "listitem",
        "math",
        "none",
        "note",
        "presentation",
        "row",
        "rowgroup",
        "rowheader",
        "separator",
        "table",
        "term",
        "toolbar",
        "tooltip",
        # Landmark roles
        "banner",
        "complementary",
        "contentinfo",
        "form",
        "main",
        "navigation",
        "region",
        "search",
        # Live region roles
        "alert",
        "log",
        "marquee",
        "status",
        "timer",
        # Window roles
        "alertdialog",
        "dialog",
    }

    # Valid ARIA attributes
    VALID_ATTRIBUTES = {
        "aria-activedescendant",
        "aria-atomic",
        "aria-autocomplete",
        "aria-busy",
        "aria-checked",
        "aria-colcount",
        "aria-colindex",
        "aria-colspan",
        "aria-controls",
        "aria-current",
        "aria-describedby",
        "aria-details",
        "aria-disabled",
        "aria-errormessage",
        "aria-expanded",
        "aria-flowto",
        "aria-haspopup",
        "aria-hidden",
        "aria-invalid",
        "aria-keyshortcuts",
        "aria-label",
        "aria-labelledby",
        "aria-level",
        "aria-live",
        "aria-modal",
        "aria-multiline",
        "aria-multiselectable",
        "aria-orientation",
        "aria-owns",
        "aria-placeholder",
        "aria-posinset",
        "aria-pressed",
        "aria-readonly",
        "aria-relevant",
        "aria-required",
        "aria-roledescription",
        "aria-rowcount",
        "aria-rowindex",
        "aria-rowspan",
        "aria-selected",
        "aria-setsize",
        "aria-sort",
        "aria-valuemax",
        "aria-valuemin",
        "aria-valuenow",
        "aria-valuetext",
    }

    # Deprecated ARIA attributes (warn users about these)
    # Note: These are kept separate from VALID_ATTRIBUTES to provide deprecation warnings
    DEPRECATED_ATTRIBUTES = {
        "aria-grabbed": "Deprecated in ARIA 1.2, use drag-and-drop API instead",
        "aria-dropeffect": "Deprecated in ARIA 1.2, use drag-and-drop API instead",
    }

    # Prohibited roles for specific elements
    PROHIBITED_ROLES = {
        "button": {"link", "tab"},  # button element shouldn't have these roles
        "a": {"button"},  # links with href shouldn't be buttons
        "input": {"button"},  # use button element instead
    }

    # Required attributes for specific roles
    REQUIRED_ATTRIBUTES = {
        "checkbox": {"aria-checked"},
        "combobox": {"aria-controls", "aria-expanded"},
        "heading": {"aria-level"},
        "radio": {"aria-checked"},
        "scrollbar": {"aria-valuenow", "aria-valuemin", "aria-valuemax"},
        "slider": {"aria-valuenow", "aria-valuemin", "aria-valuemax"},
        "spinbutton": {"aria-valuenow", "aria-valuemin", "aria-valuemax"},
        "switch": {"aria-checked"},
    }

    # Implicit roles for HTML elements
    IMPLICIT_ROLES = {
        "a": "link",  # when has href
        "article": "article",
        "aside": "complementary",
        "button": "button",
        "footer": "contentinfo",
        "form": "form",
        "h1": "heading",
        "h2": "heading",
        "h3": "heading",
        "h4": "heading",
        "h5": "heading",
        "h6": "heading",
        "header": "banner",
        "input": {
            "button": "button",
            "checkbox": "checkbox",
            "radio": "radio",
            "text": "textbox",
            "search": "searchbox",
        },
        "li": "listitem",
        "main": "main",
        "nav": "navigation",
        "ol": "list",
        "section": "region",
        "ul": "list",
    }

    def __init__(self):
        """Initialize the ARIA validator."""
        super().__init__()
        self.issues = []
        self.elements = []
        self.landmarks = []
        self.element_stack = []

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]):
        """Handle opening tags."""
        attrs_dict = dict(attrs)

        element_info = {
            "tag": tag,
            "id": attrs_dict.get("id", ""),
            "class": attrs_dict.get("class", ""),
            "attrs": attrs_dict,
        }

        # Validate role attribute
        role = attrs_dict.get("role")
        if role:
            self._validate_role(tag, role, attrs_dict, element_info)

        # Validate ARIA attributes
        for attr_name in attrs_dict:
            if attr_name.startswith("aria-"):
                self._validate_aria_attribute(
                    tag, attr_name, attrs_dict[attr_name], role, element_info
                )

        # Check for required ARIA attributes
        if role and role in self.REQUIRED_ATTRIBUTES:
            self._check_required_attributes(role, attrs_dict, element_info)

        # Check for redundant explicit roles
        self._check_redundant_role(tag, role, attrs_dict, element_info)

        self.elements.append(element_info)
        self.element_stack.append(element_info)

    def handle_endtag(self, tag: str):
        """Handle closing tags."""
        if self.element_stack and self.element_stack[-1]["tag"] == tag:
            self.element_stack.pop()

    def _validate_role(self, tag: str, role: str, attrs: Dict, element_info: Dict):
        """Validate ARIA role."""
        # Check if role is valid
        if role not in self.VALID_ROLES:
            self.issues.append(
                {
                    "type": "invalid_role",
                    "severity": "error",
                    "message": f"Invalid ARIA role: '{role}'",
                    "element": element_info,
                    "wcag": "WCAG 2.1 Level A - 4.1.2 Name, Role, Value",
                }
            )

        # Check for prohibited role combinations
        if tag in self.PROHIBITED_ROLES and role in self.PROHIBITED_ROLES[tag]:
            self.issues.append(
                {
                    "type": "prohibited_role",
                    "severity": "error",
                    "message": f"Role '{role}' is not appropriate for {tag} element",
                    "element": element_info,
                    "wcag": "WCAG 2.1 Level A - 4.1.2 Name, Role, Value",
                    "recommendation": f"Use semantic HTML or a different role"
                }
            )

        # Check for role="presentation" or role="none" with interactive elements
        if role in ["presentation", "none"]:
            if tag in ["button", "a", "input", "select", "textarea"]:
                self.issues.append(
                    {
                        "type": "presentation_on_interactive",
                        "severity": "error",
                        "message": f"Interactive element {tag} should not have role='{role}'",
                        "element": element_info,
                        "wcag": "WCAG 2.1 Level A - 4.1.2 Name, Role, Value",
                    }
                )

    def _validate_aria_attribute(
        self, tag: str, attr_name: str, attr_value: str, role: Optional[str], element_info: Dict
    ):
        """Validate ARIA attribute."""
        # Check if attribute is deprecated first
        if attr_name in self.DEPRECATED_ATTRIBUTES:
            self.issues.append(
                {
                    "type": "deprecated_aria_attribute",
                    "severity": "warning",
                    "message": f"Deprecated ARIA attribute: '{attr_name}' - {self.DEPRECATED_ATTRIBUTES[attr_name]}",
                    "element": element_info,
                    "wcag": "Best Practice - Use modern ARIA patterns",
                }
            )
            # Don't also flag it as invalid since it's deprecated but still recognized
            return
        
        # Check if attribute is valid
        if attr_name not in self.VALID_ATTRIBUTES:
            self.issues.append(
                {
                    "type": "invalid_aria_attribute",
                    "severity": "warning",
                    "message": f"Invalid ARIA attribute: '{attr_name}'",
                    "element": element_info,
                    "wcag": "WCAG 2.1 Level A - 4.1.2 Name, Role, Value",
                }
            )
            return

        # Validate specific attribute values
        if attr_name == "aria-hidden":
            if attr_value not in ["true", "false"]:
                self.issues.append(
                    {
                        "type": "invalid_aria_value",
                        "severity": "error",
                        "message": f"aria-hidden must be 'true' or 'false', got '{attr_value}'",
                        "element": element_info,
                        "wcag": "WCAG 2.1 Level A - 4.1.2 Name, Role, Value",
                    }
                )

        elif attr_name == "aria-checked":
            if attr_value not in ["true", "false", "mixed"]:
                self.issues.append(
                    {
                        "type": "invalid_aria_value",
                        "severity": "error",
                        "message": f"aria-checked must be 'true', 'false', or 'mixed'",
                        "element": element_info,
                        "wcag": "WCAG 2.1 Level A - 4.1.2 Name, Role, Value",
                    }
                )

        elif attr_name == "aria-expanded":
            if attr_value not in ["true", "false"]:
                self.issues.append(
                    {
                        "type": "invalid_aria_value",
                        "severity": "error",
                        "message": f"aria-expanded must be 'true' or 'false'",
                        "element": element_info,
                        "wcag": "WCAG 2.1 Level A - 4.1.2 Name, Role, Value",
                    }
                )

        elif attr_name in ["aria-valuenow", "aria-valuemin", "aria-valuemax"]:
            try:
                float(attr_value)
            except ValueError:
                self.issues.append(
                    {
                        "type": "invalid_aria_value",
                        "severity": "error",
                        "message": f"{attr_name} must be a number",
                        "element": element_info,
                        "wcag": "WCAG 2.1 Level A - 4.1.2 Name, Role, Value",
                    }
                )

        elif attr_name == "aria-live":
            if attr_value not in ["off", "polite", "assertive"]:
                self.issues.append(
                    {
                        "type": "invalid_aria_value",
                        "severity": "error",
                        "message": f"aria-live must be 'off', 'polite', or 'assertive'",
                        "element": element_info,
                        "wcag": "WCAG 2.1 Level A - 4.1.2 Name, Role, Value",
                    }
                )

    def _check_required_attributes(self, role: str, attrs: Dict, element_info: Dict):
        """Check for required ARIA attributes."""
        required = self.REQUIRED_ATTRIBUTES.get(role, set())

        for required_attr in required:
            if required_attr not in attrs:
                self.issues.append(
                    {
                        "type": "missing_required_aria",
                        "severity": "error",
                        "message": f"Role '{role}' requires attribute '{required_attr}'",
                        "element": element_info,
                        "wcag": "WCAG 2.1 Level A - 4.1.2 Name, Role, Value",
                    }
                )

    def _check_redundant_role(self, tag: str, role: Optional[str], attrs: Dict, element_info: Dict):
        """Check for redundant explicit roles."""
        if not role:
            return

        # Get implicit role
        implicit_role = self.IMPLICIT_ROLES.get(tag)

        # Handle special cases
        if isinstance(implicit_role, dict):
            input_type = attrs.get("type", "text")
            implicit_role = implicit_role.get(input_type)

        # Check if role is redundant
        if implicit_role == role:
            self.issues.append(
                {
                    "type": "redundant_role",
                    "severity": "info",
                    "message": f"Role '{role}' is redundant for <{tag}> element",
                    "element": element_info,
                    "wcag": "Best Practice",
                }
            )

    def validate_html(self, html_content: str) -> Dict:
        """
        Validate ARIA attributes in HTML content.

        Args:
            html_content: HTML content to validate

        Returns:
            Dictionary with validation results
        """
        # Reset state
        self.issues = []
        self.elements = []
        self.landmarks = []
        self.element_stack = []

        # Parse HTML
        self.feed(html_content)

        # Additional checks
        self._check_landmark_structure()
        self._check_duplicate_ids()

        return {
            "issues": self.issues,
            "elements_checked": len(self.elements),
            "errors": len([i for i in self.issues if i["severity"] == "error"]),
            "warnings": len([i for i in self.issues if i["severity"] == "warning"]),
            "info": len([i for i in self.issues if i["severity"] == "info"]),
            "score": self._calculate_score(),
        }

    def _check_landmark_structure(self):
        """Check for proper landmark structure."""
        # Count landmark roles
        landmark_roles = ["banner", "navigation", "main", "complementary", "contentinfo"]
        role_counts = {role: 0 for role in landmark_roles}

        for element in self.elements:
            role = element["attrs"].get("role")
            if role in landmark_roles:
                role_counts[role] += 1

        # Check for missing main landmark
        if role_counts["main"] == 0:
            self.issues.append(
                {
                    "type": "missing_main_landmark",
                    "severity": "warning",
                    "message": "Page should have a 'main' landmark",
                    "wcag": "WCAG 2.1 Level A - 1.3.1 Info and Relationships",
                }
            )

        # Check for multiple main landmarks
        if role_counts["main"] > 1:
            self.issues.append(
                {
                    "type": "multiple_main_landmarks",
                    "severity": "error",
                    "message": f"Page has {role_counts['main']} 'main' landmarks, should have only one",
                    "wcag": "WCAG 2.1 Level A - 1.3.1 Info and Relationships",
                }
            )

    def _check_duplicate_ids(self):
        """Check for duplicate IDs referenced in ARIA attributes."""
        id_references = {}

        for element in self.elements:
            # Check aria-labelledby and aria-describedby
            for attr in ["aria-labelledby", "aria-describedby", "aria-controls"]:
                if attr in element["attrs"]:
                    ref_ids = element["attrs"][attr].split()
                    for ref_id in ref_ids:
                        if ref_id not in id_references:
                            id_references[ref_id] = []
                        id_references[ref_id].append(element)

        # Check if referenced IDs exist
        existing_ids = {elem["id"] for elem in self.elements if elem["id"]}

        for ref_id, elements in id_references.items():
            if ref_id not in existing_ids:
                for element in elements:
                    self.issues.append(
                        {
                            "type": "invalid_id_reference",
                            "severity": "error",
                            "message": f"ARIA attribute references non-existent ID: '{ref_id}'",
                            "element": element,
                            "wcag": "WCAG 2.1 Level A - 4.1.2 Name, Role, Value",
                        }
                    )

    def _calculate_score(self) -> Dict:
        """Calculate ARIA validation score."""
        total_score = 100
        deductions = 0

        for issue in self.issues:
            if issue["severity"] == "error":
                deductions += 10
            elif issue["severity"] == "warning":
                deductions += 5
            elif issue["severity"] == "info":
                deductions += 1

        score = max(0, total_score - deductions)

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

        return {"score": score, "grade": grade}
