# G2-20r2 precision-object-domain preregistration

Date: 2026-08-10

## Preserved results

G2-20 and G2-20r1 remain unchanged. G2-20r1 established independent Decimal
agreement with maximum normalized difference `6.9511487791608603e-153`.
Its all-column precision comparison was nevertheless dominated by effectivity
and route ratios whose denominators can approach the precision floor.

## Precision-gate object domain

The 120/180 precision gate assesses quantities required to reconstruct a
coverage decision:

```text
beta_J_frobenius
beta_A_frobenius
alpha_E_frobenius
realized_vs_declared_perturbation_gap
U_z, U_zg, U_sub, U_direct
U_response_parentprop, U_response_forcing, U_response_solve, U_response
error_z, error_zg, error_subtraction, error_direct, error_response
actual_response_parentprop, actual_response_forcing, actual_response_solve
reference_response_norm, reference_parent_norm, eta_reference
observed_direct_norm, observed_response_norm
reference_identity_difference
maximum_reference_relative_residual
reference_delta_json
all coverage and finite booleans
```

The following derived ratios are excluded from the precision gate and are
reported from the 180-digit evaluation only:

```text
effectivity_direct
effectivity_response
response_to_direct_error_ratio
response_to_direct_bound_ratio
relative_U_direct
relative_U_response
```

Exclusion is required because a ratio with an exactly or nearly zero measured
error can vary arbitrarily under precision escalation even when both its
numerator and the underlying reference response agree. This is not a waiver of
tightness reporting: the ratios and their extreme case identities remain in
the scientific results.

Each scalar or vector component is compared by the pre-existing numerical
convention

```text
abs(a-b) / max(1, abs(a), abs(b)).
```

## Gate and restrictions

```text
CORE_MAXIMUM_NORMALIZED_120_180_DIFFERENCE <= 1e-90
CORE_BOOLEAN_MISMATCH_COUNT = 0
```

No solve, bound, coverage result, holdout row, threshold, or scientific model
may be regenerated or changed. G2-20r2 reads the frozen G2-20 CSV files only.

```text
G2_20R2_STATUS = PREREGISTERED_CORE_COMPARISON_NOT_EXECUTED
```
