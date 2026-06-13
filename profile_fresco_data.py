from __future__ import annotations

import argparse
import re
import time
from collections import defaultdict
from pathlib import Path

import pyarrow.parquet as pq


FILENAME_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})-(\d{2})_(.+)\.parquet$")


def empty_bucket() -> dict:
    return {
        "files": 0,
        "rows": 0,
        "bytes": 0,
        "bad": 0,
        "clusters": defaultdict(lambda: {"files": 0, "rows": 0, "bytes": 0}),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Profile extracted FRESCO Parquet density.")
    parser.add_argument(
        "root",
        nargs="?",
        default=r"C:\Users\jmckerra\Code\IEEE-GSC-Challenge\fresco-data-6-9-26\unzipped-data",
        help="Directory containing extracted hourly Parquet files.",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Scan recursively instead of assuming a flat extracted directory.",
    )
    args = parser.parse_args()

    root = Path(args.root)
    files = sorted(root.rglob("*.parquet") if args.recursive else root.glob("*.parquet"))

    by_month = defaultdict(empty_bucket)
    by_cluster = defaultdict(lambda: {"files": 0, "rows": 0, "bytes": 0, "months": set()})
    columns = None
    errors = []
    started = time.time()

    for path in files:
        match = FILENAME_RE.match(path.name)
        month = f"{match.group(1)}-{match.group(2)}" if match else "UNKNOWN"
        cluster = match.group(5) if match else "UNKNOWN"

        try:
            parquet_file = pq.ParquetFile(path)
            rows = parquet_file.metadata.num_rows
            if columns is None:
                columns = parquet_file.schema_arrow.names
        except Exception as exc:  # Keep going while extraction may still be active.
            rows = 0
            errors.append((path.name, type(exc).__name__, str(exc)[:160]))
            by_month[month]["bad"] += 1

        size = path.stat().st_size
        by_month[month]["files"] += 1
        by_month[month]["rows"] += rows
        by_month[month]["bytes"] += size
        by_month[month]["clusters"][cluster]["files"] += 1
        by_month[month]["clusters"][cluster]["rows"] += rows
        by_month[month]["clusters"][cluster]["bytes"] += size

        by_cluster[cluster]["files"] += 1
        by_cluster[cluster]["rows"] += rows
        by_cluster[cluster]["bytes"] += size
        by_cluster[cluster]["months"].add(month)

    print(f"root: {root}")
    print(f"snapshot_files: {len(files)}")
    print(f"elapsed_sec: {time.time() - started:.2f}")
    print(f"columns: {columns}")
    print(f"errors: {len(errors)}")
    for error in errors[:10]:
        print(f"  error: {error}")

    print("\nMONTH_SUMMARY")
    for month in sorted(by_month):
        data = by_month[month]
        cluster_parts = []
        for cluster, cluster_data in sorted(data["clusters"].items()):
            cluster_parts.append(
                f"{cluster}:{cluster_data['files']}f/{cluster_data['rows']}r/"
                f"{cluster_data['bytes'] / 1_000_000:.1f}mb"
            )
        print(
            f"{month}\tfiles={data['files']}\trows={data['rows']}\t"
            f"mb={data['bytes'] / 1_000_000:.1f}\tbad={data['bad']}\t"
            f"clusters={'; '.join(cluster_parts)}"
        )

    print("\nCLUSTER_SUMMARY")
    for cluster, data in sorted(by_cluster.items()):
        months = sorted(data["months"])
        first = months[0] if months else ""
        last = months[-1] if months else ""
        print(
            f"{cluster}\tfiles={data['files']}\trows={data['rows']}\t"
            f"mb={data['bytes'] / 1_000_000:.1f}\tfirst={first}\tlast={last}\t"
            f"n_months={len(months)}"
        )


if __name__ == "__main__":
    main()
