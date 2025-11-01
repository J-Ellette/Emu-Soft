"""
Developed by PowerShield, as an alternative to Accessibility Testing
"""

"""
Contrast Analyzer

Analyzes color contrast ratios for accessibility compliance with WCAG guidelines.

Inspired by:
- WebAIM Contrast Checker
- Colour Contrast Analyser (CCA)
- Chrome DevTools Contrast Ratio
"""

from typing import Dict, List, Tuple, Optional
import re
import math


class ContrastAnalyzer:
    """
    Analyzes color contrast ratios for WCAG compliance.

    WCAG 2.1 Requirements:
    - Level AA: 4.5:1 for normal text, 3:1 for large text
    - Level AAA: 7:1 for normal text, 4.5:1 for large text
    - Large text: 18pt+ or 14pt+ bold
    """

    # WCAG contrast ratio requirements
    WCAG_AA_NORMAL = 4.5
    WCAG_AA_LARGE = 3.0
    WCAG_AAA_NORMAL = 7.0
    WCAG_AAA_LARGE = 4.5

    # Named colors mapping (extended CSS named colors for better coverage)
    NAMED_COLORS = {
        "black": "#000000",
        "white": "#ffffff",
        "red": "#ff0000",
        "green": "#008000",
        "blue": "#0000ff",
        "yellow": "#ffff00",
        "cyan": "#00ffff",
        "magenta": "#ff00ff",
        "silver": "#c0c0c0",
        "gray": "#808080",
        "maroon": "#800000",
        "olive": "#808000",
        "lime": "#00ff00",
        "aqua": "#00ffff",
        "teal": "#008080",
        "navy": "#000080",
        "fuchsia": "#ff00ff",
        "purple": "#800080",
        # Extended color names
        "orange": "#ffa500",
        "pink": "#ffc0cb",
        "brown": "#a52a2a",
        "gold": "#ffd700",
        "indigo": "#4b0082",
        "violet": "#ee82ee",
        "tan": "#d2b48c",
        "beige": "#f5f5dc",
        "coral": "#ff7f50",
        "crimson": "#dc143c",
        "darkblue": "#00008b",
        "darkgreen": "#006400",
        "darkred": "#8b0000",
        "lightblue": "#add8e6",
        "lightgreen": "#90ee90",
        "lightgray": "#d3d3d3",
        "darkgray": "#a9a9a9",
        "whitesmoke": "#f5f5f5",
        "snow": "#fffafa",
        "ivory": "#fffff0",
    }

    def __init__(self):
        """Initialize the contrast analyzer."""
        pass

    def parse_color(self, color_str: str) -> Optional[Tuple[int, int, int]]:
        """
        Parse color string to RGB tuple.

        Args:
            color_str: Color string (hex, rgb, rgba, or named color)

        Returns:
            RGB tuple (r, g, b) or None if invalid
        """
        color_str = color_str.strip().lower()

        # Handle named colors
        if color_str in self.NAMED_COLORS:
            color_str = self.NAMED_COLORS[color_str]

        # Handle hex colors
        if color_str.startswith("#"):
            hex_color = color_str.lstrip("#")

            # Expand 3-digit hex to 6-digit
            if len(hex_color) == 3:
                hex_color = "".join([c * 2 for c in hex_color])

            if len(hex_color) == 6:
                try:
                    r = int(hex_color[0:2], 16)
                    g = int(hex_color[2:4], 16)
                    b = int(hex_color[4:6], 16)
                    return (r, g, b)
                except ValueError:
                    return None

        # Handle rgb() and rgba()
        rgb_match = re.match(
            r"rgba?\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*(?:,\s*[\d.]+)?\s*\)", color_str
        )
        if rgb_match:
            r = int(rgb_match.group(1))
            g = int(rgb_match.group(2))
            b = int(rgb_match.group(3))
            return (r, g, b)

        return None

    def get_relative_luminance(self, r: int, g: int, b: int) -> float:
        """
        Calculate relative luminance according to WCAG formula.

        Args:
            r: Red component (0-255)
            g: Green component (0-255)
            b: Blue component (0-255)

        Returns:
            Relative luminance value (0-1)
        """
        # Normalize to 0-1
        r_srgb = r / 255.0
        g_srgb = g / 255.0
        b_srgb = b / 255.0

        # Apply sRGB to linear RGB conversion
        def to_linear(c):
            if c <= 0.03928:
                return c / 12.92
            else:
                return math.pow((c + 0.055) / 1.055, 2.4)

        r_linear = to_linear(r_srgb)
        g_linear = to_linear(g_srgb)
        b_linear = to_linear(b_srgb)

        # Calculate relative luminance
        luminance = 0.2126 * r_linear + 0.7152 * g_linear + 0.0722 * b_linear

        return luminance

    def calculate_contrast_ratio(self, color1: str, color2: str) -> Optional[float]:
        """
        Calculate contrast ratio between two colors.

        Args:
            color1: First color (foreground)
            color2: Second color (background)

        Returns:
            Contrast ratio or None if colors are invalid
        """
        rgb1 = self.parse_color(color1)
        rgb2 = self.parse_color(color2)

        if not rgb1 or not rgb2:
            return None

        l1 = self.get_relative_luminance(*rgb1)
        l2 = self.get_relative_luminance(*rgb2)

        # Ensure l1 is the lighter color
        if l1 < l2:
            l1, l2 = l2, l1

        # Calculate contrast ratio
        ratio = (l1 + 0.05) / (l2 + 0.05)

        return ratio

    def check_wcag_compliance(
        self, foreground: str, background: str, font_size_pt: float = 12.0, is_bold: bool = False
    ) -> Dict:
        """
        Check WCAG compliance for a color combination.

        Args:
            foreground: Foreground color
            background: Background color
            font_size_pt: Font size in points
            is_bold: Whether text is bold

        Returns:
            Dictionary with compliance results
        """
        ratio = self.calculate_contrast_ratio(foreground, background)

        if ratio is None:
            return {"valid": False, "error": "Invalid color format"}

        # Determine if text is "large"
        is_large_text = (font_size_pt >= 18.0) or (font_size_pt >= 14.0 and is_bold)

        # Check compliance levels
        if is_large_text:
            aa_pass = ratio >= self.WCAG_AA_LARGE
            aaa_pass = ratio >= self.WCAG_AAA_LARGE
            required_aa = self.WCAG_AA_LARGE
            required_aaa = self.WCAG_AAA_LARGE
        else:
            aa_pass = ratio >= self.WCAG_AA_NORMAL
            aaa_pass = ratio >= self.WCAG_AAA_NORMAL
            required_aa = self.WCAG_AA_NORMAL
            required_aaa = self.WCAG_AAA_NORMAL

        return {
            "valid": True,
            "ratio": round(ratio, 2),
            "ratio_string": f"{ratio:.2f}:1",
            "is_large_text": is_large_text,
            "wcag_aa": {"pass": aa_pass, "required": required_aa},
            "wcag_aaa": {"pass": aaa_pass, "required": required_aaa},
            "recommendation": self._get_recommendation(ratio, is_large_text),
        }

    def _get_recommendation(self, ratio: float, is_large_text: bool) -> str:
        """Get recommendation based on contrast ratio."""
        required = self.WCAG_AA_LARGE if is_large_text else self.WCAG_AA_NORMAL

        if ratio >= self.WCAG_AAA_NORMAL:
            return "Excellent - Passes WCAG AAA"
        elif ratio >= self.WCAG_AA_NORMAL:
            return "Good - Passes WCAG AA"
        elif ratio >= required:
            return "Adequate - Meets minimum requirements"
        else:
            return "Poor - Does not meet WCAG requirements"

    def suggest_foreground_colors(self, background: str, target_ratio: float = 4.5) -> List[Dict]:
        """
        Suggest foreground colors that meet contrast requirements.

        Args:
            background: Background color
            target_ratio: Target contrast ratio

        Returns:
            List of suggested colors
        """
        bg_rgb = self.parse_color(background)
        if not bg_rgb:
            return []

        bg_luminance = self.get_relative_luminance(*bg_rgb)

        suggestions = []

        # Calculate required luminance for target ratio
        # For lighter foreground: (L1 + 0.05) / (bg_luminance + 0.05) = target_ratio
        # L1 = target_ratio * (bg_luminance + 0.05) - 0.05

        # For darker foreground: (bg_luminance + 0.05) / (L2 + 0.05) = target_ratio
        # L2 = (bg_luminance + 0.05) / target_ratio - 0.05

        lighter_luminance = target_ratio * (bg_luminance + 0.05) - 0.05
        darker_luminance = (bg_luminance + 0.05) / target_ratio - 0.05

        # Suggest black or white as safe choices
        if lighter_luminance <= 1.0:
            suggestions.append(
                {
                    "color": "#ffffff",
                    "name": "White",
                    "ratio": self.calculate_contrast_ratio("#ffffff", background),
                }
            )

        if darker_luminance >= 0.0:
            suggestions.append(
                {
                    "color": "#000000",
                    "name": "Black",
                    "ratio": self.calculate_contrast_ratio("#000000", background),
                }
            )

        return suggestions

    def analyze_css_colors(self, css_content: str) -> List[Dict]:
        """
        Analyze color combinations in CSS for contrast issues.

        Args:
            css_content: CSS content to analyze

        Returns:
            List of color combinations with contrast analysis
        """
        results = []

        # Find rules with both color and background-color
        rule_pattern = re.compile(r"([^{]+)\s*\{([^}]+)\}", re.MULTILINE | re.DOTALL)

        for match in rule_pattern.finditer(css_content):
            selector = match.group(1).strip()
            rules = match.group(2)

            # Extract color and background-color
            color_match = re.search(r"color\s*:\s*([^;]+)", rules, re.IGNORECASE)
            bg_match = re.search(r"background(?:-color)?\s*:\s*([^;]+)", rules, re.IGNORECASE)

            if color_match and bg_match:
                foreground = color_match.group(1).strip()
                background = bg_match.group(1).strip()

                # Extract font-size if present
                font_size = 12.0
                font_size_match = re.search(r"font-size\s*:\s*(\d+)pt", rules, re.IGNORECASE)
                if font_size_match:
                    font_size = float(font_size_match.group(1))

                # Check if bold
                is_bold = (
                    re.search(r"font-weight\s*:\s*bold", rules, re.IGNORECASE) is not None
                    or re.search(r"font-weight\s*:\s*[6-9]00", rules, re.IGNORECASE) is not None
                )

                compliance = self.check_wcag_compliance(foreground, background, font_size, is_bold)

                if compliance.get("valid"):
                    results.append(
                        {
                            "selector": selector,
                            "foreground": foreground,
                            "background": background,
                            "font_size_pt": font_size,
                            "is_bold": is_bold,
                            **compliance,
                        }
                    )

        return results

    def get_contrast_grade(self, ratio: float) -> str:
        """
        Get letter grade for contrast ratio.

        Args:
            ratio: Contrast ratio

        Returns:
            Letter grade (A+, A, B, C, D, F)
        """
        if ratio >= 7.0:
            return "A+"
        elif ratio >= 4.5:
            return "A"
        elif ratio >= 3.0:
            return "B"
        elif ratio >= 2.5:
            return "C"
        elif ratio >= 2.0:
            return "D"
        else:
            return "F"
