# G2-20 preregistration and scope lock

## Purpose

G2-20 closes one specific Paper 2 evidence asymmetry: the direct-difference route already has a formal finite-precision error enclosure and development/holdout coverage evidence, whereas the response-equation route has only arithmetic-error comparisons and two finite-element case enclosures.

The confirmatory question is:

> Does the frozen response-equation error enclosure cover the realized binary64 response error on the existing development family and on a newly generated, unopened holdout family?

This work package does not develop the scalable sparse estimator reserved for Paper 3.

## Immutable parent

| Artifact | SHA-256 |
|---|---|
| `Paper2_scientific_candidate_v0.12.0.tex` | `6ABC90BB5A0964A77BA00A11A400F4240EB4E1F9C02A65B9F9B68E564F6A2E30` |
| `Paper2_references_v0.11.0.bib` | `ECFEF073AC4A4F6069431BDC53D3189A651D406AF6FB6FEF25919F280EC4212C` |
| development decimal systems | `C7FDF9795C24F99625EEE84190A89C781E1D9D6C725765E2CD7D3B1664542446` |
| development binary64 capture | `5133ACFE55FDC7DDAF67AC0D75C792F127D6D3E6B6B4FF7D890C8AC8050C18B7` |
| archived effectivity rows | `4CA125DEB5AB7CDF6856681E197EF713A9DD351D508849822BFEB431FA390ED3` |
| archived route-comparison rows | `9B9C0E8C3D4840D2A26186A9E8E5C8B684D21D78C963F8E03632A472318B4D0F` |

Parent artifacts remain read-only. Historical WP25-WP27, G2-03, G2-03r1, G2-08, M8, and M16 classifications are not rewritten.

## Frozen response-route model

For each reference lane `ell`, define the realized perturbation between the two
solved operators as

```text
J_ell z_ell = b_ell
E_ell = A_ell - J_ell
A_ell delta_ell = -E_ell z_ell
```

For the decimal-source lane, `A_source = J_source + DeltaJ_source` and hence
`E_source = DeltaJ_source`. For the binary64-operand lane, `J_binary` and
`A_binary` are the two independently captured solve operands and
`E_binary = A_binary - J_binary` in exact-real reconstruction. The captured
`DeltaJ_binary` remains the operand used to construct the floating-point
forcing. This distinction retains the last-bit matrix-addition representation
effect instead of assuming it away.

The captured binary64 route supplies `z_tilde`,

```text
f_tilde = fl(-DeltaJ_binary z_tilde)
A_binary delta_tilde approximately equals f_tilde.
```

For the selected lane, define

```text
r_z,ell     = b_ell - J_ell z_tilde
q_f,ell     = f_tilde + E_ell z_tilde
r_delta,ell = f_tilde - A_ell delta_tilde
```

Let the computed majorants satisfy

```text
beta_J,ell >= norm_2(inv(J_ell))
beta_A,ell >= norm_2(inv(A_ell))
alpha_E,ell >= norm_2(E_ell).
```

The frozen component bounds are

```text
U_z,ell          = beta_J,ell * norm_2(r_z,ell)
U_parentprop,ell = beta_A,ell * alpha_E,ell * U_z,ell
U_forcing,ell    = beta_A,ell * norm_2(q_f,ell)
U_solve,ell      = beta_A,ell * norm_2(r_delta,ell)

U_response,ell =
    U_parentprop,ell + U_forcing,ell + U_solve,ell.
```

The signs are additive. No cancellation between error budgets is permitted.

The default majorants are

```text
beta_J,ell = norm_F(inv(J_ell))
beta_A,ell = norm_F(inv(A_ell))
alpha_E,ell = norm_F(E_ell).
```

They are used because `norm_2(M) <= norm_F(M)`. Frobenius norms are majorants, not subordinate matrix norms paired with the Euclidean vector norm.

The confirmatory enclosure is

```text
error_response,ell = norm_2(delta_tilde - delta_ell)
coverage_response,ell = error_response,ell <= U_response,ell.
```

For comparison only, the already validated direct-route construction is recomputed without changing its formula:

```text
U_direct,ell = U_z,ell + U_zg,ell + U_sub.
```

## Reference lanes

Two non-interchangeable real-valued reference problems are retained:

1. `decimal-source`: decimal source matrices and right-hand side;
2. `binary64-operand`: exact real reconstruction of captured binary64 operands.

Every error, residual, inverse majorant, and coverage decision is evaluated within one lane. Cross-lane substitution is forbidden.

## Development and unopened holdout

Development uses the existing 300 decimal systems. The new holdout is not generated until this file and `inputs/g2_20_contract.json` are frozen.

The new holdout contains 300 systems:

```text
families: SPD, NONSYMMETRIC, SADDLE_POINT_LIKE
dimensions: 2, 4, 8, 16
condition exponents: 0, 11, 12, 13, 14
guard amplitudes: 7e-17, 7e-16, 7e-15, 7e-13, 7e-9
master seed: 2026081002
```

The condition and perturbation grids are disjoint from both earlier grids. The matrix-construction algorithms remain unchanged.

## Precision and independent backend

The primary evaluator is run at 120 and 180 decimal digits. A separate 120-digit process is repeated exactly. Precision agreement is checked before scientific interpretation.

An independently implemented Python `decimal` Gaussian-elimination backend evaluates 36 preregistered stratified holdout cases at 160 digits. It shares no `mpmath`, NumPy solve, or SciPy solve call with the primary reference path. This is an implementation-independence audit, not interval arithmetic or outward-rounded certification.

## Registered gates

The following gates are fixed before holdout generation:

```text
DEVELOPMENT_ROWS = 300
HOLDOUT_ROWS = 300

DEVELOPMENT_RESPONSE_SOURCE_COVERAGE = 300/300
DEVELOPMENT_RESPONSE_BINARY_COVERAGE = 300/300
HOLDOUT_RESPONSE_SOURCE_COVERAGE = 300/300
HOLDOUT_RESPONSE_BINARY_COVERAGE = 300/300

FALSE_ENCLOSURE_COUNT = 0
COMPONENT_BOUND_FAILURE_COUNT = 0
NONFINITE_COUNT = 0
REFERENCE_RELATIVE_RESIDUAL_MAX <= 1e-90
NORMALIZED_120_180_DIFFERENCE_MAX <= 1e-90
RUN1_RUN2_120_REPEATABILITY = EXACT_SHA256
DECIMAL_BACKEND_CASES = 36/36
DECIMAL_BACKEND_NORMALIZED_DIFFERENCE_MAX <= 1e-80
```

No gate is set for effectivity, route superiority, threshold classification, or a minimum number of decisive cases. Tightness and route ratios are reported without favorable filtering.

## Confirmatory classifications

```text
PASS_RESPONSE_ROUTE_ENCLOSURE_VALIDATED_ON_DEVELOPMENT_AND_NEW_HOLDOUT
FAIL_RESPONSE_ROUTE_FALSE_ENCLOSURE
INCONCLUSIVE_REFERENCE_OR_PRECISION_FAILURE
BLOCKED_INPUT_FINGERPRINT
```

## Existing-data analyses authorized in parallel

Only deterministic postprocessing is authorized:

1. factor the direct-route parent effectivity into inverse-norm-majorant inflation and residual-direction inflation;
2. fit a prespecified multivariable descriptive model for `log10(I_eff)` with condition exponent, perturbation exponent, dimension, family, reference lane, and data-set indicators;
3. report drop-one partial R-squared values and standardized coefficients;
4. report the extreme ratio as `log10(max)` and retain its case identity and near-zero denominator.

These analyses are descriptive. They do not establish a population law.

## Forbidden

- no Abaqus or UEL run;
- no M32 or new finite-element tangent;
- no sparse estimator or Paper 3 result;
- no guard redesign or perturbation selection;
- no nonlinear-trajectory claim;
- no interval, certified, guaranteed, or outward-rounded claim;
- no favorable rerun, fitted safety multiplier, or post-result threshold;
- no Paper 1 modification.

## Status at preregistration

```text
G2_20_STATUS = PREREGISTERED_NOT_EXECUTED
UNOPENED_HOLDOUT = NOT_GENERATED
MANUSCRIPT_REVISION = NOT_STARTED
```
