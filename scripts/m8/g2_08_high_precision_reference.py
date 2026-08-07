from __future__ import annotations

import argparse
import json
import math
import struct
import time
from pathlib import Path
from typing import Any

import mpmath as mp
import numpy as np


HERE = Path(__file__).resolve()
RELEASE_ROOT = HERE.parents[2]
SNAPSHOT = RELEASE_ROOT / "data/M8_operands_binary64.npz"


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def bits_of(value: np.float64) -> int:
    return struct.unpack("<Q", struct.pack("<d", float(value)))[0]


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


def relative_residual(matrix: mp.matrix, solution: mp.matrix, rhs: mp.matrix) -> mp.mpf:
    residual = matrix * solution - rhs
    denominator = max(
        mp.mpf(1),
        norm2(rhs),
        frobenius(matrix) * norm2(solution),
    )
    return norm2(residual) / denominator


def normalized_vector(left: mp.matrix, right: mp.matrix) -> mp.mpf:
    return max(
        abs(left[index] - right[index])
        / max(mp.mpf(1), abs(left[index]), abs(right[index]))
        for index in range(left.rows)
    )


def decimal(value: mp.mpf, digits: int) -> str:
    return mp.nstr(value, digits)


def vector_strings(vector: mp.matrix, digits: int) -> np.ndarray:
    return np.asarray([decimal(vector[index], digits) for index in range(vector.rows)])


def matrix_strings(matrix: mp.matrix, digits: int) -> np.ndarray:
    rows = [
        [decimal(matrix[row, col], digits) for col in range(matrix.cols)]
        for row in range(matrix.rows)
    ]
    return np.asarray(rows)


def reconstruction_audit(output_root: Path) -> bool:
    mp.mp.dps = 120
    rows: list[dict[str, Any]] = []
    total = 0
    exact = 0
    positive_zero = 0
    negative_zero = 0
    with np.load(SNAPSHOT, allow_pickle=False) as data:
        for key in sorted(data.files):
            array = data[key]
            if array.dtype != np.float64:
                continue
            local_exact = 0
            local_pos_zero = 0
            local_neg_zero = 0
            for item in array.reshape(-1):
                value = np.float64(item)
                bits = bits_of(value)
                sign = bits >> 63
                if value == 0.0:
                    local_neg_zero += int(sign == 1)
                    local_pos_zero += int(sign == 0)
                    roundtrip = bits in {0x0000000000000000, 0x8000000000000000}
                else:
                    reconstructed = float(exact_mpf(value))
                    roundtrip = bits_of(np.float64(reconstructed)) == bits
                local_exact += int(roundtrip)
            count = int(array.size)
            total += count
            exact += local_exact
            positive_zero += local_pos_zero
            negative_zero += local_neg_zero
            rows.append(
                {
                    "key": key,
                    "values": count,
                    "bit_roundtrip_exact": local_exact,
                    "positive_zero_count": local_pos_zero,
                    "negative_zero_count": local_neg_zero,
                    "pass": local_exact == count,
                }
            )
    result = {
        "schema_version": "1.0",
        "reconstruction": "IEEE_BINARY64_INTEGER_RATIO_WITH_SIGNED_ZERO_AUDIT",
        "decimal_input_route_used": False,
        "float64_value_count": total,
        "bit_roundtrip_exact_count": exact,
        "positive_zero_count": positive_zero,
        "negative_zero_count": negative_zero,
        "rows": rows,
        "pass": total > 0 and exact == total and all(row["pass"] for row in rows),
    }
    write_json(output_root / "g2_08_binary_operand_reconstruction.json", result)
    return bool(result["pass"])


def parent_reference(dps: int, output_path: Path) -> bool:
    if dps not in {120, 180}:
        raise ValueError("Only the registered 120 and 180 dps routes are allowed")
    started = time.perf_counter()
    mp.mp.dps = dps
    with np.load(SNAPSHOT, allow_pickle=False) as data:
        print(f"reconstructing operands at {dps} dps", flush=True)
        j = mp_matrix(data["jhat_phys"])
        jg = mp_matrix(data["jhat_reg"])
        rhs = mp_vector(data["rhs_hat"])
    delta_j = jg - j

    print(f"inverting J at {dps} dps", flush=True)
    inverse_j = j ** -1
    inverse_frobenius_j = frobenius(inverse_j)
    z_ref = inverse_j * rhs
    del inverse_j

    print(f"inverting Jg at {dps} dps", flush=True)
    inverse_jg = jg ** -1
    inverse_frobenius_jg = frobenius(inverse_jg)
    zg_ref = inverse_jg * rhs
    delta_parent = zg_ref - z_ref
    response_rhs = -(delta_j * z_ref)
    delta_response = inverse_jg * response_rhs

    residual_z = relative_residual(j, z_ref, rhs)
    residual_zg = relative_residual(jg, zg_ref, rhs)
    residual_response = relative_residual(jg, delta_response, response_rhs)
    identity_difference = normalized_vector(delta_parent, delta_response)
    metrics = {
        "schema_version": "1.0",
        "dps": dps,
        "mpmath_version": mp.__version__,
        "relative_residual_z": decimal(residual_z, dps),
        "relative_residual_zg": decimal(residual_zg, dps),
        "relative_residual_response": decimal(residual_response, dps),
        "parent_response_identity_normalized_difference": decimal(
            identity_difference, dps
        ),
        "inverse_frobenius_j": decimal(inverse_frobenius_j, dps),
        "inverse_frobenius_jg": decimal(inverse_frobenius_jg, dps),
        "factorizations": 2,
        "right_hand_sides": 3,
        "wall_time_seconds": time.perf_counter() - started,
        "finite": all(
            mp.isfinite(value)
            for value in [
                residual_z,
                residual_zg,
                residual_response,
                identity_difference,
                inverse_frobenius_j,
                inverse_frobenius_jg,
            ]
        ),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"serializing reference at {dps} dps", flush=True)
    np.savez_compressed(
        output_path,
        z_ref=vector_strings(z_ref, dps),
        zg_ref=vector_strings(zg_ref, dps),
        delta_ref_parent=vector_strings(delta_parent, dps),
        delta_ref_response=vector_strings(delta_response, dps),
        inverse_jg=matrix_strings(inverse_jg, dps),
        metrics_json=np.asarray(json.dumps(metrics, allow_nan=False)),
    )
    print(f"reference {dps} dps complete", flush=True)
    return bool(
        metrics["finite"]
        and residual_z <= mp.mpf("1e-90")
        and residual_zg <= mp.mpf("1e-90")
        and residual_response <= mp.mpf("1e-90")
        and identity_difference <= mp.mpf("1e-80")
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", required=True, choices=["audit", "reference"])
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--dps", type=int)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.mode == "audit":
        return 0 if reconstruction_audit(args.output_root) else 2
    if args.dps is None or args.output is None:
        parser.error("--dps and --output are required in reference mode")
    return 0 if parent_reference(args.dps, args.output) else 3


if __name__ == "__main__":
    raise SystemExit(main())
