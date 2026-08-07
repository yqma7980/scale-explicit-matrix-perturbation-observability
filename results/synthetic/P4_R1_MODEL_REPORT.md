# P4-r1 uncertainty coverage revision report

## Registered outcome

```text
P4_R1_FINAL_STATUS=DONE_P4_R1_TWO_TRUTH_UNCERTAINTY_MODEL_VALIDATED_ON_FROZEN_AND_HOLDOUT
ALL_REGISTERED_GATES_PASS=YES
P1_P2_P3_CHANGED=NO
WP27_HISTORY_CHANGED=NO
PAPER1_MODIFIED=NO
ABAQUS_RUN=NO
MANUSCRIPT_BODY_WRITTEN=NO
READY_FOR_SEPARATE_G2_04_INTEGRATION=YES
```

## Coverage

| data set | rows | source coverage | binary coverage | severe | component failures | subtraction failures |
|---|---:|---:|---:|---:|---:|---:|
| development | 300 | 300 | 300 | 0 | 0 | 0 |
| holdout | 300 | 300 | 300 | 0 | 0 | 0 |

## Historical reconciliation

The historical binary64 lane was reproduced exactly for 300/300 rows. Its 287/300 coverage and three severe undercoverage cases remain unchanged. The revised source envelope adds no fitted factor; it changes the truth contract by evaluating parent residuals against the declared decimal source operators.

The three historical severe cases are listed in `outputs/historical_severe_case_attribution.csv`. This supports a missing source-representation response component in the historical envelope. It does not establish a guard defect.

## Claim boundary

The revised model is validated only for the registered dimension-2/4/8/16 decimal families and disjoint holdout. WP27 labels remain diagnostic-only because its historical systems do not have this case-matched source-truth audit. The result does not prove a universal uncertainty bound, guard safety, or nonlinear convergence.

## Registered gates

| gate | observed | required | status |
|---|---|---|---|
| INPUT_FINGERPRINTS | 12 | 12 | PASS |
| END_FINGERPRINTS | 12 | 12 | PASS |
| LEGACY_EXACT_ROWS | 300 | 300 | PASS |
| LEGACY_COVERAGE_REPRODUCTION | 287 | 287 | PASS |
| LEGACY_SEVERE_REPRODUCTION | 3 | 3 | PASS |
| HOLDOUT_CARDINALITY | 300 | 300 | PASS |
| DEVELOPMENT_SOURCE_COVERAGE | 300 | 300 | PASS |
| DEVELOPMENT_BINARY_COVERAGE | 300 | 300 | PASS |
| HOLDOUT_SOURCE_COVERAGE | 300 | 300 | PASS |
| HOLDOUT_BINARY_COVERAGE | 300 | 300 | PASS |
| SEVERE_UNDERCOVERAGE | 0 | 0 | PASS |
| COMPONENT_BOUND_FAILURES | 0 | 0 | PASS |
| SUBTRACTION_BOUND_FAILURES | 0 | 0 | PASS |
| REFERENCE_RELATIVE_RESIDUAL_MAX | 6.15236029869614753170882916397730867400586658E-105 | 1E-70 | PASS |
| NONFINITE_COUNT | 0 | 0 | PASS |
| REPEATABILITY | 4 | 4 | PASS |
| ABAQUS_SOLVER_PROCESS | [] | NONE | PASS |

## Tightness boundary

The registered gates validate source-truth and binary-operand error coverage. They do not validate bound tightness or observability-class sharpness. The post-execution, non-gating diagnostic in `P4_R1_TIGHTNESS_DIAGNOSTIC.md` shows that the inverse-Frobenius envelope is deliberately conservative.

```text
VALIDATED_SCOPE=SOURCE_AND_BINARY_ERROR_COVERAGE_ONLY
TIGHTNESS_QUALIFIED=NO
CLASSIFICATION_SHARPNESS_CLAIM=NOT_AUTHORIZED
```
