"""
Shim for AI Router to match requested root-level module name.
Imports functionality from src.core.ai_router.
"""

from src.core.ai_router import generate, generate_stream, router, AIRouter, send_prompt

__all__ = ['generate', 'generate_stream', 'router', 'AIRouter', 'send_prompt']
