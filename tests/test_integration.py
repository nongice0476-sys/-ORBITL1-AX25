"""Phase 3: Integration & Interoperability Tests for ORBITL1-AX25.

Exercises the complete end-to-end pipeline:
  Flight software payload (bytes)
  -> build_ui_frame() [AX.25 frame + flags + CRC-16/X-25 FCS]
  -> encode_hdlc() [Flag + HDLC bit stuffing + Flag]
  -> nrzi_encode() [NRZI line levels]
  -> AX25ReceivePipeline.feed_nrzi_levels() [NRZI decode + HDLC stream decode + AX.25 parse]
  -> Validated AX.25 UI packet dictionary.

Includes:
- Boundary conditions and long runs of 1s (bit stuffing stress).
- Consecutive frames (separate flags, shared flags, multiple idle flags).
- Arbitrary streaming chunk boundaries (1 bit, 3 bits, 7 bits, 13 bits, etc.).
- Robust recovery from corrupted FCS, truncated frames, HDLC aborts, and oversized frames.
- Independent interoperability evidence: CRC-16/X-25 known-answer vectors,
  AX.25 v2.2 specification address vectors, and an independent reference model.
"""

from __future__ import annotations

import random
import unittest

from src.ax25 import (
    AX25_FLAG,
    AX25_NO_LAYER3_PID,
    AX25_UI_CONTROL,
    MAX_INFORMATION_BYTES,
    build_ui_frame,
    crc16_x25,
    decode_address,
    decode_ui_frame,
    encode_address,
)
from src.ax25_hdlc import HDLCStreamDecoder
from src.ax25_receiver import AX25ReceivePipeline
from src.ax25_transmitter import (
    bit_stuff,
    bytes_to_bits,
    encode_hdlc,
    nrzi_decode,
    nrzi_encode,
)


class IndependentAX25Reference:
    """Independent reference model for AX.25 UI frame, HDLC, and NRZI.

    Implemented independently from first principles following ISO 3309 and
    AX.25 v2.2 specifications to provide cross-implementation verification.
    """

    @staticmethod
    def calculate_crc16_x25(data: bytes) -> int:
        """Bitwise calculation of CRC-16/X-25 without lookup tables."""
        crc = 0xFFFF
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 1:
                    crc = (crc >> 1) ^ 0x8408
                else:
                    crc >>= 1
        return crc ^ 0xFFFF

    @staticmethod
    def encode_callsign(call: str, ssid: int, is_last: bool) -> bytes:
        """Encode 7-byte address field according to AX.25 v2.2 section 3.12."""
        if "-" in call:
            call_base = call.split("-")[0]
        else:
            call_base = call
        call_padded = call_base.upper().ljust(6)[:6]
        out = bytearray(ord(c) << 1 for c in call_padded)
        ssid_octet = 0x60 | ((ssid & 0x0F) << 1) | (1 if is_last else 0)
        out.append(ssid_octet)
        return bytes(out)

    @staticmethod
    def build_frame(dest: str, dest_ssid: int, src: str, src_ssid: int, info: bytes) -> bytes:
        """Construct full AX.25 UI frame with flags and FCS."""
        body = bytearray()
        body.extend(IndependentAX25Reference.encode_callsign(dest, dest_ssid, is_last=False))
        body.extend(IndependentAX25Reference.encode_callsign(src, src_ssid, is_last=True))
        body.append(0x03)  # UI control
        body.append(0xF0)  # PID no layer 3
        body.extend(info)
        fcs = IndependentAX25Reference.calculate_crc16_x25(bytes(body))
        body.append(fcs & 0xFF)
        body.append((fcs >> 8) & 0xFF)
        return bytes([0x7E]) + bytes(body) + bytes([0x7E])

    @staticmethod
    def bit_stuff(bits: list[int]) -> list[int]:
        stuffed: list[int] = []
        ones = 0
        for b in bits:
            stuffed.append(b)
            if b == 1:
                ones += 1
                if ones == 5:
                    stuffed.append(0)
                    ones = 0
            else:
                ones = 0
        return stuffed

    @staticmethod
    def bit_unstuff(bits: list[int]) -> list[int]:
        unstuffed: list[int] = []
        ones = 0
        i = 0
        while i < len(bits):
            b = bits[i]
            if ones == 5:
                if b == 0:
                    # Stuffed zero: discard and reset counter
                    ones = 0
                    i += 1
                    continue
                else:
                    # 6 or more ones: flag or abort
                    unstuffed.append(b)
                    ones += 1
            else:
                unstuffed.append(b)
                if b == 1:
                    ones += 1
                else:
                    ones = 0
            i += 1
        return unstuffed


class TestEndToEndIntegration(unittest.TestCase):
    """End-to-end integration covering the entire transmit and receive pipeline."""

    def test_e2e_empty_payload(self):
        dest, src, payload = "GROUND", "ORBITL-1", b""
        frame = build_ui_frame(dest, src, payload)
        levels = nrzi_encode(encode_hdlc(frame))
        packets = AX25ReceivePipeline().feed_nrzi_levels(levels)
        self.assertEqual(len(packets), 1)
        self.assertEqual(packets[0]["information"], payload)
        self.assertEqual(packets[0]["destination"]["callsign"], "GROUND")
        self.assertEqual(packets[0]["source"]["callsign"], "ORBITL")
        self.assertEqual(packets[0]["source"]["ssid"], 1)
        self.assertTrue(packets[0]["fcs_verified"])

    def test_e2e_ordinary_telemetry_payload(self):
        dest, src = "GROUND-0", "ORBITL-1"
        payload = b"SEQ=42,V_BAT=3.92V,I_BUS=0.45A,TEMP=24.5C,STATE=NOMINAL"
        frame = build_ui_frame(dest, src, payload)
        levels = nrzi_encode(encode_hdlc(frame))
        packets = AX25ReceivePipeline().feed_nrzi_levels(levels)
        self.assertEqual(len(packets), 1)
        self.assertEqual(packets[0]["information"], payload)
        self.assertTrue(packets[0]["fcs_verified"])

    def test_e2e_bit_stuffing_stress_long_ones(self):
        """Stress bit stuffing with payloads containing dense sequences of 1 bits."""
        patterns = [
            b"\xFF" * 10,
            b"\xFF" * 50,
            b"\x7E" * 25,
            b"\x3F\x7F\xFF" * 15,
            bytes([0xFF, 0xFE, 0xFC, 0xF8, 0xF0, 0xE0, 0xC0, 0x80] * 8),
        ]
        for idx, payload in enumerate(patterns):
            with self.subTest(pattern_idx=idx, length=len(payload)):
                frame = build_ui_frame("GROUND", "ORBITL-1", payload)
                hdlc_bits = encode_hdlc(frame)
                # Verify bit stuffing actually inserted zeros
                raw_body_bits = bytes_to_bits(frame[1:-1])
                stuffed_body_bits = bit_stuff(raw_body_bits)
                self.assertGreater(len(stuffed_body_bits), len(raw_body_bits))

                levels = nrzi_encode(hdlc_bits)
                packets = AX25ReceivePipeline().feed_nrzi_levels(levels)
                self.assertEqual(len(packets), 1)
                self.assertEqual(packets[0]["information"], payload)
                self.assertTrue(packets[0]["fcs_verified"])

    def test_e2e_boundary_payload_sizes(self):
        """Verify boundary payload sizes up to the exact maximum limit (4078 bytes)."""
        sizes = [0, 1, 2, 7, 8, 128, 255, 256, 512, 1024, 2048, 4077, 4078]
        for size in sizes:
            with self.subTest(size=size):
                payload = bytes((i & 0xFF) for i in range(size))
                frame = build_ui_frame("GROUND", "ORBITL-1", payload)
                self.assertEqual(len(frame), 16 + size + 2 + 2)  # header + info + fcs + flags

                levels = nrzi_encode(encode_hdlc(frame))
                packets = AX25ReceivePipeline().feed_nrzi_levels(levels)
                self.assertEqual(len(packets), 1)
                self.assertEqual(packets[0]["information"], payload)
                self.assertTrue(packets[0]["fcs_verified"])

    def test_e2e_multiple_consecutive_frames_back_to_back(self):
        """Verify transmission of multiple consecutive frames with standard flags."""
        frames = [
            build_ui_frame("GROUND", "ORBITL-1", f"FRAME-{i:03d}".encode("ascii"))
            for i in range(10)
        ]
        bitstream: list[int] = []
        for f in frames:
            bitstream.extend(encode_hdlc(f))

        levels = nrzi_encode(bitstream)
        packets = AX25ReceivePipeline().feed_nrzi_levels(levels)
        self.assertEqual(len(packets), 10)
        for i, pkt in enumerate(packets):
            self.assertEqual(pkt["information"], f"FRAME-{i:03d}".encode("ascii"))
            self.assertTrue(pkt["fcs_verified"])

    def test_e2e_shared_delimiter_flag(self):
        """Verify that two frames sharing a single 0x7E delimiter flag are both decoded."""
        f1 = build_ui_frame("GROUND", "ORBITL-1", b"MSG-A")
        f2 = build_ui_frame("GROUND", "ORBITL-1", b"MSG-B")

        # Encode f1 without its trailing flag, immediately followed by f2
        bits_f1 = encode_hdlc(f1)[:-8]  # strip trailing flag
        bits_f2 = encode_hdlc(f2)       # includes leading and trailing flag
        shared_stream = bits_f1 + bits_f2

        levels = nrzi_encode(shared_stream)
        packets = AX25ReceivePipeline().feed_nrzi_levels(levels)
        self.assertEqual(len(packets), 2)
        self.assertEqual(packets[0]["information"], b"MSG-A")
        self.assertEqual(packets[1]["information"], b"MSG-B")

    def test_e2e_multiple_idle_flags_between_frames(self):
        """Verify that multiple idle 0x7E flags between frames are cleanly ignored."""
        f1 = build_ui_frame("GROUND", "ORBITL-1", b"TELEMETRY-1")
        f2 = build_ui_frame("GROUND", "ORBITL-1", b"TELEMETRY-2")
        idle_flags = bytes_to_bits(b"\x7E\x7E\x7E\x7E\x7E")

        stream = encode_hdlc(f1) + idle_flags + encode_hdlc(f2)
        levels = nrzi_encode(stream)
        packets = AX25ReceivePipeline().feed_nrzi_levels(levels)
        self.assertEqual(len(packets), 2)
        self.assertEqual([p["information"] for p in packets], [b"TELEMETRY-1", b"TELEMETRY-2"])

    def test_e2e_arbitrary_streaming_chunk_sizes(self):
        """Verify that feeding NRZI levels in prime or arbitrary chunk sizes retains state."""
        payload = b"ORBITL1-ARBITRARY-STREAMING-CHUNK-TEST"
        frame = build_ui_frame("GROUND", "ORBITL-1", payload)
        levels = nrzi_encode(encode_hdlc(frame))

        chunk_sizes = [1, 2, 3, 5, 7, 11, 13, 17, 31, 64, 128]
        for chunk_size in chunk_sizes:
            with self.subTest(chunk_size=chunk_size):
                pipe = AX25ReceivePipeline()
                received = []
                for offset in range(0, len(levels), chunk_size):
                    chunk = levels[offset : offset + chunk_size]
                    received.extend(pipe.feed_nrzi_levels(chunk))
                self.assertEqual(len(received), 1)
                self.assertEqual(received[0]["information"], payload)
                self.assertTrue(received[0]["fcs_verified"])

    def test_e2e_split_across_critical_boundaries(self):
        """Specifically split chunks at exact structural boundaries."""
        payload = b"CRITICAL-BOUNDARY-SPLIT"
        frame = build_ui_frame("GROUND", "ORBITL-1", payload)
        raw_bits = encode_hdlc(frame)
        levels = nrzi_encode(raw_bits)

        # Split directly at bit positions 8 (flag end), 16, 64 (address), len-24 (FCS start)
        split_points = [8, 16, 64, 112, len(levels) - 24, len(levels) - 8]
        pipe = AX25ReceivePipeline()
        received = []
        prev = 0
        for sp in split_points:
            chunk = levels[prev:sp]
            received.extend(pipe.feed_nrzi_levels(chunk))
            prev = sp
        received.extend(pipe.feed_nrzi_levels(levels[prev:]))
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0]["information"], payload)


class TestErrorRecoveryAndRejection(unittest.TestCase):
    """Robustness against corrupted input, aborts, and boundary violations."""

    def test_corrupted_fcs_single_and_double_bit_flips(self):
        frame = build_ui_frame("GROUND", "ORBITL-1", b"FCS-TEST")
        body_with_fcs = frame[1:-1]

        # Test single-bit flips on FCS bytes (last two bytes of content)
        for bit_pos in [0, 1, 7, 8, 15]:
            corrupted = bytearray(body_with_fcs)
            byte_idx = -2 if bit_pos < 8 else -1
            corrupted[byte_idx] ^= 1 << (bit_pos % 8)
            wire_frame = bytes([0x7E]) + bytes(corrupted) + bytes([0x7E])
            levels = nrzi_encode(encode_hdlc(wire_frame))
            packets = AX25ReceivePipeline().feed_nrzi_levels(levels)
            self.assertEqual(packets, [], f"Bit flip at position {bit_pos} was not rejected")

    def test_corrupted_fcs_inverted(self):
        frame = build_ui_frame("GROUND", "ORBITL-1", b"INVERT-FCS")
        corrupted = bytearray(frame[1:-1])
        corrupted[-2] ^= 0xFF
        corrupted[-1] ^= 0xFF
        wire = bytes([0x7E]) + bytes(corrupted) + bytes([0x7E])
        packets = AX25ReceivePipeline().feed_nrzi_levels(nrzi_encode(encode_hdlc(wire)))
        self.assertEqual(packets, [])

    def test_missing_opening_flag(self):
        frame = build_ui_frame("GROUND", "ORBITL-1", b"NO-OPENING-FLAG")
        bits = encode_hdlc(frame)[8:]  # remove opening 0x7E
        packets = AX25ReceivePipeline().feed_nrzi_levels(nrzi_encode(bits))
        self.assertEqual(packets, [])

    def test_missing_closing_flag(self):
        frame = build_ui_frame("GROUND", "ORBITL-1", b"NO-CLOSING-FLAG")
        bits = encode_hdlc(frame)[:-8]  # remove closing 0x7E
        packets = AX25ReceivePipeline().feed_nrzi_levels(nrzi_encode(bits))
        self.assertEqual(packets, [])

    def test_hdlc_abort_sequence_handling_and_recovery(self):
        """HDLC abort: 7 or more contiguous 1s must abort current frame and recover."""
        valid_a = build_ui_frame("GROUND", "ORBITL-1", b"BEFORE-ABORT")
        incomplete = build_ui_frame("GROUND", "ORBITL-1", b"ABORTED-FRAME")
        valid_b = build_ui_frame("GROUND", "ORBITL-1", b"AFTER-ABORT")

        # Create stream: valid_a + truncated incomplete + 8 ones (abort) + valid_b
        stream = (
            encode_hdlc(valid_a)
            + encode_hdlc(incomplete)[: len(encode_hdlc(incomplete)) // 2]
            + [1] * 8
            + encode_hdlc(valid_b)
        )
        levels = nrzi_encode(stream)
        packets = AX25ReceivePipeline().feed_nrzi_levels(levels)
        self.assertEqual(len(packets), 2)
        self.assertEqual(packets[0]["information"], b"BEFORE-ABORT")
        self.assertEqual(packets[1]["information"], b"AFTER-ABORT")

    def test_oversized_frame_rejection_and_pipeline_recovery(self):
        """Oversized frame (> 4096 bytes HDLC content) must be dropped and recover."""
        oversized_payload = b"X" * 4079  # 16 header + 4079 info + 2 FCS = 4097 bytes
        # Construct raw wire frame directly because build_ui_frame intentionally rejects it
        body = bytearray()
        body.extend(encode_address("GROUND", last=False))
        body.extend(encode_address("ORBITL-1", last=True))
        body.extend((AX25_UI_CONTROL, AX25_NO_LAYER3_PID))
        body.extend(oversized_payload)
        fcs = crc16_x25(bytes(body))
        content = bytes(body) + bytes([fcs & 0xFF, (fcs >> 8) & 0xFF])
        oversized_wire = bytes([0x7E]) + content + bytes([0x7E])

        valid = build_ui_frame("GROUND", "ORBITL-1", b"VALID-AFTER-OVERSIZED")

        stream = encode_hdlc(oversized_wire) + encode_hdlc(valid)
        levels = nrzi_encode(stream)
        packets = AX25ReceivePipeline().feed_nrzi_levels(levels)
        self.assertEqual(len(packets), 1)
        self.assertEqual(packets[0]["information"], b"VALID-AFTER-OVERSIZED")

    def test_continuous_stream_recovery_after_random_noise(self):
        """Verify pipeline resynchronizes on valid frame after bursts of line noise."""
        rng = random.Random(20261019)
        valid_frame = build_ui_frame("GROUND", "ORBITL-1", b"CLEAN-AFTER-NOISE")
        valid_bits = encode_hdlc(valid_frame)

        for noise_len in [10, 50, 100, 500]:
            noise = [rng.randint(0, 1) for _ in range(noise_len)]
            stream = noise + valid_bits
            levels = nrzi_encode(stream)
            pipe = AX25ReceivePipeline()
            packets = pipe.feed_nrzi_levels(levels)
            self.assertEqual(len(packets), 1)
            self.assertEqual(packets[0]["information"], b"CLEAN-AFTER-NOISE")

    def test_preservation_of_frame_ordering_and_content(self):
        """Ensure 50 frames with variable sizes are recovered in exact sequence."""
        rng = random.Random(20261019)
        expected: list[bytes] = []
        stream: list[int] = []

        for seq in range(50):
            size = rng.randint(0, 256)
            payload = f"SEQ={seq:04d}:".encode("ascii") + rng.randbytes(size)
            expected.append(payload)
            frame = build_ui_frame("GROUND", "ORBITL-1", payload)
            stream.extend(encode_hdlc(frame))

        levels = nrzi_encode(stream)
        pipe = AX25ReceivePipeline()
        received: list[bytes] = []
        offset = 0
        while offset < len(levels):
            step = rng.randint(5, 53)
            chunk = levels[offset : offset + step]
            received.extend(p["information"] for p in pipe.feed_nrzi_levels(chunk))
            offset += len(chunk)

        self.assertEqual(len(received), 50)
        self.assertEqual(received, expected)


class TestIndependentInteroperability(unittest.TestCase):
    """Independent interoperability evidence and reference vector validation."""

    def test_crc16_x25_authoritative_vectors(self):
        """Verify CRC-16/X-25 standard catalog test vectors.

        Standard parameters:
          Polynomial: 0x1021 (reflected: 0x8408)
          Initial remainder: 0xFFFF
          Reflect in/out: True
          Final XOR: 0xFFFF
        """
        # Universal ISO/IEC 3309 and ITU-T X.25 standard test string:
        self.assertEqual(crc16_x25(b"123456789"), 0x906E)

        # Empty vector: 0xFFFF ^ 0xFFFF = 0x0000
        self.assertEqual(crc16_x25(b""), 0x0000)

        # Known single-byte and text vectors:
        self.assertEqual(crc16_x25(b"A"), 0xA3F5)
        self.assertEqual(crc16_x25(b"TEST"), 0x89D1)

        # Cross-check against independent bitwise reference implementation
        for test_bytes in [b"", b"123456789", b"A", b"ORBITL1-CRC-VECTOR", bytes(range(256))]:
            ref_crc = IndependentAX25Reference.calculate_crc16_x25(test_bytes)
            self.assertEqual(crc16_x25(test_bytes), ref_crc)

    def test_crc16_x25_fcs_residual_constant(self):
        """Verifies mathematical HDLC FCS residual check (0xF0B8).

        In ISO 3309 / AX.25, appending the 16-bit FCS (low byte first) to the
        data and computing the CRC without final inversion yields the fixed
        constant residue 0xF0B8.
        """
        from src.vendor.mobilinkd.CRC import CRC16CCITT

        data = b"ORBITL1-FCS-RESIDUAL-CHECK"
        fcs = crc16_x25(data)
        # Transmit low byte first
        wire_data = data + bytes([fcs & 0xFF, (fcs >> 8) & 0xFF])

        crc_calc = CRC16CCITT()
        residual = crc_calc.compute(wire_data.decode("latin-1"))
        self.assertEqual(residual, 0xF0B8)

    def test_ax25_v22_spec_address_vectors(self):
        """Verify AX.25 v2.2 specification address field encoding (Section 3.12)."""
        # AX.25 Spec Figure 3.5: Destination NJ7P, SSID=0, not last
        nj7p = encode_address("NJ7P-0", last=False)
        self.assertEqual(nj7p, bytes.fromhex("9C 94 6E A0 40 40 60"))
        call, ssid, last = decode_address(nj7p)
        self.assertEqual(call, "NJ7P")
        self.assertEqual(ssid, 0)
        self.assertFalse(last)

        # AX.25 Spec Figure 3.6: Source N7LEM, SSID=0, last
        n7lem = encode_address("N7LEM-0", last=True)
        self.assertEqual(n7lem, bytes.fromhex("9C 6E 98 8A 9A 40 61"))
        call, ssid, last = decode_address(n7lem)
        self.assertEqual(call, "N7LEM")
        self.assertEqual(ssid, 0)
        self.assertTrue(last)

        # Project standard addresses
        orbitl = encode_address("ORBITL-1", last=True)
        self.assertEqual(orbitl, bytes.fromhex("9E A4 84 92 A8 98 63"))
        ground = encode_address("GROUND-0", last=False)
        self.assertEqual(ground, bytes.fromhex("8E A4 9E AA 9C 88 60"))

    def test_independent_reference_model_cross_validation(self):
        """Cross-validate project implementation against IndependentAX25Reference."""
        dest, src, payload = "GROUND", "ORBITL-1", b"CROSS-VALIDATION-VECTOR"

        # 1. Compare frame builder output
        project_frame = build_ui_frame(dest, src, payload)
        ref_frame = IndependentAX25Reference.build_frame(dest, 0, src, 1, payload)
        self.assertEqual(project_frame, ref_frame)

        # 2. Compare bit stuffing
        raw_bits = bytes_to_bits(project_frame[1:-1])
        project_stuffed = bit_stuff(raw_bits)
        ref_stuffed = IndependentAX25Reference.bit_stuff(raw_bits)
        self.assertEqual(project_stuffed, ref_stuffed)

        # 3. Compare unstuffing
        ref_unstuffed = IndependentAX25Reference.bit_unstuff(ref_stuffed)
        self.assertEqual(ref_unstuffed, raw_bits)

        # 4. Compare NRZI encoding
        nrzi_levels = nrzi_encode(project_stuffed)
        recovered_bits = nrzi_decode(nrzi_levels)
        self.assertEqual(recovered_bits, project_stuffed)

    def test_wire_conventions_lsb_first_and_nrzi_transitions(self):
        """Verify LSB-first bit ordering and NRZI line level transitions.

        AX.25 v2.2 Section 3.8: All octets (except FCS) are transmitted LSB-first.
        NRZI: '0' bit causes a transition; '1' bit causes no transition.
        """
        # Octet 0x03 (00000011b): LSB-first is [1, 1, 0, 0, 0, 0, 0, 0]
        self.assertEqual(bytes_to_bits(b"\x03"), [1, 1, 0, 0, 0, 0, 0, 0])

        # Octet 0x7E (01111110b): LSB-first is [0, 1, 1, 1, 1, 1, 1, 0]
        self.assertEqual(bytes_to_bits(b"\x7E"), [0, 1, 1, 1, 1, 1, 1, 0])

        # NRZI: starting at level 0:
        # bit 0 -> toggle to 1
        # bit 1 -> hold at 1
        # bit 0 -> toggle to 0
        bits = [0, 1, 0]
        levels = nrzi_encode(bits, initial_level=0)
        self.assertEqual(levels, [1, 1, 0])
        self.assertEqual(nrzi_decode(levels, initial_level=0), bits)


if __name__ == "__main__":
    unittest.main()
