"""Template system for rendering HTML templates with variable substitution and control structures."""  # noqa: E501

from mycms.templates.engine import TemplateEngine
from mycms.templates.loader import TemplateLoader
from mycms.templates.context import Context
from mycms.templates.filters import TemplateFilters
from mycms.templates.components import (
    Component,
    FunctionalComponent,
    ComponentRegistry,
    ButtonComponent,
    CardComponent,
    AlertComponent,
    get_global_registry,
    component,
)
from mycms.templates.ai_generator import (
    AITemplateGenerator,
    TemplatePattern,
    get_global_generator,
)
from mycms.templates.collaboration import (
    CollaborationSession,
    CollaborationManager,
    TemplateChange,
    TemplateVersion,
    get_global_collaboration_manager,
)
from mycms.templates.optimizer import (
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
