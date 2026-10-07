"""Scoped original-author lineage checks; no fits or protected outcome reads."""
from .common import ROOT, OUT, REP, np, pd, sha256, readj, jsave, save
from collections import defaultdict, Counter
from pathlib import Path
import json
import re
import zipfile
import xml.etree.ElementTree as ET

CORE = ROOT / "results/probabilistic_ranking_20260928/candidate_index.csv"
MIKL = ROOT / "data/raw/mikl_gse173098/supplementary/files/SupplementaryData_NAR_Final/SupplementaryTables/TableS2.csv"
MOFF = ROOT / "data/raw/moffatt_gse334718/supplementary/supplementary_table_3.csv"
FASTA = MOFF.with_name("supplementary_file_1.txt")
ASTRO = ROOT / "data/raw/astrocyte_gse330741/supplementary/media-1.xlsx"
SEQ = "full library sequence (primers-barcode-test sequence)"
XML = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
NS = "{" + XML["m"] + "}"
TOL = 5e-10


def selected_csv(path, columns, indexes, metadata_rows):
    """Physical-row restriction verified before numeric-column access."""
    payload = path.read_bytes()
    assert payload.count(b"\n") == metadata_rows + 1, "Multiline CSV requires another scoped reader"
    assert payload.endswith(b"\n")
    indexes = sorted(set(int(i) for i in indexes))
    assert indexes and min(indexes) >= 0 and max(indexes) < metadata_rows
    keep = {i + 1 for i in indexes}
    result = pd.read_csv(path, usecols=columns, skiprows=lambda i: i != 0 and i not in keep,
                         float_precision="round_trip")
    assert len(result) == len(indexes)
    result.index = indexes
    return result


def shared_strings(archive, requested):
    requested = set(requested)
    if not requested:
        return {}
    output, index = {}, 0
    with archive.open("xl/sharedStrings.xml") as stream:
        for event, item in ET.iterparse(stream, events=("end",)):
            if item.tag == NS + "si":
                if index in requested:
                    output[index] = "".join(node.text or "" for node in item.iter(NS + "t"))
                index += 1
                item.clear()
    assert set(output) == requested
    return output


def cell_raw(cell):
    kind = cell.attrib.get("t", "n")
    if kind == "inlineStr":
        return kind, "".join(node.text or "" for node in cell.iter(NS + "t"))
    return kind, cell.findtext(NS + "v")


def resolved(raw, strings):
    kind, value = raw
    return strings[int(value)] if kind == "s" else value


def scoped_sheet(path, sheet_name, key_column, allowed_ids, columns):
    """Read metadata keys first; numeric cells only on approved author rows.

    No other worksheet or outcome column is materialized. Shared-string text
    is decoded only for headers, row keys and requested selected cells.
    """
    with zipfile.ZipFile(path) as archive:
        workbook = ET.fromstring(archive.read("xl/workbook.xml"))
        sheets = {item.attrib["name"]: item.attrib["{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"]
                  for item in workbook.findall("m:sheets/m:sheet", XML)}
        rels = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
        targets = {item.attrib["Id"]: item.attrib["Target"] for item in rels}
        target = targets[sheets[sheet_name]]
        member = target.lstrip("/") if target.startswith("/") else "xl/" + target
        with archive.open(member) as stream:
            for event, row in ET.iterparse(stream, events=("end",)):
                if row.tag == NS + "row":
                    assert int(row.attrib["r"]) == 1
                    headers = {re.sub(r"\d+$", "", cell.attrib["r"]): cell_raw(cell) for cell in row if cell.tag == NS + "c"}
                    break
        strings = shared_strings(archive, [int(value) for kind, value in headers.values() if kind == "s"])
        column_map = {resolved(raw, strings): letter for letter, raw in headers.items()}
        assert set(columns) <= set(column_map) and key_column in columns
        key_letter = column_map[key_column]
        keys = {}
        with archive.open(member) as stream:
            for event, row in ET.iterparse(stream, events=("end",)):
                if row.tag != NS + "row":
                    continue
                number = int(row.attrib["r"])
                if number != 1:
                    for cell in row:
                        if cell.tag == NS + "c" and re.sub(r"\d+$", "", cell.attrib["r"]) == key_letter:
                            keys[number] = cell_raw(cell)
                row.clear()
        key_strings = shared_strings(archive, [int(value) for kind, value in keys.values() if kind == "s"])
        row_ids = {number: str(resolved(raw, key_strings)) for number, raw in keys.items()}
        selected_rows = {number for number, key in row_ids.items() if key in allowed_ids}
        assert {row_ids[number] for number in selected_rows} == set(allowed_ids)
        wanted_letters = {column_map[column]: column for column in columns}
        raw_rows = []
        with archive.open(member) as stream:
            for event, row in ET.iterparse(stream, events=("end",)):
                if row.tag != NS + "row":
                    continue
                number = int(row.attrib["r"])
                if number in selected_rows:
                    values = {"excel_row": number}
                    for cell in row:
                        letter = re.sub(r"\d+$", "", cell.attrib["r"])
                        if letter in wanted_letters:
                            values[wanted_letters[letter]] = cell_raw(cell)
                    raw_rows.append(values)
                row.clear()
        strings = shared_strings(archive, [int(value) for row in raw_rows for column, raw in row.items()
                                           if column != "excel_row" for kind, value in [raw] if kind == "s"])
        rows = [{column: resolved(value, strings) if column != "excel_row" else value
                 for column, value in row.items()} for row in raw_rows]
        result = pd.DataFrame(rows)
        assert not result[key_column].duplicated().any()
        assert set(result[key_column]) == set(allowed_ids)
        return result.set_index(key_column)


def compare_effect(actual, expected):
    actual, expected = np.asarray(actual, float), np.asarray(expected, float)
    assert actual.shape == expected.shape and np.isfinite(actual).all() and np.isfinite(expected).all()
    error = float(np.max(np.abs(actual - expected), initial=0.))
    assert error <= TOL, ("Author effect discrepancy", error)
    return error


def audit_mikl(core):
    frame = core[core.dataset.eq("mikl_gse173098")].copy()
    lineage_path = ROOT / "results/v4_phaseA/mikl_interventions.csv.gz"
    lineage = pd.read_csv(lineage_path, usecols=["source_row", "mutant_id", "parent_id", "parent_sequence", "mutant_sequence", "motif_family", "parent_barcode_construct_count"])
    selected = lineage[lineage.mutant_id.isin(frame.mutant_id)].copy()
    assert selected.mutant_id.is_unique and set(selected.mutant_id) == set(frame.mutant_id)
    metadata = pd.read_csv(MIKL, usecols=["Unnamed: 0", "gene name", "position in 3UTR", "subset", "changes", SEQ])
    assert len(metadata) == 47347 and metadata[SEQ].is_unique
    assert set(metadata[SEQ].str.len()) == {198}
    metadata["insert"] = metadata[SEQ].str.upper().str.slice(30, 180)
    assert metadata["insert"].str.fullmatch("[ACGT]{150}").all()
    wts = metadata[metadata.subset.eq("wt scanning 50")]
    groups = {(str(gene), position): group for (gene, position), group in wts.groupby(["gene name", "position in 3UTR"], dropna=False)}
    pairs, needed = {}, set()
    for row in selected.itertuples():
        source = metadata.loc[int(row.source_row)]
        assert source["subset"] == "mut scanning 50"
        mutant = source["insert"]
        assert mutant == row.mutant_sequence
        motif = str(source["changes"]).split(" replaced by random", 1)[0].upper()
        assert motif == row.motif_family and re.fullmatch("[ACGT]+", motif)
        candidates = groups[(str(source["gene name"]), source["position in 3UTR"])]
        accepted = []
        for parent in candidates["insert"].unique():
            covered = {position for start in range(len(parent) - len(motif) + 1)
                       if parent[start:start + len(motif)] == motif for position in range(start, start + len(motif))}
            changed = {i for i, (a, b) in enumerate(zip(parent, mutant)) if a != b}
            if changed and covered and changed <= covered:
                accepted.append(parent)
        assert accepted == [row.parent_sequence], "Semantic parent is missing, different, or ambiguous"
        parent_rows = candidates.index[candidates["insert"].eq(accepted[0])].tolist()
        assert len(parent_rows) == row.parent_barcode_construct_count
        needed.update(parent_rows); needed.add(int(row.source_row))
        pairs[row.mutant_id] = (int(row.source_row), parent_rows)
    effect_columns = {"CAD": "logFC(neurite/soma) - CAD", "Neuro-2a": "logFC(neurite/soma) - Neuro-2a"}
    errors, nonfinite_parents, examples = {}, {}, []
    for cell, column in effect_columns.items():
        rows = frame[frame.cell_type.eq(cell)]
        cell_needed = set()
        for identifier in rows.mutant_id:
            index, parent_rows = pairs[identifier]
            cell_needed.add(index); cell_needed.update(parent_rows)
        numeric = selected_csv(MIKL, [column], cell_needed, len(metadata))
        expected, parent_values, mutant_values = [], [], []
        nonfinite = 0
        for row in rows.itertuples():
            index, parent_rows = pairs[row.mutant_id]
            parent_vector = numeric.loc[parent_rows, column]
            nonfinite += int((~np.isfinite(parent_vector)).sum())
            parent = float(parent_vector.mean())
            mutant = float(numeric.loc[index, column])
            expected.append(mutant - parent); parent_values.append(parent); mutant_values.append(mutant)
        errors[cell] = {"rows": len(rows), "delta_max_absolute_error": compare_effect(rows.measured_delta, expected)}
        # Some canonical adapters intentionally store no absolute Mikl endpoint;
        # only test those fields if every value is present.
        for field, values in [("measured_parent_localization", parent_values), ("measured_mutant_localization", mutant_values)]:
            if np.isfinite(rows[field].to_numpy(float)).all():
                errors[cell][field + "_max_absolute_error"] = compare_effect(rows[field], values)
        nonfinite_parents[cell] = nonfinite
        for row in rows.sort_values(["parent_id", "intervention_id"]).drop_duplicates("parent_id").head(3).itertuples():
            index, parent_rows = pairs[row.mutant_id]
            parent = float(numeric.loc[parent_rows, column].mean()); mutant = float(numeric.loc[index, column])
            examples.append({"cell": cell, "mutant_id": row.mutant_id, "source_row_0based": index,
                "author_index": str(metadata.loc[index, "Unnamed: 0"]), "parent_rows_0based": parent_rows,
                "parent_sequence_sha256": hashlib_sequence(row.parent_sequence),
                "mutant_sequence_sha256": hashlib_sequence(row.mutant_sequence),
                "author_parent_mean": parent, "author_mutant": mutant, "canonical_delta": float(row.measured_delta)})
    return {"rows": len(frame), "unique_mutants": len(pairs), "source_metadata_rows": len(metadata),
        "numeric_author_rows_selected": len(needed), "numeric_columns": list(effect_columns.values()),
        "unique_semantic_parent_and_150nt_insert": "PASS", "effects": errors,
        "parent_barcode_construct_counts": dict(sorted(Counter(selected.parent_barcode_construct_count).items())),
        "nonfinite_author_parent_entries_counted_per_admitted_cell_candidate": nonfinite_parents,
        "fixed_examples": examples}, [MIKL, lineage_path]


def hashlib_sequence(sequence):
    import hashlib
    return hashlib.sha256(sequence.encode("ascii")).hexdigest()


def audit_moffatt(core):
    frame = core[core.dataset.eq("moffatt_gse334718")].copy()
    metadata = pd.read_csv(MOFF, usecols=["oligo"])
    assert metadata.oligo.is_unique
    rows = metadata.index[metadata.oligo.isin(frame.mutant_id)].tolist()
    assert set(metadata.loc[rows, "oligo"]) == set(frame.mutant_id)
    # The dictionary is outcome-free; only mutation insert records are retained.
    dictionary, calls = {}, defaultdict(lambda: [set() for _ in range(260)])
    simple = re.compile(r"^(\w+)_(\d+):(\d+)_([123])\+mut$")
    with FASTA.open(encoding="utf-8") as stream:
        while True:
            header = stream.readline()
            if not header:
                break
            sequence = stream.readline().strip().upper()
            assert header.startswith(">")
            identifier = header.strip()[1:]
            if identifier.endswith("+mut") and len(sequence) == 300 and re.fullmatch("[ACGT]+", sequence):
                assert identifier not in dictionary
                child = sequence[20:280]
                dictionary[identifier] = child
                match = simple.fullmatch(identifier)
                if match:
                    gene, start, end, copy = match.groups()
                    for position, base in enumerate(child):
                        if not int(start) - 1 <= position < int(end):
                            calls[gene.lower()][position].add(base)
    assert set(frame.mutant_id) <= set(dictionary)
    parents = {}
    for gene, bases in calls.items():
        assert all(len(values) == 1 for values in bases), "Missing/conflicting outcome-free consensus base"
        parents[gene] = "".join(next(iter(values)) for values in bases)
    for row in frame.itertuples():
        gene = row.mutant_id.split("_", 1)[0].lower()
        assert dictionary[row.mutant_id] == row.mutant_sequence and parents[gene] == row.parent_sequence
        changed = {i + 1 for i, (a, b) in enumerate(zip(row.parent_sequence, row.mutant_sequence)) if a != b}
        spans = [(int(a), int(b)) for a, b in re.findall(r"(\d+):(\d+)", row.mutant_id)]
        allowed = {position for start, end in spans for position in range(start, end + 1)}
        assert changed and len(changed) == row.substitution_count and changed <= allowed
    errors, examples = {}, []
    for reporter, column in [("GFP", "log2fc_gfp"), ("Firefly", "log2fc_ff")]:
        subset = frame[frame.reporter.eq(reporter)]
        reporter_rows = metadata.index[metadata.oligo.isin(subset.mutant_id)].tolist()
        numeric = selected_csv(MOFF, ["oligo", column], reporter_rows, len(metadata)).set_index("oligo")
        values = numeric.loc[subset.mutant_id, column].to_numpy(float)
        errors[reporter] = {"rows": len(subset), "maximum_absolute_error": compare_effect(subset.measured_delta, values)}
        for row in subset.sort_values(["parent_id", "intervention_id"]).drop_duplicates("parent_id").head(3).itertuples():
            examples.append({"reporter": reporter, "mutant_id": row.mutant_id,
                "original_csv_row_0based": int(metadata.index[metadata.oligo.eq(row.mutant_id)][0]),
                "author_effect": float(numeric.loc[row.mutant_id, column]), "canonical_delta": float(row.measured_delta),
                "parent_sequence_sha256": hashlib_sequence(row.parent_sequence), "mutant_sequence_sha256": hashlib_sequence(row.mutant_sequence)})
    return {"rows": len(frame), "numeric_author_rows_selected": len(rows),
        "numeric_columns": ["log2fc_gfp", "log2fc_ff"], "effects": errors,
        "mutation_dictionary_exact_inserts_and_outcome_free_parent_consensus": "PASS",
        "parents": len(parents), "fixed_examples": examples,
        "WT_normalization_author_pipeline_reconstructed": False,
        "limitation": "Author processed normalized coefficients copied correctly; mutation-library WT/control normalization and paired mutant-WT raw uncertainty not independently reproduced."}, [MOFF, FASTA]


def audit_astro(core):
    frame = core[core.dataset.eq("astrocyte_gse330741")].copy()
    ids = set(frame.mutant_id) | set(frame.parent_id)
    design_columns = ["element", "element_group", "gene", "CRE", "seq_length", "original_nt", "mutant_nt", "position_start"]
    design = scoped_sheet(ASTRO, "S6_mutagenesis_lib_seq_info", "element", ids, design_columns)
    numeric = scoped_sheet(ASTRO, "S8_lib2_results_summary", "element", ids, ["element", "snin_ctxin_logFC"])
    mutant_values, parent_values = [], []
    for row in frame.itertuples():
        mutant, parent = design.loc[row.mutant_id], design.loc[row.parent_id]
        assert str(mutant.CRE).upper().replace("U", "T") == row.mutant_sequence
        assert str(parent.CRE).upper().replace("U", "T") == row.parent_sequence
        assert int(float(parent.seq_length)) == 190 and str(parent.original_nt).lower() == "wt"
        assert mutant.element_group == row.parent_id
        changed = [i + 1 for i, (a, b) in enumerate(zip(row.parent_sequence, row.mutant_sequence)) if a != b]
        assert changed == [row.edit_start] and row.edit_start == row.edit_end
        assert int(float(mutant.position_start)) - int(float(parent.position_start)) + 1 == row.edit_start
        assert row.parent_sequence[row.edit_start - 1] == str(mutant.original_nt).upper()
        assert row.mutant_sequence[row.edit_start - 1] == str(mutant.mutant_nt).upper()
        mutant_values.append(float(numeric.loc[row.mutant_id, "snin_ctxin_logFC"]))
        parent_values.append(float(numeric.loc[row.parent_id, "snin_ctxin_logFC"]))
    errors = {"delta": compare_effect(frame.measured_delta, np.asarray(mutant_values) - parent_values),
              "mutant": compare_effect(frame.measured_mutant_localization, mutant_values),
              "parent": compare_effect(frame.measured_parent_localization, parent_values)}
    examples = []
    for row in frame.sort_values(["parent_id", "intervention_id"]).drop_duplicates("parent_id").itertuples():
        examples.append({"parent_id": row.parent_id, "mutant_id": row.mutant_id,
            "mutant_design_excel_row": int(design.loc[row.mutant_id, "excel_row"]),
            "mutant_result_excel_row": int(numeric.loc[row.mutant_id, "excel_row"]),
            "parent_result_excel_row": int(numeric.loc[row.parent_id, "excel_row"]),
            "author_mutant_coefficient": float(numeric.loc[row.mutant_id, "snin_ctxin_logFC"]),
            "author_WT_coefficient": float(numeric.loc[row.parent_id, "snin_ctxin_logFC"]),
            "canonical_delta": float(row.measured_delta)})
    return {"rows": len(frame), "numeric_author_rows_selected": len(ids), "numeric_columns": ["snin_ctxin_logFC"],
        "worksheet_allowlist": ["S6_mutagenesis_lib_seq_info", "S8_lib2_results_summary"],
        "exact_WT_design_join": "PASS", "maximum_absolute_errors": errors, "fixed_examples": examples,
        "limitation": "Published per-element REML coefficients verified against exact WT; original raw-count median normalization and REML coefficient production not independently rerun."}, [ASTRO]


def run():
    target = OUT / "original_author_lineage_audit.json"
    assert not target.exists(), "Preserve author-lineage audit"
    assert sha256(CORE) == "773d6145bbe4b17ff50597e47eba13f0b2977a3ddf541a1b238adcb7ff433e3d"
    columns = ["intervention_id", "dataset", "cell_type", "reporter", "parent_id", "mutant_id",
               "parent_sequence", "mutant_sequence", "edit_start", "edit_end", "substitution_count",
               "measured_parent_localization", "measured_mutant_localization", "measured_delta"]
    core = pd.read_csv(CORE, usecols=columns, float_precision="round_trip")
    manifest_path = ROOT / "results/v4_phaseA/source_manifest.json"
    manifest = readj(manifest_path)
    expected = {entry["path"]: entry["sha256"] for entry in manifest["sources"]}
    for path in (MIKL, MOFF, FASTA):
        assert sha256(path) == expected[path.relative_to(ROOT).as_posix()]
    assert sha256(ASTRO) == "1d17c0631fc962b762dddf3f27f76494dadf882f28a0154b5af76dbedd57c3f6"
    checks, inputs = {}, [CORE, manifest_path]
    for name, function in [("mikl", audit_mikl), ("moffatt", audit_moffatt), ("astrocyte", audit_astro)]:
        checks[name], paths = function(core)
        inputs.extend(paths)
        print(name, checks[name]["rows"], "original author admitted-row lineage PASS", flush=True)
    assert sum(check["rows"] for check in checks.values()) == 24514
    result = {"status": "PASS", "scope": "Original author localization columns for admitted mutants and exact WT rows only; metadata-selected deterministic examples",
        "rows": 24514, "checks": checks, "models_fit": 0, "protected_outcomes_opened": False,
        "author_pipeline_reproduction": False, "eligibility_or_models_changed": False,
        "source_hashes": {path.relative_to(ROOT).as_posix(): sha256(path) for path in sorted(set(inputs))},
        "code_sha256": sha256(Path(__file__)),
        "limitations": ["SRLE not reopened; its original count-to-author-table chain remains partial",
                        "Matching author coefficients does not certify their estimator, causal interpretation, clone identity or complete reporter processing",
                        "Mikl author barcode-averaged parent coefficients and raw pseudocounted replicate differences are different estimators",
                        "Moffatt known omitted-WT note is sufficiency-specific; not evidence of a mutation-library error",
                        "Astro exact author REML processing and Moffatt mutation WT normalization remain unresolved"]}
    jsave(target, result)
    lines = ["# Original author lineage audit", "", "The admitted Mikl, Moffatt mutation and Astrocyte coefficients agree with their original author files. Every tested parent and mutant sequence also passes independent author-metadata reconstruction. This is source fidelity, not complete reproduction of the authors' measurement pipelines.", "",
             "No frozen table, model, eligibility rule or gate was changed. No stability, protected confirmation, nonadmitted numeric outcome or other Astrocyte endpoint was selected. Mikl and Moffatt CSV numeric reads use admitted row IDs plus exact Mikl WT barcode rows; Astrocyte XML extraction restricts numerical cells to admitted elements and exact WTs.", ""]
    for name, check in checks.items():
        lines += ["## " + name, "", "```json", json.dumps(check, indent=2, sort_keys=True), "```", ""]
    lines += ["## Remaining confidence gaps", ""] + ["- " + item for item in result["limitations"]] + ["", "Exact file and code hashes are recorded in `results/generalization_rbp_20261007/original_author_lineage_audit.json`. Metadata examples use the lexical first intervention in each sorted parent (first three parents per Mikl cell/Moffatt reporter; all seven Astrocyte parents), fixed independently of effect values. No result-driven example selection was used.", ""]
    save(REP / "original_author_lineage_audit.md", "\n".join(lines).encode())


if __name__ == "__main__":
    run()
