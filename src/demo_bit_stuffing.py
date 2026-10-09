from ax25 import build_ui_frame

from ax25_hdlc import (
    bytes_to_bits_lsb_first,
    bit_stuff,
)


destination = "GROUND-0"
source = "ORBITL-1"

telemetry = (
    "SEQ=1,"
    "BAT=7.60,"
    "TEMP=31.4,"
    "MODE=NOMINAL"
)


# Build logical AX.25 frame.
frame = build_ui_frame(
    destination=destination,
    source=source,
    information=telemetry.encode("ascii")
)


# Remove opening and closing logical flags.
frame_body = frame[1:-1]


# Convert frame body to LSB-first bits.
bits = bytes_to_bits_lsb_first(
    frame_body
)


# Apply HDLC bit stuffing.
stuffed_bits = bit_stuff(
    bits
)


print(
    "Original bit length:",
    len(bits)
)

print(
    "Stuffed bit length:",
    len(stuffed_bits)
)

print(
    "Inserted bits:",
    len(stuffed_bits) - len(bits)
)

print()

print("Original first 64 bits:")

print(
    "".join(
        str(bit)
        for bit in bits[:64]
    )
)

print()

print("Stuffed first 64 bits:")

print(
    "".join(
        str(bit)
        for bit in stuffed_bits[:64]
    )
)