
"""HDLC streaming decoder adapter for ORBITL1-AX25.

Uses the vendored, MIT-licensed Mobilinkd HDLC decoder.
Original copyright (c) 2019 Mobilinkd LLC.

See src/vendor/mobilinkd/LICENSE.

Input: raw HDLC bits after NRZI decoding.
Output: CRC-validated AX.25 frame bodies without flags or FCS.
"""

from src.vendor.mobilinkd.HDLC import HDLC


class HDLCStreamDecoder:
    """Streaming decoder for CRC-valid HDLC frames."""

    def __init__(self):
        self._receiver = HDLC()

    def feed_bit(self, bit: int):
        if type(bit) is not int or bit not in (0, 1):
            raise ValueError("Bit must be 0 or 1")

        # True means the demodulator has signal lock.
        result = self._receiver(bit, True)

        if result is None:
            return None

        residue, decoded = result

        if residue != 0xF0B8:
            return None

        # Mobilinkd uses an 8-bit character string.
        # Its returned data excludes the 2-byte FCS.
        return decoded.encode("latin-1")

    def feed(self, bits):
        """Decode a chunk and return all valid frame bodies."""
        frames = []

        for bit in bits:
            frame = self.feed_bit(bit)

            if frame is not None:
                frames.append(frame)

        return frames

    def reset(self):
        """Reset the underlying HDLC decoder."""
        self._receiver.reset()
