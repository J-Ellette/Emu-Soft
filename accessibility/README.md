# Accessibility Simulation Tools

Comprehensive accessibility testing and simulation tools to preview sites as seen by users with visual impairments or screen readers, ensuring WCAG 2.1 compliance.

## Overview

This module provides a complete suite of accessibility tools for testing, validating, and simulating how users with disabilities experience web content. **Enhanced beyond the original tools** with modern web standards support.

## Enhancements Beyond Original Tools

This implementation goes beyond the original tools it emulates:

1. **HSL/HSLA Color Support** - Color blindness simulator now handles modern HSL color formats, not just RGB/hex
2. **ARIA Live Regions** - Screen reader simulator detects and announces live region politeness levels
3. **Modern CSS Support** - Detects `:focus-visible` pseudo-class for better keyboard UX
4. **WCAG 2.2 Compliance** - Includes latest 2.2 success criteria like Target Size (Minimum)
5. **Extended Color Names** - Supports 38+ CSS named colors vs. original 18
6. **Deprecated ARIA Detection** - Warns about deprecated attributes like `aria-grabbed`
7. **Role Conflict Detection** - Identifies prohibited role combinations for semantic HTML

## Inspired By

- **axe DevTools** - Accessibility testing engine
- **WAVE** - Web Accessibility Evaluation Tool
- **Pa11y** - Automated accessibility testing
- **Lighthouse** - Accessibility audits
- **Chrome DevTools** - Accessibility features
- **Coblis** - Color Blindness Simulator
- **NVDA/JAWS** - Screen readers

## Features

### 1. Color Blindness Simulation

Simulates various types of color vision deficiencies to preview how users with color blindness see your content.

**Supported Types:**
- **Protanopia** - Red-blind (missing L-cones) - ~1% of males
- **Deuteranopia** - Green-blind (missing M-cones) - ~1% of males
- **Tritanopia** - Blue-blind (missing S-cones) - ~0.001% of population
- **Protanomaly** - Red-weak (anomalous L-cones) - ~1% of males
- **Deuteranomaly** - Green-weak (anomalous M-cones) - ~5% of males
- **Tritanomaly** - Blue-weak (anomalous S-cones) - Rare
- **Achromatopsia** - Complete color blindness - ~0.003% of population
- **Achromatomaly** - Partial color blindness - Rare

**Capabilities:**
- RGB to simulated RGB transformation
- Hex color simulation
- CSS color simulation (hex, rgb, rgba, hsl, hsla)
- HTML inline style simulation

### 2. Screen Reader Simulator

Simulates how screen readers interpret and announce web content.

**Features:**
- Text extraction in reading order
- ARIA label interpretation
- Alternative text extraction
- Semantic structure identification
- Heading hierarchy analysis
- Link and button identification
- Form element labeling
- Landmark region detection
- Accessibility issue detection

**Checks:**
- Images without alt text
- Empty links
- Heading hierarchy skips
- Form inputs without labels
- ARIA live regions presence

### 3. Keyboard Navigation Tester

Tests and validates keyboard navigation accessibility.

**Features:**
- Tab order analysis
- Focus management validation
- Skip link detection
- Keyboard trap detection
- Tabindex validation
- Focus indicator checking
- Interactive element accessibility

**Validates:**
- All interactive elements are keyboard accessible
- No positive tabindex (best practice)
- Skip navigation links present
- Focus order is logical
- No keyboard traps
- Modern :focus-visible support
- Target sizes meet WCAG 2.2 (24x24px)

### 4. Contrast Analyzer

Analyzes color contrast ratios for WCAG compliance.

**WCAG Requirements:**
- **Level AA**: 4.5:1 for normal text, 3:1 for large text
- **Level AAA**: 7:1 for normal text, 4.5:1 for large text
- **Large text**: 18pt+ or 14pt+ bold

**Features:**
- Color parsing (hex, rgb, rgba, named colors)
- Relative luminance calculation
- Contrast ratio calculation
- WCAG AA/AAA compliance checking
- CSS color combination analysis
- Foreground color suggestions
- Letter grade assignment

### 5. ARIA Validator

Validates ARIA (Accessible Rich Internet Applications) attributes.

**Validates:**
- Valid ARIA roles
- Valid ARIA attributes
- Required ARIA attributes for roles
- ARIA attribute values
- Implicit vs explicit roles
- ARIA landmark structure
- ID reference validity

**Checks:**
- Invalid roles
- Missing required attributes
- Invalid attribute values
- Redundant explicit roles
- Proper landmark usage
- Duplicate/missing ID references
- Deprecated ARIA attributes (aria-grabbed, aria-dropeffect)
- Prohibited role combinations

### 6. WCAG Compliance Checker

Comprehensive WCAG 2.1 and 2.2 compliance checking with live preview.

**WCAG 2.1 Principles (POUR):**
- **Perceivable** - Content must be perceivable
- **Operable** - Interface must be operable
- **Understandable** - Information must be understandable
- **Robust** - Content must be robust

**WCAG 2.2 New Success Criteria:**
- 2.5.8 Target Size (Minimum) - Interactive elements should be at least 24x24 CSS pixels

**Checks:**
- Level A requirements (must)
- Level AA requirements (should)
- Level AAA requirements (may)

**Guidelines Covered:**
- 1.1.1 Non-text Content (A)
- 1.3.1 Info and Relationships (A)
- 1.4.3 Contrast (Minimum) (AA)
- 1.4.6 Contrast (Enhanced) (AAA)
- 2.1.1 Keyboard (A)
- 2.1.2 No Keyboard Trap (A)
- 2.4.1 Bypass Blocks (A)
- 2.4.3 Focus Order (A)
- 2.4.4 Link Purpose (A)
- 2.4.7 Focus Visible (AA)
- 3.3.1 Error Identification (A)
- 3.3.2 Labels or Instructions (A)
- 4.1.2 Name, Role, Value (A)

### 7. Accessibility Scorer

Calculates comprehensive accessibility scores with actionable insights.

**Scoring Categories:**
- WCAG Compliance (40%)
- Color & Contrast (20%)
- Keyboard Navigation (20%)
- Screen Reader Compatibility (15%)
- ARIA Implementation (5%)

**Provides:**
- Overall score (0-100)
- Letter grade (A+ to F)
- WCAG level achieved
- Category-specific scores
- Prioritized issues
- Actionable recommendations

## Installation

The accessibility module can be imported directly:

```python
from accessibility import (
    ColorBlindnessSimulator,
    ScreenReaderSimulator,
    KeyboardNavigationTester,
    ContrastAnalyzer,
    ARIAValidator,
    WCAGComplianceChecker,
    AccessibilityScorer
)
```

## Quick Start

### Color Blindness Simulation

```python
from accessibility import ColorBlindnessSimulator

sim = ColorBlindnessSimulator()

# Simulate a color
simulated = sim.simulate_hex_color("#FF0000", "protanopia")
print(f"Red for protanopes: {simulated}")

# Simulate CSS
css = "color: #FF0000; background: #00FF00;"
simulated_css = sim.simulate_css(css, "deuteranopia")

# Simulate HTML
html = '<div style="color: #FF0000;">Red text</div>'
simulated_html = sim.simulate_html(html, "tritanopia")

# Get available simulation types
types = sim.get_simulation_types()
```

### Screen Reader Preview

```python
from accessibility import ScreenReaderSimulator

sim = ScreenReaderSimulator()

html = """
<h1>Welcome</h1>
<img src="logo.jpg" alt="Company Logo">
<a href="/about">About Us</a>
"""

# Get screen reader output
output = sim.get_screen_reader_output(html)
print(output)

# Extract headings
headings = sim.get_heading_structure(html)

# Extract links
links = sim.get_links(html)

# Check for issues
issues = sim.check_accessibility_issues(html)
```

### Keyboard Navigation Testing

```python
from accessibility import KeyboardNavigationTester

tester = KeyboardNavigationTester()

html = """
<nav>
    <a href="#main">Skip to content</a>
    <button>Menu</button>
</nav>
<main id="main">
    <input type="text" name="search">
</main>
"""

# Analyze keyboard accessibility
result = tester.analyze_keyboard_accessibility(html)
print(f"Score: {result['score']['score']}/100")
print(f"Issues: {result['issues']}")

# Get tab sequence
sequence = tester.get_tab_sequence(html)
```

### Contrast Analysis

```python
from accessibility import ContrastAnalyzer

analyzer = ContrastAnalyzer()

# Check contrast ratio
ratio = analyzer.calculate_contrast_ratio("#000000", "#FFFFFF")
print(f"Contrast ratio: {ratio:.2f}:1")

# Check WCAG compliance
result = analyzer.check_wcag_compliance(
    foreground="#0000FF",
    background="#FFFFFF",
    font_size_pt=14.0,
    is_bold=False
)

print(f"WCAG AA: {'Pass' if result['wcag_aa']['pass'] else 'Fail'}")
print(f"WCAG AAA: {'Pass' if result['wcag_aaa']['pass'] else 'Fail'}")

# Analyze CSS colors
css = "body { color: #333; background: #fff; }"
results = analyzer.analyze_css_colors(css)
```

### ARIA Validation

```python
from accessibility import ARIAValidator

validator = ARIAValidator()

html = """
<div role="button" aria-label="Close">X</div>
<div role="checkbox" aria-checked="true">Accept</div>
"""

# Validate ARIA
result = validator.validate_html(html)
print(f"Score: {result['score']['score']}/100")
print(f"Errors: {result['errors']}")
print(f"Warnings: {result['warnings']}")

for issue in result['issues']:
    print(f"[{issue['severity']}] {issue['message']}")
```

### WCAG Compliance Checking

```python
from accessibility import WCAGComplianceChecker

checker = WCAGComplianceChecker()

html = """
<!DOCTYPE html>
<html lang="en">
<body>
    <h1>Title</h1>
    <img src="test.jpg" alt="Description">
</body>
</html>
"""

css = "body { color: #000; background: #fff; }"

# Check compliance
result = checker.check_compliance(html, css, target_level="AA")
print(f"Compliance Rate: {result['summary']['compliance_rate']}%")
print(f"Is Compliant: {result['summary']['is_compliant']}")

# Generate report
report = checker.generate_report(html, css, "AA")
print(report)
```

### Comprehensive Accessibility Scoring

```python
from accessibility import AccessibilityScorer

scorer = AccessibilityScorer()

html = """
<!DOCTYPE html>
<html lang="en">
<body>
    <header role="banner">
        <h1>Welcome</h1>
    </header>
    <main role="main">
        <img src="test.jpg" alt="Description">
    </main>
</body>
</html>
"""

css = "body { color: #000; background: #fff; }"

# Calculate score
result = scorer.calculate_score(html, css, target_level="AA")
print(f"Score: {result['total_score']}/100")
print(f"Grade: {result['grade']}")
print(f"Level: {result['level_achieved']}")

# Generate report
report = scorer.generate_report(html, css, "AA")
print(report)
```

## Usage Examples

### Complete Page Audit

```python
from accessibility import AccessibilityScorer

scorer = AccessibilityScorer()

# Load your HTML and CSS
with open('page.html') as f:
    html = f.read()

with open('styles.css') as f:
    css = f.read()

# Get comprehensive report
report = scorer.generate_report(html, css, "AA")
print(report)

# Get detailed results
results = scorer.calculate_score(html, css, "AA")

# Act on priorities
for priority in results['priorities']:
    print(f"Priority: {priority}")

# Implement recommendations
for recommendation in results['recommendations']:
    print(f"TODO: {recommendation}")
```

### Preview for Different Users

```python
from accessibility import ColorBlindnessSimulator, ScreenReaderSimulator

# Load page
with open('page.html') as f:
    html = f.read()

# Preview for color blind users
color_sim = ColorBlindnessSimulator()
for sim_type in ['protanopia', 'deuteranopia', 'tritanopia']:
    simulated = color_sim.simulate_html(html, sim_type)
    with open(f'preview_{sim_type}.html', 'w') as f:
        f.write(simulated)

# Preview for screen reader users
screen_reader = ScreenReaderSimulator()
output = screen_reader.get_screen_reader_output(html)
with open('screen_reader_output.txt', 'w') as f:
    f.write(output)
```

## Testing

Run the comprehensive test suite:

```bash
pytest tests/test_accessibility.py -v
```

Test coverage includes:
- 30 comprehensive tests
- All simulation types
- All validation features
- Integration tests
- Comparison tests

## Demo

Run the demonstration script:

```bash
python examples/accessibility_demo.py
```

The demo showcases:
- Color blindness simulation
- Screen reader output
- Keyboard navigation analysis
- Contrast checking
- ARIA validation
- WCAG compliance checking
- Accessibility scoring

## Implementation Notes

### No External Dependencies

All tools are implemented using only Python standard library:
- `html.parser` for HTML parsing
- `re` for pattern matching
- `math` for calculations
- `typing` for type hints

This ensures:
- Zero external dependencies
- Fast performance
- Easy deployment
- Full control over functionality

### Accuracy

The tools use industry-standard algorithms:
- **Color blindness**: Brettel, Viénot and Mollon JPEG algorithm
- **Contrast**: WCAG 2.1 relative luminance formula
- **ARIA**: W3C ARIA 1.2 specification
- **WCAG**: WCAG 2.1 Level A/AA/AAA guidelines

### Performance

- Efficient HTML parsing with `HTMLParser`
- Optimized color calculations
- Minimal memory footprint
- Fast validation checks

## Best Practices

### 1. Test Early and Often

```python
# Check accessibility during development
scorer = AccessibilityScorer()
results = scorer.calculate_score(html, css)
assert results['total_score'] >= 80, "Accessibility score too low"
```

### 2. Target AA Compliance Minimum

```python
# Always target WCAG 2.1 Level AA at minimum
checker = WCAGComplianceChecker()
result = checker.check_compliance(html, css, "AA")
assert result['summary']['is_compliant'], "WCAG AA compliance required"
```

### 3. Test Multiple Simulations

```python
# Test for multiple color blindness types
sim = ColorBlindnessSimulator()
for sim_type in ['protanopia', 'deuteranopia', 'tritanopia']:
    simulated = sim.simulate_html(html, sim_type)
    # Verify content is still usable
```

### 4. Validate ARIA Carefully

```python
# ARIA can make things worse if used incorrectly
validator = ARIAValidator()
result = validator.validate_html(html)
if result['errors'] > 0:
    # Fix ARIA errors immediately
    pass
```

### 5. Monitor Score Trends

```python
# Track accessibility scores over time
scorer = AccessibilityScorer()
result = scorer.calculate_score(html, css)

# Log scores for monitoring
print(f"Date: {datetime.now()}, Score: {result['total_score']}")
```

## Limitations

### Static Analysis Only

These tools perform static analysis of HTML/CSS:
- Cannot detect dynamic JavaScript issues
- Cannot test actual user interactions
- Cannot measure real-time performance

For complete testing, supplement with:
- Manual testing with real screen readers
- Browser-based testing tools
- User testing with people with disabilities

### Color Blindness Approximation

Color blindness simulation is an approximation:
- Individual experiences vary
- Lighting conditions affect perception
- Some conditions are difficult to simulate perfectly

Always test with actual users when possible.

### WCAG Coverage

While comprehensive, not all WCAG criteria can be automatically checked:
- Some require manual verification
- Context-dependent guidelines need human judgment
- Behavioral aspects require interactive testing

## Future Enhancements

Potential future additions:
- Dynamic JavaScript analysis
- Automated remediation suggestions
- Integration with CI/CD pipelines
- Browser extension
- Visual diff tools
- PDF accessibility checking
- Mobile-specific checks

## Contributing

When adding new accessibility features:

1. Follow WCAG 2.1 guidelines
2. Use standard algorithms
3. Add comprehensive tests
4. Document thoroughly
5. Include examples
6. Update this README

## Resources

### Standards
- [WCAG 2.1](https://www.w3.org/TR/WCAG21/)
- [ARIA 1.2](https://www.w3.org/TR/wai-aria-1.2/)
- [HTML Accessibility](https://www.w3.org/TR/html-aria/)

### Tools
- [axe DevTools](https://www.deque.com/axe/)
- [WAVE](https://wave.webaim.org/)
- [Pa11y](https://pa11y.org/)
- [Lighthouse](https://developers.google.com/web/tools/lighthouse)

### Learning
- [WebAIM](https://webaim.org/)
- [A11y Project](https://www.a11yproject.com/)
- [MDN Accessibility](https://developer.mozilla.org/en-US/docs/Web/Accessibility)

## License

Part of the Emu-Soft collection, licensed under MIT License.

## Version History

- **1.0.0** (2025-10-30) - Initial release
  - Color blindness simulation (8 types)
  - Screen reader simulation
  - Keyboard navigation testing
  - Contrast analysis
  - ARIA validation
  - WCAG compliance checking
  - Accessibility scoring
  - Comprehensive test suite
  - Full documentation

---

*Last Updated: 2025-10-30*
