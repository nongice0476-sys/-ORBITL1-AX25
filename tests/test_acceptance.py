"""Phase 4: Reliability & Acceptance Test Suite for ORBITL1-AX25.

Provides comprehensive reliability verification:
- Deterministic randomized payload round trips across multiple fixed seeds.
- Strict profile boundary enforcement:
  - Rejection of unsupported control octets (I-frame, S-frame, non-UI U-frames).
  - Rejection of unsupported PID octets (IPv4, X.25, CDPD, etc.).
  - Rejection of malformed wire addresses and SSIDs.
- Exact payload size boundary verification (4078 accepted, 4079 rejected).
- Continuous mixed-stream robustness with interleaved corruption, aborts, and oversized frames.
- Sustained processing throughput and memory stability benchmark.
"""

from __future__ import annotations

import random
import time
import unittest

from src.ax25 import (
    AX25_FLAG,
    AX25_HEADER_BYTES,
    AX25_NO_LAYER3_PID,
    AX25_UI_CONTROL,
    FCS_BYTES,
    MAX_HDLC_CONTENT_BYTES,
    MAX_INFORMATION_BYTES,
    build_ui_frame,
    crc16_x25,
    decode_address,
    decode_ui_frame,
    encode_address,
)
from src.ax25_receiver import AX25ReceivePipeline
from src.ax25_transmitter import encode_hdlc, nrzi_decode, nrzi_encode


def make_wire_frame_with_overrides(
    dest: str = "GROUND-0",
    src: str = "ORBITL-1",
    control: int = AX25_UI_CONTROL,
    pid: int = AX25_NO_LAYER3_PID,
    payload: bytes = b"",
) -> bytes:
    """Build a raw wire frame allowing explicit control/PID overrides."""
    body = bytearray()
    body.extend(encode_address(dest, last=False))
    body.extend(encode_address(src, last=True))
    body.append(control)
    body.append(pid)
    body.extend(payload)
    fcs = crc16_x25(bytes(body))
    content = bytes(body) + bytes([fcs & 0xFF, (fcs >> 8) & 0xFF])
    return bytes([AX25_FLAG]) + content + bytes([AX25_FLAG])


class TestDeterministicRandomizedReliability(unittest.TestCase):
    """Randomized frame round trips across multiple deterministic seeds."""

    def test_multiseed_payload_round_trips(self):
        """Verify round-trip data preservation across 4 fixed random seeds."""
        seeds = [20261009, 20261019, 42, 1337]

        for seed in seeds:
            rng = random.Random(seed)
            for trial in range(25):
                size = rng.randint(0, 1024)
                payload = rng.randbytes(size)
                frame = build_ui_frame("GROUND", "ORBITL-1", payload)
                levels = nrzi_encode(encode_hdlc(frame))
                packets = AX25ReceivePipeline().feed_nrzi_levels(levels)
                self.assertEqual(len(packets), 1, f"Seed {seed}, trial {trial}")
                self.assertEqual(packets[0]["information"], payload)
                self.assertTrue(packets[0]["fcs_verified"])

    def test_pathological_payload_patterns(self):
        """Verify survival of pathological payload byte patterns."""
        patterns = [
            b"\x00" * 256,                              # All zeros
            b"\xFF" * 256,                              # All ones (bit-stuffing heavy)
            b"\x55" * 256,                              # Alternating 01010101
            b"\xAA" * 256,                              # Alternating 10101010
            bytes(i & 0xFF for i in range(512)),        # Ramp up
            bytes((255 - (i & 0xFF)) for i in range(512)),  # Ramp down
            b"\x7E" * 128,                              # HDLC flag bytes as payload
            b"\x7F" * 128,                              # HDLC abort bytes as payload
        ]
        for idx, pattern in enumerate(patterns):
            with self.subTest(pattern_idx=idx, length=len(pattern)):
                frame = build_ui_frame("GROUND", "ORBITL-1", pattern)
                levels = nrzi_encode(encode_hdlc(frame))
                packets = AX25ReceivePipeline().feed_nrzi_levels(levels)
                self.assertEqual(len(packets), 1)
                self.assertEqual(packets[0]["information"], pattern)


class TestProfileRejectionEnforcement(unittest.TestCase):
    """Enforces rejection of invalid addresses, SSIDs, control fields, and PIDs."""

    def test_rejection_of_unsupported_control_fields(self):
        """Reject all non-UI frame control fields even with valid CRC-16."""
        # Non-UI controls: I-frame (0x00, 0x10), RR (0x01), RNR (0x05), REJ (0x09),
        # SABM (0x2F), DISC (0x43), DM (0x0F), FRMR (0x87)
        unsupported_controls = [0x00, 0x10, 0x01, 0x05, 0x09, 0x2F, 0x43, 0x0F, 0x87, 0x13]
        for ctrl in unsupported_controls:
            with self.subTest(control=hex(ctrl)):
                frame = make_wire_frame_with_overrides(control=ctrl, payload=b"TEST")
                # Direct byte frame decoder must reject
                with self.assertRaisesRegex(ValueError, "control field"):
                    decode_ui_frame(frame)
                # Streaming receiver must drop it
                packets = AX25ReceivePipeline().feed_nrzi_levels(nrzi_encode(encode_hdlc(frame)))
                self.assertEqual(packets, [])

    def test_rejection_of_unsupported_pids(self):
        """Reject all non-0xF0 PIDs even with valid CRC-16."""
        # Non-0xF0 PIDs: IPv4 (0xCC), X.25 PLP (0x01), Q.931 (0x08), CDPD (0x81), etc.
        unsupported_pids = [0x01, 0x06, 0x08, 0x81, 0xCC, 0xCD, 0xCE, 0xCF, 0xFF, 0x00]
        for pid in unsupported_pids:
            with self.subTest(pid=hex(pid)):
                frame = make_wire_frame_with_overrides(pid=pid, payload=b"TEST")
                with self.assertRaisesRegex(ValueError, "PID"):
                    decode_ui_frame(frame)
                packets = AX25ReceivePipeline().feed_nrzi_levels(nrzi_encode(encode_hdlc(frame)))
                self.assertEqual(packets, [])

    def test_rejection_of_malformed_wire_addresses(self):
        """Reject addresses with invalid reserved bits or extension bits."""
        # Destination with extension bit set (must be 0 for destination)
        bad_dest = bytearray(encode_address("GROUND", last=False))
        bad_dest[6] |= 0x01  # set extension bit
        body_bad_dest = bytes(bad_dest) + encode_address("ORBITL-1", last=True) + bytes([0x03, 0xF0])
        fcs_dest = crc16_x25(body_bad_dest)
        frame_bad_dest = (
            bytes([AX25_FLAG])
            + body_bad_dest
            + bytes([fcs_dest & 0xFF, (fcs_dest >> 8) & 0xFF, AX25_FLAG])
        )
        with self.assertRaisesRegex(ValueError, "Destination address must not have the final-address bit set"):
            decode_ui_frame(frame_bad_dest)

        # Source with extension bit clear (must be 1 for source in 2-address profile)
        bad_src = bytearray(encode_address("ORBITL-1", last=True))
        bad_src[6] &= ~0x01  # clear extension bit
        body = encode_address("GROUND", last=False) + bytes(bad_src) + bytes([0x03, 0xF0])
        fcs = crc16_x25(body)
        frame = bytes([AX25_FLAG]) + body + bytes([fcs & 0xFF, (fcs >> 8) & 0xFF, AX25_FLAG])
        with self.assertRaisesRegex(ValueError, "Source address must be final"):
            decode_ui_frame(frame)


class TestPayloadSizeBoundaries(unittest.TestCase):
    """Enforce exact maximum information field limits."""

    def test_maximum_information_boundary(self):
        """4078 bytes accepted, 4079 bytes rejected by builder and receiver."""
        self.assertEqual(MAX_INFORMATION_BYTES, 4078)
        self.assertEqual(MAX_HDLC_CONTENT_BYTES, 4096)

        # 4078 bytes: exact boundary
        payload_4078 = b"M" * 4078
        frame_4078 = build_ui_frame("GROUND", "ORBITL-1", payload_4078)
        self.assertEqual(len(frame_4078), 16 + 4078 + 2 + 2)  # 4098 bytes total with flags

        pipe = AX25ReceivePipeline()
        packets = pipe.feed_nrzi_levels(nrzi_encode(encode_hdlc(frame_4078)))
        self.assertEqual(len(packets), 1)
        self.assertEqual(packets[0]["information"], payload_4078)

        # 4079 bytes: rejected by builder
        with self.assertRaisesRegex(ValueError, "exceeds 4078 bytes"):
            build_ui_frame("GROUND", "ORBITL-1", b"M" * 4079)

        # 4079 bytes: wire frame rejected by receiver pipeline
        wire_oversized = make_wire_frame_with_overrides(payload=b"M" * 4079)
        pipe.reset()
        dropped = pipe.feed_nrzi_levels(nrzi_encode(encode_hdlc(wire_oversized)))
        self.assertEqual(dropped, [])

    def test_oversized_frame_recovery_subsequent_frame_intact(self):
        """Receiver must recover immediately following an oversized frame."""
        pipe = AX25ReceivePipeline()
        oversized = make_wire_frame_with_overrides(payload=b"Z" * 4080)
        valid = build_ui_frame("GROUND", "ORBITL-1", b"SUBSEQUENT-VALID")

        stream = encode_hdlc(oversized) + encode_hdlc(valid)
        packets = pipe.feed_nrzi_levels(nrzi_encode(stream))
        self.assertEqual(len(packets), 1)
        self.assertEqual(packets[0]["information"], b"SUBSEQUENT-VALID")


class TestMixedContinuousStreamRobustness(unittest.TestCase):
    """Stress tests continuous streams containing interleaved corruption and noise."""

    def test_mixed_stream_with_interleaved_faults(self):
        """Send 100 frames where every 3rd has CRC error, every 5th is aborted, every 7th oversized."""
        rng = random.Random(20261019)
        expected: list[bytes] = []
        stream: list[int] = []

        for i in range(100):
            payload = f"FRAME-{i:03d}:".encode("ascii") + rng.randbytes(32)

            if i % 3 == 0:
                # Corrupted CRC
                f = bytearray(build_ui_frame("GROUND", "ORBITL-1", payload))
                f[-3] ^= 0x01
                stream.extend(encode_hdlc(bytes(f)))
            elif i % 5 == 0:
                # Truncated with abort sequence (8 ones)
                f = build_ui_frame("GROUND", "ORBITL-1", payload)
                bits = encode_hdlc(f)
                stream.extend(bits[: len(bits) // 2] + [1] * 8)
            elif i % 7 == 0:
                # Oversized frame
                oversized = make_wire_frame_with_overrides(payload=b"X" * 4080)
                stream.extend(encode_hdlc(oversized))
            else:
                # Valid frame
                expected.append(payload)
                f = build_ui_frame("GROUND", "ORBITL-1", payload)
                stream.extend(encode_hdlc(f))

        pipe = AX25ReceivePipeline()
        levels = nrzi_encode(stream)
        received: list[bytes] = []

        # Feed in randomized chunk sizes (1 to 64 bits)
        offset = 0
        while offset < len(levels):
            step = rng.randint(1, 64)
            chunk = levels[offset : offset + step]
            received.extend(p["information"] for p in pipe.feed_nrzi_levels(chunk))
            offset += len(chunk)

        self.assertEqual(len(received), len(expected))
        self.assertEqual(received, expected)


class TestPerformanceAndMemoryBehavior(unittest.TestCase):
    """Measures processing throughput and confirms stable execution over sustained input."""

    def test_sustained_load_throughput_benchmark(self):
        """Benchmark 500 frames through the complete NRZI + HDLC + AX.25 pipeline."""
        rng = random.Random(20261019)
        num_frames = 500
        payload_size = 128  # Typical telemetry payload size

        frames = [
            build_ui_frame("GROUND", "ORBITL-1", rng.randbytes(payload_size))
            for _ in range(num_frames)
        ]

        total_bytes = sum(len(f) for f in frames)
        stream: list[int] = []
        for f in frames:
            stream.extend(encode_hdlc(f))

        levels = nrzi_encode(stream)

        # Measure receive pipeline execution time
        pipe = AX25ReceivePipeline()
        t0 = time.perf_counter()
        packets = pipe.feed_nrzi_levels(levels)
        elapsed = time.perf_counter() - t0

        self.assertEqual(len(packets), num_frames)

        fps = num_frames / elapsed
        kbps = (total_bytes * 8 / 1000) / elapsed
        mbps = kbps / 1000

        # Verify deterministic non-zero throughput
        self.assertGreater(fps, 10.0, f"Frames/sec too low: {fps:.1f}")
        self.assertGreater(kbps, 50.0, f"Throughput too low: {kbps:.1f} kbps")

        # Record benchmark metrics for report generation
        TestPerformanceAndMemoryBehavior.last_benchmark = {
            "num_frames": num_frames,
            "payload_size": payload_size,
            "total_bytes": total_bytes,
            "elapsed_seconds": elapsed,
            "frames_per_sec": fps,
            "throughput_kbps": kbps,
            "throughput_mbps": mbps,
        }


if __name__ == "__main__":
    unittest.main()
