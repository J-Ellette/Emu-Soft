#!/usr/bin/env python
"""
Accessibility Simulation Tools Demo

Demonstrates the capabilities of the accessibility simulation tools.
"""

from mycms.accessibility import (
    ColorBlindnessSimulator,
    ScreenReaderSimulator,
    KeyboardNavigationTester,
    ContrastAnalyzer,
    ARIAValidator,
    WCAGComplianceChecker,
    AccessibilityScorer,
)


def print_section(title):
    """Print a formatted section header."""
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70 + "\n")


def demo_color_blindness():
    """Demonstrate color blindness simulation."""
    print_section("COLOR BLINDNESS SIMULATION")

    sim = ColorBlindnessSimulator()

    # Test color
    test_color = "#FF0000"  # Red
    print(f"Original color: {test_color}")
    print("\nSimulations:")

    for sim_type in ["protanopia", "deuteranopia", "tritanopia"]:
        simulated = sim.simulate_hex_color(test_color, sim_type)
        info = sim.get_simulation_info(sim_type)
        print(f"  {info['name']:20} {simulated:10} - {info['description']}")

    # Test CSS simulation
    print("\n\nCSS Simulation Example:")
    css = """
    .button {
        color: #FF0000;
        background-color: #00FF00;
    }
    """
    print("Original CSS:")
    print(css)

    simulated_css = sim.simulate_css(css, "deuteranopia")
    print("\nDeuteranopia simulation:")
    print(simulated_css)


def demo_screen_reader():
    """Demonstrate screen reader simulation."""
    print_section("SCREEN READER SIMULATION")

    sim = ScreenReaderSimulator()

    html = """
    <header>
        <h1>Welcome to Our Site</h1>
        <nav>
            <a href="#main">Skip to main content</a>
            <a href="/about">About</a>
            <a href="/contact">Contact</a>
        </nav>
    </header>
    <main id="main">
        <article>
            <h2>Article Title</h2>
            <p>This is the article content.</p>
            <img src="image.jpg" alt="A beautiful landscape">
        </article>
    </main>
    """

    print("HTML Content:")
    print(html)

    print("\n\nScreen Reader Output:")
    print("-" * 70)
    output = sim.get_screen_reader_output(html)
    print(output)

    print("\n\nHeading Structure:")
    headings = sim.get_heading_structure(html)
    for heading in headings:
        indent = "  " * (heading["level"] - 1)
        print(f"{indent}H{heading['level']}: {heading['text']}")

    print("\n\nAccessibility Issues Found:")
    issues = sim.check_accessibility_issues(html)
    if issues:
        for issue in issues:
            print(f"  [{issue['severity'].upper()}] {issue['message']}")
    else:
        print("  No issues found!")


def demo_keyboard_navigation():
    """Demonstrate keyboard navigation testing."""
    print_section("KEYBOARD NAVIGATION TESTING")

    tester = KeyboardNavigationTester()

    html = """
    <nav>
        <a href="#main">Skip to content</a>
        <a href="/home">Home</a>
        <button>Menu</button>
    </nav>
    <main id="main">
        <form>
            <input type="text" name="search" placeholder="Search">
            <button type="submit">Search</button>
        </form>
        <div onclick="alert('clicked')" tabindex="0">Clickable div</div>
    </main>
    """

    print("HTML Content:")
    print(html)

    print("\n\nKeyboard Accessibility Analysis:")
    print("-" * 70)
    result = tester.analyze_keyboard_accessibility(html)

    print(f"Focusable Elements: {result['focusable_elements']}")
    print(f"Score: {result['score']['score']}/100 (Grade: {result['score']['grade']})")
    print(f"Issues: {result['score']['errors']} errors, {result['score']['warnings']} warnings")

    print("\n\nTab Sequence:")
    sequence = tester.get_tab_sequence(html)
    for i, element in enumerate(sequence, 1):
        print(f"  {i}. {element}")

    print("\n\nIssues Found:")
    if result["issues"]:
        for issue in result["issues"]:
            print(f"  [{issue['severity'].upper()}] {issue['message']}")
    else:
        print("  No issues found!")


def demo_contrast_analyzer():
    """Demonstrate contrast analysis."""
    print_section("CONTRAST ANALYSIS")

    analyzer = ContrastAnalyzer()

    # Test color pairs
    test_pairs = [
        ("#000000", "#FFFFFF", "Black on White"),
        ("#0000FF", "#FFFFFF", "Blue on White"),
        ("#888888", "#999999", "Light Gray on Gray"),
        ("#FFFFFF", "#FF0000", "White on Red"),
    ]

    print("Color Contrast Analysis:")
    print("-" * 70)

    for fg, bg, description in test_pairs:
        result = analyzer.check_wcag_compliance(fg, bg)
        ratio = result["ratio_string"]
        aa_pass = "✓" if result["wcag_aa"]["pass"] else "✗"
        aaa_pass = "✓" if result["wcag_aaa"]["pass"] else "✗"

        print(f"\n{description}:")
        print(f"  Foreground: {fg}, Background: {bg}")
        print(f"  Contrast Ratio: {ratio}")
        print(f"  WCAG AA:  {aa_pass} (requires {result['wcag_aa']['required']}:1)")
        print(f"  WCAG AAA: {aaa_pass} (requires {result['wcag_aaa']['required']}:1)")
        print(f"  Recommendation: {result['recommendation']}")


def demo_aria_validator():
    """Demonstrate ARIA validation."""
    print_section("ARIA VALIDATION")

    validator = ARIAValidator()

    html = """
    <div role="button" aria-label="Close dialog">X</div>
    <div role="checkbox" aria-checked="true">Accept terms</div>
    <div role="invalid-role">Invalid</div>
    <button aria-expanded="true">Expand</button>
    <div role="slider">Slider without required attributes</div>
    """

    print("HTML Content:")
    print(html)

    print("\n\nARIA Validation Results:")
    print("-" * 70)
    result = validator.validate_html(html)

    print(f"Elements Checked: {result['elements_checked']}")
    print(f"Score: {result['score']['score']}/100 (Grade: {result['score']['grade']})")
    print(f"Issues: {result['errors']} errors, {result['warnings']} warnings")

    print("\n\nIssues Found:")
    if result["issues"]:
        for issue in result["issues"]:
            severity = issue["severity"].upper()
            print(f"  [{severity}] {issue['message']}")
    else:
        print("  No issues found!")


def demo_wcag_checker():
    """Demonstrate WCAG compliance checking."""
    print_section("WCAG 2.1 COMPLIANCE CHECKING")

    checker = WCAGComplianceChecker()

    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head><title>Test Page</title></head>
    <body>
        <header>
            <h1>Welcome</h1>
            <nav>
                <a href="/home">Home</a>
            </nav>
        </header>
        <main>
            <img src="test.jpg">
            <form>
                <input type="text" name="name">
                <button type="submit">Submit</button>
            </form>
        </main>
    </body>
    </html>
    """

    css = """
    body { color: #888; background: #999; }
    """

    print("Checking WCAG 2.1 Level AA compliance...")
    print("-" * 70)

    report = checker.generate_report(html, css, "AA")
    print(report)


def demo_accessibility_scorer():
    """Demonstrate accessibility scoring."""
    print_section("COMPREHENSIVE ACCESSIBILITY SCORING")

    scorer = AccessibilityScorer()

    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head><title>Test Page</title></head>
    <body>
        <header role="banner">
            <h1>Welcome</h1>
            <nav role="navigation">
                <a href="#main">Skip to main</a>
                <a href="/about">About</a>
            </nav>
        </header>
        <main id="main" role="main">
            <article>
                <h2>Article Title</h2>
                <p>Content goes here.</p>
                <img src="image.jpg" alt="Description">
            </article>
            <form>
                <label for="email">Email:</label>
                <input type="email" id="email" name="email" required>
                <button type="submit">Subscribe</button>
            </form>
        </main>
        <footer role="contentinfo">
            <p>Footer content</p>
        </footer>
    </body>
    </html>
    """

    css = """
    body { color: #000; background: #fff; }
    a { color: #0066cc; }
    a:focus { outline: 2px solid #000; }
    """

    print("Calculating comprehensive accessibility score...")
    print("-" * 70)

    report = scorer.generate_report(html, css, "AA")
    print(report)


def main():
    """Run all demonstrations."""
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 68 + "║")
    print("║" + "    ACCESSIBILITY SIMULATION TOOLS DEMONSTRATION".center(68) + "║")
    print("║" + " " * 68 + "║")
    print("╚" + "═" * 68 + "╝")

    # Run demonstrations
    demo_color_blindness()
    demo_screen_reader()
    demo_keyboard_navigation()
    demo_contrast_analyzer()
    demo_aria_validator()
    demo_wcag_checker()
    demo_accessibility_scorer()

    print("\n" + "=" * 70)
    print("DEMONSTRATION COMPLETE")
    print("=" * 70)
    print("\nAll accessibility simulation tools have been demonstrated.")
    print("These tools help ensure your content is accessible to all users.")
    print("\n")


if __name__ == "__main__":
    main()
