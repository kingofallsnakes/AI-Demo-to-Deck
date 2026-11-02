"""Build a ProjectProfile that separates repository facts from inferences."""

from __future__ import annotations

import re
from typing import Any

from demo_to_deck.inspector.filesystem import extract_bullet_lines
from demo_to_deck.models import Claim, ClaimKind, FileSummary, ProjectProfile

FEATURE_SECTION_KEYS = (
    "features",
    "feature",
    "what it does",
    "functionality",
    "capabilities",
    "highlights",
)
SETUP_SECTION_KEYS = (
    "setup",
    "installation",
    "install",
    "getting started",
    "quickstart",
    "quick start",
    "usage",
    "run",
    "running",
    "development",
)
DEMO_SECTION_KEYS = (
    "demo",
    "walkthrough",
    "tutorial",
    "example",
    "examples",
    "how to use",
    "user guide",
)
PURPOSE_SECTION_KEYS = (
    "intro",
    "introduction",
    "overview",
    "about",
    "description",
    "github_description",
    "why",
    "motivation",
)


def _section_match(sections: dict[str, str], keys: tuple[str, ...]) -> list[tuple[str, str]]:
    found: list[tuple[str, str]] = []
    for heading, body in sections.items():
        for key in keys:
            if key in heading:
                found.append((heading, body))
                break
    return found


def _first_paragraph(text: str) -> str:
    chunks = [c.strip() for c in re.split(r"\n\s*\n", text.strip()) if c.strip()]
    if not chunks:
        return ""
    # Prefer a prose paragraph over a badge/link line
    for chunk in chunks:
        if chunk.startswith("[!") or chunk.startswith("<") or chunk.startswith("[!["):
            continue
        line = " ".join(chunk.split())
        if len(line) > 30:
            return line[:400]
    return " ".join(chunks[0].split())[:400]


def _fact(text: str, source: str) -> Claim:
    return Claim(text=text.strip(), kind=ClaimKind.FACT, source=source, confidence=1.0)


def _inference(text: str, source: str, confidence: float = 0.6) -> Claim:
    return Claim(text=text.strip(), kind=ClaimKind.INFERENCE, source=source, confidence=confidence)


def build_project_profile(inspection: dict[str, Any]) -> ProjectProfile:
    name = inspection.get("name") or "Untitled Project"
    sections: dict[str, str] = inspection.get("readme_sections") or {}
    readme = inspection.get("readme_text") or ""
    signals: dict[str, Any] = inspection.get("signals") or {}
    warnings: list[str] = list(inspection.get("warnings") or [])

    purpose: list[Claim] = []
    features: list[Claim] = []
    setup_steps: list[Claim] = []
    demo_flow: list[Claim] = []
    tech_stack: list[Claim] = []

    # Calculate readiness score components
    score = 0

    # --- Purpose (facts from README / GitHub description) ---
    purpose_sections = _section_match(sections, PURPOSE_SECTION_KEYS)
    if purpose_sections:
        para = _first_paragraph(purpose_sections[0][1]) or _first_paragraph(readme)
        if para:
            purpose.append(_fact(para, f"README#{purpose_sections[0][0]}"))
            score += 25
    elif readme:
        para = _first_paragraph(readme)
        if para:
            purpose.append(_fact(para, "README"))
            score += 20
    gh = inspection.get("github") or {}
    if gh.get("description") and not purpose:
        purpose.append(_fact(gh["description"], "GitHub repository description"))
        score += 20

    if not purpose:
        langs = ", ".join(signals.get("languages") or []) or "unknown stack"
        purpose.append(
            _inference(
                f"{name} appears to be a software project ({langs}) based on repository layout; "
                "purpose was not clearly stated in documentation.",
                "inferred from file layout",
                0.45,
            )
        )
        warnings.append("No clear purpose statement found in README; purpose was inferred.")
        score += 5

    # --- Features ---
    feature_matches = _section_match(sections, FEATURE_SECTION_KEYS)
    for heading, body in feature_matches:
        for bullet in extract_bullet_lines(body):
            features.append(_fact(bullet, f"README#{heading}"))
    if features:
        score += 20
    else:
        # Infer from frameworks / entry points
        for fw in signals.get("frameworks") or []:
            features.append(
                _inference(f"Provides integration and capabilities powered by {fw}.", "inferred from dependencies", 0.65)
            )
        for hint in signals.get("entry_hints") or []:
            features.append(
                _inference(f"Executes interactive workflows via entrypoint: {hint}", "inferred from manifests", 0.6)
            )
        if not features:
            features.append(
                _inference(
                    "Feature list was not documented; review key source files for capabilities.",
                    "inferred",
                    0.4,
                )
            )
            warnings.append("No feature list found in docs; features were inferred.")
            score += 5
        else:
            score += 10

    # --- Setup steps ---
    setup_matches = _section_match(sections, SETUP_SECTION_KEYS)
    for heading, body in setup_matches:
        bullets = extract_bullet_lines(body)
        if bullets:
            for bullet in bullets:
                setup_steps.append(_fact(bullet, f"README#{heading}"))
        else:
            snippet = _first_paragraph(body)
            if snippet:
                setup_steps.append(_fact(snippet, f"README#{heading}"))
    if setup_steps:
        score += 20
    else:
        pm = signals.get("package_managers") or []
        if "pip/poetry" in pm:
            setup_steps.append(
                _inference("Set up virtual environment, then run: pip install -r requirements.txt", "inferred", 0.7)
            )
        if "npm/yarn/pnpm" in pm:
            setup_steps.append(
                _inference("Install dependencies with npm install, then execute npm start / npm run dev.", "inferred", 0.7)
            )
        if signals.get("has_docker"):
            setup_steps.append(
                _inference("Container execution supported: docker build -t app . && docker run app", "inferred", 0.65)
            )
        if not setup_steps:
            setup_steps.append(
                _inference("Follow the repository README for install/run instructions (none auto-detected).", "inferred", 0.4)
            )
            warnings.append("No setup section found; setup steps were inferred.")
            score += 5
        else:
            score += 12

    # --- Demo flow ---
    demo_matches = _section_match(sections, DEMO_SECTION_KEYS)
    for heading, body in demo_matches:
        bullets = extract_bullet_lines(body)
        if bullets:
            for bullet in bullets:
                demo_flow.append(_fact(bullet, f"README#{heading}"))
        else:
            snippet = _first_paragraph(body)
            if snippet:
                demo_flow.append(_fact(snippet, f"README#{heading}"))
    if demo_flow:
        score += 15
    else:
        demo_flow.extend(
            [
                _inference("Open the app's primary UI entrypoint.", "inferred demo flow", 0.55),
                _inference("Perform the core workflow highlighted in the README.", "inferred demo flow", 0.5),
                _inference("Demonstrate real-time output generation and artifact preview.", "inferred demo flow", 0.45),
                _inference("Export or review generated deliverables with the audience.", "inferred demo flow", 0.45),
            ]
        )
        warnings.append("No demo walkthrough found in docs; demo flow was inferred.")
        score += 5

    # --- Tech stack ---
    for lang in signals.get("languages") or []:
        tech_stack.append(_fact(f"Language: {lang}", "repository files"))
    for fw in signals.get("frameworks") or []:
        tech_stack.append(_fact(f"Framework: {fw}", "repository files"))
    if gh.get("language"):
        tech_stack.append(_fact(f"GitHub Primary Language: {gh['language']}", "GitHub API"))
    if signals.get("has_tests"):
        tech_stack.append(_fact("Test suite is present and configured.", "repository files"))
        score += 10
    if signals.get("has_docker"):
        tech_stack.append(_fact("Docker container configuration detected.", "repository files"))
        score += 5

    if tech_stack:
        score += 10

    readiness_score = min(100, max(20, score))

    # Architecture notes
    arch_notes = []
    if signals.get("has_docker"):
        arch_notes.append("Containerized environment ready for reproducible deployment.")
    if signals.get("has_tests"):
        arch_notes.append("Automated test coverage present in codebase.")
    for entry in signals.get("entry_hints") or []:
        arch_notes.append(f"Entrypoint discovered: {entry}")

    key_files = [
        FileSummary(path=item["path"], role=item["role"], excerpt=item.get("excerpt", ""))
        for item in inspection.get("key_files") or []
    ]

    target_audience = "Software engineers, product teams, and stakeholders"
    problem_statement = purpose[0].text if purpose else f"Streamlining operations and workflows for {name}."

    return ProjectProfile(
        name=name,
        source_type=inspection.get("source_type", "local"),
        source_path=inspection.get("source_path", ""),
        purpose=purpose,
        features=features,
        setup_steps=setup_steps,
        demo_flow=demo_flow,
        tech_stack=tech_stack,
        key_files=key_files,
        readme_text=readme,
        warnings=warnings,
        raw_signals={
            "signals": signals,
            "github": gh,
            "file_count": inspection.get("file_count"),
        },
        readiness_score=readiness_score,
        target_audience=target_audience,
        problem_statement=problem_statement,
        architecture_notes=arch_notes,
        stats={
            "facts_count": len([c for c in purpose + features + setup_steps + demo_flow + tech_stack if c.kind == ClaimKind.FACT]),
            "inferences_count": len([c for c in purpose + features + setup_steps + demo_flow + tech_stack if c.kind == ClaimKind.INFERENCE]),
            "key_files_count": len(key_files),
        },
    )
