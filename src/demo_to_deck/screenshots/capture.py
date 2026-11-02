"""
Screenshot utilities with modern window mockups and safe fallback generation.

Safety policy:
- Prefer static inspection; do not auto-run arbitrary repository code.
- Screenshot capture is limited to an explicit URL the user (or safe sample demo) provides.
- Uses optional Playwright if installed; otherwise renders crisp browser window mockups.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

from demo_to_deck.models import ProjectProfile


def render_placeholder_screenshot(
    output_path: Path,
    title: str = "Live App Demonstration",
    subtitle: str = "Launch your app at http://localhost:8765 or upload a screen capture",
    url_label: str = "http://127.0.0.1:8765/app",
) -> Path:
    """Create a modern browser-framed PNG mockup when live capture is unavailable."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    width, height = 1280, 720
    # Base background: clean modern slate
    img = Image.new("RGB", (width, height), color=(241, 245, 249))
    draw = ImageDraw.Draw(img)

    # Window Card (centered)
    card_x0, card_y0 = 60, 50
    card_x1, card_y1 = width - 60, height - 50
    header_h = 56

    # Shadow outline
    draw.rectangle([card_x0 + 6, card_y0 + 6, card_x1 + 6, card_y1 + 6], fill=(226, 232, 240))
    # Window Body
    draw.rectangle([card_x0, card_y0, card_x1, card_y1], fill=(255, 255, 255), outline=(203, 213, 225), width=2)
    # Window Header Bar
    draw.rectangle([card_x0, card_y0, card_x1, card_y0 + header_h], fill=(248, 250, 252))
    draw.line([(card_x0, card_y0 + header_h), (card_x1, card_y0 + header_h)], fill=(226, 232, 240), width=2)

    # Traffic light window dots: Red, Yellow, Green
    dot_y = card_y0 + 28
    draw.ellipse([card_x0 + 28, dot_y - 7, card_x0 + 42, dot_y + 7], fill=(239, 68, 68))
    draw.ellipse([card_x0 + 50, dot_y - 7, card_x0 + 64, dot_y + 7], fill=(245, 158, 11))
    draw.ellipse([card_x0 + 72, dot_y - 7, card_x0 + 86, dot_y + 7], fill=(16, 185, 129))

    # Address bar mockup
    bar_x0, bar_x1 = card_x0 + 120, card_x1 - 120
    bar_y0, bar_y1 = card_y0 + 14, card_y0 + 42
    draw.rectangle([bar_x0, bar_y0, bar_x1, bar_y1], fill=(241, 245, 249), outline=(226, 232, 240), width=1)

    # Try loading clean font
    try:
        font_large = ImageFont.truetype("arial.ttf", 36)
        font_med = ImageFont.truetype("arial.ttf", 22)
        font_small = ImageFont.truetype("arial.ttf", 16)
        font_mono = ImageFont.truetype("consola.ttf", 14)
    except OSError:
        font_large = font_med = font_small = font_mono = ImageFont.load_default()

    # Address text
    draw.text((bar_x0 + 20, bar_y0 + 6), f"🔒 {url_label[:60]}", fill=(100, 116, 139), font=font_mono)

    # Center Mock Content Area
    content_cy = (card_y0 + header_h + card_y1) // 2

    # Accent badge
    badge_w, badge_h = 240, 36
    badge_x0 = (width - badge_w) // 2
    badge_y0 = content_cy - 120
    draw.rectangle([badge_x0, badge_y0, badge_x0 + badge_w, badge_y0 + badge_h], fill=(240, 253, 250), outline=(20, 184, 166), width=1)
    draw.text((badge_x0 + 26, badge_y0 + 8), "✨ LIVE DEMO PREVIEW", fill=(15, 118, 110), font=font_small)

    # Title & Subtitle
    title_text = title[:50]
    draw.text((card_x0 + 80, content_cy - 40), title_text, fill=(15, 23, 42), font=font_large)

    subtitle_text = subtitle[:90]
    draw.text((card_x0 + 80, content_cy + 20), subtitle_text, fill=(71, 85, 105), font=font_med)

    # Footer banner in mockup
    draw.line([(card_x0 + 80, content_cy + 90), (card_x1 - 80, content_cy + 90)], fill=(226, 232, 240), width=1)
    draw.text(
        (card_x0 + 80, content_cy + 110),
        "Tip: Point Demo-to-Deck to a running localhost URL or upload direct screenshots in Step 3.",
        fill=(148, 163, 184),
        font=font_small,
    )

    img.save(output_path, "PNG")
    return output_path


def capture_url_screenshot(url: str, output_path: Path, timeout_ms: int = 15000) -> dict[str, Any]:
    """
    Attempt to screenshot a running HTTP page.
    Returns a result dict with ok/path/message. Never raises for missing Playwright.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if not (url.startswith("http://") or url.startswith("https://")):
        return {
            "ok": False,
            "path": None,
            "message": "Screenshot URL must start with http:// or https://",
        }

    try:
        from playwright.sync_api import sync_playwright  # type: ignore
    except ImportError:
        placeholder = render_placeholder_screenshot(
            output_path,
            title="Interactive Demo Screen Cue",
            subtitle=f"Target URL: {url} — launch app or upload a real screenshot",
            url_label=url,
        )
        return {
            "ok": False,
            "path": placeholder,
            "message": (
                "Playwright optional package is not installed. "
                "A clean presentation mockup was generated. Install playwright with: "
                "`pip install playwright && playwright install chromium` or upload your own screenshots."
            ),
        }

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1280, "height": 720})
            page.goto(url, wait_until="networkidle", timeout=timeout_ms)
            page.screenshot(path=str(output_path), full_page=False)
            browser.close()
        return {
            "ok": True,
            "path": output_path,
            "message": f"Successfully captured live screenshot from {url}",
        }
    except Exception as exc:  # noqa: BLE001
        placeholder = render_placeholder_screenshot(
            output_path,
            title="Capture Unavailable",
            subtitle=str(exc)[:90],
            url_label=url,
        )
        return {
            "ok": False,
            "path": placeholder,
            "message": f"Could not capture screenshot ({exc}). Generated UI mockup placeholder.",
        }


def describe_run_instructions(profile: ProjectProfile) -> list[str]:
    """Return user-friendly instructions on how to run the target project for demo walkthroughs."""
    lines: list[str] = []
    if profile.setup_steps:
        lines.append("Verified Setup Steps:")
        for step in profile.setup_steps:
            lines.append(f"  - {step.text}")
    else:
        lines.append("No explicit setup instructions detected in documentation.")
        lines.append("Try inspecting main application entry points or package manifests.")
    return lines
