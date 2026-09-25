"""Standard-library replay of anonymous, already-computed SRLE risk aggregates."""

from pathlib import Path
import argparse
import csv
import hashlib
import json
import math


MODELS = ("composition", "kmer123", "position_additive", "position_pair")
DIRECTIONS = (-1, 1)
REPLICATES = (1, 2)
CLASSES = tuple(range(60))
GROUP_METRICS = (
    "mean_directed_change", "fraction_positive", "fraction_negative",
    "fraction_numerical_tie", "mean_loss_including_zero",
    "fraction_benefit_at_least_0_1", "fraction_harm_at_least_0_1",
)
PAIR_METRICS = (
    "fraction_positive_both", "fraction_negative_both",
    "fraction_opposite_signs", "fraction_involving_tie",
    "mean_smaller_directed_change",
)
MEMBERS = (
    "README.md", "replay.py", "fixed_groups.csv", "fixed_pairs.csv",
    "uniform_groups.csv", "uniform_pairs.csv", "bootstrap_indices.csv",
    "fixed_result.json", "uniform_result.json", "fixed_spec.md",
    "uniform_spec.md", "provenance.json",
)
TOLERANCE = 1e-12
SCHEMAS = {
    "fixed_groups.csv": ("class_id", "model", "direction", "replicate", "parent_count") + GROUP_METRICS,
    "fixed_pairs.csv": ("class_id", "model", "direction") + PAIR_METRICS,
    "uniform_groups.csv": ("direction", "replicate") + GROUP_METRICS + ("parent_count", "class_id"),
    "uniform_pairs.csv": ("direction",) + PAIR_METRICS + ("parent_count", "class_id"),
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path):
    def reject_constant(value):
        raise ValueError("Nonfinite JSON constant: " + value)
    return json.loads(path.read_text(encoding="utf-8"), parse_constant=reject_constant)


def verify_members(directory):
    expected = set(MEMBERS) | {"integrity.json"}
    require({p.name for p in directory.iterdir()} == expected, "Unexpected or missing package member")
    require(all((directory / name).is_file() and not (directory / name).is_symlink()
                for name in expected), "Members must be regular nonsymlink files")
    manifest = read_json(directory / "integrity.json")
    require(set(manifest) == set(MEMBERS), "Integrity manifest member mismatch")
    for name in MEMBERS:
        require(sha256(directory / name) == manifest[name], "SHA256 mismatch: " + name)
    return len(MEMBERS)


def integer(value, field):
    result = int(value)
    require(str(result) == value, "Noncanonical integer: " + field)
    return result


def read_rows(directory, name):
    fixed = name.startswith("fixed")
    paired = "pairs" in name
    metrics = PAIR_METRICS if paired else GROUP_METRICS
    result = {}
    with (directory / name).open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        require(tuple(reader.fieldnames or ()) == SCHEMAS[name], "CSV schema mismatch: " + name)
        for row in reader:
            require(set(row) == set(SCHEMAS[name]) and all(v is not None for v in row.values()),
                    "Malformed CSV row: " + name)
            class_id = integer(row["class_id"], "class_id")
            direction = integer(row["direction"], "direction")
            require(class_id in CLASSES and direction in DIRECTIONS, "Invalid class or direction")
            prefix = ()
            if fixed:
                require(row["model"] in MODELS, "Unknown model")
                prefix = (row["model"],)
            key = prefix + (direction,)
            if not paired:
                replicate = integer(row["replicate"], "replicate")
                require(replicate in REPLICATES, "Invalid replicate")
                key += (replicate,)
            key += (class_id,)
            require(key not in result, "Duplicate class/cohort row")
            values = {metric: float(row[metric]) for metric in metrics}
            require(all(math.isfinite(v) for v in values.values()), "Nonfinite CSV metric")
            for metric, value in values.items():
                if metric.startswith("fraction_"):
                    require(0 <= value <= 1, "Fraction outside [0,1]")
            fractions = PAIR_METRICS[:4] if paired else GROUP_METRICS[1:4]
            require(abs(math.fsum(values[m] for m in fractions) - 1) <= TOLERANCE,
                    "Sign fractions do not sum to one")
            if not paired:
                require(values["mean_loss_including_zero"] >= 0, "Negative loss")
                require(values["fraction_benefit_at_least_0_1"] <= values["fraction_positive"] + TOLERANCE,
                        "Benefit fraction exceeds positive fraction")
                require(values["fraction_harm_at_least_0_1"] <= values["fraction_negative"] + TOLERANCE,
                        "Harm fraction exceeds negative fraction")
            if "parent_count" in row:
                values["parent_count"] = integer(row["parent_count"], "parent_count")
                require(values["parent_count"] > 0, "Nonpositive class parent count")
            result[key] = values
    models = MODELS if fixed else (None,)
    reps = (None,) if paired else REPLICATES
    expected = set()
    for model in models:
        for direction in DIRECTIONS:
            for replicate in reps:
                for class_id in CLASSES:
                    key = (() if model is None else (model,)) + (direction,)
                    if replicate is not None:
                        key += (replicate,)
                    expected.add(key + (class_id,))
    require(set(result) == expected, "Incomplete class-balanced cohort: " + name)
    return result


def read_draws(directory):
    with (directory / "bootstrap_indices.csv").open(encoding="utf-8", newline="") as handle:
        draws = [[integer(x, "bootstrap index") for x in row] for row in csv.reader(handle)]
    require(len(draws) == 2000 and all(len(row) == 60 for row in draws), "Bootstrap shape mismatch")
    require(all(i in CLASSES for row in draws for i in row), "Bootstrap index outside 0..59")
    return draws


def mean(values):
    return math.fsum(values) / len(values)


def quantile(values, probability):
    ordered = sorted(values)
    location = (len(ordered) - 1) * probability
    lower, upper = math.floor(location), math.ceil(location)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (location - lower)


def summarize(values, draws):
    require(len(values) == 60, "Summary must contain 60 equally weighted classes")
    sampled = [mean([values[i] for i in indices]) for indices in draws]
    return {"estimate": mean(values), "descriptive_ci95": [quantile(sampled, 0.025), quantile(sampled, 0.975)]}


def direction_summary(groups, pairs, prefix, direction, draws, reference_groups=None, reference_pairs=None):
    def values(table, metric, suffix, reference):
        answer = [table[prefix + suffix + (c,)][metric] for c in CLASSES]
        if reference is not None:
            answer = [v - reference[suffix + (c,)][metric] for c, v in zip(CLASSES, answer)]
        return answer
    return {
        "replicates": {
            str(rep): {metric: summarize(values(groups, metric, (direction, rep), reference_groups), draws)
                       for metric in GROUP_METRICS}
            for rep in REPLICATES
        },
        "paired_replicates": {
            metric: summarize(values(pairs, metric, (direction,), reference_pairs), draws)
            for metric in PAIR_METRICS
        },
    }


def compare(actual, expected, path="summary"):
    if isinstance(actual, dict):
        require(isinstance(expected, dict) and set(actual) == set(expected), "Summary keys differ: " + path)
        return [difference for key in actual for difference in compare(actual[key], expected[key], path + "." + key)]
    if isinstance(actual, list):
        require(isinstance(expected, list) and len(actual) == len(expected), "Summary list differs: " + path)
        return [difference for i, value in enumerate(actual)
                for difference in compare(value, expected[i], path + "[" + str(i) + "]")]
    require(type(expected) in (int, float) and math.isfinite(expected), "Invalid expected number: " + path)
    difference = abs(actual - expected)
    require(difference <= TOLERANCE, "Numeric discrepancy exceeds tolerance: " + path)
    return [difference]


def replay(directory):
    directory = Path(directory).resolve()
    member_count = verify_members(directory)
    tables = {name: read_rows(directory, name) for name in SCHEMAS}
    fixed_groups, fixed_pairs = tables["fixed_groups.csv"], tables["fixed_pairs.csv"]
    uniform_groups, uniform_pairs = tables["uniform_groups.csv"], tables["uniform_pairs.csv"]
    counts = {c: fixed_groups[(MODELS[0], -1, 1, c)]["parent_count"] for c in CLASSES}
    require(sum(counts.values()) == 592, "Parent total mismatch")
    for table in (fixed_groups, uniform_groups, uniform_pairs):
        require(all(row["parent_count"] == counts[key[-1]] for key, row in table.items()),
                "Class parent counts differ between cohorts")
    fixed = read_json(directory / "fixed_result.json")
    uniform = read_json(directory / "uniform_result.json")
    for result in (fixed, uniform):
        require(result["bootstrap"] == {"draws": 2000, "seed": 20260921, "unit": "composition class"},
                "Unexpected archived bootstrap declaration")
        for key in ("choices_changed", "models_fit", "gates_changed"):
            require(result[key] == 0, "Archived scope mismatch: " + key)
        for key in ("new_outcomes", "sequence_identifiers_exported"):
            require(result[key] is False, "Archived scope mismatch: " + key)
    require(fixed["classes"] == 60 and fixed["parents"] == 592, "Archived cohort mismatch")
    require(fixed["tie_tolerance"] == 1e-12 and fixed["fixed_descriptive_scale"] == 0.1,
            "Archived descriptive threshold mismatch")
    for local_name, original_name in (
        ("fixed_groups.csv", "srle_fixed_choice_risk_groups_20260924.csv"),
        ("fixed_pairs.csv", "srle_fixed_choice_risk_pairs_20260924.csv"),
        ("uniform_groups.csv", "srle_uniform_risk_groups_20260924.csv"),
        ("uniform_pairs.csv", "srle_uniform_risk_pairs_20260924.csv"),
    ):
        original = fixed["output_hashes"] if local_name.startswith("fixed") else uniform["outputs"]
        require(sha256(directory / local_name) == original["results/research_20260921/" + original_name],
                "Archived CSV hash mismatch: " + local_name)
    draws = read_draws(directory)
    actual_fixed = {model: {str(direction): direction_summary(fixed_groups, fixed_pairs, (model,), direction, draws)
                            for direction in DIRECTIONS} for model in MODELS}
    actual_uniform = {
        "uniform": {str(direction): direction_summary(uniform_groups, uniform_pairs, (), direction, draws)
                    for direction in DIRECTIONS},
        "model_minus_uniform": {
            model: {str(direction): direction_summary(fixed_groups, fixed_pairs, (model,), direction, draws,
                                                      uniform_groups, uniform_pairs)
                    for direction in DIRECTIONS} for model in MODELS
        },
    }
    fixed_differences = compare(actual_fixed, fixed["models"], "fixed")
    uniform_differences = compare(actual_uniform, uniform["comparisons"], "uniform")
    require(len(fixed_differences) == 456 and len(uniform_differences) == 570, "Unexpected comparison count")
    return {
        "status": "PASS", "scope": "Aggregation arithmetic only; conditional posthoc shared-experiment summaries.",
        "integrity_members_checked": member_count, "csv_rows": {name: len(table) for name, table in tables.items()},
        "classes_per_cohort": 60, "class_balanced_cohorts": 30, "parents_per_cohort": 592,
        "models": list(MODELS), "directions": list(DIRECTIONS), "replicates": list(REPLICATES),
        "bootstrap_draws": len(draws), "classes_per_draw": 60,
        "fixed_statistics": len(fixed_differences) // 3, "uniform_statistics": len(uniform_differences) // 3,
        "estimates_checked": (len(fixed_differences) + len(uniform_differences)) // 3,
        "ci_endpoints_checked": 2 * (len(fixed_differences) + len(uniform_differences)) // 3,
        "numeric_comparisons": len(fixed_differences) + len(uniform_differences),
        "max_absolute_discrepancy": max(fixed_differences + uniform_differences),
        "absolute_tolerance": TOLERANCE,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", nargs="?", type=Path, default=Path(__file__).resolve().parent)
    print(json.dumps(replay(parser.parse_args().directory), sort_keys=True, indent=2, allow_nan=False))
