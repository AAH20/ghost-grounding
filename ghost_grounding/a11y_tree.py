"""
Accessibility (a11y) Tree & DOM Semantic Parser for Ghost-Grounding.
Extracts structured UI nodes with bounding boxes from accessibility trees and desktop hierarchies.
"""

from typing import List, Dict, Any, Optional
from .models import SemanticElement, ElementType, BoundingBox


class A11yTreeParser:
    """Parses raw Accessibility Tree and DOM dictionaries into SemanticElements."""

    ROLE_MAP = {
        "button": ElementType.BUTTON,
        "pushbutton": ElementType.BUTTON,
        "entry": ElementType.INPUT,
        "textbox": ElementType.INPUT,
        "searchbox": ElementType.INPUT,
        "link": ElementType.LINK,
        "heading": ElementType.TEXT,
        "label": ElementType.TEXT,
        "statictext": ElementType.TEXT,
        "window": ElementType.WINDOW,
        "dialog": ElementType.MODAL,
        "checkbox": ElementType.CHECKBOX,
        "radiobutton": ElementType.RADIO,
        "combobox": ElementType.DROPDOWN,
        "tab": ElementType.TAB,
        "menuitem": ElementType.MENU,
        "panel": ElementType.CONTAINER,
    }

    def parse_a11y_node(self, node: Dict[str, Any], parent_offset: Optional[BoundingBox] = None) -> List[SemanticElement]:
        """Recursively parses an a11y node tree into a flat list of semantic elements."""
        results: List[SemanticElement] = []

        raw_role = str(node.get("role", "statictext")).lower()
        role = self.ROLE_MAP.get(raw_role, ElementType.TEXT)

        # Coordinate parsing
        bounds = node.get("bounds", node.get("rect", [0, 0, 0, 0]))
        if len(bounds) == 4:
            x, y, w, h = bounds
        else:
            x, y, w, h = 0, 0, 0, 0

        # Adjust for parent if relative
        if parent_offset and node.get("relative_coords", False):
            x += parent_offset.x
            y += parent_offset.y

        bbox = BoundingBox(x=int(x), y=int(y), width=int(w), height=int(h))

        node_id = str(node.get("id", f"{role.value}_{x}_{y}"))
        label = str(node.get("name", node.get("label", node.get("text", "")))).strip()
        value = node.get("value")
        if value is not None:
            value = str(value)

        is_interactive = role in {
            ElementType.BUTTON,
            ElementType.INPUT,
            ElementType.LINK,
            ElementType.CHECKBOX,
            ElementType.RADIO,
            ElementType.DROPDOWN,
            ElementType.TAB,
            ElementType.MENU,
        } or node.get("focusable", False) or node.get("clickable", False)

        element = SemanticElement(
            id=node_id,
            role=role,
            label=label,
            value=value,
            bbox=bbox,
            is_interactive=is_interactive,
            is_focused=bool(node.get("focused", False)),
            confidence=float(node.get("confidence", 1.0)),
            meta={k: v for k, v in node.items() if k not in ("children", "bounds", "rect", "role", "name")}
        )

        results.append(element)

        # Process children
        for child in node.get("children", []):
            results.extend(self.parse_a11y_node(child, parent_offset=bbox))

        return results

    def parse_desktop_state(self, windows_state: Dict[str, Any]) -> List[SemanticElement]:
        """Extracts semantic elements directly from Ghost-Desktop WindowState structures."""
        elements: List[SemanticElement] = []

        for win_id, win in windows_state.items():
            rect = getattr(win, "rect", (0, 0, 800, 600))
            is_active = getattr(win, "is_active", False)
            title = getattr(win, "title", win_id)
            wx, wy, ww, wh = rect

            # Window frame element
            win_el = SemanticElement(
                id=win_id,
                role=ElementType.WINDOW,
                label=title,
                bbox=BoundingBox(x=wx, y=wy, width=ww, height=wh),
                is_interactive=True,
                is_focused=is_active,
                confidence=1.0,
            )
            elements.append(win_el)

            # Window Titlebar close button
            elements.append(
                SemanticElement(
                    id=f"{win_id}_close_btn",
                    role=ElementType.BUTTON,
                    label="Close Window",
                    bbox=BoundingBox(x=wx + ww - 24, y=wy + 4, width=16, height=16),
                    is_interactive=True,
                    confidence=1.0,
                )
            )

            # Window content or inputs
            input_text = getattr(win, "input_text", None)
            if input_text is not None:
                elements.append(
                    SemanticElement(
                        id=f"{win_id}_input_box",
                        role=ElementType.INPUT,
                        label="Address / Input Bar",
                        value=input_text,
                        bbox=BoundingBox(x=wx + 10, y=wy + 35, width=ww - 20, height=28),
                        is_interactive=True,
                        is_focused=is_active,
                        confidence=1.0,
                    )
                )

            # Text content lines
            content_lines = getattr(win, "content_lines", [])
            for idx, line in enumerate(content_lines[:15]):
                line_str = str(line).strip()
                if not line_str:
                    continue

                line_y = wy + 70 + (idx * 20)
                # Check for actionable interactive buttons in content (e.g. "[1] Deploy")
                if line_str.startswith("[") and "]" in line_str:
                    parts = line_str.split("]", 1)
                    btn_label = parts[1].strip() if len(parts) > 1 else line_str
                    elements.append(
                        SemanticElement(
                            id=f"{win_id}_action_btn_{idx}",
                            role=ElementType.BUTTON,
                            label=btn_label,
                            bbox=BoundingBox(x=wx + 20, y=line_y, width=min(250, ww - 40), height=18),
                            is_interactive=True,
                            confidence=0.98,
                        )
                    )
                else:
                    elements.append(
                        SemanticElement(
                            id=f"{win_id}_text_l{idx}",
                            role=ElementType.TEXT,
                            label=line_str,
                            bbox=BoundingBox(x=wx + 20, y=line_y, width=ww - 40, height=18),
                            is_interactive=False,
                            confidence=1.0,
                        )
                    )

        return elements
