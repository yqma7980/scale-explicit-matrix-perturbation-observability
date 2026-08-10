# G2-20r1 implementation freeze

Date: 2026-08-10

| File | SHA-256 |
|---|---|
| `G2_20R1_PRECISION_METRIC_CORRECTION_PREREGISTRATION.md` | `582727A188FBA9690796147190DA8A759BD25688DBE85C1EB40C3F41498461B5` |
| `implementation/compare_precision.py` | `67813B068B6AE401726820C123834D027F736AE448A5A92D66F6B887C549CB11` |
| `implementation/decimal_backend_audit.py` | `996CE500D81519F662BFB03A9D179F9FBA26A308E8EA532BEEF4AB4AF241F4AB` |

Both corrected scripts passed `python -m py_compile`. No response model,
scientific output, holdout row, or coverage decision is modified by G2-20r1.

```text
G2_20R1_IMPLEMENTATION = FROZEN_NOT_EXECUTED
```
