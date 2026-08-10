# Route-specific finite-precision qualification of tangent perturbations

Reproducibility artifact for the manuscript:

> Coordinate-Explicit and Route-Specific Finite-Precision Qualification of
> Tangent-Only Perturbations in Coupled Finite-Element Linearizations

Release v1.1.0 contains non-confidential synthetic development and prospectively
separated holdout records, two frozen dimensionless finite-element linear-system
operand sets (M8 and M16), binary64 and independent-precision analysis scripts,
route-specific finite-precision error-enclosure records, exact manuscript tables,
and provenance manifests.

## Scope

The artifact supports a coordinate-explicit, route-specific qualification of a
selected tangent-only matrix perturbation. It does not distribute Abaqus, a UEL,
proprietary solver files, engineering project data, or a production simulation
model. M8 and M16 are independent frozen linearizations, not a mesh-refinement
sequence. The results do not establish guard safety, nonlinear convergence,
universal stabilization, engineering qualification, or a scalable sparse
estimator.

## Repository layout

- `data/`: sanitized binary64 operands and their array-level hashes.
- `scripts/m8/`: M8 binary64, high-precision, and uncertainty routes.
- `scripts/m16/`: M16 binary64, high-precision, and uncertainty routes.
- `scripts/synthetic/`: source used for the registered synthetic uncertainty study.
- `scripts/g2_20/`: registered direct- and response-route enclosure evaluation.
- `results/`: frozen synthetic, M8, and M16 result records.
- `results/g2_20/`: development, new holdout, precision, route, and effectivity records.
- `provenance/`: claim-evidence and execution reports.
- `provenance/g2_20/`: preregistration, preserved first execution, tooling-only
  corrections, and final adjudication.
- `manuscript/`: manuscript-supporting exact tables and release citation.
- `manuscript/v0.13.0/`: revised manuscript, supplement, vector figures, and
  deterministic figure scripts. No graphical abstract is included.
- `MANIFEST_SHA256.csv`: file-level release hashes.

## Quick verification

Python 3.12 is recommended. The recorded environment used NumPy 2.4.3, SciPy 1.17.1, and mpmath 1.3.0.

```text
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python scripts\run_binary64_smoke.py
```

The smoke test checks the public operand schemas, reconstructs both binary64 response routes for M8 and M16, and compares the resulting metrics with the frozen records. It does not rerun Abaqus or create new scientific cases.

## Independent-precision routes

The full routes reproduce the registered 120- and 180-decimal-digit calculations from the public binary64 operands. M16 can require several hours and substantial memory; see `RESOURCE_NOTES.md` before running it.

Example for M8:

```text
python scripts/m8/g2_08_binary64_response.py --mode direct --output-root generated/m8
python scripts/m8/g2_08_binary64_response.py --mode response --output-root generated/m8
python scripts/m8/g2_08_high_precision_reference.py --mode audit --output-root generated/m8
python scripts/m8/g2_08_high_precision_reference.py --mode reference --dps 120 --output generated/m8/reference_120dps.npz --output-root generated/m8
python scripts/m8/g2_08_high_precision_reference.py --mode reference --dps 180 --output generated/m8/reference_180dps.npz --output-root generated/m8
python scripts/m8/g2_08_uncertainty_evaluator.py --mode reference-audit --ref120 generated/m8/reference_120dps.npz --ref180 generated/m8/reference_180dps.npz --output-root generated/m8
python scripts/m8/g2_08_uncertainty_evaluator.py --mode direct --ref180 generated/m8/reference_180dps.npz --output-root generated/m8
python scripts/m8/g2_08_uncertainty_evaluator.py --mode response --ref180 generated/m8/reference_180dps.npz --output-root generated/m8
python scripts/m8/g2_08_uncertainty_evaluator.py --mode finalize --output-root generated/m8
```

The M16 commands are identical after replacing `m8/g2_08` with `m16/g2_11` and the output directory with `generated/m16`.

## Current registered result

The response-equation enclosure covered 300/300 development and 300/300 newly
generated holdout systems under both decimal-source and binary64-operand
contracts. The direct-difference enclosure retained the same coverage. An
independent 160-digit Python Decimal implementation checked 36 stratified
systems without importing mpmath, NumPy, or SciPy. The preserved first execution
remains classified as inconclusive because its near-zero comparator was
ill-posed; the corrected run was a preregistered tooling-only rerun from row 1.

## Citation

Liang, B., Ma, Y., Sun, W., and He, S. (2026). *Route-specific
finite-precision qualification of tangent perturbations: reproducibility
artifact* (Version 1.1.0). Zenodo. https://doi.org/10.5281/zenodo.21833850

## Licenses

Code is released under the MIT License. Data, documentation, and manuscript-supporting material are released under CC BY 4.0; see `LICENSE-DATA`.

## Contact

Correspondence about the artifact: Weiji Sun, `sunweiji-1231@163.com`.
