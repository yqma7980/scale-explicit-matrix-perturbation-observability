from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

import numpy as np


EPS64 = np.finfo(np.float64).eps
TINY64 = np.finfo(np.float64).tiny


def matrix_hex(matrix: np.ndarray) -> str:
    return json.dumps([[float(value).hex() for value in row] for row in matrix], separators=(",", ":"))


def vector_hex(vector: np.ndarray) -> str:
    return json.dumps([float(value).hex() for value in vector], separators=(",", ":"))


def backward_error(matrix: np.ndarray, solution: np.ndarray, rhs: np.ndarray) -> float:
    numerator = float(np.linalg.norm(rhs - matrix @ solution, 2))
    denominator = float(np.linalg.norm(matrix, 2)) * float(np.linalg.norm(solution, 2)) + float(np.linalg.norm(rhs, 2))
    return numerator / max(denominator, TINY64)


def forward_bound(condition: float, backward: float) -> float:
    product = condition * backward
    if not math.isfinite(product) or product >= 1.0:
        return math.inf
    return product / max(1.0 - product, TINY64)


def legacy_label(eta: float, uncertainty: float) -> str:
    if not math.isfinite(uncertainty):
        return "UNDEFINED"
    if eta <= uncertainty:
        return "RESOLUTION_LIMITED"
    if eta <= 10.0 * uncertainty:
        return "TRANSITION"
    return "OBSERVABLE"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    rows: list[dict[str, object]] = []
    with args.input.open("r", encoding="utf-8") as handle:
        for line in handle:
            source = json.loads(line)
            j = np.asarray(source["J"], dtype=np.float64)
            delta_j = np.asarray(source["DeltaJ"], dtype=np.float64)
            rhs = np.asarray(source["b"], dtype=np.float64)
            guarded = j + delta_j
            z = np.linalg.solve(j, rhs)
            zg = np.linalg.solve(guarded, rhs)
            delta_direct = zg - z
            delta_stable = np.linalg.solve(guarded, -(delta_j @ z))
            condition_j = float(np.linalg.cond(j, 2))
            condition_guarded = float(np.linalg.cond(guarded, 2))
            backward_j = backward_error(j, z, rhs)
            backward_guarded = backward_error(guarded, zg, rhs)
            forward_j = forward_bound(condition_j, backward_j)
            forward_guarded = forward_bound(condition_guarded, backward_guarded)
            z_norm = float(np.linalg.norm(z, 2))
            zg_norm = float(np.linalg.norm(zg, 2))
            if math.isfinite(forward_j) and math.isfinite(forward_guarded):
                u_legacy = forward_j * z_norm + forward_guarded * zg_norm + 10.0 * EPS64 * (z_norm + zg_norm)
            else:
                u_legacy = math.inf
            relative_legacy = u_legacy / max(z_norm, TINY64)
            eta_stable = float(np.linalg.norm(delta_stable, 2)) / max(z_norm, TINY64)
            finite = all(
                np.all(np.isfinite(value))
                for value in (j, delta_j, guarded, rhs, z, zg, delta_direct, delta_stable)
            )
            rows.append(
                {
                    "system_id": source["system_id"],
                    "family": source["family"],
                    "dimension": source["dimension"],
                    "condition_exponent": source["condition_exponent"],
                    "epsilon": source["epsilon"],
                    "seed": source["seed"],
                    "J_binary_hex": matrix_hex(j),
                    "DeltaJ_binary_hex": matrix_hex(delta_j),
                    "A_guarded_binary_hex": matrix_hex(guarded),
                    "b_binary_hex": vector_hex(rhs),
                    "z_tilde_hex": vector_hex(z),
                    "zg_tilde_hex": vector_hex(zg),
                    "delta_direct_hex": vector_hex(delta_direct),
                    "delta_stable_hex": vector_hex(delta_stable),
                    "condition2_j": condition_j,
                    "condition2_guarded": condition_guarded,
                    "backward_error_j": backward_j,
                    "backward_error_guarded": backward_guarded,
                    "forward_bound_j": forward_j,
                    "forward_bound_guarded": forward_guarded,
                    "U_legacy": u_legacy,
                    "U_legacy_hex": float(u_legacy).hex(),
                    "relative_uncertainty_legacy": relative_legacy,
                    "eta_stable_binary64": eta_stable,
                    "legacy_label": legacy_label(eta_stable, relative_legacy),
                    "finite": finite,
                }
            )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
