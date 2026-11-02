"""Command-line entrypoint for demo-to-deck."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from demo_to_deck.analyzer.profile import build_project_profile
from demo_to_deck.deck.export import export_bundle
from demo_to_deck.generator.pitch import generate_pitch_deck
from demo_to_deck.inspector.github import fetch_public_github_repo, is_probably_github_url
from demo_to_deck.inspector.local import inspect_local_path
from demo_to_deck.models import DeckArchetype, DeckTheme


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="demo-to-deck",
        description="Turn a repository into a structured pitch deck and timed script.",
    )
    parser.add_argument(
        "source",
        nargs="?",
        default="sample_demo_app",
        help="Local directory path or public GitHub URL (default: sample_demo_app)",
    )
    parser.add_argument(
        "--output-dir",
        "-o",
        default="output",
        help="Directory to save generated PPTX, script, and notes (default: output)",
    )
    parser.add_argument(
        "--archetype",
        "-a",
        choices=["investor", "tech_demo", "customer", "lightning"],
        default="investor",
        help="Pitch deck archetype (default: investor)",
    )
    parser.add_argument(
        "--theme",
        "-t",
        choices=["emerald", "midnight", "ocean", "sunset"],
        default="emerald",
        help="Visual color theme for PowerPoint slides (default: emerald)",
    )
    parser.add_argument(
        "--duration",
        "-d",
        type=int,
        default=None,
        help="Target presentation duration in minutes (e.g. 3, 5, 10)",
    )
    parser.add_argument(
        "--no-llm",
        action="store_true",
        help="Force rule-based generation even if an LLM key is present",
    )
    args = parser.parse_args(argv)

    source = args.source
    output_dir = Path(args.output_dir).resolve()
    use_llm = not args.no_llm
    archetype = DeckArchetype(args.archetype)
    theme = DeckTheme(args.theme)

    print(f"[*] Inspecting target: {source}")
    try:
        if is_probably_github_url(source):
            inspection = fetch_public_github_repo(source)
        else:
            local_path = Path(source).resolve()
            if not local_path.exists():
                print(f"[!] Error: Path '{local_path}' does not exist.", file=sys.stderr)
                return 1
            inspection = inspect_local_path(local_path)
    except Exception as exc:
        print(f"[!] Inspection failed: {exc}", file=sys.stderr)
        return 1

    profile = build_project_profile(inspection)
    print(f"[+] Analyzed '{profile.name}'")
    print(f"    - Readiness score: {profile.readiness_score}/100")
    print(f"    - Verified facts: {len(profile.facts())}")
    print(f"    - Inferences: {len(profile.inferences())}")
    print(f"    - Key files: {len(profile.key_files)}")

    print(f"[*] Generating {archetype.value.upper()} pitch deck (theme: {theme.value})...")
    deck = generate_pitch_deck(
        profile,
        use_llm=use_llm,
        archetype=archetype,
        theme=theme,
        target_duration_minutes=args.duration,
    )
    mins = deck.total_duration_seconds // 60
    secs = deck.total_duration_seconds % 60
    print(f"[+] Deck ready: {len(deck.slides)} slides ({mins}m {secs:02d}s) [mode: {deck.generation_mode}]")

    print(f"[*] Exporting bundle to {output_dir}...")
    bundle = export_bundle(deck, profile, output_dir=output_dir)
    print("[+] Export complete:")
    for key, path in bundle.items():
        print(f"    - {key}: {path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
