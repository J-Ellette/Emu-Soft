"""
Developed by PowerShield, as an alternative to Django Templates
"""

"""Component-based templating system for React-like component development in Python.

This module provides a component-based architecture for building reusable
template components with props, state, and lifecycle methods.
"""

from typing import Any, Dict, Optional, List, Callable
from abc import ABC, abstractmethod
import json
import hashlib


class Component(ABC):
    """Base class for template components.

    Components are reusable template units that can accept props,
    manage internal state, and render to HTML.
    """

    def __init__(self, props: Optional[Dict[str, Any]] = None) -> None:
        """Initialize a component with props.

        Args:
            props: Dictionary of properties passed to the component
        """
        self.props = props or {}
        self.state: Dict[str, Any] = {}
        self.children: List["Component"] = []
        self._mounted = False

    @abstractmethod
    def render(self) -> str:
        """Render the component to HTML.

        Returns:
            HTML string representation of the component
        """
        pass

    def set_state(self, updates: Dict[str, Any]) -> None:
        """Update component state.

        Args:
            updates: Dictionary of state updates
        """
        self.state.update(updates)
        if self._mounted:
            self._on_update()

    def mount(self) -> None:
        """Mount the component (lifecycle method)."""
        self._mounted = True
        self._on_mount()

    def unmount(self) -> None:
        """Unmount the component (lifecycle method)."""
        self._on_unmount()
        self._mounted = False

    def _on_mount(self) -> None:
        """Called when component is mounted. Override in subclasses."""
        pass

    def _on_update(self) -> None:
        """Called when component state updates. Override in subclasses."""
        pass

    def _on_unmount(self) -> None:
        """Called when component is unmounted. Override in subclasses."""
        pass

    def add_child(self, child: "Component") -> None:
        """Add a child component.

        Args:
            child: Child component to add
        """
        self.children.append(child)

    def get_cache_key(self) -> str:
        """Generate a cache key for this component based on props.

        Returns:
            Cache key string
        """
        props_str = json.dumps(self.props, sort_keys=True)
        return hashlib.md5(props_str.encode()).hexdigest()


class FunctionalComponent:
    """Functional component that takes props and returns HTML.

    Simpler alternative to class-based components for stateless rendering.
    """

    def __init__(self, render_func: Callable[[Dict[str, Any]], str]) -> None:
        """Initialize a functional component.

        Args:
            render_func: Function that takes props and returns HTML
        """
        self.render_func = render_func

    def __call__(self, props: Optional[Dict[str, Any]] = None) -> str:
        """Render the component with given props.

        Args:
            props: Dictionary of properties

        Returns:
            Rendered HTML string
        """
        return self.render_func(props or {})


class ComponentRegistry:
    """Registry for managing reusable components."""

    def __init__(self) -> None:
        """Initialize the component registry."""
        self._components: Dict[str, type | FunctionalComponent] = {}

    def register(self, name: str, component: type | FunctionalComponent) -> None:
        """Register a component.

        Args:
            name: Component name
            component: Component class or functional component
        """
        self._components[name] = component

    def get(self, name: str) -> Optional[type | FunctionalComponent]:
        """Get a registered component.

        Args:
            name: Component name

        Returns:
            Component class or functional component, or None if not found
        """
        return self._components.get(name)

    def render(self, name: str, props: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """Render a registered component.

        Args:
            name: Component name
            props: Component props

        Returns:
            Rendered HTML string, or None if component not found
        """
        component = self.get(name)
        if component is None:
            return None

        if isinstance(component, FunctionalComponent):
            return component(props)
        elif issubclass(component, Component):
            instance = component(props)
            instance.mount()
            html = instance.render()
            instance.unmount()
            return html

        return None

    def list_components(self) -> List[str]:
        """List all registered component names.

        Returns:
            List of component names
        """
        return list(self._components.keys())


# Built-in components
class ButtonComponent(Component):
    """A reusable button component with USWDS styling."""

    def render(self) -> str:
        """Render the button.

        Props:
            text (str): Button text
            variant (str): Button variant (primary, secondary, accent, etc.)
            size (str): Button size (big, small, default)
            disabled (bool): Whether button is disabled
            type (str): Button type (button, submit)

        Returns:
            HTML string
        """
        text = self.props.get("text", "Button")
        variant = self.props.get("variant", "primary")
        size = self.props.get("size", "")
        disabled = self.props.get("disabled", False)
        btn_type = self.props.get("type", "button")

        classes = ["usa-button"]
        if variant != "primary":
            classes.append(f"usa-button--{variant}")
        if size:
            classes.append(f"usa-button--{size}")

        disabled_attr = ' disabled="disabled"' if disabled else ""
        class_str = " ".join(classes)

        return f'<button type="{btn_type}" class="{class_str}"{disabled_attr}>' f"{text}</button>"


class CardComponent(Component):
    """A reusable card component with USWDS styling."""

    def render(self) -> str:
        """Render the card.

        Props:
            title (str): Card title
            content (str): Card content
            header_level (str): Header level (h1-h6)
            image_url (str): Optional image URL
            image_alt (str): Image alt text

        Returns:
            HTML string
        """
        title = self.props.get("title", "")
        content = self.props.get("content", "")
        header_level = self.props.get("header_level", "h2")
        image_url = self.props.get("image_url")
        image_alt = self.props.get("image_alt", "")

        html_parts = ['<div class="usa-card">']

        if image_url:
            html_parts.append('<div class="usa-card__container">')
            html_parts.append('<div class="usa-card__header">')
            html_parts.append(f'<img src="{image_url}" alt="{image_alt}" class="usa-card__img" />')
            html_parts.append("</div>")
        else:
            html_parts.append('<div class="usa-card__container">')

        html_parts.append('<div class="usa-card__body">')
        if title:
            html_parts.append(f'<{header_level} class="usa-card__heading">{title}</{header_level}>')
        if content:
            html_parts.append(f"<p>{content}</p>")
        html_parts.append("</div>")
        html_parts.append("</div>")
        html_parts.append("</div>")

        return "".join(html_parts)


class AlertComponent(Component):
    """A reusable alert component with USWDS styling."""

    def render(self) -> str:
        """Render the alert.

        Props:
            type (str): Alert type (info, warning, error, success)
            heading (str): Alert heading
            message (str): Alert message
            slim (bool): Whether to use slim variant

        Returns:
            HTML string
        """
        alert_type = self.props.get("type", "info")
        heading = self.props.get("heading", "")
        message = self.props.get("message", "")
        slim = self.props.get("slim", False)

        classes = ["usa-alert", f"usa-alert--{alert_type}"]
        if slim:
            classes.append("usa-alert--slim")

        class_str = " ".join(classes)

        html_parts = [f'<div class="{class_str}" role="alert">']
        html_parts.append('<div class="usa-alert__body">')
        if heading:
            html_parts.append(f'<h4 class="usa-alert__heading">{heading}</h4>')
        if message:
            html_parts.append(f'<p class="usa-alert__text">{message}</p>')
        html_parts.append("</div>")
        html_parts.append("</div>")

        return "".join(html_parts)


# Global component registry
_global_registry = ComponentRegistry()

# Register built-in components
_global_registry.register("Button", ButtonComponent)
_global_registry.register("Card", CardComponent)
_global_registry.register("Alert", AlertComponent)


def get_global_registry() -> ComponentRegistry:
    """Get the global component registry.

    Returns:
        Global ComponentRegistry instance
    """
    return _global_registry


def component(func: Callable[[Dict[str, Any]], str]) -> FunctionalComponent:
    """Decorator to create a functional component.

    Args:
        func: Function that takes props and returns HTML

    Returns:
        FunctionalComponent instance
    """
    return FunctionalComponent(func)
