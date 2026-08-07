from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import scipy
import scipy.linalg


HERE = Path(__file__).resolve()
RELEASE_ROOT = HERE.parents[2]
SNAPSHOT = RELEASE_ROOT / "data/M8_operands_binary64.npz"


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def array_sha256(value: np.ndarray) -> str:
    array = np.ascontiguousarray(value)
    digest = hashlib.sha256()
    digest.update(str(array.dtype).encode("ascii"))
    digest.update(str(array.shape).encode("ascii"))
    digest.update(array.tobytes(order="C"))
    return digest.hexdigest().upper()


def direct_route(output_root: Path) -> bool:
    output_root.mkdir(parents=True, exist_ok=True)
    with np.load(SNAPSHOT, allow_pickle=False) as data:
        z_phys = np.asarray(data["z_phys"], dtype=np.float64)
        z_reg = np.asarray(data["z_reg"], dtype=np.float64)
    delta = np.empty(z_phys.size, dtype=np.float64)
    for index in range(z_phys.size):
        delta[index] = np.float64(z_reg[index] - z_phys[index])
    response_norm = float(np.linalg.norm(delta))
    parent_norm = float(np.linalg.norm(z_phys))
    eta = response_norm / max(parent_norm, np.finfo(np.float64).tiny)
    np.savez_compressed(
        output_root / "g2_08_direct_route_vector.npz",
        delta_direct64=delta,
        z_phys64=z_phys,
        z_reg64=z_reg,
    )
    result = {
        "schema_version": "1.0",
        "route": "DIRECT_PARENT_SOLUTION_DIFFERENCE",
        "dimension": int(delta.size),
        "response_norm_binary64": response_norm,
        "parent_norm_binary64": parent_norm,
        "eta_binary64": eta,
        "delta_sha256": array_sha256(delta),
        "finite": bool(np.isfinite(delta).all() and np.isfinite(eta)),
        "serialized_before_reference_comparison": True,
    }
    write_json(output_root / "g2_08_binary64_direct_summary.json", result)
    return bool(result["finite"])


def construct_delta_j(left: np.ndarray, right: np.ndarray) -> np.ndarray:
    rows, cols = left.shape
    result = np.empty_like(left, dtype=np.float64)
    for row in range(rows):
        for col in range(cols):
            result[row, col] = np.float64(right[row, col] - left[row, col])
    return result


def construct_forcing(delta_j: np.ndarray, z_phys: np.ndarray) -> np.ndarray:
    rows, cols = delta_j.shape
    result = np.empty(rows, dtype=np.float64)
    for row in range(rows):
        accumulator = np.float64(0.0)
        for col in range(cols):
            product = np.float64(delta_j[row, col] * z_phys[col])
            accumulator = np.float64(accumulator + product)
        result[row] = np.float64(-accumulator)
    return result


def response_route(output_root: Path) -> bool:
    output_root.mkdir(parents=True, exist_ok=True)
    with np.load(SNAPSHOT, allow_pickle=False) as data:
        jhat_phys = np.asarray(data["jhat_phys"], dtype=np.float64)
        jhat_reg = np.asarray(data["jhat_reg"], dtype=np.float64)
        z_phys = np.asarray(data["z_phys"], dtype=np.float64)
    delta_j = construct_delta_j(jhat_phys, jhat_reg)
    rhs = construct_forcing(delta_j, z_phys)
    response = scipy.linalg.solve(
        jhat_reg,
        rhs,
        assume_a="gen",
        overwrite_a=False,
        overwrite_b=False,
        check_finite=True,
    )
    response = np.asarray(response, dtype=np.float64)
    np.savez_compressed(
        output_root / "g2_08_response_route_vector.npz",
        delta_j64=delta_j,
        rhs_response64=rhs,
        delta_response64=response,
    )
    diagonal = np.diag(delta_j)
    off_diagonal = delta_j.copy()
    indices = np.arange(delta_j.shape[0])
    off_diagonal[indices, indices] = 0.0
    result = {
        "schema_version": "1.0",
        "route": "INDEPENDENT_RESPONSE_EQUATION",
        "python": __import__("sys").version.split()[0],
        "numpy": np.__version__,
        "scipy": scipy.__version__,
        "solver": "scipy.linalg.solve",
        "assume_a": "gen",
        "forcing_order": "ROW_MAJOR_SEQUENTIAL_MULTIPLY_ADD_NO_FMA",
        "dimension": int(response.size),
        "delta_j_nonzero_count": int(np.count_nonzero(delta_j)),
        "delta_j_off_diagonal_nonzero_count": int(np.count_nonzero(off_diagonal)),
        "delta_j_diagonal_nonzero_count": int(np.count_nonzero(diagonal)),
        "delta_j_diagonal_bitwise_uniform": bool(
            np.all(diagonal.view(np.uint64) == diagonal.view(np.uint64)[0])
        ),
        "delta_j_sha256": array_sha256(delta_j),
        "rhs_sha256": array_sha256(rhs),
        "response_sha256": array_sha256(response),
        "finite": bool(
            np.isfinite(delta_j).all()
            and np.isfinite(rhs).all()
            and np.isfinite(response).all()
        ),
        "serialized_before_reference_comparison": True,
    }
    write_json(output_root / "g2_08_binary64_response_summary.json", result)
    return bool(
        result["finite"]
        and result["delta_j_nonzero_count"] == 196
        and result["delta_j_off_diagonal_nonzero_count"] == 0
        and result["delta_j_diagonal_nonzero_count"] == 196
        and result["delta_j_diagonal_bitwise_uniform"]
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", required=True, choices=["direct", "response"])
    parser.add_argument("--output-root", required=True, type=Path)
    args = parser.parse_args()
    passed = direct_route(args.output_root) if args.mode == "direct" else response_route(args.output_root)
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
