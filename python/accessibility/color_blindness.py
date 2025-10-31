"""
Color Blindness Simulation

Simulates various types of color vision deficiencies to preview how users
with color blindness see your content.

Inspired by:
- Chrome DevTools Color Vision Deficiency Emulation
- Colorblind Web Page Filter
- Coblis - Color Blindness Simulator
"""

from typing import Dict, Tuple, List, Optional
import re


class ColorBlindnessSimulator:
    """
    Simulates color blindness by applying transformation matrices to colors.

    Supports:
    - Protanopia (red-blind)
    - Deuteranopia (green-blind)
    - Tritanopia (blue-blind)
    - Protanomaly (red-weak)
    - Deuteranomaly (green-weak)
    - Tritanomaly (blue-weak)
    - Achromatopsia (complete color blindness)
    - Achromatomaly (partial color blindness)
    """

    # Transformation matrices for different color blindness types
    # Based on Brettel, Viénot and Mollon JPEG algorithm
    TRANSFORMATIONS = {
        "protanopia": [[0.567, 0.433, 0.0], [0.558, 0.442, 0.0], [0.0, 0.242, 0.758]],
        "deuteranopia": [[0.625, 0.375, 0.0], [0.7, 0.3, 0.0], [0.0, 0.3, 0.7]],
        "tritanopia": [[0.95, 0.05, 0.0], [0.0, 0.433, 0.567], [0.0, 0.475, 0.525]],
        "protanomaly": [[0.817, 0.183, 0.0], [0.333, 0.667, 0.0], [0.0, 0.125, 0.875]],
        "deuteranomaly": [[0.8, 0.2, 0.0], [0.258, 0.742, 0.0], [0.0, 0.142, 0.858]],
        "tritanomaly": [[0.967, 0.033, 0.0], [0.0, 0.733, 0.267], [0.0, 0.183, 0.817]],
        "achromatopsia": [[0.299, 0.587, 0.114], [0.299, 0.587, 0.114], [0.299, 0.587, 0.114]],
        "achromatomaly": [[0.618, 0.320, 0.062], [0.163, 0.775, 0.062], [0.163, 0.320, 0.516]],
    }

    def __init__(self):
        """Initialize the color blindness simulator."""
        self.simulation_type = "normal"

    def simulate_color(
        self, r: int, g: int, b: int, simulation_type: str = "protanopia"
    ) -> Tuple[int, int, int]:
        """
        Apply color blindness simulation to an RGB color.

        Args:
            r: Red component (0-255)
            g: Green component (0-255)
            b: Blue component (0-255)
            simulation_type: Type of color blindness to simulate

        Returns:
            Tuple of (r, g, b) simulated values
        """
        if simulation_type == "normal" or simulation_type not in self.TRANSFORMATIONS:
            return (r, g, b)

        # Normalize to 0-1 range
        r_norm = r / 255.0
        g_norm = g / 255.0
        b_norm = b / 255.0

        # Apply transformation matrix
        matrix = self.TRANSFORMATIONS[simulation_type]

        r_new = matrix[0][0] * r_norm + matrix[0][1] * g_norm + matrix[0][2] * b_norm
        g_new = matrix[1][0] * r_norm + matrix[1][1] * g_norm + matrix[1][2] * b_norm
        b_new = matrix[2][0] * r_norm + matrix[2][1] * g_norm + matrix[2][2] * b_norm

        # Clamp to 0-1 range and convert back to 0-255
        r_final = max(0, min(255, int(r_new * 255)))
        g_final = max(0, min(255, int(g_new * 255)))
        b_final = max(0, min(255, int(b_new * 255)))

        return (r_final, g_final, b_final)

    def simulate_hex_color(self, hex_color: str, simulation_type: str = "protanopia") -> str:
        """
        Apply color blindness simulation to a hex color.

        Args:
            hex_color: Hex color string (e.g., "#FF0000" or "FF0000")
            simulation_type: Type of color blindness to simulate

        Returns:
            Simulated hex color string
        """
        # Remove # if present
        hex_color = hex_color.lstrip("#")

        # Parse RGB values
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)

        # Simulate
        r_sim, g_sim, b_sim = self.simulate_color(r, g, b, simulation_type)

        # Convert back to hex
        return f"#{r_sim:02x}{g_sim:02x}{b_sim:02x}"

    def simulate_css(self, css_content: str, simulation_type: str = "protanopia") -> str:
        """
        Apply color blindness simulation to all colors in CSS content.

        Args:
            css_content: CSS content as string
            simulation_type: Type of color blindness to simulate

        Returns:
            Modified CSS with simulated colors
        """
        # Pattern to match hex colors in CSS
        hex_pattern = re.compile(r"#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})")

        def replace_hex(match):
            hex_color = match.group(0)
            # Expand 3-digit hex to 6-digit
            if len(hex_color) == 4:
                hex_color = f"#{hex_color[1]*2}{hex_color[2]*2}{hex_color[3]*2}"
            return self.simulate_hex_color(hex_color, simulation_type)

        css_content = hex_pattern.sub(replace_hex, css_content)

        # Pattern to match rgb() and rgba() colors
        rgb_pattern = re.compile(
            r"rgba?\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*(?:,\s*[\d.]+)?\s*\)"
        )

        def replace_rgb(match):
            r, g, b = int(match.group(1)), int(match.group(2)), int(match.group(3))
            r_sim, g_sim, b_sim = self.simulate_color(r, g, b, simulation_type)

            # Check if it was rgba
            if match.group(0).startswith("rgba"):
                alpha = match.group(0).split(",")[-1].strip().rstrip(")")
                return f"rgba({r_sim}, {g_sim}, {b_sim}, {alpha})"
            return f"rgb({r_sim}, {g_sim}, {b_sim})"

        css_content = rgb_pattern.sub(replace_rgb, css_content)

        # Pattern to match hsl() and hsla() colors - convert to RGB, simulate, convert back
        hsl_pattern = re.compile(
            r"hsla?\s*\(\s*([\d.]+)\s*,\s*([\d.]+)%\s*,\s*([\d.]+)%\s*(?:,\s*[\d.]+)?\s*\)"
        )

        def replace_hsl(match):
            h, s, l = float(match.group(1)), float(match.group(2)), float(match.group(3))
            r, g, b = self._hsl_to_rgb(h, s, l)
            r_sim, g_sim, b_sim = self.simulate_color(r, g, b, simulation_type)
            
            # Convert back to HSL for consistency
            h_sim, s_sim, l_sim = self._rgb_to_hsl(r_sim, g_sim, b_sim)
            
            # Check if it was hsla
            if match.group(0).startswith("hsla"):
                alpha = match.group(0).split(",")[-1].strip().rstrip(")")
                return f"hsla({h_sim:.0f}, {s_sim:.1f}%, {l_sim:.1f}%, {alpha})"
            return f"hsl({h_sim:.0f}, {s_sim:.1f}%, {l_sim:.1f}%)"

        css_content = hsl_pattern.sub(replace_hsl, css_content)

        return css_content

    def simulate_html(self, html_content: str, simulation_type: str = "protanopia") -> str:
        """
        Apply color blindness simulation to all inline colors in HTML.

        Args:
            html_content: HTML content as string
            simulation_type: Type of color blindness to simulate

        Returns:
            Modified HTML with simulated colors
        """
        # Find all style attributes and inline styles
        style_pattern = re.compile(r'style\s*=\s*["\']([^"\']*)["\']', re.IGNORECASE)

        def replace_style(match):
            style_content = match.group(1)
            simulated_style = self.simulate_css(style_content, simulation_type)
            quote = '"' if '"' in match.group(0) else "'"
            return f"style={quote}{simulated_style}{quote}"

        html_content = style_pattern.sub(replace_style, html_content)

        # Also handle bgcolor and color attributes
        color_attr_pattern = re.compile(
            r'(bgcolor|color)\s*=\s*["\']#([0-9a-fA-F]{6})["\']', re.IGNORECASE
        )

        def replace_color_attr(match):
            attr_name = match.group(1)
            hex_color = f"#{match.group(2)}"
            simulated = self.simulate_hex_color(hex_color, simulation_type)
            quote = '"' if '"' in match.group(0) else "'"
            return f"{attr_name}={quote}{simulated}{quote}"

        html_content = color_attr_pattern.sub(replace_color_attr, html_content)

        return html_content

    def get_simulation_types(self) -> List[str]:
        """Get list of available simulation types."""
        return list(self.TRANSFORMATIONS.keys())

    def get_simulation_info(self, simulation_type: str) -> Dict[str, str]:
        """
        Get information about a simulation type.

        Args:
            simulation_type: Type of color blindness

        Returns:
            Dictionary with name, description, and prevalence
        """
        info = {
            "protanopia": {
                "name": "Protanopia",
                "description": "Red-blind (missing L-cones)",
                "prevalence": "~1% of males",
                "severity": "severe",
            },
            "deuteranopia": {
                "name": "Deuteranopia",
                "description": "Green-blind (missing M-cones)",
                "prevalence": "~1% of males",
                "severity": "severe",
            },
            "tritanopia": {
                "name": "Tritanopia",
                "description": "Blue-blind (missing S-cones)",
                "prevalence": "~0.001% of population",
                "severity": "severe",
            },
            "protanomaly": {
                "name": "Protanomaly",
                "description": "Red-weak (anomalous L-cones)",
                "prevalence": "~1% of males",
                "severity": "mild",
            },
            "deuteranomaly": {
                "name": "Deuteranomaly",
                "description": "Green-weak (anomalous M-cones)",
                "prevalence": "~5% of males",
                "severity": "mild",
            },
            "tritanomaly": {
                "name": "Tritanomaly",
                "description": "Blue-weak (anomalous S-cones)",
                "prevalence": "Rare",
                "severity": "mild",
            },
            "achromatopsia": {
                "name": "Achromatopsia",
                "description": "Complete color blindness (no color perception)",
                "prevalence": "~0.003% of population",
                "severity": "complete",
            },
            "achromatomaly": {
                "name": "Achromatomaly",
                "description": "Partial color blindness (reduced color perception)",
                "prevalence": "Rare",
                "severity": "moderate",
            },
        }

        return info.get(
            simulation_type,
            {
                "name": "Unknown",
                "description": "Unknown color blindness type",
                "prevalence": "Unknown",
                "severity": "unknown",
            },
        )

    def _hsl_to_rgb(self, h: float, s: float, l: float) -> Tuple[int, int, int]:
        """
        Convert HSL to RGB.
        
        Args:
            h: Hue (0-360)
            s: Saturation (0-100)
            l: Lightness (0-100)
            
        Returns:
            RGB tuple (0-255 for each component)
        """
        h = h / 360.0
        s = s / 100.0
        l = l / 100.0
        
        if s == 0:
            # Achromatic (gray)
            r = g = b = l
        else:
            def hue_to_rgb(p, q, t):
                if t < 0:
                    t += 1
                if t > 1:
                    t -= 1
                if t < 1/6:
                    return p + (q - p) * 6 * t
                if t < 1/2:
                    return q
                if t < 2/3:
                    return p + (q - p) * (2/3 - t) * 6
                return p
            
            q = l * (1 + s) if l < 0.5 else l + s - l * s
            p = 2 * l - q
            r = hue_to_rgb(p, q, h + 1/3)
            g = hue_to_rgb(p, q, h)
            b = hue_to_rgb(p, q, h - 1/3)
        
        return (int(round(r * 255)), int(round(g * 255)), int(round(b * 255)))
    
    def _rgb_to_hsl(self, r: int, g: int, b: int) -> Tuple[float, float, float]:
        """
        Convert RGB to HSL.
        
        Args:
            r: Red (0-255)
            g: Green (0-255)
            b: Blue (0-255)
            
        Returns:
            HSL tuple (h: 0-360, s: 0-100, l: 0-100)
        """
        r = r / 255.0
        g = g / 255.0
        b = b / 255.0
        
        max_c = max(r, g, b)
        min_c = min(r, g, b)
        l = (max_c + min_c) / 2.0
        
        if max_c == min_c:
            h = s = 0.0  # Achromatic
        else:
            d = max_c - min_c
            s = d / (2.0 - max_c - min_c) if l > 0.5 else d / (max_c + min_c)
            
            if max_c == r:
                h = (g - b) / d + (6 if g < b else 0)
            elif max_c == g:
                h = (b - r) / d + 2
            else:
                h = (r - g) / d + 4
            h /= 6
        
        return (h * 360, s * 100, l * 100)
