from __future__ import annotations

import json
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APP = ROOT / "app"
sys.path.insert(0, str(APP))

from review_integrity import (
    packet_sha256,
    sha256_text,
    validate_packet,
)

PROMOTED_PATH = (
    ROOT
    / "data"
    / "knowledge"
    / "promoted_evidence"
    / "biology_ready_evidence.json"
)

SOURCE_PATH = (
    ROOT
    / "data"
    / "knowledge"
    / "evidence_records"
    / "biology_source_backed_evidence.json"
)

FACTUAL_APPROVAL_DIR = (
    ROOT
    / "data"
    / "knowledge"
    / "factual_approval"
)

OUTPUT_PACKET = (
    FACTUAL_APPROVAL_DIR
    / "biology_hash_bound_reviewer_packet.json"
)

OUTPUT_DECISIONS = (
    FACTUAL_APPROVAL_DIR
    / "biology_hash_bound_review_decisions.json"
)


def read_json(path: Path):
    return json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )


def write_json(path: Path, value):
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    path.write_text(
        json.dumps(
            value,
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def normalize_record_id(value) -> str:
    return unicodedata.normalize(
        "NFC",
        str(value or "").strip(),
    )


def collect_record_objects(value):
    found = []

    if isinstance(value, dict):
        if value.get("record_id"):
            found.append(value)

        for child in value.values():
            found.extend(
                collect_record_objects(
                    child
                )
            )

    elif isinstance(value, list):
        for child in value:
            found.extend(
                collect_record_objects(
                    child
                )
            )

    return found


def promoted_record_ids(document):
    records = collect_record_objects(
        document
    )

    ready = []

    for record in records:
        states = {
            str(
                record.get(key, "")
            ).upper()
            for key in (
                "status",
                "promotion_status",
                "evidence_status",
            )
        }

        if "READY" in states:
            ready.append(record)

    chosen = ready or records

    result = []
    seen = set()

    for record in chosen:
        raw_id = record["record_id"]
        normalized = normalize_record_id(
            raw_id
        )

        if normalized in seen:
            continue

        seen.add(normalized)
        result.append(raw_id)

    if not result:
        raise RuntimeError(
            "No promoted evidence records found."
        )

    return result


def candidate_documents(
    promoted_document,
):
    """
    Search only trusted project-derived evidence/review artifacts.

    Promoted evidence is checked first. The original source-backed
    evidence file and previous independent factual-review artifacts
    are fallback sources.

    Multiple copies are accepted only when their exact text/hash
    payload is identical. Any conflict fails closed.
    """

    documents = [
        (
            str(PROMOTED_PATH),
            promoted_document,
        )
    ]

    if SOURCE_PATH.exists():
        documents.append(
            (
                str(SOURCE_PATH),
                read_json(
                    SOURCE_PATH
                ),
            )
        )

    if FACTUAL_APPROVAL_DIR.exists():
        for path in sorted(
            FACTUAL_APPROVAL_DIR.glob(
                "*.json"
            )
        ):
            if path in {
                OUTPUT_PACKET,
                OUTPUT_DECISIONS,
            }:
                continue

            try:
                documents.append(
                    (
                        str(path),
                        read_json(path),
                    )
                )
            except (
                OSError,
                json.JSONDecodeError,
            ):
                continue

    return documents


def find_source_record(
    record_id,
    documents,
):
    target = normalize_record_id(
        record_id
    )

    matches = []

    for source_name, document in documents:
        for record in collect_record_objects(
            document
        ):
            if (
                normalize_record_id(
                    record.get(
                        "record_id"
                    )
                )
                != target
            ):
                continue

            if (
                "evidence_text"
                not in record
                or "text_sha256"
                not in record
            ):
                continue

            evidence_text = record[
                "evidence_text"
            ]
            declared_hash = record[
                "text_sha256"
            ]
            actual_hash = sha256_text(
                evidence_text
            )

            if declared_hash != actual_hash:
                raise RuntimeError(
                    "Evidence SHA-256 mismatch in "
                    f"{source_name}: {record_id}"
                )

            matches.append(
                (
                    source_name,
                    record,
                    actual_hash,
                )
            )

    if not matches:
        raise RuntimeError(
            "Missing exact source-backed evidence in trusted "
            f"artifacts: {record_id}"
        )

    payloads = {
        (
            match[1]["evidence_text"],
            match[2],
        )
        for match in matches
    }

    if len(payloads) != 1:
        sources = ", ".join(
            source_name
            for (
                source_name,
                _record,
                _hash,
            ) in matches
        )

        raise RuntimeError(
            "Conflicting evidence payloads for "
            f"{record_id}. Sources: {sources}"
        )

    return matches[0][1]


def build_packet(
    promoted_document,
    documents,
):
    ids = promoted_record_ids(
        promoted_document
    )

    records = []

    for record_id in ids:
        source = find_source_record(
            record_id,
            documents,
        )

        evidence_text = source[
            "evidence_text"
        ]
        exact_hash = sha256_text(
            evidence_text
        )

        records.append(
            {
                "record_id": record_id,
                "outcome_id": source.get(
                    "outcome_id"
                ),
                "grade": source.get(
                    "grade"
                ),
                "theme_name": source.get(
                    "theme_name"
                ),
                "outcome_title": source.get(
                    "outcome_title"
                ),
                "source_package": source.get(
                    "source_package"
                ),
                "source_page": source.get(
                    "source_page"
                ),
                "source_anchor": source.get(
                    "source_anchor"
                ),
                "text_sha256": exact_hash,
                "reviewed_text_sha256": exact_hash,
                "evidence_text": evidence_text,
                "required_decision_fields": {
                    "record_id": "immutable",
                    "reviewed_text_sha256": "immutable",
                    "review_packet_sha256": "immutable",
                    "status": (
                        "APPROVED_FOR_EVIDENCE_READY | "
                        "MANUAL_REVIEW_REQUIRED | REJECTED"
                    ),
                    "reviewer_type": (
                        "HUMAN | EXTERNAL_LLM"
                    ),
                    "reviewer_id": "required",
                    "factual_support": "boolean",
                    "outcome_support": "boolean",
                    "source_consistency": "boolean",
                    "rationale": "required",
                },
                "student_ready": False,
                "student_visible": False,
            }
        )

    packet = {
        "schema_version": "2.0-hash-bound",
        "purpose": (
            "Hash-bound factual re-review of currently "
            "promoted Biology evidence."
        ),
        "integrity_policy": (
            "EXACT_TEXT_AND_PACKET_HASH_BINDING"
        ),
        "authenticated_signature": False,
        "record_count": len(
            records
        ),
        "records": records,
    }

    packet[
        "packet_sha256"
    ] = packet_sha256(
        packet
    )

    validate_packet(
        packet
    )

    return packet


def build_decisions_template(packet):
    packet_hash = packet[
        "packet_sha256"
    ]

    return {
        "schema_version": "2.0-hash-bound",
        "review_packet_sha256": packet_hash,
        "decisions": [
            {
                "record_id": record[
                    "record_id"
                ],
                "reviewed_text_sha256": record[
                    "reviewed_text_sha256"
                ],
                "review_packet_sha256": packet_hash,
                "status": "",
                "reviewer_type": "",
                "reviewer_id": "",
                "factual_support": None,
                "outcome_support": None,
                "source_consistency": None,
                "rationale": "",
            }
            for record in packet[
                "records"
            ]
        ],
    }


def main():
    promoted = read_json(
        PROMOTED_PATH
    )

    documents = candidate_documents(
        promoted
    )

    packet = build_packet(
        promoted,
        documents,
    )

    decisions = build_decisions_template(
        packet
    )

    write_json(
        OUTPUT_PACKET,
        packet,
    )
    write_json(
        OUTPUT_DECISIONS,
        decisions,
    )

    print(
        "KNOWLEDGE FACTORY V2 — PHASE 6M "
        "REVIEW INTEGRITY HARDENING"
    )
    print(
        f"Hash-bound records : {packet['record_count']}"
    )
    print(
        f"Packet SHA-256      : {packet['packet_sha256']}"
    )
    print(
        "Source resolution   : CONSISTENCY-ENFORCED"
    )
    print(
        "Authenticated sig.  : False"
    )
    print(
        "Student ready       : False"
    )
    print(
        "Student visible     : False"
    )
    print(
        f"PACKET | {OUTPUT_PACKET}"
    )
    print(
        f"DECISIONS TEMPLATE | {OUTPUT_DECISIONS}"
    )


if __name__ == "__main__":
    main()
