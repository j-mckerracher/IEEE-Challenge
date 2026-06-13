from __future__ import annotations

import argparse
import re
from collections import defaultdict
from pathlib import Path

import duckdb
import pyarrow.parquet as pq


SUFFIX_RE = re.compile(r"^\d{4}-\d{2}-\d{2}-\d{2}_(.+)\.parquet$")
NOSUFFIX_RE = re.compile(r"^\d{4}-\d{2}-\d{2}-\d{2}\.parquet$")
MONTH_RE = re.compile(r"^(\d{4}-\d{2})-\d{2}-\d{2}(?:_.+)?\.parquet$")


def quote_path(path: Path) -> str:
    return "'" + str(path).replace("\\", "\\\\").replace("'", "''") + "'"


def cluster_from_name(name: str) -> str:
    suffix = SUFFIX_RE.match(name)
    if suffix:
        return suffix.group(1)
    if NOSUFFIX_RE.match(name):
        return "NO_SUFFIX"
    return "UNKNOWN"


def month_from_name(name: str) -> str:
    month = MONTH_RE.match(name)
    return month.group(1) if month else "UNKNOWN"


def print_exitcode_sample(files: list[Path], sample_files_per_cluster: int) -> None:
    print("EXITCODE_SAMPLE")
    selected: list[Path] = []
    seen: dict[str, int] = {}
    for path in files:
        cluster = cluster_from_name(path.name)
        if seen.get(cluster, 0) < sample_files_per_cluster:
            selected.append(path)
            seen[cluster] = seen.get(cluster, 0) + 1

    con = duckdb.connect()
    file_sql = "[" + ",".join(quote_path(path) for path in selected) + "]"
    query = f"""
        SELECT
          regexp_extract(filename, '([0-9]{{4}}-[0-9]{{2}})', 1) AS month,
          CASE
            WHEN regexp_extract(filename, '_([^_/\\\\]+)\\.parquet$', 1) <> ''
              THEN regexp_extract(filename, '_([^_/\\\\]+)\\.parquet$', 1)
            WHEN regexp_extract(filename, '[0-9]{{4}}-[0-9]{{2}}-[0-9]{{2}}-[0-9]{{2}}\\.parquet$', 0) <> ''
              THEN 'NO_SUFFIX'
            ELSE 'UNKNOWN'
          END AS cluster,
          unit,
          CAST(exitcode AS VARCHAR) AS exitcode,
          COUNT(*) AS telemetry_rows,
          COUNT(DISTINCT jid) AS distinct_jids
        FROM read_parquet({file_sql}, filename=true, union_by_name=true)
        GROUP BY 1, 2, 3, 4
        ORDER BY cluster, month, telemetry_rows DESC
        LIMIT 120
    """
    print(con.execute(query).fetchdf().to_string(index=False))


def print_chunked_monthly_job_summary(files: list[Path]) -> None:
    print("\nMONTHLY_JOB_SUMMARY")
    groups: dict[tuple[str, str], list[Path]] = defaultdict(list)
    for path in files:
        groups[(month_from_name(path.name), cluster_from_name(path.name))].append(path)

    con = duckdb.connect()
    print(
        "month\tcluster\tfiles\tjobs\tcompleted_jobs\tfailed_timeout_jobs\t"
        "other_noncomplete_jobs\tunknown_label_jobs\tfailed_timeout_pct"
    )
    for (month, cluster), group_files in sorted(groups.items()):
        file_sql = "[" + ",".join(quote_path(path) for path in group_files) + "]"
        query = f"""
            WITH jobs AS (
              SELECT
                CAST(jid AS VARCHAR) AS jid,
                MAX(CASE WHEN upper(trim(CAST(exitcode AS VARCHAR))) = 'COMPLETED' THEN 1 ELSE 0 END) AS has_completed,
                MAX(CASE WHEN upper(trim(CAST(exitcode AS VARCHAR))) IN ('FAILED', 'TIMEOUT') THEN 1 ELSE 0 END) AS has_failed_timeout,
                MAX(CASE WHEN upper(trim(CAST(exitcode AS VARCHAR))) NOT IN ('COMPLETED', 'FAILED', 'TIMEOUT') THEN 1 ELSE 0 END) AS has_other_noncomplete,
                MAX(CASE WHEN exitcode IS NULL OR trim(CAST(exitcode AS VARCHAR)) = '' THEN 1 ELSE 0 END) AS has_unknown
              FROM read_parquet({file_sql}, union_by_name=true)
              GROUP BY 1
            )
            SELECT
              COUNT(*) AS jobs,
              SUM(CASE WHEN has_failed_timeout = 0 AND has_other_noncomplete = 0 AND has_completed = 1 THEN 1 ELSE 0 END) AS completed_jobs,
              SUM(CASE WHEN has_failed_timeout = 1 THEN 1 ELSE 0 END) AS failed_timeout_jobs,
              SUM(CASE WHEN has_failed_timeout = 0 AND has_other_noncomplete = 1 THEN 1 ELSE 0 END) AS other_noncomplete_jobs,
              SUM(CASE WHEN has_completed = 0 AND has_failed_timeout = 0 AND has_other_noncomplete = 0 AND has_unknown = 1 THEN 1 ELSE 0 END) AS unknown_label_jobs,
              ROUND(100.0 * SUM(CASE WHEN has_failed_timeout = 1 THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 3) AS failed_timeout_pct
            FROM jobs
        """
        row = con.execute(query).fetchone()
        print(
            f"{month}\t{cluster}\t{len(group_files)}\t{row[0]}\t{row[1]}\t"
            f"{row[2]}\t{row[3]}\t{row[4]}\t{row[5]}",
            flush=True,
        )


def print_monthly_job_summary(files: list[Path]) -> None:
    print("\nMONTHLY_JOB_SUMMARY")
    con = duckdb.connect()
    root_glob = str(files[0].parent / "*.parquet").replace("\\", "\\\\")
    query = f"""
        WITH rows AS (
          SELECT
            regexp_extract(filename, '([0-9]{{4}}-[0-9]{{2}})', 1) AS month,
            CASE
              WHEN regexp_extract(filename, '_([^_/\\\\]+)\\.parquet$', 1) <> ''
                THEN regexp_extract(filename, '_([^_/\\\\]+)\\.parquet$', 1)
              WHEN regexp_extract(filename, '[0-9]{{4}}-[0-9]{{2}}-[0-9]{{2}}-[0-9]{{2}}\\.parquet$', 0) <> ''
                THEN 'NO_SUFFIX'
              ELSE 'UNKNOWN'
            END AS cluster,
            CAST(jid AS VARCHAR) AS jid,
            CAST(exitcode AS VARCHAR) AS exitcode
          FROM read_parquet('{root_glob}', filename=true, union_by_name=true)
        ),
        jobs AS (
          SELECT
            month,
            cluster,
            jid,
            MAX(CASE
              WHEN exitcode IS NULL OR trim(exitcode) = '' THEN NULL
              WHEN upper(trim(exitcode)) IN ('COMPLETED', '0', '0:0', '0.0') THEN 0
              WHEN upper(trim(exitcode)) IN ('FAILED', 'TIMEOUT', 'CANCELLED', 'NODE_FAIL') THEN 1
              ELSE 1
            END) AS failed_or_nonzero
          FROM rows
          GROUP BY 1, 2, 3
        )
        SELECT
          month,
          cluster,
          COUNT(*) AS jobs,
          SUM(CASE WHEN failed_or_nonzero = 1 THEN 1 ELSE 0 END) AS failed_jobs,
          SUM(CASE WHEN failed_or_nonzero = 0 THEN 1 ELSE 0 END) AS success_jobs,
          SUM(CASE WHEN failed_or_nonzero IS NULL THEN 1 ELSE 0 END) AS unknown_label_jobs,
          ROUND(100.0 * SUM(CASE WHEN failed_or_nonzero = 1 THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 3) AS failure_pct
        FROM jobs
        GROUP BY 1, 2
        ORDER BY month, cluster
    """
    print(con.execute(query).fetchdf().to_string(index=False))


def main() -> None:
    parser = argparse.ArgumentParser(description="Profile FRESCO job labels by month.")
    parser.add_argument(
        "root",
        nargs="?",
        default=r"C:\Users\jmckerra\Code\IEEE-GSC-Challenge\fresco-data-6-9-26\unzipped-data",
    )
    parser.add_argument("--sample-files-per-cluster", type=int, default=8)
    parser.add_argument("--sample-only", action="store_true")
    parser.add_argument(
        "--all-at-once",
        action="store_true",
        help="Use one global DuckDB query. Usually slower and less observable.",
    )
    args = parser.parse_args()

    root = Path(args.root)
    files = sorted(root.glob("*.parquet"))
    if not files:
        raise SystemExit(f"No parquet files found in {root}")

    print(f"root: {root}")
    print(f"snapshot_files: {len(files)}")

    first = pq.ParquetFile(files[0])
    print(f"columns: {first.schema_arrow.names}")
    print_exitcode_sample(files, args.sample_files_per_cluster)

    if not args.sample_only:
        if args.all_at_once:
            print_monthly_job_summary(files)
        else:
            print_chunked_monthly_job_summary(files)


if __name__ == "__main__":
    main()
