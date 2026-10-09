# ORBITL-1 AX.25 Protocol Development

## 1. Objective
Develop and evaluate AX.25 for ORBITL-1 communication.

## 2. Scope

Input:
Telemetry / Telecommand Packet

Processing:
AX.25 Encode / Decode

Output:
AX.25 Frame

## 3. Initial Use Case
UHF Housekeeping Beacon

Example telemetry:
SEQ = 1
BAT = 7.60 V
TEMP = 31.4 C
MODE = NOMINAL

## 4. Interfaces

Flight Software
↓
AX.25
↓
RF / SDR
↓
AX.25
↓
Ground Control Software

## 5. Relevant Requirements

COM-REQ-006
COM-REQ-017
COM-REQ-025
COM-REQ-026

## 6. TBR

Final AX.25/CSP decision
Callsign
SSID
Packet format
Bitrate
Modulation
Authentication
Maximum frame size