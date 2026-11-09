"""
LangGraph Graph Factory for GamED-AI — V4 Pipeline Only

This module provides:
- get_checkpointer(): SQLite/Postgres checkpointer for LangGraph persistence
- get_compiled_graph(): Returns compiled V4 pipeline graph
- run_game_generation(): High-level function to run the pipeline
"""

import os
import logging
from typing import Optional
from datetime import datetime

from langgraph.checkpoint.memory import MemorySaver

logger = logging.getLogger("gamed_ai.graph")


# =============================================================================
# CHECKPOINTER
# =============================================================================

_checkpointer = None
_checkpointer_cm = None


def get_checkpointer():
    """
    Get database-backed checkpointer for LangGraph.

    Uses SQLite checkpointer for development (matches current DB setup).
    Can be extended to support PostgreSQL for production.

    Returns:
        Checkpointer instance (SqliteSaver, PostgresSaver, or MemorySaver)
    """
    global _checkpointer, _checkpointer_cm

    if _checkpointer is not None:
        return _checkpointer

    db_url = os.getenv("DATABASE_URL", "sqlite:///./gamed_ai_v2.db")

    try:
        if db_url.startswith("sqlite"):
            from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

            sqlite_path = db_url.replace("sqlite:///", "")
            if sqlite_path == ":memory:":
                sqlite_path = ":memory:"

            logger.info(f"Initializing Async SQLite checkpointer with path: {sqlite_path}")
            _checkpointer_cm = AsyncSqliteSaver.from_conn_string(sqlite_path)
            _checkpointer = _checkpointer_cm.__enter__()
            return _checkpointer
        else:
            try:
                from langgraph.checkpoint.postgres import PostgresSaver
                logger.info("Initializing PostgreSQL checkpointer")
                cm = PostgresSaver.from_conn_string(db_url)
                if hasattr(cm, '__enter__'):
                    _checkpointer_cm = cm
                    _checkpointer = _checkpointer_cm.__enter__()
                else:
                    _checkpointer = cm
                return _checkpointer
            except ImportError:
                logger.warning(
                    "PostgreSQL checkpointer not available. "
                    "Falling back to MemorySaver."
                )
                _checkpointer = MemorySaver()
                return _checkpointer
    except Exception as e:
        logger.error(f"Failed to initialize checkpointer: {e}. Falling back to MemorySaver.")
        _checkpointer = MemorySaver()
        return _checkpointer


# =============================================================================
# GRAPH FACTORY
# =============================================================================


def get_compiled_graph(topology: Optional[str] = None, preset: Optional[str] = None):
    """
    Get compiled V4 pipeline graph.

    Args:
        topology: Ignored (kept for API compatibility)
        preset: Ignored (always uses V4)

    Returns:
        Compiled StateGraph with checkpointer
    """
    from app.v4.graph import create_v4_graph

    checkpointer = get_checkpointer()
    logger.info("Compiling V4 pipeline graph")
    return create_v4_graph(checkpointer=checkpointer)


# =============================================================================
# HIGH-LEVEL RUNNER
# =============================================================================


async def run_game_generation(
    question_id: str,
    question_text: str,
    question_options: list = None,
    thread_id: str = None,
) -> dict:
    """
    Run the V4 game generation pipeline.

    Args:
        question_id: Unique ID for the question
        question_text: The question text
        question_options: Optional answer choices
        thread_id: Optional thread ID for resuming

    Returns:
        Final state after generation
    """
    graph = get_compiled_graph()

    initial_state = {
        "question_text": question_text,
        "question_id": question_id,
        "question_options": question_options,
        "_run_id": question_id,
        "_pipeline_preset": "v4",
        "design_retry_count": 0,
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

    config = {"configurable": {"thread_id": thread_id or question_id}}

    logger.info(f"Starting V4 game generation for question {question_id}")

    try:
        final_state = await graph.ainvoke(initial_state, config)
        logger.info(f"Game generation complete for {question_id}")
        return final_state
    except Exception as e:
        logger.error(f"Game generation failed: {e}", exc_info=True)
        raise
