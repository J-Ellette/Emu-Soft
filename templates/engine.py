"""Template engine for rendering templates with variables and control structures."""

import re
from typing import Any, Dict, Optional
from templates.context import Context
from templates.filters import TemplateFilters
from templates.loader import TemplateLoader


class TemplateEngine:
    """A simple template engine with variable substitution, filters, and control structures.

    Supports:
    - Variable substitution: {{ variable }}
    - Filters: {{ variable|filter_name }}
    - If statements: {% if condition %} ... {% endif %}
    - For loops: {% for item in list %} ... {% endfor %}
    - Template inclusion: {% include "template.html" %}
    - Comments: {# This is a comment #}
    """

    # Regex patterns for template syntax
    VARIABLE_PATTERN = re.compile(r"\{\{\s*([^}]+?)\s*\}\}")
    BLOCK_PATTERN = re.compile(r"\{%\s*([^%]+?)\s*%\}")
    COMMENT_PATTERN = re.compile(r"\{#.*?#\}", re.DOTALL)

    def __init__(self, loader: Optional[TemplateLoader] = None) -> None:
        """Initialize the template engine.

        Args:
            loader: Template loader for loading templates from filesystem
        """
        self.loader = loader or TemplateLoader()
        self.filters = TemplateFilters()

    def render(self, template_str: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Render a template string with the given context.

        Args:
            template_str: Template string to render
            context: Dictionary of variables to use in the template

        Returns:
            Rendered template as a string
        """
        ctx = Context(context or {})
        return self._render(template_str, ctx)

    def render_template(self, template_name: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Load and render a template file.

        Args:
            template_name: Name of the template file
            context: Dictionary of variables to use in the template

        Returns:
            Rendered template as a string
        """
        template_str = self.loader.load(template_name)
        return self.render(template_str, context)

    def _render(self, template_str: str, context: Context, process_blocks: bool = True) -> str:
        """Internal render method that uses Context object.

        Args:
            template_str: Template string to render
            context: Context object with template variables
            process_blocks: Whether to process block tags (default: True)

        Returns:
            Rendered template as a string
        """
        # Remove comments first
        template_str = self.COMMENT_PATTERN.sub("", template_str)

        # Process block tags (if, for, include) first
        if process_blocks:
            template_str = self._process_blocks(template_str, context)

        # Process variables after blocks
        template_str = self._process_variables(template_str, context)

        return template_str

    def _process_variables(self, template_str: str, context: Context) -> str:
        """Process variable substitutions in the template.

        Args:
            template_str: Template string
            context: Context object

        Returns:
            Template with variables replaced
        """

        def replace_variable(match: re.Match[str]) -> str:
            var_expr = match.group(1).strip()

            # Check if there are filters
            if "|" in var_expr:
                parts = var_expr.split("|")
                var_name = parts[0].strip()
                value = context.get(var_name, "")

                # Track if escape was explicitly applied
                has_safe = False
                has_escape = False

                # Apply filters in sequence
                for filter_part in parts[1:]:
                    filter_part = filter_part.strip()
                    # Check for filter arguments (e.g., truncate:100)
                    if ":" in filter_part:
                        filter_name, filter_args = filter_part.split(":", 1)
                        filter_name = filter_name.strip()
                        # Parse arguments (simple string or number)
                        args = [arg.strip().strip("\"'") for arg in filter_args.split(",")]
                        # Convert numeric args
                        converted_args: list[int | str] = []
                        for arg in args:
                            try:
                                converted_args.append(int(arg))
                            except ValueError:
                                converted_args.append(arg)
                        value = self.filters.apply(value, filter_name, *converted_args)
                    else:
                        if filter_part == "safe":
                            has_safe = True
                        elif filter_part == "escape":
                            has_escape = True
                        value = self.filters.apply(value, filter_part)

                # Auto-escape unless 'safe' filter was used or 'escape' was explicitly applied
                if not has_safe and not has_escape:
                    value = self.filters.escape(value)
                return str(value)
            else:
                # Simple variable without filters - auto-escape
                value = context.get(var_expr, "")
                return self.filters.escape(str(value))

        return self.VARIABLE_PATTERN.sub(replace_variable, template_str)

    def _process_blocks(self, template_str: str, context: Context) -> str:
        """Process block tags (if, for, include) in the template.

        Args:
            template_str: Template string
            context: Context object

        Returns:
            Template with blocks processed
        """
        # Process for loops first (they contain if statements)
        template_str = self._process_for_blocks(template_str, context)

        # Then process remaining if statements
        template_str = self._process_if_blocks(template_str, context)

        # Process includes last
        template_str = self._process_includes(template_str, context)

        return template_str

    def _process_if_blocks(self, template_str: str, context: Context) -> str:
        """Process if/else/endif blocks.

        Args:
            template_str: Template string
            context: Context object

        Returns:
            Template with if blocks processed
        """
        # Pattern for if/else/endif blocks
        if_pattern = re.compile(
            r"\{%\s*if\s+([^%]+?)\s*%\}(.*?)(?:\{%\s*else\s*%\}(.*?))?\{%\s*endif\s*%\}",
            re.DOTALL,
        )

        def replace_if(match: re.Match[str]) -> str:
            condition = match.group(1).strip()
            if_block = match.group(2)
            else_block = match.group(3) if match.group(3) else ""

            # Evaluate condition
            if self._evaluate_condition(condition, context):
                # Process nested for loops first, then variables
                rendered = self._process_for_blocks(if_block, context)
                return self._process_variables(rendered, context)
            else:
                rendered = self._process_for_blocks(else_block, context)
                return self._process_variables(rendered, context)

        # Keep processing until no more if blocks
        while if_pattern.search(template_str):
            template_str = if_pattern.sub(replace_if, template_str)

        return template_str

    def _process_for_blocks(self, template_str: str, context: Context) -> str:
        """Process for/endfor loops.

        Args:
            template_str: Template string
            context: Context object

        Returns:
            Template with for loops processed
        """
        # Pattern for for/endfor blocks
        for_pattern = re.compile(
            r"\{%\s*for\s+(\w+)\s+in\s+(\w+)\s*%\}(.*?)\{%\s*endfor\s*%\}", re.DOTALL
        )

        def replace_for(match: re.Match[str]) -> str:
            item_name = match.group(1).strip()
            list_name = match.group(2).strip()
            loop_block = match.group(3)

            # Get the list from context
            items = context.get(list_name, [])
            if not isinstance(items, (list, tuple)):
                return ""

            # Render loop block for each item
            result = []
            for item in items:
                context.push({item_name: item})
                # Process both blocks and variables for each iteration
                # First process any if blocks in the loop
                rendered = self._process_if_blocks(loop_block, context)
                # Then process variables
                rendered = self._process_variables(rendered, context)
                result.append(rendered)
                context.pop()

            return "".join(result)

            return "".join(result)

        # Keep processing until no more for blocks
        while for_pattern.search(template_str):
            template_str = for_pattern.sub(replace_for, template_str)

        return template_str

    def _process_includes(self, template_str: str, context: Context) -> str:
        """Process include tags.

        Args:
            template_str: Template string
            context: Context object

        Returns:
            Template with includes processed
        """
        # Pattern for include tags
        include_pattern = re.compile(r'\{%\s*include\s+["\']([^"\']+)["\']\s*%\}')

        def replace_include(match: re.Match[str]) -> str:
            template_name = match.group(1).strip()
            try:
                included_template = self.loader.load(template_name)
                # Process the included template with full rendering
                return self._render(included_template, context, process_blocks=True)
            except FileNotFoundError:
                return f"<!-- Template not found: {template_name} -->"

        return include_pattern.sub(replace_include, template_str)

    def _evaluate_condition(self, condition: str, context: Context) -> bool:
        """Evaluate a template condition.

        Supports: variable, not variable, variable == value, variable != value

        Args:
            condition: Condition string
            context: Context object

        Returns:
            Boolean result of the condition
        """
        condition = condition.strip()

        # Handle 'not' operator
        if condition.startswith("not "):
            return not self._evaluate_condition(condition[4:], context)

        # Handle equality/inequality operators
        if "==" in condition:
            left, right = condition.split("==", 1)
            left_val = self._get_value(left.strip(), context)
            right_val = self._get_value(right.strip(), context)
            return left_val == right_val
        elif "!=" in condition:
            left, right = condition.split("!=", 1)
            left_val = self._get_value(left.strip(), context)
            right_val = self._get_value(right.strip(), context)
            return left_val != right_val

        # Simple variable check
        value = context.get(condition)
        return self._is_truthy(value)

    def _get_value(self, expr: str, context: Context) -> Any:
        """Get a value from an expression (variable or literal).

        Args:
            expr: Expression string
            context: Context object

        Returns:
            The value
        """
        # Check if it's a string literal
        if (expr.startswith('"') and expr.endswith('"')) or (
            expr.startswith("'") and expr.endswith("'")
        ):
            return expr[1:-1]

        # Check if it's a number
        try:
            return int(expr)
        except ValueError:
            pass

        try:
            return float(expr)
        except ValueError:
            pass

        # It's a variable
        return context.get(expr)

    @staticmethod
    def _is_truthy(value: Any) -> bool:
        """Check if a value is truthy for template conditions.

        Args:
            value: Value to check

        Returns:
            True if the value is truthy, False otherwise
        """
        if value is None:
            return False
        if isinstance(value, bool):
            return value
        if isinstance(value, (list, dict, tuple, str)):
            return len(value) > 0
        if isinstance(value, (int, float)):
            return value != 0
        return True
