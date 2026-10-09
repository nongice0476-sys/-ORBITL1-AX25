
"""Final acceptance regression tests for ORBITL1 Phase 2."""

import random
import unittest

from src.ax25 import build_ui_frame
from src.ax25_transmitter import (
    encode_hdlc,
    nrzi_encode,
    nrzi_decode,
)
from src.ax25_hdlc import HDLCStreamDecoder
from src.ax25_receiver import AX25ReceivePipeline


class TestHDLCFinalAcceptance(unittest.TestCase):

    def test_randomized_round_trip_1000(self):
        rng = random.Random(20261009)

        for i in range(1000):
            size = rng.randint(0, 512)
            payload = rng.randbytes(size)

            frame = build_ui_frame(
                "GROUND", "ORBITL-1", payload
            )

            levels = nrzi_encode(encode_hdlc(frame))
            bits = nrzi_decode(levels)

            packets = AX25ReceivePipeline().feed_bits(bits)

            self.assertEqual(
                len(packets), 1,
                f"Frame {i}, payload size {size}"
            )
            self.assertEqual(
                packets[0]["information"], payload
            )
            self.assertTrue(packets[0]["fcs_verified"])

    def test_continuous_chunked_stream(self):
        rng = random.Random(20261009)
        stream = []
        expected = []

        for i in range(100):
            payload = (
                i.to_bytes(4, "little")
                + rng.randbytes(rng.randint(0, 512))
            )

            expected.append(payload)
            frame = build_ui_frame(
                "GROUND", "ORBITL-1", payload
            )
            stream.extend(encode_hdlc(frame))

        receiver = AX25ReceivePipeline()
        received = []
        offset = 0

        while offset < len(stream):
            size = rng.randint(1, 97)
            chunk = stream[offset:offset + size]

            received.extend(
                packet["information"]
                for packet in receiver.feed_bits(chunk)
            )
            offset += len(chunk)

        self.assertEqual(received, expected)

    def test_crc_corruption_and_recovery(self):
        rng = random.Random(20261009)
        receiver = AX25ReceivePipeline()
        expected = []
        received = []

        for i in range(100):
            payload = (
                i.to_bytes(4, "little")
                + rng.randbytes(rng.randint(1, 256))
            )
            frame = bytearray(
                build_ui_frame(
                    "GROUND", "ORBITL-1", payload
                )
            )

            if i % 3 == 1:
                frame[16] ^= 0x01
            else:
                expected.append(payload)

            bits = encode_hdlc(bytes(frame))
            offset = 0

            while offset < len(bits):
                size = rng.randint(1, 47)
                chunk = bits[offset:offset + size]
                received.extend(
                    packet["information"]
                    for packet in receiver.feed_bits(chunk)
                )
                offset += len(chunk)

        self.assertEqual(len(expected), 67)
        self.assertEqual(received, expected)

    def test_abort_and_recovery(self):
        damaged = build_ui_frame(
            "GROUND", "ORBITL-1", b"ABORT-ME"
        )
        valid = build_ui_frame(
            "GROUND", "ORBITL-1",
            b"RECOVERY-AFTER-ABORT"
        )

        stream = (
            encode_hdlc(damaged)[:-24]
            + [1] * 8
            + encode_hdlc(valid)
        )

        packets = AX25ReceivePipeline().feed_bits(stream)

        self.assertEqual(
            [p["information"] for p in packets],
            [b"RECOVERY-AFTER-ABORT"]
        )

    def test_buffer_overflow_and_recovery(self):
        decoder = HDLCStreamDecoder()

        incomplete = build_ui_frame(
            "GROUND", "ORBITL-1", b"BUFFER-CHECK"
        )

        decoder.feed(encode_hdlc(incomplete)[:-8])

        # Large unterminated stream: should be discarded.
        decoder.feed([0, 1, 0, 1, 0, 1, 0, 1] * 6000)

        valid = build_ui_frame(
            "GROUND", "ORBITL-1", b"RECOVERY-OK"
        )

        self.assertEqual(
            decoder.feed(encode_hdlc(valid)),
            [valid[1:-3]]
        )

    def test_maximum_frame_boundary(self):
        # The current vendor buffer limit is 4096 bytes.
        # Verify a moderately large valid payload succeeds.
        payload = bytes(range(256)) * 8

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

    def test_no_invalid_frame_accepted(self):
        frame = bytearray(
            build_ui_frame(
                "GROUND", "ORBITL-1", b"INVALID-FCS"
            )
        )

        frame[-3] ^= 0x80

        packets = AX25ReceivePipeline().feed_bits(
            encode_hdlc(bytes(frame))
        )

        self.assertEqual(packets, [])


def frame(payload):
    return build_ui_frame("GROUND", "ORBITL-1", payload)


class TestAX25Robustness(unittest.TestCase):

    def test_binary_payload(self):
        original = frame(bytes(range(256)))
        recovered = HDLCStreamDecoder().feed(
            encode_hdlc(original)
        )
        self.assertEqual(recovered, [original[1:-3]])

    def test_corrupted_frame_recovery(self):
        a = frame(b"SEQ=1")
        bad = bytearray(frame(b"SEQ=2"))
        c = frame(b"SEQ=3")
        bad[19] ^= 1

        stream = (
            encode_hdlc(a)
            + encode_hdlc(bytes(bad))
            + encode_hdlc(c)
        )

        recovered = HDLCStreamDecoder().feed(stream)
        self.assertEqual(
            recovered, [a[1:-3], c[1:-3]]
        )

    def test_truncated_frame_with_reset(self):
        damaged = encode_hdlc(frame(b"SEQ=10"))
        valid = frame(b"SEQ=11")

        decoder = HDLCStreamDecoder()
        self.assertEqual(
            decoder.feed(damaged[:len(damaged)//2]), []
        )
        decoder.reset()
        self.assertEqual(
            decoder.feed(encode_hdlc(valid)),
            [valid[1:-3]]
        )

    def test_automatic_resynchronization(self):
        damaged = encode_hdlc(frame(b"SEQ=20"))
        valid = frame(b"SEQ=21")
        flag = [0, 1, 1, 1, 1, 1, 1, 0]

        stream = (
            damaged[:len(damaged)//2]
            + flag
            + encode_hdlc(valid)
        )

        self.assertEqual(
            HDLCStreamDecoder().feed(stream),
            [valid[1:-3]]
        )

    def test_noise_recovery(self):
        valid = frame(b"SEQ=30")
        noise = [1,0,1,0,0,1,1,0,0,0,1,0,1]

        self.assertEqual(
            HDLCStreamDecoder().feed(
                noise + encode_hdlc(valid)
            ),
            [valid[1:-3]]
        )

    def test_missing_opening_flag(self):
        bits = encode_hdlc(frame(b"SEQ=31"))

        self.assertEqual(
            HDLCStreamDecoder().feed(bits[8:]), []
        )

    def test_missing_closing_flag(self):
        bits = encode_hdlc(frame(b"SEQ=32"))

        self.assertEqual(
            HDLCStreamDecoder().feed(bits[:-8]), []
        )


class TestHDLCBoundaryRegression(unittest.TestCase):

    def test_frame12_closing_flag(self):
        rng = random.Random(20261009)

        for _ in range(13):
            size = rng.randint(0, 512)
            payload = rng.randbytes(size)

        frame = build_ui_frame(
            "GROUND", "ORBITL-1", payload
        )

        recovered = HDLCStreamDecoder().feed(
            encode_hdlc(frame)
        )

        self.assertEqual(
            recovered,
            [frame[1:-3]]
        )


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
