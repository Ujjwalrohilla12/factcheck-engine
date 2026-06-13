"""Generate a sample PDF for local testing."""

from __future__ import annotations

from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer


SAMPLE_TEXT = [
    "FactCheck AI Sample Marketing Report",
    "The global AI market is projected to reach $1.8 trillion by 2030 according to several analyst forecasts.",
    "ChatGPT reached 200 million users as of 2024 in some public reporting.",
    "Google holds 85% of the global search market in 2025 according to one internal slide.",
    "Enterprise AI spending grew 38% year-over-year in 2024 across surveyed companies.",
    "OpenAI reported $4.2 billion in annualized revenue in 2024 in media coverage.",
    "GPT-4 was launched in March 2023 by OpenAI.",
    "Cloud infrastructure market share for AWS is 31% in 2024 based on analyst estimates.",
    "Cybersecurity breaches increased 72% between 2022 and 2024 in one vendor report.",
]


def ensure_sample_pdf(output_path: Path | None = None) -> Path:
    """Create the bundled sample PDF if it does not already exist."""
    path = output_path or Path(__file__).resolve().parents[1] / "assets" / "sample_report.pdf"
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        return path

    doc = SimpleDocTemplate(str(path), pagesize=letter)
    styles = getSampleStyleSheet()
    story = [Paragraph(SAMPLE_TEXT[0], styles["Title"]), Spacer(1, 12)]
    for paragraph in SAMPLE_TEXT[1:]:
        story.append(Paragraph(paragraph, styles["BodyText"]))
        story.append(Spacer(1, 8))
    doc.build(story)
    return path


if __name__ == "__main__":
    print(ensure_sample_pdf())
