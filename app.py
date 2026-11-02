"""
Streamlit application for Demo-to-Deck — Advanced AI Pitch Generator & Repository Intelligence.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Add src to sys.path so demo_to_deck can be imported directly
ROOT_DIR = Path(__file__).resolve().parent
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import streamlit as st
from dotenv import load_dotenv

from demo_to_deck.analyzer.profile import build_project_profile
from demo_to_deck.deck.export import THEME_PALETTES, export_bundle
from demo_to_deck.generator.llm import get_active_provider, llm_available
from demo_to_deck.generator.pitch import generate_pitch_deck
from demo_to_deck.inspector.github import (
    PrivateOrInaccessibleRepoError,
    fetch_public_github_repo,
    is_probably_github_url,
)
from demo_to_deck.inspector.local import inspect_local_path
from demo_to_deck.models import (
    ClaimKind,
    DeckArchetype,
    DeckTheme,
    PitchDeck,
    ProjectProfile,
    Slide,
)
from demo_to_deck.screenshots.capture import capture_url_screenshot, render_placeholder_screenshot

load_dotenv()

OUTPUT_DIR = ROOT_DIR / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def setup_page() -> None:
    st.set_page_config(
        page_title="Demo-to-Deck | Advanced AI Pitch Generator",
        page_icon="🎯",
        layout="wide",
        initial_sidebar_state="expanded",
    )


def init_session_state() -> None:
    if "profile" not in st.session_state:
        st.session_state.profile = None
    if "deck" not in st.session_state:
        st.session_state.deck = None
    if "bundle_paths" not in st.session_state:
        st.session_state.bundle_paths = None
    if "screenshots" not in st.session_state:
        st.session_state.screenshots = []
    if "presenter_slide_idx" not in st.session_state:
        st.session_state.presenter_slide_idx = 0


def run_inspection(source_type: str, source_target: str) -> ProjectProfile | None:
    try:
        with st.spinner(f"Scanning {source_type}: {source_target}..."):
            if source_type == "GitHub Repository":
                inspection = fetch_public_github_repo(source_target)
            else:
                path = Path(source_target).resolve()
                if not path.exists():
                    st.error(f"Directory not found: `{path}`")
                    return None
                inspection = inspect_local_path(path)

            profile = build_project_profile(inspection)
            return profile
    except PrivateOrInaccessibleRepoError as exc:
        st.error(f"GitHub access error: {exc}")
        return None
    except Exception as exc:
        st.error(f"Failed to inspect repository: {exc}")
        return None


def main() -> None:
    setup_page()
    init_session_state()

    # --- Header ---
    col_h1, col_h2 = st.columns([4, 1])
    with col_h1:
        st.title("🎯 Demo-to-Deck")
        st.caption(
            "Executive AI Pitch Generator: Turn any codebase into publication-ready PowerPoint presentations, "
            "timed presenter scripts, and defensible ground-truth audits."
        )
    with col_h2:
        provider = get_active_provider()
        if provider == "gemini":
            st.success("🟢 AI: Google Gemini")
        elif provider == "openai":
            st.success("🟢 AI: OpenAI")
        elif provider == "anthropic":
            st.success("🟢 AI: Anthropic")
        else:
            st.info("⚡ Rule Engine (Local)")

    # --- Sidebar Configuration ---
    with st.sidebar:
        st.header("⚙️ Pitch Deck Studio")

        # Archetype selector
        archetype_map = {
            "💼 Investor Seed Pitch (7 slides)": DeckArchetype.INVESTOR,
            "⚙️ Technical Architecture (6 slides)": DeckArchetype.TECH_DEMO,
            "🛍️ Customer / Solution Walkthrough (5 slides)": DeckArchetype.CUSTOMER,
            "⚡ Lightning / Hackathon (4 slides)": DeckArchetype.LIGHTNING,
        }
        selected_archetype_label = st.selectbox("Presentation Archetype", list(archetype_map.keys()), index=0)
        chosen_archetype = archetype_map[selected_archetype_label]

        # Theme selector
        theme_map = {
            "🌲 Modern Emerald (Forest & Jade)": DeckTheme.EMERALD,
            "🌌 Midnight Tech (Dark Slate & Indigo)": DeckTheme.MIDNIGHT,
            "🌊 Corporate Ocean (Navy & Cobalt)": DeckTheme.OCEAN,
            "🌅 Sunset Stone (Charcoal & Tangerine)": DeckTheme.SUNSET,
        }
        selected_theme_label = st.selectbox("Visual Presentation Theme", list(theme_map.keys()), index=0)
        chosen_theme = theme_map[selected_theme_label]

        # Target Duration Slider
        target_mins = st.slider("Target Presentation Duration (Minutes)", min_value=1, max_value=12, value=5)

        st.divider()
        st.subheader("🤖 AI Enhancer Configuration")
        ai_provider_choice = st.selectbox(
            "AI Enhancement Provider",
            ["Auto-detect", "Google Gemini", "OpenAI / OpenAI-Compatible", "Anthropic Claude", "Disable (Local Only)"],
            index=0,
        )

        if ai_provider_choice == "Google Gemini":
            gem_key = st.text_input("Gemini API Key", value=os.getenv("GEMINI_API_KEY", ""), type="password")
            if gem_key:
                os.environ["GEMINI_API_KEY"] = gem_key
            gem_model = st.selectbox("Gemini Model", ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.0-flash-exp"], index=0)
            os.environ["GEMINI_MODEL"] = gem_model

        elif ai_provider_choice == "OpenAI / OpenAI-Compatible":
            oai_key = st.text_input("OpenAI API Key", value=os.getenv("OPENAI_API_KEY", ""), type="password")
            if oai_key:
                os.environ["OPENAI_API_KEY"] = oai_key
            oai_model = st.text_input("OpenAI Model", value=os.getenv("OPENAI_MODEL", "gpt-4o-mini"))
            os.environ["OPENAI_MODEL"] = oai_model
            base_url = st.text_input("Base URL (Optional for Groq/Ollama)", value=os.getenv("OPENAI_BASE_URL", ""))
            if base_url:
                os.environ["OPENAI_BASE_URL"] = base_url

        elif ai_provider_choice == "Anthropic Claude":
            ant_key = st.text_input("Anthropic API Key", value=os.getenv("ANTHROPIC_API_KEY", ""), type="password")
            if ant_key:
                os.environ["ANTHROPIC_API_KEY"] = ant_key
            ant_model = st.selectbox("Model", ["claude-3-5-sonnet-20241022", "claude-3-5-haiku-20241022"], index=0)
            os.environ["ANTHROPIC_MODEL"] = ant_model

        st.divider()
        st.subheader("💡 Shortcuts")
        sample_path = (ROOT_DIR / "sample_demo_app").resolve()
        use_sample = st.button("Use Sample Demo App", use_container_width=True)

        st.markdown("---")
        st.caption("🛡️ **Deterministic & Safe**: Code inspection is strictly static.")

    # --- Step 1: Source Selection ---
    st.subheader("1. Source Repository")
    col_type, col_input = st.columns([1, 3])

    with col_type:
        source_mode = st.radio(
            "Source Type",
            ["Local Directory", "GitHub Repository"],
            index=0,
        )

    with col_input:
        if source_mode == "Local Directory":
            default_val = str(sample_path) if use_sample else str(ROOT_DIR)
            source_input = st.text_input(
                "Local Directory Path",
                value=default_val,
                help="Path to the local repository directory.",
            )
        else:
            source_input = st.text_input(
                "GitHub Repository URL",
                value="https://github.com/streamlit/demo-self-driving",
                help="Public repository URL or owner/repo shorthand.",
            )

    col_btn, _ = st.columns([1, 4])
    with col_btn:
        inspect_triggered = st.button("🔍 Inspect Repository", type="primary", use_container_width=True)

    if inspect_triggered or (use_sample and not st.session_state.profile):
        profile = run_inspection(source_mode, source_input)
        if profile:
            st.session_state.profile = profile
            st.session_state.deck = None
            st.session_state.bundle_paths = None
            st.success(f"Analyzed **{profile.name}** (Readiness Score: {profile.readiness_score}/100)")

    profile: ProjectProfile | None = st.session_state.profile

    if profile:
        st.divider()
        # --- Step 2: Repository Intelligence Dashboard ---
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        col_m1.metric("Pitch Readiness", f"{profile.readiness_score} / 100")
        col_m2.metric("Verified Facts", len(profile.facts()))
        col_m3.metric("Inferred Claims", len(profile.inferences()))
        col_m4.metric("Key Files", len(profile.key_files))

        tab_dash, tab_audit, tab_tech, tab_files = st.tabs([
            "📊 Executive Summary",
            "⚖️ Fact vs Inference Audit",
            "🛠️ Tech Stack & Signals",
            "📁 Codebase Structure",
        ])

        with tab_dash:
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                st.markdown("#### 🎯 Core Value & Purpose")
                for p in profile.purpose:
                    badge = "🟢 FACT" if p.kind == ClaimKind.FACT else "🟡 INFERRED"
                    st.markdown(f"- `{badge}` {p.text}")

                st.markdown("#### 💡 Differentiating Features")
                for f in profile.features[:6]:
                    badge = "🟢 FACT" if f.kind == ClaimKind.FACT else "🟡 INFERRED"
                    st.markdown(f"- `{badge}` {f.text}")

            with col_d2:
                st.markdown("#### 🚀 Setup & Execution")
                for s in profile.setup_steps[:4]:
                    badge = "🟢 FACT" if s.kind == ClaimKind.FACT else "🟡 INFERRED"
                    st.markdown(f"- `{badge}` {s.text}")

                if profile.warnings:
                    with st.expander("⚠️ Missing Documentation Notices", expanded=False):
                        for w in profile.warnings:
                            st.warning(w)

        with tab_audit:
            st.caption("Demo-to-Deck strictly labels claims to protect the speaker's credibility with stakeholders.")
            col_f, col_i = st.columns(2)
            with col_f:
                st.markdown("### 🟢 Ground-Truth Facts (Citations)")
                for claim in profile.facts():
                    src = f" — *{claim.source}*" if claim.source else ""
                    st.markdown(f"- {claim.text}{src}")
            with col_i:
                st.markdown("### 🟡 Inferred Heuristics (Analyzer)")
                for inf in profile.inferences():
                    st.markdown(f"- {inf.text} *(Confidence: {int(inf.confidence * 100)}%)*")

        with tab_tech:
            st.markdown("#### 🛠️ Detected Languages & Frameworks")
            badges = "  ".join([f"`{claim.text}`" for claim in profile.tech_stack])
            st.markdown(badges if badges else "*No explicit stack manifests found.*")

            if profile.architecture_notes:
                st.markdown("#### 🏗️ Architecture Signals")
                for note in profile.architecture_notes:
                    st.markdown(f"- {note}")

        with tab_files:
            for kf in profile.key_files:
                st.markdown(f"- **`{kf.path}`** *({kf.role})*")
                if kf.excerpt:
                    st.caption(f"> {kf.excerpt[:200]}...")

        # --- Step 3: Screenshots & Visual Proof ---
        st.divider()
        st.subheader("2. Attach Live Proof & Screenshots")
        col_s1, col_s2 = st.columns(2)

        with col_s1:
            st.markdown("**Option A: Capture URL Screenshot**")
            url_target = st.text_input("Live Application URL", value="http://127.0.0.1:8765")
            if st.button("📸 Capture Live Screen"):
                shot_path = OUTPUT_DIR / f"{profile.name}_screen.png"
                res = capture_url_screenshot(url_target, shot_path)
                if res["ok"]:
                    st.success(res["message"])
                    if shot_path not in st.session_state.screenshots:
                        st.session_state.screenshots.append(shot_path)
                else:
                    st.warning(res["message"])
                    if res.get("path") and res["path"] not in st.session_state.screenshots:
                        st.session_state.screenshots.append(res["path"])

        with col_s2:
            st.markdown("**Option B: Upload Custom Screenshots**")
            uploaded_file = st.file_uploader("Upload PNG or JPEG", type=["png", "jpg", "jpeg"])
            if uploaded_file is not None:
                save_dest = OUTPUT_DIR / f"{profile.name}_{uploaded_file.name}"
                save_dest.write_bytes(uploaded_file.getbuffer())
                if save_dest not in st.session_state.screenshots:
                    st.session_state.screenshots.append(save_dest)
                st.success(f"Attached `{uploaded_file.name}`")

        if st.session_state.screenshots:
            st.markdown("**Attached Presentation Visuals:**")
            cols = st.columns(min(len(st.session_state.screenshots), 3))
            for i, shot in enumerate(st.session_state.screenshots):
                if Path(shot).exists():
                    cols[i % 3].image(str(shot), caption=f"Visual {i+1}: {Path(shot).name}", use_column_width=True)

        # --- Step 4: Deck Generation & Live Studio ---
        st.divider()
        st.subheader("3. Generate & Refine Pitch Deck")

        col_g1, col_g2 = st.columns([1, 3])
        with col_g1:
            gen_triggered = st.button("🚀 Generate Pitch Deck", type="primary", use_container_width=True)

        # Generate on click or if deck is not yet created
        if gen_triggered or (st.session_state.deck is None and profile):
            use_llm = (ai_provider_choice != "Disable (Local Only)") and llm_available()
            with st.spinner("Generating presentation slides, timing breakdown, and speaking script..."):
                deck = generate_pitch_deck(
                    profile,
                    use_llm=use_llm,
                    archetype=chosen_archetype,
                    theme=chosen_theme,
                    target_duration_minutes=target_mins,
                )
                st.session_state.deck = deck
                bundle = export_bundle(
                    deck,
                    profile,
                    output_dir=OUTPUT_DIR,
                    screenshot_paths=st.session_state.screenshots,
                )
                st.session_state.bundle_paths = bundle

        deck: PitchDeck | None = st.session_state.deck
        bundle = st.session_state.bundle_paths

        if deck:
            mins = deck.total_duration_seconds // 60
            secs = deck.total_duration_seconds % 60
            st.success(
                f"Generated **{len(deck.slides)} Slides** ({mins}m {secs:02d}s total) · "
                f"Archetype: `{deck.archetype.value.upper()}` · Theme: `{deck.theme.value.title()}` · "
                f"Mode: `{deck.generation_mode}`"
            )

            # Export download buttons
            if bundle and Path(bundle["pptx"]).exists():
                st.markdown("### 📥 Download Presentation Deliverables")
                d1, d2, d3, d4 = st.columns(4)
                with d1:
                    with open(bundle["pptx"], "rb") as f:
                        st.download_button(
                            label="📊 Download PowerPoint (.pptx)",
                            data=f.read(),
                            file_name=Path(bundle["pptx"]).name,
                            mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                            use_container_width=True,
                        )
                with d2:
                    with open(bundle["script"], "rb") as f:
                        st.download_button(
                            label="📝 Download Timed Script (.md)",
                            data=f.read(),
                            file_name=Path(bundle["script"]).name,
                            mime="text/markdown",
                            use_container_width=True,
                        )
                with d3:
                    with open(bundle["source_notes"], "rb") as f:
                        st.download_button(
                            label="⚖️ Download Source Notes (.md)",
                            data=f.read(),
                            file_name=Path(bundle["source_notes"]).name,
                            mime="text/markdown",
                            use_container_width=True,
                        )
                with d4:
                    with open(bundle["deck_json"], "rb") as f:
                        st.download_button(
                            label="📦 Download JSON Bundle",
                            data=f.read(),
                            file_name=Path(bundle["deck_json"]).name,
                            mime="application/json",
                            use_container_width=True,
                        )

            # --- Presentation Workspaces ---
            tab_slides, tab_teleprompter, tab_script, tab_sources = st.tabs([
                "🖼️ Slide Studio & Live Editor",
                "🎙️ Presenter Teleprompter",
                "⏱️ Timed Script View",
                "📑 Ground-Truth Citations",
            ])

            # Slide Studio & Live Editor
            with tab_slides:
                st.caption("You can live-edit slide titles, bullet points, and speaker notes below. Changes persist to your export.")
                for s in deck.slides:
                    with st.expander(f"Slide {s.number}: {s.title}  (⏱️ {s.duration_seconds}s)", expanded=(s.number == 1)):
                        c_left, c_right = st.columns([3, 2])
                        with c_left:
                            new_title = st.text_input(f"Title (Slide {s.number})", value=s.title, key=f"title_{s.number}")
                            s.title = new_title

                            bullets_text = "\n".join(s.bullets)
                            new_bullets = st.text_area(
                                f"Bullet Points (one per line)",
                                value=bullets_text,
                                key=f"bullets_{s.number}",
                                height=110,
                            )
                            s.bullets = [b.strip() for b in new_bullets.split("\n") if b.strip()]

                        with c_right:
                            new_duration = st.number_input(f"Duration (seconds)", value=s.duration_seconds, min_value=10, max_value=300, key=f"dur_{s.number}")
                            s.duration_seconds = int(new_duration)

                            new_notes = st.text_area(
                                f"Speaker Script (Spoken Narration)",
                                value=s.speaker_notes,
                                key=f"notes_{s.number}",
                                height=130,
                            )
                            s.speaker_notes = new_notes

                        if s.source_notes:
                            st.caption(f"Linked Sources: {', '.join(s.source_notes[:3])}")

                # Save Edits button
                if st.button("💾 Apply Edits & Re-export Bundle", type="secondary"):
                    bundle = export_bundle(
                        deck,
                        profile,
                        output_dir=OUTPUT_DIR,
                        screenshot_paths=st.session_state.screenshots,
                    )
                    st.session_state.bundle_paths = bundle
                    st.success("Updated PowerPoint (.pptx) and script files!")

            # Presenter Teleprompter
            with tab_teleprompter:
                st.markdown("### 🎙️ Live Presenter Teleprompter")
                total_slides = len(deck.slides)
                cur_idx = st.session_state.presenter_slide_idx
                active_slide = deck.slides[cur_idx]

                # Progress & Navigation
                col_nav1, col_nav2, col_nav3 = st.columns([1, 2, 1])
                with col_nav1:
                    if st.button("⬅️ Previous Slide", disabled=(cur_idx == 0)):
                        st.session_state.presenter_slide_idx -= 1
                        st.rerun()
                with col_nav2:
                    st.progress((cur_idx + 1) / total_slides)
                    st.write(f"Slide **{cur_idx + 1} of {total_slides}**")
                with col_nav3:
                    if st.button("Next Slide ➡️", disabled=(cur_idx == total_slides - 1)):
                        st.session_state.presenter_slide_idx += 1
                        st.rerun()

                # Large Teleprompter Display
                st.markdown(f"## {active_slide.number}. {active_slide.title}")
                st.info(f"⏱️ **Target Slide Timing:** {active_slide.duration_seconds} seconds (~{len(active_slide.speaker_notes.split())} words)")

                st.markdown("#### 🗣️ What To Say (Spoken Script):")
                st.markdown(
                    f"<div style='font-size: 20px; line-height: 1.6; padding: 20px; background: #FFF; "
                    f"border-radius: 8px; border-left: 6px solid #10B981; color: #1E293B;'>"
                    f"{active_slide.speaker_notes}</div>",
                    unsafe_allow_html=True,
                )

                st.markdown("#### 🖥️ What Audience Sees (On Screen):")
                for b in active_slide.bullets:
                    st.markdown(f"- {b}")

            # Timed Script View
            with tab_script:
                st.markdown(deck.script_markdown)

            # Ground-Truth Citations View
            with tab_sources:
                st.markdown(deck.source_notes_markdown)


if __name__ == "__main__":
    main()
