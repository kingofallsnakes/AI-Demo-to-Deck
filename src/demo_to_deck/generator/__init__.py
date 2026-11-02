"""Pitch deck and presentation script generation."""

from .llm import get_active_provider, llm_available
from .pitch import generate_pitch_deck

__all__ = ["generate_pitch_deck", "get_active_provider", "llm_available"]
