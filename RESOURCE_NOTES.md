# Resource notes

The binary64 smoke test is intended for routine verification. The independent-precision route reconstructs dense matrices with mpmath and is substantially more expensive.

Recorded full-route resources:

- M8: approximately 468 s and 110 MiB peak memory.
- M16: approximately 37,512 s and 1.35 GiB peak memory.

The registered execution used one thread, a 16 GiB memory cap, a six-hour cap per precision level, and a 36-hour total cap. Runtime depends strongly on CPU and Python/mpmath builds. The release does not require the expensive route for basic archive-integrity verification.
