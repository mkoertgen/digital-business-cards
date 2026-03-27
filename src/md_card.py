"""Markdown business card renderer.

Produces a clean, Pandoc-compatible Markdown file per contact —
a stepping stone toward PDF/EPUB output via Pandoc.

Output format example:

    ---
    title: Max Mustermann
    ---

    # Max Mustermann

    **Senior Developer** — Acme Corp

    ![](avatars/MMu.jpg)

    | | |
    |:--|:--|
    | Email | max@acme.com |
    | Phone | +49 89 12345 |
    | Mobile | +49 170 12345 |
    | Department | Engineering |
"""

import logging
from pathlib import Path
from typing import Optional

from src.models import Contact

logger = logging.getLogger(__name__)


class MarkdownCardGenerator:
    """Generate Markdown business cards from Contact objects."""

    def generate(self, contact: Contact, avatar_path: Optional[Path] = None, output_dir: Optional[Path] = None) -> str:
        """
        Render a contact as a Markdown string.

        Args:
            contact:      Contact to render.
            avatar_path:  Absolute path to avatar image (embedded as relative ref if output_dir given).
            output_dir:   Output directory (used to make avatar_path relative).

        Returns:
            Markdown content.
        """
        lines: list[str] = []

        # YAML front-matter (for Pandoc metadata)
        lines += [
            "---",
            f"title: {contact.name}",
        ]
        if contact.title:
            lines.append(f"subtitle: {contact.title}")
        if contact.company:
            lines.append(f"author: {contact.company}")
        lines += ["---", ""]

        # Heading
        lines += [f"# {contact.name}", ""]

        # Tagline
        tagline_parts = [p for p in [contact.title, contact.company] if p]
        if tagline_parts:
            lines += [" — ".join(tagline_parts), ""]

        # Avatar
        if avatar_path:
            rel = _rel(avatar_path, output_dir) if output_dir else avatar_path.name
            lines += [f"![{contact.name}]({rel})", ""]

        # Contact details table
        rows: list[tuple[str, str]] = []
        rows.append(("Email", contact.email))
        if contact.phone:
            rows.append(("Phone", contact.phone))
        if contact.mobile:
            rows.append(("Mobile", contact.mobile))
        if contact.department:
            rows.append(("Department", contact.department))

        if rows:
            lines.append("| | |")
            lines.append("|:--|:--|")
            for label, value in rows:
                lines.append(f"| {label} | {value} |")
            lines.append("")

        return "\n".join(lines)

    def save(self, contact: Contact, output_dir: Path, avatar_path: Optional[Path] = None) -> Path:
        """
        Generate and save a Markdown card.

        Args:
            contact:     Contact to render.
            output_dir:  Output directory.
            avatar_path: Optional path to avatar image.

        Returns:
            Path to saved .md file.
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        content = self.generate(contact, avatar_path=avatar_path, output_dir=output_dir)
        md_path = output_dir / f"{contact.id}.md"
        md_path.write_text(content, encoding="utf-8")
        logger.debug(f"Saved Markdown card: {md_path}")
        return md_path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _rel(target: Path, base: Path) -> str:
    """Return POSIX-style relative path from base dir to target."""
    try:
        return target.relative_to(base).as_posix()
    except ValueError:
        return target.as_posix()
