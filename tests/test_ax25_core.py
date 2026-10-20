import unittest

from src.ax25 import (
    parse_address,
    encode_address,
    decode_address,
    crc16_x25,
    build_ui_frame,
    decode_ui_frame,
)


class TestAX25Address(unittest.TestCase):

    def test_parse_address(self):
        callsign, ssid = parse_address("ORBITL-1")

        self.assertEqual(callsign, "ORBITL")
        self.assertEqual(ssid, 1)


    def test_destination_encoding(self):
        encoded = encode_address(
            "GROUND-0",
            last=False
        )

        expected = bytes.fromhex(
            "8E A4 9E AA 9C 88 60"
        )

        self.assertEqual(
            encoded,
            expected
        )


    def test_source_encoding(self):
        encoded = encode_address(
            "ORBITL-1",
            last=True
        )

        expected = bytes.fromhex(
            "9E A4 84 92 A8 98 63"
        )

        self.assertEqual(
            encoded,
            expected
        )


    def test_address_round_trip(self):
        encoded = encode_address(
            "ORBITL-1",
            last=True
        )

        callsign, ssid, last = decode_address(
            encoded
        )

        self.assertEqual(callsign, "ORBITL")
        self.assertEqual(ssid, 1)
        self.assertTrue(last)


    def test_invalid_callsign(self):
        with self.assertRaises(ValueError):
            parse_address(
                "TOOLONG-1"
            )


    def test_invalid_ssid(self):
        with self.assertRaises(ValueError):
            parse_address(
                "ORBITL-16"
            )


class TestAX25Frame(unittest.TestCase):

    def setUp(self):

        self.destination = "GROUND-0"
        self.source = "ORBITL-1"

        self.telemetry = (
            "SEQ=1,"
            "BAT=7.60,"
            "TEMP=31.4,"
            "MODE=NOMINAL"
        )

        self.frame = build_ui_frame(
            destination=self.destination,
            source=self.source,
            information=self.telemetry.encode("ascii")
        )


    def test_frame_length(self):
        self.assertEqual(
            len(self.frame),
            57
        )


    def test_frame_flags(self):
        self.assertEqual(
            self.frame[0],
            0x7E
        )

        self.assertEqual(
            self.frame[-1],
            0x7E
        )


    def test_known_fcs(self):
        # Remove opening flag, FCS, and closing flag.
        frame_body = self.frame[1:-3]

        calculated = crc16_x25(
            frame_body
        )

        self.assertEqual(
            calculated,
            0xE1E2
        )


    def test_encode_decode_round_trip(self):

        decoded = decode_ui_frame(
            self.frame
        )

        self.assertEqual(
            decoded["destination"]["callsign"],
            "GROUND"
        )

        self.assertEqual(
            decoded["destination"]["ssid"],
            0
        )

        self.assertEqual(
            decoded["source"]["callsign"],
            "ORBITL"
        )

        self.assertEqual(
            decoded["source"]["ssid"],
            1
        )

        self.assertEqual(
            decoded["control"],
            0x03
        )

        self.assertEqual(
            decoded["pid"],
            0xF0
        )

        self.assertEqual(
            decoded["information"].decode("ascii"),
            self.telemetry
        )

        self.assertEqual(
            decoded["received_fcs"],
            decoded["calculated_fcs"]
        )


    def test_corrupted_frame_rejected(self):

        corrupted = bytearray(
            self.frame
        )

        # Flip one bit inside the Information Field.
        corrupted[20] ^= 0x01

        with self.assertRaises(ValueError):
            decode_ui_frame(
                bytes(corrupted)
            )


    def test_missing_opening_flag(self):

        broken = bytearray(
            self.frame
        )

        broken[0] = 0x00

        with self.assertRaises(ValueError):
            decode_ui_frame(
                bytes(broken)
            )


    def test_missing_closing_flag(self):

        broken = bytearray(
            self.frame
        )

        broken[-1] = 0x00

        with self.assertRaises(ValueError):
            decode_ui_frame(
                bytes(broken)
            )


if __name__ == "__main__":
    unittest.main()

class TestAX25ProductionValidation(unittest.TestCase):

    def test_address_rejects_empty_and_invalid_characters(self):
        for address in ("", "-1", "ORBIT-1 ", "ORBIT_1", "ÄBC"):
            with self.subTest(address=address):
                with self.assertRaises((TypeError, ValueError)):
                    parse_address(address)

    def test_address_rejects_non_string(self):
        with self.assertRaises(TypeError):
            parse_address(None)

    def test_address_rejects_non_decimal_or_out_of_range_ssid(self):
        for address in ("ORBITL-x", "ORBITL--1", "ORBITL-16", "ORBITL-999"):
            with self.subTest(address=address):
                with self.assertRaises(ValueError):
                    parse_address(address)

    def test_decode_address_rejects_invalid_low_bits(self):
        invalid = bytearray(encode_address("ORBITL-1", last=True))
        invalid[0] |= 1
        with self.assertRaises(ValueError):
            decode_address(bytes(invalid))

    def test_decode_address_rejects_reserved_bits_clear(self):
        invalid = bytearray(encode_address("ORBITL-1", last=True))
        invalid[6] &= ~0x20
        with self.assertRaises(ValueError):
            decode_address(bytes(invalid))

    def test_frame_builder_requires_bytes_like_information(self):
        with self.assertRaises(TypeError):
            build_ui_frame("GROUND", "ORBITL-1", "not bytes")

    def test_frame_builder_enforces_maximum_information(self):
        maximum = b"A" * 4078
        frame = build_ui_frame("GROUND", "ORBITL-1", maximum)
        self.assertEqual(len(frame), 4098)
        self.assertEqual(decode_ui_frame(frame)["information"], maximum)

        with self.assertRaises(ValueError):
            build_ui_frame("GROUND", "ORBITL-1", b"A" * 4079)

    def test_frame_decoder_rejects_non_bytes_input(self):
        with self.assertRaises(TypeError):
            decode_ui_frame("not bytes")

    def test_frame_decoder_rejects_unsupported_control_with_valid_fcs(self):
        frame = bytearray(build_ui_frame("GROUND", "ORBITL-1", b"DATA"))
        body = bytearray(frame[1:-3])
        body[14] = 0x13
        fcs = crc16_x25(bytes(body))
        malformed = bytes((0x7E,)) + bytes(body) + bytes((fcs & 0xFF, fcs >> 8, 0x7E))
        with self.assertRaisesRegex(ValueError, "control field"):
            decode_ui_frame(malformed)

    def test_verified_body_parser_is_shared_with_receiver(self):
        frame = build_ui_frame("GROUND", "ORBITL-1", b"PAYLOAD")
        decoded_frame = decode_ui_frame(frame)
        packet = __import__("src.ax25", fromlist=["decode_verified_ui_body"]).decode_verified_ui_body(
            frame[1:-3]
        )
        self.assertEqual(packet["information"], decoded_frame["information"])
        self.assertTrue(packet["fcs_verified"])


class TestAX25SpecificationEdgeCases(unittest.TestCase):
    def test_address_rejects_non_ascii_that_uppercases_to_ascii(self):
        # Unicode long-s and dotless-i uppercase to ordinary ASCII letters.
        for address in ("ORBITſ", "ORBITı", "KILO"):
            with self.subTest(address=address):
                with self.assertRaises(ValueError):
                    parse_address(address)

    def test_wire_callsign_must_be_uppercase_ascii(self):
        # Build a frame, change the destination's first character to lowercase
        # on the wire, and recompute FCS so this checks address syntax rather
        # than merely failing the CRC check.
        frame = bytearray(build_ui_frame("GROUND", "ORBITL-1", b"EDGE"))
        body = bytearray(frame[1:-3])
        body[0] = ord("g") << 1
        fcs = crc16_x25(bytes(body))
        malformed = (
            bytes((0x7E,)) + bytes(body)
            + bytes((fcs & 0xFF, (fcs >> 8) & 0xFF, 0x7E))
        )
        with self.assertRaisesRegex(ValueError, "uppercase ASCII"):
            decode_ui_frame(malformed)

    def test_uppercase_wire_callsign_still_decodes(self):
        frame = build_ui_frame("GROUND-0", "ORBITL-1", b"OK")
        decoded = decode_ui_frame(frame)
        self.assertEqual(decoded["destination"]["callsign"], "GROUND")
        self.assertEqual(decoded["source"]["callsign"], "ORBITL")

class TestAX25AcceptanceVectors(unittest.TestCase):
    def test_crc16_x25_standard_check_value(self):
        # Standard CRC-16/X-25 check value (independent known-answer vector).
        self.assertEqual(crc16_x25(b"123456789"), 0x906E)

    def test_empty_information_field_round_trip(self):
        frame = build_ui_frame("GROUND-15", "ORBITL-0", b"")
        decoded = decode_ui_frame(frame)
        self.assertEqual(decoded["destination"], {"callsign": "GROUND", "ssid": 15})
        self.assertEqual(decoded["source"], {"callsign": "ORBITL", "ssid": 0})
        self.assertEqual(decoded["information"], b"")

    def test_frame_decoder_rejects_unsupported_pid_with_valid_fcs(self):
        frame = bytearray(build_ui_frame("GROUND", "ORBITL-1", b"DATA"))
        body = bytearray(frame[1:-3])
        body[15] = 0xCC
        fcs = crc16_x25(bytes(body))
        malformed = bytes((0x7E,)) + bytes(body) + bytes((fcs & 0xFF, fcs >> 8, 0x7E))
        with self.assertRaisesRegex(ValueError, "PID"):
            decode_ui_frame(malformed)
