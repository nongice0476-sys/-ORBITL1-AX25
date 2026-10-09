from ax25 import build_ui_frame


destination = "GROUND-0"
source = "ORBITL-1"

telemetry = (
    "SEQ=1,"
    "BAT=7.60,"
    "TEMP=31.4,"
    "MODE=NOMINAL"
)

frame = build_ui_frame(
    destination=destination,
    source=source,
    information=telemetry.encode("ascii")
)


print("Destination :", destination)
print("Source      :", source)
print("Telemetry   :", telemetry)

print()

print("AX.25 Frame:")
print(frame.hex(" ").upper())

print()

print("Frame length:", len(frame), "bytes")