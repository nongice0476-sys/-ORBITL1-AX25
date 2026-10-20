# ORBITL1-AX25

AX.25 protocol prototype, HDLC/NRZI framing, integration, and reliability test suite for the ORBITL-1 satellite communications subsystem.

## Repository layout

- `src/` — AX.25 UI frame, transmitter, receiver, and HDLC/NRZI adapter code.
- `tests/` — Automated test suite covering Phases 1–4 (95 passing tests).
- `docs/design/` — Protocol profile, interface specifications, and architectural notes.
- `docs/project/` — Engineering reports, machine-readable test summaries, and project roadmap.
- `docs/reference/` — Official AX.25 v2.2 specification documents.
- `scripts/` — Test execution, machine-readable reporting, and PDF generation utilities.
- `requirements/` — Documentation-generation dependencies.

Runtime code uses the reviewed Mobilinkd copy under `src/vendor/mobilinkd/`; upstream provenance is recorded in `THIRD_PARTY_NOTICES.md`.

## Automated test suite

The protocol implementation and automated test suite use only the Python standard library.

```powershell
python -m unittest discover -s tests -v
```

The comprehensive verification suite contains **95 passing tests** with zero failures and zero errors:

- `test_ax25_core.py` (29 tests) — AX.25 addressing, UI frame construction, CRC-16/X-25, and profile guards.
- `test_hdlc.py` (10 tests) — LSB-first serialization, bit stuffing, NRZI transitions, and chunked HDLC decoding.
- `test_receiver.py` (7 tests) — Receive pipeline behavior, chunked NRZI demodulator handoff, and multi-frame streaming.
- `test_reliability.py` (18 tests) — Automatic resynchronization, noise recovery, size boundary regression, and 1,000 round-trips.
- `test_integration.py` (22 tests) — Phase 3 end-to-end integration, arbitrary chunk sizes, fault recovery, spec vectors, and independent reference model.
- `test_acceptance.py` (9 tests) — Phase 4 multi-seed testing, profile rejection (Control/PID), boundary enforcement, and throughput benchmark.

To run the suite and update the machine-readable test summary:

```powershell
python scripts/run_and_record_tests.py
```

Results are saved to `docs/project/test_results.json`.

## Engineering reports

Generated technical reports are stored in `docs/project/`:

- `ORBITL1_AX25_Master_Engineering_Report.pdf` — Cumulative engineering report covering Phases 1–4.
- `ORBITL1_AX25_Phase4_Technical_Report.pdf` — Detailed technical report covering Phase 4 reliability and Phase 3 integration evidence.
- `test_results.json` — Machine-readable test execution metadata and performance benchmark metrics.

To regenerate both PDF reports:

```powershell
python -m pip install -r requirements/docs.txt
python scripts/documentation/build_phase_reports.py
```

## System interfaces & hardware demarcation

`AX25ReceivePipeline.feed_nrzi_levels(levels)` accepts binary NRZI line levels after an RF/SDR demodulator and retains NRZI state across streaming chunks. It decodes HDLC, verifies FCS (residual check constant `0xF0B8`), and forwards validated frame bodies to the shared AX.25 parser.

- **Current Profile:** Single destination + source, UI control `0x03`, PID `0xF0`, and Information field up to 4,078 bytes (under the 4,096-byte HDLC content limit).
- **Hardware Demarcation:** The software pipeline does not consume raw IQ/audio samples and does not implement carrier recovery, clock/symbol recovery, or RF demodulation. A physical radio/SDR integration layer must provide these functions.

## Third-party software

The HDLC decoder adapter uses modified Mobilinkd code under the MIT License. Copyright and license text are retained in `src/vendor/mobilinkd/LICENSE`. See `THIRD_PARTY_NOTICES.md` for provenance.
