"""Multi-archetype pitch deck + timed script generator with pacing calculations."""

from __future__ import annotations

from demo_to_deck.generator.llm import enhance_slide_copy, llm_available
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


def _texts(claims: list[Claim], prefer_facts: bool = True, limit: int = 5) -> list[str]:
    ordered = claims
    if prefer_facts:
        facts = [c for c in claims if c.kind == ClaimKind.FACT]
        inferences = [c for c in claims if c.kind == ClaimKind.INFERENCE]
        ordered = facts + inferences
    return [c.text for c in ordered[:limit]]


def _tag_source_notes(claims: list[Claim], limit: int = 6) -> list[str]:
    notes: list[str] = []
    for claim in claims[:limit]:
        label = "FACT" if claim.kind == ClaimKind.FACT else "INFERRED"
        src = f" — {claim.source}" if claim.source else ""
        notes.append(f"[{label}] {claim.text}{src}")
    return notes


def _build_investor_slides(profile: ProjectProfile) -> list[Slide]:
    purpose = _texts(profile.purpose, limit=2)
    features = _texts(profile.features, limit=4)
    setup = _texts(profile.setup_steps, limit=3)
    demo = _texts(profile.demo_flow, limit=4)
    stack = _texts(profile.tech_stack, limit=4)

    tagline = purpose[0] if purpose else f"High-impact overview of {profile.name}"

    return [
        Slide(
            number=1,
            title=profile.name,
            bullets=[
                tagline[:160],
                f"Source: {profile.source_type} ({profile.source_path})",
                "Automated pitch walkthrough generated from static repository inspection",
            ],
            speaker_notes=(
                f"Welcome everyone. Today I'm excited to present {profile.name}. "
                f"{tagline} Over the next few minutes, I'll unpack the problem we solve, "
                f"demonstrate the product live, and outline our technological moat."
            ),
            duration_seconds=45,
            screenshot_hint="Title / splash overview screen",
            source_notes=_tag_source_notes(profile.purpose),
            layout=SlideLayout.TITLE,
        ),
        Slide(
            number=2,
            title="The Market Opportunity & Pain",
            bullets=purpose[:3] or [
                "Modern teams struggle with friction between repository reality and stakeholder decks.",
                "Manual deck preparation is slow, repetitive, and introduces inaccurate claims.",
            ],
            speaker_notes=(
                "Let's anchor on the core pain. Today's problem is clear from what users experience: "
                "teams lose hours translating code into stakeholder narratives. Here is the verified opportunity."
            ),
            duration_seconds=60,
            source_notes=_tag_source_notes(profile.purpose),
        ),
        Slide(
            number=3,
            title="The Solution & Core Features",
            bullets=features or ["Automated feature extraction and verified capability reporting."],
            speaker_notes=(
                f"Here is what {profile.name} delivers. Notice that every claim shown is rooted "
                "in verified repository capabilities, keeping the product's promise completely defensible."
            ),
            duration_seconds=75,
            screenshot_hint="Primary feature interface",
            source_notes=_tag_source_notes(profile.features),
            layout=SlideLayout.FEATURE_GRID,
        ),
        Slide(
            number=4,
            title="Technical Moat & Architecture",
            bullets=stack or ["Lightweight, highly modular architecture evidenced by repository signals."],
            speaker_notes=(
                "Under the hood, our technical moat is built on robust, production-tested technologies. "
                "We leverage verified frameworks and modular components to maintain high velocity and zero runtime bloat."
            ),
            duration_seconds=45,
            source_notes=_tag_source_notes(profile.tech_stack),
        ),
        Slide(
            number=5,
            title="Interactive Demo Walkthrough",
            bullets=demo or [
                "Step 1: Ingest source repository statically without running arbitrary code.",
                "Step 2: Dissect facts vs inferences with confidence metrics.",
                "Step 3: Export production-ready PPTX and synchronized speaking notes.",
            ],
            speaker_notes=(
                "Now let's walk through the live demo. Watch the seamless flow: "
                "from first entry point to core interaction, and notice how effortlessly the end state is reached."
            ),
            duration_seconds=90,
            screenshot_hint="Live demonstration walkthrough capture",
            source_notes=_tag_source_notes(profile.demo_flow),
            layout=SlideLayout.DEMO_SCREEN,
        ),
        Slide(
            number=6,
            title="Frictionless Adoption",
            bullets=setup or [
                "Standard dependency installation via manifest.",
                "Single-command launch for developer and stakeholder workflows.",
            ],
            speaker_notes=(
                "Adoption friction is effectively zero. A developer or user can get up and running "
                "in under two minutes following the verified setup sequence directly from the repository."
            ),
            duration_seconds=45,
            source_notes=_tag_source_notes(profile.setup_steps),
        ),
        Slide(
            number=7,
            title="The Ask & Next Milestones",
            bullets=[
                f"Accelerate adoption for {profile.name} across early adopters and pilot teams.",
                "Ground-truth verification ensures stakeholder trust and repeatable delivery.",
                "Call to action: Review repository, start a pilot, and partner on next milestones.",
            ],
            speaker_notes=(
                "To conclude, we're asking for pilot partners and early feedback. "
                f"Thank you for your time, and I'd love to take any questions or walk through {profile.name} in more detail."
            ),
            duration_seconds=40,
            source_notes=[
                "[FACT] Concluding milestone slide structured for investor call-to-action.",
                *[f"[NOTE] {w}" for w in profile.warnings[:2]],
            ],
            layout=SlideLayout.CALL_TO_ACTION,
        ),
    ]


def _build_tech_demo_slides(profile: ProjectProfile) -> list[Slide]:
    purpose = _texts(profile.purpose, limit=2)
    features = _texts(profile.features, limit=4)
    setup = _texts(profile.setup_steps, limit=4)
    demo = _texts(profile.demo_flow, limit=4)
    stack = _texts(profile.tech_stack, limit=5)

    return [
        Slide(
            number=1,
            title=f"{profile.name} — Technical Architecture & Demo",
            bullets=[
                purpose[0] if purpose else f"Engineering deep dive into {profile.name}",
                f"Environment: {profile.source_type} · Path: {profile.source_path}",
                "Comprehensive architecture overview, manifests, and live walkthrough",
            ],
            speaker_notes=(
                f"Welcome engineers and technical leads. Today's session is a technical architectural walkthrough of {profile.name}. "
                "We will examine system design, dependencies, and execution flow."
            ),
            duration_seconds=45,
            layout=SlideLayout.TITLE,
        ),
        Slide(
            number=2,
            title="System Capabilities & Functional Boundaries",
            bullets=features or ["Core functional modules verified through codebase analysis."],
            speaker_notes=(
                "These are the core capabilities exposed by the system. "
                "Notice the strict separation between deterministic functions and heuristic analyzers."
            ),
            duration_seconds=60,
            source_notes=_tag_source_notes(profile.features),
        ),
        Slide(
            number=3,
            title="Technology Stack & Manifest Evidence",
            bullets=stack or ["Standard language toolchains and packaging manifests."],
            speaker_notes=(
                "Reviewing the tech stack: these are the verified languages, package managers, "
                "and runtime frameworks detected directly in repository manifests."
            ),
            duration_seconds=50,
            source_notes=_tag_source_notes(profile.tech_stack),
        ),
        Slide(
            number=4,
            title="Key File Roles & Codebase Topology",
            bullets=[f"`{f.path}` ({f.role}): {f.excerpt[:90]}..." for f in profile.key_files[:4]]
            or ["Clean modular file layout with distinct domain layers."],
            speaker_notes=(
                "Here is the codebase topology. The primary entry point orchestrates key components "
                "while models isolate state and serialization."
            ),
            duration_seconds=55,
        ),
        Slide(
            number=5,
            title="Execution Pipeline & Live Demo Flow",
            bullets=demo or ["Sequential pipeline executing static analysis and artifact generation."],
            speaker_notes=(
                "Let's trace the live execution path. Each phase validates preconditions before piping "
                "structured payloads downstream."
            ),
            duration_seconds=90,
            screenshot_hint="Pipeline or application interface",
            source_notes=_tag_source_notes(profile.demo_flow),
        ),
        Slide(
            number=6,
            title="Developer Setup & Tooling Runbook",
            bullets=setup or ["Step 1: Clone repo -> Step 2: Install dependencies -> Step 3: Run target."],
            speaker_notes=(
                "For developers wishing to contribute or test locally, here is the exact setup runbook "
                "extracted from repository documentation."
            ),
            duration_seconds=60,
            source_notes=_tag_source_notes(profile.setup_steps),
        ),
    ]


def _build_customer_slides(profile: ProjectProfile) -> list[Slide]:
    purpose = _texts(profile.purpose, limit=2)
    features = _texts(profile.features, limit=4)
    setup = _texts(profile.setup_steps, limit=3)
    demo = _texts(profile.demo_flow, limit=4)

    return [
        Slide(
            number=1,
            title=profile.name,
            bullets=[
                purpose[0] if purpose else f"Introducing {profile.name}",
                "Designed to simplify and accelerate your core workflows",
            ],
            speaker_notes=f"Hello and welcome. Today we're thrilled to introduce {profile.name}, built to solve key operational challenges.",
            duration_seconds=45,
            layout=SlideLayout.TITLE,
        ),
        Slide(
            number=2,
            title="The Challenges You Face Today",
            bullets=purpose[:2] or ["Disorganized presentation creation and uncertain technical claims."],
            speaker_notes="Every day, teams spend valuable hours wrestling with manual reporting. Here's why that friction matters.",
            duration_seconds=60,
        ),
        Slide(
            number=3,
            title="How We Solve It",
            bullets=features or ["Fast, verified capability reporting with instant presentation export."],
            speaker_notes=f"Here is how {profile.name} solves this problem directly, giving you speed, accuracy, and confidence.",
            duration_seconds=75,
            source_notes=_tag_source_notes(profile.features),
        ),
        Slide(
            number=4,
            title="See It In Action",
            bullets=demo or ["Intuitive step-by-step user journey."],
            speaker_notes="Let me show you how simple it is in practice. In just three clicks, your deliverables are generated.",
            duration_seconds=90,
            screenshot_hint="Customer workflow UI",
            source_notes=_tag_source_notes(profile.demo_flow),
        ),
        Slide(
            number=5,
            title="Immediate Time to Value",
            bullets=setup or ["Zero complex configuration required."],
            speaker_notes="Getting started takes minutes. Your team can begin seeing results today without extensive training.",
            duration_seconds=45,
            source_notes=_tag_source_notes(profile.setup_steps),
        ),
    ]


def _build_lightning_slides(profile: ProjectProfile) -> list[Slide]:
    purpose = _texts(profile.purpose, limit=1)
    features = _texts(profile.features, limit=3)
    demo = _texts(profile.demo_flow, limit=3)

    return [
        Slide(
            number=1,
            title=f"⚡ {profile.name}",
            bullets=[purpose[0] if purpose else "The fastest way to turn code into investor-ready decks."],
            speaker_notes=f"Hi everyone, we built {profile.name}! {purpose[0] if purpose else 'We turn code into ready-to-present decks.'}",
            duration_seconds=20,
            layout=SlideLayout.TITLE,
        ),
        Slide(
            number=2,
            title="The Problem & Our Innovation",
            bullets=features or ["Automated fact extraction with instant deck output."],
            speaker_notes="Engineers hate making slides; investors hate fluff. We bridge the gap by generating truthful pitch decks directly from code.",
            duration_seconds=30,
            source_notes=_tag_source_notes(profile.features),
        ),
        Slide(
            number=3,
            title="Live Demo Moment",
            bullets=demo or ["One-click static inspection and PowerPoint generation."],
            speaker_notes="Here it is live in action. Watch as the repo is scanned, verified facts are separated, and the full deck is generated in seconds.",
            duration_seconds=35,
            screenshot_hint="Killer feature highlight",
            source_notes=_tag_source_notes(profile.demo_flow),
        ),
        Slide(
            number=4,
            title="What's Next & Thank You",
            bullets=[
                f"{profile.name} is open-source and ready to try right now.",
                "Next milestone: multi-model agent fine-tuning and template marketplace.",
            ],
            speaker_notes="Thank you! Check out the project on GitHub and let us know what you think.",
            duration_seconds=15,
            layout=SlideLayout.CALL_TO_ACTION,
        ),
    ]


def _script_markdown(deck_name: str, slides: list[Slide], archetype: DeckArchetype) -> str:
    total_seconds = sum(s.duration_seconds for s in slides)
    total_words = sum(len(s.speaker_notes.split()) for s in slides)
    avg_wpm = int((total_words / (total_seconds / 60))) if total_seconds > 0 else 130

    lines = [
        f"# Presentation Script — {deck_name}",
        f"**Archetype:** {archetype.value.upper()}  |  **Target Duration:** {total_seconds // 60}m {total_seconds % 60:02d}s  |  **Pacing:** ~{avg_wpm} words/min ({total_words} total words)",
        "",
        "---",
        "",
    ]
    elapsed = 0
    for slide in slides:
        start = elapsed
        end = elapsed + slide.duration_seconds
        words = len(slide.speaker_notes.split())
        lines.extend(
            [
                f"## Slide {slide.number}: {slide.title}",
                f"*⏱️ Timer: {start // 60}:{start % 60:02d} – {end // 60}:{end % 60:02d} "
                f"({slide.duration_seconds}s | ~{words} words)*",
                "",
                f"> **Spoken Script:**",
                f"> {slide.speaker_notes}",
                "",
                "**On-screen bullets:**",
            ]
        )
        for bullet in slide.bullets:
            lines.append(f"- {bullet}")
        if slide.screenshot_hint:
            lines.extend(["", f"*📸 Visual cue:* {slide.screenshot_hint}"])
        lines.append("")
        elapsed = end
    return "\n".join(lines).strip() + "\n"


def _source_notes_markdown(profile: ProjectProfile, slides: list[Slide]) -> str:
    lines = [
        f"# Source Notes & Ground-Truth Audit — {profile.name}",
        "",
        "Every claim in Demo-to-Deck is strictly labeled **[FACT]** (verified from repository manifests/docs) "
        "or **[INFERRED]** (interpreted by the heuristic analyzer).",
        "",
        f"**Repository Readiness Score:** {profile.readiness_score}/100",
        "",
        "## Warnings & Missing Documentation",
    ]
    if profile.warnings:
        for warning in profile.warnings:
            lines.append(f"- ⚠️ {warning}")
    else:
        lines.append("- ✅ No documentation deficiencies flagged.")

    lines.extend(["", "## Slide-by-Slide Citations"])
    for slide in slides:
        lines.append(f"### Slide {slide.number}: {slide.title}")
        if slide.source_notes:
            for note in slide.source_notes:
                lines.append(f"- {note}")
        else:
            lines.append("- *(Standard pitch transition slide)*")
        lines.append("")

    lines.extend(["", "## Ground-Truth Facts Summary"])
    for claim in profile.facts():
        lines.append(f"- `FACT` {claim.text} *(Source: {claim.source or 'manifest'})*")

    lines.extend(["", "## Inferred Statements Summary"])
    for claim in profile.inferences():
        lines.append(f"- `INFERRED` {claim.text} *(Confidence: {int(claim.confidence * 100)}%)*")
    lines.append("")
    return "\n".join(lines)


def generate_pitch_deck(
    profile: ProjectProfile,
    use_llm: bool = True,
    archetype: DeckArchetype = DeckArchetype.INVESTOR,
    theme: DeckTheme = DeckTheme.EMERALD,
    target_duration_minutes: int | None = None,
) -> PitchDeck:
    """Generate a structured pitch deck customized to the requested archetype and theme."""
    if archetype == DeckArchetype.INVESTOR:
        slides = _build_investor_slides(profile)
    elif archetype == DeckArchetype.TECH_DEMO:
        slides = _build_tech_demo_slides(profile)
    elif archetype == DeckArchetype.CUSTOMER:
        slides = _build_customer_slides(profile)
    elif archetype == DeckArchetype.LIGHTNING:
        slides = _build_lightning_slides(profile)
    else:
        slides = _build_investor_slides(profile)

    # Scale slide durations if target_duration_minutes is requested
    if target_duration_minutes and target_duration_minutes > 0:
        target_total_sec = target_duration_minutes * 60
        current_total = sum(s.duration_seconds for s in slides)
        if current_total > 0:
            scale = target_total_sec / current_total
            for s in slides:
                s.duration_seconds = max(15, int(s.duration_seconds * scale))

    mode = "rule_based"

    if use_llm and llm_available():
        payload = [
            {
                "number": s.number,
                "title": s.title,
                "bullets": s.bullets,
                "speaker_notes": s.speaker_notes,
                "duration_seconds": s.duration_seconds,
            }
            for s in slides
        ]
        enhanced = enhance_slide_copy(payload, profile.name, archetype=archetype.value)
        if enhanced:
            mode = "llm_enhanced"
            rebuilt: list[Slide] = []
            for original, update in zip(slides, enhanced):
                rebuilt.append(
                    Slide(
                        number=original.number,
                        title=update.get("title", original.title),
                        bullets=update.get("bullets", original.bullets),
                        speaker_notes=update.get("speaker_notes", original.speaker_notes),
                        duration_seconds=original.duration_seconds,
                        screenshot_hint=original.screenshot_hint,
                        source_notes=original.source_notes,
                        layout=original.layout,
                        target_screenshot_index=original.target_screenshot_index,
                    )
                )
            slides = rebuilt

    purpose = _texts(profile.purpose, limit=1)
    tagline = purpose[0] if purpose else f"Pitch deck for {profile.name}"
    script = _script_markdown(profile.name, slides, archetype)
    notes = _source_notes_markdown(profile, slides)

    return PitchDeck(
        project_name=profile.name,
        tagline=tagline[:200],
        slides=slides,
        total_duration_seconds=sum(s.duration_seconds for s in slides),
        generation_mode=mode,
        archetype=archetype,
        theme=theme,
        script_markdown=script,
        source_notes_markdown=notes,
    )
