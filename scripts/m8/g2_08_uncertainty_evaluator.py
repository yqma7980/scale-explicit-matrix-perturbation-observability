from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any

import mpmath as mp
import numpy as np


HERE = Path(__file__).resolve()
RELEASE_ROOT = HERE.parents[2]
SNAPSHOT = RELEASE_ROOT / "data/M8_operands_binary64.npz"
EVAL_DPS = 180


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def exact_mpf(value: np.float64) -> mp.mpf:
    number = float(value)
    if not math.isfinite(number):
        raise ValueError("Nonfinite binary64 operand")
    if number == 0.0:
        return mp.mpf(0)
    numerator, denominator = number.as_integer_ratio()
    return mp.mpf(numerator) / mp.mpf(denominator)


def mp_matrix(values: np.ndarray) -> mp.matrix:
    rows, cols = values.shape
    result = mp.matrix(rows, cols)
    for row in range(rows):
        for col in range(cols):
            result[row, col] = exact_mpf(values[row, col])
    return result


def mp_vector(values: np.ndarray) -> mp.matrix:
    result = mp.matrix(values.size, 1)
    for index in range(values.size):
        result[index] = exact_mpf(values[index])
    return result


def string_vector(values: np.ndarray) -> mp.matrix:
    return mp.matrix([mp.mpf(str(item)) for item in values.reshape(-1)])


def string_matrix(values: np.ndarray) -> mp.matrix:
    rows, cols = values.shape
    return mp.matrix(
        [[mp.mpf(str(values[row, col])) for col in range(cols)] for row in range(rows)]
    )


def norm2(vector: mp.matrix) -> mp.mpf:
    return mp.sqrt(mp.fsum(abs(vector[index]) ** 2 for index in range(vector.rows)))


def frobenius(matrix: mp.matrix) -> mp.mpf:
    return mp.sqrt(
        mp.fsum(
            abs(matrix[row, col]) ** 2
            for row in range(matrix.rows)
            for col in range(matrix.cols)
        )
    )


def normalized_vector(left: mp.matrix, right: mp.matrix) -> mp.mpf:
    return max(
        abs(left[index] - right[index])
        / max(mp.mpf(1), abs(left[index]), abs(right[index]))
        for index in range(left.rows)
    )


def normalized_scalar(left: mp.mpf, right: mp.mpf) -> mp.mpf:
    return abs(left - right) / max(mp.mpf(1), abs(left), abs(right))


def decimal(value: mp.mpf, digits: int = 100) -> str:
    return mp.nstr(value, digits)


def load_reference(path: Path) -> dict[str, Any]:
    with np.load(path, allow_pickle=False) as data:
        return {
            "z_ref": string_vector(data["z_ref"]),
            "zg_ref": string_vector(data["zg_ref"]),
            "delta_ref_parent": string_vector(data["delta_ref_parent"]),
            "delta_ref_response": string_vector(data["delta_ref_response"]),
            "inverse_jg": string_matrix(data["inverse_jg"]),
            "metrics": json.loads(str(data["metrics_json"].item())),
        }


def tightness(actual: mp.mpf, bound: mp.mpf) -> dict[str, Any]:
    if actual == 0:
        return {
            "status": "EXACT_ZERO_ERROR_DENOMINATOR",
            "bound_to_actual_error_ratio": None,
        }
    return {
        "status": "FINITE_RATIO",
        "bound_to_actual_error_ratio": decimal(bound / actual),
    }


def reference_audit(ref120_path: Path, ref180_path: Path, output_root: Path) -> bool:
    mp.mp.dps = EVAL_DPS
    ref120 = load_reference(ref120_path)
    ref180 = load_reference(ref180_path)
    vector_fields = [
        "z_ref",
        "zg_ref",
        "delta_ref_parent",
        "delta_ref_response",
    ]
    vector_differences = {
        field: normalized_vector(ref120[field], ref180[field]) for field in vector_fields
    }
    metrics120 = ref120["metrics"]
    metrics180 = ref180["metrics"]
    inv_j_diff = normalized_scalar(
        mp.mpf(metrics120["inverse_frobenius_j"]),
        mp.mpf(metrics180["inverse_frobenius_j"]),
    )
    inv_jg_diff = normalized_scalar(
        mp.mpf(metrics120["inverse_frobenius_jg"]),
        mp.mpf(metrics180["inverse_frobenius_jg"]),
    )
    precision_max = max(*vector_differences.values(), inv_j_diff, inv_jg_diff)
    residual_fields = [
        "relative_residual_z",
        "relative_residual_zg",
        "relative_residual_response",
    ]
    residual_max = max(
        mp.mpf(metrics[field])
        for metrics in [metrics120, metrics180]
        for field in residual_fields
    )
    identity_max = max(
        mp.mpf(metrics120["parent_response_identity_normalized_difference"]),
        mp.mpf(metrics180["parent_response_identity_normalized_difference"]),
    )
    precision_pass = precision_max <= mp.mpf("1e-80")
    residual_pass = residual_max <= mp.mpf("1e-90")
    identity_pass = identity_max <= mp.mpf("1e-80")
    write_json(
        output_root / "g2_08_reference_precision_audit.json",
        {
            "schema_version": "1.0",
            "vector_normalized_differences": {
                key: decimal(value) for key, value in vector_differences.items()
            },
            "inverse_frobenius_j_normalized_difference": decimal(inv_j_diff),
            "inverse_frobenius_jg_normalized_difference": decimal(inv_jg_diff),
            "maximum_normalized_difference": decimal(precision_max),
            "limit": "1E-80",
            "pass": precision_pass,
        },
    )
    write_json(
        output_root / "g2_08_parent_reference_metrics.json",
        {
            "schema_version": "1.0",
            "relative_residuals_120dps": {
                field: metrics120[field] for field in residual_fields
            },
            "relative_residuals_180dps": {
                field: metrics180[field] for field in residual_fields
            },
            "maximum_relative_residual": decimal(residual_max),
            "limit": "1E-90",
            "z_ref_norm": decimal(norm2(ref180["z_ref"])),
            "zg_ref_norm": decimal(norm2(ref180["zg_ref"])),
            "delta_ref_norm": decimal(norm2(ref180["delta_ref_parent"])),
            "pass": residual_pass,
        },
    )
    write_json(
        output_root / "g2_08_response_identity_audit.json",
        {
            "schema_version": "1.0",
            "identity_difference_120dps": metrics120[
                "parent_response_identity_normalized_difference"
            ],
            "identity_difference_180dps": metrics180[
                "parent_response_identity_normalized_difference"
            ],
            "maximum_normalized_difference": decimal(identity_max),
            "limit": "1E-80",
            "pass": identity_pass,
        },
    )
    write_json(
        output_root / "g2_08_inverse_norm_metrics.json",
        {
            "schema_version": "1.0",
            "inverse_frobenius_j_120dps": metrics120["inverse_frobenius_j"],
            "inverse_frobenius_j_180dps": metrics180["inverse_frobenius_j"],
            "inverse_frobenius_jg_120dps": metrics120["inverse_frobenius_jg"],
            "inverse_frobenius_jg_180dps": metrics180["inverse_frobenius_jg"],
            "j_normalized_difference": decimal(inv_j_diff),
            "jg_normalized_difference": decimal(inv_jg_diff),
            "limit": "1E-80",
            "pass": inv_j_diff <= mp.mpf("1e-80")
            and inv_jg_diff <= mp.mpf("1e-80"),
        },
    )
    return bool(precision_pass and residual_pass and identity_pass)


def direct_uncertainty(ref180_path: Path, output_root: Path) -> bool:
    mp.mp.dps = EVAL_DPS
    reference = load_reference(ref180_path)
    with np.load(SNAPSHOT, allow_pickle=False) as data:
        j = mp_matrix(data["jhat_phys"])
        jg = mp_matrix(data["jhat_reg"])
        rhs = mp_vector(data["rhs_hat"])
        z_phys = mp_vector(data["z_phys"])
        z_reg = mp_vector(data["z_reg"])
    with np.load(output_root / "g2_08_direct_route_vector.npz", allow_pickle=False) as data:
        delta_direct = mp_vector(data["delta_direct64"])
    metrics = reference["metrics"]
    inv_j = mp.mpf(metrics["inverse_frobenius_j"])
    inv_jg = mp.mpf(metrics["inverse_frobenius_jg"])
    residual_z = norm2(rhs - j * z_phys)
    residual_zg = norm2(rhs - jg * z_reg)
    u_z = inv_j * residual_z
    u_zg = inv_jg * residual_zg
    unit_roundoff = mp.power(2, -53)
    gamma1 = unit_roundoff / (1 - unit_roundoff)
    absolute_parent_sum = mp.matrix(
        [abs(z_reg[index]) + abs(z_phys[index]) for index in range(z_phys.rows)]
    )
    u_sub = gamma1 * norm2(absolute_parent_sum) + mp.sqrt(196) * mp.power(2, -1075)
    u_direct = u_z + u_zg + u_sub
    error_z = norm2(z_phys - reference["z_ref"])
    error_zg = norm2(z_reg - reference["zg_ref"])
    exact_parent_difference = z_reg - z_phys
    error_sub = norm2(delta_direct - exact_parent_difference)
    error_total = norm2(delta_direct - reference["delta_ref_parent"])
    rows: list[dict[str, Any]] = []
    for component, space, actual, bound in [
        ("PARENT_Z", "SOLUTION", error_z, u_z),
        ("PARENT_ZG", "SOLUTION", error_zg, u_zg),
        ("SUBTRACTION", "SOLUTION", error_sub, u_sub),
        ("TOTAL_DIRECT_RESPONSE", "SOLUTION", error_total, u_direct),
    ]:
        row = {
            "component": component,
            "space": space,
            "actual_error": decimal(actual),
            "bound": decimal(bound),
            "covered": str(bool(actual <= bound)).upper(),
        }
        row.update(tightness(actual, bound))
        rows.append(row)
    write_csv(output_root / "g2_08_direct_uncertainty_ledger.csv", rows)
    write_json(
        output_root / "g2_08_direct_uncertainty_summary.json",
        {
            "schema_version": "1.0",
            "U_z": decimal(u_z),
            "U_zg": decimal(u_zg),
            "U_sub": decimal(u_sub),
            "U_direct": decimal(u_direct),
            "actual_total_error": decimal(error_total),
            "all_components_covered": all(row["covered"] == "TRUE" for row in rows),
        },
    )
    return all(row["covered"] == "TRUE" for row in rows)


def response_uncertainty(ref180_path: Path, output_root: Path) -> bool:
    mp.mp.dps = EVAL_DPS
    reference = load_reference(ref180_path)
    with np.load(SNAPSHOT, allow_pickle=False) as data:
        j = mp_matrix(data["jhat_phys"])
        jg = mp_matrix(data["jhat_reg"])
        z_phys = mp_vector(data["z_phys"])
        rhs_parent = mp_vector(data["rhs_hat"])
    with np.load(output_root / "g2_08_response_route_vector.npz", allow_pickle=False) as data:
        delta_j64 = mp_matrix(data["delta_j64"])
        rhs_response = mp_vector(data["rhs_response64"])
        delta_response = mp_vector(data["delta_response64"])
    delta_j = jg - j
    diagonal = [abs(delta_j[index, index]) for index in range(delta_j.rows)]
    off_diagonal_nonzero = sum(
        delta_j[row, col] != 0
        for row in range(delta_j.rows)
        for col in range(delta_j.cols)
        if row != col
    )
    if off_diagonal_nonzero != 0:
        raise RuntimeError("Registered captured DeltaJ diagonal structure changed")
    delta_j_norm2 = max(diagonal)
    inv_jg = mp.mpf(reference["metrics"]["inverse_frobenius_jg"])
    direct_summary = json.loads(
        (output_root / "g2_08_direct_uncertainty_summary.json").read_text(
            encoding="utf-8"
        )
    )
    u_z = mp.mpf(direct_summary["U_z"])
    exact_rhs_at_z_phys = -(delta_j * z_phys)
    u_rhs_round = norm2(rhs_response - exact_rhs_at_z_phys)
    actual_rhs_round = u_rhs_round
    actual_rhs_parent = norm2(delta_j * (z_phys - reference["z_ref"]))
    u_rhs_parent = delta_j_norm2 * u_z
    solve_residual = norm2(rhs_response - jg * delta_response)
    u_response_solve = inv_jg * solve_residual
    delta_rhs_exact = reference["inverse_jg"] * rhs_response
    actual_solve_error = norm2(delta_response - delta_rhs_exact)
    u_response = u_response_solve + inv_jg * (u_rhs_round + u_rhs_parent)
    actual_total = norm2(delta_response - reference["delta_ref_response"])
    rows: list[dict[str, Any]] = []
    for component, space, actual, bound in [
        ("FORCING_ROUNDING", "RIGHT_HAND_SIDE", actual_rhs_round, u_rhs_round),
        ("PARENT_Z_PROPAGATION", "RIGHT_HAND_SIDE", actual_rhs_parent, u_rhs_parent),
        ("RESPONSE_SOLVE", "SOLUTION", actual_solve_error, u_response_solve),
        ("TOTAL_RESPONSE_ROUTE", "SOLUTION", actual_total, u_response),
    ]:
        row = {
            "component": component,
            "space": space,
            "actual_error": decimal(actual),
            "bound": decimal(bound),
            "covered": str(bool(actual <= bound)).upper(),
        }
        row.update(tightness(actual, bound))
        rows.append(row)
    write_csv(output_root / "g2_08_response_uncertainty_ledger.csv", rows)
    write_json(
        output_root / "g2_08_response_uncertainty_summary.json",
        {
            "schema_version": "1.0",
            "delta_j_spectral_norm": decimal(delta_j_norm2),
            "delta_j64_difference_from_exact": decimal(frobenius(delta_j64 - delta_j)),
            "parent_rhs_norm": decimal(norm2(rhs_parent)),
            "U_rhs_round": decimal(u_rhs_round),
            "U_rhs_parent": decimal(u_rhs_parent),
            "U_response_solve": decimal(u_response_solve),
            "U_response": decimal(u_response),
            "actual_total_error": decimal(actual_total),
            "all_components_covered": all(row["covered"] == "TRUE" for row in rows),
        },
    )
    return all(row["covered"] == "TRUE" for row in rows)


def interval_decision(response: mp.matrix, bound: mp.mpf) -> dict[str, Any]:
    observed = norm2(response)
    lower = max(mp.mpf(0), observed - bound)
    upper = observed + bound
    distinguishable = observed > bound
    result: dict[str, Any] = {
        "d_obs": decimal(observed),
        "U": decimal(bound),
        "interval_lower": decimal(lower),
        "interval_upper": decimal(upper),
        "decision": (
            "DISTINGUISHABLE_FROM_ZERO"
            if distinguishable
            else "NOT_DISTINGUISHABLE_FROM_ZERO"
        ),
        "guaranteed_relative_error_upper_bound": None,
    }
    if distinguishable:
        result["guaranteed_relative_error_upper_bound"] = decimal(
            bound / (observed - bound)
        )
    return result


def finalize(output_root: Path, cost_path: Path | None) -> bool:
    mp.mp.dps = EVAL_DPS
    with np.load(output_root / "g2_08_direct_route_vector.npz", allow_pickle=False) as data:
        direct = mp_vector(data["delta_direct64"])
    with np.load(output_root / "g2_08_response_route_vector.npz", allow_pickle=False) as data:
        response = mp_vector(data["delta_response64"])
    direct_summary = json.loads(
        (output_root / "g2_08_direct_uncertainty_summary.json").read_text(
            encoding="utf-8"
        )
    )
    response_summary = json.loads(
        (output_root / "g2_08_response_uncertainty_summary.json").read_text(
            encoding="utf-8"
        )
    )
    u_direct = mp.mpf(direct_summary["U_direct"])
    u_response = mp.mpf(response_summary["U_response"])
    direct_decision = interval_decision(direct, u_direct)
    response_decision = interval_decision(response, u_response)
    route_difference = normalized_vector(direct, response)
    write_json(
        output_root / "g2_08_route_comparison.json",
        {
            "schema_version": "1.0",
            "direct_response_norm": decimal(norm2(direct)),
            "response_equation_norm": decimal(norm2(response)),
            "route_normalized_difference": decimal(route_difference),
            "route_selection_performed": False,
            "both_routes_retained": True,
        },
    )
    write_json(
        output_root / "g2_08_distinguishability_decisions.json",
        {
            "schema_version": "1.0",
            "direct_route": direct_decision,
            "response_equation_route": response_decision,
            "fixed_relative_accuracy_gate": None,
            "guard_safety_inference": "FORBIDDEN",
        },
    )
    direct_rows = list(
        csv.DictReader(
            (output_root / "g2_08_direct_uncertainty_ledger.csv").open(
                "r", encoding="utf-8", newline=""
            )
        )
    )
    response_rows = list(
        csv.DictReader(
            (output_root / "g2_08_response_uncertainty_ledger.csv").open(
                "r", encoding="utf-8", newline=""
            )
        )
    )
    cost = (
        json.loads(cost_path.read_text(encoding="utf-8"))
        if cost_path is not None and cost_path.is_file()
        else {}
    )
    write_json(
        output_root / "g2_08_tightness_and_cost.json",
        {
            "schema_version": "1.0",
            "direct_components": direct_rows,
            "response_components": response_rows,
            "reference_factorizations_per_precision": 2,
            "reference_right_hand_sides_per_precision": 3,
            "binary64_response_factorizations": 1,
            "binary64_response_right_hand_sides": 1,
            "cost": cost,
            "tightness_is_acceptance_gate": False,
        },
    )
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode",
        required=True,
        choices=["reference-audit", "direct", "response", "finalize"],
    )
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--ref120", type=Path)
    parser.add_argument("--ref180", type=Path)
    parser.add_argument("--cost-json", type=Path)
    args = parser.parse_args()
    if args.mode == "reference-audit":
        if args.ref120 is None or args.ref180 is None:
            parser.error("--ref120 and --ref180 are required")
        passed = reference_audit(args.ref120, args.ref180, args.output_root)
    elif args.mode == "direct":
        if args.ref180 is None:
            parser.error("--ref180 is required")
        passed = direct_uncertainty(args.ref180, args.output_root)
    elif args.mode == "response":
        if args.ref180 is None:
            parser.error("--ref180 is required")
        passed = response_uncertainty(args.ref180, args.output_root)
    else:
        passed = finalize(args.output_root, args.cost_json)
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
