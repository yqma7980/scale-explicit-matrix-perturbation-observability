from __future__ import annotations

import argparse
import csv
import json
from decimal import Decimal, localcontext
from pathlib import Path


Vector = list[Decimal]
Matrix = list[list[Decimal]]


def exact_float(text: str) -> Decimal:
    value = float.fromhex(text)
    numerator, denominator = value.as_integer_ratio()
    return Decimal(numerator) / Decimal(denominator)


def matrix_decimal(values: list[list[str]]) -> Matrix:
    return [[Decimal(value) for value in row] for row in values]


def vector_decimal(values: list[str]) -> Vector:
    return [Decimal(value) for value in values]


def matrix_hex(text: str) -> Matrix:
    return [[exact_float(value) for value in row] for row in json.loads(text)]


def vector_hex(text: str) -> Vector:
    return [exact_float(value) for value in json.loads(text)]


def add(a: Matrix, b: Matrix) -> Matrix:
    return [[left + right for left, right in zip(row_a, row_b)] for row_a, row_b in zip(a, b)]


def subtract(a: Matrix, b: Matrix) -> Matrix:
    return [[left - right for left, right in zip(row_a, row_b)] for row_a, row_b in zip(a, b)]


def matvec(matrix: Matrix, vector: Vector) -> Vector:
    return [sum(value * item for value, item in zip(row, vector)) for row in matrix]


def vadd(a: Vector, b: Vector) -> Vector:
    return [left + right for left, right in zip(a, b)]


def vsub(a: Vector, b: Vector) -> Vector:
    return [left - right for left, right in zip(a, b)]


def vscale(value: Decimal, vector: Vector) -> Vector:
    return [value * item for item in vector]


def norm2(vector: Vector) -> Decimal:
    return sum(value * value for value in vector).sqrt()


def frobenius(matrix: Matrix) -> Decimal:
    return sum(value * value for row in matrix for value in row).sqrt()


def solve(matrix: Matrix, rhs: Vector) -> Vector:
    n = len(rhs)
    augmented = [row[:] + [rhs[index]] for index, row in enumerate(matrix)]
    for pivot in range(n):
        selected = max(range(pivot, n), key=lambda row: abs(augmented[row][pivot]))
        if augmented[selected][pivot] == 0:
            raise ArithmeticError("Singular matrix in Decimal backend")
        if selected != pivot:
            augmented[pivot], augmented[selected] = augmented[selected], augmented[pivot]
        pivot_value = augmented[pivot][pivot]
        for column in range(pivot, n + 1):
            augmented[pivot][column] /= pivot_value
        for row in range(n):
            if row == pivot:
                continue
            factor = augmented[row][pivot]
            if factor == 0:
                continue
            for column in range(pivot, n + 1):
                augmented[row][column] -= factor * augmented[pivot][column]
    return [augmented[row][n] for row in range(n)]


def inverse(matrix: Matrix) -> Matrix:
    n = len(matrix)
    columns = []
    for column in range(n):
        rhs = [Decimal(1) if row == column else Decimal(0) for row in range(n)]
        columns.append(solve(matrix, rhs))
    return [[columns[column][row] for column in range(n)] for row in range(n)]


def relative_difference(a: Decimal, b: Decimal) -> Decimal:
    return abs(a - b) / max(Decimal(1), abs(a), abs(b))


def vector_relative_difference(a: Vector, b: Vector) -> Decimal:
    return max(
        abs(left - right) / max(Decimal(1), abs(left), abs(right))
        for left, right in zip(a, b)
    )


def selected(source: dict[str, object], contract: dict[str, object]) -> bool:
    subset = contract["independent_backend_subset"]
    pairs = {(int(pair[0]), str(pair[1])) for pair in subset["condition_epsilon_pairs"]}
    return (
        source["family"] in subset["families"]
        and int(source["dimension"]) in subset["dimensions"]
        and (int(source["condition_exponent"]), str(source["epsilon"])) in pairs
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--binary", required=True, type=Path)
    parser.add_argument("--primary", required=True, type=Path)
    parser.add_argument("--contract", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--summary", required=True, type=Path)
    args = parser.parse_args()

    contract = json.loads(args.contract.read_text(encoding="utf-8"))
    digits = int(contract["precision"]["independent_decimal_digits"])
    source_rows: dict[str, dict[str, object]] = {}
    with args.source.open("r", encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if selected(row, contract):
                source_rows[str(row["system_id"])] = row
    expected = int(contract["independent_backend_subset"]["cases"])
    if len(source_rows) != expected:
        raise RuntimeError(f"Independent subset cardinality {len(source_rows)} != {expected}")

    with args.binary.open("r", encoding="utf-8", newline="") as handle:
        binary_rows = {
            row["system_id"]: row for row in csv.DictReader(handle) if row["system_id"] in source_rows
        }
    with args.primary.open("r", encoding="utf-8", newline="") as handle:
        primary_rows = {
            (row["system_id"], row["lane"]): row
            for row in csv.DictReader(handle)
            if row["system_id"] in source_rows
        }
    if set(source_rows) != set(binary_rows):
        raise RuntimeError("Independent source and capture key sets differ")

    output_rows: list[dict[str, object]] = []
    with localcontext() as context:
        context.prec = digits
        for system_id in sorted(source_rows):
            source = source_rows[system_id]
            binary = binary_rows[system_id]
            j_source = matrix_decimal(source["J"])
            d_source = matrix_decimal(source["DeltaJ"])
            a_source = add(j_source, d_source)
            b_source = vector_decimal(source["b"])
            j_binary = matrix_hex(binary["J_binary_hex"])
            a_binary = matrix_hex(binary["A_guarded_binary_hex"])
            b_binary = vector_hex(binary["b_binary_hex"])
            z_tilde = vector_hex(binary["z_tilde_hex"])
            forcing_tilde = vector_hex(binary["forcing_tilde_hex"])
            delta_tilde = vector_hex(binary["delta_response_hex"])

            for lane, j_lane, a_lane, b_lane, e_lane in (
                ("DECIMAL_SOURCE", j_source, a_source, b_source, subtract(a_source, j_source)),
                ("BINARY64_OPERAND", j_binary, a_binary, b_binary, subtract(a_binary, j_binary)),
            ):
                z_ref = solve(j_lane, b_lane)
                zg_ref = solve(a_lane, b_lane)
                delta_ref = vsub(zg_ref, z_ref)
                beta_j = frobenius(inverse(j_lane))
                beta_a = frobenius(inverse(a_lane))
                alpha_e = frobenius(e_lane)
                residual_z = vsub(b_lane, matvec(j_lane, z_tilde))
                forcing_defect = vadd(forcing_tilde, matvec(e_lane, z_tilde))
                response_residual = vsub(forcing_tilde, matvec(a_lane, delta_tilde))
                u_z = beta_j * norm2(residual_z)
                u_response = beta_a * (
                    alpha_e * u_z + norm2(forcing_defect) + norm2(response_residual)
                )

                primary = primary_rows[(system_id, lane)]
                primary_delta = [Decimal(value) for value in json.loads(primary["reference_delta_json"])]
                primary_u = Decimal(primary["U_response"])
                delta_difference = vector_relative_difference(delta_ref, primary_delta)
                u_difference = relative_difference(u_response, primary_u)
                output_rows.append(
                    {
                        "system_id": system_id,
                        "lane": lane,
                        "family": source["family"],
                        "dimension": source["dimension"],
                        "condition_exponent": source["condition_exponent"],
                        "epsilon": source["epsilon"],
                        "decimal_digits": digits,
                        "delta_normalized_difference": str(delta_difference),
                        "U_response_normalized_difference": str(u_difference),
                        "maximum_normalized_difference": str(max(delta_difference, u_difference)),
                    }
                )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(output_rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(output_rows)

    maximum_row = max(output_rows, key=lambda row: Decimal(str(row["maximum_normalized_difference"])))
    maximum = Decimal(str(maximum_row["maximum_normalized_difference"]))
    gate = Decimal(contract["acceptance_gates"]["independent_decimal_normalized_difference_max"])
    summary = {
        "schema_version": "1.0",
        "system_count": len(source_rows),
        "lane_comparison_count": len(output_rows),
        "decimal_digits": digits,
        "maximum_normalized_difference": str(maximum),
        "maximum_record": maximum_row,
        "registered_gate": str(gate),
        "pass": maximum <= gate,
        "imports_mpmath": False,
        "imports_numpy": False,
        "imports_scipy": False,
    }
    args.summary.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
