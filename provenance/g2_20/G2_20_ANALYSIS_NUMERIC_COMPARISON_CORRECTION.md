# G2-20 analysis-only numeric comparison correction

## Scope

This correction affects descriptive route-comparison counts only. It does not
change any registered matrix, captured operand, solution, residual, error
component, enclosure, coverage decision, threshold, or holdout row.

## Issue

The first version of `analyze_effectivity.py` converted registered decimal
strings to binary64 before comparing direct- and response-route errors. Some
reference errors are below the normal binary64 range. Distinct positive values
therefore underflowed to a common zero and were counted as ties.

## Correction

Pairwise order comparisons now use Python `Decimal` directly on the registered
CSV strings. Floating conversion remains confined to non-gating descriptive
quantiles and plots.

## Corrected counts

| Data set | Reference lane | Response lower error | Response lower bound | Coverage, direct | Coverage, response |
|---|---|---:|---:|---:|---:|
| Development | Decimal source | 295/300 | 283/300 | 300/300 | 300/300 |
| Development | Binary64 operand | 199/300 | 229/300 | 300/300 | 300/300 |
| New G2-20 holdout | Decimal source | 271/300 | 229/300 | 300/300 | 300/300 |
| New G2-20 holdout | Binary64 operand | 160/300 | 188/300 | 300/300 | 300/300 |

The previously reported development decimal-source count of 295/300 is
restored exactly. No route-superiority claim is permitted from these finite
grids.
