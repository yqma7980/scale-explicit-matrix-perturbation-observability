from __future__ import annotations

import argparse
import csv
import json
import math
from decimal import Decimal
from pathlib import Path

import numpy as np
import pandas as pd


def matrix_hex(text: str) -> np.ndarray:
    return np.asarray([[float.fromhex(value) for value in row] for row in json.loads(text)], dtype=float)


def load_jsonl(path: Path) -> dict[str, dict[str, object]]:
    rows: dict[str, dict[str, object]] = {}
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            rows[str(row["system_id"])] = row
    return rows


def load_csv_keyed(path: Path) -> dict[str, dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return {row["system_id"]: row for row in csv.DictReader(handle)}


def percentile(values: pd.Series, q: float) -> float:
    return float(np.quantile(values.to_numpy(dtype=float), q))


def component_anatomy(
    dataset: str,
    source_path: Path,
    capture_path: Path,
    results_path: Path,
) -> list[dict[str, object]]:
    sources = load_jsonl(source_path)
    captures = load_csv_keyed(capture_path)
    results = load_csv_keyed(results_path)
    rows: list[dict[str, object]] = []
    for system_id in sorted(sources):
        source = sources[system_id]
        capture = captures[system_id]
        result = results[system_id]
        j_source = np.asarray(source["J"], dtype=float)
        a_source = j_source + np.asarray(source["DeltaJ"], dtype=float)
        j_binary = matrix_hex(capture["J_binary_hex"])
        a_binary = matrix_hex(capture["A_guarded_binary_hex"])
        for lane, j_matrix, a_matrix, prefix in (
            ("decimal-source", j_source, a_source, "source"),
            ("binary64-operand", j_binary, a_binary, "binary"),
        ):
            for parent, matrix, suffix in (("z", j_matrix, "z"), ("zg", a_matrix, "zg")):
                inverse = np.linalg.inv(matrix)
                norm_f = float(np.linalg.norm(inverse, "fro"))
                norm_2 = float(np.linalg.norm(inverse, 2))
                norm_inflation = norm_f / norm_2
                bound = float(result[f"U_{prefix}_{suffix}"])
                error = float(result[f"error_{prefix}_{suffix}"])
                if error == 0:
                    effectivity = math.inf if bound > 0 else 1.0
                    directional_inflation = math.inf
                    status = "ZERO_ERROR_DENOMINATOR"
                else:
                    effectivity = bound / error
                    directional_inflation = effectivity / norm_inflation
                    status = "FINITE"
                rows.append(
                    {
                        "dataset": dataset,
                        "system_id": system_id,
                        "lane": lane,
                        "family": source["family"],
                        "dimension": int(source["dimension"]),
                        "condition_exponent": int(source["condition_exponent"]),
                        "epsilon": str(source["epsilon"]),
                        "parent": parent,
                        "inverse_frobenius": norm_f,
                        "inverse_spectral": norm_2,
                        "norm_majorant_inflation": norm_inflation,
                        "parent_bound": bound,
                        "parent_error": error,
                        "parent_effectivity": effectivity,
                        "directional_alignment_inflation": directional_inflation,
                        "factorization_relative_residual": (
                            abs(effectivity - norm_inflation * directional_inflation)
                            / max(1.0, abs(effectivity))
                            if math.isfinite(effectivity) and math.isfinite(directional_inflation)
                            else math.nan
                        ),
                        "status": status,
                    }
                )
    return rows


def fit_model(frame: pd.DataFrame, label: str) -> tuple[dict[str, object], list[dict[str, object]]]:
    work = frame.copy()
    work = work[np.isfinite(work["I_eff"].astype(float)) & (work["I_eff"].astype(float) > 0)].copy()
    y_raw = np.log10(work["I_eff"].astype(float).to_numpy())
    y = (y_raw - y_raw.mean()) / y_raw.std(ddof=0)
    continuous = {
        "condition_exponent": work["condition_exponent"].astype(float).to_numpy(),
        "log10_epsilon": np.log10(work["epsilon"].astype(float).to_numpy()),
        "log2_dimension": np.log2(work["dimension"].astype(float).to_numpy()),
    }
    columns: list[tuple[str, np.ndarray, str]] = [("intercept", np.ones(len(work)), "intercept")]
    for name, values in continuous.items():
        columns.append((name, (values - values.mean()) / values.std(ddof=0), name))
    for category in ("NONSYMMETRIC", "SADDLE_POINT_LIKE"):
        columns.append((f"family_{category}", (work["family"] == category).astype(float).to_numpy(), "family"))
    columns.append(("lane_binary64", (work["lane"] == "binary64-operand").astype(float).to_numpy(), "lane"))
    if work["dataset"].nunique() > 1:
        columns.append(("dataset_holdout", (work["dataset"] == "holdout").astype(float).to_numpy(), "dataset"))

    x = np.column_stack([values for _, values, _ in columns])
    coefficients, _, _, _ = np.linalg.lstsq(x, y, rcond=None)
    residual = y - x @ coefficients
    sse = float(residual @ residual)
    sst = float(((y - y.mean()) ** 2).sum())
    r2 = 1.0 - sse / sst
    n, p = x.shape
    adjusted_r2 = 1.0 - (1.0 - r2) * (n - 1) / (n - p)

    coefficient_rows = [
        {
            "model": label,
            "term": name,
            "group": group,
            "standardized_response_coefficient": float(value),
        }
        for (name, _, group), value in zip(columns, coefficients)
    ]
    partial_rows: list[dict[str, object]] = []
    groups = sorted({group for _, _, group in columns if group != "intercept"})
    for group in groups:
        keep = [index for index, (_, _, column_group) in enumerate(columns) if column_group != group]
        reduced = x[:, keep]
        reduced_coef, _, _, _ = np.linalg.lstsq(reduced, y, rcond=None)
        reduced_residual = y - reduced @ reduced_coef
        reduced_sse = float(reduced_residual @ reduced_residual)
        partial = (reduced_sse - sse) / reduced_sse if reduced_sse > 0 else 0.0
        partial_rows.append({"model": label, "group": group, "drop_one_partial_R2": partial})

    summary = {
        "model": label,
        "rows": len(work),
        "predictor_columns": [name for name, _, _ in columns],
        "R2": r2,
        "adjusted_R2": adjusted_r2,
        "SSE": sse,
    }
    return summary, coefficient_rows + partial_rows


def summarize_routes(paths: list[Path]) -> tuple[pd.DataFrame, pd.DataFrame]:
    # Keep the registered decimal strings intact for comparisons. Several
    # reference errors are below binary64's normal range, so converting before
    # comparing can turn distinct values into an artificial tie at zero.
    frame = pd.concat(
        [pd.read_csv(path, dtype=str, keep_default_na=False) for path in paths],
        ignore_index=True,
    )
    numeric = (
        "error_direct",
        "error_response",
        "U_direct",
        "U_response",
        "effectivity_direct",
        "effectivity_response",
        "response_to_direct_error_ratio",
        "response_to_direct_bound_ratio",
        "relative_U_direct",
        "relative_U_response",
    )
    summaries: list[dict[str, object]] = []
    for (dataset, lane), group in frame.groupby(["dataset", "lane"], sort=True):
        response_lower_error_count = sum(
            Decimal(response) < Decimal(direct)
            for response, direct in zip(group["error_response"], group["error_direct"])
        )
        response_lower_bound_count = sum(
            Decimal(response) < Decimal(direct)
            for response, direct in zip(group["U_response"], group["U_direct"])
        )
        row: dict[str, object] = {
            "dataset": dataset,
            "lane": lane,
            "rows": len(group),
            "direct_coverage": int((group["direct_coverage"].astype(str).str.lower() == "true").sum()),
            "response_coverage": int((group["response_coverage"].astype(str).str.lower() == "true").sum()),
            "response_lower_error_count": int(response_lower_error_count),
            "response_lower_bound_count": int(response_lower_bound_count),
        }
        numeric_group = group.copy()
        for column in numeric:
            numeric_group[column] = pd.to_numeric(numeric_group[column], errors="coerce")
        for column in numeric:
            finite = numeric_group[column].replace([np.inf, -np.inf], np.nan).dropna()
            if column not in {"error_direct", "error_response", "U_direct", "U_response"}:
                row[f"{column}_median"] = float(finite.median())
                row[f"{column}_p95"] = percentile(finite, 0.95)
                row[f"{column}_log10_max"] = float(np.log10(finite.max()))
        summaries.append(row)
    return frame, pd.DataFrame(summaries)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True, type=Path)
    parser.add_argument("--base", required=True, type=Path)
    args = parser.parse_args()
    outputs = args.base / "analysis"
    outputs.mkdir(parents=True, exist_ok=True)

    p4 = args.project / "Paper2_G2_03r1_P4_UncertaintyCoverageRevision" / "outputs"
    anatomy = component_anatomy(
        "development",
        args.project / "Paper2_G2_03" / "matrix_families" / "decimal_systems.jsonl",
        p4 / "development_binary64_capture.csv",
        p4 / "development_results_run1.csv",
    )
    anatomy.extend(
        component_anatomy(
            "holdout",
            p4 / "holdout_decimal_systems.jsonl",
            p4 / "holdout_binary64_capture.csv",
            p4 / "holdout_results_run1.csv",
        )
    )
    anatomy_frame = pd.DataFrame(anatomy)
    anatomy_frame.to_csv(outputs / "Paper2_effectivity_anatomy.csv", index=False, lineterminator="\n")
    finite_anatomy = anatomy_frame.replace([np.inf, -np.inf], np.nan).dropna(
        subset=["parent_effectivity", "norm_majorant_inflation", "directional_alignment_inflation"]
    )
    anatomy_summary = (
        finite_anatomy.groupby(["dataset", "lane", "parent"], sort=True)
        .agg(
            rows=("system_id", "size"),
            effectivity_median=("parent_effectivity", "median"),
            norm_inflation_median=("norm_majorant_inflation", "median"),
            directional_inflation_median=("directional_alignment_inflation", "median"),
            norm_inflation_p95=("norm_majorant_inflation", lambda x: np.quantile(x, 0.95)),
            directional_inflation_p95=("directional_alignment_inflation", lambda x: np.quantile(x, 0.95)),
        )
        .reset_index()
    )
    anatomy_summary.to_csv(outputs / "Paper2_effectivity_anatomy_summary.csv", index=False, lineterminator="\n")

    direct = pd.read_csv(
        args.project / "Paper2_G2_18_EWC_FEAD_ExistingDataDeepening" / "Paper2_effectivity_per_case.csv"
    )
    direct["I_eff"] = pd.to_numeric(direct["I_eff"], errors="coerce")
    models: list[dict[str, object]] = []
    attribution_rows: list[dict[str, object]] = []
    for label, frame in (
        ("combined", direct),
        ("development", direct[direct["dataset"] == "development"]),
        ("holdout", direct[direct["dataset"] == "holdout"]),
    ):
        summary, rows = fit_model(frame, label)
        models.append(summary)
        attribution_rows.extend(rows)
    pd.DataFrame(attribution_rows).to_csv(
        outputs / "Paper2_multivariable_attribution.csv", index=False, lineterminator="\n"
    )

    finite_direct = direct[np.isfinite(direct["I_eff"]) & (direct["I_eff"] > 0)].copy()
    extreme = finite_direct.loc[finite_direct["I_eff"].idxmax()].to_dict()
    extreme["log10_I_eff"] = float(np.log10(float(extreme["I_eff"])))
    (outputs / "Paper2_extreme_ratio_record.json").write_text(
        json.dumps(extreme, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8"
    )

    route_frame, route_summary = summarize_routes(
        [
            args.base / "outputs" / "development_180_comparison.csv",
            args.base / "outputs" / "holdout_g2_20_180_comparison.csv",
        ]
    )
    route_frame.to_csv(outputs / "Paper2_response_route_per_case.csv", index=False, lineterminator="\n")
    route_summary.to_csv(outputs / "Paper2_response_route_summary.csv", index=False, lineterminator="\n")

    report = {
        "schema_version": "1.0",
        "component_rows": len(anatomy_frame),
        "component_zero_error_rows": int((anatomy_frame["status"] != "FINITE").sum()),
        "maximum_factorization_relative_residual": float(
            finite_anatomy["factorization_relative_residual"].max()
        ),
        "multivariable_models": models,
        "direct_extreme": extreme,
        "response_route_summary": route_summary.to_dict(orient="records"),
        "inference_boundary": "DESCRIPTIVE_FINITE_GRID_NO_POPULATION_LAW",
    }
    (outputs / "Paper2_G2_20_ANALYSIS.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
