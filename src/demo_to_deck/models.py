"""Shared data models for inspection, analysis, and deck generation."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class ClaimKind(str, Enum):
    FACT = "fact"
    INFERENCE = "inference"


class DeckArchetype(str, Enum):
    INVESTOR = "investor"          # 7-slide seed/angel deck with problem, moat, market & ask
    TECH_DEMO = "tech_demo"        # 6-8 slide technical architectural walkthrough & deep dive
    CUSTOMER = "customer"          # 5-6 slide product value proposition & user workflow
    LIGHTNING = "lightning"        # 4-slide fast hackathon/lightning pitch (90-120s)


class DeckTheme(str, Enum):
    EMERALD = "emerald"    # Modern Forest Green (#0F382C / #1F6F5B / #10B981)
    MIDNIGHT = "midnight"  # Dark Slate & Indigo (#0F172A / #1E293B / #6366F1)
    OCEAN = "ocean"        # Corporate Navy & Cobalt (#0C4A6E / #1D4ED8 / #38BDF8)
    SUNSET = "sunset"      # Warm Charcoal & Tangerine (#1C1917 / #EA580C / #F97316)


class SlideLayout(str, Enum):
    TITLE = "title"
    SPLIT_CONTENT = "split_content"
    FEATURE_GRID = "feature_grid"
    DEMO_SCREEN = "demo_screen"
    METRICS_SUMMARY = "metrics_summary"
    CALL_TO_ACTION = "call_to_action"


@dataclass
class Claim:
    """A single statement about the project, tagged as fact or inference."""

    text: str
    kind: ClaimKind
    source: str = ""
    confidence: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["kind"] = self.kind.value
        return data


@dataclass
class FileSummary:
    path: str
    role: str
    excerpt: str = ""


@dataclass
class ProjectProfile:
    """Structured understanding of a project after static inspection."""

    name: str
    source_type: str  # local | github
    source_path: str
    purpose: list[Claim] = field(default_factory=list)
    features: list[Claim] = field(default_factory=list)
    setup_steps: list[Claim] = field(default_factory=list)
    demo_flow: list[Claim] = field(default_factory=list)
    tech_stack: list[Claim] = field(default_factory=list)
    key_files: list[FileSummary] = field(default_factory=list)
    readme_text: str = ""
    warnings: list[str] = field(default_factory=list)
    raw_signals: dict[str, Any] = field(default_factory=dict)
    # Advanced metadata
    readiness_score: int = 75
    target_audience: str = ""
    problem_statement: str = ""
    architecture_notes: list[str] = field(default_factory=list)
    stats: dict[str, Any] = field(default_factory=dict)

    def facts(self) -> list[Claim]:
        buckets = (
            self.purpose
            + self.features
            + self.setup_steps
            + self.demo_flow
            + self.tech_stack
        )
        return [c for c in buckets if c.kind == ClaimKind.FACT]

    def inferences(self) -> list[Claim]:
        buckets = (
            self.purpose
            + self.features
            + self.setup_steps
            + self.demo_flow
            + self.tech_stack
        )
        return [c for c in buckets if c.kind == ClaimKind.INFERENCE]

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "source_type": self.source_type,
            "source_path": self.source_path,
            "purpose": [c.to_dict() for c in self.purpose],
            "features": [c.to_dict() for c in self.features],
            "setup_steps": [c.to_dict() for c in self.setup_steps],
            "demo_flow": [c.to_dict() for c in self.demo_flow],
            "tech_stack": [c.to_dict() for c in self.tech_stack],
            "key_files": [asdict(f) for f in self.key_files],
            "readme_text": self.readme_text,
            "warnings": self.warnings,
            "raw_signals": self.raw_signals,
            "readiness_score": self.readiness_score,
            "target_audience": self.target_audience,
            "problem_statement": self.problem_statement,
            "architecture_notes": self.architecture_notes,
            "stats": self.stats,
        }


@dataclass
class Slide:
    number: int
    title: str
    bullets: list[str]
    speaker_notes: str
    duration_seconds: int
    screenshot_hint: str = ""
    source_notes: list[str] = field(default_factory=list)
    layout: SlideLayout = SlideLayout.SPLIT_CONTENT
    subtitle: str = ""
    metrics: list[dict[str, str]] = field(default_factory=list)  # [{"label": "Latency", "value": "<50ms"}]
    target_screenshot_index: int | None = None


@dataclass
class PitchDeck:
    project_name: str
    tagline: str
    slides: list[Slide]
    total_duration_seconds: int
    generation_mode: str  # rule_based | llm_enhanced
    archetype: DeckArchetype = DeckArchetype.INVESTOR
    theme: DeckTheme = DeckTheme.EMERALD
    script_markdown: str = ""
    source_notes_markdown: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "project_name": self.project_name,
            "tagline": self.tagline,
            "total_duration_seconds": self.total_duration_seconds,
            "generation_mode": self.generation_mode,
            "archetype": self.archetype.value if hasattr(self.archetype, "value") else str(self.archetype),
            "theme": self.theme.value if hasattr(self.theme, "value") else str(self.theme),
            "slides": [asdict(s) for s in self.slides],
            "script_markdown": self.script_markdown,
            "source_notes_markdown": self.source_notes_markdown,
        }
