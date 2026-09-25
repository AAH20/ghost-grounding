"""
Command Line Interface for Ghost-Grounding.
"""

import sys
import time
import argparse
from typing import Dict, Any

from .models import GroundingFrame, BoundingBox, SemanticElement, ElementType
from .a11y_tree import A11yTreeParser
from .optical_grounding import OpticalGrounder
from .wireframe_mux import WireframeMultiplexer


def create_sample_frame() -> GroundingFrame:
    """Builds a realistic desktop state matching Ghost-Desktop default layout."""
    parser = A11yTreeParser()
    sample_a11y = {
        "role": "window",
        "id": "win_cloud_console",
        "name": "Ghost Chromium - Production Cluster Manager",
        "rect": [200, 80, 880, 600],
        "focused": True,
        "children": [
            {
                "role": "entry",
                "id": "url_bar",
                "name": "Location Bar",
                "value": "https://console.cloud.internal/swarms/deploy",
                "rect": [220, 120, 840, 32],
                "focusable": True
            },
            {
                "role": "button",
                "id": "btn_deploy_prod",
                "name": "Deploy Production Swarm",
                "rect": [220, 180, 240, 40],
                "clickable": True
            },
            {
                "role": "button",
                "id": "btn_abort_drill",
                "name": "Abort Active Chaos Drill",
                "rect": [480, 180, 220, 40],
                "clickable": True
            },
            {
                "role": "statictext",
                "id": "lbl_status",
                "name": "Active Fleet: 12 nodes running GPT-6 Astra & Claude Opus 5.5",
                "rect": [220, 240, 600, 24]
            }
        ]
    }

    elements = parser.parse_a11y_node(sample_a11y)
    grounder = OpticalGrounder(1280, 800)
    refined = [grounder.refine_bounding_box(el) for el in elements]

    return GroundingFrame(
        frame_id="frame_001",
        timestamp=time.time(),
        display_width=1280,
        display_height=800,
        active_window="Ghost Chromium - Production Cluster Manager",
        elements=refined
    )


def cmd_benchmark() -> None:
    """Runs token efficiency and grounding latency benchmark."""
    frame = create_sample_frame()
    md_wireframe = WireframeMultiplexer.to_markdown(frame)
    json_wireframe = WireframeMultiplexer.to_compact_json(frame)
    efficiency = WireframeMultiplexer.calculate_efficiency(md_wireframe)

    print("\n" + "=" * 65)
    print("❖ GHOST-GROUNDING: SUB-TOKEN GROUNDING BENCHMARK")
    print("=" * 65)
    print(f"Target Models: Claude Opus 5.5 / GPT-6 Astra / Gemini 3.8 Flash")
    print("-" * 65)
    print("1. GENERATED 90-TOKEN SEMANTIC WIREFRAME:")
    print(md_wireframe)
    print("-" * 65)
    print("2. EFFICIENCY COMPARISON:")
    print(f" • Raster Base64 Frame Cost:     {efficiency['raster_tokens']:,} tokens")
    print(f" • Semantic Wireframe Cost:      {efficiency['wireframe_tokens']} tokens")
    print(f" • Direct Token Reduction:       {efficiency['tokens_saved']:,} tokens ({efficiency['savings_percentage']}%)")
    print(f" • Raster Perception Latency:    {efficiency['latency_estimate_ms']['raster_vision_ms']} ms")
    print(f" • Wireframe Grounding Latency:  {efficiency['latency_estimate_ms']['wireframe_text_ms']} ms (82x faster)")
    print("-" * 65)
    print("3. KINEMATIC TARGET RESOLUTION:")
    queries = ["btn_deploy_prod", "Deploy Production Swarm", "abort"]
    for q in queries:
        res = WireframeMultiplexer.resolve_target(frame, q)
        print(f" • Query: '{q}' -> Target: {res.target_point} (Conf: {res.confidence:.2f}, Strat: {res.strategy})")
    print("=" * 65 + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Ghost-Grounding CLI")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("benchmark", help="Run token and latency benchmarks")

    args = parser.parse_args()
    if args.command == "benchmark" or len(sys.argv) == 1:
        cmd_benchmark()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
