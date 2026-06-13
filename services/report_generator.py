"""Report export utilities."""

from __future__ import annotations

import csv
import io
import logging
from datetime import datetime
from typing import Any
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from utils.helpers import calculate_claim_statistics

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generate CSV, Markdown, and PDF reports."""

    @staticmethod
    def generate_csv_report(results: list[dict[str, Any]]) -> tuple[str, str | None]:
        """Generate a CSV report string."""
        if not results:
            logger.warning("No results to export for CSV")
            return "", "No results to export."

        logger.info(f"Generating CSV report for {len(results)} results")
        output = io.StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=[
                "Claim",
                "Type",
                "Status",
                "Confidence",
                "Explanation",
                "Key Finding",
                "Sources",
                "Search Query",
            ],
        )
        writer.writeheader()

        for result in results:
            sources = "; ".join(
                f"{source.get('title', 'Source')} ({source.get('url', '')})"
                for source in result.get("sources", [])
            )
            writer.writerow({
                "Claim": result.get("claim", ""),
                "Type": result.get("type", ""),
                "Status": result.get("status", ""),
                "Confidence": result.get("confidence", 0),
                "Explanation": result.get("explanation", ""),
                "Key Finding": result.get("key_finding", ""),
                "Sources": sources,
                "Search Query": result.get("search_query", ""),
            })

        csv_content = output.getvalue()
        logger.info(f"CSV report generated ({len(csv_content)} bytes)")
        return csv_content, None

    @staticmethod
    def generate_markdown_report(results: list[dict[str, Any]], title: str = "FactCheck AI Report") -> tuple[str, str | None]:
        """Generate a Markdown report."""
        if not results:
            return "", "No results to export."

        stats = calculate_claim_statistics(results)
        lines = [
            f"# {title}",
            "",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Summary",
            f"- Total claims: {stats['total']}",
            f"- Verified: {stats['verified']}",
            f"- Inaccurate: {stats['inaccurate']}",
            f"- False: {stats['false']}",
            f"- Unverifiable: {stats['unverifiable']}",
            f"- Average confidence: {stats['avg_confidence']}%",
            "",
            "## Detailed Results",
        ]

        for index, result in enumerate(results, start=1):
            lines.extend([
                "",
                f"### {index}. {result.get('claim', '')}",
                f"- Type: {result.get('type', '')}",
                f"- Status: {result.get('status', '')}",
                f"- Confidence: {result.get('confidence', 0)}%",
                f"- Explanation: {result.get('explanation', '')}",
            ])
            if result.get("key_finding"):
                lines.append(f"- Key finding: {result.get('key_finding')}")
            if result.get("sources"):
                lines.append("- Sources:")
                for source in result.get("sources", []):
                    lines.append(f"  - [{source.get('title', 'Source')}]({source.get('url', '')})")

        return "\n".join(lines), None

    @staticmethod
    def generate_pdf_report(results: list[dict[str, Any]], title: str = "FactCheck AI Report") -> tuple[bytes, str | None]:
        """Generate a PDF report as bytes."""
        if not results:
            logger.warning("No results to export for PDF")
            return b"", "No results to export."

        logger.info(f"Generating PDF report for {len(results)} results")
        try:
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(
                buffer,
                pagesize=letter,
                rightMargin=0.55 * inch,
                leftMargin=0.55 * inch,
                topMargin=0.55 * inch,
                bottomMargin=0.55 * inch,
            )
            styles = getSampleStyleSheet()
            story = [
                Paragraph(title, styles["Title"]),
                Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles["Normal"]),
                Spacer(1, 0.2 * inch),
            ]

            stats = calculate_claim_statistics(results)
            summary_table = Table([
                ["Total", "Verified", "Inaccurate", "False", "Unverifiable", "Avg Confidence"],
                [
                    stats["total"],
                    stats["verified"],
                    stats["inaccurate"],
                    stats["false"],
                    stats["unverifiable"],
                    f"{stats['avg_confidence']}%",
                ],
            ])
            summary_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eef2ff")),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#cbd5e1")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]))
            story.extend([summary_table, Spacer(1, 0.25 * inch)])

            for index, result in enumerate(results, start=1):
                story.append(Paragraph(f"{index}. {escape(str(result.get('claim', '')))}", styles["Heading3"]))
                story.append(Paragraph(
                    f"<b>Status:</b> {escape(str(result.get('status', '')))} | "
                    f"<b>Confidence:</b> {result.get('confidence', 0)}% | "
                    f"<b>Type:</b> {escape(str(result.get('type', '')))}",
                    styles["Normal"],
                ))
                story.append(Paragraph(
                    f"<b>Explanation:</b> {escape(str(result.get('explanation', '')))}",
                    styles["BodyText"],
                ))
                if result.get("key_finding"):
                    story.append(Paragraph(
                        f"<b>Key finding:</b> {escape(str(result.get('key_finding')))}",
                        styles["BodyText"],
                    ))
                for source in result.get("sources", []):
                    story.append(Paragraph(
                        f"Source: {escape(str(source.get('title', 'Source')))} - {escape(str(source.get('url', '')))}",
                        styles["Italic"],
                    ))
                story.append(Spacer(1, 0.18 * inch))

            doc.build(story)
            pdf_content = buffer.getvalue()
            logger.info(f"PDF report generated ({len(pdf_content)} bytes)")
            return pdf_content, None
        except Exception as exc:
            logger.exception(f"Error generating PDF report: {exc}")
            return b"", f"PDF generation error: {exc}"
