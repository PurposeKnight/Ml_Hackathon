"""Build the verifiable PathSnap PDF report from committed CSVs and plots."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


ROOT = Path(__file__).resolve().parents[1]


def build() -> Path:
    output = ROOT / "reports" / "pathsnap_technical_report.pdf"
    comparison = pd.read_csv(ROOT / "results" / "corrected_models" / "model_comparison.csv")
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="ReportTitle", parent=styles["Title"], alignment=TA_CENTER, spaceAfter=18))
    styles.add(ParagraphStyle(name="Small", parent=styles["BodyText"], fontSize=8, leading=10))
    doc = SimpleDocTemplate(str(output), pagesize=A4, rightMargin=42, leftMargin=42, topMargin=42, bottomMargin=42)
    story = [Paragraph("PathSnap technical report", styles["ReportTitle"]), Paragraph("Corrected first-evaluation baseline", styles["Heading2"]), Spacer(1, 10)]
    sections = [
        ("1. System overview", "PathSnap ranks directed road-segment candidates for GPS observations and optionally reconstructs a continuous route with a log-space HMM/Viterbi decoder. Source modules separate loading, graph construction, candidates, features, models, decoding, API inference, and visualisation."),
        ("2. Data processing and features", "The loader validates headerless .track, .nodes, .arcs, and .route files while preserving the official 80 training and 10 student-test split. The corrected experiment uses a 50 m radius and at most four candidates. The eight features are distance, heading difference, speed, time delta, candidate rank, segment length, movement distance, and previous-network connectivity."),
        ("3. Corrected evaluation", "Three-fold GroupKFold groups by trip. Negative sampling is restricted to training partitions; validation and student-test contain every generated candidate. The student set has 19,160 observations and 67,872 candidate rows, with zero zero-candidate observations."),
    ]
    for heading, body in sections:
        story.extend([Paragraph(heading, styles["Heading2"]), Paragraph(body, styles["BodyText"]), Spacer(1, 8)])
    story.append(Paragraph("Corrected model comparison", styles["Heading2"]))
    columns = ["model", "cv_macro_f1", "macro_f1", "top1_accuracy_all_observations", "log_loss", "inference_ms_per_candidate"]
    data = [["Model", "CV Macro F1", "Student Macro F1", "Student Top-1", "Log loss", "ms/candidate"]]
    for _, row in comparison.iterrows():
        data.append([str(row["model"]).replace("_", " ").title(), f"{row['cv_macro_f1']:.6f}", f"{row['macro_f1']:.6f}", f"{row['top1_accuracy_all_observations']:.6f}", f"{row['log_loss']:.6f}", f"{row['inference_ms_per_candidate']:.6f}"])
    table = Table(data, repeatRows=1, colWidths=[1.35 * inch, .9 * inch, 1.05 * inch, 1.0 * inch, .75 * inch, .9 * inch])
    table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f4e79")), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white), ("GRID", (0, 0), (-1, -1), .25, colors.grey), ("FONTSIZE", (0, 0), (-1, -1), 7), ("ALIGN", (1, 1), (-1, -1), "RIGHT")]))
    story.extend([table, Spacer(1, 8), Paragraph("Logistic Regression is selected by the highest corrected CV Macro F1 (0.7295715568). Student metrics support the choice but do not define it.", styles["BodyText"]), PageBreak()])
    story.extend([Paragraph("4. HMM/Viterbi and limitations", styles["Heading2"]), Paragraph("Hidden states are candidate arc IDs. Emissions combine classifier probability with distance; transitions reward same-arc and directed-connected moves, while disconnected transitions receive a finite penalty. Empty candidate groups produce null outputs and reset decoding. Reference labels are a nearest-route-arc heuristic, so parallel roads, GPS noise, incomplete routes, and repeated arcs remain limitations. See docs/label_quality.md and results/corrected_models/label_quality.csv.", styles["BodyText"]), Spacer(1, 10)])
    for image_path, caption in [(ROOT / "results" / "corrected_models" / "model_comparison.png", "Corrected CV Macro F1 comparison"), (ROOT / "results" / "plots" / "gps_speed_distribution.png", "GPS speed distribution"), (ROOT / "results" / "plots" / "gps_matched_route_map.png", "Folium map screenshot; interactive HTML is committed separately")]:
        if image_path.exists():
            story.extend([Paragraph(caption, styles["Heading3"]), Image(str(image_path), width=6.4 * inch, height=3.3 * inch), Spacer(1, 8)])
    doc.build(story)
    return output


if __name__ == "__main__":
    print(build())
