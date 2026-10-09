# Third-party notices

## Mobilinkd AFSK demodulator

The vendored HDLC decoder and CRC implementation under
`src/vendor/mobilinkd/` are derived from the Mobilinkd AFSK demodulator:

- Copyright (c) 2019 Mobilinkd LLC
- License: MIT
- Upstream: https://github.com/mobilinkd/afsk-demodulator
- Reviewed upstream commit: `18914893d0853070788a37d986bbd58db08721aa`

The complete MIT license is retained at `src/vendor/mobilinkd/LICENSE`.
The local `HDLC.py` contains project-specific modifications and is not an
unmodified duplicate of the upstream file.
