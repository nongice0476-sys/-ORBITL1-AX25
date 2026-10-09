
import unittest

from src.ax25 import build_ui_frame
from src.ax25_transmitter import encode_hdlc
from src.ax25_receiver import AX25ReceivePipeline


class TestHDLCSizeBoundary(unittest.TestCase):

    def receive(self, payload):
        frame = build_ui_frame(
            "GROUND", "ORBITL-1", payload
        )
        return AX25ReceivePipeline().feed_bits(
            encode_hdlc(frame)
        )

    def test_exactly_4096_bytes_accepted(self):
        # AX.25 frame body:
        # 16-byte header + payload + 2-byte FCS
        payload = b"A" * 4078

        packets = self.receive(payload)

        self.assertEqual(len(packets), 1)
        self.assertEqual(
            packets[0]["information"], payload
        )

    def test_4097_bytes_rejected(self):
        payload = b"B" * 4079

        packets = self.receive(payload)

        self.assertEqual(packets, [])

    def test_recovery_after_oversized_frame(self):
        oversized = build_ui_frame(
            "GROUND", "ORBITL-1",
            b"B" * 4079
        )
        valid = build_ui_frame(
            "GROUND", "ORBITL-1",
            b"RECOVERY-OK"
        )

        receiver = AX25ReceivePipeline()
        packets = receiver.feed_bits(
            encode_hdlc(oversized)
            + encode_hdlc(valid)
        )

        self.assertEqual(
            [p["information"] for p in packets],
            [b"RECOVERY-OK"]
        )


if __name__ == "__main__":
    unittest.main()
