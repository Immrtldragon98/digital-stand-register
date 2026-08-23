"""Validated 22/08/2026 Finishing Mill General Shift snapshot.

Rules applied:
- A running stand exists only in W1/W2/W3.
- Running wins over every spare/preparation list.
- For duplicate spare entries, READY wins over PENDING.
- INP is preserved as a legacy/report status until plant meaning is finalized.

The report contains 50 unique stand codes. The plant total supplied by the user is
54, therefore 4 asset codes are still unidentified and are intentionally NOT
invented here.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

SNAPSHOT_AT = datetime(2026, 8, 22, 0, 0, 0)
EXPECTED_TOTAL_ASSETS = 54

RUNNING_LINES: dict[str, list[str]] = {
    "W1": ["1B", "2.1", "3C", "4B", "5B", "6D", "7C", "8.1", "9", "10.1"],
    "W2": ["1A", "2D", "3E", "4A", "5E", "6B", "7E", "8E", "9C", "10C"],
    "W3": ["1C", "2B", "3D", "4C", "5D", "6A", "7A", "8B", "9D", "10E"],
}

RAW_PENDING = [
    "1D", "2A", "3A", "4D", "5D", "6.1", "6C", "7.1", "8A", "8C",
    "9A", "10A", "10B", "10C",
]
RAW_READY = ["1.1", "2E", "3B", "4.1", "5A", "8A", "9A", "10A", "10D"]
RAW_INP = ["9B", "7B"]


def running_codes() -> set[str]:
    return {code for stands in RUNNING_LINES.values() for code in stands}


def normalized_spares() -> dict[str, str]:
    """Return code -> status after applying plant priority rules."""
    running = running_codes()
    result: dict[str, str] = {}

    for code in RAW_PENDING:
        if code not in running:
            result[code] = "PENDING"

    # READY overrides a duplicate PENDING row.
    for code in RAW_READY:
        if code not in running:
            result[code] = "READY"

    # INP is preserved only if the stand is not running and has no READY priority.
    for code in RAW_INP:
        if code not in running and result.get(code) != "READY":
            result[code] = "INP"

    return result


def all_known_codes() -> set[str]:
    return running_codes() | set(normalized_spares())


@dataclass(frozen=True)
class SnapshotValidation:
    running_count: int
    spare_count: int
    known_total: int
    expected_total: int
    unidentified_count: int
    duplicate_running_codes: tuple[str, ...]
    running_spare_overlap: tuple[str, ...]


def validate_snapshot() -> SnapshotValidation:
    flat_running = [code for stands in RUNNING_LINES.values() for code in stands]
    duplicates = sorted({code for code in flat_running if flat_running.count(code) > 1})
    spare_codes = set(normalized_spares())
    overlap = sorted(running_codes() & spare_codes)
    known = len(all_known_codes())
    return SnapshotValidation(
        running_count=len(flat_running),
        spare_count=len(spare_codes),
        known_total=known,
        expected_total=EXPECTED_TOTAL_ASSETS,
        unidentified_count=max(0, EXPECTED_TOTAL_ASSETS - known),
        duplicate_running_codes=tuple(duplicates),
        running_spare_overlap=tuple(overlap),
    )
