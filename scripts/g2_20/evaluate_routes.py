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
    return mp.sqrt(
        mp.fsum(matrix[i, j] ** 2 for i in range(matrix.rows) for j in range(matrix.cols))
    )


def inverse_frobenius(matrix: mp.matrix) -> mp.mpf:
    return frobenius(matrix ** -1)


def relative_residual(matrix: mp.matrix, solution: mp.matrix, rhs: mp.matrix) -> mp.mpf:
    residual = rhs - matrix * solution
    denominator = frobenius(matrix) * norm2(solution) + norm2(rhs)
    return norm2(residual) / max(denominator, mp.mpf("1e-200"))


def decimal(value: mp.mpf, digits: int) -> str:
    return mp.nstr(value, digits)


def vector_json(vector: mp.matrix, digits: int) -> str:
    return json.dumps([decimal(vector[index], digits) for index in range(vector.rows)], separators=(",", ":"))


def covered(error: mp.mpf, bound: mp.mpf, margin: mp.mpf) -> bool:
    return bool(error <= bound * (1 + margin))


def safe_ratio(numerator: mp.mpf, denominator: mp.mpf) -> mp.mpf:
    if denominator == 0:
        return mp.mpf(0) if numerator == 0 else mp.inf
    return numerator / denominator


def load_sources(path: Path) -> dict[str, dict[str, object]]:
    rows: dict[str, dict[str, object]] = {}
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            rows[str(row["system_id"])] = row
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--binary", required=True, type=Path)
    parser.add_argument("--contract", required=True, type=Path)
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--digits", required=True, type=int)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--summary", required=True, type=Path)
    args = parser.parse_args()

    contract = json.loads(args.contract.read_text(encoding="utf-8"))
    margin = mp.mpf(contract["precision"]["comparison_margin"])
    mp.mp.dps = args.digits
    output_digits = args.digits - 10

    source_rows = load_sources(args.source)
    with args.binary.open("r", encoding="utf-8", newline="") as handle:
        binary_rows = list(csv.DictReader(handle))
    if set(source_rows) != {row["system_id"] for row in binary_rows}:
        raise RuntimeError("Source and binary key sets differ")

    unit_roundoff = mp.power(2, -53)
    gamma1 = unit_roundoff / (1 - unit_roundoff)
    half_min_subnormal = mp.power(2, -1075)
    output_rows: list[dict[str, object]] = []

    for binary in binary_rows:
        source = source_rows[binary["system_id"]]
        n = int(source["dimension"])
        j_source = mp_matrix_decimal(source["J"])
        d_source = mp_matrix_decimal(source["DeltaJ"])
        a_source = j_source + d_source
        b_source = mp_vector_decimal(source["b"])

        j_binary = mp_matrix_hex(binary["J_binary_hex"])
        d_binary_operand = mp_matrix_hex(binary["DeltaJ_binary_hex"])
        a_binary = mp_matrix_hex(binary["A_guarded_binary_hex"])
        b_binary = mp_vector_hex(binary["b_binary_hex"])
        z_tilde = mp_vector_hex(binary["z_tilde_hex"])
        zg_tilde = mp_vector_hex(binary["zg_tilde_hex"])
        delta_direct = mp_vector_hex(binary["delta_direct_hex"])
        forcing_tilde = mp_vector_hex(binary["forcing_tilde_hex"])
        delta_response = mp_vector_hex(binary["delta_response_hex"])

        absolute_parent_sum = mp.matrix(
            [abs(zg_tilde[index]) + abs(z_tilde[index]) for index in range(n)]
        )
        u_sub = gamma1 * norm2(absolute_parent_sum) + mp.sqrt(n) * half_min_subnormal
        error_sub = norm2(delta_direct - (zg_tilde - z_tilde))

        lane_data = (
            ("DECIMAL_SOURCE", j_source, a_source, b_source, a_source - j_source),
            ("BINARY64_OPERAND", j_binary, a_binary, b_binary, a_binary - j_binary),
        )
        for lane, j_lane, a_lane, b_lane, e_lane in lane_data:
            z_ref = mp.lu_solve(j_lane, b_lane)
            zg_ref = mp.lu_solve(a_lane, b_lane)
            delta_ref = zg_ref - z_ref
            delta_identity = mp.lu_solve(a_lane, -(e_lane * z_ref))

            beta_j = inverse_frobenius(j_lane)
            beta_a = inverse_frobenius(a_lane)
            alpha_e = frobenius(e_lane)
            residual_z = b_lane - j_lane * z_tilde
            residual_zg = b_lane - a_lane * zg_tilde
            forcing_defect = forcing_tilde + e_lane * z_tilde
            response_residual = forcing_tilde - a_lane * delta_response

            u_z = beta_j * norm2(residual_z)
            u_zg = beta_a * norm2(residual_zg)
            u_direct = u_z + u_zg + u_sub
            u_parentprop = beta_a * alpha_e * u_z
            u_forcing = beta_a * norm2(forcing_defect)
            u_solve = beta_a * norm2(response_residual)
            u_response = u_parentprop + u_forcing + u_solve

            error_z = norm2(z_tilde - z_ref)
            error_zg = norm2(zg_tilde - zg_ref)
            error_direct = norm2(delta_direct - delta_ref)
            error_response = norm2(delta_response - delta_ref)
            actual_parentprop = norm2(mp.lu_solve(a_lane, e_lane * (z_tilde - z_ref)))
            actual_forcing = norm2(mp.lu_solve(a_lane, forcing_defect))
            actual_solve = norm2(mp.lu_solve(a_lane, response_residual))

            d_ref = norm2(delta_ref)
            z_ref_norm = norm2(z_ref)
            observed_direct = norm2(delta_direct)
            observed_response = norm2(delta_response)
            reference_residuals = (
                relative_residual(j_lane, z_ref, b_lane),
                relative_residual(a_lane, zg_ref, b_lane),
                relative_residual(a_lane, delta_identity, -(e_lane * z_ref)),
            )
            identity_difference = norm2(delta_identity - delta_ref)
            operand_gap = frobenius(e_lane - d_binary_operand)
            finite_values = (
                beta_j,
                beta_a,
                alpha_e,
                u_z,
                u_zg,
                u_sub,
                u_direct,
                u_parentprop,
                u_forcing,
                u_solve,
                u_response,
                error_direct,
                error_response,
                d_ref,
            )

            output_rows.append(
                {
                    "dataset": args.dataset,
                    "system_id": source["system_id"],
                    "lane": lane,
                    "family": source["family"],
                    "dimension": n,
                    "condition_exponent": source["condition_exponent"],
                    "epsilon": source["epsilon"],
                    "seed": source["seed"],
                    "precision_digits": args.digits,
                    "beta_J_frobenius": decimal(beta_j, output_digits),
                    "beta_A_frobenius": decimal(beta_a, output_digits),
                    "alpha_E_frobenius": decimal(alpha_e, output_digits),
                    "realized_vs_declared_perturbation_gap": decimal(operand_gap, output_digits),
                    "U_z": decimal(u_z, output_digits),
                    "U_zg": decimal(u_zg, output_digits),
                    "U_sub": decimal(u_sub, output_digits),
                    "U_direct": decimal(u_direct, output_digits),
                    "U_response_parentprop": decimal(u_parentprop, output_digits),
                    "U_response_forcing": decimal(u_forcing, output_digits),
                    "U_response_solve": decimal(u_solve, output_digits),
                    "U_response": decimal(u_response, output_digits),
                    "error_z": decimal(error_z, output_digits),
                    "error_zg": decimal(error_zg, output_digits),
                    "error_subtraction": decimal(error_sub, output_digits),
                    "error_direct": decimal(error_direct, output_digits),
                    "error_response": decimal(error_response, output_digits),
                    "actual_response_parentprop": decimal(actual_parentprop, output_digits),
                    "actual_response_forcing": decimal(actual_forcing, output_digits),
                    "actual_response_solve": decimal(actual_solve, output_digits),
                    "direct_coverage": covered(error_direct, u_direct, margin),
                    "response_coverage": covered(error_response, u_response, margin),
                    "parent_z_coverage": covered(error_z, u_z, margin),
                    "parent_zg_coverage": covered(error_zg, u_zg, margin),
                    "subtraction_coverage": covered(error_sub, u_sub, margin),
                    "response_parentprop_coverage": covered(actual_parentprop, u_parentprop, margin),
                    "response_forcing_coverage": covered(actual_forcing, u_forcing, margin),
                    "response_solve_coverage": covered(actual_solve, u_solve, margin),
                    "reference_response_norm": decimal(d_ref, output_digits),
                    "reference_parent_norm": decimal(z_ref_norm, output_digits),
                    "eta_reference": decimal(safe_ratio(d_ref, z_ref_norm), output_digits),
                    "observed_direct_norm": decimal(observed_direct, output_digits),
                    "observed_response_norm": decimal(observed_response, output_digits),
                    "effectivity_direct": decimal(safe_ratio(u_direct, error_direct), output_digits),
                    "effectivity_response": decimal(safe_ratio(u_response, error_response), output_digits),
                    "response_to_direct_error_ratio": decimal(safe_ratio(error_response, error_direct), output_digits),
                    "response_to_direct_bound_ratio": decimal(safe_ratio(u_response, u_direct), output_digits),
                    "relative_U_direct": decimal(safe_ratio(u_direct, d_ref), output_digits),
                    "relative_U_response": decimal(safe_ratio(u_response, d_ref), output_digits),
                    "reference_identity_difference": decimal(identity_difference, output_digits),
                    "maximum_reference_relative_residual": decimal(max(reference_residuals), output_digits),
                    "reference_delta_json": vector_json(delta_ref, output_digits),
                    "finite": all(mp.isfinite(value) for value in finite_values),
                }
            )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(output_rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(output_rows)

    by_lane: dict[str, dict[str, object]] = {}
    for lane in ("DECIMAL_SOURCE", "BINARY64_OPERAND"):
        selected = [row for row in output_rows if row["lane"] == lane]
        by_lane[lane] = {
            "rows": len(selected),
            "direct_coverage_count": sum(bool(row["direct_coverage"]) for row in selected),
            "response_coverage_count": sum(bool(row["response_coverage"]) for row in selected),
            "component_failure_count": sum(
                not all(
                    bool(row[field])
                    for field in (
                        "parent_z_coverage",
                        "parent_zg_coverage",
                        "subtraction_coverage",
                        "response_parentprop_coverage",
                        "response_forcing_coverage",
                        "response_solve_coverage",
                    )
                )
                for row in selected
            ),
            "nonfinite_count": sum(not bool(row["finite"]) for row in selected),
        }
    summary = {
        "schema_version": "1.0",
        "dataset": args.dataset,
        "system_count": len(binary_rows),
        "output_row_count": len(output_rows),
        "precision_digits": args.digits,
        "by_lane": by_lane,
        "maximum_reference_relative_residual": max(
            row["maximum_reference_relative_residual"] for row in output_rows
        ),
        "response_lower_error_counts": dict(
            Counter(
                "RESPONSE" if mp.mpf(str(row["error_response"])) < mp.mpf(str(row["error_direct"])) else "DIRECT_OR_TIE"
                for row in output_rows
            )
        ),
    }
    args.summary.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
