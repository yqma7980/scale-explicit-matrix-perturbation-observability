from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np


def matrix_hex(matrix: np.ndarray) -> str:
    return json.dumps([[float(value).hex() for value in row] for row in matrix], separators=(",", ":"))


def vector_hex(vector: np.ndarray) -> str:
    return json.dumps([float(value).hex() for value in vector], separators=(",", ":"))


def load_legacy(path: Path | None) -> dict[str, dict[str, str]]:
    if path is None:
        return {}
    with path.open("r", encoding="utf-8", newline="") as handle:
        return {row["system_id"]: row for row in csv.DictReader(handle)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--compatibility-output", required=True, type=Path)
    parser.add_argument("--legacy-capture", type=Path)
    args = parser.parse_args()

    legacy = load_legacy(args.legacy_capture)
    rows: list[dict[str, object]] = []
    mismatches: list[dict[str, str]] = []
    shared_fields = (
        "J_binary_hex",
        "DeltaJ_binary_hex",
        "A_guarded_binary_hex",
        "b_binary_hex",
        "z_tilde_hex",
        "zg_tilde_hex",
        "delta_direct_hex",
    )

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
            forcing = -(delta_j @ z)
            delta_response = np.linalg.solve(guarded, forcing)
            finite = all(
                np.all(np.isfinite(value))
                for value in (j, delta_j, guarded, rhs, z, zg, delta_direct, forcing, delta_response)
            )
            row: dict[str, object] = {
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
                "forcing_tilde_hex": vector_hex(forcing),
                "delta_response_hex": vector_hex(delta_response),
                "finite": finite,
            }
            rows.append(row)

            prior = legacy.get(str(source["system_id"]))
            if prior is not None:
                for field in shared_fields:
                    if str(row[field]) != prior[field]:
                        mismatches.append(
                            {"system_id": str(source["system_id"]), "field": field}
                        )
                if str(row["delta_response_hex"]) != prior["delta_stable_hex"]:
                    mismatches.append(
                        {"system_id": str(source["system_id"]), "field": "delta_response_vs_legacy_delta_stable"}
                    )

    if legacy and set(legacy) != {str(row["system_id"]) for row in rows}:
        raise RuntimeError("Legacy and regenerated development key sets differ")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    compatibility = {
        "schema_version": "1.0",
        "row_count": len(rows),
        "legacy_checked": bool(legacy),
        "legacy_row_count": len(legacy),
        "shared_fields": list(shared_fields),
        "response_matches_legacy_delta_stable": bool(legacy),
        "mismatch_count": len(mismatches),
        "mismatches": mismatches,
        "finite_count": sum(bool(row["finite"]) for row in rows),
    }
    args.compatibility_output.write_text(
        json.dumps(compatibility, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    if mismatches:
        raise RuntimeError(f"Binary64 compatibility mismatches: {len(mismatches)}")
    if compatibility["finite_count"] != len(rows):
        raise RuntimeError("Nonfinite binary64 capture")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
