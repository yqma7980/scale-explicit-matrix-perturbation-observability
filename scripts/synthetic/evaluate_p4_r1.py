from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path

import mpmath as mp


def mp_matrix_decimal(values: list[list[str]]) -> mp.matrix:
    return mp.matrix([[mp.mpf(value) for value in row] for row in values])


def mp_vector_decimal(values: list[str]) -> mp.matrix:
    return mp.matrix([mp.mpf(value) for value in values])


def exact_float(value: str) -> mp.mpf:
    binary = float.fromhex(value)
    numerator, denominator = binary.as_integer_ratio()
    return mp.mpf(numerator) / mp.mpf(denominator)


def mp_matrix_hex(text: str) -> mp.matrix:
    return mp.matrix([[exact_float(value) for value in row] for row in json.loads(text)])


def mp_vector_hex(text: str) -> mp.matrix:
    return mp.matrix([exact_float(value) for value in json.loads(text)])


def norm2(vector: mp.matrix) -> mp.mpf:
    return mp.sqrt(mp.fsum(vector[index] ** 2 for index in range(vector.rows)))


def frobenius(matrix: mp.matrix) -> mp.mpf:
    return mp.sqrt(mp.fsum(matrix[i, j] ** 2 for i in range(matrix.rows) for j in range(matrix.cols)))


def inverse_frobenius(matrix: mp.matrix) -> mp.mpf:
    return frobenius(matrix ** -1)


def relative_residual(matrix: mp.matrix, solution: mp.matrix, rhs: mp.matrix) -> mp.mpf:
    residual = rhs - matrix * solution
    denominator = frobenius(matrix) * norm2(solution) + norm2(rhs)
    return norm2(residual) / max(denominator, mp.mpf("1e-99"))


def decimal(value: mp.mpf, digits: int = 45) -> str:
    return mp.nstr(value, digits)


def diagnostic_label(eta: mp.mpf, relative_uncertainty: mp.mpf) -> str:
    if eta <= relative_uncertainty:
        return "RESOLUTION_LIMITED"
    if eta <= 10 * relative_uncertainty:
        return "TRANSITION"
    return "OBSERVABLE"


def covered(error: mp.mpf, bound: mp.mpf, margin: mp.mpf) -> bool:
    return bool(error <= bound * (1 + margin) + mp.mpf("1e-99"))


def severe(error: mp.mpf, bound: mp.mpf, margin: mp.mpf) -> bool:
    return bool(error > 10 * bound * (1 + margin) + mp.mpf("1e-99"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--binary", required=True, type=Path)
    parser.add_argument("--contract", required=True, type=Path)
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--summary", required=True, type=Path)
    args = parser.parse_args()
    contract = json.loads(args.contract.read_text(encoding="utf-8"))
    digits = int(contract["precision_digits"])
    margin = mp.mpf(contract["comparison_relative_margin"])
    mp.mp.dps = digits

    source_rows: dict[str, dict[str, object]] = {}
    with args.source.open("r", encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            source_rows[str(row["system_id"])] = row
    with args.binary.open("r", encoding="utf-8", newline="") as handle:
        binary_rows = list(csv.DictReader(handle))
    if set(source_rows) != {row["system_id"] for row in binary_rows}:
        raise RuntimeError("Source and binary key sets differ")

    unit_roundoff = mp.power(2, -53)
    gamma1 = unit_roundoff / (1 - unit_roundoff)
    half_min_subnormal = mp.power(2, -1075)
    output_rows: list[dict[str, object]] = []
    max_reference_residual = mp.mpf(0)

    for binary in binary_rows:
        source = source_rows[binary["system_id"]]
        n = int(source["dimension"])
        j_source = mp_matrix_decimal(source["J"])
        delta_j_source = mp_matrix_decimal(source["DeltaJ"])
        a_source = j_source + delta_j_source
        b_source = mp_vector_decimal(source["b"])

        j_binary = mp_matrix_hex(binary["J_binary_hex"])
        a_binary = mp_matrix_hex(binary["A_guarded_binary_hex"])
        b_binary = mp_vector_hex(binary["b_binary_hex"])
        z_tilde = mp_vector_hex(binary["z_tilde_hex"])
        zg_tilde = mp_vector_hex(binary["zg_tilde_hex"])
        delta_direct = mp_vector_hex(binary["delta_direct_hex"])

        z_source = mp.lu_solve(j_source, b_source)
        zg_source = mp.lu_solve(a_source, b_source)
        z_binary = mp.lu_solve(j_binary, b_binary)
        zg_binary = mp.lu_solve(a_binary, b_binary)
        delta_source = zg_source - z_source
        delta_binary = zg_binary - z_binary
        exact_parent_difference = zg_tilde - z_tilde

        source_residual_z = b_source - j_source * z_tilde
        source_residual_zg = b_source - a_source * zg_tilde
        binary_residual_z = b_binary - j_binary * z_tilde
        binary_residual_zg = b_binary - a_binary * zg_tilde

        u_source_z = inverse_frobenius(j_source) * norm2(source_residual_z)
        u_source_zg = inverse_frobenius(a_source) * norm2(source_residual_zg)
        u_binary_z = inverse_frobenius(j_binary) * norm2(binary_residual_z)
        u_binary_zg = inverse_frobenius(a_binary) * norm2(binary_residual_zg)
        absolute_parent_sum = mp.matrix(
            [abs(zg_tilde[index]) + abs(z_tilde[index]) for index in range(n)]
        )
        u_sub = gamma1 * norm2(absolute_parent_sum) + mp.sqrt(n) * half_min_subnormal
        u_source_total = u_source_z + u_source_zg + u_sub
        u_binary_total = u_binary_z + u_binary_zg + u_sub

        error_source_direct = norm2(delta_direct - delta_source)
        error_binary_direct = norm2(delta_direct - delta_binary)
        error_source_z = norm2(z_tilde - z_source)
        error_source_zg = norm2(zg_tilde - zg_source)
        error_binary_z = norm2(z_tilde - z_binary)
        error_binary_zg = norm2(zg_tilde - zg_binary)
        error_sub = norm2(delta_direct - exact_parent_difference)
        source_drift_z = norm2(z_binary - z_source)
        source_drift_zg = norm2(zg_binary - zg_source)
        arithmetic_error_z = norm2(z_tilde - z_binary)
        arithmetic_error_zg = norm2(zg_tilde - zg_binary)

        residuals = [
            relative_residual(j_source, z_source, b_source),
            relative_residual(a_source, zg_source, b_source),
            relative_residual(j_binary, z_binary, b_binary),
            relative_residual(a_binary, zg_binary, b_binary),
        ]
        max_reference_residual = max(max_reference_residual, *residuals)

        source_coverage = covered(error_source_direct, u_source_total, margin)
        binary_coverage = covered(error_binary_direct, u_binary_total, margin)
        component_source_z = covered(error_source_z, u_source_z, margin)
        component_source_zg = covered(error_source_zg, u_source_zg, margin)
        component_binary_z = covered(error_binary_z, u_binary_z, margin)
        component_binary_zg = covered(error_binary_zg, u_binary_zg, margin)
        subtraction_coverage = covered(error_sub, u_sub, margin)
        z_source_norm = norm2(z_source)
        z_binary_norm = norm2(z_binary)
        eta_source = norm2(delta_source) / max(z_source_norm, mp.mpf("1e-99"))
        eta_binary = norm2(delta_binary) / max(z_binary_norm, mp.mpf("1e-99"))
        relative_source_uncertainty = u_source_total / max(z_source_norm, mp.mpf("1e-99"))
        relative_binary_uncertainty = u_binary_total / max(z_binary_norm, mp.mpf("1e-99"))
        finite_values = [
            u_source_z,
            u_source_zg,
            u_binary_z,
            u_binary_zg,
            u_sub,
            u_source_total,
            u_binary_total,
            error_source_direct,
            error_binary_direct,
            eta_source,
            eta_binary,
        ]
        output_rows.append(
            {
                "dataset": args.dataset,
                "system_id": source["system_id"],
                "family": source["family"],
                "dimension": n,
                "condition_exponent": source["condition_exponent"],
                "epsilon": source["epsilon"],
                "seed": source["seed"],
                "U_legacy": binary["U_legacy"],
                "U_source_z": decimal(u_source_z),
                "U_source_zg": decimal(u_source_zg),
                "U_binary_z": decimal(u_binary_z),
                "U_binary_zg": decimal(u_binary_zg),
                "U_sub": decimal(u_sub),
                "U_source_r1": decimal(u_source_total),
                "U_binary_r1": decimal(u_binary_total),
                "error_source_direct": decimal(error_source_direct),
                "error_binary_direct": decimal(error_binary_direct),
                "error_source_z": decimal(error_source_z),
                "error_source_zg": decimal(error_source_zg),
                "error_binary_z": decimal(error_binary_z),
                "error_binary_zg": decimal(error_binary_zg),
                "error_subtraction": decimal(error_sub),
                "source_drift_z": decimal(source_drift_z),
                "source_drift_zg": decimal(source_drift_zg),
                "arithmetic_error_z": decimal(arithmetic_error_z),
                "arithmetic_error_zg": decimal(arithmetic_error_zg),
                "source_coverage": source_coverage,
                "binary_coverage": binary_coverage,
                "source_severe_undercoverage": severe(error_source_direct, u_source_total, margin),
                "binary_severe_undercoverage": severe(error_binary_direct, u_binary_total, margin),
                "source_parent_z_coverage": component_source_z,
                "source_parent_zg_coverage": component_source_zg,
                "binary_parent_z_coverage": component_binary_z,
                "binary_parent_zg_coverage": component_binary_zg,
                "subtraction_coverage": subtraction_coverage,
                "eta_source_reference": decimal(eta_source),
                "eta_binary_reference": decimal(eta_binary),
                "relative_U_source_r1": decimal(relative_source_uncertainty),
                "relative_U_binary_r1": decimal(relative_binary_uncertainty),
                "source_reference_label": diagnostic_label(eta_source, relative_source_uncertainty),
                "binary_reference_label": diagnostic_label(eta_binary, relative_binary_uncertainty),
                "maximum_reference_relative_residual": decimal(max(residuals)),
                "finite": all(mp.isfinite(value) for value in finite_values),
            }
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(output_rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(output_rows)

    source_labels = Counter(str(row["source_reference_label"]) for row in output_rows)
    binary_labels = Counter(str(row["binary_reference_label"]) for row in output_rows)
    summary = {
        "schema_version": "1.0",
        "dataset": args.dataset,
        "row_count": len(output_rows),
        "precision_digits": digits,
        "source_coverage_count": sum(bool(row["source_coverage"]) for row in output_rows),
        "binary_coverage_count": sum(bool(row["binary_coverage"]) for row in output_rows),
        "source_severe_undercoverage_count": sum(bool(row["source_severe_undercoverage"]) for row in output_rows),
        "binary_severe_undercoverage_count": sum(bool(row["binary_severe_undercoverage"]) for row in output_rows),
        "component_bound_failure_count": sum(
            not all(
                bool(row[field])
                for field in (
                    "source_parent_z_coverage",
                    "source_parent_zg_coverage",
                    "binary_parent_z_coverage",
                    "binary_parent_zg_coverage",
                )
            )
            for row in output_rows
        ),
        "subtraction_bound_failure_count": sum(not bool(row["subtraction_coverage"]) for row in output_rows),
        "nonfinite_count": sum(not bool(row["finite"]) for row in output_rows),
        "maximum_reference_relative_residual": decimal(max_reference_residual),
        "source_reference_label_counts": dict(sorted(source_labels.items())),
        "binary_reference_label_counts": dict(sorted(binary_labels.items())),
    }
    args.summary.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
