from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
from decimal import Decimal, getcontext
from pathlib import Path


getcontext().prec = 80


def stable_seed(master_seed: int, *parts: object) -> int:
    payload = ":".join([str(master_seed), *(str(part) for part in parts)])
    return int.from_bytes(hashlib.sha256(payload.encode("ascii")).digest()[:8], "big")


def zeros(n: int) -> list[list[Decimal]]:
    return [[Decimal(0) for _ in range(n)] for _ in range(n)]


def transpose(matrix: list[list[Decimal]]) -> list[list[Decimal]]:
    return [list(row) for row in zip(*matrix)]


def matmul(a: list[list[Decimal]], b: list[list[Decimal]]) -> list[list[Decimal]]:
    bt = transpose(b)
    return [[sum(x * y for x, y in zip(row, col)) for col in bt] for row in a]


def matvec(matrix: list[list[Decimal]], vector: list[Decimal]) -> list[Decimal]:
    return [sum(value * item for value, item in zip(row, vector)) for row in matrix]


def dec(value: Decimal) -> str:
    return "0" if value == 0 else str(value.normalize())


def exponent_profile(n: int, maximum: int) -> list[int]:
    if n == 1:
        return [maximum]
    return [int(round(maximum * index / (n - 1))) for index in range(n)]


def spd(n: int, exponent: int, rng: random.Random) -> list[list[Decimal]]:
    lower = zeros(n)
    for i, diagonal_exponent in enumerate(exponent_profile(n, exponent // 2)):
        diagonal = Decimal(10) ** Decimal(-diagonal_exponent)
        lower[i][i] = diagonal
        for j in range(i):
            lower[i][j] = diagonal * Decimal(rng.randint(-2, 2)) * Decimal("0.01")
    return matmul(lower, transpose(lower))


def nonsymmetric(n: int, exponent: int, rng: random.Random) -> list[list[Decimal]]:
    matrix = zeros(n)
    for i, diagonal_exponent in enumerate(exponent_profile(n, exponent)):
        diagonal = Decimal(10) ** Decimal(-diagonal_exponent)
        matrix[i][i] = diagonal
        for j in range(n):
            if i != j:
                matrix[i][j] = diagonal * Decimal(rng.randint(-2, 2)) * Decimal("0.005")
    if n > 1:
        matrix[0][1] += Decimal("0.003") * matrix[0][0]
        matrix[1][0] -= Decimal("0.002") * matrix[1][1]
    return matrix


def saddle(n: int, exponent: int, rng: random.Random) -> list[list[Decimal]]:
    half = n // 2
    a = zeros(half)
    b = zeros(half)
    for i in range(half):
        a[i][i] = Decimal(1) + Decimal(i + 1) / Decimal(10 * half)
        for j in range(i):
            coupling = Decimal(rng.randint(-2, 2)) * Decimal("0.005")
            a[i][j] = coupling
            a[j][i] = coupling
    for i, diagonal_exponent in enumerate(exponent_profile(half, exponent // 2)):
        diagonal = Decimal(10) ** Decimal(-diagonal_exponent)
        b[i][i] = diagonal
        for j in range(half):
            if i != j:
                b[i][j] = diagonal * Decimal(rng.randint(-2, 2)) * Decimal("0.01")
    matrix = zeros(n)
    bt = transpose(b)
    for i in range(half):
        for j in range(half):
            matrix[i][j] = a[i][j]
            matrix[i][half + j] = bt[i][j]
            matrix[half + i][j] = b[i][j]
    return matrix


def build_system(
    family: str,
    dimension: int,
    exponent: int,
    epsilon_text: str,
    master_seed: int,
) -> dict[str, object]:
    seed = stable_seed(master_seed, family, dimension, exponent, epsilon_text)
    rng = random.Random(seed)
    if family == "SPD":
        matrix = spd(dimension, exponent, rng)
        construction = "LOWER_TRIANGULAR_GRAM"
    elif family == "NONSYMMETRIC":
        matrix = nonsymmetric(dimension, exponent, rng)
        construction = "ROW_SCALED_STRICT_DIAGONAL_DOMINANCE"
    elif family == "SADDLE_POINT_LIKE":
        matrix = saddle(dimension, exponent, rng)
        construction = "SYMMETRIC_A_BT_B_ZERO_BLOCK"
    else:
        raise ValueError(family)

    target: list[Decimal] = []
    for index in range(dimension):
        raw = rng.randint(-9, 9)
        if raw == 0:
            raw = 1 if index % 2 == 0 else -1
        target.append(Decimal(raw) / Decimal(10))
    rhs = matvec(matrix, target)
    guard = zeros(dimension)
    epsilon = Decimal(epsilon_text)
    for index in range(dimension):
        guard[index][index] = epsilon
    system_id = (
        f"HOLDOUT_{family}_D{dimension:02d}_C{exponent:02d}_"
        f"E{epsilon_text.replace('-', 'M').replace('+', 'P')}"
    )
    return {
        "system_id": system_id,
        "family": family,
        "dimension": dimension,
        "condition_exponent": exponent,
        "epsilon": epsilon_text,
        "seed": seed,
        "construction": construction,
        "J": [[dec(value) for value in row] for row in matrix],
        "DeltaJ": [[dec(value) for value in row] for row in guard],
        "b": [dec(value) for value in rhs],
        "z_target": [dec(value) for value in target],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    args = parser.parse_args()
    contract = json.loads(args.contract.read_text(encoding="utf-8"))["holdout"]
    rows = [
        build_system(family, int(dimension), int(exponent), str(epsilon), int(contract["master_seed"]))
        for family in contract["families"]
        for dimension in contract["dimensions"]
        for exponent in contract["condition_exponents"]
        for epsilon in contract["guard_epsilons"]
    ]
    if len(rows) != int(contract["expected_rows"]):
        raise RuntimeError("Holdout cardinality mismatch")
    if len({row["system_id"] for row in rows}) != len(rows):
        raise RuntimeError("Holdout identifiers are not unique")
    if len({row["seed"] for row in rows}) != len(rows):
        raise RuntimeError("Holdout seeds are not unique")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
    fields = ["system_id", "family", "dimension", "condition_exponent", "epsilon", "seed", "construction"]
    with args.manifest.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows({field: row[field] for field in fields} for row in rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

