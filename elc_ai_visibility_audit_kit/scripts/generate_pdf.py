from pathlib import Path
import argparse
import logging

import pandas as pd
from reportlab.lib.pagesizes import LETTER
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet

"""
ELC AI Visibility Audit - PDF Report Builder

Enhancements:
- Argparse CLI flags: --counts-file, --output-file, --title, --top-n, --verbose
- Graceful handling when data is missing/empty
- Minor styling polish
"""

DEFAULT_OUTPUT_PDF = Path("output") / "ELC_AI_Visibility_Audit.pdf"
DEFAULT_COUNTS_CSV = Path("output") / "outlet_counts.csv"


def build_pdf(counts_csv: Path, output_pdf: Path, title_text: str, top_n: int) -> None:
    styles = getSampleStyleSheet()
    title_style = styles["Title"]
    h2 = styles["Heading2"]
    body = styles["BodyText"]

    output_pdf.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(str(output_pdf), pagesize=LETTER)
    els = []

    # Title
    els.append(Paragraph(title_text, title_style))
    els.append(Spacer(1, 12))
    els.append(Paragraph("“The outlets AI trusts most are the ones you need to win.”", h2))
    els.append(Spacer(1, 24))

    # Executive summary
    els.append(Paragraph("Executive Summary", h2))
    els.append(
        Paragraph(
            "This report aggregates citations (where available) and likely outlets (signal-only where citations are not exposed) "
            "to identify which publishers shape AI-generated answers for Estée Lauder Companies (ELC).",
            body,
        )
    )
    els.append(Spacer(1, 12))

    # Top outlets table
    if counts_csv.exists():
        df = pd.read_csv(counts_csv)
        if not df.empty:
            # Standardize expected columns
            if set(df.columns) >= {"outlet", "count"}:
                df = df[["outlet", "count"]]
            else:
                # Attempt best-effort rename if columns are titled differently
                col_map = {}
                for c in df.columns:
                    lc = c.lower()
                    if "outlet" in lc and "name" in lc or lc == "outlet":
                        col_map[c] = "outlet"
                    if "count" in lc or "freq" in lc:
                        col_map[c] = "count"
                if col_map:
                    df = df.rename(columns=col_map)
                missing = [c for c in ["outlet", "count"] if c not in df.columns]
                if missing:
                    els.append(Paragraph(f"Outlet data found but missing columns: {', '.join(missing)}", body))
                    doc.build(els)
                    return

            df = df.head(max(1, int(top_n)))
            els.append(Paragraph("Top Influential Outlets (Aggregated)", h2))
            # Build table data
            data = [["Outlet", "Mentions"]] + [[str(o), int(c)] for o, c in df.values.tolist()]

            tbl = Table(data, hAlign="LEFT", colWidths=[300, 100])
            tbl.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#d9d9d9")),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("ALIGN", (1, 1), (1, -1), "RIGHT"),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f7f7f7")]),
                    ]
                )
            )
            els.append(tbl)
            els.append(Spacer(1, 12))
        else:
            els.append(Paragraph("No outlet data found (CSV is empty). Run scripts/run_audit.py first.", body))
    else:
        els.append(Paragraph("No outlet data found. Run scripts/run_audit.py first.", body))

    # Recommendations
    els.append(Paragraph("Recommendations (Sample)", h2))
    els.append(
        Paragraph(
            "1) Prioritize outreach to the top 5 outlets above. "
            "2) Close gaps in outlets citing competitors. "
            "3) Place stories reinforcing leadership, innovation, and sustainability narratives. "
            "4) Re-run quarterly to track gains.",
            body,
        )
    )

    doc.build(els)
    logging.info(f"Wrote PDF: {output_pdf}")


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="ELC AI Visibility Audit - PDF Report Builder")
    p.add_argument(
        "--counts-file",
        type=Path,
        default=DEFAULT_COUNTS_CSV,
        help="Path to outlet counts CSV (default: output/outlet_counts.csv)",
    )
    p.add_argument(
        "--output-file",
        type=Path,
        default=DEFAULT_OUTPUT_PDF,
        help="Output PDF path (default: output/ELC_AI_Visibility_Audit.pdf)",
    )
    p.add_argument(
        "--title",
        type=str,
        default="AI Visibility Audit — Estée Lauder Companies",
        help="Report title",
    )
    p.add_argument("--top-n", type=int, default=15, help="Number of top outlets to include")
    p.add_argument("--verbose", action="store_true", help="Verbose logging")
    return p


def main():
    parser = build_arg_parser()
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )

    build_pdf(
        counts_csv=args.counts_file,
        output_pdf=args.output_file,
        title_text=args.title,
        top_n=args.top_n,
    )


if __name__ == "__main__":
    main()
