#!/usr/bin/env python3
"""
GamED-AI — Generate an educational game from a natural language question.

Usage:
    python run.py "Label the parts of a plant cell"
    python run.py "Label the parts of a plant cell" --output my_game.json
    python run.py --dry-run                          # validate graph compilation only
    python run.py --list-questions                   # show example questions

Requires:
    - GOOGLE_API_KEY in .env (for Gemini models)
    - Optionally SERPER_API_KEY (for diagram image search)
"""

import asyncio
import sys
import json
import argparse
import time
import logging
import os
import re
from pathlib import Path
from datetime import datetime

# Suppress noisy warnings
import warnings
warnings.filterwarnings("ignore", message=".*Pydantic.*", category=UserWarning)

# Ensure backend/ is on the path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

# Set default preset if not already set
if not os.environ.get("AGENT_CONFIG_PRESET"):
    if os.environ.get("GOOGLE_API_KEY"):
        os.environ["AGENT_CONFIG_PRESET"] = "gemini_only"
    elif os.environ.get("GROQ_API_KEY"):
        os.environ["AGENT_CONFIG_PRESET"] = "groq_free"
    else:
        os.environ["AGENT_CONFIG_PRESET"] = "balanced"


EXAMPLE_QUESTIONS = [
    "Label the parts of a plant cell",
    "Heart: label the chambers, trace the blood flow path, and order the steps of the cardiac cycle",
    "Sort the phases of mitosis into the correct order, then match each phase to its description",
    "Describe the function of each organelle in an animal cell",
    "Identify the layers of the Earth's atmosphere",
    "Order the steps of the water cycle",
    "Match historical figures to their achievements",
    "Label the parts of a computer motherboard",
]


def slugify(text: str) -> str:
    """Convert question text to a filename-safe slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    return text[:60].rstrip("-")


def test_graph_compilation() -> bool:
    """Verify V4 graph compiles without API calls."""
    from app.v4.graph import create_v4_graph

    try:
        graph = create_v4_graph()
        nodes = list(graph.nodes.keys())
        print(f"✓ V4 graph compiled: {len(nodes)} nodes")
        print(f"  Nodes: {', '.join(nodes)}")
        return True
    except Exception as e:
        print(f"✗ Graph compilation failed: {e}")
        return False


async def generate(question: str, verbose: bool = False) -> dict:
    """Run the V4 pipeline on a question and return the final state."""
    from app.v4.graph import create_v4_graph

    if verbose:
        logging.basicConfig(level=logging.DEBUG, format="%(asctime)s [%(levelname)-8s] %(name)s: %(message)s")
        for name in ["httpx", "httpcore", "openai", "urllib3", "google", "grpc"]:
            logging.getLogger(name).setLevel(logging.WARNING)
    else:
        logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)-8s] %(message)s")

    graph = create_v4_graph()

    initial_state = {
        "question_text": question,
        "question_id": f"cli_{int(time.time())}",
        "question_options": None,
        "_run_id": "",  # empty = skip instrumentation DB writes
        "_pipeline_preset": "v4",
        "design_retry_count": 0,
        "concept_retry_count": 0,
        "content_retry_count": 0,
        "asset_retry_count": 0,
        "generation_complete": False,
        "is_degraded": False,
        "_stage_order": 0,
        "started_at": datetime.utcnow().isoformat(),
        "last_updated_at": datetime.utcnow().isoformat(),
        "generated_assets_raw": [],
        "failed_asset_scene_ids": [],
        "phase_errors": [],
    }

    start = time.time()
    final_state = await graph.ainvoke(initial_state, {"recursion_limit": 50})
    elapsed = time.time() - start

    return final_state, elapsed


def print_summary(blueprint: dict, elapsed: float):
    """Print a human-readable summary of the generated game."""
    if not blueprint:
        print("✗ No blueprint generated (pipeline may have failed)")
        return

    title = blueprint.get("title", "Untitled")
    template = blueprint.get("templateType", "unknown")
    mechanics = [m.get("type", "?") for m in blueprint.get("mechanics", [])]
    total_score = blueprint.get("totalMaxScore", 0)
    complete = blueprint.get("generation_complete", False)
    is_multi = blueprint.get("is_multi_scene", False)
    scene_count = blueprint.get("game_sequence", {}).get("total_scenes", 1) if is_multi else 1

    print()
    print("=" * 60)
    print(f"  Game: {title}")
    print(f"  Template: {template}")
    print(f"  Mechanics: {', '.join(mechanics) if mechanics else 'none'}")
    print(f"  Scenes: {scene_count}")
    print(f"  Max Score: {total_score}")
    print(f"  Complete: {'✓' if complete else '✗'}")
    print(f"  Time: {elapsed:.1f}s")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="GamED-AI — Generate educational games from questions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n"
               '  python run.py "Label the parts of a plant cell"\n'
               '  python run.py "Order the steps of the water cycle" -o water_cycle.json\n'
               "  python run.py --dry-run\n"
               "  python run.py --list-questions\n",
    )
    parser.add_argument("question", nargs="?", help="The question/topic for the game")
    parser.add_argument("--output", "-o", help="Output JSON file path")
    parser.add_argument("--dry-run", action="store_true", help="Only test graph compilation")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable debug logging")
    parser.add_argument("--list-questions", action="store_true", help="Show example questions")
    args = parser.parse_args()

    if args.list_questions:
        print("Example questions you can try:\n")
        for i, q in enumerate(EXAMPLE_QUESTIONS, 1):
            print(f"  {i}. {q}")
        print()
        return

    if args.dry_run:
        success = test_graph_compilation()
        sys.exit(0 if success else 1)

    if not args.question:
        parser.error("Please provide a question, e.g.: python run.py \"Label the parts of a plant cell\"")

    # Check API keys
    if not os.environ.get("GOOGLE_API_KEY") and not os.environ.get("GROQ_API_KEY"):
        print("⚠ No API key found. Set GOOGLE_API_KEY or GROQ_API_KEY in .env")
        print("  See .env.example for setup instructions.")
        sys.exit(1)

    print(f"Generating game for: \"{args.question}\"")
    print(f"Using preset: {os.environ.get('AGENT_CONFIG_PRESET', 'balanced')}")
    print()

    final_state, elapsed = asyncio.run(generate(args.question, verbose=args.verbose))

    blueprint = final_state.get("blueprint", {})
    print_summary(blueprint, elapsed)

    # Save output
    output_path = args.output or f"output/{slugify(args.question)}.json"
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    # Save the full game entry (same format as ACL demo games)
    game_entry = {
        "id": slugify(args.question),
        "title": blueprint.get("title", args.question),
        "question": args.question,
        "gameType": "interactive_diagram",
        "blueprint": blueprint,
        "pipelineMetrics": {
            "totalDurationMs": int(elapsed * 1000),
            "generationComplete": blueprint.get("generation_complete", False),
        },
    }

    json_text = json.dumps(game_entry, indent=2, ensure_ascii=False)
    Path(output_path).write_text(json_text, encoding="utf-8")

    print(f"\nBlueprint saved to: {output_path}")

    # Also copy to frontend/public/games/ for the player page
    frontend_games = Path(__file__).parent.parent / "frontend" / "public" / "games"
    if frontend_games.parent.exists():
        frontend_games.mkdir(parents=True, exist_ok=True)
        frontend_path = frontend_games / f"{slugify(args.question)}.json"
        frontend_path.write_text(json_text, encoding="utf-8")
        print(f"Copied to frontend: {frontend_path}")


if __name__ == "__main__":
    main()
