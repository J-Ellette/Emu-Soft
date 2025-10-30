"""
Screen Reader Simulator

Simulates how screen readers interpret and announce web content,
helping developers understand the user experience for visually impaired users.

Inspired by:
- NVDA (NonVisual Desktop Access)
- JAWS (Job Access With Speech)
- VoiceOver
- ChromeVox
"""

from typing import Dict, List, Tuple, Optional
from html.parser import HTMLParser
import re


class ScreenReaderSimulator(HTMLParser):
    """
    Simulates screen reader interpretation of HTML content.

    Provides:
    - Text extraction in reading order
    - ARIA label interpretation
    - Alternative text extraction
    - Semantic structure identification
    - Heading hierarchy analysis
    - Link and button identification
    - Form element labeling
    """

    # Elements that are typically skipped by screen readers
    SKIP_ELEMENTS = {"script", "style", "noscript", "template", "svg", "path"}

    # Interactive elements
    INTERACTIVE_ELEMENTS = {"a", "button", "input", "select", "textarea", "details", "summary"}

    # Landmark elements
    LANDMARK_ELEMENTS = {"header", "nav", "main", "aside", "footer", "section", "article", "form"}

    def __init__(self):
        """Initialize the screen reader simulator."""
        super().__init__()
        self.output = []
        self.current_element = None
        self.element_stack = []
        self.skip_content = False
        self.in_link = False
        self.link_text = []
        self.headings = []
        self.links = []
        self.landmarks = []
        self.form_elements = []
        self.images = []
        self.semantic_structure = []

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]):
        """Handle opening tags."""
        attrs_dict = dict(attrs)

        # Skip content in certain elements
        if tag in self.SKIP_ELEMENTS:
            self.skip_content = True
            return

        # Check for aria-hidden
        if attrs_dict.get("aria-hidden") == "true":
            self.skip_content = True
            return

        self.element_stack.append(tag)

        # Handle landmarks
        if tag in self.LANDMARK_ELEMENTS:
            landmark_name = attrs_dict.get("aria-label") or self._get_landmark_name(tag)
            self.landmarks.append({"type": tag, "name": landmark_name})
            self.output.append(f"[Landmark: {landmark_name}]")

        # Handle role attribute
        role = attrs_dict.get("role")
        if role:
            role_label = attrs_dict.get("aria-label") or role
            self.output.append(f"[Role: {role_label}]")

        # Handle headings
        if tag in ["h1", "h2", "h3", "h4", "h5", "h6"]:
            level = tag[1]
            self.headings.append({"level": int(level), "text": "", "position": len(self.output)})
            self.output.append(f"[Heading level {level}]")

        # Handle links
        if tag == "a":
            self.in_link = True
            self.link_text = []
            href = attrs_dict.get("href", "")
            aria_label = attrs_dict.get("aria-label")
            if aria_label:
                self.output.append(f"[Link: {aria_label}]")
            else:
                self.output.append("[Link:")

        # Handle images
        if tag == "img":
            alt = attrs_dict.get("alt", "")
            aria_label = attrs_dict.get("aria-label", "")
            label = aria_label or alt

            self.images.append(
                {"alt": alt, "aria_label": aria_label, "src": attrs_dict.get("src", "")}
            )

            if label:
                self.output.append(f"[Image: {label}]")
            else:
                self.output.append("[Image without alternative text]")

        # Handle buttons
        if tag == "button":
            aria_label = attrs_dict.get("aria-label")
            if aria_label:
                self.output.append(f"[Button: {aria_label}]")
            else:
                self.output.append("[Button:")

        # Handle form inputs
        if tag == "input":
            input_type = attrs_dict.get("type", "text")
            aria_label = attrs_dict.get("aria-label")
            placeholder = attrs_dict.get("placeholder", "")
            name = attrs_dict.get("name", "")

            label = aria_label or placeholder or name

            self.form_elements.append(
                {
                    "type": input_type,
                    "label": label,
                    "name": name,
                    "required": "required" in attrs_dict,
                }
            )

            required_text = " (required)" if "required" in attrs_dict else ""
            self.output.append(f"[Input {input_type}: {label}{required_text}]")

        # Handle labels
        if tag == "label":
            for_attr = attrs_dict.get("for")
            if for_attr:
                self.output.append(f"[Label for {for_attr}:")

        # Handle select
        if tag == "select":
            aria_label = attrs_dict.get("aria-label")
            name = attrs_dict.get("name", "")
            label = aria_label or name
            self.output.append(f"[Select {label}]")

        # Handle lists
        if tag == "ul":
            self.output.append("[List]")
        elif tag == "ol":
            self.output.append("[Ordered List]")
        elif tag == "li":
            self.output.append("[List item]")

        # Handle tables
        if tag == "table":
            caption = attrs_dict.get("aria-label")
            if caption:
                self.output.append(f"[Table: {caption}]")
            else:
                self.output.append("[Table]")
        elif tag == "th":
            self.output.append("[Table header:")
        elif tag == "td":
            self.output.append("[Table cell:")

        # Handle dialog/modal
        if role == "dialog" or role == "alertdialog":
            aria_label = attrs_dict.get("aria-label", "Dialog")
            self.output.append(f"[Dialog opened: {aria_label}]")

    def handle_endtag(self, tag: str):
        """Handle closing tags."""
        if tag in self.SKIP_ELEMENTS:
            self.skip_content = False
            return

        if self.element_stack and self.element_stack[-1] == tag:
            self.element_stack.pop()

        # Handle link end
        if tag == "a" and self.in_link:
            self.in_link = False
            link_text = " ".join(self.link_text).strip()
            if link_text:
                self.links.append(link_text)
                self.output.append(f"{link_text}]")
            else:
                self.output.append("Unlabeled link]")

        # Close labels, buttons, table cells
        if tag in ["label", "button", "th", "td"]:
            if self.output and not self.output[-1].endswith("]"):
                self.output.append("]")

    def handle_data(self, data: str):
        """Handle text content."""
        if self.skip_content:
            return

        data = data.strip()
        if not data:
            return

        # Track link text
        if self.in_link:
            self.link_text.append(data)

        # Add text to output
        self.output.append(data)

        # Track heading text
        if self.element_stack and self.element_stack[-1] in ["h1", "h2", "h3", "h4", "h5", "h6"]:
            if self.headings:
                self.headings[-1]["text"] = data

    def _get_landmark_name(self, tag: str) -> str:
        """Get default landmark name for a tag."""
        landmark_names = {
            "header": "banner",
            "nav": "navigation",
            "main": "main content",
            "aside": "complementary",
            "footer": "content information",
            "section": "section",
            "article": "article",
            "form": "form",
        }
        return landmark_names.get(tag, tag)

    def get_screen_reader_output(self, html_content: str) -> str:
        """
        Get simulated screen reader output.

        Args:
            html_content: HTML content to parse

        Returns:
            Screen reader output as text
        """
        self.output = []
        self.headings = []
        self.links = []
        self.landmarks = []
        self.form_elements = []
        self.images = []
        self.element_stack = []
        self.skip_content = False
        self.in_link = False
        self.link_text = []

        self.feed(html_content)

        return "\n".join(self.output)

    def get_heading_structure(self, html_content: str) -> List[Dict]:
        """
        Extract heading structure for navigation.

        Args:
            html_content: HTML content to parse

        Returns:
            List of headings with level and text
        """
        self.get_screen_reader_output(html_content)
        return self.headings

    def get_landmarks(self, html_content: str) -> List[Dict]:
        """
        Extract landmark regions.

        Args:
            html_content: HTML content to parse

        Returns:
            List of landmarks
        """
        self.get_screen_reader_output(html_content)
        return self.landmarks

    def get_links(self, html_content: str) -> List[str]:
        """
        Extract all links.

        Args:
            html_content: HTML content to parse

        Returns:
            List of link texts
        """
        self.get_screen_reader_output(html_content)
        return self.links

    def get_form_elements(self, html_content: str) -> List[Dict]:
        """
        Extract form elements with labels.

        Args:
            html_content: HTML content to parse

        Returns:
            List of form elements
        """
        self.get_screen_reader_output(html_content)
        return self.form_elements

    def get_images(self, html_content: str) -> List[Dict]:
        """
        Extract images with alt text.

        Args:
            html_content: HTML content to parse

        Returns:
            List of images with alt text
        """
        self.get_screen_reader_output(html_content)
        return self.images

    def check_accessibility_issues(self, html_content: str) -> List[Dict]:
        """
        Check for common accessibility issues.

        Args:
            html_content: HTML content to check

        Returns:
            List of accessibility issues found
        """
        self.get_screen_reader_output(html_content)

        issues = []

        # Check for images without alt text
        for img in self.images:
            if not img["alt"] and not img["aria_label"]:
                issues.append(
                    {
                        "type": "missing_alt_text",
                        "severity": "error",
                        "message": f"Image missing alt text: {img['src']}",
                        "wcag": "WCAG 2.1 Level A - 1.1.1 Non-text Content",
                    }
                )

        # Check for empty links
        if any(link == "" for link in self.links):
            issues.append(
                {
                    "type": "empty_link",
                    "severity": "error",
                    "message": "Link with no accessible text found",
                    "wcag": "WCAG 2.1 Level A - 2.4.4 Link Purpose",
                }
            )

        # Check heading hierarchy
        if self.headings:
            prev_level = 0
            for heading in self.headings:
                if heading["level"] > prev_level + 1:
                    issues.append(
                        {
                            "type": "heading_skip",
                            "severity": "warning",
                            "message": f"Heading level skipped: h{prev_level} to h{heading['level']}",
                            "wcag": "WCAG 2.1 Level A - 1.3.1 Info and Relationships",
                        }
                    )
                prev_level = heading["level"]

        # Check for form inputs without labels
        for form_elem in self.form_elements:
            if not form_elem["label"]:
                issues.append(
                    {
                        "type": "unlabeled_input",
                        "severity": "error",
                        "message": f"Form input without label: {form_elem['type']} ({form_elem['name']})",
                        "wcag": "WCAG 2.1 Level A - 1.3.1 Info and Relationships",
                    }
                )

        return issues
