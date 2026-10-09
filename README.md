# ORBITL1-AX25

AX.25 protocol prototype and HDLC/NRZI integration tests for ORBITL-1.

## Repository layout

- `src/` — AX.25 frame, transmitter, receiver, and HDLC adapter code.
- `tests/` — regression and acceptance tests. Test criteria are unchanged.
- `docs/design/` — protocol scope and project design notes.
- `docs/project/` — project phase and roadmap documents.
- `docs/reference/` — AX.25 reference documents.
- `scripts/documentation/` — optional document-generation utilities.

Runtime code uses the reviewed Mobilinkd copy under
`src/vendor/mobilinkd/`; upstream provenance is recorded in
`THIRD_PARTY_NOTICES.md`.

## Run the regression suite

The protocol implementation and tests use only the Python standard library.

```powershell
python -m unittest discover -s tests -v
```

The expected maintained baseline is 46 passing tests.

## Optional documentation dependency

The PDF translation utility has a separate dependency and may use a network
translation service:

```powershell
python -m pip install -r requirements/docs.txt
python scripts/documentation/translate_pdf.py
```

Generated caches, virtual environments, temporary files, and output folders
are excluded by `.gitignore`.

## Third-party software

The HDLC decoder adapter uses modified Mobilinkd code under the MIT License.
Copyright and license text are retained in
`src/vendor/mobilinkd/LICENSE`. See `THIRD_PARTY_NOTICES.md` for provenance.
