# G2-20 preregistration amendment 01

Date: 2026-08-10

Status when amended:

```text
UNOPENED_HOLDOUT = NOT_GENERATED
NUMERICAL_EXECUTION = NOT_STARTED
MANUSCRIPT_REVISION = NOT_STARTED
```

The binary64 capture stores the parent matrix `J_binary`, the guarded matrix
`A_binary`, and the declared perturbation operand `DeltaJ_binary`. Exact-real
reconstruction need not make `A_binary - J_binary` bitwise identical to
`DeltaJ_binary`, because the guarded-matrix addition was performed in
binary64. The response theorem therefore uses the realized perturbation
`E_lane = A_lane - J_lane`, while the captured forcing remains
`fl(-DeltaJ_binary*z_tilde)`. Their difference is retained in the forcing
error component. This amendment prevents a last-bit representation effect
from being silently discarded.

No gate, family, dimension, condition exponent, perturbation amplitude, seed,
precision level, or backend criterion changed.

Post-amendment fingerprints:

```text
G2_20_PRE_REGISTRATION_AND_SCOPE_LOCK.md
8B553057A423300AD775949F524A594872DF5D87F51D1A0ECF450428B99A712B

inputs/g2_20_contract.json
61F30D5939B80F9D3756FB0E7AAC8787E1EDADAAF8008F892004FFCCBDB360D8
```
