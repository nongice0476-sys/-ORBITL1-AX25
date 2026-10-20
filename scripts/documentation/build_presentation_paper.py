"""Build clean, monochrome technical paper for ORBITL1-AX25 progress presentation.

Outputs:
  docs/project/ORBITL1_AX25_Progress_Presentation_Paper.pdf
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
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
PDF_PATH = OUT_DIR / "ORBITL1_AX25_Progress_Presentation_Paper.pdf"

# Fonts and Shaping setup
try:
    import uharfbuzz
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

# Clean Monochrome Palette (Academic / Typewritten Printout Style)
C_BLACK = colors.HexColor("#111111")
C_DARK = colors.HexColor("#222222")
C_GRAY_HEADER = colors.HexColor("#EAEAEA")
C_GRAY_ALT = colors.HexColor("#F8F8F8")
C_BORDER = colors.HexColor("#333333")
C_BORDER_LIGHT = colors.HexColor("#B0B0B0")
C_MUTED = colors.HexColor("#555555")


class PlainPaperCanvas(canvas.Canvas):
    """Clean monochrome paper canvas with running header and page numbering."""

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
            self.draw_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_decorations(self, total_pages):
        self.saveState()
        width, height = self._pagesize

        # Running Top Header (Pages 2+)
        if self._pageNumber > 1:
            self.setFont(FONT_REGULAR, 7.5)
            self.setFillColor(C_MUTED)
            self.drawString(36, height - 26, "โครงการดาวเทียม ORBITL-1 - รายงานความคืบหน้า ORBITL-1 AX.25")
            self.drawRightString(width - 36, height - 26, "ผลการทดสอบระดับซอฟต์แวร์ เฟส 1 - 4")
            self.setStrokeColor(C_BORDER_LIGHT)
            self.setLineWidth(0.5)
            self.line(36, height - 29, width - 36, height - 29)

        # Running Bottom Footer
        self.setStrokeColor(C_BORDER_LIGHT)
        self.setLineWidth(0.5)
        self.line(36, 30, width - 36, 30)

        self.setFont(FONT_REGULAR, 7.5)
        self.setFillColor(C_MUTED)
        self.drawString(36, 19, "เอกสารรายงานความคืบหน้าโครงการ ORBITL-1 - ตรวจสอบการทำงานของซอฟต์แวร์ผ่าน 100%")
        page_str = f"หน้า {self._pageNumber} จาก {total_pages}"
        self.drawRightString(width - 36, 19, page_str)

        self.restoreState()


def get_paper_styles():
    styles = {}

    styles["DocTitle"] = ParagraphStyle(
        "DocTitle",
        fontName=FONT_BOLD,
        fontSize=16,
        leading=20,
        textColor=C_BLACK,
        alignment=1,  # Center
        spaceAfter=3,
        shaping=HAS_SHAPING,
    )
    styles["DocSub"] = ParagraphStyle(
        "DocSub",
        fontName=FONT_REGULAR,
        fontSize=9.5,
        leading=13,
        textColor=C_MUTED,
        alignment=1,
        spaceAfter=7,
        shaping=HAS_SHAPING,
    )
    styles["Heading1"] = ParagraphStyle(
        "Heading1",
        fontName=FONT_BOLD,
        fontSize=9.8,
        leading=12.8,
        textColor=C_BLACK,
        spaceBefore=5,
        spaceAfter=2,
        shaping=HAS_SHAPING,
    )
    styles["Heading2"] = ParagraphStyle(
        "Heading2",
        fontName=FONT_BOLD,
        fontSize=8.6,
        leading=11.2,
        textColor=C_BLACK,
        spaceBefore=3.5,
        spaceAfter=1.5,
        shaping=HAS_SHAPING,
    )
    styles["Body"] = ParagraphStyle(
        "Body",
        fontName=FONT_REGULAR,
        fontSize=7.6,
        leading=10.6,
        textColor=C_DARK,
        spaceAfter=2,
        shaping=HAS_SHAPING,
    )
    styles["BodyBold"] = ParagraphStyle(
        "BodyBold",
        fontName=FONT_BOLD,
        fontSize=7.6,
        leading=10.6,
        textColor=C_BLACK,
        spaceAfter=2,
        shaping=HAS_SHAPING,
    )
    styles["TableHead"] = ParagraphStyle(
        "TableHead",
        fontName=FONT_BOLD,
        fontSize=7.2,
        leading=9.0,
        textColor=C_BLACK,
        shaping=HAS_SHAPING,
    )
    styles["TableCell"] = ParagraphStyle(
        "TableCell",
        fontName=FONT_REGULAR,
        fontSize=7.2,
        leading=9.4,
        textColor=C_DARK,
        shaping=HAS_SHAPING,
    )
    styles["TableCellBold"] = ParagraphStyle(
        "TableCellBold",
        fontName=FONT_BOLD,
        fontSize=7.2,
        leading=9.4,
        textColor=C_BLACK,
        shaping=HAS_SHAPING,
    )
    styles["Code"] = ParagraphStyle(
        "Code",
        fontName="Courier",
        fontSize=6.6,
        leading=8.5,
        textColor=C_BLACK,
        shaping=HAS_SHAPING,
    )
    styles["MetaBlock"] = ParagraphStyle(
        "MetaBlock",
        fontName=FONT_REGULAR,
        fontSize=7.4,
        leading=10.5,
        textColor=C_DARK,
        shaping=HAS_SHAPING,
    )
    styles["Note"] = ParagraphStyle(
        "Note",
        fontName=FONT_REGULAR,
        fontSize=7.2,
        leading=9.8,
        textColor=C_BLACK,
        shaping=HAS_SHAPING,
    )
    return styles


def make_plain_table(headers: list[str], rows: list[list], col_widths: list[float], styles, pad_v: float = 1.8) -> Table:
    data = [[Paragraph(f"<b>{h}</b>", styles["TableHead"]) for h in headers]]
    for r in rows:
        row_data = []
        for c in r:
            if isinstance(c, str):
                if c in ("PASS", "ผ่าน", "100%", "MATCH", "VERIFIED", "ตรงกัน", "ผ่านครบ 100%", "ผ่าน (29/29)", "ผ่าน (10/10)", "ผ่าน (7/7)", "ผ่าน (18/18)", "ผ่าน (22/22)", "ผ่าน (9/9)", "ผ่าน 100%"):
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
            ("BACKGROUND", (0, 0), (-1, 0), C_GRAY_HEADER),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, C_GRAY_ALT]),
            ("BOX", (0, 0), (-1, -1), 0.6, C_BORDER),
            ("INNERGRID", (0, 0), (-1, -1), 0.35, C_BORDER_LIGHT),
            ("LINEBELOW", (0, 0), (-1, 0), 0.8, C_BORDER),
            ("TOPPADDING", (0, 0), (-1, -1), pad_v),
            ("BOTTOMPADDING", (0, 0), (-1, -1), pad_v),
            ("LEFTPADDING", (0, 0), (-1, -1), 3.5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 3.5),
        ])
    )
    return t


def make_box(text: str, styles, width: float = 523, pad_v: float = 3.2) -> Table:
    t = Table([[Paragraph(text, styles["Note"])]], colWidths=[width])
    t.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), C_GRAY_ALT),
            ("BOX", (0, 0), (-1, -1), 0.6, C_BORDER),
            ("LINEBEFORE", (0, 0), (0, -1), 2.2, C_BORDER),
            ("TOPPADDING", (0, 0), (-1, -1), pad_v),
            ("BOTTOMPADDING", (0, 0), (-1, -1), pad_v),
            ("LEFTPADDING", (0, 0), (-1, -1), 6.5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6.5),
        ])
    )
    return t


def build_progress_paper():
    # Page setup: A4 with 36pt margins (0.5 inch) -> usable width = 523pt, height = 770pt
    doc = SimpleDocTemplate(
        str(PDF_PATH),
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=32,
        bottomMargin=32,
    )
    styles = get_paper_styles()
    story = []

    # =========================================================================
    # PAGE 1: TITLE, METADATA, WORK ACCOMPLISHED & TESTING
    # =========================================================================
    story.append(Paragraph("รายงานความคืบหน้า ORBITL-1 AX.25", styles["DocTitle"]))
    story.append(Paragraph("สรุปผลการทำงานและผลการทดสอบระบบ (เฟส 1 - 4 ผ่านการทดสอบครบ 100%)", styles["DocSub"]))
    story.append(HRFlowable(width="100%", thickness=0.8, color=C_BORDER, spaceBefore=0, spaceAfter=4))

    meta_table = Table([
        [
            Paragraph("<b>โครงการ:</b> ดาวเทียมวิจัย ORBITL-1 CubeSat<br/><b>ระบบย่อย:</b> ระบบสื่อสารข้อมูล (AX.25 Track)<br/><b>ภาษาที่ใช้:</b> Python 3.14 (Standard Library Only)", styles["MetaBlock"]),
            Paragraph("<b>สถานะปัจจุบัน:</b> ผ่านการทดสอบระดับซอฟต์แวร์ครบ 100%<br/><b>ผลการทดสอบ:</b> 95 / 95 Tests PASS (0 Failures, 0 Errors)", styles["MetaBlock"]),
        ]
    ], colWidths=[260, 263])
    meta_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 1),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(meta_table)
    story.append(HRFlowable(width="100%", thickness=0.4, color=C_BORDER_LIGHT, spaceBefore=2, spaceAfter=4))

    # SECTION 1: WORK ACCOMPLISHED (Engineering Terms in Table)
    story.append(Paragraph("1. สรุปงานที่ทำไปแล้ว (เฟส 1 ถึง เฟส 4)", styles["Heading1"]))
    story.append(Paragraph("การทำงานแบ่งออกเป็น 4 เฟสตามขั้นตอนของระบบสื่อสาร ดังนี้:", styles["Body"]))

    work_table = make_plain_table(
        ["ระยะการพัฒนา (Phase)", "ขอบเขตทางเทคนิค (Technical Scope & Implementation)", "ผลลัพธ์เชิงระบบ (Engineering Deliverables)"],
        [
            ["Phase 1: Frame Core", "- ออกแบบและสร้าง AX.25 UI Frame (Control 0x03, PID 0xF0)<br/>- ตรวจสอบ Address Field, Callsign (1-6 ตัวอักษร) และ SSID (0-15)<br/>- คำนวณและตรวจสอบ CRC-16/X-25 แบบ Low-Byte First", "ได้ Frame Encoder/Decoder พร้อม Guard Validation ตรวจจับรูปแบบข้อมูลผิดพลาดได้ 100%"],
            ["Phase 2: HDLC & NRZI", "- แปลงข้อมูลไบต์เป็น Bitstream แบบ LSB-First<br/>- ระบบ Bit Stuffing (แทรกบิต 0 หลังบิต 1 ต่อเนื่อง 5 ตัว) และ Flag 0x7E<br/>- Line Coding แบบ NRZI (Invert on Zero) สลับระดับสัญญาณ<br/>- HDLC Stream Decoder จำกัด Frame Buffer สูงสุด 4,096 ไบต์", "ได้ Bit-level Framing Pipeline และ Streaming Decoder ที่รักษา State ข้าม Chunk ได้สมบูรณ์"],
            ["Phase 3: E2E Integration", "- เชื่อมต่อ End-to-End Pipeline ครบวงจร (Payload -> Framing -> NRZI -> Decoder)<br/>- รองรับการรับส่งสตรีมแบบผันแปร (Streaming Chunks ขนาด 1 ถึง 128 บิต)<br/>- ตรวจสอบความถูกต้องเทียบกับเวกเตอร์อ้างอิงตามมาตรฐาน<br/>- พัฒนาโมเดลจำลองอิสระ (Pure-Python Reference Model) เทียบชนบิตต่อบิต", "ยืนยันความสอดคล้องตามมาตรฐานระดับบิตต่อบิต (Bit-accurate Interoperability) 100%"],
            ["Phase 4: Reliability & Benchmark", "- วางแนวป้องกัน Fault Injection (ตัดทิ้ง Frame เสีย, Frame Abort, Bit-Flip)<br/>- ตรวจจับและปฏิเสธ Frame ที่ขนาดเกิน 4,078 ไบต์ ป้องกัน Buffer Overflow<br/>- Sustained Workload Benchmark สตรีมต่อเนื่อง 500 เฟรม วัด Throughput และ Memory", "ระบบมีความทนทานสูงต่อสัญญาณรบกวน (High Robustness) พร้อมผลวัดประสิทธิภาพเชิงตัวเลข"],
        ],
        [110, 250, 163],
        styles,
        pad_v=1.6,
    )
    story.append(work_table)
    story.append(Spacer(1, 3))

    flow_text = (
        "<b>ผังกระบวนการส่งและรับข้อมูลครบวงจร (End-to-End Pipeline Data Flow):</b><br/>"
        "- <b>ขาส่ง (TX):</b> ข้อมูลข้อความ -> ประกอบเฟรม AX.25 -> แทรกบิตและใส่ธง HDLC -> แปลงสัญญาณ NRZI -> ลำดับบิตสัญญาณ<br/>"
        "- <b>ขารับ (RX):</b> ลำดับบิตสัญญาณ -> ถอดสัญญาณ NRZI -> แกะเฟรม HDLC -> อ่านข้อมูล AX.25 -> ได้ข้อมูลเดิมกลับมาครบถ้วน"
    )
    story.append(make_box(flow_text, styles, width=523, pad_v=2.8))
    story.append(Spacer(1, 3.5))

    # SECTION 2: TESTING & EVIDENCE (Engineering Terms in Table)
    story.append(Paragraph("2. ผลการทดสอบระบบ (ผ่านครบ 95 รายการ)", styles["Heading1"]))
    story.append(Paragraph(
        "ชุดทดสอบอัตโนมัติถูกจัดแบ่งตามหน้าที่อย่างชัดเจน รวมทั้งหมด <b>95 การทดสอบ</b> "
        "ครอบคลุมทั้งการทำงานปกติ สภาวะขอบเขตข้อมูล และการจำลองข้อมูลผิดปกติ (Fault Injection):",
        styles["Body"],
    ))

    test_table = make_plain_table(
        ["ชุดทดสอบ (Test Suite)", "จำนวน", "หมวดหมู่การทดสอบ", "กรณีทดสอบและสภาวะการทำงาน (Test Cases & Conditions)", "ผลการทดสอบ"],
        [
            ["test_ax25_core.py", "29", "Frame & Address Core", "- Address Round-trip, Callsign Case Invariance, SSID Boundary (0-15)<br/>- CRC-16 Standard Vector Verification (Input 123456789 -> 0x906E)<br/>- ปฏิเสธ Unsupported Control/PID Field แม้ค่า FCS ถูกต้อง", "ผ่าน (29/29)"],
            ["test_hdlc.py", "10", "HDLC & Bit Framing", "- Bit Stuffing / Unstuffing ความแม่นยำ 100% ป้องกัน False Flag<br/>- NRZI Encode/Decode State Machine Transition ตรงตามตารางเวกเตอร์", "ผ่าน (10/10)"],
            ["test_receiver.py", "7", "Receive Pipeline", "- Demodulator Handoff Interface ทดสอบป้อนบิต NRZI ทีละ 7 บิตต่อเนื่อง<br/>- Back-to-Back Frames Recovery ถอดรหัส 2 เฟรมติดกันโดยไม่เสียสถานะ", "ผ่าน (7/7)"],
            ["test_reliability.py", "18", "Robustness & Recovery", "- Automatic Resynchronization กู้คืนสถานะเมื่อ Flag ขาดหายหรือมี Noise แทรก<br/>- Randomized Round-trip Stress Test 1,000 รอบต่อเนื่อง (Zero Data Loss)", "ผ่าน (18/18)"],
            ["test_integration.py", "22", "E2E & Fault Injection", "- High-Density Ones Stress (0xFF*50, 0x7E*25) ไม่เกิด False Delimiter<br/>- Prime-sized Streaming Chunks (1, 2, 3, 5, 7, 11, 13, 17, 31 บิต)<br/>- FCS Single/Double Bit-Flip Injection พิสูจน์ว่า Drop เฟรมเสีย 100%", "ผ่าน (22/22)"],
            ["test_acceptance.py", "9", "Acceptance & Benchmark", "- Multi-seed Deterministic Testing (Seeds: 20261009, 20261019, 42, 1337)<br/>- Payload Boundary Gate: 4,078 ไบต์ (ผ่าน) / 4,079 ไบต์ (Drop ทันที)<br/>- Continuous Stream 100 เฟรมที่มี Abort Sequence และ Corrupted Frames ปนเปื้อน", "ผ่าน (9/9)"],
            ["รวมทุกชุดทดสอบ", "95", "Cumulative Suite", "ครอบคลุมการทำงานทุกสภาวะ รันผ่าน 100% (0 Failures, 0 Errors) ใน ~5.8 วินาที", "ผ่านครบ 100%"],
        ],
        [105, 34, 110, 214, 60],
        styles,
        pad_v=1.4,
    )
    story.append(test_table)

    # =========================================================================
    # PAGE 2: STANDARDS INTEROPERABILITY, BENCHMARKS & DEMARCATION
    # =========================================================================
    story.append(PageBreak())

    # SECTION 3: STANDARDS INTEROPERABILITY & CITATIONS
    story.append(Paragraph("3. การอ้างอิงมาตรฐานและการทดสอบความถูกต้อง", styles["Heading1"]))
    story.append(Paragraph(
        "ระบบสื่อสาร ORBITL-1 AX.25 ได้รับการพัฒนาและตรวจสอบตามข้อกำหนดมาตรฐาน 3 ฉบับหลัก "
        "เพื่อให้มั่นใจว่าซอฟต์แวร์สอดคล้องตามมาตรฐานระดับบิตต่อบิต (Bit-accurate Interoperability):",
        styles["Body"],
    ))

    interop_table = make_plain_table(
        ["เกณฑ์อ้างอิง (Reference)", "เวกเตอร์ทดสอบ (Input Vector)", "ค่าตามข้อกำหนด (Expected)", "ค่าที่ระบบคำนวณได้ (Actual)", "สถานะ (Status)"],
        [
            ["ตามมาตรฐาน (ISO/IEC 3309)", "CRC-16 ASCII Vector: '123456789'", "CRC-16 = 0x906E", "0x906E (ถูกต้องตามสเปก)", "ตรงกัน"],
            ["ตามมาตรฐาน (ISO/IEC 3309)", "CRC-16 FCS Residue Verification", "Residual Constant = 0xF0B8", "0xF0B8 (Residue Verified)", "ตรงกัน"],
            ["ตามมาตรฐาน AX.25 (TAPR v2.2)", "Destination 'NJ7P', SSID 0 (Bit 0=0)", "9C 94 6E A0 40 40 60", "9C 94 6E A0 40 40 60", "ตรงกัน"],
            ["ตามมาตรฐาน AX.25 (TAPR v2.2)", "Source 'N7LEM', SSID 0 (Bit 0=1)", "9C 6E 98 8A 9A 40 61", "9C 6E 98 8A 9A 40 61", "ตรงกัน"],
            ["ตามมาตรฐาน AX.25 (TAPR v2.2)", "LSB-First Order, UI Control 0x03, PID 0xF0", "Control=0x03, PID=0xF0", "โครงสร้าง UI Frame ถูกต้อง", "ตรงกัน"],
            ["ตามมาตรฐาน HDLC (ITU-T V.42)", "HDLC Delimiter Flag 0x7E & Bit Stuffing", "Flag 0x7E, Insert 0 after 5x '1'", "แทรกและถอดบิตตรงตามสเปก", "ตรงกัน"],
            ["ตามมาตรฐาน (Reference Model)", "NRZI Line Coding & E2E Stream Pipeline", "ตรงกันบิตต่อบิต (Bit-accurate)", "สอดคล้องตรงกันทุกตำแหน่ง 100%", "ตรงกัน"],
        ],
        [135, 137, 112, 99, 40],
        styles,
        pad_v=1.5,
    )
    story.append(interop_table)
    story.append(Spacer(1, 3))

    std_text = (
        "<b>รายการมาตรฐานที่ใช้เป็นเกณฑ์อ้างอิงและตรวจสอบในระบบ (Normative Standards Citations):</b><br/>"
        "1. <b>TAPR / ARRL AX.25 Version 2.2 (July 1998):</b> กำหนดโครงสร้างเฟรม UI, Address Shifting (Sec 3.12), LSB-First (Sec 2.2.3) และ Control 0x03, PID 0xF0<br/>"
        "2. <b>ISO/IEC 3309:1993 / ITU-T Recommendation X.25:</b> กำหนดการคำนวณ FCS CRC-16 (พหุนาม x^16 + x^12 + x^5 + 1) และค่าตรวจคงเหลือ 0xF0B8<br/>"
        "3. <b>ITU-T Recommendation V.42 / ISO 7776:</b> กำหนด HDLC Framing (Flag 0x7E, Bit Stuffing หลังบิต 1 ห้าตัว) และ Line Coding แบบ NRZI (Invert on Zero)"
    )
    story.append(make_box(std_text, styles, width=523, pad_v=2.4))
    story.append(Spacer(1, 3.5))

    # SECTION 4: PERFORMANCE BENCHMARK (Engineering Terms in Table)
    story.append(Paragraph("4. ผลการวัดความเร็วและประสิทธิภาพการทำงาน", styles["Heading1"]))
    story.append(Paragraph(
        "ทำการทดสอบภาระงานต่อเนื่อง (Sustained Workload Benchmark) โดยสตรีมเฟรม AX.25 จำนวน <b>500 เฟรม</b> "
        "(ขนาดข้อมูลรวม 74,000 ไบต์ หรือ 592,000 บิต) ผ่านระบบแปลงสัญญาณและถอดรหัสเต็มรูปแบบ:",
        styles["Body"],
    ))

    bench_table = make_plain_table(
        ["ดัชนีชี้วัดประสิทธิภาพ (Metric)", "ผลการวัดจริง (Measured Value)", "เปรียบเทียบกับวิทยุดาวเทียม (Satellite RF Baseline)", "ความหมายทางวิศวกรรม (Engineering Implication)"],
        [
            ["Workload Dataset", "500 เฟรม (Payload 128 ไบต์/เฟรม, รวม 74 kB)", "เทียบเท่าข้อมูล Telemetry ดาวเทียม ~10 นาที", "รองรับปริมาณข้อมูลครบถ้วนตลอดช่วงการติดต่อ (Ground Pass)"],
            ["Execution Time", "0.579 วินาที (เฉลี่ย ~1.15 ms ต่อเฟรม)", "อัตราส่งวิทยุปกติ: 1 เฟรม ทุก 1 - 10 วินาที", "ประมวลผลแบบ Real-time มี Latency ต่ำ ไม่เกิด Buffer Queue สะสม"],
            ["Frame Processing Rate", "864.0 เฟรม/วินาที", "อัตราส่งวิทยุจริง: 0.1 - 2 เฟรม/วินาที", "อัตราการประมวลผลซอฟต์แวร์เร็วกว่าอัตราส่งวิทยุจริง >400 เท่า"],
            ["Effective Throughput", "1,022.98 kbps (~1.02 Mbps)", "วิทยุ CubeSat: 1.2 kbps (AFSK) / 9.6 kbps (GFSK)", "ขีดความสามารถซอฟต์แวร์มี Headroom สูงกว่าอัตราส่งวิทยุจริง >100 เท่า"],
            ["Memory Stability", "Heap คงที่สมบูรณ์ (Zero Leak Profile)", "รันสตรีมต่อเนื่องหลายพันรอบ ไม่พบ Memory บวม", "เสถียรภาพสูง ปลอดภัยต่อการรันเป็น Background Service บนสถานีภาคพื้น"],
        ],
        [122, 133, 135, 133],
        styles,
        pad_v=1.6,
    )
    story.append(bench_table)
    story.append(Spacer(1, 4))

    # SECTION 5: DEMARCATION & NEXT STEPS (Engineering Terms in Table)
    story.append(Paragraph("5. ขอบเขตการทำงาน (ซอฟต์แวร์ vs วิทยุจริง)", styles["Heading1"]))
    story.append(Paragraph(
        "เพื่อความชัดเจนในการทำงาน ขอยืนยันขอบเขตส่วนที่ซอฟต์แวร์ทำเสร็จแล้ว "
        "กับส่วนที่ต้องทำต่อกับวิทยุจริงในเฟสถัดไป ดังนี้:",
        styles["Body"],
    ))

    demarc_table = make_plain_table(
        ["ระดับชั้นสถาปัตยกรรม (Layer)", "สถานะ (Status)", "ขอบเขตที่ซอฟต์แวร์ดำเนินการแล้ว (Software-Verified)", "ขอบเขตที่ต้องเชื่อมต่อฮาร์ดแวร์ RF (Physical Hardware Target)"],
        [
            ["Data Link Layer (AX.25)", "ผ่าน 100%", "- สร้างและถอดรหัส Frame, ตรวจสอบ Address/SSID<br/>- คำนวณและตรวจสอบ CRC-16 Checksum", "- ออกแบบ Mission Telemetry Payload Schema ใน Information Field"],
            ["Framing Layer (HDLC)", "ผ่าน 100%", "- Bit Stuffing/Unstuffing, กำกับ Flag 0x7E, Abort Handling<br/>- Frame Buffer Guard ป้องกัน Overflow ไม่เกิน 4,096 ไบต์", "- เชื่อมต่อ Interface เข้ากับชิปโมเด็มหรือกล่อง TNC Hardware"],
            ["Line Coding (NRZI)", "ผ่าน 100%", "- Line Encoding/Decoding แปลงบิต 0/1 ตาม Transition Rule<br/>- Streaming Interface รองรับการป้อนข้อมูลแบบ Chunked Levels", "- ตรวจสอบและชดเชยการกลับขั้วสัญญาณบิต (Bit Polarity Inversion)"],
            ["Physical / RF Layer", "แผนงานเฟส 5", "- รับสัญญาณบิตที่ผ่านการ Demodulate ในระดับ Baseband แล้ว", "- Carrier Recovery, Symbol Timing Sync, Doppler Compensation (+/- 3.5 kHz)<br/>- SDR Demodulation (IQ/Audio) และการวัดค่า BER/PER"],
        ],
        [110, 58, 175, 180],
        styles,
        pad_v=1.6,
    )
    story.append(demarc_table)
    story.append(Spacer(1, 3))

    phase5_plan = (
        "<b>แผนงานขั้นต่อไปในเฟส 5 (เชื่อมต่อวิทยุและสถานีภาคพื้น):</b><br/>"
        "1. <b>ทำตัวเชื่อมต่อ KISS Protocol:</b> เพื่อให้คุยกับวิทยุ TNC จริงหรือโปรแกรม Dire Wolf ผ่านพอร์ต Serial หรือ TCP ได้ "
        "2. <b>กำหนดรูปแบบข้อมูลดาวเทียม:</b> จัดวางตำแหน่งข้อมูลสถานะแบตเตอรี่ อุณหภูมิ และเซนเซอร์ต่างๆ ในตัวข้อมูล<br/>"
        "3. <b>เชื่อมต่อหน้าจอควบคุมภาคพื้น:</b> แสดงผลแบบเรียลไทม์ และบันทึกลงฐานข้อมูล "
        "4. <b>ทดสอบกับอุปกรณ์จริง (Hardware-in-the-Loop):</b> เชื่อมต่อผ่านการ์ดเสียงและวิทยุ SDR จำลองการส่งสัญญาณจริง"
    )
    story.append(make_box(phase5_plan, styles, width=523, pad_v=2.5))

    doc.build(story, canvasmaker=PlainPaperCanvas)
    print(f"Generated Plain Presentation Paper PDF: {PDF_PATH} ({os.path.getsize(PDF_PATH)} bytes)")


if __name__ == "__main__":
    build_progress_paper()
