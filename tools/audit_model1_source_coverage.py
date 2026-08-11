"""Audit MODEL-1 source-grounded curriculum coverage."""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

APP = Path(__file__).resolve().parent.parent / "app"
if str(APP) not in sys.path:
    sys.path.insert(0, str(APP))

from model1_official_source_context import (  # noqa: E402
    LOCAL_PAGE_INDEX,
    DIN_CACHE,
    load_curriculum_records,
    source_coverage,
)


def main():
    records = load_curriculum_records()

    if not LOCAL_PAGE_INDEX.exists():
        print("MODEL-1 OFFICIAL SOURCE COVERAGE")
        print("STATUS : BLOCKED")
        print(f"Missing local page index: {LOCAL_PAGE_INDEX}")
        print("Run: py tools\\build_local_page_bundle_index.py")
        raise SystemExit(2)

    results = source_coverage(allow_network=True)
    counts = Counter(item["status"] for item in results)

    print("=" * 72)
    print("MODEL-1 OFFICIAL SOURCE COVERAGE")
    print("=" * 72)
    print(f"TOTAL CURRICULUM : {len(records)}")
    print(f"SOURCE READY     : {counts['SOURCE_READY']}")
    print(f"MISSING SOURCE   : {counts['MISSING_SOURCE']}")
    print(f"DIN LOCAL CACHE  : {DIN_CACHE}")

    missing = [item for item in results if item["status"] != "SOURCE_READY"]
    if missing:
        print("\nMISSING:")
        for item in missing:
            print(
                f"{item['exam']} | {item['subject']} | {item['topic']}"
            )
        print("\nMODEL-1 BULK SOURCE GATE: FAIL-CLOSED")
        raise SystemExit(2)

    print("\nMODEL-1 BULK SOURCE GATE: PASS")
    print("All curriculum topics have an official-source teaching path.")


if __name__ == "__main__":
    main()
