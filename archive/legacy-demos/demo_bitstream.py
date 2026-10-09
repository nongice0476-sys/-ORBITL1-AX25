from ax25 import build_ui_frame
from ax25_hdlc import bytes_to_bits_lsb_first


destination = "GROUND-0"
source = "ORBITL-1"

telemetry = (
    "SEQ=1,"
    "BAT=7.60,"
    "TEMP=31.4,"
    "MODE=NOMINAL"
)


# Build the AX.25 logical frame.
frame = build_ui_frame(
    destination=destination,
    source=source,
    information=telemetry.encode("ascii")
)


# Remove the logical opening and closing 0x7E flags.
#
# Phase 2 will handle HDLC flags separately.
frame_body = frame[1:-1]


# Convert frame body into LSB-first bits.
bits = bytes_to_bits_lsb_first(
    frame_body
)


print("AX.25 Frame:")
print(
    frame.hex(" ").upper()
)

print()

print(
    "Complete frame length:",
    len(frame),
    "bytes"
)

print(
    "Frame body length:",
    len(frame_body),
    "bytes"
)

print(
    "Frame body bit length:",
    len(bits),
    "bits"
)

print()

print("First byte:")

print(
    f"0x{frame_body[0]:02X}"
)

print()

print("First 8 transmitted bits:")

print(
    "".join(
        str(bit)
        for bit in bits[:8]
    )
)

print()

print("First 32 transmitted bits:")

print(
    "".join(
        str(bit)
        for bit in bits[:32]
    )
)