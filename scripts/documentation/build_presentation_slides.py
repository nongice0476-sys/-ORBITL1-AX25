"""Build presentation slide PDF for ORBITL1-AX25 progress report.

Generates:
  docs/project/ORBITL1_AX25_Progress_Presentation_Slides.pdf
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "docs" / "project"
OUT_DIR.mkdir(parents=True, exist_ok=True)
PDF_PATH = OUT_DIR / "ORBITL1_AX25_Progress_Presentation_Slides.pdf"

# Fonts & Shaping
try:
    import uharfbuzz
    HAS_SHAPING = True
except ImportError:
    HAS_SHAPING = False

FONT_REGULAR = "Helvetica"
FONT_BOLD = "Helvetica-Bold"

windows_fonts = [
    ("Leelawadee", r"C:\Windows\Fonts\leelawad.ttf", r"C:\Windows\Fonts\leelawadb.ttf"),
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

# Theme Colors
C_NAVY = colors.HexColor("#0D2235")
C_DEEP = colors.HexColor("#12304A")
C_CYAN = colors.HexColor("#18A6B7")
C_BLUE = colors.HexColor("#1D5F91")
C_DARK = colors.HexColor("#233746")
C_MUTED = colors.HexColor("#5C7180")
C_BG_LIGHT = colors.HexColor("#F4F9FB")
C_NOTE_BG = colors.HexColor("#EAF5F8")
C_CODE_BG = colors.HexColor("#102E43")
C_BORDER = colors.HexColor("#C9DDE6")
C_GREEN = colors.HexColor("#0E703C")
C_GREEN_BG = colors.HexColor("#E6F4EA")


class SlideCanvas(canvas.Canvas):
    """Presentation slide canvas with running header, accent bars, and page numbering."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_slide_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_slide_decorations(self, total_slides):
        self.saveState()
        width, height = self._pagesize

        if self._pageNumber == 1:
            # Title slide background banner
            self.setFillColor(C_NAVY)
            self.rect(0, 0, width, height, stroke=0, fill=1)
            self.setFillColor(C_CYAN)
            self.rect(0, 0, 16, height, stroke=0, fill=1)
            self.rect(0, 0, width, 10, stroke=0, fill=1)
            self.restoreState()
            return

        # Running Top Accent
        self.setFillColor(C_DEEP)
        self.rect(0, height - 12, width, 12, stroke=0, fill=1)
        self.setFillColor(C_CYAN)
        self.rect(0, height - 12, width * 0.35, 12, stroke=0, fill=1)

        # Bottom Footer Bar
        self.setFillColor(C_NAVY)
        self.rect(0, 0, width, 24, stroke=0, fill=1)
        self.setFillColor(C_CYAN)
        self.rect(0, 22, width, 2, stroke=0, fill=1)

        self.setFillColor(colors.white)
        self.setFont(FONT_BOLD, 8)
        self.drawString(28, 8, "ORBITL-1 CUBESAT  |  AX.25 COMMUNICATION SUBSYSTEM")
        self.setFont(FONT_REGULAR, 8)
        self.drawString(320, 8, "PROGRESS PRESENTATION  •  PHASES 1–4 FULL SOFTWARE VERIFICATION")

        page_str = f"Slide {self._pageNumber} of {total_slides}"
        self.drawRightString(width - 28, 8, page_str)

        self.restoreState()


def get_styles():
    styles = {}

    styles["CoverTitle"] = ParagraphStyle(
        "CoverTitle",
        fontName=FONT_BOLD,
        fontSize=28,
        leading=34,
        textColor=colors.white,
        spaceAfter=8,
        shaping=HAS_SHAPING,
    )
    styles["CoverSub"] = ParagraphStyle(
        "CoverSub",
        fontName=FONT_REGULAR,
        fontSize=13,
        leading=18,
        textColor=C_CYAN,
        spaceAfter=20,
        shaping=HAS_SHAPING,
    )
    styles["CoverMeta"] = ParagraphStyle(
        "CoverMeta",
        fontName=FONT_REGULAR,
        fontSize=9.5,
        leading=14,
        textColor=colors.HexColor("#C9DDE6"),
        shaping=HAS_SHAPING,
    )
    styles["SlideTitle"] = ParagraphStyle(
        "SlideTitle",
        fontName=FONT_BOLD,
        fontSize=18,
        leading=22,
        textColor=C_DEEP,
        spaceAfter=2,
        shaping=HAS_SHAPING,
    )
    styles["SlideCategory"] = ParagraphStyle(
        "SlideCategory",
        fontName=FONT_BOLD,
        fontSize=8.5,
        leading=11,
        textColor=C_CYAN,
        spaceAfter=4,
        shaping=HAS_SHAPING,
    )
    styles["SlideSub"] = ParagraphStyle(
        "SlideSub",
        fontName=FONT_REGULAR,
        fontSize=9.5,
        leading=13,
        textColor=C_MUTED,
        spaceAfter=10,
        shaping=HAS_SHAPING,
    )
    styles["SectionHeader"] = ParagraphStyle(
        "SectionHeader",
        fontName=FONT_BOLD,
        fontSize=11,
        leading=14,
        textColor=C_DEEP,
        spaceBefore=4,
        spaceAfter=4,
        shaping=HAS_SHAPING,
    )
    styles["Normal"] = ParagraphStyle(
        "Normal",
        fontName=FONT_REGULAR,
        fontSize=8.5,
        leading=12,
        textColor=C_DARK,
        shaping=HAS_SHAPING,
    )
    styles["NormalBold"] = ParagraphStyle(
        "NormalBold",
        fontName=FONT_BOLD,
        fontSize=8.5,
        leading=12,
        textColor=C_DEEP,
        shaping=HAS_SHAPING,
    )
    styles["TableHead"] = ParagraphStyle(
        "TableHead",
        fontName=FONT_BOLD,
        fontSize=8,
        leading=10.5,
        textColor=colors.white,
        shaping=HAS_SHAPING,
    )
    styles["TableCell"] = ParagraphStyle(
        "TableCell",
        fontName=FONT_REGULAR,
        fontSize=7.8,
        leading=10.5,
        textColor=C_DARK,
        shaping=HAS_SHAPING,
    )
    styles["TableCellBold"] = ParagraphStyle(
        "TableCellBold",
        fontName=FONT_BOLD,
        fontSize=7.8,
        leading=10.5,
        textColor=C_DEEP,
        shaping=HAS_SHAPING,
    )
    styles["TableCellGreen"] = ParagraphStyle(
        "TableCellGreen",
        fontName=FONT_BOLD,
        fontSize=7.8,
        leading=10.5,
        textColor=C_GREEN,
        shaping=HAS_SHAPING,
    )
    styles["KpiNumber"] = ParagraphStyle(
        "KpiNumber",
        fontName=FONT_BOLD,
        fontSize=20,
        leading=24,
        textColor=C_DEEP,
        alignment=1,
        shaping=HAS_SHAPING,
    )
    styles["KpiLabel"] = ParagraphStyle(
        "KpiLabel",
        fontName=FONT_BOLD,
        fontSize=8,
        leading=10,
        textColor=C_BLUE,
        alignment=1,
        shaping=HAS_SHAPING,
    )
    styles["KpiSub"] = ParagraphStyle(
        "KpiSub",
        fontName=FONT_REGULAR,
        fontSize=7,
        leading=9,
        textColor=C_MUTED,
        alignment=1,
        shaping=HAS_SHAPING,
    )
    styles["CardTitle"] = ParagraphStyle(
        "CardTitle",
        fontName=FONT_BOLD,
        fontSize=9.5,
        leading=12,
        textColor=C_DEEP,
        spaceAfter=3,
        shaping=HAS_SHAPING,
    )
    styles["CardBody"] = ParagraphStyle(
        "CardBody",
        fontName=FONT_REGULAR,
        fontSize=7.8,
        leading=10.5,
        textColor=C_DARK,
        shaping=HAS_SHAPING,
    )
    return styles


def create_slide_header(category: str, title: str, subtitle: str, styles) -> list:
    return [
        Paragraph(category.upper(), styles["SlideCategory"]),
        Paragraph(title, styles["SlideTitle"]),
        Paragraph(subtitle, styles["SlideSub"]),
        Spacer(1, 4),
    ]


def make_kpi_card(number: str, label: str, sub: str, styles, width: float = 185) -> Table:
    t = Table(
        [
            [Paragraph(number, styles["KpiNumber"])],
            [Paragraph(label, styles["KpiLabel"])],
            [Paragraph(sub, styles["KpiSub"])],
        ],
        colWidths=[width],
    )
    t.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), C_BG_LIGHT),
            ("BOX", (0, 0), (-1, -1), 1, C_BORDER),
            ("LINEBEFORE", (0, 0), (0, -1), 3.5, C_CYAN),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ])
    )
    return t


def make_card(title: str, text: str, styles, width: float = 250, border_color=C_CYAN) -> Table:
    t = Table(
        [
            [Paragraph(f"<b>{title}</b>", styles["CardTitle"])],
            [Paragraph(text, styles["CardBody"])],
        ],
        colWidths=[width],
    )
    t.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), C_BG_LIGHT),
            ("BOX", (0, 0), (-1, -1), 1, C_BORDER),
            ("LINEBEFORE", (0, 0), (0, -1), 3.5, border_color),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ])
    )
    return t


def make_slide_table(headers: list[str], rows: list[list], col_widths: list[float], styles) -> Table:
    data = [[Paragraph(h, styles["TableHead"]) for h in headers]]
    for r in rows:
        row_data = []
        for c in r:
            if isinstance(c, str):
                if c in ("PASS", "VERIFIED", "100%", "SUCCESS", "MATCH"):
                    p = Paragraph(f"<b>{c}</b>", styles["TableCellGreen"])
                elif c.isupper() and len(c) <= 12:
                    p = Paragraph(f"<b>{c}</b>", styles["TableCellBold"])
                else:
                    p = Paragraph(c, styles["TableCell"])
            else:
                p = c
            row_data.append(p)
        data.append(row_data)

    t = Table(data, colWidths=col_widths)
    t.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), C_DEEP),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, C_BG_LIGHT]),
            ("GRID", (0, 0), (-1, -1), 0.5, C_BORDER),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ])
    )
    return t


def build_presentation_slides():
    doc = SimpleDocTemplate(
        str(PDF_PATH),
        pagesize=landscape(A4),
        leftMargin=32,
        rightMargin=32,
        topMargin=26,
        bottomMargin=34,
    )
    styles = get_styles()
    story = []

    # =========================================================================
    # SLIDE 1: COVER SLIDE
    # =========================================================================
    story.append(Spacer(1, 40))
    story.append(Paragraph("ORBITL-1 CUBESAT MISSION", styles["CoverSub"]))
    story.append(Paragraph("ความคืบหน้าการพัฒนาระบบสื่อสาร AX.25<br/>(Phase 1 – Phase 4 Verification Complete)", styles["CoverTitle"]))
    story.append(Spacer(1, 10))

    meta_text = """
    <b>สถานะโครงการ:</b> ผ่านการทดสอบระดับซอฟต์แวร์ 100% (Software-Complete)<br/>
    <b>ผลการทดสอบ:</b> 95 / 95 Unit, Integration & Reliability Tests PASS (Zero Regressions)<br/>
    <b>ขอบเขตที่ตรวจรับ:</b> AX.25 Frame Core, HDLC/NRZI Layer, E2E Integration, Reliability & Benchmarks<br/>
    <b>วันที่รายงาน:</b> ตุลาคม 2026  |  ทีมวิศวกรรมระบบสื่อสาร ORBITL-1
    """
    story.append(Paragraph(meta_text, styles["CoverMeta"]))
    story.append(Spacer(1, 30))

    # =========================================================================
    # SLIDE 2: EXECUTIVE SUMMARY & KEY METRICS
    # =========================================================================
    story.append(PageBreak())
    story.extend(create_slide_header(
        "Executive Summary",
        "ภาพรวมความคืบหน้าและดัชนีชี้วัดหลัก (Key Engineering Metrics)",
        "ระบบโปรโตคอล AX.25 สำหรับ ORBITL-1 พัฒนาและตรวจสอบความสมบูรณ์ครบทั้ง 4 เฟสซอฟต์แวร์",
        styles,
    ))

    # 4 KPI Cards
    kpis = Table([
        [
            make_kpi_card("95 / 95", "AUTOMATED TESTS", "ผ่านครบทุกการทดสอบ (100% Pass)", styles, 185),
            make_kpi_card("1,000+", "RANDOMIZED ROUND-TRIPS", "ทดสอบสุ่มหลากหลาย Seed ไม่มีหลุด", styles, 185),
            make_kpi_card("4,078 B", "MAX INFORMATION PAYLOAD", "ขีดจำกัดขนาดสูงสุดของ Profile", styles, 185),
            make_kpi_card("1.02 Mbps", "SOFTWARE THROUGHPUT", "864 เฟรม/วินาที (เร็วกว่า RF 100x)", styles, 185),
        ]
    ], colWidths=[195, 195, 195, 195])
    kpis.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story.append(kpis)
    story.append(Spacer(1, 14))

    # 3 Summary Cards
    cards = Table([
        [
            make_card(
                "1. Protocol Core & Framing (Phase 1-2)",
                "• สร้างและแปลงเฟรม AX.25 UI (Control 0x03, PID 0xF0)<br/>"
                "• คำนวณ CRC-16/X-25 และตรวจ FCS ก่อนถอดรหัส<br/>"
                "• จัดการ HDLC Bit-Stuffing, Flags 0x7E และแปลง NRZI<br/>"
                "• โค้ดเดิมใน Phase 1/2 ตรวจ SHA-256 ตรง 100% ไม่ถูกดัดแปลง",
                styles, 255, C_BLUE
            ),
            make_card(
                "2. Integration & Interoperability (Phase 3)",
                "• รัน End-to-End ตั้งแต่ Payload bytes → NRZI → Packet dict<br/>"
                "• รองรับการแบ่งส่งข้อมูลขนาดบิตไม่คงที่ (1, 3, 7, 13 บิต/ชิ้น)<br/>"
                "• ตรวจสอบเวกเตอร์มาตรฐาน ISO/IEC 3309 (0x906E)<br/>"
                "• เทียบสเปก AX.25 v2.2 และโมเดลอ้างอิงอิสระตรงกันบิตต่อบิต",
                styles, 255, C_CYAN
            ),
            make_card(
                "3. Reliability & Stress Defense (Phase 4)",
                "• ทนทานต่อสตรีมสัญญาณรบกวนและข้อมูลเสียหาย (Fault Injection)<br/>"
                "• ตรวจจับและปฏิเสธเฟรม Control/PID ที่ไม่ถูกต้อง 100%<br/>"
                "• ดักจับเฟรมขนาดเกิน (4079 ไบต์) ป้องกัน Memory บวม<br/>"
                "• วัด Throughput ต่อเนื่อง 500 เฟรม ทำงานเสถียรไม่มีค้าง",
                styles, 255, C_GREEN
            ),
        ]
    ], colWidths=[260, 260, 260])
    cards.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story.append(cards)

    # =========================================================================
    # SLIDE 3: WHAT WAS DONE (PHASES 1 TO 4 ARCHITECTURE)
    # =========================================================================
    story.append(PageBreak())
    story.extend(create_slide_header(
        "System Architecture",
        "สิ่งที่ทำไปแล้ว: สถาปัตยกรรมและกระบวนการทำงาน (End-to-End Pipeline)",
        "โครงสร้างการแปลงข้อมูลตั้งแต่ Payload จนถึงการถอดรหัสฝั่งสถานีภาคพื้นดิน",
        styles,
    ))

    # Pipeline Flow
    flow_steps = [
        ("1. Flight Payload", "ข้อมูลเทเลเมทรี<br/>(ไบต์คำสั่ง/ข้อมูลดาวเทียม)"),
        ("2. Phase 1 Core", "build_ui_frame()<br/>ใส่ Header, Addr, CRC-16"),
        ("3. Phase 2 TX", "encode_hdlc()<br/>Bit-Stuffing & ธง 0x7E"),
        ("4. Modulation", "nrzi_encode()<br/>แปลงเป็นระดับสัญญาณ 0/1"),
        ("5. Demod Handoff", "feed_nrzi_levels()<br/>ส่งต่อระดับบิตเข้าตัวถอด"),
        ("6. Phase 2 RX", "HDLCStreamDecoder<br/>ดึงบิตออก, ตรวจสอบ FCS"),
        ("7. Ground App", "decode_verified_body()<br/>ได้ข้อมูล Packet Dictionary"),
    ]
    p_row = []
    p_widths = []
    w_box = (780 - 6 * 14) / 7
    for i, (stitle, sdesc) in enumerate(flow_steps):
        p_row.append(Paragraph(f"<b>{stitle}</b><br/>{sdesc}", styles["TableCell"]))
        p_widths.append(w_box)
        if i < len(flow_steps) - 1:
            p_row.append(Paragraph("<b>→</b>", styles["KpiLabel"]))
            p_widths.append(14)

    t_flow = Table([p_row], colWidths=p_widths)
    t_flow_style = [
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]
    for idx in range(0, len(p_row), 2):
        t_flow_style.extend([
            ("BACKGROUND", (idx, 0), (idx, 0), C_BG_LIGHT),
            ("BOX", (idx, 0), (idx, 0), 1, C_CYAN),
        ])
    t_flow.setStyle(TableStyle(t_flow_style))
    story.append(t_flow)
    story.append(Spacer(1, 10))

    # Architecture Details Table
    arch_table = make_slide_table(
        ["โมดูล / เฟส", "หน้าที่รับผิดชอบในระบบ", "ข้อกำหนดทางเทคนิค (Profile Specification)", "สถานะ"],
        [
            ["Phase 1: AX.25 Frame Core", "จัดการโครงสร้างเฟรม, Call Sign และการตรวจสอบความถูกต้อง", "• Address: Destination + Source (ASCII 1-6 ตัว, SSID 0-15)<br/>• Frame: UI Control 0x03, PID 0xF0 (No Layer 3)<br/>• FCS: CRC-16/X-25 ส่ง Low-byte ก่อน", "สมบูรณ์ (VERIFIED)"],
            ["Phase 2: HDLC & NRZI", "การแปลงเป็นสตรีมบิตทางกายภาพและถอดรหัสบิต", "• Serialization: ส่ง LSB ก่อน (บิตต่ำขึ้นก่อน)<br/>• Bit Stuffing: แทรกบิต 0 หลังบิต 1 ติดกัน 5 ตัว<br/>• NRZI: บิต 0 เปลี่ยนสถานะ, บิต 1 คงสถานะเดิม<br/>• Buffer Cap: จำกัดขนาดเฟรมไม่เกิน 4096 ไบต์", "สมบูรณ์ (VERIFIED)"],
            ["Phase 3: Integration", "เชื่อมต่อส่ง-รับครบวงลูป และรองรับ Streaming", "• รองรับการแบ่งส่งข้อมูลขนาดบิตไม่สม่ำเสมอ (Chunking)<br/>• รองรับ Shared Flag (ใช้ธงร่วมกันระหว่างเฟรม)<br/>• กู้คืนระบบอัตโนมัติเมื่อเจอ Abort (บิต 1 ต่อกัน 7 ตัวขึ้นไป)", "สมบูรณ์ (VERIFIED)"],
            ["Phase 4: Reliability", "ความทนทานต่อสภาวะผิดปกติและวัดความเร็ว", "• ป้องกัน Payload ขนาดเกิน 4,078 ไบต์ (Header 16B + FCS 2B)<br/>• ปฏิเสธเฟรมผิดประเภท (I-frame, S-frame, PID IPv4/X.25)<br/>• รองรับสตรีมต่อเนื่องที่มีสัญญาณกวนปนเปื้อน 100%", "สมบูรณ์ (VERIFIED)"],
        ],
        [150, 230, 310, 90],
        styles,
    )
    story.append(arch_table)

    # =========================================================================
    # SLIDE 4: TESTING & VERIFICATION EVIDENCE
    # =========================================================================
    story.append(PageBreak())
    story.extend(create_slide_header(
        "Verification & Testing",
        "เทสอะไรบ้าง: รายละเอียดชุดทดสอบและการจำลองความผิดปกติ (Fault Injection)",
        "ชุดทดสอบครอบคลุม 95 การทดสอบ ทั้งระดับ Unit, Integration, Robustness และ Acceptance",
        styles,
    ))

    test_table = make_slide_table(
        ["หมวดหมู่การทดสอบ", "ไฟล์ทดสอบ", "จำนวน", "สถานการณ์ที่จำลองและทดสอบ (Test Scenarios)", "ผลลัพธ์"],
        [
            ["AX.25 Frame Core", "test_ax25_core.py", "29", "• เข้ารหัส/ถอดรหัส Address, Callsign ตัวพิมพ์เล็ก/ใหญ่, SSID เกิน 15<br/>• ตรวจสอบ CRC-16/X-25 เวกเตอร์มาตรฐาน 123456789 -> 0x906E<br/>• ปฏิเสธ Control/PID แปลกปลอม แม้ CRC จะคำนวณมาถูกต้อง", "PASS (29/29)"],
            ["HDLC & NRZI Layer", "test_hdlc.py", "10", "• ทดสอบ Bit Stuffing แทรก 0 เมื่อเจอ 11111 และ Unstuffing คืนรูป<br/>• ตรวจสอบการสลับระดับสัญญาณ NRZI ตรงตามตารางเวกเตอร์", "PASS (10/10)"],
            ["Receiver Pipeline", "test_receiver.py", "7", "• เชื่อม NRZI เข้าสู่ Receive Pipeline จำลองการส่งเป็นก้อนเล็ก 7 บิต<br/>• ส่งข้อมูลต่อเนื่อง 2 เฟรมติดกันและดึง Payload คืนได้ถูกต้อง", "PASS (7/7)"],
            ["Robustness Baseline", "test_reliability.py", "18", "• กู้คืนอัตโนมัติเมื่อหัว/ท้ายเฟรมขาดหาย (Missing Flags)<br/>• จำลอง Noise แปลกปลอมและเฟรมไม่สมบูรณ์คั่นกลาง<br/>• สุ่มทดสอบความถูกต้องไป-กลับ 1,000 รอบต่อเนื่อง", "PASS (18/18)"],
            ["Phase 3 E2E Integration", "test_integration.py", "22", "• ส่ง Payload มีบิต 1 ยาวๆ (0xFF*50, 0x7E*25) ไม่เกิด False Flag<br/>• แบ่งสตรีมทีละ 1, 2, 3, 5, 7, 11, 13, 17, 31, 64 บิต ไม่หลุดสถานะ<br/>• สลับบิต FCS (Single/Double-bit flip) มั่นใจว่าเฟรมเสียถูกทิ้ง 100%", "PASS (22/22)"],
            ["Phase 4 Acceptance", "test_acceptance.py", "9", "• Multi-seed Testing (Seed 20261009, 20261019, 42, 1337)<br/>• ทดสอบขนาด 4,078 ไบต์ (ผ่าน) และ 4,079 ไบต์ (ปฏิเสธทันที)<br/>• สตรีมต่อเนื่อง 100 เฟรมที่มีเฟรมเสีย/Abort/ขนาดเกินปนเปื้อน", "PASS (9/9)"],
        ],
        [125, 120, 45, 410, 80],
        styles,
    )
    story.append(test_table)
    story.append(Spacer(1, 6))

    story.append(Paragraph(
        "<b>สรุปผลการเทส:</b> รันผ่าน 100% ครบทั้ง 95 tests ภายในเวลา ~5.88 วินาที บนระบบ Python 3.14 โดยไม่มีข้อผิดพลาดใดๆ",
        styles["NormalBold"],
    ))

    # =========================================================================
    # SLIDE 5: INDEPENDENT INTEROPERABILITY EVIDENCE
    # =========================================================================
    story.append(PageBreak())
    story.extend(create_slide_header(
        "Interoperability Evidence",
        "หลักฐานการทำงานร่วมและเทียบมาตรฐานสากล (Independent Verification)",
        "ไม่เพียงแต่ทดสอบโค้ดตัวเอง แต่ยังเทียบกับเวกเตอร์มาตรฐานสากลและโมเดลอิสระ",
        styles,
    ))

    interop_table = make_slide_table(
        ["สถาบัน / เอกสารอ้างอิง", "เวกเตอร์ทดสอบที่นำมาเทียบ", "ค่าที่มาตรฐานกำหนด", "ผลลัพธ์จากโค้ด ORBITL-1", "สถานะการเทียบ"],
        [
            ["ISO/IEC 3309 / ITU-T X.25", "ข้อความ ASCII: '123456789'", "CRC-16 = 0x906E", "0x906E", "MATCH 100%"],
            ["ITU-T X.25 Standard", "สตริงว่าง: b''", "CRC-16 = 0x0000", "0x0000", "MATCH 100%"],
            ["Catalogue of CRCs (Cook)", "อักขระเดี่ยว: b'A'", "CRC-16 = 0xA3F5", "0xA3F5", "MATCH 100%"],
            ["AX.25 v2.2 Spec (Figure 3.5)", "Destination 'NJ7P', SSID 0, not last", "9C 94 6E A0 40 40 60", "9C 94 6E A0 40 40 60", "MATCH 100%"],
            ["AX.25 v2.2 Spec (Figure 3.6)", "Source 'N7LEM', SSID 0, last address", "9C 6E 98 8A 9A 40 61", "9C 6E 98 8A 9A 40 61", "MATCH 100%"],
            ["ISO 3309 FCS Residue", "เฟรมที่ถูกต้องต่อท้ายด้วย FCS", "ค่าคงที่ตกค้าง = 0xF0B8", "0xF0B8 (Residue Verified)", "MATCH 100%"],
            ["Independent Python Model", "โมเดลอ้างอิงอิสระที่เขียนขึ้นใหม่จากสูตรเพียวๆ", "ตรงกันทุกบิต ทุกไบต์", "ตรงกันสมบูรณ์ 100%", "MATCH 100%"],
        ],
        [150, 190, 160, 170, 110],
        styles,
    )
    story.append(interop_table)
    story.append(Spacer(1, 10))

    # SHA-256 Box
    hash_summary = """
    <b>การันตีความถูกต้องของไฟล์ Runtime เดิม (Zero Modification / SHA-256 Verified):</b><br/>
    • <code>src/ax25.py</code>: <code>8da3d41a47c8...</code> (ตรงกับก่อนเริ่มงาน 100%)<br/>
    • <code>src/ax25_hdlc.py</code>: <code>38fbab7afe40...</code> (ตรงกับก่อนเริ่มงาน 100%)<br/>
    • <code>src/ax25_receiver.py</code>: <code>7d9b6c1df0af...</code> (ตรงกับก่อนเริ่มงาน 100%)<br/>
    • <code>src/ax25_transmitter.py</code>: <code>612040815981...</code> (ตรงกับก่อนเริ่มงาน 100%)<br/>
    • <code>src/vendor/mobilinkd/HDLC.py</code>: <code>db5c61e16cbf...</code> (ตรงกับก่อนเริ่มงาน 100%)
    """
    story.append(make_card("ความปลอดภัยและความเสถียรของซอร์สโค้ด", hash_summary, styles, 780, C_GREEN))

    # =========================================================================
    # SLIDE 6: PERFORMANCE BENCHMARK
    # =========================================================================
    story.append(PageBreak())
    story.extend(create_slide_header(
        "Performance Benchmarks",
        "ได้ผลยังไง: ผลการวัดประสิทธิภาพและความเร็วของระบบ (Sustained Workload)",
        "วัดประสิทธิภาพจริงในการสตรีมข้อมูลต่อเนื่องผ่านท่อส่งสัญญาณ NRZI + HDLC + AX.25",
        styles,
    ))

    # 4 Benchmark KPIs
    b_kpis = Table([
        [
            make_kpi_card("500 Frames", "BURST LOAD", "74,000 ไบต์ (592,000 บิต)", styles, 185),
            make_kpi_card("0.579 s", "PROCESSING TIME", "เวลาถอดรหัสทั้งหมดในระบบ", styles, 185),
            make_kpi_card("864.0", "FRAMES PER SECOND", "อัตราประมวลผลเฟรมของซอฟต์แวร์", styles, 185),
            make_kpi_card("1.02 Mbps", "SUSTAINED DATA RATE", "ความเร็วการดึงข้อมูลต่อเนื่อง", styles, 185),
        ]
    ], colWidths=[195, 195, 195, 195])
    b_kpis.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story.append(b_kpis)
    story.append(Spacer(1, 14))

    # Benchmark Comparison Table
    bench_table = make_slide_table(
        ["ดัชนีชี้วัดประสิทธิภาพ", "ผลการทดสอบจริง (Measured)", "บริบทการสื่อสารผ่านดาวเทียม (Satellite Context)", "ความหมายทางวิศวกรรม"],
        [
            ["ปริมาณข้อมูลที่ประมวลผล", "500 เฟรม (74,000 ไบต์)", "เทียบเท่าการรับ Telemetry ต่อเนื่อง ~10 นาทีบนสัญญาณ 1200 bps", "เพียงพอต่อการรับข้อมูล 1 Pass การโคจรของสถานีภาคพื้น"],
            ["เวลาประมวลผล", "0.579 วินาที", "คิดเป็นเวลาถอดรหัสเฉลี่ยเพียง ~1.15 มิลลิวินาทีต่อ 1 เฟรม", "Real-time Processing ไม่มีอาการหน่วงหรือคอขวด"],
            ["อัตราการรับเฟรม", "864.0 เฟรม / วินาที", "อัตราส่งวิทยุดาวเทียมปกติอยู่ที่ 0.1 ถึง 2.0 เฟรม / วินาที", "ความเร็วซอฟต์แวร์สูงกว่าความเร็วรับวิทยุจริง >400 เท่า"],
            ["อัตรา Throughput ข้อมูล", "1,022.98 kbps (~1.02 Mbps)", "ช่องสัญญาณวิทยุสมัครเล่น CubeSat: 1.2 kbps (AFSK) หรือ 9.6 kbps (GFSK)", "มี Headroom เหลือเฟือ ไม่กิน CPU ของบอร์ดควบคุมภาคพื้น"],
            ["เสถียรภาพ Memory", "คงที่สมบูรณ์ (Zero Leak)", "รันติดต่อกันหลายพันเฟรม ขนาด Buffer ไม่เติบโตผิดปกติ", "ปลอดภัยสำหรับรันเป็น Background Daemon บนสถานีภาคพื้น"],
        ],
        [140, 160, 260, 220],
        styles,
    )
    story.append(bench_table)

    # =========================================================================
    # SLIDE 7: HARDWARE DEMARCATION & PHASE 5 ROADMAP
    # =========================================================================
    story.append(PageBreak())
    story.extend(create_slide_header(
        "Next Steps & Roadmap",
        "ขอบเขตซอฟต์แวร์ vs ฮาร์ดแวร์จริง และสิ่งที่ต้องทำต่อใน Phase 5",
        "กำหนดเส้นแบ่งการทำงานชัดเจน (Demarcation) เพื่อเตรียมเชื่อมต่อระบบจริงในขั้นถัดไป",
        styles,
    ))

    # Demarcation Table
    demarc_table = make_slide_table(
        ["ระดับชั้นการทำงาน (Layer)", "สถานะปัจจุบัน", "ส่วนที่ซอฟต์แวร์ทำเสร็จสมบูรณ์แล้ว", "ส่วนที่ต้องทำต่อในทางกายภาพ (RF / Hardware)"],
        [
            ["Data Link (AX.25)", "สมบูรณ์ (100%)", "• การเข้า/ถอดรหัส Address, Control, PID<br/>• การคำนวณและตรวจสอบ CRC-16/X-25", "• การกำหนด Mission Payload Schema ภายใน Information field"],
            ["Framing (HDLC)", "สมบูรณ์ (100%)", "• Bit-stuffing, ธง 0x7E, ตรวจจับ Abort sequence<br/>• การจำกัดขนาด Buffer ไม่เกิน 4096 ไบต์", "• การเชื่อมต่อกับชิปโมเด็มฮาร์ดแวร์ (TNC Chipset)"],
            ["Line Coding (NRZI)", "สมบูรณ์ (100%)", "• การแปลงบิต 0/1 สลับสัญญาณ NRZI<br/>• การจำลองการส่งข้อมูลแบบ Chunking ข้ามรอบ", "• การตรวจจับการสลับขั้วสัญญาณบิต (Bit Polarity Inversion)"],
            ["Physical / RF Layer", "ยังไม่เริ่ม (รอ Phase 5+)", "• รับเฉพาะสตรีมบิต 0/1 ที่แปลงสัญญาณมาแล้ว", "• Carrier Recovery, Symbol Timing Sync, Doppler Shift (±3.5 kHz)<br/>• SDR Demodulation (IQ / Audio Samples) และค่า BER/PER"],
        ],
        [130, 100, 260, 290],
        styles,
    )
    story.append(demarc_table)
    story.append(Spacer(1, 10))

    # Phase 5 Plan Cards
    p5_cards = Table([
        [
            make_card(
                "Phase 5.1: KISS TNC Protocol Adapter",
                "สร้างตัวเชื่อมต่อ KISS Protocol (Serial COM Port / TCP Port 8001) เพื่อคุยกับฮาร์ดแวร์ TNC หรือซอฟต์แวร์โมเด็ม Dire Wolf ภายนอก",
                styles, 255, C_CYAN
            ),
            make_card(
                "Phase 5.2: Mission Telemetry Mapping",
                "ออกแบบ Format ข้อมูลภายใน Information Field (Packet Type, Sequence Number, Timestamp, ข้อมูลแรงดันแบตเตอรี่, เซนเซอร์อุณหภูมิ)",
                styles, 255, C_BLUE
            ),
            make_card(
                "Phase 5.3: Ground Control & HIL Test",
                "เชื่อมเข้ากับ Ground Dashboard แสดงผลสด, บันทึก Log ข้อมูล และทดสอบ Hardware-in-the-Loop ผ่าน Soundcard/SDR Loopback จริง",
                styles, 255, C_GREEN
            ),
        ]
    ], colWidths=[260, 260, 260])
    p5_cards.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story.append(p5_cards)

    # =========================================================================
    # SLIDE 8: SUMMARY & DELIVERABLES
    # =========================================================================
    story.append(PageBreak())
    story.extend(create_slide_header(
        "Deliverables & Sign-Off",
        "สรุปภาพรวมและรายการไฟล์ส่งมอบโครงการ (Project Deliverables)",
        "เอกสารทางเทคนิค โค้ดที่ผ่านการรับรอง และแพ็กเกจส่งมอบพร้อมนำไปใช้งาน",
        styles,
    ))

    deliv_table = make_slide_table(
        ["รายการไฟล์ส่งมอบ (Deliverable)", "ที่อยู่ไฟล์ (Path)", "ขนาดไฟล์", "การตรวจสอบความถูกต้อง (Verification)"],
        [
            ["Phase 1 Technical Report", "docs/project/ORBITL1_AX25_Phase1_Technical_Report.pdf", "31 kB (4 หน้า)", "รายงานเจาะลึก Phase 1: Frame Core, Addressing และ CRC-16"],
            ["Phase 2 Technical Report", "docs/project/ORBITL1_AX25_Phase2_Technical_Report.pdf", "30 kB (4 หน้า)", "รายงานเจาะลึก Phase 2: HDLC Framing, Bit Stuffing และ NRZI"],
            ["Phase 3 Technical Report", "docs/project/ORBITL1_AX25_Phase3_Technical_Report.pdf", "30 kB (4 หน้า)", "รายงานเจาะลึก Phase 3: E2E Integration และ Reference Model"],
            ["Phase 4 Technical Report", "docs/project/ORBITL1_AX25_Phase4_Technical_Report.pdf", "31 kB (4 หน้า)", "รายงานเจาะลึก Phase 4: Reliability, Fault Injection และ Benchmark"],
            ["Progress Presentation Paper", "docs/project/ORBITL1_AX25_Progress_Presentation_Paper.pdf", "68 kB (2 หน้า)", "เอกสารสรุปความคืบหน้ารูปแบบ Academic Paper 2 หน้ากระชับ"],
            ["Machine-Readable Test Summary", "docs/project/test_results.json", "33 kB", "บันทึกผลการทดสอบเชิงเครื่อง 95 รายการ พร้อม Benchmark และ Hashes"],
            ["Progress Presentation Slides (ชุดนี้)", "docs/project/ORBITL1_AX25_Progress_Presentation_Slides.pdf", "สร้างสดใหม่", "สไลด์สรุปผลงานระดับผู้บริหารและทีมวิศวกรรม"],
        ],
        [190, 270, 70, 250],
        styles,
    )
    story.append(deliv_table)
    story.append(Spacer(1, 14))

    signoff_box = """
    <b>สรุปผลการส่งมอบ (Acceptance Gate):</b><br/>
    ระบบโปรโตคอล AX.25 สำหรับดาวเทียม ORBITL-1 ในส่วน <b>Phase 1 ถึง Phase 4 ผ่านการทดสอบระดับซอฟต์แวร์เสร็จสมบูรณ์ 100%</b><br/>
    พร้อมส่งมอบโค้ด ชุดทดสอบ และเอกสารรายงานทางวิศวกรรม เพื่อใช้เป็นฐานในการต่อยอดเข้าสู่ Phase 5 (TNC / Ground Station Integration) ต่อไป
    """
    story.append(make_card("การรับรองผลงาน (Software Acceptance Sign-off)", signoff_box, styles, 780, C_GREEN))

    # Build document
    doc.build(story, canvasmaker=SlideCanvas)
    print(f"Generated Presentation Slides PDF: {PDF_PATH} ({os.path.getsize(PDF_PATH)} bytes)")


if __name__ == "__main__":
    build_presentation_slides()
