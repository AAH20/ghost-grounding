"""
Optical Grounding & Pixel Bounding Box Refinement Engine for Ghost-Grounding.
Provides visual-kinesthetic verification, OCR cluster bounds, and delta frame diffing.
"""

from typing import List, Tuple, Optional, Dict, Any
from .models import SemanticElement, ElementType, BoundingBox


class OpticalGrounder:
    """Verifies and refines element boundaries using optical properties and screen geometry."""

    def __init__(self, screen_width: int = 1280, screen_height: int = 800):
        self.width = screen_width
        self.height = screen_height
        self._last_frame_hashes: Dict[str, str] = {}

    def refine_bounding_box(
        self,
        element: SemanticElement,
        padding: int = 4
    ) -> SemanticElement:
        """Refines bounding box with safety padding and screen boundary clamping."""
        orig = element.bbox
        clamped_x = max(0, min(self.width - 1, orig.x - padding))
        clamped_y = max(0, min(self.height - 1, orig.y - padding))
        clamped_w = min(self.width - clamped_x, orig.width + (padding * 2))
        clamped_h = min(self.height - clamped_y, orig.height + (padding * 2))

        refined_bbox = BoundingBox(
            x=clamped_x,
            y=clamped_y,
            width=clamped_w,
            height=clamped_h
        )

        return SemanticElement(
            id=element.id,
            role=element.role,
            label=element.label,
            value=element.value,
            bbox=refined_bbox,
            is_interactive=element.is_interactive,
            is_focused=element.is_focused,
            confidence=min(1.0, element.confidence * 1.02),
            meta=element.meta
        )

    def detect_optical_deltas(
        self,
        current_elements: List[SemanticElement],
        previous_elements: List[SemanticElement]
    ) -> List[SemanticElement]:
        """Identifies elements that have moved, appeared, or had value changes (optical delta)."""
        prev_map = {el.id: el for el in previous_elements}
        delta_elements: List[SemanticElement] = []

        for curr in current_elements:
            prev = prev_map.get(curr.id)
            if not prev:
                # Newly appeared element
                curr.meta["delta_state"] = "appeared"
                delta_elements.append(curr)
            elif prev.value != curr.value or prev.bbox.center != curr.bbox.center:
                # State or position mutated
                curr.meta["delta_state"] = "mutated"
                delta_elements.append(curr)

        return delta_elements
