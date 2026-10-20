"""Generate updated professional 2-page landscape PDF roadmap for ORBITL1-AX25.

Outputs:
  docs/project/ORBITL1_AX25_Roadmap_Clear.pdf
"""

from __future__ import annotations

import os
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "docs" / "project"
OUT_DIR.mkdir(parents=True, exist_ok=True)
PDF_PATH = OUT_DIR / "ORBITL1_AX25_Roadmap_Clear.pdf"

# Fonts & OpenType Shaping Setup
try:
    import uharfbuzz  # noqa: F401
    HAS_SHAPING = True
except ImportError:
    HAS_SHAPING = False

FONT_REGULAR = "Helvetica"
FONT_BOLD = "Helvetica-Bold"

windows_fonts = [
    ("Leelawadee", r"C:\Windows\Fonts\leelawad.ttf", r"C:\Windows\Fonts\leelawdb.ttf"),
    ("Tahoma", r"C:\Windows\Fonts\tahoma.ttf", r"C:\Windows\Fonts\tahomabd.ttf"),
    ("Arial", r"C:\Windows\Fonts\arial.ttf", r"C:\Windows\Fonts\arialbd.ttf"),
]

for name, regular, bold in windows_fonts:
    if os.path.exists(regular):
        try:
            pdfmetrics.registerFont(TTFont(name, regular))
            if os.path.exists(bold):
                pdfmetrics.registerFont(TTFont(f"{name}-Bold", bold))
                FONT_BOLD = f"{name}-Bold"
            else:
                FONT_BOLD = name
            FONT_REGULAR = name
            break
        except Exception:
            pass

# Theme Colors extracted from original vector design
C_NAVY = colors.HexColor("#07182B")
C_CYAN = colors.HexColor("#26C6E3")
C_GREEN = colors.HexColor("#22B573")
C_BLUE = colors.HexColor("#3B82F6")
C_GRAY_BADGE = colors.HexColor("#64748B")
C_BORDER = colors.HexColor("#DBE5ED")
C_BG_BAR = colors.HexColor("#F4F7FA")
C_TITLE = colors.HexColor("#0F172A")
C_DESC = colors.HexColor("#475569")
C_MUTED = colors.HexColor("#94A3B8")
C_WHITE = colors.white

# Amber callout colors
C_AMBER_BG = colors.HexColor("#FFF7E6")
C_AMBER_BORDER = colors.HexColor("#F2CC72")
C_AMBER_ACCENT = colors.HexColor("#F5A623")
C_AMBER_TEXT = colors.HexColor("#1E293B")


def get_styles():
    return {
        "Category": ParagraphStyle(
            "Category",
            fontName=FONT_BOLD,
            fontSize=10,
            leading=12,
            textColor=C_CYAN,
            shaping=HAS_SHAPING,
        ),
        "MainTitle": ParagraphStyle(
            "MainTitle",
            fontName=FONT_BOLD,
            fontSize=21,
            leading=25,
            textColor=C_WHITE,
            shaping=HAS_SHAPING,
        ),
        "Subtitle": ParagraphStyle(
            "Subtitle",
            fontName=FONT_REGULAR,
            fontSize=10,
            leading=13,
            textColor=C_MUTED,
            shaping=HAS_SHAPING,
        ),
        "LegendBold": ParagraphStyle(
            "LegendBold",
            fontName=FONT_BOLD,
            fontSize=9.5,
            leading=12,
            textColor=C_TITLE,
            shaping=HAS_SHAPING,
        ),
        "LegendRegular": ParagraphStyle(
            "LegendRegular",
            fontName=FONT_REGULAR,
            fontSize=9.5,
            leading=12,
            textColor=C_DESC,
            shaping=HAS_SHAPING,
        ),
        "PhaseNumber": ParagraphStyle(
            "PhaseNumber",
            fontName=FONT_BOLD,
            fontSize=13,
            leading=16,
            textColor=C_WHITE,
            alignment=1,  # Centered
            shaping=HAS_SHAPING,
        ),
        "CardTitle": ParagraphStyle(
            "CardTitle",
            fontName=FONT_BOLD,
            fontSize=11.5,
            leading=14,
            textColor=C_TITLE,
            shaping=HAS_SHAPING,
        ),
        "CardDesc": ParagraphStyle(
            "CardDesc",
            fontName=FONT_REGULAR,
            fontSize=8.8,
            leading=12,
            textColor=C_DESC,
            shaping=HAS_SHAPING,
        ),
        "StatusBadge": ParagraphStyle(
            "StatusBadge",
            fontName=FONT_BOLD,
            fontSize=9,
            leading=11,
            textColor=C_WHITE,
            alignment=1,  # Centered
            shaping=HAS_SHAPING,
        ),
        "CalloutText": ParagraphStyle(
            "CalloutText",
            fontName=FONT_REGULAR,
            fontSize=9.5,
            leading=13,
            textColor=C_AMBER_TEXT,
            shaping=HAS_SHAPING,
        ),
        "Footer": ParagraphStyle(
            "Footer",
            fontName=FONT_REGULAR,
            fontSize=8,
            leading=10,
            textColor=C_MUTED,
            shaping=HAS_SHAPING,
        ),
        "FooterPage": ParagraphStyle(
            "FooterPage",
            fontName=FONT_BOLD,
            fontSize=8,
            leading=10,
            textColor=C_MUTED,
            alignment=2,  # Right
            shaping=HAS_SHAPING,
        ),
    }


def draw_header(c: canvas.Canvas, main_title: str, subtitle: str, styles):
    # Header Background Banner
    c.saveState()
    c.setFillColor(C_NAVY)
    c.rect(0, 595.28 - 99.2, 841.89, 99.2, fill=1, stroke=0)

    # Header texts
    p_cat = Paragraph("ORBITL-1 • AX.25 PROJECT ROADMAP", styles["Category"])
    p_cat.wrap(400, 20)
    p_cat.drawOn(c, 39.7, 595.28 - 30)

    p_title = Paragraph(main_title, styles["MainTitle"])
    p_title.wrap(600, 30)
    p_title.drawOn(c, 39.7, 595.28 - 60)

    p_sub = Paragraph(subtitle, styles["Subtitle"])
    p_sub.wrap(400, 20)
    p_sub.drawOn(c, 39.7, 595.28 - 83)
    c.restoreState()


def draw_legend(c: canvas.Canvas, styles):
    c.saveState()
    x = 39.7
    y = 595.28 - 141.0
    w = 762.5
    h = 27.6

    # Bar background
    c.setFillColor(C_BG_BAR)
    c.setStrokeColor(C_BORDER)
    c.setLineWidth(0.6)
    c.roundRect(x, y, w, h, radius=13.8, fill=1, stroke=1)

    # 1. Phase 0-4 เสร็จแล้ว
    c.setFillColor(C_GREEN)
    c.roundRect(51.0, y + 8.1, 11.3, 11.3, radius=2.5, fill=1, stroke=0)
    p1 = Paragraph("<b>Phase 0-4</b> &nbsp;เสร็จแล้ว", styles["LegendBold"])
    p1.wrap(180, 16)
    p1.drawOn(c, 70.0, y + 7.5)

    # 2. Phase 5 งานถัดไป
    c.setFillColor(C_BLUE)
    c.roundRect(301.4, y + 8.1, 11.3, 11.3, radius=2.5, fill=1, stroke=0)
    p2 = Paragraph("<b>Phase 5</b> &nbsp;งานถัดไป", styles["LegendBold"])
    p2.wrap(180, 16)
    p2.drawOn(c, 320.4, y + 7.5)

    # 3. Phase 6-10 ยังไม่เริ่ม
    c.setFillColor(C_GRAY_BADGE)
    c.roundRect(551.8, y + 8.1, 11.3, 11.3, radius=2.5, fill=1, stroke=0)
    p3 = Paragraph("<b>Phase 6-10</b> &nbsp;ยังไม่เริ่ม", styles["LegendBold"])
    p3.wrap(180, 16)
    p3.drawOn(c, 570.8, y + 7.5)

    c.restoreState()


def draw_card(
    c: canvas.Canvas,
    y_top: float,
    phase_label: str,
    title: str,
    desc: str,
    status_text: str,
    status_type: str,  # 'done', 'next', 'todo'
    styles,
):
    c.saveState()
    x = 39.7
    w = 762.5
    h = 52.1
    y_bottom = 595.28 - y_top - h

    # Outer Card Box
    c.setFillColor(C_WHITE)
    c.setStrokeColor(C_BORDER)
    c.setLineWidth(0.7)
    c.roundRect(x, y_bottom, w, h, radius=6.0, fill=1, stroke=1)

    # Left Phase Block
    block_w = 82.2
    c.setFillColor(C_NAVY)
    c.roundRect(x + 0.7, y_bottom + 0.7, block_w, h - 1.4, radius=5.0, fill=1, stroke=0)

    # Left Accent Stripe on the Phase Block
    if status_type == "done":
        accent_color = C_GREEN
    elif status_type == "next":
        accent_color = C_BLUE
    else:
        accent_color = C_CYAN

    c.setFillColor(accent_color)
    c.roundRect(x + 0.7, y_bottom + 0.7, 4.5, h - 1.4, radius=2.0, fill=1, stroke=0)

    # Phase Number text
    p_phase = Paragraph(phase_label, styles["PhaseNumber"])
    p_phase.wrap(block_w, 20)
    p_phase.drawOn(c, x + 0.7, y_bottom + 17.5)

    # Content (Title & Description)
    content_x = 134.0
    p_title = Paragraph(title, styles["CardTitle"])
    p_title.wrap(575, 16)
    p_title.drawOn(c, content_x, y_bottom + 27.5)

    p_desc = Paragraph(desc, styles["CardDesc"])
    p_desc.wrap(575, 16)
    p_desc.drawOn(c, content_x, y_bottom + 11.5)

    # Right Status Badge
    badge_x = 723.5
    badge_w = 73.7
    badge_h = 30.0
    badge_y = y_bottom + 11.0

    if status_type == "done":
        badge_bg = C_GREEN
    elif status_type == "next":
        badge_bg = C_BLUE
    else:
        badge_bg = C_GRAY_BADGE

    c.setFillColor(badge_bg)
    c.roundRect(badge_x, badge_y, badge_w, badge_h, radius=15.0, fill=1, stroke=0)

    p_badge = Paragraph(status_text, styles["StatusBadge"])
    p_badge.wrap(badge_w, 16)
    p_badge.drawOn(c, badge_x, badge_y + 9.5)

    c.restoreState()


def draw_callout_box(c: canvas.Canvas, y_top: float, text: str, styles):
    c.saveState()
    x = 39.7
    w = 762.5
    h = 36.0
    y_bottom = 595.28 - y_top - h

    # Box background
    c.setFillColor(C_AMBER_BG)
    c.setStrokeColor(C_AMBER_BORDER)
    c.setLineWidth(0.8)
    c.roundRect(x, y_bottom, w, h, radius=6.0, fill=1, stroke=1)

    # Left accent line
    c.setFillColor(C_AMBER_ACCENT)
    c.roundRect(x, y_bottom, 5.0, h, radius=2.5, fill=1, stroke=0)

    # Callout text
    p = Paragraph(text, styles["CalloutText"])
    p.wrap(w - 30, 20)
    p.drawOn(c, x + 16.0, y_bottom + 11.5)

    c.restoreState()


def draw_footer(c: canvas.Canvas, page_num_str: str, styles):
    c.saveState()
    p_foot = Paragraph("Ground Control System Project • AX.25 Protocol Track", styles["Footer"])
    p_foot.wrap(400, 15)
    p_foot.drawOn(c, 39.7, 14.0)

    p_num = Paragraph(page_num_str, styles["FooterPage"])
    p_num.wrap(100, 15)
    p_num.drawOn(c, 702.2, 14.0)
    c.restoreState()


def build_roadmap_pdf():
    styles = get_styles()
    c = canvas.Canvas(str(PDF_PATH), pagesize=landscape(A4))

    # =========================================================================
    # PAGE 1: PHASE 0 - PHASE 5
    # =========================================================================
    draw_header(c, "แผนงาน: สิ่งที่ทำแล้วและงานถัดไป", "Phase 0 - Phase 5", styles)
    draw_legend(c, styles)

    # Cards for Page 1
    page1_cards = [
        (
            146.7,
            "Phase 0",
            "Requirements & Scope",
            "กำหนดขอบเขตงาน AX.25, requirements ที่เกี่ยวข้อง, interface กับ subsystem อื่น และรายการ TBR",
            "เสร็จแล้ว",
            "done",
        ),
        (
            204.5,
            "Phase 1",
            "AX.25 Frame Core & Address Validation",
            "สร้างและถอดรหัส AX.25 UI frame: Address, Control 0x03, PID 0xF0, CRC-16/X-25 (ผ่าน 29/29 tests)",
            "เสร็จแล้ว",
            "done",
        ),
        (
            262.3,
            "Phase 2",
            "Bit / HDLC Layer & NRZI Line Coding",
            "แปลง frame เป็น bitstream: LSB-first, Bit Stuffing, HDLC Flags, NRZI และ decode ย้อนกลับ (ผ่าน 17/17 tests)",
            "เสร็จแล้ว",
            "done",
        ),
        (
            320.1,
            "Phase 3",
            "Integration & Standards Interoperability",
            "ทดสอบ E2E ข้าม Chunk ขนาดต่างๆ, เทียบเคียงเวกเตอร์มาตรฐาน AX.25/ISO, และ Reference Model (ผ่าน 22/22 tests)",
            "เสร็จแล้ว",
            "done",
        ),
        (
            377.9,
            "Phase 4",
            "Reliability & Fault Acceptance",
            "ทดสอบ Multi-seed, กู้คืนจาก Noise/CRC fail, ขนาดเฟรม 4078 ไบต์, Benchmark 500 เฟรม (ผ่าน 27/27 tests)",
            "เสร็จแล้ว",
            "done",
        ),
        (
            435.2,
            "Phase 5",
            "TNC / KISS Protocol & Ground Interface",
            "พัฒนาตัวเชื่อมต่อ KISS Protocol (Serial/TCP), กำหนดรูปแบบข้อมูล Telemetry และเชื่อมต่อ Ground Control",
            "งานถัดไป",
            "next",
        ),
    ]

    for y_top, phase_lbl, title, desc, st_txt, st_type in page1_cards:
        draw_card(c, y_top, phase_lbl, title, desc, st_txt, st_type, styles)

    draw_footer(c, "01", styles)
    c.showPage()

    # =========================================================================
    # PAGE 2: PHASE 6 - PHASE 10
    # =========================================================================
    draw_header(c, "แผนงาน: Integration และ Verification", "Phase 6 - Phase 10", styles)
    draw_legend(c, styles)

    page2_cards = [
        (
            146.7,
            "Phase 6",
            "SDR Integration",
            "เชื่อม protocol core กับ modem / SDR / physical communication chain เพื่อเริ่มทดสอบเส้นทางสัญญาณจริง",
            "ยังไม่เริ่ม",
            "todo",
        ),
        (
            204.5,
            "Phase 7",
            "RF Channel & Environmental Testing",
            "ทดสอบ Doppler shift (±3.5 kHz), สัญญาณรบกวนในช่องสัญญาณ RF จริง, วัดค่า BER/PER และ Link Margin",
            "ยังไม่เริ่ม",
            "todo",
        ),
        (
            262.3,
            "Phase 8",
            "AX.25 vs CSP Trade Study",
            "เปรียบเทียบ AX.25, CSP และแนวทาง Hybrid แล้วจัดทำเหตุผลในการเลือก protocol สำหรับ ORBITL-1",
            "ยังไม่เริ่ม",
            "todo",
        ),
        (
            320.1,
            "Phase 9",
            "ICD & Flight Integration",
            "ล็อก interface ร่วมระหว่าง Flight Software, Ground Software และ Communication/RF subsystem เป็น Protocol ICD",
            "ยังไม่เริ่ม",
            "todo",
        ),
        (
            377.9,
            "Phase 10",
            "FlatSat / End-to-End Verification",
            "ทดสอบทั้งสาย Flight Packet -> Protocol -> RF Path -> Ground Decode/Log และเก็บหลักฐานสำหรับการตรวจรับระบบ",
            "ยังไม่เริ่ม",
            "todo",
        ),
    ]

    for y_top, phase_lbl, title, desc, st_txt, st_type in page2_cards:
        draw_card(c, y_top, phase_lbl, title, desc, st_txt, st_type, styles)

    callout_msg = (
        "<b>จุดที่อยู่ตอนนี้:</b> Phase 0-4 เสร็จสมบูรณ์ (ผ่านการทดสอบระดับซอฟต์แวร์ 95/95 ข้อ) "
        "• <b>Phase 5</b> เป็นงานถัดไป • Phase 6-10 ยังไม่เริ่ม"
    )
    draw_callout_box(c, 440.9, callout_msg, styles)

    draw_footer(c, "02", styles)
    c.showPage()

    c.save()
    print(f"Generated Updated Roadmap PDF: {PDF_PATH} ({os.path.getsize(PDF_PATH)} bytes)")


if __name__ == "__main__":
    build_roadmap_pdf()
