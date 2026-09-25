"""
Unit tests for Ghost-Grounding using standard unittest.
"""

import unittest
from ghost_grounding.models import (
    ElementType,
    BoundingBox,
    SemanticElement,
    GroundingFrame,
)
from ghost_grounding.a11y_tree import A11yTreeParser
from ghost_grounding.optical_grounding import OpticalGrounder
from ghost_grounding.wireframe_mux import WireframeMultiplexer


class TestGhostGrounding(unittest.TestCase):
    def test_bounding_box_center_and_contains(self):
        bbox = BoundingBox(x=100, y=200, width=50, height=30)
        self.assertEqual(bbox.center, (125, 215))
        self.assertTrue(bbox.contains(125, 215))
        self.assertTrue(bbox.contains(100, 200))
        self.assertFalse(bbox.contains(99, 200))
        self.assertFalse(bbox.contains(151, 200))

    def test_a11y_parser_recursion(self):
        parser = A11yTreeParser()
        node = {
            "role": "dialog",
            "id": "confirm_modal",
            "name": "Confirm Action",
            "rect": [100, 100, 400, 300],
            "children": [
                {
                    "role": "button",
                    "id": "btn_yes",
                    "name": "Yes, Proceed",
                    "rect": [120, 320, 100, 30],
                    "clickable": True,
                }
            ],
        }

        elements = parser.parse_a11y_node(node)
        self.assertEqual(len(elements), 2)
        self.assertEqual(elements[0].role, ElementType.MODAL)
        self.assertEqual(elements[1].role, ElementType.BUTTON)
        self.assertTrue(elements[1].is_interactive)
        self.assertEqual(elements[1].bbox.center, (170, 335))

    def test_optical_refine_and_deltas(self):
        grounder = OpticalGrounder(screen_width=1280, screen_height=800)
        el = SemanticElement(
            id="btn_run",
            role=ElementType.BUTTON,
            label="Run Task",
            bbox=BoundingBox(x=10, y=10, width=100, height=30),
        )

        refined = grounder.refine_bounding_box(el, padding=5)
        self.assertEqual(refined.bbox.x, 5)
        self.assertEqual(refined.bbox.y, 5)
        self.assertEqual(refined.bbox.width, 110)
        self.assertEqual(refined.bbox.height, 40)

        # Delta test
        mutated = SemanticElement(
            id="btn_run",
            role=ElementType.BUTTON,
            label="Run Task",
            value="Running...",
            bbox=refined.bbox,
        )
        deltas = grounder.detect_optical_deltas([mutated], [el])
        self.assertEqual(len(deltas), 1)
        self.assertEqual(deltas[0].meta.get("delta_state"), "mutated")

    def test_wireframe_mux_markdown_and_efficiency(self):
        frame = GroundingFrame(
            frame_id="f1",
            timestamp=1000.0,
            elements=[
                SemanticElement(
                    id="btn_auth",
                    role=ElementType.BUTTON,
                    label="Sign In With SSO",
                    bbox=BoundingBox(x=500, y=400, width=200, height=50),
                    is_interactive=True,
                )
            ],
        )

        md = WireframeMultiplexer.to_markdown(frame)
        self.assertIn("btn_auth", md)
        self.assertIn("[CLICK:btn_auth]", md)

        efficiency = WireframeMultiplexer.calculate_efficiency(md)
        self.assertGreater(efficiency["savings_percentage"], 90.0)
        self.assertLess(efficiency["wireframe_tokens"], 100)

    def test_target_resolution_strategies(self):
        frame = GroundingFrame(
            frame_id="f2",
            timestamp=1001.0,
            elements=[
                SemanticElement(
                    id="nav_settings",
                    role=ElementType.LINK,
                    label="Account Settings",
                    bbox=BoundingBox(x=800, y=20, width=120, height=24),
                )
            ],
        )

        # By exact ID
        res1 = WireframeMultiplexer.resolve_target(frame, "nav_settings")
        self.assertEqual(res1.target_point, (860, 32))
        self.assertEqual(res1.strategy, "exact_id")

        # By click syntax
        res2 = WireframeMultiplexer.resolve_target(frame, "[CLICK:nav_settings]")
        self.assertEqual(res2.target_point, (860, 32))

        # By label
        res3 = WireframeMultiplexer.resolve_target(frame, "Account Settings")
        self.assertEqual(res3.target_point, (860, 32))
        self.assertEqual(res3.strategy, "exact_label")

        # By substring
        res4 = WireframeMultiplexer.resolve_target(frame, "settings")
        self.assertEqual(res4.target_point, (860, 32))
        self.assertEqual(res4.strategy, "substring_match")


if __name__ == "__main__":
    unittest.main()
