
"""AX.25 HDLC bitstream transmitter and NRZI utilities.

Complements the MIT-licensed Mobilinkd receiver adapter.
Bit-level implementation for ORBITL1-AX25.
"""


def bytes_to_bits(data: bytes) -> list[int]:
    """Convert bytes to LSB-first bits."""
    return [
        (byte >> bit_position) & 1
        for byte in data
        for bit_position in range(8)
    ]


def bit_stuff(bits: list[int]) -> list[int]:
    """Insert a zero after five consecutive one bits."""
    output = []
    ones = 0

    for bit in bits:
        if bit not in (0, 1):
            raise ValueError("Bits must be 0 or 1")

        output.append(bit)

        if bit == 1:
            ones += 1
            if ones == 5:
                output.append(0)
                ones = 0
        else:
            ones = 0

    return output


def encode_hdlc(frame: bytes) -> list[int]:
    """Convert an AX.25 frame into an HDLC bitstream.

    The input frame includes the leading and trailing 0x7E
    flags produced by Phase 1.
    """
    if len(frame) < 2 or frame[0] != 0x7E or frame[-1] != 0x7E:
        raise ValueError("Expected an AX.25 frame with boundary flags")

    body = frame[1:-1]
    flag = bytes_to_bits(b"\x7e")

    return flag + bit_stuff(bytes_to_bits(body)) + flag


def nrzi_encode(bits: list[int], initial_level: int = 0) -> list[int]:
    """NRZI: bit 0 causes transition, bit 1 means no transition."""
    if initial_level not in (0, 1):
        raise ValueError("Invalid initial level")

    output = []
    level = initial_level

    for bit in bits:
        if bit not in (0, 1):
            raise ValueError("Bits must be 0 or 1")
        if bit == 0:
            level ^= 1
        output.append(level)

    return output


def nrzi_decode(levels: list[int], initial_level: int = 0) -> list[int]:
    """Recover bits from NRZI line levels."""
    if initial_level not in (0, 1):
        raise ValueError("Invalid initial level")

    output = []
    previous = initial_level

    for level in levels:
        if level not in (0, 1):
            raise ValueError("NRZI levels must be 0 or 1")
        output.append(1 if level == previous else 0)
        previous = level

    return output
