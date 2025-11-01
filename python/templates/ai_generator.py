"""
Developed by PowerShield, as an alternative to Django Templates
"""

"""AI-powered template generation helpers.

This module provides utilities for AI-assisted template generation,
including pattern analysis, template suggestions, and auto-completion.
"""

from typing import Dict, List, Any, Optional
import re


class TemplatePattern:
    """Represents a recognized template pattern."""

    def __init__(
        self,
        name: str,
        description: str,
        template: str,
        variables: Optional[List[str]] = None,
    ) -> None:
        """Initialize a template pattern.

        Args:
            name: Pattern name
            description: Pattern description
            template: Template string
            variables: List of expected variables
        """
        self.name = name
        self.description = description
        self.template = template
        self.variables = variables or []


class AITemplateGenerator:
    """AI-powered template generator with pattern recognition and suggestions."""

    def __init__(self) -> None:
        """Initialize the AI template generator."""
        self.patterns: Dict[str, TemplatePattern] = {}
        self._load_default_patterns()

    def _load_default_patterns(self) -> None:
        """Load default template patterns."""
        # Blog post pattern
        self.register_pattern(
            TemplatePattern(
                name="blog_post",
                description="Standard blog post layout with header, content, and metadata",
                template="""
<article class="usa-prose">
    <header>
        <h1>{{ title }}</h1>
        <p class="text-base-dark">
            Published on {{ publish_date|date_format:"%B %d, %Y" }}
            {% if author %}by {{ author }}{% endif %}
        </p>
    </header>
    <div class="content">
        {{ content|safe }}
    </div>
    {% if tags %}
    <footer>
        <p>Tags:
            {% for tag in tags %}
                <span class="usa-tag">{{ tag }}</span>
            {% endfor %}
        </p>
    </footer>
    {% endif %}
</article>
""".strip(),
                variables=["title", "publish_date", "author", "content", "tags"],
            )
        )

        # Landing page hero pattern
        self.register_pattern(
            TemplatePattern(
                name="hero_section",
                description="Hero section for landing pages with call-to-action",
                template="""
<section class="usa-hero">
    <div class="grid-container">
        <div class="usa-hero__callout">
            <h1 class="usa-hero__heading">{{ heading }}</h1>
            <p>{{ tagline }}</p>
            {% if cta_text and cta_url %}
            <a class="usa-button usa-button--big" href="{{ cta_url }}">{{ cta_text }}</a>
            {% endif %}
        </div>
    </div>
</section>
""".strip(),
                variables=["heading", "tagline", "cta_text", "cta_url"],
            )
        )

        # Card grid pattern
        self.register_pattern(
            TemplatePattern(
                name="card_grid",
                description="Grid of cards for displaying multiple items",
                template="""
<div class="grid-container">
    <div class="grid-row grid-gap">
        {% for item in items %}
        <div class="tablet:grid-col-4">
            <div class="usa-card">
                <div class="usa-card__container">
                    <div class="usa-card__body">
                        <h3 class="usa-card__heading">{{ item.title }}</h3>
                        <p>{{ item.description }}</p>
                        {% if item.link %}
                        <a href="{{ item.link }}" class="usa-button">Learn more</a>
                        {% endif %}
                    </div>
                </div>
            </div>
        </div>
        {% endfor %}
    </div>
</div>
""".strip(),
                variables=["items"],
            )
        )

        # Form pattern
        self.register_pattern(
            TemplatePattern(
                name="contact_form",
                description="Standard contact form with USWDS styling",
                template="""
<form class="usa-form usa-form--large" method="post" action="{{ action_url }}">
    <fieldset class="usa-fieldset">
        <legend class="usa-legend usa-legend--large">{{ form_title }}</legend>

        <label class="usa-label" for="name">Full name</label>
        <input class="usa-input" id="name" name="name" type="text" required />

        <label class="usa-label" for="email">Email address</label>
        <input class="usa-input" id="email" name="email" type="email" required />

        <label class="usa-label" for="message">Message</label>
        <textarea class="usa-textarea" id="message" name="message" required></textarea>

        <button type="submit" class="usa-button">{{ submit_text|default:"Send" }}</button>
    </fieldset>
</form>
""".strip(),
                variables=["action_url", "form_title", "submit_text"],
            )
        )

    def register_pattern(self, pattern: TemplatePattern) -> None:
        """Register a new template pattern.

        Args:
            pattern: Template pattern to register
        """
        self.patterns[pattern.name] = pattern

    def get_pattern(self, name: str) -> Optional[TemplatePattern]:
        """Get a template pattern by name.

        Args:
            name: Pattern name

        Returns:
            TemplatePattern or None if not found
        """
        return self.patterns.get(name)

    def list_patterns(self) -> List[Dict[str, str]]:
        """List all available patterns.

        Returns:
            List of pattern info dictionaries
        """
        return [
            {"name": p.name, "description": p.description, "variables": p.variables}
            for p in self.patterns.values()
        ]

    def generate_from_pattern(
        self, pattern_name: str, context: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """Generate template from a pattern.

        Args:
            pattern_name: Name of the pattern to use
            context: Context data for the template

        Returns:
            Generated template string or None if pattern not found
        """
        pattern = self.get_pattern(pattern_name)
        if pattern is None:
            return None

        return pattern.template

    def suggest_patterns(self, keywords: List[str]) -> List[TemplatePattern]:
        """Suggest patterns based on keywords.

        Args:
            keywords: List of keywords to match

        Returns:
            List of matching patterns
        """
        suggestions = []
        keywords_lower = [k.lower() for k in keywords]

        for pattern in self.patterns.values():
            # Check if any keyword matches pattern name or description
            pattern_text = f"{pattern.name} {pattern.description}".lower()
            if any(keyword in pattern_text for keyword in keywords_lower):
                suggestions.append(pattern)

        return suggestions

    def analyze_template(self, template_str: str) -> Dict[str, Any]:
        """Analyze a template and provide insights.

        Args:
            template_str: Template string to analyze

        Returns:
            Analysis results dictionary
        """
        analysis = {
            "variables": [],
            "filters": [],
            "blocks": [],
            "components": [],
            "complexity": 0,
        }

        # Extract variables
        var_pattern = re.compile(r"\{\{\s*([^}|]+?)(?:\|[^}]+)?\s*\}\}")
        variables = var_pattern.findall(template_str)
        analysis["variables"] = list(set(variables))

        # Extract filters
        filter_pattern = re.compile(r"\|(\w+)")
        filters = filter_pattern.findall(template_str)
        analysis["filters"] = list(set(filters))

        # Extract block tags
        block_pattern = re.compile(r"\{%\s*(\w+)")
        blocks = block_pattern.findall(template_str)
        analysis["blocks"] = list(set(blocks))

        # Calculate complexity
        analysis["complexity"] = (
            len(analysis["variables"]) * 1
            + len(analysis["filters"]) * 2
            + len(analysis["blocks"]) * 3
        )

        return analysis

    def optimize_suggestions(self, template_str: str) -> List[Dict[str, str]]:
        """Suggest optimizations for a template.

        Args:
            template_str: Template string to analyze

        Returns:
            List of optimization suggestions
        """
        suggestions = []

        # Check for missing filters
        if "{{" in template_str:
            var_pattern = re.compile(r"\{\{\s*([^}|]+?)\s*\}\}")
            vars_without_filters = var_pattern.findall(template_str)
            if len(vars_without_filters) > 0:
                suggestions.append(
                    {
                        "type": "safety",
                        "message": "Consider adding |escape or |safe filters to variables",
                        "severity": "medium",
                    }
                )

        # Check for deeply nested blocks
        if_count = template_str.count("{% if")
        for_count = template_str.count("{% for")
        if if_count > 3 or for_count > 2:
            suggestions.append(
                {
                    "type": "complexity",
                    "message": "Template has high nesting complexity. "
                    "Consider breaking into components",
                    "severity": "medium",
                }
            )

        # Check for long template
        if len(template_str) > 1000:
            suggestions.append(
                {
                    "type": "maintainability",
                    "message": "Template is quite long. "
                    "Consider splitting into smaller templates",
                    "severity": "low",
                }
            )

        # Check for hardcoded styles
        if 'style="' in template_str:
            suggestions.append(
                {
                    "type": "best_practice",
                    "message": "Inline styles detected. " "Consider using CSS classes instead",
                    "severity": "low",
                }
            )

        return suggestions

    def auto_complete(self, partial_template: str) -> List[str]:
        """Provide auto-completion suggestions.

        Args:
            partial_template: Partial template string

        Returns:
            List of completion suggestions
        """
        suggestions = []

        # Complete opening tags
        if partial_template.endswith("{{"):
            suggestions.extend(["{{ variable }}", "{{ variable|filter }}"])
        elif partial_template.endswith("{%"):
            suggestions.extend(
                [
                    "{% if condition %}",
                    "{% for item in list %}",
                    "{% include 'template.html' %}",
                ]
            )
        elif partial_template.endswith("{#"):
            suggestions.append("{# comment #}")

        # Suggest closing tags
        if "{% if" in partial_template and "{% endif" not in partial_template:
            suggestions.append("{% endif %}")
        if "{% for" in partial_template and "{% endfor" not in partial_template:
            suggestions.append("{% endfor %}")

        return suggestions


# Global AI generator instance
_global_generator = AITemplateGenerator()


def get_global_generator() -> AITemplateGenerator:
    """Get the global AI template generator.

    Returns:
        Global AITemplateGenerator instance
    """
    return _global_generator
