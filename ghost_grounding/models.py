"""
Data models and typed structures for Ghost-Grounding.
Zero-external-dependency dataclasses for maximum portability.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Tuple, Dict, Any


class ElementType(str, Enum):
    BUTTON = "button"
    INPUT = "input"
    LINK = "link"
    TEXT = "text"
    WINDOW = "window"
    MODAL = "modal"
    CHECKBOX = "checkbox"
    RADIO = "radio"
    DROPDOWN = "dropdown"
    ICON = "icon"
    TAB = "tab"
    MENU = "menu"
    CONTAINER = "container"


@dataclass
class BoundingBox:
    x: int
    y: int
    width: int
    height: int

    @property
    def center(self) -> Tuple[int, int]:
        """Sub-pixel target center coordinate for mouse click events."""
        return (self.x + self.width // 2, self.y + self.height // 2)

    @property
    def right(self) -> int:
        return self.x + self.width

    @property
    def bottom(self) -> int:
        return self.y + self.height

    def contains(self, px: int, py: int) -> bool:
        return self.x <= px <= self.right and self.y <= py <= self.bottom


@dataclass
class SemanticElement:
    id: str
    role: ElementType
    bbox: BoundingBox
    label: str = ""
    value: Optional[str] = None
    is_interactive: bool = True
    is_focused: bool = False
    confidence: float = 1.0
    meta: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GroundingFrame:
    frame_id: str
    timestamp: float
    display_width: int = 1280
    display_height: int = 800
    active_window: str = "Desktop"
    elements: List[SemanticElement] = field(default_factory=list)

    def interactive_elements(self) -> List[SemanticElement]:
        return [el for el in self.elements if el.is_interactive]


class WireframeFormat(str, Enum):
    MARKDOWN = "markdown"
    COMPACT_JSON = "json"
    COMPACT_TUPLES = "tuples"


@dataclass
class GroundingResolution:
    query: str
    matched_element: Optional[SemanticElement] = None
    target_point: Optional[Tuple[int, int]] = None
    confidence: float = 0.0
    strategy: str = "exact_id"
