
"""ORBITL1 AX.25 receive pipeline.

Receives HDLC bits and parses CRC-validated AX.25 UI frames.
Mobilinkd HDLC decoder verifies FCS before returning the body.
"""

from src.ax25 import decode_verified_ui_body
from src.ax25_hdlc import HDLCStreamDecoder
from src.ax25_transmitter import nrzi_decode


class AX25ReceivePipeline:
    def __init__(self):
        self._decoder = HDLCStreamDecoder()
        self._nrzi_previous_level = 0

    def feed_bits(self, bits):
        """Accept demodulated HDLC bits after NRZI decoding.

        The iterable may be a complete frame or an arbitrary streaming chunk.
        Only CRC-valid HDLC bodies that match the supported AX.25 UI profile
        are returned.
        """
        packets = []

        for body in self._decoder.feed(bits):
            try:
                packet = decode_verified_ui_body(body)
            except ValueError:
                # CRC-valid but unsupported/malformed frame.
                continue

            packets.append(packet)

        return packets

    def feed_nrzi_levels(self, levels, initial_level: int | None = None):
        """Accept binary NRZI levels from a demodulator and decode packets.

        This is the digital interface immediately after RF/SDR demodulation;
        it does not consume raw audio/IQ samples or perform clock recovery.
        NRZI state is retained across chunks. Supply ``initial_level`` only
        when deliberately starting a new line-level stream.
        """
        levels = list(levels)
        if initial_level is not None:
            if type(initial_level) is not int or initial_level not in (0, 1):
                raise ValueError("Invalid initial NRZI level")
            self._nrzi_previous_level = initial_level
        if not levels:
            return []

        bits = nrzi_decode(levels, initial_level=self._nrzi_previous_level)
        self._nrzi_previous_level = levels[-1]
        return self.feed_bits(bits)

    def reset(self):
        self._decoder.reset()
        self._nrzi_previous_level = 0
