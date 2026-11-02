"""
Export pitch materials to professional PPTX + Markdown bundles.

Features:
- Multiple executive visual themes (Emerald, Midnight Dark, Ocean, Sunset).
- Dynamic slide layouts (Hero title with pill chips, split content cards, metric callouts).
- High-contrast typography and structured speaker notes with speech pacing guidance.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt

from demo_to_deck.models import DeckArchetype, DeckTheme, PitchDeck, ProjectProfile, Slide, SlideLayout


# Theme color palette definition
THEME_PALETTES = {
    DeckTheme.EMERALD: {
        "bg": RGBColor(0xF7, 0xF9, 0xF8),
        "accent": RGBColor(0x10, 0xB9, 0x81),  # Emerald
        "primary": RGBColor(0x0F, 0x38, 0x2C), # Forest
        "title": RGBColor(0x0A, 0x26, 0x1E),
        "text": RGBColor(0x1E, 0x29, 0x3B),
        "muted": RGBColor(0x64, 0x74, 0x8B),
        "card_bg": RGBColor(0xFF, 0xFF, 0xFF),
        "card_border": RGBColor(0xE2, 0xE8, 0xF0),
        "chip_bg": RGBColor(0xDC, 0xFC, 0xE7),
        "chip_text": RGBColor(0x16, 0x65, 0x34),
        "is_dark": False,
    },
    DeckTheme.MIDNIGHT: {
        "bg": RGBColor(0x0B, 0x0F, 0x19),      # Deep Dark
        "accent": RGBColor(0x63, 0x66, 0xF1),  # Indigo
        "primary": RGBColor(0x38, 0xBD, 0xF8), # Cyan
        "title": RGBColor(0xF8, 0xFA, 0xFC),
        "text": RGBColor(0xE2, 0xE8, 0xF0),
        "muted": RGBColor(0x94, 0xA3, 0xB8),
        "card_bg": RGBColor(0x15, 0x1C, 0x2C),
        "card_border": RGBColor(0x1E, 0x29, 0x3B),
        "chip_bg": RGBColor(0x1E, 0x1B, 0x4B),
        "chip_text": RGBColor(0xC7, 0xD2, 0xFE),
        "is_dark": True,
    },
    DeckTheme.OCEAN: {
        "bg": RGBColor(0xF8, 0xFA, 0xFC),
        "accent": RGBColor(0x25, 0x63, 0xEB),  # Cobalt Blue
        "primary": RGBColor(0x0C, 0x4A, 0x6E), # Deep Navy
        "title": RGBColor(0x0F, 0x17, 0x2A),
        "text": RGBColor(0x1E, 0x29, 0x3B),
        "muted": RGBColor(0x64, 0x74, 0x8B),
        "card_bg": RGBColor(0xFF, 0xFF, 0xFF),
        "card_border": RGBColor(0xE2, 0xE8, 0xF0),
        "chip_bg": RGBColor(0xE0, 0xF2, 0xFE),
        "chip_text": RGBColor(0x03, 0x69, 0xA1),
        "is_dark": False,
    },
    DeckTheme.SUNSET: {
        "bg": RGBColor(0xFA, 0xF8, 0xF5),      # Warm bone
        "accent": RGBColor(0xF9, 0x73, 0x16),  # Tangerine
        "primary": RGBColor(0x1C, 0x19, 0x17), # Stone
        "title": RGBColor(0x1C, 0x19, 0x17),
        "text": RGBColor(0x29, 0x25, 0x24),
        "muted": RGBColor(0x78, 0x71, 0x6C),
        "card_bg": RGBColor(0xFF, 0xFF, 0xFF),
        "card_border": RGBColor(0xE7, 0xE5, 0xE4),
        "chip_bg": RGBColor(0xFF, 0xED, 0xD5),
        "chip_text": RGBColor(0xC2, 0x41, 0x0C),
        "is_dark": False,
    },
}


def _safe_stem(name: str) -> str:
    cleaned = re.sub(r"[^\w\-]+", "_", name.strip())[:60].strip("_")
    return cleaned or "pitch_deck"


def _set_slide_background(slide: Any, color: RGBColor) -> None:
    bg = slide.background
    fill = bg.fill
    fill.solid()
    fill.fore_color.rgb = color


def _add_accent_header(slide: Any, accent_color: RGBColor) -> None:
    bar = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        Inches(0),
        Inches(0),
        Inches(13.333),
        Inches(0.18),
    )
    bar.fill.solid()
    bar.fill.fore_color.rgb = accent_color
    bar.line.fill.background()


def export_pptx(deck: PitchDeck, output_path: Path, screenshot_paths: list[Path] | None = None) -> Path:
    """Create a high-impact, professionally styled PowerPoint presentation."""
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank = prs.slide_layouts[6]

    theme_enum = deck.theme if isinstance(deck.theme, DeckTheme) else DeckTheme.EMERALD
    palette = THEME_PALETTES.get(theme_enum, THEME_PALETTES[DeckTheme.EMERALD])

    screenshots = [p for p in (screenshot_paths or []) if Path(p).exists()]
    shot_idx = 0

    archetype_labels = {
        DeckArchetype.INVESTOR: "INVESTOR SEED PITCH",
        DeckArchetype.TECH_DEMO: "TECHNICAL DEMO & ARCHITECTURE",
        DeckArchetype.CUSTOMER: "CUSTOMER SOLUTION WALKTHROUGH",
        DeckArchetype.LIGHTNING: "LIGHTNING HACKATHON PITCH",
    }
    archetype_title = archetype_labels.get(deck.archetype, "PROJECT PITCH DECK")

    for idx, slide_model in enumerate(deck.slides):
        slide = prs.slides.add_slide(blank)
        _set_slide_background(slide, palette["bg"])
        _add_accent_header(slide, palette["accent"])

        is_title_slide = (idx == 0)

        if is_title_slide:
            # --- Title Slide (Hero Layout) ---
            # Category Chip Pill
            chip = slide.shapes.add_shape(
                MSO_SHAPE.ROUNDED_RECTANGLE,
                Inches(1.0),
                Inches(1.0),
                Inches(4.2),
                Inches(0.45),
            )
            chip.fill.solid()
            chip.fill.fore_color.rgb = palette["chip_bg"]
            chip.line.fill.background()
            chip_tf = chip.text_frame
            chip_tf.clear()
            cp = chip_tf.paragraphs[0]
            cp.text = f"✨  {archetype_title}"
            cp.font.size = Pt(13)
            cp.font.bold = True
            cp.font.color.rgb = palette["chip_text"]
            cp.alignment = PP_ALIGN.CENTER

            # Main Title
            title_box = slide.shapes.add_textbox(Inches(1.0), Inches(1.65), Inches(11.3), Inches(1.8))
            tf = title_box.text_frame
            tf.word_wrap = True
            tf.clear()
            p = tf.paragraphs[0]
            p.text = slide_model.title
            p.font.size = Pt(46)
            p.font.bold = True
            p.font.color.rgb = palette["title"]

            # Tagline / Subtitle
            tagline_box = slide.shapes.add_textbox(Inches(1.0), Inches(3.6), Inches(7.5), Inches(1.8))
            tg_tf = tagline_box.text_frame
            tg_tf.word_wrap = True
            tg_tf.clear()
            for b_idx, bullet in enumerate(slide_model.bullets):
                para = tg_tf.paragraphs[0] if b_idx == 0 else tg_tf.add_paragraph()
                para.text = bullet
                para.font.size = Pt(18)
                para.font.color.rgb = palette["text"]
                para.space_after = Pt(8)

            # Right Side Hero Card or Screenshot
            if screenshots:
                try:
                    slide.shapes.add_picture(
                        str(screenshots[0]),
                        Inches(8.8),
                        Inches(2.0),
                        width=Inches(3.8),
                    )
                except Exception:
                    pass
            else:
                # Decorative stats card on title slide
                stat_card = slide.shapes.add_shape(
                    MSO_SHAPE.ROUNDED_RECTANGLE,
                    Inches(8.8),
                    Inches(2.0),
                    Inches(3.6),
                    Inches(3.4),
                )
                stat_card.fill.solid()
                stat_card.fill.fore_color.rgb = palette["card_bg"]
                stat_card.line.color.rgb = palette["card_border"]
                stat_card.line.width = Pt(1.5)
                sc_tf = stat_card.text_frame
                sc_tf.clear()
                p1 = sc_tf.paragraphs[0]
                p1.text = "PITCH OVERVIEW"
                p1.font.size = Pt(12)
                p1.font.bold = True
                p1.font.color.rgb = palette["muted"]
                p1.space_after = Pt(14)

                p2 = sc_tf.add_paragraph()
                p2.text = f"{len(deck.slides)} Slides"
                p2.font.size = Pt(24)
                p2.font.bold = True
                p2.font.color.rgb = palette["title"]
                p2.space_after = Pt(10)

                p3 = sc_tf.add_paragraph()
                p3.text = f"Target: {deck.total_duration_seconds // 60}m {deck.total_duration_seconds % 60:02d}s"
                p3.font.size = Pt(15)
                p3.font.color.rgb = palette["accent"]
                p3.space_after = Pt(10)

                p4 = sc_tf.add_paragraph()
                p4.text = f"Mode: {deck.generation_mode.upper()}"
                p4.font.size = Pt(13)
                p4.font.color.rgb = palette["muted"]

        else:
            # --- Standard Content Slide ---
            # Slide Header
            header_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(11.5), Inches(0.9))
            htf = header_box.text_frame
            htf.clear()
            p = htf.paragraphs[0]
            p.text = f"{slide_model.number}.  {slide_model.title}"
            p.font.size = Pt(30)
            p.font.bold = True
            p.font.color.rgb = palette["title"]

            # Content Columns (Left column content card)
            has_right_asset = False
            right_image_path = None

            # Determine if this slide should feature a screenshot
            if screenshots:
                target_idx = slide_model.target_screenshot_index
                if target_idx is not None and target_idx < len(screenshots):
                    right_image_path = screenshots[target_idx]
                    has_right_asset = True
                elif slide_model.number in {2, 3, 5} and shot_idx < len(screenshots):
                    right_image_path = screenshots[shot_idx]
                    shot_idx = (shot_idx + 1) % len(screenshots)
                    has_right_asset = True

            left_width = Inches(7.4) if has_right_asset else Inches(11.5)

            # Content container card
            card = slide.shapes.add_shape(
                MSO_SHAPE.ROUNDED_RECTANGLE,
                Inches(0.8),
                Inches(1.4),
                left_width,
                Inches(5.0),
            )
            card.fill.solid()
            card.fill.fore_color.rgb = palette["card_bg"]
            card.line.color.rgb = palette["card_border"]
            card.line.width = Pt(1.5)

            body_tf = card.text_frame
            body_tf.word_wrap = True
            body_tf.clear()

            for b_idx, bullet in enumerate(slide_model.bullets):
                para = body_tf.paragraphs[0] if b_idx == 0 else body_tf.add_paragraph()
                para.text = f"•  {bullet}"
                para.font.size = Pt(19)
                para.font.color.rgb = palette["text"]
                para.space_after = Pt(14)

            # Optional screenshot on the right
            if has_right_asset and right_image_path:
                try:
                    slide.shapes.add_picture(
                        str(right_image_path),
                        Inches(8.5),
                        Inches(1.5),
                        width=Inches(4.1),
                    )
                except Exception:
                    pass

        # Speaker notes injection
        notes_frame = slide.notes_slide.notes_text_frame
        wpm = 130
        estimated_words = len(slide_model.speaker_notes.split())
        target_words = int(slide_model.duration_seconds * (wpm / 60))

        notes_content = [
            f"🎯 SLIDE {slide_model.number}: {slide_model.title}",
            f"⏱️ Allocated Time: {slide_model.duration_seconds}s  (Pacing: ~{estimated_words} words / {target_words} target)",
            "",
            "🗣️ PRESENTER SPOKEN SCRIPT:",
            slide_model.speaker_notes,
            "",
        ]
        if slide_model.source_notes:
            notes_content.extend(["📑 SOURCE AUDIT & CITATIONS:", *slide_model.source_notes])

        notes_frame.text = "\n".join(notes_content)

        # Polished Footer
        footer_box = slide.shapes.add_textbox(Inches(0.8), Inches(6.85), Inches(11.5), Inches(0.4))
        ftf = footer_box.text_frame
        ftf.clear()
        fp = ftf.paragraphs[0]
        fp.text = f"{deck.project_name}  ·  Slide {slide_model.number} of {len(deck.slides)}  ·  ⏱️ {slide_model.duration_seconds}s  ·  {archetype_title}"
        fp.font.size = Pt(11)
        fp.font.color.rgb = palette["muted"]
        fp.alignment = PP_ALIGN.LEFT

    output_path.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(output_path))
    return output_path


def export_bundle(
    deck: PitchDeck,
    profile: ProjectProfile,
    output_dir: str | Path,
    screenshot_paths: list[Path] | None = None,
) -> dict[str, Path]:
    """Write PPTX + script + source notes + JSON summaries into output_dir."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    stem = _safe_stem(deck.project_name)

    pptx_path = out / f"{stem}_deck.pptx"
    script_path = out / f"{stem}_script.md"
    notes_path = out / f"{stem}_source_notes.md"
    json_path = out / f"{stem}_bundle.json"
    profile_path = out / f"{stem}_profile.json"

    export_pptx(deck, pptx_path, screenshot_paths=screenshot_paths)
    script_path.write_text(deck.script_markdown, encoding="utf-8")
    notes_path.write_text(deck.source_notes_markdown, encoding="utf-8")
    json_path.write_text(json.dumps(deck.to_dict(), indent=2), encoding="utf-8")
    profile_path.write_text(json.dumps(profile.to_dict(), indent=2), encoding="utf-8")

    return {
        "pptx": pptx_path,
        "script": script_path,
        "source_notes": notes_path,
        "deck_json": json_path,
        "profile_json": profile_path,
    }
