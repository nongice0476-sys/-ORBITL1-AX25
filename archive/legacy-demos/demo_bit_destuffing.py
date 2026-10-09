from ax25 import build_ui_frame

from ax25_hdlc import (
    bytes_to_bits_lsb_first,
    bit_stuff,
    bit_destuff,
)


destination = "GROUND-0"
source = "ORBITL-1"

telemetry = (
    "SEQ=1,"
    "BAT=7.60,"
    "TEMP=31.4,"
    "MODE=NOMINAL"
)


# Build AX.25 frame.
frame = build_ui_frame(
    destination=destination,
    source=source,
    information=telemetry.encode("ascii")
)


# Remove logical opening and closing flags.
frame_body = frame[1:-1]


# Convert bytes to LSB-first bits.
original_bits = bytes_to_bits_lsb_first(
    frame_body
)


# Apply bit stuffing.
stuffed_bits = bit_stuff(
    original_bits
)


# Remove stuffed bits.
destuffed_bits = bit_destuff(
    stuffed_bits
)


print(
    "Original bit length:",
    len(original_bits)
)

print(
    "Stuffed bit length:",
    len(stuffed_bits)
)

print(
    "Destuffed bit length:",
    len(destuffed_bits)
)

print()

print(
    "Inserted bits:",
    len(stuffed_bits) - len(original_bits)
)

print(
    "Removed bits:",
    len(stuffed_bits) - len(destuffed_bits)
)

print()


# Verify round trip.
if destuffed_bits == original_bits:

    print("BIT STUFF / DESTUFF RESULT: PASS")

else:

    print("BIT STUFF / DESTUFF RESULT: FAIL")