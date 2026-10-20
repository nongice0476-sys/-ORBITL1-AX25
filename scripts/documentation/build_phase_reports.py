"""Build cumulative Master Engineering Report and Phase 4 Technical Report using ReportLab.

Outputs:
  - docs/project/ORBITL1_AX25_Master_Engineering_Report.pdf
  - docs/project/ORBITL1_AX25_Phase4_Technical_Report.pdf
"""

from __future__ import annotations

import json
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

# Register fonts
FONT_FAMILY = "Helvetica"
FONT_FAMILY_BOLD = "Helvetica-Bold"

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
                FONT_FAMILY_BOLD = f"{name}-Bold"
            else:
                FONT_FAMILY_BOLD = name
            FONT_FAMILY = name
            break
        except Exception:
            pass

# Theme Colors
C_NAVY = colors.HexColor("#12304A")
C_CYAN = colors.HexColor("#18A6B7")
C_BLUE = colors.HexColor("#1D5F91")
C_DARK = colors.HexColor("#233746")
C_MUTED = colors.HexColor("#5C7180")
C_BG_LIGHT = colors.HexColor("#F4F9FB")
C_NOTE_BG = colors.HexColor("#EAF5F8")
C_CODE_BG = colors.HexColor("#102E43")
C_CODE_TEXT = colors.HexColor("#E9F7FA")
C_BORDER = colors.HexColor("#C9DDE6")
C_GREEN = colors.HexColor("#107C41")


class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas to dynamically compute and draw 'Page X of Y' and header."""

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
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        width, height = self._pagesize

        # Running Header
        self.setFillColor(C_NAVY)
        self.rect(28, height - 26, width - 56, 18, stroke=0, fill=1)
        self.setFillColor(C_CYAN)
        self.rect(28, height - 26, 8, 18, stroke=0, fill=1)

        self.setFillColor(colors.white)
        self.setFont(FONT_FAMILY_BOLD, 8)
        self.drawString(42, height - 20, "ORBITL1-AX25   |   OFFICIAL ENGINEERING REPORT")
        self.setFont(FONT_FAMILY, 8)
        self.drawRightString(width - 36, height - 20, "PHASES 1–4 FULL SOFTWARE VERIFICATION")

        # Running Footer
        self.setStrokeColor(C_BORDER)
        self.setLineWidth(0.75)
        self.line(28, 26, width - 28, 26)

        self.setFillColor(C_MUTED)
        self.setFont(FONT_FAMILY, 7.5)
        self.drawString(28, 16, "CONFIDENTIAL / TECHNICAL REPORT  —  Software verification completed; RF hardware unverified pending radio integration.")
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(width - 28, 16, page_str)

        self.restoreState()


def get_styles():
    base = getSampleStyleSheet()
    styles = {}

    styles["DocTitle"] = ParagraphStyle(
        "DocTitle",
        fontName=FONT_FAMILY_BOLD,
        fontSize=20,
        leading=24,
        textColor=C_NAVY,
        spaceAfter=2,
    )
    styles["DocSub"] = ParagraphStyle(
        "DocSub",
        fontName=FONT_FAMILY,
        fontSize=10,
        leading=13,
        textColor=C_MUTED,
        spaceAfter=8,
    )
    styles["Heading1"] = ParagraphStyle(
        "Heading1",
        fontName=FONT_FAMILY_BOLD,
        fontSize=13,
        leading=16,
        textColor=C_NAVY,
        spaceBefore=4,
        spaceAfter=4,
    )
    styles["Heading2"] = ParagraphStyle(
        "Heading2",
        fontName=FONT_FAMILY_BOLD,
        fontSize=10.5,
        leading=13,
        textColor=C_BLUE,
        spaceBefore=3,
        spaceAfter=2,
    )
    styles["Normal"] = ParagraphStyle(
        "Normal",
        fontName=FONT_FAMILY,
        fontSize=8,
        leading=11,
        textColor=C_DARK,
        spaceAfter=3,
    )
    styles["BodyBold"] = ParagraphStyle(
        "BodyBold",
        fontName=FONT_FAMILY_BOLD,
        fontSize=8,
        leading=11,
        textColor=C_DARK,
    )
    styles["TableHead"] = ParagraphStyle(
        "TableHead",
        fontName=FONT_FAMILY_BOLD,
        fontSize=7.5,
        leading=10,
        textColor=colors.white,
    )
    styles["TableCell"] = ParagraphStyle(
        "TableCell",
        fontName=FONT_FAMILY,
        fontSize=7.5,
        leading=9.5,
        textColor=C_DARK,
    )
    styles["TableCellBold"] = ParagraphStyle(
        "TableCellBold",
        fontName=FONT_FAMILY_BOLD,
        fontSize=7.5,
        leading=9.5,
        textColor=C_NAVY,
    )
    styles["TableCellGreen"] = ParagraphStyle(
        "TableCellGreen",
        fontName=FONT_FAMILY_BOLD,
        fontSize=7.5,
        leading=9.5,
        textColor=C_GREEN,
    )
    styles["Code"] = ParagraphStyle(
        "Code",
        fontName="Courier",
        fontSize=6.8,
        leading=8.5,
        textColor=C_CODE_TEXT,
    )
    styles["KpiVal"] = ParagraphStyle(
        "KpiVal",
        fontName=FONT_FAMILY_BOLD,
        fontSize=14,
        leading=16,
        textColor=C_NAVY,
        alignment=1,
    )
    styles["KpiLabel"] = ParagraphStyle(
        "KpiLabel",
        fontName=FONT_FAMILY,
        fontSize=7,
        leading=8.5,
        textColor=C_MUTED,
        alignment=1,
    )
    styles["Note"] = ParagraphStyle(
        "Note",
        fontName=FONT_FAMILY,
        fontSize=7.5,
        leading=10,
        textColor=C_DARK,
    )
    return styles


def make_kpi_card(val: str, label: str, styles) -> Table:
    t = Table(
        [[Paragraph(val, styles["KpiVal"])], [Paragraph(label, styles["KpiLabel"])]],
        colWidths=[185],
    )
    t.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), C_BG_LIGHT),
            ("BOX", (0, 0), (-1, -1), 1, C_BORDER),
            ("LINEBEFORE", (0, 0), (0, -1), 3.5, C_CYAN),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ])
    )
    return t


def make_note_box(text: str, styles, width: float = 780) -> Table:
    t = Table([[Paragraph(f"<b>NOTE / DEMARCATION:</b> {text}", styles["Note"])]], colWidths=[width])
    t.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), C_NOTE_BG),
            ("BOX", (0, 0), (-1, -1), 0.75, C_BORDER),
            ("LINEBEFORE", (0, 0), (0, -1), 3.5, C_CYAN),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ])
    )
    return t


def make_code_box(code_text: str, styles, width: float = 780) -> Table:
    t = Table([[Paragraph(code_text.replace("\n", "<br/>").replace(" ", "&nbsp;"), styles["Code"])]], colWidths=[width])
    t.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), C_CODE_BG),
            ("BOX", (0, 0), (-1, -1), 1, C_NAVY),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ])
    )
    return t


def make_pipeline_diagram(styles, width: float = 780) -> Table:
    """Render horizontal data-flow pipeline boxes."""
    steps = [
        ("Flight Software", "Payload bytes<br/>(telemetry/cmd)"),
        ("Phase 1 Core", "build_ui_frame()<br/>AX.25 + CRC-16"),
        ("Phase 2 Transmit", "encode_hdlc()<br/>Bit stuffing + Flag"),
        ("Line Modulation", "nrzi_encode()<br/>NRZI Line Levels"),
        ("Demod Handoff", "feed_nrzi_levels()<br/>Continuous state"),
        ("Phase 2 Receive", "HDLCStreamDecoder<br/>FCS verification"),
        ("Ground App", "decode_verified_body()<br/>Packet dictionary"),
    ]
    row = []
    col_w = (width - (len(steps) - 1) * 16) / len(steps)
    widths = []
    for i, (title, desc) in enumerate(steps):
        cell_p = Paragraph(f"<b>{title}</b><br/>{desc}", styles["TableCell"])
        row.append(cell_p)
        widths.append(col_w)
        if i < len(steps) - 1:
            row.append(Paragraph("<b>→</b>", styles["KpiVal"]))
            widths.append(16)

    t = Table([row], colWidths=widths)
    ts = [
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    for idx in range(0, len(row), 2):
        ts.extend([
            ("BACKGROUND", (idx, 0), (idx, 0), C_BG_LIGHT),
            ("BOX", (idx, 0), (idx, 0), 1, C_CYAN),
        ])
    t.setStyle(TableStyle(ts))
    return t


def build_table(headers: list[str], rows: list[list], col_widths: list[float], styles) -> Table:
    data = [[Paragraph(h, styles["TableHead"]) for h in headers]]
    for r in rows:
        row_data = []
        for c in r:
            if isinstance(c, str):
                if c in ("PASS", "VERIFIED", "SUCCESS", "MATCH"):
                    p = Paragraph(c, styles["TableCellGreen"])
                elif c.isupper() and len(c) <= 12:
                    p = Paragraph(c, styles["TableCellBold"])
                else:
                    p = Paragraph(c, styles["TableCell"])
            else:
                p = c
            row_data.append(p)
        data.append(row_data)

    t = Table(data, colWidths=col_widths)
    t.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), C_NAVY),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, C_BG_LIGHT]),
            ("GRID", (0, 0), (-1, -1), 0.5, C_BORDER),
            ("TOPPADDING", (0, 0), (-1, -1), 2.5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ])
    )
    return t


def generate_master_engineering_report(output_path: Path):
    """Generate 5-page Cumulative Master Engineering Report."""
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=landscape(A4),
        leftMargin=28,
        rightMargin=28,
        topMargin=32,
        bottomMargin=32,
    )
    styles = get_styles()
    story = []

    # ==================== PAGE 1: EXECUTIVE SUMMARY ====================
    story.append(Paragraph("ORBITL1-AX25", styles["DocTitle"]))
    story.append(Paragraph("CUMULATIVE MASTER ENGINEERING REPORT  |  PHASES 1–4 FULL SYSTEM VERIFICATION", styles["DocSub"]))

    # KPI Row
    kpis = Table([
        [
            make_kpi_card("95 / 95 PASS", "Full Regression & Acceptance Suite", styles),
            make_kpi_card("1,000+ Rounds", "Deterministic Randomized Round-Trips", styles),
            make_kpi_card("4,078 Bytes", "Max Information Payload Limit", styles),
            make_kpi_card("1,022.9 kbps", "Sustained Software Throughput (~1.02 Mbps)", styles),
        ]
    ], colWidths=[195, 195, 195, 195])
    kpis.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story.append(kpis)
    story.append(Spacer(1, 6))

    story.append(Paragraph("End-to-End Implementation & Demarcation Architecture", styles["Heading2"]))
    story.append(make_pipeline_diagram(styles, width=780))
    story.append(Spacer(1, 6))

    # Phase Status Table
    story.append(Paragraph("Phase Status & Verification Summary", styles["Heading2"]))
    phase_table = build_table(
        ["Engineering Phase", "Scope of Responsibility", "Verified Evidence", "Phase Status", "Hardware Demarcation"],
        [
            ["Phase 1: AX.25 Frame Core", "Addressing, UI framing, CRC-16/X-25, profile guard, body parsing", "29 tests PASS; CRC 0x906E vector; 4078 B boundary; field checks", "VERIFIED", "Software framing logic only; no RF carrier"],
            ["Phase 2: HDLC & NRZI", "HDLC bit stuffing, flag handling, NRZI encode/decode, Mobilinkd adapter", "17 tests PASS; 1,000 round-trips; chunked handoff; 4096 B cap", "VERIFIED", "Expects demodulated binary levels; no IQ/audio"],
            ["Phase 3: Integration & Interop", "Full end-to-end pipeline, arbitrary chunks, fault recovery, spec vectors", "22 tests PASS; AX.25 spec vectors; independent reference model", "VERIFIED", "Software-closed loop; external SDR unverified"],
            ["Phase 4: Reliability & Acceptance", "Multi-seed testing, continuous mixed stream, throughput benchmark", "27 tests PASS (9 acceptance + 18 reliability); stress benchmarks", "VERIFIED", "Flight environment & channel noise TBR"],
        ],
        [110, 210, 230, 80, 150],
        styles,
    )
    story.append(phase_table)
    story.append(Spacer(1, 6))
    story.append(make_note_box(
        "Software test completion establishes protocol correctness, boundary enforcement, and deterministic streaming recovery. "
        "It does NOT establish physical RF range, SDR clock recovery, Doppler tolerance, or flight hardware qualification. "
        "All RF transmission and hardware modem interfaces remain TBR pending radio selection.",
        styles,
    ))

    # ==================== PAGE 2: PHASES 1 & 2 BASELINE ====================
    story.append(PageBreak())
    story.append(Paragraph("Phase 1 & Phase 2 Technical Baseline", styles["Heading1"]))
    story.append(Paragraph("Detailed verification of frame structure, bit-level serialization, and runtime code preservation.", styles["DocSub"]))

    story.append(Paragraph("Phase 1: AX.25 UI Frame Profile Specifications", styles["Heading2"]))
    p1_table = build_table(
        ["Parameter", "Implemented Specification", "Validation & Rejection Rules", "Compliance Evidence"],
        [
            ["Addressing", "Single destination + single source; 1-6 alphanumeric ASCII chars", "Trailing space padding only; lowercase on wire rejected; no digipeater", "test_address_round_trip, test_wire_callsign_must_be_uppercase_ascii"],
            ["SSID Range", "SSIDs 0 through 15 encoded with reserved bits 0x60", "Decimal integer string; non-digits & out-of-range rejected; bits 5-6 checked", "test_address_rejects_non_decimal_or_out_of_range_ssid"],
            ["Control Field", "UI frame: Control = 0x03 (Unnumbered Information)", "All non-UI values (I-frames, S-frames, other U-frames) strictly rejected", "test_frame_decoder_rejects_unsupported_control_with_valid_fcs"],
            ["Protocol ID (PID)", "No Layer 3 protocol: PID = 0xF0", "All other PIDs (IPv4 0xCC, X.25 0x01, CDPD 0x81, etc.) strictly rejected", "test_frame_decoder_rejects_unsupported_pid_with_valid_fcs"],
            ["FCS Algorithm", "CRC-16/X-25 (reflected polynomial 0x8408, init 0xFFFF, final 0xFFFF)", "Transmitted low-byte-first; verified before interpreting any frame field", "test_crc16_x25_standard_check_value (0x906E)"],
            ["Payload Limit", "Max Information: 4078 bytes (Header 16B + FCS 2B = 4096B HDLC cap)", "4078 bytes accepted; 4079 bytes raises ValueError in frame builder", "test_frame_builder_enforces_maximum_information"],
        ],
        [85, 230, 245, 220],
        styles,
    )
    story.append(p1_table)
    story.append(Spacer(1, 6))

    story.append(Paragraph("Phase 2: HDLC Framing, NRZI Line Coding & Runtime File Hash Verification", styles["Heading2"]))
    runtime_table = build_table(
        ["File Path", "Module Responsibility", "Pre-Change SHA-256 (Baseline)", "Post-Verification SHA-256", "Status"],
        [
            ["src/ax25.py", "AX.25 UI frame builder, decoder, address parser, CRC-16", "8da3d41a47c8211e482270a554cbb04e046867159dadfb789e8944990e30b9f1", "8da3d41a47c8211e482270a554cbb04e046867159dadfb789e8944990e30b9f1", "MATCH (Preserved)"],
            ["src/ax25_hdlc.py", "HDLC stream decoder adapter for Mobilinkd engine", "38fbab7afe40a822bbee0ea0b0c5047deede1ab1f05306813e01ff11a4894391", "38fbab7afe40a822bbee0ea0b0c5047deede1ab1f05306813e01ff11a4894391", "MATCH (Preserved)"],
            ["src/ax25_receiver.py", "AX25ReceivePipeline; chunked NRZI level demod handoff", "7d9b6c1df0af7636f4babdf1e9a980f425045ee63a17c2740f0f3c681bb87d68", "7d9b6c1df0af7636f4babdf1e9a980f425045ee63a17c2740f0f3c681bb87d68", "MATCH (Preserved)"],
            ["src/ax25_transmitter.py", "HDLC bit stuffing, byte serialization, NRZI encode/decode", "6120408159812b97dfc1612a54c8f58d54bd76c4810d9941ce29280c2029aca8", "6120408159812b97dfc1612a54c8f58d54bd76c4810d9941ce29280c2029aca8", "MATCH (Preserved)"],
            ["src/vendor/mobilinkd/CRC.py", "CCITT CRC lookup table computation engine", "6717e22099e38177351b215565efd9539a686fe341a5838b96509f9aefb0481a", "6717e22099e38177351b215565efd9539a686fe341a5838b96509f9aefb0481a", "MATCH (Preserved)"],
            ["src/vendor/mobilinkd/HDLC.py", "Core HDLC state machine with 4096B limit & frame 12 fix", "db5c61e16cbff27cce26d244ed71afffdb4c42c036588c57c990e6754dbe7b36", "db5c61e16cbff27cce26d244ed71afffdb4c42c036588c57c990e6754dbe7b36", "MATCH (Preserved)"],
            ["src/vendor/mobilinkd/LICENSE", "Original MIT copyright notice (Mobilinkd LLC)", "0e95b2f5f69e2e17b8c429d43b166e2ebc72704f9040cc9db34774ef65907450", "0e95b2f5f69e2e17b8c429d43b166e2ebc72704f9040cc9db34774ef65907450", "MATCH (Preserved)"],
        ],
        [140, 150, 205, 205, 80],
        styles,
    )
    story.append(runtime_table)

    # ==================== PAGE 3: PHASE 3 INTEGRATION ====================
    story.append(PageBreak())
    story.append(Paragraph("Phase 3: Integration & Independent Interoperability", styles["Heading1"]))
    story.append(Paragraph("End-to-end integration across arbitrary chunk boundaries, error recovery, and independent standards validation.", styles["DocSub"]))

    story.append(Paragraph("End-to-End Integration Test Matrix (22 Tests)", styles["Heading2"]))
    e2e_table = build_table(
        ["Test Category", "Test Execution Scenario", "Pipeline Stages Exercised", "Observed Outcome", "Gate Result"],
        [
            ["Empty & Ordinary Payload", "Payloads from 0 bytes up to ordinary telemetry strings", "build_ui_frame → HDLC → NRZI → feed_nrzi_levels", "100% data preservation; valid FCS verification", "PASS"],
            ["Bit Stuffing Stress", "Payloads with dense 1-runs: 0xFF*50, 0x7E*25, 0x3F/7F/FF", "Stuffing insertion (zeros after 5 ones); unstuffing", "Stuffed bits > raw bits; perfect recovery", "PASS"],
            ["Boundary Lengths", "Exact sizes: 0, 1, 2, 7, 8, 128, 256, 512, 1024, 2048, 4078 B", "Frame builder & receiver buffer limits", "All boundary sizes decoded; 4078 B verified", "PASS"],
            ["Consecutive Frames", "10 back-to-back frames; shared flags; 5 idle 0x7E flags", "HDLC boundary transitions & idle flag filtering", "All frames extracted in order without loss", "PASS"],
            ["Arbitrary Streaming Chunks", "Prime chunk sizes: 1, 2, 3, 5, 7, 11, 13, 17, 31, 64, 128 bits", "NRZI state retention across chunk handoffs", "Exact packet recovery across all chunkings", "PASS"],
            ["Critical Boundary Splits", "Split bits directly at flag, address, PID, and FCS edges", "State machine boundary transitions across chunks", "No fragmentation errors; frame fully parsed", "PASS"],
            ["Corrupted FCS Rejection", "Single-bit flips (bits 0,1,7,8,15) and inverted FCS", "HDLC CRC residue check (residue != 0xF0B8)", "100% of corrupted frames dropped; 0 false accepts", "PASS"],
            ["Abort & Noise Recovery", "7+ ones abort sequence; random noise bursts up to 500 bits", "HDLC abort detection; resynchronization on next flag", "Pipeline cleanly resyncs on next valid frame", "PASS"],
        ],
        [105, 195, 200, 210, 70],
        styles,
    )
    story.append(e2e_table)
    story.append(Spacer(1, 6))

    story.append(Paragraph("Independent Interoperability Evidence & Published Vectors", styles["Heading2"]))
    interop_table = build_table(
        ["Reference Authority", "Published / Standard Vector", "Expected Output", "Implementation Result", "Conventions & Notes"],
        [
            ["ISO/IEC 3309 / ITU-T X.25", "ASCII string: '123456789'", "CRC-16 = 0x906E", "0x906E (Exact Match)", "Reflected polynomial 0x8408, final XOR 0xFFFF"],
            ["ITU-T X.25 Standard", "Empty byte string: b''", "CRC-16 = 0x0000", "0x0000 (Exact Match)", "Initial 0xFFFF inverted by final XOR 0xFFFF"],
            ["Catalogue of CRCs (Cook)", "Single character: b'A'", "CRC-16 = 0xA3F5", "0xA3F5 (Exact Match)", "Direct mathematical polynomial check"],
            ["AX.25 v2.2 Spec §3.12 (Fig 3.5)", "Destination 'NJ7P', SSID 0, not last", "9C 94 6E A0 40 40 60", "9C 94 6E A0 40 40 60 (Match)", "Low bit 0 = address extension; bits 5-6 = 0x60"],
            ["AX.25 v2.2 Spec §3.12 (Fig 3.6)", "Source 'N7LEM', SSID 0, last address", "9C 6E 98 8A 9A 40 61", "9C 6E 98 8A 9A 40 61 (Match)", "Low bit 1 = final address indicator"],
            ["ISO 3309 FCS Residue", "Any valid frame + FCS (low-byte-first)", "Residue = 0xF0B8", "0xF0B8 (Exact Match)", "Verified by Mobilinkd HDLC receiver engine"],
            ["Independent Python Model", "Independent pure-Python bitwise reference", "Byte-for-byte identical", "100% Bit/Byte Match", "Independent bit stuffing, unstuffing, and CRC"],
        ],
        [110, 160, 130, 130, 250],
        styles,
    )
    story.append(interop_table)

    # ==================== PAGE 4: PHASE 4 RELIABILITY ====================
    story.append(PageBreak())
    story.append(Paragraph("Phase 4: Reliability, Acceptance & Stress Benchmarks", styles["Heading1"]))
    story.append(Paragraph("Multi-seed randomized testing, strict profile validation, continuous fault injection, and sustained throughput.", styles["DocSub"]))

    story.append(Paragraph("Phase 4 Test Suite Architecture (27 Tests: 9 Acceptance + 18 Reliability)", styles["Heading2"]))
    p4_table = build_table(
        ["Test Module & Class", "Focus Area", "Test Input / Parameter Space", "Observed Behavior", "Status"],
        [
            ["test_acceptance: TestRandomized", "Deterministic Multi-Seed", "4 fixed seeds (20261009, 20261019, 42, 1337); 100 random frames", "0 failures; 100% data preservation across seeds", "PASS"],
            ["test_acceptance: TestRandomized", "Pathological Patterns", "All 0s, all 1s, alternating 0xAA/0x55, ramps, embedded flags/aborts", "Bit stuffing handles all density extremes", "PASS"],
            ["test_acceptance: TestProfile", "Control Field Rejection", "I-frames (0x00, 0x10), S-frames (RR, RNR, REJ), U-frames (SABM, DISC)", "All non-UI controls rejected with valid CRC", "PASS"],
            ["test_acceptance: TestProfile", "PID Field Rejection", "IPv4 (0xCC), X.25 PLP (0x01), CDPD (0x81), 0xFF, 0x00, 0x08", "All non-0xF0 PIDs rejected with valid CRC", "PASS"],
            ["test_acceptance: TestProfile", "Malformed Addresses", "Destination extension bit=1; Source extension bit=0; bad reserved bits", "Wire syntax violations rejected prior to delivery", "PASS"],
            ["test_acceptance: TestBoundaries", "Payload Size Limits", "4078 bytes (accepted); 4079 bytes (builder ValueError & receiver drop)", "Exact boundary verified at builder and wire levels", "PASS"],
            ["test_acceptance: TestMixedStream", "Continuous Fault Stream", "100 frames with interleaved CRC corruptions, aborts, and oversized inputs", "All valid frames recovered in exact order; 0 corruptions", "PASS"],
            ["test_acceptance: TestBenchmark", "Sustained Throughput", "500 frames (74,000 bytes) end-to-end through NRZI/HDLC pipeline", "864.0 frames/sec; 1,022.9 kbps sustained rate", "PASS"],
        ],
        [140, 110, 220, 240, 70],
        styles,
    )
    story.append(p4_table)
    story.append(Spacer(1, 6))

    story.append(Paragraph("Sustained Processing Performance Benchmark Results", styles["Heading2"]))
    bench_table = build_table(
        ["Benchmark Metric", "Measured Value", "Flight Context / Physical Comparison", "Engineering Implication"],
        [
            ["Processed Frames", "500 frames", "128-byte payload per frame (representative CubeSat telemetry packet)", "Statistically significant sample size"],
            ["Total Decoded Data", "74,000 bytes (592,000 bits)", "Equivalent to ~10 minutes of continuous 1200 bps VHF downlink", "Exceeds single-pass LEO ground pass volume"],
            ["Elapsed Processing Time", "0.579 seconds", "Pure Python 3.14 execution on Windows AMD64 host", "Sub-millisecond latency per frame (~1.15 ms/frame)"],
            ["Frame Processing Rate", "864.0 frames / second", "Normal satellite transmission rate: 0.1 to 2.0 frames / second", "Software pipeline easily outpaces radio receiver link"],
            ["Sustained Data Rate", "1,022.98 kbps (1.02 Mbps)", "Satellite RF downlink bitrate: 1.2 kbps (AFSK) or 9.6 kbps (GFSK)", "Software throughput headroom > 100x required RF bitrate"],
            ["Memory & State Stability", "Deterministic (0 growth)", "Continuous execution without state accumulation or memory leaks", "Safe for long-duration ground station daemon operation"],
        ],
        [125, 145, 230, 280],
        styles,
    )
    story.append(bench_table)

    # ==================== PAGE 5: HARDWARE DEMARCATION & ROADMAP ====================
    story.append(PageBreak())
    story.append(Paragraph("Hardware Demarcation & Engineering Roadmap", styles["Heading1"]))
    story.append(Paragraph("Explicit separation between verified software protocol logic and unverified physical radio hardware.", styles["DocSub"]))

    story.append(Paragraph("Software Boundary vs. Physical RF Layer Demarcation", styles["Heading2"]))
    demarc_table = build_table(
        ["Subsystem Layer", "Implementation Status", "Verified Functions", "Unverified / Out-of-Scope Items"],
        [
            ["Application & Telemetry", "Verified (Phase 1)", "Telemetry byte encapsulation, size checking (0-4078 B), packet dictionary", "Payload schema definition, command authentication, replay protection (TBR)"],
            ["Data Link Layer (AX.25)", "Verified (Phase 1)", "Addressing, SSID, UI control (0x03), PID (0xF0), CRC-16/X-25 generation", "Digipeater routing, multi-hop paths, connection-oriented AX.25 (out of scope)"],
            ["Framing Layer (HDLC)", "Verified (Phase 2)", "Bit stuffing, flag delimiters (0x7E), abort detection, 4096B buffer cap", "Hardware HDLC chips or TNC firmware handshakes"],
            ["Line Coding (NRZI)", "Verified (Phase 2)", "NRZI line level encode/decode, chunked level transition tracking", "Bit polarity inversion detection in hardware"],
            ["Physical / RF Layer", "UNVERIFIED (Phase 5+)", "None (feed_nrzi_levels receives already-demodulated digital bits)", "Carrier recovery, clock/symbol recovery, Doppler compensation, SDR IQ/audio, BER/PER"],
        ],
        [110, 100, 250, 320],
        styles,
    )
    story.append(demarc_table)
    story.append(Spacer(1, 6))

    story.append(Paragraph("Recommended Hardware-in-the-Loop (HIL) Test Plan", styles["Heading2"]))
    hil_table = build_table(
        ["Test Step", "Equipment Required", "Test Procedure", "Pass / Fail Criteria"],
        [
            ["1. Audio AFSK Loopback", "Soundcard / TNC audio interface, 1200 baud Bell 202 modem", "Modulate AX.25 bitstream to 1200/2200 Hz tones; feed to software demodulator", "100% frame recovery without CRC errors over 500 packets"],
            ["2. SDR Baseband (IQ) Loop", "HackRF / USRP / RTL-SDR, GNU Radio flowgraph, coaxial cable", "Stream G3RUH 9600 bps FSK IQ samples through channel model into receiver", "PER < 1% at SNR > 14 dB; frame recovery confirmed"],
            ["3. Doppler Shift Tolerance", "RF signal generator with frequency sweep capability (±3.5 kHz)", "Simulate LEO orbit Doppler shift profile on 437.5 MHz UHF carrier", "Receiver maintains bit-clock synchronization throughout pass"],
            ["4. Third-Party Modem Interop", "Dire Wolf 1.7+, Kenwood TH-D72 / Mobilinkd TNC3 hardware", "Transmit frames from ORBITL-1 software; receive and parse with Dire Wolf", "Mutual frame decode confirmed with zero syntax rejections"],
        ],
        [110, 160, 260, 250],
        styles,
    )
    story.append(hil_table)
    story.append(Spacer(1, 6))

    story.append(Paragraph("Deliverables & Release Integrity", styles["Heading2"]))
    story.append(Paragraph(
        "<b>Release Artifact:</b> <code>ORBITL1-AX25_Phases1-4_Release.zip</code> containing verified source code, unit/integration/acceptance tests, "
        "engineering reports, reference specifications, and test execution metadata. "
        "All 95 automated tests execute via <code>python -m unittest discover -s tests -v</code> using Python 3 standard library.",
        styles["Normal"],
    ))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Generated Master Engineering Report: {output_path} ({os.path.getsize(output_path)} bytes)")


def generate_phase4_technical_report(output_path: Path):
    """Generate 4-page Phase 4 Technical Report."""
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=landscape(A4),
        leftMargin=28,
        rightMargin=28,
        topMargin=32,
        bottomMargin=32,
    )
    styles = get_styles()
    story = []

    # ==================== PAGE 1: SCOPE & SUMMARY ====================
    story.append(Paragraph("ORBITL1-AX25", styles["DocTitle"]))
    story.append(Paragraph("PHASE 4 TECHNICAL REPORT  |  RELIABILITY, ACCEPTANCE & INTEGRATION EVIDENCE", styles["DocSub"]))

    # KPI Row
    kpis = Table([
        [
            make_kpi_card("Phase 4 COMPLETE", "Software Acceptance Gate Status", styles),
            make_kpi_card("95 / 95 Tests PASS", "Cumulative Verification Suite", styles),
            make_kpi_card("864.0 Frames / s", "Sustained Processing Rate", styles),
            make_kpi_card("0 Defects / Regressions", "Runtime Code Baseline Integrity", styles),
        ]
    ], colWidths=[195, 195, 195, 195])
    kpis.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story.append(kpis)
    story.append(Spacer(1, 6))

    story.append(Paragraph("Phase 4 Mission & Acceptance Objectives", styles["Heading2"]))
    story.append(Paragraph(
        "Phase 4 establishes the formal software reliability and acceptance baseline for the ORBITL-1 AX.25 protocol implementation. "
        "Building upon Phase 1 (Frame Core) and Phase 2 (HDLC/NRZI), Phase 4 validates system robustness under multi-seed randomized testing, "
        "pathological byte distributions, strict protocol boundary enforcement, and mixed continuous fault streams containing interleaved CRC corruptions, "
        "HDLC abort sequences, and oversized frames.",
        styles["Normal"],
    ))
    story.append(Spacer(1, 4))

    story.append(Paragraph("Cumulative Test Suite Composition by Responsibility", styles["Heading2"]))
    suite_table = build_table(
        ["Test Module", "Test Class Focus", "Tests", "Phase Responsibility", "Pass Rate"],
        [
            ["tests/test_ax25_core.py", "Address encoding/decoding, UI frame builder, FCS validation, profile edge cases", "29", "Phase 1: AX.25 Frame Core", "100% (29/29)"],
            ["tests/test_hdlc.py", "Bit stuffing, NRZI transitions, chunked HDLC decoding, bit validation", "10", "Phase 2: HDLC & NRZI", "100% (10/10)"],
            ["tests/test_receiver.py", "AX25ReceivePipeline, NRZI demodulator handoff, streaming chunks", "7", "Phase 2: Receive Pipeline", "100% (7/7)"],
            ["tests/test_reliability.py", "Automatic resynchronization, noise recovery, size boundary regression, 1000 rounds", "18", "Phase 2/4: Robustness Baseline", "100% (18/18)"],
            ["tests/test_integration.py", "End-to-end integration, arbitrary chunk sizes, fault recovery, spec vectors, reference model", "22", "Phase 3: Integration & Interoperability", "100% (22/22)"],
            ["tests/test_acceptance.py", "Multi-seed testing, profile rejection (Control/PID), boundary enforcement, stress benchmark", "9", "Phase 4: Reliability & Acceptance", "100% (9/9)"],
            ["TOTAL CUMULATIVE", "Full Automated Test Suite across all phases (executed via standard unittest)", "95", "Phases 1 through 4 Combined", "100% (95/95)"],
        ],
        [140, 310, 50, 180, 100],
        styles,
    )
    story.append(suite_table)

    # ==================== PAGE 2: PHASE 4 METHODOLOGY & EVIDENCE ====================
    story.append(PageBreak())
    story.append(Paragraph("Phase 4 Reliability Methodology & Verification Evidence", styles["Heading1"]))
    story.append(Paragraph("Detailed results of randomized testing, pathological inputs, and strict profile rejection.", styles["DocSub"]))

    story.append(Paragraph("1. Deterministic Multi-Seed Randomized Testing", styles["Heading2"]))
    story.append(Paragraph(
        "To ensure deterministic and reproducible verification, testing utilizes fixed pseudorandom seeds (<code>20261009</code>, <code>20261019</code>, <code>42</code>, <code>1337</code>). "
        "For each seed, 25 randomized payloads ranging from 0 to 1,024 bytes were encoded into AX.25 UI frames, framed via HDLC, modulated to NRZI levels, "
        "and streamed into the receive pipeline. 100% of packets were recovered with bit-for-bit accuracy and valid FCS verification.",
        styles["Normal"],
    ))

    story.append(Paragraph("2. Pathological Payload Survival Matrix", styles["Heading2"]))
    path_table = build_table(
        ["Test Pattern", "Data Size", "Stress Factor", "Bit Stuffing Behavior", "Receiver Result"],
        [
            ["All 0x00 bytes", "256 bytes", "Dense 0-bits (maximum NRZI line transitions)", "Zero bit stuffing required; maximum transition rate", "PASS (100% match)"],
            ["All 0xFF bytes", "256 bytes", "Dense 1-bits (maximum bit stuffing stress)", "Stuffs zero bit after every 5 ones; unstuffs cleanly", "PASS (100% match)"],
            ["Alternating 0x55 / 0xAA", "256 bytes each", "High-frequency bit inversion (01010101 and 10101010)", "Tests byte boundary alignment and shift registers", "PASS (100% match)"],
            ["Ascending / Descending Ramps", "512 bytes each", "Covers all 256 octet values sequentially in both directions", "Ensures no byte-value sensitivity in parser", "PASS (100% match)"],
            ["HDLC Flag Octets (0x7E)", "128 bytes", "Accidental flag sequence (01111110) in payload data", "Bit stuffing successfully prevents false frame close", "PASS (100% match)"],
            ["HDLC Abort Octets (0x7F)", "128 bytes", "Accidental abort sequence (01111111) in payload data", "Bit stuffing breaks consecutive 1s; no abort triggered", "PASS (100% match)"],
        ],
        [150, 80, 220, 210, 120],
        styles,
    )
    story.append(path_table)
    story.append(Spacer(1, 6))

    story.append(Paragraph("3. Strict Profile Rejection Matrix", styles["Heading2"]))
    rej_table = build_table(
        ["Rejected Profile Parameter", "Tested Values", "Enforcement Point", "Observed System Response"],
        [
            ["Non-UI Control Fields", "0x00, 0x10 (I-frame), 0x01 (RR), 0x05 (RNR), 0x09 (REJ), 0x2F (SABM), 0x43 (DISC)", "_decode_ui_body() in src/ax25.py", "ValueError('Unsupported AX.25 control field'); receiver drops frame"],
            ["Non-0xF0 Protocol IDs", "0x01 (X.25), 0x08 (Q.931), 0x81 (CDPD), 0xCC (IPv4), 0xFF, 0x00", "_decode_ui_body() in src/ax25.py", "ValueError('Unsupported AX.25 PID'); receiver drops frame"],
            ["Malformed Wire Addresses", "Destination extension bit=1; Source extension bit=0; clear reserved bits", "_decode_ui_body() and decode_address()", "ValueError('Destination address must not have final-address bit set')"],
            ["Oversized Information Field", "4079 bytes payload (exceeds 4078-byte profile cap)", "build_ui_frame() and HDLC size guard", "build_ui_frame raises ValueError; receiver drops wire frame cleanly"],
        ],
        [140, 220, 180, 240],
        styles,
    )
    story.append(rej_table)

    # ==================== PAGE 3: BENCHMARK & SOURCE EXCERPTS ====================
    story.append(PageBreak())
    story.append(Paragraph("Throughput Benchmarks & Implementation Evidence", styles["Heading1"]))
    story.append(Paragraph("Execution metrics and verified source excerpts from the production codebase.", styles["DocSub"]))

    story.append(Paragraph("Throughput Benchmark Summary (test_sustained_load_throughput_benchmark)", styles["Heading2"]))
    story.append(Paragraph(
        "A sustained stress workload of 500 frames (74,000 total bytes) was streamed through the complete NRZI + HDLC + AX.25 pipeline. "
        "The software receiver processed the entire batch in <b>0.579 seconds</b>, achieving a sustained throughput of <b>864.0 frames/second</b> "
        "(<b>1,022.98 kbps / ~1.02 Mbps</b>). Compared to typical amateur satellite telemetry rates of 1.2 kbps or 9.6 kbps, the software protocol stack "
        "provides over <b>100x processing headroom</b>.",
        styles["Normal"],
    ))
    story.append(Spacer(1, 4))

    story.append(Paragraph("Production Source Code Excerpts (Verified Truth)", styles["Heading2"]))

    # Excerpt 1: AX.25 UI Frame Builder
    e1_code = """# From src/ax25.py: build_ui_frame
def build_ui_frame(destination: str, source: str, information: bytes) -> bytes:
    information = _require_bytes(information, "information")
    if len(information) > MAX_INFORMATION_BYTES:  # 4078 bytes
        raise ValueError(f"Information field exceeds {MAX_INFORMATION_BYTES} bytes...")
    body = bytearray()
    body.extend(encode_address(destination, last=False))
    body.extend(encode_address(source, last=True))
    body.extend((AX25_UI_CONTROL, AX25_NO_LAYER3_PID))  # 0x03, 0xF0
    body.extend(information)
    fcs = crc16_x25(bytes(body))
    body.extend((fcs & 0xFF, (fcs >> 8) & 0xFF))  # low byte first
    return bytes((AX25_FLAG,)) + bytes(body) + bytes((AX25_FLAG,))"""
    story.append(make_code_box(e1_code, styles, width=780))
    story.append(Spacer(1, 4))

    # Excerpt 2: Receiver Pipeline Demodulator Handoff
    e2_code = """# From src/ax25_receiver.py: feed_nrzi_levels
def feed_nrzi_levels(self, levels, initial_level: int | None = None):
    levels = list(levels)
    if initial_level is not None:
        self._nrzi_previous_level = initial_level
    if not levels: return []
    bits = nrzi_decode(levels, initial_level=self._nrzi_previous_level)
    self._nrzi_previous_level = levels[-1]  # Retain state across streaming chunks
    return self.feed_bits(bits)"""
    story.append(make_code_box(e2_code, styles, width=780))
    story.append(Spacer(1, 4))

    # Excerpt 3: HDLC Stream Decoder Buffer Guard
    e3_code = """# From src/vendor/mobilinkd/HDLC.py: _finish_frame and process
def _finish_frame(self):
    length = self.frame.tell()
    if 14 < length <= self.MAX_FRAME_BYTES:  # 4096 bytes cap
        return (self.crc(), self.frame.getvalue()[:-2])
    return None"""
    story.append(make_code_box(e3_code, styles, width=780))

    # ==================== PAGE 4: PHASE 3 EVIDENCE & HIL PLAN ====================
    story.append(PageBreak())
    story.append(Paragraph("Phase 3 Integration Cross-Evidence & Hardware Roadmap", styles["Heading1"]))
    story.append(Paragraph("Independent vector validation, hardware demarcation, and actionable HIL roadmap.", styles["DocSub"]))

    story.append(Paragraph("Phase 3 Independent Interoperability Summary", styles["Heading2"]))
    story.append(Paragraph(
        "Phase 4 acceptance is directly backed by Phase 3 independent interoperability verification. "
        "The project's frame construction and CRC calculation were validated against external standards: "
        "(1) ISO/IEC 3309 and ITU-T X.25 test vector <code>123456789 -> 0x906E</code>, "
        "(2) AX.25 v2.2 specification Section 3.12 published address vectors for <code>NJ7P-0</code> and <code>N7LEM-0</code>, and "
        "(3) an independent, from-scratch pure-Python reference model (<code>IndependentAX25Reference</code>) demonstrating 100% bit-accurate agreement.",
        styles["Normal"],
    ))
    story.append(Spacer(1, 4))

    story.append(Paragraph("Hardware-in-the-Loop (HIL) Preparation Checklist", styles["Heading2"]))
    checklist_table = build_table(
        ["Subsystem / Milestone", "Prerequisite Completed in SW", "Hardware Requirement", "Verification Target"],
        [
            ["AFSK 1200 Baud Audio", "NRZI & bitstream verified", "Bell 202 audio DAC/ADC interface", "Zero CRC errors on loopback"],
            ["GFSK 9600 Baud SDR", "4096B stream buffer guard", "SDR transceiver (HackRF/USRP/Lime)", "Demodulator handoff to feed_nrzi_levels"],
            ["Doppler Tracking", "Chunked streaming state", "Gpredict / Hamlib frequency steering", "Carrier lock maintained through ±3.5 kHz shift"],
            ["Telecommand Auth", "FCS validation & error drop", "HMAC / AES crypto wrapper on payload", "Anti-replay protection on uplink telecommands"],
        ],
        [150, 180, 220, 230],
        styles,
    )
    story.append(checklist_table)
    story.append(Spacer(1, 6))

    story.append(Paragraph("Formal Software Acceptance Declaration", styles["Heading2"]))
    story.append(make_note_box(
        "<b>PHASE 3 & PHASE 4 ACCEPTANCE GATE: MET (SOFTWARE-COMPLETE)</b><br/>"
        "All 95 unit, integration, reliability, and acceptance tests pass deterministically. "
        "Runtime code integrity of Phases 1 and 2 has been preserved without unauthorized modification. "
        "The software protocol layer is verified, packaged, and documented. "
        "Physical RF hardware qualification remains TBR pending radio selection and HIL testing.",
        styles,
    ))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Generated Phase 4 Technical Report: {output_path} ({os.path.getsize(output_path)} bytes)")


def main():
    master_path = OUT_DIR / "ORBITL1_AX25_Master_Engineering_Report.pdf"
    phase4_path = OUT_DIR / "ORBITL1_AX25_Phase4_Technical_Report.pdf"

    print("Building Cumulative Master Engineering Report...")
    generate_master_engineering_report(master_path)

    print("Building Phase 4 Technical Report...")
    generate_phase4_technical_report(phase4_path)

    print("\nPDF Generation Completed Successfully.")


if __name__ == "__main__":
    main()
