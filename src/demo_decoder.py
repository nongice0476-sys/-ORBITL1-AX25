from ax25 import build_ui_frame, decode_ui_frame


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


# Decode AX.25 frame.
decoded = decode_ui_frame(frame)


destination_text = (
    decoded["destination"]["callsign"]
    + "-"
    + str(decoded["destination"]["ssid"])
)

source_text = (
    decoded["source"]["callsign"]
    + "-"
    + str(decoded["source"]["ssid"])
)

decoded_telemetry = (
    decoded["information"].decode("ascii")
)


print("Destination :", destination_text)

print("Source      :", source_text)

print(
    "Control     :",
    f'0x{decoded["control"]:02X}'
)

print(
    "PID         :",
    f'0x{decoded["pid"]:02X}'
)

print(
    "Telemetry   :",
    decoded_telemetry
)

print(
    "Received FCS:",
    f'0x{decoded["received_fcs"]:04X}'
)

print(
    "Calculated  :",
    f'0x{decoded["calculated_fcs"]:04X}'
)


if decoded_telemetry == telemetry:
    print("RESULT: PASS")
else:
    print("RESULT: FAIL")