from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "generated"

CASES = {
    "m8": {
        "script": ROOT / "scripts/m8/g2_08_binary64_response.py",
        "output": GENERATED / "m8",
        "prefix": "g2_08",
        "dimension": 196,
        "data": ROOT / "data/M8_operands_binary64.npz",
        "expected": ROOT / "results/m8",
    },
    "m16": {
        "script": ROOT / "scripts/m16/g2_11_binary64_response.py",
        "output": GENERATED / "m16",
        "prefix": "g2_11",
        "dimension": 900,
        "data": ROOT / "data/M16_operands_binary64.npz",
        "expected": ROOT / "results/m16",
    },
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def normalized_difference(left: float, right: float) -> float:
    return abs(left - right) / max(1.0, abs(left), abs(right))


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def run_case(name: str, item: dict[str, Any]) -> dict[str, Any]:
    with np.load(item["data"], allow_pickle=False) as operands:
        key_set = set(operands.files)
        schema_ok = key_set == {
            "jhat_phys",
            "jhat_reg",
            "rhs_hat",
            "z_phys",
            "z_reg",
            "free_dofs",
            "row_scale",
            "x_scale",
        }
        dimension_ok = operands["jhat_phys"].shape == (
            item["dimension"],
            item["dimension"],
        )
        finite = all(np.isfinite(operands[key]).all() for key in operands.files)

    item["output"].mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["OMP_NUM_THREADS"] = "1"
    env["MKL_NUM_THREADS"] = "1"
    commands = []
    for mode in ("direct", "response"):
        command = [
            sys.executable,
            str(item["script"]),
            "--mode",
            mode,
            "--output-root",
            str(item["output"]),
        ]
        completed = subprocess.run(command, check=False, env=env)
        commands.append({"mode": mode, "returncode": completed.returncode})

    prefix = item["prefix"]
    actual_direct = load_json(item["output"] / f"{prefix}_binary64_direct_summary.json")
    expected_direct = load_json(item["expected"] / f"{prefix}_binary64_direct_summary.json")
    actual_response = load_json(item["output"] / f"{prefix}_binary64_response_summary.json")
    expected_response = load_json(item["expected"] / f"{prefix}_binary64_response_summary.json")

    eta_difference = normalized_difference(
        float(actual_direct["eta_binary64"]),
        float(expected_direct["eta_binary64"]),
    )
    response_hash_exact = (
        actual_response["response_sha256"] == expected_response["response_sha256"]
    )
    delta_j_hash_exact = (
        actual_response["delta_j_sha256"] == expected_response["delta_j_sha256"]
    )
    passed = (
        schema_ok
        and dimension_ok
        and finite
        and all(row["returncode"] == 0 for row in commands)
        and eta_difference <= 1.0e-13
        and response_hash_exact
        and delta_j_hash_exact
    )
    return {
        "case": name,
        "operand_file": item["data"].relative_to(ROOT).as_posix(),
        "operand_sha256": sha256(item["data"]),
        "schema_ok": bool(schema_ok),
        "dimension_ok": bool(dimension_ok),
        "finite": bool(finite),
        "commands": commands,
        "eta_binary64": actual_direct["eta_binary64"],
        "eta_expected": expected_direct["eta_binary64"],
        "eta_normalized_difference": eta_difference,
        "response_hash_exact": response_hash_exact,
        "delta_j_hash_exact": delta_j_hash_exact,
        "pass": passed,
    }


def main() -> int:
    results = [run_case(name, item) for name, item in CASES.items()]
    payload = {
        "schema_version": "1.0",
        "python": sys.version.split()[0],
        "cases": results,
        "pass": all(row["pass"] for row in results),
    }
    GENERATED.mkdir(parents=True, exist_ok=True)
    output = GENERATED / "binary64_smoke_test.json"
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0 if payload["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
