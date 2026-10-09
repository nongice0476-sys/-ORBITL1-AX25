from ax25 import build_ui_frame

from ax25_hdlc import (
    build_hdlc_bitstream,
    nrzi_encode,
    nrzi_decode,
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


# Remove logical byte-level flags.
frame_body = frame[1:-1]


# Build HDLC bitstream.
hdlc_bits = build_hdlc_bitstream(
    frame_body
)


# NRZI encode.
nrzi_levels = nrzi_encode(
    hdlc_bits,
    initial_level=0
)


# NRZI decode.
decoded_bits = nrzi_decode(
    nrzi_levels,
    initial_level=0
)


print(
    "HDLC bit length:",
    len(hdlc_bits)
)

print(
    "NRZI level length:",
    len(nrzi_levels)
)

print()

print(
    "First 32 HDLC bits:"
)

print(
    "".join(
        str(bit)
        for bit in hdlc_bits[:32]
    )
)

print()

print(
    "First 32 NRZI levels:"
)

print(
    "".join(
        str(level)
        for level in nrzi_levels[:32]
    )
)

print()


if decoded_bits == hdlc_bits:

    print("NRZI ENCODE / DECODE RESULT: PASS")

else:

    print("NRZI ENCODE / DECODE RESULT: FAIL")

