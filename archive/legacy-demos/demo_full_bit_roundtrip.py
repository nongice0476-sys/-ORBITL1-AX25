from ax25 import build_ui_frame

from ax25_hdlc import (
    build_hdlc_bitstream,
    decode_hdlc_bitstream,
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


# Build logical AX.25 frame.
frame = build_ui_frame(
    destination=destination,
    source=source,
    information=telemetry.encode("ascii")
)


# Remove logical byte-level flags.
original_frame_body = frame[1:-1]


# Build HDLC bitstream.
hdlc_bits = build_hdlc_bitstream(
    original_frame_body
)


# NRZI encode.
nrzi_levels = nrzi_encode(
    hdlc_bits,
    initial_level=0
)


# NRZI decode.
recovered_hdlc_bits = nrzi_decode(
    nrzi_levels,
    initial_level=0
)


# Decode HDLC stream back into frame body bytes.
recovered_frame_body = decode_hdlc_bitstream(
    recovered_hdlc_bits
)


print(
    "Original frame body:",
    len(original_frame_body),
    "bytes"
)

print(
    "Recovered frame body:",
    len(recovered_frame_body),
    "bytes"
)

print()


if recovered_frame_body == original_frame_body:

    print("FULL BIT-LEVEL ROUND TRIP: PASS")

else:

    print("FULL BIT-LEVEL ROUND TRIP: FAIL")