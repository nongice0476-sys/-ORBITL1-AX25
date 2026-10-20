# ORBITL-1 AX.25 Protocol Development

## 1. Objective

Develop and verify the software protocol boundary for ORBITL-1 telemetry and telecommand transport using an AX.25 UI frame profile. The current implementation is a software protocol stack, verified through Phases 1–4, prior to integration with a qualified RF modem or flight radio.

## 2. Current supported profile

- **Addressing:** one destination and one source address; no digipeater path.
- **Frame type:** AX.25 UI (`Control = 0x03`).
- **PID:** no Layer 3 protocol (`PID = 0xF0`).
- **FCS:** CRC-16/X-25, transmitted low byte first.
- **Maximum HDLC content:** 4096 bytes, excluding opening/closing flags and including the two FCS bytes.
- **Maximum Information field for this profile:** 4078 bytes (4096 - 16-byte AX.25 header - 2-byte FCS).
- **Callsign syntax implemented:** 1-6 ASCII letters/digits, normalized to uppercase; SSID 0-15.

These are implementation constraints, not a final mission-interface approval. The final flight callsign, SSID, packet schema, bitrate, modulation, authentication, and operational frame limit remain TBR pending system requirements and radio selection.

## 3. Interfaces and data flow

### Transmit direction

```
Flight software payload (bytes)
  -> build_ui_frame()
  -> flagged AX.25 UI frame with FCS
  -> encode_hdlc()
  -> bit-stuffed HDLC bitstream
  -> nrzi_encode()
  -> binary NRZI line levels
  -> RF/SDR transmit chain (hardware demarcation).
```

### Receive direction

```
RF/SDR receiver and demodulator
  -> binary NRZI line levels
  -> AX25ReceivePipeline.feed_nrzi_levels()
  -> nrzi_decode() (state retained across chunks)
  -> HDLCStreamDecoder (bit unstuffing, flag detection, size guard, FCS validation)
  -> decode_verified_ui_body()
  -> validated AX.25 UI packet dictionary
  -> ground application.
```

`feed_nrzi_levels()` expects already-demodulated binary line levels. It does not consume raw IQ/audio samples and does not perform carrier recovery, timing recovery, symbol decisions, or physical-layer FEC. A radio/SDR integration layer must provide these functions and the correct bit polarity/clocking.

If an external modem supplies a complete byte-oriented AX.25 frame instead, `decode_ui_frame()` validates flags, length, FCS, addressing, control, and PID directly.

## 4. Phase responsibilities summary

### Phase 1: Frame core and validation
- Parse, validate, encode, and decode supported AX.25 address fields.
- Construct complete UI frames with flags and FCS.
- Validate FCS before interpreting a received complete frame.
- Validate frame boundaries, minimum/maximum size, address extension bits, reserved SSID bits, UI control, and PID.
- Expose `decode_verified_ui_body()` as the shared parsing boundary for the Phase 2 HDLC receiver.

### Phase 2: HDLC framing and NRZI line coding
- Serialize bytes LSB-first, apply HDLC bit stuffing and flags, and encode/decode NRZI.
- Stream-decode HDLC bits, reject invalid FCS (residual constant `0xF0B8`), enforce the 4096-byte frame cap, and recover after malformed/oversized frames.
- Retain NRZI state across streaming chunks.
- Pass only FCS-verified bodies into the Phase 1 parser.

### Phase 3: Integration & interoperability
- End-to-end integration across arbitrary chunk sizes (1 bit, 3 bits, 7 bits, 13 bits, 64 bits).
- Consecutive frame streaming: back-to-back flags, shared single delimiter flag, and multiple idle flags.
- Recovery from corrupted FCS (single/double bit flips, inverted FCS), premature flags, HDLC abort sequences (7+ ones), and line noise.
- Independent interoperability evidence:
  - CRC-16/X-25 standard known-answer vectors: `123456789 -> 0x906E`, `"" -> 0x0000`, `A -> 0xA3F5`, `TEST -> 0x89D1`.
  - AX.25 v2.2 specification standard address vectors (Section 3.12 Figures 3.5 & 3.6: `NJ7P-0`, `N7LEM-0`, `GROUND-0`, `ORBITL-1`).
  - Independent pure-Python reference model (`IndependentAX25Reference`) cross-validation with bit-for-bit equivalence.

### Phase 4: Reliability & acceptance
- Deterministic multi-seed randomized testing with fixed seeds (`20261009`, `20261019`, `42`, `1337`).
- Pathological payload byte pattern survival (all 0s, all 1s, alternating 0xAA/0x55, ramps, embedded flags/aborts).
- Strict profile rejection enforcement: non-UI controls (I-frame, S-frame, U-frame), non-0xF0 PIDs, malformed wire addresses.
- Exact payload size boundary verification: 4078 bytes accepted, 4079 bytes rejected by builder and wire receiver.
- Continuous mixed stream robustness: 100+ frames with interleaved CRC corruptions, aborts, and oversized frames with zero false accepts and sequential order preservation.
- Sustained processing performance benchmark: 500 frames (74 kB) processed in ~0.58s (864 frames/s, 1.02 Mbps throughput).

## 5. Software verification status

The repository automated test suite currently contains **95 passing tests** across 6 test modules:
- `test_ax25_core.py` (29 tests) — Addressing, frame construction, CRC-16, and profile guards.
- `test_hdlc.py` (10 tests) — Bit stuffing, NRZI transitions, chunked stream decoding.
- `test_receiver.py` (7 tests) — Receive pipeline, demodulator handoff, streaming chunks.
- `test_reliability.py` (18 tests) — Robustness, noise recovery, size boundaries, 1,000 round-trips.
- `test_integration.py` (22 tests) — End-to-end integration, arbitrary chunks, spec vectors, reference model.
- `test_acceptance.py` (9 tests) — Multi-seed testing, profile rejection, boundary checks, throughput benchmark.

All 95 tests pass deterministically via `python -m unittest discover -s tests -v` with zero failures and zero errors.

## 6. Hardware demarcation and remaining risks

Passing software tests do not establish real RF range, sensitivity, bit error rate, Doppler tolerance, clock recovery, modem interoperability, or flight readiness.

### Items explicitly unverified in software:
1. **Physical SDR / modem hardware compatibility:** Hardware timing, buffer underruns, and PTT turnaround.
2. **Audio / IQ sample path:** Software expects binary NRZI line levels; carrier recovery, timing synchronization, and matched filtering must be performed by the SDR/radio layer.
3. **Doppler shift & channel dynamics:** Frequency drift on LEO orbit passes (±3.5 kHz at 437 MHz).
4. **Physical channel BER / PER:** Forward error correction (FEC) is not part of standard AX.25; link margin must be verified with physical attenuators.
5. **Telecommand security:** Authentication and anti-replay wrappers must be layered on top of the AX.25 Information field prior to flight deployment.
