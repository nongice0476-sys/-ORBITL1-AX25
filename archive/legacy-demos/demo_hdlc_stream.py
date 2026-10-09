from ax25 import build_ui_frame

from ax25_hdlc import (
    build_hdlc_bitstream,
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


# Remove logical byte-level flags.
frame_body = frame[1:-1]


# Build HDLC bitstream.
hdlc_bits = build_hdlc_bitstream(
    frame_body
)


print(
    "Frame body length:",
    len(frame_body),
    "bytes"
)

print(
    "HDLC bitstream length:",
    len(hdlc_bits),
    "bits"
)

print()

print(
    "Opening flag bits:",
    "".join(
        str(bit)
        for bit in hdlc_bits[:8]
    )
)

print(
    "Closing flag bits:",
    "".join(
        str(bit)
        for bit in hdlc_bits[-8:]
    )
)

print()

print(
    "First 40 HDLC bits:"
)

print(
    "".join(
        str(bit)
        for bit in hdlc_bits[:40]
    )
)