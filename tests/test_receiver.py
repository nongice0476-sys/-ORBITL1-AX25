
import unittest

from src.ax25 import build_ui_frame
from src.ax25_transmitter import encode_hdlc
from src.ax25_receiver import AX25ReceivePipeline


class TestAX25Receiver(unittest.TestCase):

    def test_valid_telemetry(self):
        payload = b"SEQ=100;BAT=7.60V"
        frame = build_ui_frame(
            "GROUND", "ORBITL-1", payload
        )

        receiver = AX25ReceivePipeline()
        packets = receiver.feed_bits(encode_hdlc(frame))

        self.assertEqual(len(packets), 1)
        self.assertEqual(
            packets[0]["information"], payload
        )
        self.assertEqual(
            packets[0]["source"]["callsign"], "ORBITL"
        )
        self.assertTrue(packets[0]["fcs_verified"])

    def test_corrupted_frame(self):
        frame = bytearray(build_ui_frame(
            "GROUND", "ORBITL-1", b"SEQ=101"
        ))

        frame[19] ^= 1

        receiver = AX25ReceivePipeline()
        self.assertEqual(
            receiver.feed_bits(encode_hdlc(bytes(frame))),
            []
        )

    def test_binary_payload(self):
        payload = bytes(range(256))
        frame = build_ui_frame(
            "GROUND", "ORBITL-1", payload
        )

        packets = AX25ReceivePipeline().feed_bits(
            encode_hdlc(frame)
        )

        self.assertEqual(len(packets), 1)
        self.assertEqual(
            packets[0]["information"], payload
        )

    def test_streaming_chunks(self):
        frame = build_ui_frame(
            "GROUND", "ORBITL-1", b"SEQ=102"
        )
        bits = encode_hdlc(frame)

        receiver = AX25ReceivePipeline()
        packets = []

        for i in range(0, len(bits), 7):
            packets.extend(
                receiver.feed_bits(bits[i:i + 7])
            )

        self.assertEqual(len(packets), 1)
        self.assertEqual(
            packets[0]["information"], b"SEQ=102"
        )

    def test_two_frames(self):
        frames = [
            build_ui_frame("GROUND", "ORBITL-1", b"SEQ=1"),
            build_ui_frame("GROUND", "ORBITL-1", b"SEQ=2"),
        ]

        stream = encode_hdlc(frames[0]) + encode_hdlc(frames[1])
        packets = AX25ReceivePipeline().feed_bits(stream)

        self.assertEqual(
            [p["information"] for p in packets],
            [b"SEQ=1", b"SEQ=2"]
        )


if __name__ == "__main__":
    unittest.main()


class TestDemodulatorHandoff(unittest.TestCase):

    def test_nrzi_levels_from_demodulator_reach_phase1_parser(self):
        from src.ax25_transmitter import nrzi_encode

        payload = b"SEQ=205;BAT=7.55V"
        frame = build_ui_frame("GROUND", "ORBITL-1", payload)
        levels = nrzi_encode(encode_hdlc(frame))

        packets = AX25ReceivePipeline().feed_nrzi_levels(levels)
        self.assertEqual(len(packets), 1)
        self.assertEqual(packets[0]["information"], payload)
        self.assertTrue(packets[0]["fcs_verified"])

    def test_nrzi_level_streaming_chunks(self):
        from src.ax25_transmitter import nrzi_encode

        payload = b"CHUNKED-RF-INTERFACE"
        frame = build_ui_frame("GROUND", "ORBITL-1", payload)
        levels = nrzi_encode(encode_hdlc(frame))

        receiver = AX25ReceivePipeline()
        packets = []
        for offset in range(0, len(levels), 13):
            packets.extend(receiver.feed_nrzi_levels(levels[offset:offset + 13]))

        self.assertEqual([packet["information"] for packet in packets], [payload])
