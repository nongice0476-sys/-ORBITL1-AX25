
"""ORBITL1 AX.25 receive pipeline.

Receives HDLC bits and parses CRC-validated AX.25 UI frames.
Mobilinkd HDLC decoder verifies FCS before returning the body.
"""

from src.ax25 import (
    AX25_UI_CONTROL,
    AX25_NO_LAYER3_PID,
    decode_address,
)
from src.ax25_hdlc import HDLCStreamDecoder


class AX25ReceivePipeline:
    def __init__(self):
        self._decoder = HDLCStreamDecoder()

    def _parse_verified_body(self, body: bytes):
        # Body has already passed HDLC FCS verification.
        # Mobilinkd removes the two FCS bytes.
        if len(body) < 16:
            raise ValueError("AX.25 UI body is too short")

        destination = decode_address(body[0:7])
        source = decode_address(body[7:14])

        if destination[2]:
            raise ValueError("Unexpected final destination address")

        if not source[2]:
            raise ValueError("Digipeater addresses not supported")

        control = body[14]
        pid = body[15]

        if control != AX25_UI_CONTROL:
            raise ValueError("Unsupported AX.25 control field")

        if pid != AX25_NO_LAYER3_PID:
            raise ValueError("Unsupported AX.25 PID")

        return {
            "destination": {
                "callsign": destination[0],
                "ssid": destination[1],
            },
            "source": {
                "callsign": source[0],
                "ssid": source[1],
            },
            "control": control,
            "pid": pid,
            "information": body[16:],
            "fcs_verified": True,
        }

    def feed_bits(self, bits):
        packets = []

        for body in self._decoder.feed(bits):
            try:
                packet = self._parse_verified_body(body)
            except ValueError:
                # CRC-valid but unsupported/malformed frame.
                continue

            packets.append(packet)

        return packets

    def reset(self):
        self._decoder.reset()
