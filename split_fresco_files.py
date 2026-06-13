from __future__ import annotations

import argparse
import re
from collections import Counter
from pathlib import Path


ROOT = Path(r"C:\Users\jmckerra\Code\IEEE-GSC-Challenge")
SOURCE = ROOT / "fresco-data-6-9-26" / "unzipped-data"

SUFFIX_RE = re.compile(r"^(\d{4}-\d{2})-\d{2}-\d{2}_(C|S)\.parquet$")
NO_SUFFIX_RE = re.compile(r"^(\d{4}-\d{2})-\d{2}-\d{2}\.parquet$")


def month_between(month: str, start: str, end: str) -> bool:
    return start <= month <= end


def destination_for(path: Path) -> str:
    suffix_match = SUFFIX_RE.match(path.name)
    if suffix_match:
        month, cluster = suffix_match.groups()

        if cluster == "S":
            if month_between(month, "2013-02", "2016-12"):
                return "participant"
            if month_between(month, "2017-01", "2017-03"):
                return "validation"
            if month_between(month, "2017-04", "2017-08"):
                return "judge"
            return "quarantine"

        if cluster == "C":
            if month in {"2015-04", "2015-07", "2016-05"}:
                return "quarantine"
            if month_between(month, "2015-05", "2016-12"):
                return "participant"
            if month_between(month, "2017-01", "2017-03"):
                return "validation"
            if month_between(month, "2017-04", "2017-06"):
                return "judge"
            return "quarantine"

    no_suffix_match = NO_SUFFIX_RE.match(path.name)
    if no_suffix_match:
        month = no_suffix_match.group(1)
        if month_between(month, "2022-07", "2023-02"):
            return "participant"
        if month == "2023-03":
            return "validation"
        if month_between(month, "2023-04", "2023-05"):
            return "judge"
        return "quarantine"

    return "quarantine"


def main() -> None:
    parser = argparse.ArgumentParser(description="Move FRESCO Parquet files into challenge splits.")
    parser.add_argument("--apply", action="store_true", help="Actually move files. Without this, only prints counts.")
    parser.add_argument("--source", type=Path, default=SOURCE)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()

    files = sorted(args.source.glob("*.parquet"))
    counts = Counter(destination_for(path) for path in files)

    print(f"source: {args.source}")
    print(f"files_seen: {len(files)}")
    for split in ["participant", "validation", "judge", "quarantine"]:
        print(f"{split}: {counts[split]}")

    if not args.apply:
        print("dry_run: true")
        return

    for split in ["participant", "validation", "judge"]:
        (args.root / split).mkdir(exist_ok=True)

    moved = Counter()
    for path in files:
        split = destination_for(path)
        if split == "quarantine":
            continue

        target = args.root / split / path.name
        if target.exists():
            raise FileExistsError(f"Refusing to overwrite existing file: {target}")

        path.rename(target)
        moved[split] += 1

    print("moved:")
    for split in ["participant", "validation", "judge"]:
        print(f"{split}: {moved[split]}")
    print(f"left_in_source: {sum(1 for _ in args.source.glob('*.parquet'))}")


if __name__ == "__main__":
    main()
