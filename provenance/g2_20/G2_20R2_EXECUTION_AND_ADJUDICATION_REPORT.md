# G2-20r2 execution and adjudication report

## Decision

```text
PASS_RESPONSE_ROUTE_ENCLOSURE_VALIDATED_ON_DEVELOPMENT_AND_NEW_HOLDOUT
```

The frozen response-route finite-precision error enclosure covered all 300
development systems and all 300 newly generated holdout systems in both the
decimal-source and binary64-operand reference lanes. No component bound failed
and no nonfinite record occurred.

## Precision and independent implementation

The core 120/180-digit comparison gave maximum normalized differences of
`5.160463131876421e-110` for development and
`6.820386813941388e-107` for holdout. All coverage and finite booleans agreed.
The independent 160-digit Python Decimal implementation evaluated 36
preregistered holdout systems, or 72 lane comparisons, with maximum normalized
difference `6.9511487791608603e-153`.

## Preserved failure chain

The first G2-20 execution remains classified
`INCONCLUSIVE_REFERENCE_OR_PRECISION_FAILURE`. Its scientific coverage gates
passed, but its comparator normalized each near-zero value by its own
magnitude. G2-20r1 restored the project's existing `max(1,...)` convention;
G2-20r2 then locked the precision-gate object domain to reference and enclosure
quantities, excluding effectivity ratios with precision-limited denominators.
No solve, response, error bound, coverage decision, holdout row, or threshold
was changed in either tooling correction.

## Allowed Paper 2 claim

Paper 2 may state that the direct-difference and response-equation error
enclosures were each evaluated on prospectively separated synthetic operator
sets, and that the response-route enclosure achieved complete coverage on the
registered development and new holdout sets under both reference contracts.

Paper 2 may not call the computations interval-certified, claim universal
route superiority, infer a tightness law, or import Paper 3 scalability claims.
