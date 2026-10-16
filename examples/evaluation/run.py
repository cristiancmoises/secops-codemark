#!/usr/bin/env python3
"""Run the frozen synthetic comparison with existing, explicitly chosen tools."""

import argparse
import datetime
import hashlib
import importlib
import json
import os
import platform
import shutil
import subprocess
import sys
import time
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
JAR_SHA256 = "5f2c21e8b88ed77134effcb3a5a3ab13d188f6a3e16d401387f7479e92db9aa2"
JAVA_OPTIONS = [
    "-XX:ActiveProcessorCount=2",
    "-Xmx256m",
    "-XX:ReservedCodeCacheSize=64m",
    "-XX:CompressedClassSpaceSize=32m",
]


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def runtime_hashes():
    return {
        path.name: sha256(path) for path in sorted((PROJECT / "codemark").glob("*.py"))
    }


def execute(arguments, directory, environment):
    start = time.perf_counter()
    try:
        result = subprocess.run(
            [str(value) for value in arguments],
            cwd=directory,
            env=environment,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            timeout=60,
            check=False,
        )
        return {
            "command": [str(value) for value in arguments],
            "returncode": result.returncode,
            "stdout": result.stdout.decode("utf-8", "replace"),
            "stderr": result.stderr.decode("utf-8", "replace"),
            "wall_seconds": time.perf_counter() - start,
        }
    except subprocess.TimeoutExpired as error:
        return {
            "command": [str(value) for value in arguments],
            "returncode": None,
            "error": "timeout after 60 seconds",
            "stdout": (error.stdout or b"").decode("utf-8", "replace"),
            "stderr": (error.stderr or b"").decode("utf-8", "replace"),
            "wall_seconds": time.perf_counter() - start,
        }


def copydetect_worker(args):
    if args.worker_output is None:
        raise ValueError("The Copydetect worker needs an output path")
    if args.copydetect_path:
        sys.path.insert(0, str(args.copydetect_path.resolve()))
    copydetect = importlib.import_module("copydetect")
    detector = copydetect.CopyDetector(
        test_dirs=[str(args.corpus / "candidates")],
        ref_dirs=[str(args.corpus / "reference")],
        extensions=["py"],
        autoopen=False,
        silent=True,
    )
    detector.run()
    pairs = []
    for i, test in enumerate(detector.test_files):
        for j, reference in enumerate(detector.ref_files):
            first, second = detector.similarity_matrix[i, j]
            pairs.append(
                {
                    "candidate": Path(test).parent.name,
                    "reference": str(Path(reference).relative_to(args.corpus)),
                    "candidate_coverage": float(first),
                    "reference_coverage": float(second),
                    "mean_coverage": float((first + second) / 2),
                    "overlapping_filtered_characters": int(
                        detector.token_overlap_matrix[i, j]
                    ),
                }
            )
    args.worker_output.write_text(
        json.dumps(
            {
                "version": copydetect.__version__,
                "defaults": {
                    "noise_t": detector.conf.noise_t,
                    "guarantee_t": detector.conf.guarantee_t,
                    "display_t": detector.conf.display_t,
                },
                "pairs": pairs,
            },
            indent=2,
        )
        + "\n"
    )


def jplag_artifacts(directory, archive):
    artifacts = {"json": {}, "csv": {}}
    archive_hash = None
    for path in directory.rglob("*.csv"):
        artifacts["csv"][path.relative_to(directory).as_posix()] = path.read_text()
    if archive.is_file():
        archive_hash = sha256(archive)
        with zipfile.ZipFile(archive) as bundle:
            for name in bundle.namelist():
                if name.endswith(".json"):
                    artifacts["json"][name] = json.loads(bundle.read(name))
                elif name.endswith(".csv"):
                    artifacts["csv"][name] = bundle.read(name).decode("utf-8")
    return {**artifacts, "archive_sha256": archive_hash}


def jplag_pairs(artifacts):
    pairs = []
    documents = artifacts["json"]
    mappings = documents["submissionMappings.json"]["submissionIds"]
    for name, comparison in documents.items():
        if not name.startswith("comparisons/"):
            continue
        first = mappings[comparison["firstSubmissionId"]]
        second = mappings[comparison["secondSubmissionId"]]
        if "reference/original" not in (first, second):
            continue
        candidate_first = second == "reference/original"
        candidate = first if candidate_first else second
        similarities = comparison["similarities"]
        if not 0 <= similarities["AVG"] <= 1:
            raise ValueError("Unexpected JPlag average similarity scale")
        pairs.append(
            {
                "candidate": Path(candidate).name,
                "average_similarity": similarities["AVG"],
                "candidate_similarity": comparison[
                    "firstSimilarity" if candidate_first else "secondSimilarity"
                ],
                "reference_similarity": comparison[
                    "secondSimilarity" if candidate_first else "firstSimilarity"
                ],
                "native_similarities": similarities,
            }
        )
    return pairs


def observations(manifest, runs):
    rows = []
    threshold = manifest["settings"]["illustrative_observation_threshold"]
    for run in runs:
        scores = {pair["candidate"]: pair for pair in run.get("pairs", [])}
        for case in manifest["cases"]:
            pair = scores.get(case["id"])
            completed = "error" not in run and "adapter_error" not in run
            score = None
            if pair is not None:
                field = {
                    "codemark": "similarity",
                    "copydetect": "mean_coverage",
                    "jplag": "average_similarity",
                }[run["tool"]]
                score = pair[field]
            rows.append(
                {
                    "tool": run["tool"],
                    "repeat": run["repeat"],
                    "case": case["id"],
                    "expected_derived_copy": case["derived_from_reference"],
                    "raw_score": score,
                    "reported": pair is not None,
                    "run_completed": completed,
                    "illustrative_at_least_0_65": None
                    if score is None
                    else score >= threshold,
                    "absence_meaning": (
                        "Tool or adapter did not complete; no score was produced."
                        if not completed
                        else "No reported candidate; quality gate or zero, not an invented zero score."
                    )
                    if pair is None
                    else None,
                }
            )
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, default=HERE / "corpus")
    parser.add_argument("--jplag-jar", type=Path)
    parser.add_argument(
        "--copydetect-path",
        type=Path,
        help="existing unpacked packages; optional when Copydetect is installed",
    )
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--java-resource-profile",
        choices=["initial", "serialgc"],
        default="serialgc",
        help="serialgc adds SerialGC/Xms32m; initial reproduces the original resource profile",
    )
    parser.add_argument("--worker", choices=["copydetect"], help=argparse.SUPPRESS)
    parser.add_argument("--worker-output", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    args.corpus = args.corpus.resolve()
    if args.worker:
        copydetect_worker(args)
        return 0
    if args.jplag_jar is None or args.output is None:
        parser.error("--jplag-jar and a new --output directory are required")
    args.jplag_jar = args.jplag_jar.resolve()
    if sha256(args.jplag_jar) != JAR_SHA256:
        parser.error("JPlag JAR differs from the frozen 6.3.0 artifact")
    manifest_path = args.corpus / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    for name, expected in manifest["files"].items():
        path = args.corpus / name
        if sha256(path) != expected["sha256"]:
            parser.error("Frozen corpus differs: " + name)
        if b"CodeMark v1 project=" in path.read_bytes():
            parser.error("Corpus contains an inherited watermark: " + name)
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    java_options = list(JAVA_OPTIONS)
    if args.java_resource_profile == "serialgc":
        java_options.extend(["-XX:+UseSerialGC", "-Xms32m"])
    before = runtime_hashes()
    runs = []
    for repeat in range(1, manifest["settings"]["repeats"] + 1):
        trial = output / f"repeat-{repeat}"
        trial.mkdir()
        environment = dict(
            os.environ,
            MPLBACKEND="Agg",
            MPLCONFIGDIR=str(trial / "cache"),
            OPENBLAS_NUM_THREADS="2",
            OMP_NUM_THREADS="2",
        )
        marked = trial / "marked-reference"
        shutil.copytree(args.corpus / "reference", marked)
        mark = execute(
            [
                sys.executable,
                "-m",
                "codemark",
                "mark",
                marked,
                "--owner",
                "Synthetic evaluation fixture",
                "--apply",
                "--json",
            ],
            PROJECT,
            environment,
        )
        comparison = execute(
            [
                sys.executable,
                "-m",
                "codemark",
                "compare",
                marked,
                args.corpus / "candidates",
                "--threshold",
                "1e-9",
                "--json",
            ],
            PROJECT,
            environment,
        )
        run = {
            "tool": "codemark",
            "repeat": repeat,
            "processes": [mark, comparison],
            "wall_seconds": mark["wall_seconds"] + comparison["wall_seconds"],
            "pairs": [],
        }
        if mark["returncode"] == 0 and comparison["returncode"] in (0, 1):
            report = json.loads(comparison["stdout"])
            run["pairs"] = [
                {
                    **pair,
                    "candidate_path": pair["candidate"],
                    "candidate": Path(pair["candidate"]).parent.name,
                }
                for pair in report["matches"]
            ]
        else:
            run["error"] = "CodeMark mark/compare did not complete"
        runs.append(run)
        worker_output = trial / "copydetect.json"
        command = [
            sys.executable,
            Path(__file__).resolve(),
            "--worker",
            "copydetect",
            "--corpus",
            args.corpus,
            "--worker-output",
            worker_output,
        ]
        if args.copydetect_path:
            command.extend(["--copydetect-path", args.copydetect_path.resolve()])
        process = execute(command, PROJECT, environment)
        run = {
            "tool": "copydetect",
            "repeat": repeat,
            "processes": [process],
            "wall_seconds": process["wall_seconds"],
        }
        if process["returncode"] == 0 and worker_output.is_file():
            run.update(json.loads(worker_output.read_text()))
        else:
            run["error"] = "Copydetect worker did not complete"
        runs.append(run)
        jplag = trial / "jplag"
        jplag.mkdir()
        archive = jplag / "results.jplag"
        process = execute(
            [
                "java",
                *java_options,
                "-jar",
                args.jplag_jar,
                "--mode",
                "RUN",
                "--language",
                "python3",
                "--new",
                args.corpus / "candidates",
                "--old",
                args.corpus / "reference",
                "--csv-export",
                "--shown-comparisons",
                "-1",
                "--result-file",
                archive,
            ],
            jplag,
            environment,
        )
        run = {
            "tool": "jplag",
            "repeat": repeat,
            "processes": [process],
            "wall_seconds": process["wall_seconds"],
            "pairs": [],
        }
        run["raw_artifacts"] = jplag_artifacts(jplag, archive)
        if process["returncode"] == 0:
            try:
                run["pairs"] = jplag_pairs(run["raw_artifacts"])
            except (KeyError, TypeError, ValueError) as error:
                run["adapter_error"] = type(error).__name__ + ": " + str(error)
        else:
            run["error"] = "JPlag did not complete"
        runs.append(run)
        (output / "partial-results.json").write_text(json.dumps(runs, indent=2) + "\n")
    result = {
        "schema": 1,
        "recorded_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "corpus_manifest_sha256": sha256(manifest_path),
        "corpus_manifest": manifest,
        "environment": {
            "system": platform.system(),
            "machine": platform.machine(),
            "python": platform.python_version(),
            "network": "Execution isolation is supplied by the caller; this runner never downloads or installs tools.",
        },
        "runtime_source_sha256": before,
        "runtime_source_changed_during_run": before != runtime_hashes(),
        "jplag_jar_sha256": sha256(args.jplag_jar),
        "jplag_java_options": java_options,
        "java_resource_profile": args.java_resource_profile,
        "runner_sha256": sha256(Path(__file__)),
        "runs": runs,
        "observations": observations(manifest, runs),
        "timing_scope": "Full subprocess wall time: CodeMark mark plus compare; Copydetect startup/import/fingerprint/compare; JPlag JVM startup/version network probe/parsing/comparison/export. No speed ranking is supported.",
    }
    destination = output / "similarity-results.json"
    destination.write_text(json.dumps(result, indent=2) + "\n")
    errors = sum("error" in run or "adapter_error" in run for run in runs)
    print(
        json.dumps(
            {
                "report": str(destination),
                "runs": len(runs),
                "errors": errors,
                "runtime_source_changed": result["runtime_source_changed_during_run"],
            }
        )
    )
    return int(bool(errors or result["runtime_source_changed_during_run"]))


if __name__ == "__main__":
    raise SystemExit(main())
