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

## 7. System Boundary

### AX.25 Responsibility

My responsibility:
- AX.25 frame construction
- AX.25 frame parsing
- AX.25 addressing
- Control and PID fields
- FCS / CRC verification
- Bit stuffing / de-stuffing
- AX.25 encoder / decoder
- AX.25 test vectors
- Protocol documentation

Interface from Flight Software:
Telemetry / Telecommand Packet
        ↓
AX.25 Encoder

Interface to RF / SDR:
AX.25 Frame / Bitstream
        ↓
RF / SDR

Interface from RF / SDR:
Received AX.25 Frame / Bitstream
        ↓
AX.25 Decoder

Interface to Ground Control Software:
Decoded Telemetry / Telecommand Packet

                 ORBITL-1

             Flight Software
                    │
                    │ Packet
                    ▼
          ┌──────────────────┐
          │   AX.25 Encoder  │
          │                  │
          │          MY WORK     │
          └────────┬─────────┘
                   │
                   │ AX.25 Frame
                   ▼
          ┌──────────────────┐
          │     RF / SDR     │
          │      │
          └────────┬─────────┘
                   │
                   │ Radio Link
~~~~~~~~~~~~~~~~~~~│~~~~~~~~~~~~~~~~~~~
                   │
                   ▼
          ┌──────────────────┐
          │     RF / SDR     │
          └────────┬─────────┘
                   │
                   │ AX.25 Frame
                   ▼
          ┌──────────────────┐
          │   AX.25 Decoder  │
          │                  │
          │   MY WORK        │
          └────────┬─────────┘
                   │
                   │ Packet
                   ▼
          Ground Control Software
               
## 8. Phase 0 Exit Criteria

Phase 0 is complete when:

- AX.25 development objective is defined.
- Input and output interfaces are identified.
- AX.25 responsibility boundary is identified.
- Initial UHF beacon use case is defined.
- Relevant communication requirements are identified.
- Undecided parameters are marked as TBR.
- No final AX.25/CSP decision has been assumed.






