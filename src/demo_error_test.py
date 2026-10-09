from ax25 import build_ui_frame, decode_ui_frame


destination = "GROUND-0"
source = "ORBITL-1"

telemetry = (
    "SEQ=1,"
    "BAT=7.60,"
    "TEMP=31.4,"
    "MODE=NOMINAL"
)


# Build a valid AX.25 frame.
frame = build_ui_frame(
    destination=destination,
    source=source,
    information=telemetry.encode("ascii")
)


print("Original AX.25 Frame:")
print(frame.hex(" ").upper())

print()


# Convert immutable bytes to bytearray
# so we can intentionally modify the frame.
corrupted_frame = bytearray(frame)


# Corrupt one bit inside the Information Field.
#
# XOR with 0x01 flips one bit.
corrupted_frame[20] ^= 0x01


print("Corrupted AX.25 Frame:")
print(corrupted_frame.hex(" ").upper())

print()


# Try to decode the corrupted frame.
try:

    decoded = decode_ui_frame(
        bytes(corrupted_frame)
    )

    print("ERROR: Corrupted frame was accepted")

except ValueError as error:

    print("CRC ERROR DETECTED")
    print("Reason:", error)
    print("RESULT: PASS")