"""Build the verifiable PathSnap PDF report from committed CSVs and plots."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
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
    tuned = pd.read_csv(ROOT / "results" / "corrected_models" / "corrected_logistic_tuned_vs_baseline.csv")
    inventory = pd.read_csv(ROOT / "results" / "eda" / "dataset_inventory.csv")
    optimization = json.loads((ROOT / "results" / "corrected_models" / "corrected_logistic_optimization.json").read_text(encoding="utf-8"))
    sequence = json.loads((ROOT / "results" / "corrected_models" / "sequence_comparison.json").read_text(encoding="utf-8"))
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="ReportTitle", parent=styles["Title"], alignment=TA_CENTER, spaceAfter=18))
    styles.add(ParagraphStyle(name="Small", parent=styles["BodyText"], fontSize=8, leading=10))
    doc = SimpleDocTemplate(str(output), pagesize=A4, rightMargin=42, leftMargin=42, topMargin=42, bottomMargin=42)
    metrics_plot = ROOT / "reports" / "model_metrics_comparison.png"
    labels = comparison["model"].str.replace("_", " ").str.title()
    fig, axes = plt.subplots(2, 2, figsize=(11, 7))
    metrics = [("cv_macro_f1", "CV Macro F1", "#2ca02c"), ("top1_accuracy_all_observations", "Student Top-1 Accuracy", "#9467bd"), ("macro_f1", "Student Macro F1", "#1f77b4"), ("log_loss", "Student Log Loss", "#d62728")]
    for ax, (column, title, color) in zip(axes.ravel(), metrics, strict=True):
        ax.bar(labels, comparison[column], color=color)
        ax.set_title(title)
        ax.tick_params(axis="x", rotation=35, labelsize=8)
        ax.grid(axis="y", alpha=0.25)
    fig.suptitle("PathSnap five-model evaluation", fontsize=14)
    fig.tight_layout()
    fig.savefig(metrics_plot, dpi=180)
    plt.close(fig)
    story = [Paragraph("PathSnap technical report", styles["ReportTitle"]), Paragraph("Final first-evaluation baseline", styles["Heading2"]), Spacer(1, 10)]
    sections = [
        ("1. System overview", "PathSnap ranks directed road-segment candidates for GPS observations and optionally reconstructs a continuous route with a log-space HMM/Viterbi decoder. Source modules separate loading, graph construction, candidates, features, models, decoding, API inference, and visualisation."),
        ("2. Data processing and features", "The loader validates headerless .track, .nodes, .arcs, and .route files while preserving the official 80 training and 10 student-test split. The final experiment uses a 50 m radius and at most four candidates. The eight features are distance, heading difference, speed, time delta, candidate rank, segment length, movement distance, and previous-network connectivity."),
        ("3. Final model evaluation", "Three-fold GroupKFold groups by trip. Negative sampling is restricted to training partitions; validation and student-test contain every generated candidate. The student set has 19,160 observations and 67,872 candidate rows, with zero zero-candidate observations."),
    ]
    for heading, body in sections:
        story.extend([Paragraph(heading, styles["Heading2"]), Paragraph(body, styles["BodyText"]), Spacer(1, 8)])
    train_inventory = inventory.loc[inventory["partition"].eq("train")]
    student_inventory = inventory.loc[inventory["partition"].eq("student_test")]
    story.extend([Paragraph("Data quality evidence", styles["Heading3"]), Paragraph(f"The committed inventory covers {len(train_inventory)} training trips and {len(student_inventory)} student-test trips. Missing-value totals are {int(train_inventory['missing_values'].sum())} for training and {int(student_inventory['missing_values'].sum())} for student testing; invalid-trip counts are {int((~train_inventory['valid']).sum())} and {int((~student_inventory['valid']).sum())}, respectively.", styles["BodyText"]), Spacer(1, 8)])
    story.append(Paragraph("Five-model comparison", styles["Heading2"]))
    columns = ["model", "cv_macro_f1", "macro_f1", "top1_accuracy_all_observations", "log_loss", "inference_ms_per_candidate"]
    data = [["Model", "CV Macro F1", "Student Macro F1", "Student Top-1", "Log loss", "ms/candidate"]]
    for _, row in comparison.iterrows():
        data.append([str(row["model"]).replace("_", " ").title(), f"{row['cv_macro_f1']:.6f}", f"{row['macro_f1']:.6f}", f"{row['top1_accuracy_all_observations']:.6f}", f"{row['log_loss']:.6f}", f"{row['inference_ms_per_candidate']:.6f}"])
    table = Table(data, repeatRows=1, colWidths=[1.35 * inch, .9 * inch, 1.05 * inch, 1.0 * inch, .75 * inch, .9 * inch])
    table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f4e79")), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white), ("GRID", (0, 0), (-1, -1), .25, colors.grey), ("FONTSIZE", (0, 0), (-1, -1), 7), ("ALIGN", (1, 1), (-1, -1), "RIGHT")]))
    tuned_row = tuned.loc[tuned["model"].eq("tuned_logistic_regression")].iloc[0]
    story.extend([table, Spacer(1, 8), Paragraph(f"Bayesian optimization improved Logistic Regression CV Macro F1 from {tuned.loc[tuned['model'].eq('baseline_logistic_regression'), 'cv_macro_f1'].iloc[0]:.6f} to {tuned_row['cv_macro_f1']:.6f}. The tuned artifact is selected; its student Macro F1 is {tuned_row['macro_f1']:.6f} and complete-candidate Top-1 is {tuned_row['top1_accuracy_all_observations']:.6f}.", styles["BodyText"]), PageBreak()])
    model_notes = {
        "logistic_regression": "Linear probabilistic baseline; StandardScaler, class_weight=balanced and max_iter=400 before tuning. Strength: fast, interpretable emission scores. Limitation: linear boundary.",
        "knn": "Instance-based local baseline; StandardScaler, k=7 and distance weighting. Strength: flexible local regions. Limitation: slow inference and weak probability quality.",
        "random_forest": "Bagged nonlinear trees; 40 trees, min_samples_leaf=2 and balanced_subsample. Strength: feature interactions. Limitation: poor calibration and weaker complete-candidate ranking here.",
        "hist_gradient_boosting": "Boosted nonlinear trees; max_iter=150, learning_rate=0.08 and max_leaf_nodes=31. Strength: expressive tabular rules. Limitation: probability behavior shifted under complete candidate evaluation.",
        "mlp": "One-hidden-layer neural network; StandardScaler, 8 hidden units and max_iter=20. Strength: nonlinear representation. Limitation: sensitive to scaling, capacity and convergence.",
    }
    story.append(Paragraph("Model-by-model interpretation", styles["Heading2"]))
    for _, row in comparison.iterrows():
        name = row["model"]
        story.extend([Paragraph(str(name).replace("_", " ").title(), styles["Heading3"]), Paragraph(model_notes[name] + f" Observed CV Macro F1={row['cv_macro_f1']:.6f}, student Macro F1={row['macro_f1']:.6f}, Top-1={row['top1_accuracy_all_observations']:.6f}, Log Loss={row['log_loss']:.6f}. Train-versus-validation histories were not recorded, so overfitting cannot be diagnosed conclusively from these outputs alone.", styles["BodyText"])])
    story.append(PageBreak())
    story.append(Paragraph("5. Bayesian hyperparameter optimisation", styles["Heading2"]))
    story.append(Paragraph(f"Optuna TPE searched {optimization['trials']} trials with seed {optimization['seed']} and {optimization['folds']}-fold GroupKFold. The search space was C in [1e-3, 1e2] log-uniform, class_weight in {{balanced, None}}, and max_iter from 200 to 800. Best parameters were C={optimization['best_params']['C']:.10f}, class_weight={optimization['best_params']['class_weight']}, max_iter={optimization['best_params']['max_iter']}. The objective was mean validation Macro F1 on complete validation candidates.", styles["BodyText"]))
    tuned_table = [["Metric", "Untuned", "Tuned"], ["CV Macro F1", f"{tuned.iloc[0]['cv_macro_f1']:.6f}", f"{tuned.iloc[1]['cv_macro_f1']:.6f}"], ["Student Top-1", f"{tuned.iloc[0]['top1_accuracy_all_observations']:.6f}", f"{tuned.iloc[1]['top1_accuracy_all_observations']:.6f}"], ["Student Macro F1", f"{tuned.iloc[0]['macro_f1']:.6f}", f"{tuned.iloc[1]['macro_f1']:.6f}"], ["Log Loss", f"{tuned.iloc[0]['log_loss']:.6f}", f"{tuned.iloc[1]['log_loss']:.6f}"], ["Inference ms/candidate", f"{tuned.iloc[0]['inference_ms_per_candidate']:.6f}", f"{tuned.iloc[1]['inference_ms_per_candidate']:.6f}"]]
    tuned_table_obj = Table(tuned_table, colWidths=[2.1 * inch, 1.3 * inch, 1.3 * inch])
    tuned_table_obj.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f4e79")), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white), ("GRID", (0, 0), (-1, -1), .25, colors.grey), ("FONTSIZE", (0, 0), (-1, -1), 8)]))
    story.extend([Spacer(1, 8), tuned_table_obj, PageBreak()])
    story.append(Paragraph("6. Classifier-only versus HMM/Viterbi", styles["Heading2"]))
    story.extend([Paragraph(f"On the same 10 student-test trips, the tuned classifier-only sequence achieved Top-1 accuracy {sequence['classifier_top1_accuracy']:.6f} and route continuity {sequence['classifier_route_continuity']:.6f}. HMM/Viterbi achieved Top-1 accuracy {sequence['hmm_top1_accuracy']:.6f} and route continuity {sequence['hmm_route_continuity']:.6f}. Thus the measured changes were {sequence['hmm_top1_accuracy'] - sequence['classifier_top1_accuracy']:+.6f} Top-1 and {sequence['hmm_route_continuity'] - sequence['classifier_route_continuity']:+.6f} continuity. Continuity is the fraction of eligible adjacent predicted pairs that stay on the same arc or follow a directed graph edge; missing predictions are excluded from the eligible-edge denominator. This is a development-partition result, not evaluator ground truth.", styles["BodyText"]), Spacer(1, 8)])
    story.extend([Paragraph("7. Model visualisations", styles["Heading2"]), Paragraph("The following comparison figure contains actual CV Macro F1, student Top-1 accuracy, student Macro F1, and log-loss bars for all five trained models. The selected-model confusion matrix is included as a diagnostic; no artificial training curves are used because these models do not expose comparable epoch histories.", styles["BodyText"]), Spacer(1, 8)])
    story.extend([Paragraph("8. HMM/Viterbi and limitations", styles["Heading2"]), Paragraph("Hidden states are candidate arc IDs. Emissions combine classifier probability with distance; transitions reward same-arc and directed-connected moves, while disconnected transitions receive a finite penalty. Empty candidate groups produce null outputs and reset decoding. Reference labels are a nearest-route-arc heuristic, so parallel roads, GPS noise, incomplete routes, and repeated arcs remain limitations. See docs/label_quality.md and the committed label-quality audit.", styles["BodyText"]), Spacer(1, 10)])
    for image_path, caption in [(metrics_plot, "Five-model metric comparison"), (ROOT / "results" / "corrected_models" / "confusion_matrix.png", "Selected-model confusion matrix"), (ROOT / "results" / "plots" / "gps_speed_distribution.png", "GPS speed distribution"), (ROOT / "results" / "plots" / "gps_to_road_distance_distribution.png", "GPS-to-road distance distribution"), (ROOT / "results" / "plots" / "gps_matched_route_map.png", "Folium map screenshot; interactive HTML is committed separately"), (ROOT / "reports" / "laptop2_ui_demo.png", "Laptop 2 evaluator UI demonstration with a live prediction")]:
        if image_path.exists():
            story.extend([Paragraph(caption, styles["Heading3"]), Image(str(image_path), width=6.4 * inch, height=3.3 * inch), Spacer(1, 8)])
    doc.build(story)
    return output


if __name__ == "__main__":
    print(build())
