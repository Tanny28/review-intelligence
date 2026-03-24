from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from datetime import datetime
import pandas as pd
import io


# ── Brand colors ─────────────────────────────────────────────────────────────
GREEN   = colors.HexColor("#1D9E75")
RED     = colors.HexColor("#E24B4A")
PURPLE  = colors.HexColor("#534AB7")
AMBER   = colors.HexColor("#BA7517")
DARK    = colors.HexColor("#1a1a2e")
LIGHT   = colors.HexColor("#f8f9fa")
BORDER  = colors.HexColor("#e0e0e0")
WHITE   = colors.white


# ── Custom styles ─────────────────────────────────────────────────────────────
def build_styles():
    base = getSampleStyleSheet()

    styles = {
        "cover_title": ParagraphStyle(
            "cover_title",
            fontSize=28, fontName="Helvetica-Bold",
            textColor=WHITE, alignment=TA_CENTER, spaceAfter=6
        ),
        "cover_sub": ParagraphStyle(
            "cover_sub",
            fontSize=13, fontName="Helvetica",
            textColor=colors.HexColor("#cccccc"), alignment=TA_CENTER, spaceAfter=4
        ),
        "section_heading": ParagraphStyle(
            "section_heading",
            fontSize=14, fontName="Helvetica-Bold",
            textColor=DARK, spaceBefore=14, spaceAfter=6,
            borderPad=4
        ),
        "body": ParagraphStyle(
            "body",
            fontSize=10, fontName="Helvetica",
            textColor=colors.HexColor("#333333"),
            leading=15, spaceAfter=4
        ),
        "small": ParagraphStyle(
            "small",
            fontSize=8, fontName="Helvetica",
            textColor=colors.HexColor("#888888"), spaceAfter=2
        ),
        "alert_critical": ParagraphStyle(
            "alert_critical",
            fontSize=10, fontName="Helvetica-Bold",
            textColor=RED, spaceAfter=4
        ),
        "alert_warning": ParagraphStyle(
            "alert_warning",
            fontSize=10, fontName="Helvetica-Bold",
            textColor=AMBER, spaceAfter=4
        ),
        "review_text": ParagraphStyle(
            "review_text",
            fontSize=9, fontName="Helvetica",
            textColor=colors.HexColor("#444444"),
            leading=13, spaceAfter=2
        ),
        "positive": ParagraphStyle(
            "positive", fontSize=9, fontName="Helvetica-Bold",
            textColor=GREEN, spaceAfter=1
        ),
        "negative": ParagraphStyle(
            "negative", fontSize=9, fontName="Helvetica-Bold",
            textColor=RED, spaceAfter=1
        ),
        "neutral": ParagraphStyle(
            "neutral", fontSize=9, fontName="Helvetica-Bold",
            textColor=AMBER, spaceAfter=1
        ),
    }
    return styles


# ── Helper: stat card row ─────────────────────────────────────────────────────
def stat_table(stats):
    data = [[
        f"{stats['total_reviews']}\nTotal Reviews",
        f"{stats['positive_pct']}%\nPositive",
        f"{stats['negative_pct']}%\nNegative",
        f"{stats['avg_rating']}/5\nAvg Rating",
        f"{stats['top_aspect']}\nTop Issue",
    ]]

    t = Table(data, colWidths=[35*mm]*5)
    t.setStyle(TableStyle([
        ("BACKGROUND",  (0,0), (-1,-1), LIGHT),
        ("BACKGROUND",  (1,0), (1,0),   colors.HexColor("#E1F5EE")),
        ("BACKGROUND",  (2,0), (2,0),   colors.HexColor("#FAECE7")),
        ("ALIGN",       (0,0), (-1,-1), "CENTER"),
        ("VALIGN",      (0,0), (-1,-1), "MIDDLE"),
        ("FONTNAME",    (0,0), (-1,-1), "Helvetica-Bold"),
        ("FONTSIZE",    (0,0), (-1,-1), 11),
        ("ROWBACKGROUNDS", (0,0), (-1,-1), [LIGHT]),
        ("BOX",         (0,0), (-1,-1), 0.5, BORDER),
        ("INNERGRID",   (0,0), (-1,-1), 0.5, BORDER),
        ("TOPPADDING",  (0,0), (-1,-1), 10),
        ("BOTTOMPADDING",(0,0),(-1,-1), 10),
        ("ROWHEIGHT",   (0,0), (-1,-1), 18*mm),
    ]))
    return t


# ── Helper: aspect breakdown table ───────────────────────────────────────────
def aspect_table(df, styles):
    aspect_counts = df['aspect'].value_counts()
    total = len(df)

    rows = [["Aspect", "Count", "% of Reviews", "Dominant Sentiment"]]
    for aspect, count in aspect_counts.items():
        subset = df[df['aspect'] == aspect]
        dominant = subset['final_label'].value_counts().idxmax()
        pct = round(count / total * 100, 1)
        rows.append([aspect, str(count), f"{pct}%", dominant])

    t = Table(rows, colWidths=[55*mm, 25*mm, 40*mm, 55*mm])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,0),  DARK),
        ("TEXTCOLOR",     (0,0), (-1,0),  WHITE),
        ("FONTNAME",      (0,0), (-1,0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0,0), (-1,-1), 9),
        ("ALIGN",         (1,0), (-1,-1), "CENTER"),
        ("ROWBACKGROUNDS",(0,1), (-1,-1), [WHITE, LIGHT]),
        ("BOX",           (0,0), (-1,-1), 0.5, BORDER),
        ("INNERGRID",     (0,0), (-1,-1), 0.3, BORDER),
        ("TOPPADDING",    (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
    ]))
    return t


# ── Helper: reviews table ─────────────────────────────────────────────────────
def reviews_table(df, sentiment_filter, max_rows=5):
    subset = df[df['final_label'] == sentiment_filter].head(max_rows)
    if subset.empty:
        return None

    rows = [["Review", "Score", "Aspect", "Rating"]]
    for _, row in subset.iterrows():
        stars = "★" * int(row['rating']) + "☆" * (5 - int(row['rating']))
        text = row['review_text'][:120] + ("..." if len(row['review_text']) > 120 else "")
        rows.append([text, str(round(row['final_score'], 3)), row['aspect'], stars])

    t = Table(rows, colWidths=[90*mm, 22*mm, 35*mm, 28*mm])
    header_color = GREEN if sentiment_filter == "Positive" else RED if sentiment_filter == "Negative" else AMBER
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,0),  header_color),
        ("TEXTCOLOR",     (0,0), (-1,0),  WHITE),
        ("FONTNAME",      (0,0), (-1,0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0,0), (-1,-1), 8),
        ("ALIGN",         (1,0), (-1,-1), "CENTER"),
        ("ROWBACKGROUNDS",(0,1), (-1,-1), [WHITE, LIGHT]),
        ("BOX",           (0,0), (-1,-1), 0.5, BORDER),
        ("INNERGRID",     (0,0), (-1,-1), 0.3, BORDER),
        ("TOPPADDING",    (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("VALIGN",        (0,0), (-1,-1), "TOP"),
    ]))
    return t


# ── Page header/footer ────────────────────────────────────────────────────────
def on_page(canvas, doc):
    canvas.saveState()
    w, h = A4

    # Header bar
    canvas.setFillColor(DARK)
    canvas.rect(0, h - 18*mm, w, 18*mm, fill=1, stroke=0)
    canvas.setFillColor(WHITE)
    canvas.setFont("Helvetica-Bold", 10)
    canvas.drawString(15*mm, h - 12*mm, "Review Intelligence System")
    canvas.setFont("Helvetica", 9)
    canvas.drawRightString(w - 15*mm, h - 12*mm, f"Confidential — {datetime.now().strftime('%B %Y')}")

    # Footer
    canvas.setFillColor(colors.HexColor("#888888"))
    canvas.setFont("Helvetica", 8)
    canvas.drawString(15*mm, 10*mm, "Enterprise Review Intelligence System — AI-powered NLP Analysis")
    canvas.drawRightString(w - 15*mm, 10*mm, f"Page {doc.page}")

    canvas.restoreState()


# ── Main export function ──────────────────────────────────────────────────────
def generate_report(df: pd.DataFrame, stats: dict, alerts: list,
                    industry: str, ai_summary: str = None) -> io.BytesIO:
    """
    Generate a PDF report from analysis results.

    Args:
        df          : Analyzed DataFrame from run_full_analysis()
        stats       : Dict from get_summary_stats()
        alerts      : List from check_crisis()
        industry    : Industry string (FMCG / Banking / Pharma / Fragrance)
        ai_summary  : Raw AI summary text (optional)

    Returns:
        io.BytesIO containing the PDF
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=22*mm, bottomMargin=20*mm,
        leftMargin=15*mm, rightMargin=15*mm
    )

    S = build_styles()
    story = []
    w = A4[0] - 30*mm  # usable width

    # ── Cover page ────────────────────────────────────────────────────────────
    story.append(Spacer(1, 40*mm))

    # Title block with background via a 1-row table
    cover_data = [[
        Paragraph("Review Intelligence Report", S["cover_title"]),
    ]]
    cover_table = Table(cover_data, colWidths=[w])
    cover_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), DARK),
        ("TOPPADDING",    (0,0), (-1,-1), 20),
        ("BOTTOMPADDING", (0,0), (-1,-1), 20),
        ("ROUNDEDCORNERS", [6]),
    ]))
    story.append(cover_table)
    story.append(Spacer(1, 8*mm))

    meta_data = [[
        Paragraph(f"Industry: <b>{industry}</b>", S["body"]),
        Paragraph(f"Generated: <b>{datetime.now().strftime('%d %B %Y, %I:%M %p')}</b>", S["body"]),
        Paragraph(f"Total Reviews Analyzed: <b>{stats['total_reviews']}</b>", S["body"]),
    ]]
    meta_table = Table(meta_data, colWidths=[w/3]*3)
    meta_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), LIGHT),
        ("BOX",        (0,0), (-1,-1), 0.5, BORDER),
        ("INNERGRID",  (0,0), (-1,-1), 0.3, BORDER),
        ("ALIGN",      (0,0), (-1,-1), "CENTER"),
        ("TOPPADDING", (0,0), (-1,-1), 8),
        ("BOTTOMPADDING",(0,0),(-1,-1), 8),
    ]))
    story.append(meta_table)
    story.append(PageBreak())

    # ── Section 1: Overview metrics ───────────────────────────────────────────
    story.append(Paragraph("1. Executive Overview", S["section_heading"]))
    story.append(HRFlowable(width=w, thickness=1, color=PURPLE, spaceAfter=6))
    story.append(stat_table(stats))
    story.append(Spacer(1, 6*mm))

    # ── Section 2: Crisis Alerts ──────────────────────────────────────────────
    if alerts:
        story.append(Paragraph("2. Crisis Alerts", S["section_heading"]))
        story.append(HRFlowable(width=w, thickness=1, color=RED, spaceAfter=6))
        for alert in alerts:
            style = S["alert_critical"] if alert['type'] == "CRITICAL" else S["alert_warning"]
            story.append(Paragraph(f"{alert['icon']}  {alert['type']}: {alert['message']}", style))
        story.append(Spacer(1, 4*mm))

    # ── Section 3: Sentiment distribution ────────────────────────────────────
    section_num = 3 if alerts else 2
    story.append(Paragraph(f"{section_num}. Sentiment Distribution", S["section_heading"]))
    story.append(HRFlowable(width=w, thickness=1, color=GREEN, spaceAfter=6))

    sent_counts = df['final_label'].value_counts()
    total = len(df)
    sent_rows = [["Sentiment", "Count", "Percentage"]]
    sent_colors_map = {"Positive": GREEN, "Negative": RED, "Neutral": AMBER}
    for label, count in sent_counts.items():
        sent_rows.append([label, str(count), f"{round(count/total*100, 1)}%"])

    sent_table = Table(sent_rows, colWidths=[60*mm, 40*mm, 75*mm])
    sent_table.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,0),  PURPLE),
        ("TEXTCOLOR",     (0,0), (-1,0),  WHITE),
        ("FONTNAME",      (0,0), (-1,0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0,0), (-1,-1), 10),
        ("ALIGN",         (1,0), (-1,-1), "CENTER"),
        ("ROWBACKGROUNDS",(0,1), (-1,-1), [WHITE, LIGHT]),
        ("BOX",           (0,0), (-1,-1), 0.5, BORDER),
        ("INNERGRID",     (0,0), (-1,-1), 0.3, BORDER),
        ("TOPPADDING",    (0,0), (-1,-1), 7),
        ("BOTTOMPADDING", (0,0), (-1,-1), 7),
    ]))
    story.append(sent_table)
    story.append(Spacer(1, 6*mm))

    # ── Section 4: Aspect breakdown ───────────────────────────────────────────
    section_num += 1
    story.append(Paragraph(f"{section_num}. Aspect / Topic Breakdown", S["section_heading"]))
    story.append(HRFlowable(width=w, thickness=1, color=AMBER, spaceAfter=6))
    story.append(aspect_table(df, S))
    story.append(Spacer(1, 6*mm))

    # ── Section 5: AI Summary ─────────────────────────────────────────────────
    if ai_summary:
        section_num += 1
        story.append(Paragraph(f"{section_num}. AI Executive Summary", S["section_heading"]))
        story.append(HRFlowable(width=w, thickness=1, color=PURPLE, spaceAfter=6))

        complaints, strengths, action = [], [], ""
        in_complaints = in_strengths = False
        for line in ai_summary.strip().split('\n'):
            if 'COMPLAINTS' in line:
                in_complaints, in_strengths = True, False
            elif 'STRENGTHS' in line:
                in_complaints, in_strengths = False, True
            elif 'ACTION:' in line:
                in_complaints = in_strengths = False
                action = line.replace('ACTION:', '').strip()
            elif in_complaints and line.startswith('- '):
                complaints.append(line[2:].strip())
            elif in_strengths and line.startswith('- '):
                strengths.append(line[2:].strip())

        ai_data = [
            [Paragraph("<b>Top Complaints</b>", S["body"]),
             Paragraph("<b>Key Strengths</b>", S["body"])],
        ]
        complaints_text = "<br/>".join([f"&#x2022; {c}" for c in complaints]) or "N/A"
        strengths_text  = "<br/>".join([f"&#x2022; {s}" for s in strengths])  or "N/A"
        ai_data.append([
            Paragraph(complaints_text, S["body"]),
            Paragraph(strengths_text,  S["body"]),
        ])

        ai_table = Table(ai_data, colWidths=[w/2, w/2])
        ai_table.setStyle(TableStyle([
            ("BACKGROUND",    (0,0), (0,0), colors.HexColor("#FAECE7")),
            ("BACKGROUND",    (1,0), (1,0), colors.HexColor("#E1F5EE")),
            ("BACKGROUND",    (0,1), (0,1), WHITE),
            ("BACKGROUND",    (1,1), (1,1), WHITE),
            ("BOX",           (0,0), (-1,-1), 0.5, BORDER),
            ("INNERGRID",     (0,0), (-1,-1), 0.3, BORDER),
            ("TOPPADDING",    (0,0), (-1,-1), 8),
            ("BOTTOMPADDING", (0,0), (-1,-1), 8),
            ("LEFTPADDING",   (0,0), (-1,-1), 10),
            ("VALIGN",        (0,0), (-1,-1), "TOP"),
        ]))
        story.append(ai_table)

        if action:
            story.append(Spacer(1, 4*mm))
            action_data = [[Paragraph(f"&#x1F4A1; <b>Recommended Action:</b> {action}", S["body"])]]
            action_table = Table(action_data, colWidths=[w])
            action_table.setStyle(TableStyle([
                ("BACKGROUND",    (0,0), (-1,-1), colors.HexColor("#EEF2FF")),
                ("BOX",           (0,0), (-1,-1), 0.5, PURPLE),
                ("TOPPADDING",    (0,0), (-1,-1), 10),
                ("BOTTOMPADDING", (0,0), (-1,-1), 10),
                ("LEFTPADDING",   (0,0), (-1,-1), 12),
            ]))
            story.append(action_table)
        story.append(Spacer(1, 6*mm))

    # ── Section 6: Sample reviews ─────────────────────────────────────────────
    section_num += 1
    story.append(PageBreak())
    story.append(Paragraph(f"{section_num}. Sample Reviews", S["section_heading"]))
    story.append(HRFlowable(width=w, thickness=1, color=DARK, spaceAfter=6))

    for sentiment in ["Negative", "Positive", "Neutral"]:
        t = reviews_table(df, sentiment, max_rows=5)
        if t:
            story.append(Paragraph(f"{sentiment} Reviews", S["body"]))
            story.append(t)
            story.append(Spacer(1, 4*mm))

    # ── Build ─────────────────────────────────────────────────────────────────
    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    buffer.seek(0)
    return buffer