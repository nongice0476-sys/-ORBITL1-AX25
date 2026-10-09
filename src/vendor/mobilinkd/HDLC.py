
# SPDX-License-Identifier: MIT
#
# HDLC decoder derived from Mobilinkd.
# Modified for the ORBITL1-AX25 project.
#
# Modifications:
# - Fix HDLC closing-flag detection (Frame 12).
# - Enforce MAX_FRAME_BYTES = 4096.
# - Reject oversized frames before delivery.
# - Recover from oversized/unterminated frames.
#
# Retain the original Mobilinkd LICENSE file.

from io import StringIO
from .CRC import CRC16CCITT


class HDLC:

    SEARCH = 0
    HUNT = 1
    FRAME = 2

    FLAG = 0x7E
    ABORT = 0x7F
    IDLE = 0xFF

    # Project-defined limit, not the AX.25 standard limit.
    # Includes AX.25 header, payload and 2-byte FCS.
    MAX_FRAME_BYTES = 4096

    BOGONS = [0xFF00, 0xFE00, 0x7F00]

    FRAME_ERRORS = [
        0xFF00,
        0xFE00,
        0xFC00,
        0x7F00,
        0x7E00,
    ]

    def __init__(self, passall=False, callback=None):
        self.passall = passall
        self.callback = callback

        self.reset()

        self.action = [
            self.search,
            self.hunt,
            self.do_frame,
        ]

    def reset(self):
        self.state = HDLC.SEARCH
        self.bits = 0
        self.ones = 0
        self.buffer = 0
        self.frame = StringIO()

        self.ready = False
        self.pll = False

    def __call__(self, bit, pll):
        result = None

        if not pll:
            if (
                self.passall
                and self.frame.tell() > 14
                and self.frame.tell() <= self.MAX_FRAME_BYTES
            ):
                result = (
                    self.crc(),
                    self.frame.getvalue(),
                )

            self.reset()

        else:
            self.pll = pll
            result = self.process(bit)

            if result is not None:
                crc = result[0]

                self.reset()

                if crc != 0xF0B8 and not self.passall:
                    result = None
                else:
                    self.start_hunt()

        return result

    def framing(self):
        return self.state == HDLC.FRAME

    def _add_bit(self, bit):
        self.buffer >>= 1
        self.buffer |= 0x8000 * int(bit)
        self.bits += 1

    def _have_flag(self):
        return (self.buffer & 0xFF00) == 0x7E00

    def _have_bogon(self):
        return (
            self.buffer & 0xFF00
        ) in HDLC.BOGONS

    def _have_frame_error(self):
        return (
            self.buffer & 0xFF00
        ) in HDLC.FRAME_ERRORS

    def start_search(self):
        self.state = HDLC.SEARCH

    def search(self, bit):
        self._add_bit(bit)

        if self._have_flag():
            self.start_hunt()

        return None

    def start_hunt(self):
        self.state = HDLC.HUNT
        self.bits = 0
        self.buffer = 0

    def hunt(self, bit):
        self._add_bit(bit)

        if self.bits == 8:

            if self._have_flag():
                self.start_hunt()

            elif self._have_bogon():
                self.start_search()

            elif not self._have_frame_error():
                self.start_frame()

            else:
                self.start_search()

        return None

    def start_frame(self):
        self.state = HDLC.FRAME
        self.frame = StringIO()
        self.ones = 0
        self.buffer &= 0xFF00

    def getchar(self):
        return chr(self.buffer & 0xFF)

    def consume_byte(self):
        self.buffer &= 0xFF00
        self.bits -= 8

    def consume_bit(self):
        tmp = (self.buffer & 0x7F) << 1
        self.buffer &= 0xFF00
        self.buffer |= tmp
        self.bits -= 1

    def _finish_frame(self):
        """Return a complete frame only if its length is valid.

        The returned payload excludes the 2-byte FCS.
        CRC validation is performed by __call__.
        """
        length = self.frame.tell()

        if 14 < length <= self.MAX_FRAME_BYTES:
            return (
                self.crc(),
                self.frame.getvalue()[:-2],
            )

        return None

    def do_frame(self, bit):
        result = None

        self._add_bit(bit)

        if self.ones < 5:

            if (self.buffer & 0x80) == 0x80:
                self.ones += 1
            else:
                self.ones = 0

            # Store a complete decoded byte.
            if self.bits == 16:
                self.frame.write(self.getchar())
                self.consume_byte()

                # Reject an oversized unfinished frame
                # before its closing flag can arrive.
                if self.frame.tell() > self.MAX_FRAME_BYTES:
                    self.reset()
                    return None

            # Original closing-flag detection.
            if self._have_flag():

                # Check frame size BEFORE start_frame()
                # clears the accumulated data.
                result = self._finish_frame()

                self.start_frame()

        else:
            # At least five consecutive 1 bits.
            if (self.buffer & 0x80) == 0:

                # Closing-flag fix for Frame 12.
                # Do not discard a flag as a stuffed zero.
                if self._have_flag():

                    result = self._finish_frame()

                    self.start_frame()
                    return result

                # Normal HDLC bit destuffing.
                self.consume_bit()
                self.ones = 0

            else:
                # Framing error / abort sequence.
                if (
                    self.passall
                    and 14 < self.frame.tell()
                    <= self.MAX_FRAME_BYTES
                ):
                    result = (
                        self.crc(),
                        self.frame.getvalue(),
                    )

                if (
                    (
                        self.buffer
                        >> (16 - self.bits)
                    ) & 0xFF
                ) == 0x7E:

                    self.bits -= 8
                    self.state = HDLC.HUNT
                    self.frame = StringIO()

                else:
                    self.start_search()

        return result

    def process(self, bit):
        result = self.action[self.state](bit)

        # Additional resource-safety guard.
        if (
            self.state == HDLC.FRAME
            and self.frame.tell() > self.MAX_FRAME_BYTES
        ):
            self.reset()
            return None

        return result

    def check_frame(self):
        if self.crc() == 0xF0B8:
            return self.frame.getvalue()

        return None

    def crc(self):
        crc = CRC16CCITT()
        return crc.compute(self.frame.getvalue())
