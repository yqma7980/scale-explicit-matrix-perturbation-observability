from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import sys
from decimal import Decimal
from pathlib import Path


BASE = Path(__file__).resolve().parents[1]
PROJECT = BASE.parent
IMPLEMENTATION = BASE / "implementation"
INPUTS = BASE / "inputs"
OUTPUTS = BASE / "outputs"
LOGS = BASE / "logs"
CONTRACT = INPUTS / "g2_20_contract.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def run(label: str, arguments: list[str]) -> None:
    LOGS.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(arguments, text=True, capture_output=True, check=False)
    (LOGS / f"{label}.stdout.log").write_text(result.stdout, encoding="utf-8")
    (LOGS / f"{label}.stderr.log").write_text(result.stderr, encoding="utf-8")
    if result.returncode != 0:
        raise RuntimeError(f"{label} failed with exit code {result.returncode}")


def verify_fingerprints(contract: dict[str, object]) -> dict[str, str]:
    parent = contract["parent"]
    paths = {
        "manuscript_sha256": PROJECT
        / "Paper2_G2_19_FEAD_FullFigureRedesign"
        / "Paper2_scientific_candidate_v0.12.0.tex",
        "bibliography_sha256": PROJECT
        / "Paper2_G2_19_FEAD_FullFigureRedesign"
        / "Paper2_references_v0.11.0.bib",
        "development_systems_sha256": PROJECT
        / "Paper2_G2_03"
        / "matrix_families"
        / "decimal_systems.jsonl",
        "development_capture_sha256": PROJECT
        / "Paper2_G2_03r1_P4_UncertaintyCoverageRevision"
        / "outputs"
        / "development_binary64_capture.csv",
        "effectivity_rows_sha256": PROJECT
        / "Paper2_G2_18_EWC_FEAD_ExistingDataDeepening"
        / "Paper2_effectivity_per_case.csv",
        "route_rows_sha256": PROJECT
        / "Paper2_G2_18_EWC_FEAD_ExistingDataDeepening"
        / "inputs"
        / "route_validation_results.csv",
    }
    observed: dict[str, str] = {}
    for key, path in paths.items():
        value = sha256(path)
        observed[key] = value
        if value != str(parent[key]).upper():
            raise RuntimeError(f"Parent fingerprint mismatch for {key}: {value}")

    preregistered = {
        BASE / "G2_20_PRE_REGISTRATION_AND_SCOPE_LOCK.md": "8B553057A423300AD775949F524A594872DF5D87F51D1A0ECF450428B99A712B",
        CONTRACT: "61F30D5939B80F9D3756FB0E7AAC8787E1EDADAAF8008F892004FFCCBDB360D8",
    }
    for path, expected in preregistered.items():
        value = sha256(path)
        observed[path.name] = value
        if value != expected:
            raise RuntimeError(f"Preregistration fingerprint mismatch for {path.name}: {value}")
    return observed


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> int:
    if OUTPUTS.exists() and any(OUTPUTS.iterdir()):
        raise RuntimeError("Registered output directory is not empty; favorable reruns are forbidden")
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    LOGS.mkdir(parents=True, exist_ok=True)
    contract = load_json(CONTRACT)
    parent_hashes = verify_fingerprints(contract)

    development_source = PROJECT / "Paper2_G2_03" / "matrix_families" / "decimal_systems.jsonl"
    legacy_capture = (
        PROJECT
        / "Paper2_G2_03r1_P4_UncertaintyCoverageRevision"
        / "outputs"
        / "development_binary64_capture.csv"
    )
    holdout_source = OUTPUTS / "holdout_decimal_systems.jsonl"
    holdout_manifest = OUTPUTS / "holdout_manifest.csv"
    development_capture = OUTPUTS / "development_route_capture.csv"
    holdout_capture = OUTPUTS / "holdout_route_capture.csv"

    run(
        "01_generate_holdout",
        [
            sys.executable,
            str(IMPLEMENTATION / "generate_holdout.py"),
            "--contract",
            str(CONTRACT),
            "--output",
            str(holdout_source),
            "--manifest",
            str(holdout_manifest),
        ],
    )
    run(
        "02_capture_development",
        [
            sys.executable,
            str(IMPLEMENTATION / "capture_routes.py"),
            "--input",
            str(development_source),
            "--output",
            str(development_capture),
            "--compatibility-output",
            str(OUTPUTS / "development_capture_compatibility.json"),
            "--legacy-capture",
            str(legacy_capture),
        ],
    )
    run(
        "03_capture_holdout",
        [
            sys.executable,
            str(IMPLEMENTATION / "capture_routes.py"),
            "--input",
            str(holdout_source),
            "--output",
            str(holdout_capture),
            "--compatibility-output",
            str(OUTPUTS / "holdout_capture_compatibility.json"),
        ],
    )

    datasets = {
        "DEVELOPMENT": (development_source, development_capture),
        "HOLDOUT_G2_20": (holdout_source, holdout_capture),
    }
    for digits, run_name in ((120, "run1"), (120, "run2"), (180, "comparison")):
        for dataset, (source_path, capture_path) in datasets.items():
            slug = dataset.lower()
            output = OUTPUTS / f"{slug}_{digits}_{run_name}.csv"
            summary = OUTPUTS / f"{slug}_{digits}_{run_name}_summary.json"
            run(
                f"evaluate_{slug}_{digits}_{run_name}",
                [
                    sys.executable,
                    str(IMPLEMENTATION / "evaluate_routes.py"),
                    "--source",
                    str(source_path),
                    "--binary",
                    str(capture_path),
                    "--contract",
                    str(CONTRACT),
                    "--dataset",
                    dataset,
                    "--digits",
                    str(digits),
                    "--output",
                    str(output),
                    "--summary",
                    str(summary),
                ],
            )

    repeatability: dict[str, object] = {}
    precision: dict[str, object] = {}
    for dataset in datasets:
        slug = dataset.lower()
        run1 = OUTPUTS / f"{slug}_120_run1.csv"
        run2 = OUTPUTS / f"{slug}_120_run2.csv"
        repeatability[dataset] = {
            "run1_sha256": sha256(run1),
            "run2_sha256": sha256(run2),
            "exact": sha256(run1) == sha256(run2),
        }
        comparison_output = OUTPUTS / f"{slug}_precision_comparison.json"
        run(
            f"compare_precision_{slug}",
            [
                sys.executable,
                str(IMPLEMENTATION / "compare_precision.py"),
                "--lower",
                str(run1),
                "--higher",
                str(OUTPUTS / f"{slug}_180_comparison.csv"),
                "--output",
                str(comparison_output),
            ],
        )
        precision[dataset] = load_json(comparison_output)

    run(
        "decimal_backend_audit",
        [
            sys.executable,
            str(IMPLEMENTATION / "decimal_backend_audit.py"),
            "--source",
            str(holdout_source),
            "--binary",
            str(holdout_capture),
            "--primary",
            str(OUTPUTS / "holdout_g2_20_180_comparison.csv"),
            "--contract",
            str(CONTRACT),
            "--output",
            str(OUTPUTS / "decimal_backend_audit.csv"),
            "--summary",
            str(OUTPUTS / "decimal_backend_audit_summary.json"),
        ],
    )

    gates = contract["acceptance_gates"]
    summaries = {
        dataset: load_json(OUTPUTS / f"{dataset.lower()}_180_comparison_summary.json")
        for dataset in datasets
    }
    result_rows = {
        dataset: load_rows(OUTPUTS / f"{dataset.lower()}_180_comparison.csv")
        for dataset in datasets
    }
    gate_results: dict[str, object] = {}
    for dataset, summary in summaries.items():
        expected = int(contract["development" if dataset == "DEVELOPMENT" else "holdout"]["expected_rows"])
        for lane, expected_key in (
            ("DECIMAL_SOURCE", "source"),
            ("BINARY64_OPERAND", "binary"),
        ):
            lane_summary = summary["by_lane"][lane]
            gate_results[f"{dataset}_{expected_key}_response_coverage"] = (
                int(lane_summary["response_coverage_count"]) == expected
            )
            gate_results[f"{dataset}_{expected_key}_component_bounds"] = (
                int(lane_summary["component_failure_count"]) == 0
            )
            gate_results[f"{dataset}_{expected_key}_finite"] = int(lane_summary["nonfinite_count"]) == 0

    max_residual = max(
        Decimal(row["maximum_reference_relative_residual"])
        for rows in result_rows.values()
        for row in rows
    )
    max_precision = max(
        Decimal(str(value["maximum_normalized_difference"])) for value in precision.values()
    )
    bool_mismatch = sum(int(value["boolean_mismatch_count"]) for value in precision.values())
    decimal_summary = load_json(OUTPUTS / "decimal_backend_audit_summary.json")
    gate_results["reference_residual"] = max_residual <= Decimal(gates["reference_relative_residual_max"])
    gate_results["precision_120_180"] = (
        max_precision <= Decimal(gates["normalized_120_180_difference_max"]) and bool_mismatch == 0
    )
    gate_results["repeatability"] = all(bool(value["exact"]) for value in repeatability.values())
    gate_results["independent_decimal_backend"] = bool(decimal_summary["pass"])
    gate_results["development_capture_compatibility"] = (
        int(load_json(OUTPUTS / "development_capture_compatibility.json")["mismatch_count"]) == 0
    )

    coverage_failures = [key for key, value in gate_results.items() if "coverage" in key and not value]
    if coverage_failures:
        classification = "FAIL_RESPONSE_ROUTE_FALSE_ENCLOSURE"
    elif not all(bool(value) for value in gate_results.values()):
        classification = "INCONCLUSIVE_REFERENCE_OR_PRECISION_FAILURE"
    else:
        classification = "PASS_RESPONSE_ROUTE_ENCLOSURE_VALIDATED_ON_DEVELOPMENT_AND_NEW_HOLDOUT"

    status = {
        "schema_version": "1.0",
        "classification": classification,
        "parent_fingerprints": parent_hashes,
        "holdout_sha256": sha256(holdout_source),
        "holdout_rows": len(load_rows(holdout_manifest)),
        "repeatability": repeatability,
        "precision_comparison": precision,
        "independent_decimal_backend": decimal_summary,
        "maximum_reference_relative_residual": str(max_residual),
        "maximum_normalized_120_180_difference": str(max_precision),
        "precision_boolean_mismatch_count": bool_mismatch,
        "gate_results": gate_results,
    }
    (BASE / "G2_20_FINAL_STATUS.json").write_text(
        json.dumps(status, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    hashes: list[dict[str, str]] = []
    for path in sorted(BASE.rglob("*")):
        if path.is_file() and "logs" not in path.parts and path.name != "G2_20_SHA256SUMS.csv":
            hashes.append({"path": path.relative_to(BASE).as_posix(), "sha256": sha256(path)})
    with (BASE / "G2_20_SHA256SUMS.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=("path", "sha256"), lineterminator="\n")
        writer.writeheader()
        writer.writerows(hashes)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
