"""Comprehensive unit and end-to-end tests for Demo-to-Deck."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from demo_to_deck.analyzer.profile import build_project_profile
from demo_to_deck.deck.export import export_bundle, export_pptx
from demo_to_deck.generator.pitch import generate_pitch_deck
from demo_to_deck.inspector.local import inspect_local_path
from demo_to_deck.models import (
    DeckArchetype,
    DeckTheme,
    PitchDeck,
    ProjectProfile,
)
from demo_to_deck.screenshots.capture import render_placeholder_screenshot


class TestDemoToDeck(unittest.TestCase):
    def test_inspect_sample_demo_app(self):
        root = Path(__file__).resolve().parent.parent / "sample_demo_app"
        inspection = inspect_local_path(root)

        self.assertEqual(inspection["name"], "sample_demo_app")
        self.assertEqual(inspection["source_type"], "local")
        self.assertIn("readme_text", inspection)
        self.assertGreater(len(inspection["relative_files"]), 0)

    def test_build_profile_with_readiness_score(self):
        sample_inspection = {
            "name": "Test Project",
            "source_type": "local",
            "source_path": "/tmp/test",
            "readme_sections": {
                "overview": "A test project designed to verify functionality.",
                "features": "- Fast analysis\n- Automated decks\n- Accurate facts",
                "setup": "Run pip install -r requirements.txt",
                "demo": "Open the web app and view dashboard.",
            },
            "readme_text": "Sample readme text with full documentation.",
            "signals": {"frameworks": ["FastAPI"], "languages": ["Python"], "has_tests": True},
            "key_files": [],
            "warnings": [],
        }

        profile = build_project_profile(sample_inspection)
        self.assertEqual(profile.name, "Test Project")
        self.assertGreaterEqual(profile.readiness_score, 80)
        self.assertGreater(len(profile.facts()), 0)
        self.assertTrue(any("Fast analysis" in c.text for c in profile.features))

    def test_archetypes_generation(self):
        sample_inspection = {
            "name": "PulseCheck",
            "source_type": "local",
            "source_path": "./sample_demo_app",
            "readme_sections": {
                "overview": "PulseCheck is a productivity checklist for demos.",
                "features": "- Visual status indicator\n- One-click reset",
                "setup": "python sample_demo_app/server.py",
            },
            "readme_text": "PulseCheck helps verify demo status.",
            "signals": {},
            "key_files": [],
            "warnings": [],
        }
        profile = build_project_profile(sample_inspection)

        # Investor archetype (7 slides)
        deck_investor = generate_pitch_deck(profile, use_llm=False, archetype=DeckArchetype.INVESTOR)
        self.assertEqual(len(deck_investor.slides), 7)
        self.assertEqual(deck_investor.archetype, DeckArchetype.INVESTOR)

        # Tech Demo archetype (6 slides)
        deck_tech = generate_pitch_deck(profile, use_llm=False, archetype=DeckArchetype.TECH_DEMO)
        self.assertEqual(len(deck_tech.slides), 6)
        self.assertEqual(deck_tech.archetype, DeckArchetype.TECH_DEMO)

        # Customer archetype (5 slides)
        deck_customer = generate_pitch_deck(profile, use_llm=False, archetype=DeckArchetype.CUSTOMER)
        self.assertEqual(len(deck_customer.slides), 5)

        # Lightning archetype (4 slides)
        deck_lightning = generate_pitch_deck(profile, use_llm=False, archetype=DeckArchetype.LIGHTNING)
        self.assertEqual(len(deck_lightning.slides), 4)

    def test_duration_scaling(self):
        sample_inspection = {
            "name": "QuickPitch",
            "source_type": "local",
            "source_path": ".",
            "readme_sections": {"overview": "Quick pitch project"},
            "readme_text": "Overview",
            "signals": {},
            "key_files": [],
            "warnings": [],
        }
        profile = build_project_profile(sample_inspection)
        deck = generate_pitch_deck(profile, use_llm=False, target_duration_minutes=3)
        self.assertAlmostEqual(deck.total_duration_seconds, 180, delta=15)

    def test_export_bundle_with_themes(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            sample_inspection = {
                "name": "ThemedDeck",
                "source_type": "local",
                "source_path": "./sample_demo_app",
                "readme_sections": {"overview": "Sample test project for export"},
                "readme_text": "Overview",
                "signals": {},
                "key_files": [],
                "warnings": [],
            }
            profile = build_project_profile(sample_inspection)

            # Test dark theme export
            deck_midnight = generate_pitch_deck(
                profile,
                use_llm=False,
                archetype=DeckArchetype.INVESTOR,
                theme=DeckTheme.MIDNIGHT,
            )
            bundle = export_bundle(deck_midnight, profile, output_dir=tmp_path)
            self.assertTrue(Path(bundle["pptx"]).exists())
            self.assertTrue(Path(bundle["script"]).exists())
            self.assertTrue(Path(bundle["source_notes"]).exists())
            self.assertTrue(Path(bundle["deck_json"]).exists())

    def test_render_placeholder_mockup(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            shot_file = Path(tmp_dir) / "test_mockup.png"
            rendered = render_placeholder_screenshot(shot_file, title="Test Mockup", subtitle="Subtitle")
            self.assertTrue(rendered.exists())
            self.assertGreater(rendered.stat().st_size, 1000)


if __name__ == "__main__":
    unittest.main()
