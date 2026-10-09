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