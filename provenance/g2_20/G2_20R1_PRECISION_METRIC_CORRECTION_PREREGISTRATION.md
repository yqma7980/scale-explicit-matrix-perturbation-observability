# G2-20r1 precision-metric correction preregistration

Date: 2026-08-10

## Preserved first execution

The first registered execution remains authoritative and unchanged:

```text
G2_20_CLASSIFICATION = INCONCLUSIVE_REFERENCE_OR_PRECISION_FAILURE
RESPONSE_COVERAGE_FAILURE = 0
COMPONENT_BOUND_FAILURE = 0
```

The precision comparator divided discrepancies by the magnitude of each
quantity with a `1e-200` floor. For near-zero reference components, this made a
120-digit truncation residual near `1e-124` and a 180-digit value near
`1e-182` appear to differ by order one. The same issue affected the independent
Decimal comparison. It does not change a response, error bound, or coverage
decision.

## Pre-existing comparison convention

Before G2-20, the project metric contract and G2-08 precision audit defined
normalized numerical comparison as

```text
abs(a-b) / max(1, abs(a), abs(b)).
```

For vectors, the componentwise maximum of this quantity is used. This is a
numerical reporting convention, not a physical norm and not a relative-error
claim for an exactly or nearly zero component.

## Authorized correction

G2-20r1 may only:

1. apply the pre-existing `max(1,...)` normalization to the already generated
   120- and 180-digit CSV files;
2. rerun the same 36-case Decimal implementation with the same inputs,
   arithmetic precision, solves, response model, and error bounds, changing
   only the comparison normalization;
3. write new `r1` comparison and adjudication files without overwriting any
   G2-20 result.

## Gates

```text
NORMALIZED_120_180_DIFFERENCE_MAX <= 1e-90
DECIMAL_BACKEND_NORMALIZED_DIFFERENCE_MAX <= 1e-80
BOOLEAN_MISMATCH_COUNT = 0
```

## Forbidden

- no regeneration of the holdout;
- no recomputation of binary64 captures;
- no recomputation or replacement of response coverage results;
- no change to the response theorem, component formulas, precision, or gates;
- no deletion or relabeling of the first G2-20 status;
- no favorable case filtering.

```text
G2_20R1_STATUS = PREREGISTERED_TOOLING_CORRECTION_NOT_EXECUTED
```
