"""AI Demo-to-Deck & Pitch Generator.

Turn raw project repositories into timed pitch decks, demo walkthrough scripts,
and presentation materials — with verifiable facts and inferences strictly separated.
"""

from demo_to_deck.analyzer.profile import build_project_profile
from demo_to_deck.deck.export import export_bundle, export_pptx
from demo_to_deck.generator.pitch import generate_pitch_deck
from demo_to_deck.inspector.github import fetch_public_github_repo
from demo_to_deck.inspector.local import inspect_local_path
from demo_to_deck.models import (
    Claim,
    ClaimKind,
    DeckArchetype,
    DeckTheme,
    PitchDeck,
    ProjectProfile,
    Slide,
    SlideLayout,
)

__version__ = "1.0.0"

__all__ = [
    "__version__",
    "inspect_local_path",
    "fetch_public_github_repo",
    "build_project_profile",
    "generate_pitch_deck",
    "export_bundle",
    "export_pptx",
    "Claim",
    "ClaimKind",
    "DeckArchetype",
    "DeckTheme",
    "PitchDeck",
    "ProjectProfile",
    "Slide",
    "SlideLayout",
]
