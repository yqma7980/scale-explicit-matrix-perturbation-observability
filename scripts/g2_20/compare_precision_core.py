from __future__ import annotations

import argparse
import csv
import json
from decimal import Decimal, getcontext
from pathlib import Path


getcontext().prec = 220

KEYS = ("dataset", "system_id", "lane")
CORE_SCALARS = (
    "beta_J_frobenius",
    "beta_A_frobenius",
    "alpha_E_frobenius",
    "realized_vs_declared_perturbation_gap",
    "U_z",
    "U_zg",
    "U_sub",
    "U_direct",
    "U_response_parentprop",
    "U_response_forcing",
    "U_response_solve",
    "U_response",
    "error_z",
    "error_zg",
    "error_subtraction",
    "error_direct",
    "error_response",
    "actual_response_parentprop",
    "actual_response_forcing",
    "actual_response_solve",
    "reference_response_norm",
    "reference_parent_norm",
    "eta_reference",
    "observed_direct_norm",
    "observed_response_norm",
    "reference_identity_difference",
    "maximum_reference_relative_residual",
)
BOOLEAN_FIELDS = (
    "direct_coverage",
    "response_coverage",
    "parent_z_coverage",
    "parent_zg_coverage",
    "subtraction_coverage",
    "response_parentprop_coverage",
    "response_forcing_coverage",
    "response_solve_coverage",
    "finite",
)


def load(path: Path) -> dict[tuple[str, str, str], dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    return {tuple(row[key] for key in KEYS): row for row in rows}


def normalized(a: Decimal, b: Decimal) -> Decimal:
    return abs(a - b) / max(Decimal(1), abs(a), abs(b))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lower", required=True, type=Path)
    parser.add_argument("--higher", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    lower = load(args.lower)
    higher = load(args.higher)
    if set(lower) != set(higher):
        raise RuntimeError("Precision files have different key sets")

    maximum = Decimal(0)
    maximum_record: dict[str, object] = {}
    boolean_mismatches: list[dict[str, object]] = []
    for key in sorted(lower):
        row_low = lower[key]
        row_high = higher[key]
        for field in CORE_SCALARS:
            difference = normalized(Decimal(row_low[field]), Decimal(row_high[field]))
            if difference > maximum:
                maximum = difference
                maximum_record = {
                    "key": key,
                    "field": field,
                    "lower": row_low[field],
                    "higher": row_high[field],
                }
        vector_low = [Decimal(value) for value in json.loads(row_low["reference_delta_json"])]
        vector_high = [Decimal(value) for value in json.loads(row_high["reference_delta_json"])]
        for index, (value_low, value_high) in enumerate(zip(vector_low, vector_high)):
            difference = normalized(value_low, value_high)
            if difference > maximum:
                maximum = difference
                maximum_record = {
                    "key": key,
                    "field": f"reference_delta_json[{index}]",
                    "lower": str(value_low),
                    "higher": str(value_high),
                }
        for field in BOOLEAN_FIELDS:
            if row_low[field] != row_high[field]:
                boolean_mismatches.append({"key": key, "field": field})

    result = {
        "schema_version": "1.0",
        "row_count": len(lower),
        "core_scalar_fields": list(CORE_SCALARS),
        "boolean_fields": list(BOOLEAN_FIELDS),
        "maximum_normalized_difference": str(maximum),
        "maximum_record": maximum_record,
        "boolean_mismatch_count": len(boolean_mismatches),
        "boolean_mismatches": boolean_mismatches,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
