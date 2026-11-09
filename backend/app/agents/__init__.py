"""
GamED-AI Agents Module — V4 Pipeline

Provides the V4 LangGraph pipeline for educational game generation.
"""

# Suppress Pydantic V1 deprecation warnings
import warnings
warnings.filterwarnings("ignore", message=".*Pydantic V1.*", category=UserWarning)
warnings.filterwarnings("ignore", message=".*pydantic.v1.*", category=UserWarning)
warnings.filterwarnings("ignore", message=".*Core Pydantic V1.*", category=UserWarning)

from app.agents.graph import (
    get_compiled_graph,
    run_game_generation,
)

__all__ = [
    "get_compiled_graph",
    "run_game_generation",
]
