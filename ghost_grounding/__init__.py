"""
Ghost-Grounding: Sub-Token Semantic a11y & Optical Wireframe Multiplexer for Computer-Use AI Agents.
Optimized for Claude Opus 5.5, GPT-6 Astra, and high-frequency agentic GUI grounding.
"""

from .models import (
    ElementType,
    BoundingBox,
    SemanticElement,
    GroundingFrame,
    WireframeFormat,
    GroundingResolution,
)
from .a11y_tree import A11yTreeParser
from .optical_grounding import OpticalGrounder
from .wireframe_mux import WireframeMultiplexer

__version__ = "1.0.0"
__all__ = [
    "ElementType",
    "BoundingBox",
    "SemanticElement",
    "GroundingFrame",
    "WireframeFormat",
    "GroundingResolution",
    "A11yTreeParser",
    "OpticalGrounder",
    "WireframeMultiplexer",
]
