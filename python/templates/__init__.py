"""Template system for rendering HTML templates with variable substitution and control structures."""  # noqa: E501

from templates.engine import TemplateEngine
from templates.loader import TemplateLoader
from templates.context import Context
from templates.filters import TemplateFilters
from templates.components import (
    Component,
    FunctionalComponent,
    ComponentRegistry,
    ButtonComponent,
    CardComponent,
    AlertComponent,
    get_global_registry,
    component,
)
from templates.ai_generator import (
    AITemplateGenerator,
    TemplatePattern,
    get_global_generator,
)
from templates.collaboration import (
    CollaborationSession,
    CollaborationManager,
    TemplateChange,
    TemplateVersion,
    get_global_collaboration_manager,
)
from templates.optimizer import (
    TemplateOptimizer,
    OptimizedTemplateEngine,
    TemplateCache,
    RenderMetrics,
)

__all__ = [
    # Core template system
    "TemplateEngine",
    "TemplateLoader",
    "Context",
    "TemplateFilters",
    # Component-based templating
    "Component",
    "FunctionalComponent",
    "ComponentRegistry",
    "ButtonComponent",
    "CardComponent",
    "AlertComponent",
    "get_global_registry",
    "component",
    # AI-powered template generation
    "AITemplateGenerator",
    "TemplatePattern",
    "get_global_generator",
    # Real-time collaboration
    "CollaborationSession",
    "CollaborationManager",
    "TemplateChange",
    "TemplateVersion",
    "get_global_collaboration_manager",
    # Performance optimization
    "TemplateOptimizer",
    "OptimizedTemplateEngine",
    "TemplateCache",
    "RenderMetrics",
]
