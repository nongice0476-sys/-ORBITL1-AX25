"""AX.25 UI frame construction and validation for ORBITL1-AX25.

This module owns the logical AX.25 frame boundary. RF demodulation,
NRZI decoding, HDLC de-stuffing, and FCS checking happen before a received
body is handed to :func:`decode_verified_ui_body` by the Phase 2 pipeline.

Supported profile: one destination, one source, UI control (0x03), PID
0xF0, no digipeater path. The maximum HDLC frame content is 4096 bytes,
including the two FCS bytes but excluding opening/closing flags.
"""

from __future__ import annotations

from typing import Any

AX25_FLAG = 0x7E
AX25_UI_CONTROL = 0x03
AX25_NO_LAYER3_PID = 0xF0
MAX_HDLC_CONTENT_BYTES = 4096  # AX.25 body + 2-byte FCS, flags excluded
ADDRESS_FIELD_BYTES = 7
AX25_HEADER_BYTES = 16  # destination + source + control + PID
FCS_BYTES = 2
MAX_INFORMATION_BYTES = (
    MAX_HDLC_CONTENT_BYTES - AX25_HEADER_BYTES - FCS_BYTES
)  # 4078 bytes for this profile


def _require_bytes(value: Any, name: str) -> bytes:
    """Accept bytes-like input and reject accidental text/iterables."""
    if isinstance(value, bytes):
        return value
    if isinstance(value, (bytearray, memoryview)):
        return bytes(value)
    raise TypeError(f"{name} must be bytes-like")


def parse_address(address: str) -> tuple[str, int]:
    """Parse a callsign with optional SSID, e.g. ``ORBITL-1``.

    Callsigns are normalized to uppercase and limited to 1-6 ASCII letters
    or digits. SSIDs are decimal integers from 0 through 15.
    """
    if not isinstance(address, str):
        raise TypeError("AX.25 address must be a string")
    if not address or address != address.strip():
        raise ValueError("AX.25 address must not be empty or padded with spaces")

    # Check the original input before case normalization: some Unicode
    # characters (for example long-s and dotless-i) uppercase to ASCII.
    # AX.25 callsigns are restricted to ASCII letters and digits.
    if not address.isascii():
        raise ValueError("AX.25 address must contain ASCII characters only")

    normalized = address.upper()
    if "-" in normalized:
        callsign, ssid_text = normalized.rsplit("-", 1)
        if not ssid_text or not ssid_text.isascii() or not ssid_text.isdigit():
            raise ValueError("AX.25 SSID must be a decimal integer")
        ssid = int(ssid_text, 10)
    else:
        callsign, ssid = normalized, 0

    if not 1 <= len(callsign) <= 6:
        raise ValueError("AX.25 callsign must contain 1 to 6 characters")
    if not callsign.isascii() or not all(c.isalnum() for c in callsign):
        raise ValueError("AX.25 callsign may contain only ASCII letters and digits")
    if not 0 <= ssid <= 15:
        raise ValueError("AX.25 SSID must be between 0 and 15")

    return callsign, ssid


def encode_address(address: str, last: bool) -> bytes:
    """Encode a seven-byte AX.25 address field."""
    if type(last) is not bool:
        raise TypeError("last must be a bool")

    callsign, ssid = parse_address(address)
    encoded = bytearray((ord(character) << 1) for character in callsign.ljust(6))

    # Bits 5-6 are reserved and set to 1; bits 1-4 carry the SSID;
    # bit 0 is the extension bit (1 only for the final address field).
    ssid_byte = 0x60 | (ssid << 1) | int(last)
    encoded.append(ssid_byte)
    return bytes(encoded)


def decode_address(data: bytes) -> tuple[str, int, bool]:
    """Validate and decode one seven-byte AX.25 address field."""
    data = _require_bytes(data, "address data")
    if len(data) != ADDRESS_FIELD_BYTES:
        raise ValueError("AX.25 address must contain exactly 7 bytes")

    if any(byte & 0x01 for byte in data[:6]):
        raise ValueError("AX.25 callsign octets must have their low bit clear")
    if (data[6] & 0x60) != 0x60:
        raise ValueError("AX.25 SSID reserved bits must be set")

    chars = "".join(chr(byte >> 1) for byte in data[:6])
    callsign = chars.rstrip(" ")
    if not callsign or " " in callsign:
        raise ValueError("AX.25 callsign padding must be trailing only")
    if not callsign.isascii() or not all(c.isalnum() for c in callsign):
        raise ValueError("AX.25 callsign contains invalid characters")
    if callsign != callsign.upper():
        raise ValueError("AX.25 callsign on the wire must use uppercase ASCII")

    ssid = (data[6] >> 1) & 0x0F
    last = bool(data[6] & 0x01)
    return callsign, ssid, last


def crc16_x25(data: bytes) -> int:
    """Calculate CRC-16/X-25 (reflected polynomial 0x8408)."""
    data = _require_bytes(data, "CRC input")
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            crc = (crc >> 1) ^ (0x8408 if crc & 1 else 0)
    return crc ^ 0xFFFF


def _decode_ui_body(body: bytes) -> dict[str, Any]:
    """Parse AX.25 UI content without flags or FCS after FCS verification."""
    if len(body) < AX25_HEADER_BYTES:
        raise ValueError("AX.25 UI body is too short")
    if len(body) + FCS_BYTES > MAX_HDLC_CONTENT_BYTES:
        raise ValueError("AX.25 frame exceeds the 4096-byte HDLC content limit")

    destination = decode_address(body[0:7])
    source = decode_address(body[7:14])

    if destination[2]:
        raise ValueError("Destination address must not have the final-address bit set")
    if not source[2]:
        raise ValueError("Source address must be final; digipeater paths are unsupported")

    control = body[14]
    pid = body[15]
    if control != AX25_UI_CONTROL:
        raise ValueError(f"Unsupported AX.25 control field: 0x{control:02X}")
    if pid != AX25_NO_LAYER3_PID:
        raise ValueError(f"Unsupported AX.25 PID: 0x{pid:02X}")

    return {
        "destination": {"callsign": destination[0], "ssid": destination[1]},
        "source": {"callsign": source[0], "ssid": source[1]},
        "control": control,
        "pid": pid,
        "information": body[AX25_HEADER_BYTES:],
        "fcs_verified": True,
    }


def decode_verified_ui_body(body: bytes) -> dict[str, Any]:
    """Parse a body returned by a trusted HDLC decoder after valid-FCS check.

    The caller MUST ensure that HDLC/FCS verification succeeded. This is the
    Phase 2 -> Phase 1 integration boundary; this function does not calculate
    or independently verify an FCS because the body does not contain it.
    """
    body = _require_bytes(body, "verified AX.25 body")
    return _decode_ui_body(body)


def build_ui_frame(
    destination: str,
    source: str,
    information: bytes,
) -> bytes:
    """Build a complete flagged AX.25 UI frame with a valid FCS."""
    information = _require_bytes(information, "information")
    if len(information) > MAX_INFORMATION_BYTES:
        raise ValueError(
            f"Information field exceeds {MAX_INFORMATION_BYTES} bytes "
            "for the configured 4096-byte HDLC content limit"
        )

    body = bytearray()
    body.extend(encode_address(destination, last=False))
    body.extend(encode_address(source, last=True))
    body.extend((AX25_UI_CONTROL, AX25_NO_LAYER3_PID))
    body.extend(information)

    fcs = crc16_x25(bytes(body))
    body.extend((fcs & 0xFF, (fcs >> 8) & 0xFF))
    return bytes((AX25_FLAG,)) + bytes(body) + bytes((AX25_FLAG,))


def decode_ui_frame(frame: bytes) -> dict[str, Any]:
    """Validate and decode a complete flagged AX.25 UI frame.

    ``frame`` includes opening/closing flags and the two FCS bytes.
    """
    frame = _require_bytes(frame, "AX.25 frame")
    if len(frame) < 20:
        raise ValueError("AX.25 frame is too short")
    if frame[0] != AX25_FLAG:
        raise ValueError("Missing opening AX.25 flag")
    if frame[-1] != AX25_FLAG:
        raise ValueError("Missing closing AX.25 flag")

    content = frame[1:-1]
    if len(content) > MAX_HDLC_CONTENT_BYTES:
        raise ValueError("AX.25 frame exceeds the 4096-byte HDLC content limit")
    if len(content) < AX25_HEADER_BYTES + FCS_BYTES:
        raise ValueError("AX.25 frame content is too short")

    body = content[:-FCS_BYTES]
    received_fcs = content[-2] | (content[-1] << 8)
    calculated_fcs = crc16_x25(body)
    if received_fcs != calculated_fcs:
        raise ValueError("AX.25 FCS/CRC validation failed")

    decoded = _decode_ui_body(body)
    decoded["received_fcs"] = received_fcs
    decoded["calculated_fcs"] = calculated_fcs
    return decoded
