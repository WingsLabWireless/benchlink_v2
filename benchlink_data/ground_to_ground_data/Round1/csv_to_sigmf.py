#!/usr/bin/env python3
"""
csv_to_sigmf.py

Place this script inside the DATASETS folder and run it:

    cd DATASETS/
    python3 csv_to_sigmf.py

It will:
  1. Scan all subfolders (e.g. 1rep_4qam/, 2rep_16qam/, 8rep_64qam/)
  2. Parse pilot repetitions and modulation from each folder name
  3. Convert every *_data.csv into a .sigmf-meta JSON file next to it
  4. Produce a combined benchlink_combined.sigmf-meta with all experiments
"""

import csv
import json
import os
import re
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKIP_COLUMNS = {"mission"}


def parse_folder_name(name):
    """Parse '1rep_4qam' or '8rep_64qam' into (pilot_reps, modulation)."""
    m = re.match(r'(\d+)\s*reps?[_\-](\d*\w*qam)', name, re.IGNORECASE)
    if m:
        return int(m.group(1)), m.group(2).upper()
    return None, None


def parse_timestamp(ts):
    try:
        return datetime.strptime(ts, "%Y%m%d_%H%M%S").strftime("%Y-%m-%dT%H:%M:%S")
    except ValueError:
        return ts


def to_val(s):
    s = s.strip()
    if s == "":
        return None
    try:
        f = float(s)
        return int(f) if f == int(f) else f
    except ValueError:
        return s


def usable_columns(rows, fields):
    out = []
    for col in fields:
        if col in SKIP_COLUMNS:
            continue
        vals = [r[col].strip() for r in rows]
        non_empty = [v for v in vals if v]
        if not non_empty:
            continue
        if all(v.lower() == "unknown" for v in non_empty):
            continue
        out.append(col)
    return out


def convert_csv(csv_path, pilot_reps, modulation):
    with open(csv_path, "r") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    if not rows:
        return None

    cols = usable_columns(rows, reader.fieldnames)
    first = rows[0]

    date = parse_timestamp(first["timestamp"]).split("T")[0] if "timestamp" in cols else "unknown"
    freq_hz = int(float(first["frequency"])) * 1_000_000 if "frequency" in cols else None

    g = {
        "core:version": "0.0.1",
        "core:description": "BenchLink PHY-layer experiment data",
        "core:author": "WINGS Lab",
        "core:experiment_date": date,
        "core:sample_count": len(rows),
    }
    if pilot_reps is not None:
        g["benchlink:pilot_repetitions"] = pilot_reps
    if modulation is not None:
        g["benchlink:modulation"] = modulation
    if freq_hz:
        g["core:frequency"] = freq_hz
    for k, c in [("benchlink:src_lat", "src_lat"), ("benchlink:src_lon", "src_lon"),
                  ("benchlink:dest_lat", "dest_lat"), ("benchlink:dest_lon", "dest_lon"),
                  ("benchlink:distance_m", "distance")]:
        if c in cols:
            g[k] = to_val(first[c])

    # Captures
    cfg_cols = [c for c in ["modulation", "frequency", "rx_gain", "tx_node", "rx_node"] if c in cols]
    captures = []
    cur = None
    for i, row in enumerate(rows):
        cfg = tuple(row[c].strip() for c in cfg_cols)
        if cfg != cur:
            cap = {"core:sample_start": i}
            if freq_hz:
                cap["core:frequency"] = int(float(row["frequency"])) * 1_000_000
            if "timestamp" in cols:
                cap["core:datetime"] = parse_timestamp(row["timestamp"])
            if "modulation" in cols:
                cap["benchlink:modulation"] = row["modulation"].strip()
            for field, key in [("tx_node", "benchlink:tx_node"), ("rx_node", "benchlink:rx_node"),
                               ("rx_gain", "benchlink:rx_gain_dB"), ("distance", "benchlink:distance_m")]:
                if field in cols:
                    cap[key] = to_val(row[field])
            if pilot_reps is not None:
                cap["benchlink:pilot_repetitions"] = pilot_reps
            captures.append(cap)
            cur = cfg

    # Annotations
    metric_cols = [c for c in cols if c in ("avg_sinr", "throughput", "avg_ser")]
    annotations = []
    for i, row in enumerate(rows):
        ann = {"core:sample_start": i, "core:sample_count": 1}
        if "timestamp" in cols:
            ann["core:datetime"] = parse_timestamp(row["timestamp"])
        for c in metric_cols:
            v = to_val(row[c])
            if v is not None:
                ann[f"benchlink:{c}"] = v
        annotations.append(ann)

    return {"global": g, "captures": captures, "annotations": annotations}


def main():
    all_experiments = []
    converted = 0
    skipped = 0

    print(f"Scanning: {SCRIPT_DIR}\n")

    for entry in sorted(os.listdir(SCRIPT_DIR)):
        subdir = os.path.join(SCRIPT_DIR, entry)
        if not os.path.isdir(subdir):
            continue

        pilot_reps, modulation = parse_folder_name(entry)
        if pilot_reps is None:
            continue

        csv_files = sorted([f for f in os.listdir(subdir) if f.lower().endswith("_data.csv")])
        if not csv_files:
            continue

        print(f"[{entry}] pilot_reps={pilot_reps}, modulation={modulation}")

        for csv_file in csv_files:
            csv_path = os.path.join(subdir, csv_file)
            try:
                sigmf = convert_csv(csv_path, pilot_reps, modulation)
            except Exception as e:
                print(f"  ERROR: {csv_file}: {e}")
                skipped += 1
                continue

            if sigmf is None:
                print(f"  SKIP:  {csv_file} (empty)")
                skipped += 1
                continue

            # Write individual .sigmf-meta
            out_name = os.path.splitext(csv_file)[0] + ".sigmf-meta"
            out_path = os.path.join(subdir, out_name)
            with open(out_path, "w") as f:
                json.dump(sigmf, f, indent=2)

            n = len(sigmf["annotations"])
            print(f"  OK:    {csv_file} -> {out_name} ({n} rows)")
            converted += 1

            # Collect for combined file
            all_experiments.append({
                "folder": entry,
                "file": csv_file,
                "pilot_repetitions": pilot_reps,
                "modulation": modulation,
                "sigmf": sigmf,
            })

    # Write combined file
    if all_experiments:
        combined = {
            "core:version": "0.0.1",
            "core:description": "BenchLink combined dataset (all configurations)",
            "core:author": "WINGS Lab",
            "core:experiment_count": len(all_experiments),
            "experiments": [],
        }
        for exp in all_experiments:
            combined["experiments"].append({
                "folder": exp["folder"],
                "file": exp["file"],
                "pilot_repetitions": exp["pilot_repetitions"],
                "modulation": exp["modulation"],
                "global": exp["sigmf"]["global"],
                "captures": exp["sigmf"]["captures"],
                "annotations_count": len(exp["sigmf"]["annotations"]),
                # Full annotations omitted to keep combined file manageable.
                # See individual .sigmf-meta files for per-row annotations.
            })

        combined_path = os.path.join(SCRIPT_DIR, "benchlink_combined.sigmf-meta")
        with open(combined_path, "w") as f:
            json.dump(combined, f, indent=2)
        print(f"\nCombined: benchlink_combined.sigmf-meta ({len(all_experiments)} experiments)")

    print(f"\nDone. Converted: {converted}, Skipped: {skipped}")


if __name__ == "__main__":
    main()