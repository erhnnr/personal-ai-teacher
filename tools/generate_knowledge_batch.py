"""
Batch Knowledge Draft Generator

Purpose:
Generate structured knowledge DRAFTS from the current
TYT/AYT curriculum using the local LM Studio model.

Pipeline:
Curriculum
-> EVIDENCE_READY gate
-> Claim-level provenance annotated LLM Draft
-> Claim reference validation
-> Claim-anchor + explicit evidence scope guard
-> Canonical knowledge draft
-> Structural Validation
-> Deterministic Math Factual Review
-> DRAFT status report

IMPORTANT:
Generated content is NOT verified knowledge.

Knowledge Factory V2 rule:
New generation requires a valid EVIDENCE_READY package.
The LLM may transform supplied evidence into pedagogical
structure, but it must not invent unsupported factual claims.

Outputs are written to:

data/knowledge/drafts/

They must never be treated as READY merely because
they pass structural or factual checks.
"""

import argparse
import json
import re
import shutil
import sys
import unicodedata
from datetime import datetime
from pathlib import Path

from jsonschema import Draft202012Validator


PROJECT_ROOT = Path(__file__).resolve().parent.parent
APP_PATH = PROJECT_ROOT / "app"
TOOLS_PATH = PROJECT_ROOT / "tools"

if str(APP_PATH) not in sys.path:
    sys.path.insert(0, str(APP_PATH))

if str(TOOLS_PATH) not in sys.path:
    sys.path.insert(0, str(TOOLS_PATH))


from config import MODEL_NAME
from curriculum_engine import load_curriculum_data
from llm import client, check_llm_connection
from validate_knowledge import validate_topic
from review_math_draft import review_draft
from evidence_factory import validate_evidence_package


RETRYABLE_GENERATION_ERRORS = (
    json.JSONDecodeError,
    ValueError,
    RuntimeError,
)


DRAFT_ROOT = (
    PROJECT_ROOT
    / "data"
    / "knowledge"
    / "drafts"
)

UNIT_ROOT = (
    PROJECT_ROOT
    / "data"
    / "knowledge"
    / "units"
)


EVIDENCE_ROOT = (
    PROJECT_ROOT
    / "data"
    / "knowledge"
    / "evidence"
)


GROUNDING_SCHEMA_PATH = (
    PROJECT_ROOT
    / "data"
    / "knowledge"
    / "schemas"
    / "grounded_generation.schema.json"
)


def slugify(value):
    """
    Convert Turkish display text into a stable
    ASCII directory name.
    """

    value = str(value).strip()

    replacements = {
        "İ": "I",
        "Ç": "C",
        "Ğ": "G",
        "Ö": "O",
        "Ş": "S",
        "Ü": "U",
        "ı": "i",
        "ç": "c",
        "ğ": "g",
        "ö": "o",
        "ş": "s",
        "ü": "u",
    }

    for old, new in replacements.items():
        value = value.replace(
            old,
            new,
        )

    value = value.lower()

    value = re.sub(
        r"[^a-z0-9]+",
        "_",
        value,
    )

    return value.strip("_")


def normalize(value):
    return str(value).strip().casefold()


def load_json(path):
    return json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )


def write_json(path, data):
    path.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def find_existing_unit(
    subject,
    topic,
):
    """
    Check whether a real knowledge unit already exists.

    Existing verified units are never overwritten.
    """

    if not UNIT_ROOT.exists():
        return None

    for concept_file in UNIT_ROOT.rglob(
        "concept.json"
    ):

        try:
            data = load_json(
                concept_file
            )

        except Exception:
            continue

        if (
            normalize(
                data.get("subject")
            )
            == normalize(subject)
            and
            normalize(
                data.get("topic")
            )
            == normalize(topic)
        ):
            return concept_file.parent

    return None


def get_draft_path(
    subject,
    grade,
    topic,
):
    return (
        DRAFT_ROOT
        / slugify(subject)
        / f"grade{grade}"
        / slugify(topic)
    )


def prepare_draft_for_overwrite(
    draft_path,
    overwrite,
):
    """
    Remove an obsolete generated draft before
    an explicit overwrite attempt.

    Drafts are unverified temporary artifacts.
    If regeneration later fails, no stale draft
    should remain and appear current.
    """

    draft_path = Path(
        draft_path
    )

    if (
        overwrite
        and draft_path.exists()
    ):
        shutil.rmtree(
            draft_path
        )

        return True

    return False



def get_evidence_path(
    subject,
    grade,
    topic,
):
    """
    Return the canonical Knowledge Factory V2
    evidence.json path for one curriculum topic.
    """

    return (
        EVIDENCE_ROOT
        / slugify(subject)
        / f"grade{grade}"
        / slugify(topic)
        / "evidence.json"
    )


def load_ready_evidence(
    record,
    grade,
):
    """
    Load and validate the source-grounding package.

    Generation is forbidden when:
    - evidence.json is missing,
    - the package is structurally invalid,
    - source references are not registered,
    - identity does not match the curriculum record,
    - status is not EVIDENCE_READY.

    This is the Knowledge Factory V2 hard gate.
    """

    evidence_path = get_evidence_path(
        record["subject"],
        grade,
        record["topic"],
    )

    if not evidence_path.exists():
        raise ValueError(
            "EVIDENCE_READY required but evidence file "
            f"is missing: {evidence_path}"
        )

    evidence = load_json(
        evidence_path
    )

    validate_evidence_package(
        evidence
    )

    expected_exam = normalize(
        record.get("exam")
    )

    expected_subject = normalize(
        record.get("subject")
    )

    expected_topic = normalize(
        record.get("topic")
    )

    expected_grade = normalize(
        grade
    )

    if normalize(
        evidence.get("exam")
    ) != expected_exam:
        raise ValueError(
            "Evidence exam does not match curriculum record."
        )

    if normalize(
        evidence.get("subject")
    ) != expected_subject:
        raise ValueError(
            "Evidence subject does not match curriculum record."
        )

    if normalize(
        evidence.get("topic")
    ) != expected_topic:
        raise ValueError(
            "Evidence topic does not match curriculum record."
        )

    if normalize(
        evidence.get("grade")
    ) != expected_grade:
        raise ValueError(
            "Evidence grade does not match requested grade."
        )

    if evidence.get(
        "status"
    ) != "EVIDENCE_READY":
        raise ValueError(
            "Evidence package is not EVIDENCE_READY."
        )

    return evidence


def build_grounding_context(
    evidence,
):
    """
    Convert a validated evidence package into the only
    factual context available to the generation prompt.
    """

    return json.dumps(
        {
            "evidence_id": evidence["id"],
            "sources": evidence["sources"],
            "claims": evidence["claims"],
            "coverage": evidence["coverage"],
        },
        ensure_ascii=False,
        indent=2,
    )


GENERIC_GROUNDING_ROOTS = {
    "acikla",
    "anla",
    "uygula",
    "ogren",
    "ogrenci",
    "ogret",
    "konu",
    "kavram",
    "kural",
    "temel",
    "ornek",
    "soru",
    "cevap",
    "coz",
    "cozum",
    "dogru",
    "yanlis",
    "hata",
    "dikkat",
    "goster",
    "kullan",
    "bul",
    "hesapla",
    "ifade",
    "islem",
    "yontem",
    "adim",
    "bilgi",
    "amac",
    "hedef",
    "iliski",
    "ilgili",
    "gereken",
    "gerek",
    "durum",
    "sekil",
    "bicim",
    "deger",
    "sonuc",
    "fark",
    "toplam",
    "sabit",
    "fonksiyon",
    "matematik",
    "yks",
    "sinif",
    "gercek",
    "hayat",
    "olarak",
    "ol",
    "kabul",
    "edil",
    "et",
    "yaz",
    "yazil",
    "burada",
    "say",
    "sayi",
    "denir",
    "adlandir",
    "ele",
    "alin",
    "veril",
    "gerektir",
    "aciklan",
    "kapsa",
    "biçim",
}


TURKISH_SUFFIXES = (
    "larindan",
    "lerinden",
    "larinin",
    "lerinin",
    "larina",
    "lerine",
    "larini",
    "lerini",
    "larin",
    "lerin",
    "lar",
    "ler",
    "inin",
    "ının",
    "unun",
    "ünün",
    "nın",
    "nin",
    "nun",
    "nün",
    "dan",
    "den",
    "tan",
    "ten",
    "dır",
    "dir",
    "dur",
    "dür",
    "tır",
    "tir",
    "tur",
    "tür",
    "lık",
    "lik",
    "luk",
    "lük",
    "lı",
    "li",
    "lu",
    "lü",
    "ını",
    "ini",
    "unu",
    "ünü",
    "yla",
    "yle",
    "ya",
    "ye",
    "da",
    "de",
    "ta",
    "te",
    "dan",
    "den",
    "ın",
    "in",
    "un",
    "ün",
    "ı",
    "i",
    "u",
    "ü",
    "ma",
    "me",
    "mak",
    "mek",    "sina",
    "sine",
    "suna",
    "sune",
    "inda",
    "inde",
    "unda",
    "unde",
    "indan",
    "inden",
    "undan",
    "unden",
    "idir",
    "udur",
    "ilir",
    "ulur",
    "lanir",
    "lenir",

)


def validate_grounded_generation_schema(
    package,
):
    """
    Validate the annotated model output before canonicalization.

    The canonical knowledge-unit schema intentionally remains
    unchanged. Provenance is a generation-time contract.
    """

    schema = load_json(
        GROUNDING_SCHEMA_PATH
    )

    validator = Draft202012Validator(
        schema
    )

    errors = sorted(
        validator.iter_errors(
            package
        ),
        key=lambda error: list(
            error.path
        ),
    )

    if errors:
        first = errors[0]

        location = ".".join(
            str(item)
            for item in first.path
        )

        if location:
            location = f" at '{location}'"

        raise ValueError(
            "Grounded generation schema failed"
            f"{location}: {first.message}"
        )

    return True


def claim_lookup(
    evidence,
):
    return {
        claim["id"]: claim
        for claim in evidence.get(
            "claims",
            []
        )
    }


def iter_grounded_items(
    package,
):
    """
    Yield:
        path
        textual payload
        evidence_refs
        vocabulary_guard_enabled
    """

    concept = package["concept"]

    factual_concept_fields = {
        "learning_objectives",
        "prerequisites",
        "core_concepts",
        "rules",
    }

    for field in (
        "learning_objectives",
        "prerequisites",
        "core_concepts",
        "rules",
        "common_confusions",
        "teaching_notes",
    ):
        for index, item in enumerate(
            concept.get(field, [])
        ):
            yield (
                f"concept.{field}[{index}]",
                item["text"],
                item["evidence_refs"],
                field in factual_concept_fields,
            )

    for index, item in enumerate(
        concept.get(
            "definitions",
            []
        )
    ):
        yield (
            f"concept.definitions[{index}]",
            (
                f"{item['term']} "
                f"{item['definition']}"
            ),
            item["evidence_refs"],
            True,
        )

    for index, item in enumerate(
        package["examples"].get(
            "examples",
            []
        )
    ):
        yield (
            f"examples.examples[{index}]",
            " ".join(
                [
                    item.get(
                        "question",
                        "",
                    ),
                    item.get(
                        "answer",
                        "",
                    ),
                    item.get(
                        "learning_point",
                        "",
                    ),
                ]
            ),
            item["evidence_refs"],
            False,
        )

    for index, item in enumerate(
        package["mistakes"].get(
            "mistakes",
            []
        )
    ):
        yield (
            f"mistakes.mistakes[{index}]",
            " ".join(
                [
                    item.get(
                        "error",
                        "",
                    ),
                    item.get(
                        "explanation",
                        "",
                    ),
                    item.get(
                        "teacher_action",
                        "",
                    ),
                ]
            ),
            item["evidence_refs"],
            False,
        )

    relations = package["relations"]

    for field in (
        "prerequisites",
        "next_topics",
        "related_topics",
    ):
        for index, item in enumerate(
            relations.get(field, [])
        ):
            text_parts = [
                item.get(
                    "topic",
                    "",
                )
            ]

            if field == "related_topics":
                text_parts.append(
                    item.get(
                        "relation",
                        "",
                    )
                )
            else:
                text_parts.append(
                    item.get(
                        "reason",
                        "",
                    )
                )

            yield (
                f"relations.{field}[{index}]",
                " ".join(
                    text_parts
                ),
                item["evidence_refs"],
                True,
            )


def validate_claim_level_provenance(
    package,
    evidence,
):
    """
    Every generated factual item must cite at least one
    claim ID that actually exists in the EVIDENCE_READY package.

    A fabricated/missing claim ID is a hard generation failure.
    """

    claims = claim_lookup(
        evidence
    )

    if not claims:
        raise ValueError(
            "Evidence package has no claims."
        )

    for (
        path,
        _text,
        refs,
        _guard,
    ) in iter_grounded_items(
        package
    ):
        if not refs:
            raise ValueError(
                f"Missing evidence_refs at {path}."
            )

        unknown = sorted(
            {
                ref
                for ref in refs
                if ref not in claims
            }
        )

        if unknown:
            raise ValueError(
                f"Unknown evidence claim at {path}: "
                + ", ".join(
                    unknown
                )
            )

    return True


def normalize_grounding_text(
    value,
):
    """
    Normalize Turkish text for deterministic vocabulary checks.

    Important:
    Unicode casefold can turn capital Turkish İ into
    "i" + COMBINING DOT ABOVE. If that combining mark is left
    in place, tokenization can split "İntegral" into "i" and
    "ntegral". Normalize and remove combining marks first.
    """

    value = str(
        value
    )

    replacements = {
        "İ": "I",
        "I": "I",
        "ı": "i",
        "Ç": "C",
        "ç": "c",
        "Ğ": "G",
        "ğ": "g",
        "Ö": "O",
        "ö": "o",
        "Ş": "S",
        "ş": "s",
        "Ü": "U",
        "ü": "u",
    }

    for old, new in replacements.items():
        value = value.replace(
            old,
            new,
        )

    value = unicodedata.normalize(
        "NFKD",
        value,
    )

    value = "".join(
        char
        for char in value
        if not unicodedata.combining(
            char
        )
    )

    return value.casefold()


def grounding_tokens(
    value,
):
    return re.findall(
        r"[a-z0-9]+",
        normalize_grounding_text(
            value
        ),
    )


def grounding_root(
    token,
):
    token = str(
        token
    ).strip()

    if len(token) < 5:
        return token

    for suffix in sorted(
        TURKISH_SUFFIXES,
        key=len,
        reverse=True,
    ):
        if (
            token.endswith(
                suffix
            )
            and len(token) - len(
                suffix
            ) >= 4
        ):
            return token[
                :-len(suffix)
            ]

    return token



def is_generic_grounding_token(
    token,
    root,
):
    """
    Match ordinary Turkish teaching-language forms without
    weakening the factual vocabulary guard.

    The previous exact-root check produced false positives for
    conjugated verbs such as "açıklar" -> "acik" while the
    generic lexicon contains "acikla".

    Prefix matching is allowed only when both sides have at least
    four characters, so short accidental matches are avoided.
    """

    token = str(
        token
    ).strip()

    root = str(
        root
    ).strip()

    for generic in (
        GENERIC_GROUNDING_ROOTS
    ):
        if (
            token == generic
            or root == generic
        ):
            return True

        if (
            len(token) >= 4
            and len(generic) >= 4
            and (
                token.startswith(
                    generic
                )
                or generic.startswith(
                    token
                )
            )
        ):
            return True

        if (
            len(root) >= 4
            and len(generic) >= 4
            and (
                root.startswith(
                    generic
                )
                or generic.startswith(
                    root
                )
            )
        ):
            return True

    return False

def evidence_excluded_terms(
    evidence,
):
    """
    Return explicit topic-scope exclusions from the evidence package.

    These are deterministic hard blocks, not model instructions.
    """

    coverage = evidence.get(
        "coverage",
        {},
    )

    return [
        str(term).strip()
        for term in coverage.get(
            "excluded_terms",
            [],
        )
        if str(term).strip()
    ]


def normalized_phrase(
    value,
):
    return " ".join(
        grounding_tokens(
            value
        )
    )


def meaningful_grounding_roots(
    value,
):
    roots = set()

    for token in grounding_tokens(
        value
    ):
        if len(token) < 4:
            continue

        root = grounding_root(
            token
        )

        if is_generic_grounding_token(
            token,
            root,
        ):
            continue

        roots.add(
            root
        )

    return roots


def grounding_roots_overlap(
    left,
    right,
):
    for left_root in left:
        for right_root in right:
            if left_root == right_root:
                return True

            if (
                len(left_root) >= 4
                and len(right_root) >= 4
                and (
                    left_root.startswith(
                        right_root
                    )
                    or right_root.startswith(
                        left_root
                    )
                )
            ):
                return True

    return False


def validate_validation_type_scope(
    package,
    evidence,
):
    """
    Prevent machine-validation type names from bypassing evidence scope.
    """

    excluded = {
        normalized_phrase(term)
        for term in evidence_excluded_terms(
            evidence
        )
    }

    validation_scope_terms = {
        "indefinite_integral": normalized_phrase(
            "belirsiz integral"
        ),
        "definite_integral": normalized_phrase(
            "belirli integral"
        ),
    }

    for index, item in enumerate(
        package.get(
            "examples",
            {},
        ).get(
            "examples",
            [],
        )
    ):
        validation = item.get(
            "validation",
            {},
        )

        validation_type = validation.get(
            "type"
        )

        scoped_term = validation_scope_terms.get(
            validation_type
        )

        if (
            scoped_term
            and scoped_term in excluded
        ):
            raise ValueError(
                "Evidence scope exclusion failed "
                f"at examples.examples[{index}].validation.type: "
                f"{validation_type}"
            )

    return True


def validate_claim_vocabulary_scope(
    package,
    evidence,
):
    """
    Phase 3.4 semantic scope contract.

    The old word-by-word allowlist was intentionally removed because
    natural Turkish paraphrases caused false positives. The guard now:

    1. blocks explicit evidence exclusions everywhere;
    2. requires core factual/domain-bearing fields to share at least
       one meaningful anchor with their cited evidence claim(s);
    3. does NOT reject harmless extra pedagogical wording.

    Claim IDs are still validated separately by
    validate_claim_level_provenance().
    """

    claims = claim_lookup(
        evidence
    )

    excluded_terms = [
        (
            term,
            normalized_phrase(
                term
            ),
        )
        for term in evidence_excluded_terms(
            evidence
        )
    ]

    for (
        path,
        text,
        refs,
        use_guard,
    ) in iter_grounded_items(
        package
    ):
        generated_phrase = normalized_phrase(
            text
        )

        for (
            original_term,
            excluded_phrase,
        ) in excluded_terms:
            if (
                excluded_phrase
                and excluded_phrase
                in generated_phrase
            ):
                raise ValueError(
                    "Evidence scope exclusion failed "
                    f"at {path}. Excluded term: "
                    f"{original_term}"
                )

        if not use_guard:
            continue

        claim_text = " ".join(
            claims[ref]["text"]
            for ref in refs
        )

        claim_roots = meaningful_grounding_roots(
            claim_text
        )

        generated_roots = meaningful_grounding_roots(
            text
        )

        # If a claim contains no stable lexical anchor, provenance is
        # still valid but this deterministic lexical check cannot add
        # information; do not invent a rejection criterion.
        if not claim_roots:
            continue

        if not grounding_roots_overlap(
            generated_roots,
            claim_roots,
        ):
            raise ValueError(
                "Evidence claim-anchor failed "
                f"at {path}. Generated text has no "
                "meaningful overlap with cited claim(s)."
            )

    validate_validation_type_scope(
        package,
        evidence,
    )

    return True


def canonicalize_grounded_package(
    package,
    evidence,
):
    """
    Strip generation-only evidence_refs from the canonical
    knowledge files while preserving a complete provenance map.

    This keeps existing knowledge_unit.schema.json compatible.
    """

    concept = package["concept"]

    canonical_concept = {
        "id": concept["id"],
        "subject": concept["subject"],
        "grade": concept["grade"],
        "topic": concept["topic"],
    }

    for field in (
        "learning_objectives",
        "prerequisites",
        "core_concepts",
        "rules",
        "common_confusions",
        "teaching_notes",
    ):
        canonical_concept[
            field
        ] = [
            item["text"]
            for item in concept.get(
                field,
                []
            )
        ]

    canonical_concept[
        "definitions"
    ] = [
        {
            "term": item[
                "term"
            ],
            "definition": item[
                "definition"
            ],
        }
        for item in concept.get(
            "definitions",
            []
        )
    ]

    canonical_examples = {
        "topic": package[
            "examples"
        ]["topic"],
        "examples": [],
    }

    for item in package[
        "examples"
    ].get(
        "examples",
        []
    ):
        canonical_item = {
            key: value
            for key, value in item.items()
            if key != "evidence_refs"
        }

        canonical_examples[
            "examples"
        ].append(
            canonical_item
        )

    canonical_mistakes = {
        "topic": package[
            "mistakes"
        ]["topic"],
        "mistakes": [],
    }

    for item in package[
        "mistakes"
    ].get(
        "mistakes",
        []
    ):
        canonical_item = {
            key: value
            for key, value in item.items()
            if key != "evidence_refs"
        }

        canonical_mistakes[
            "mistakes"
        ].append(
            canonical_item
        )

    canonical_relations = {
        "topic": package[
            "relations"
        ]["topic"],
    }

    for field in (
        "prerequisites",
        "next_topics",
        "related_topics",
    ):
        canonical_relations[
            field
        ] = []

        for item in package[
            "relations"
        ].get(
            field,
            []
        ):
            canonical_item = {
                key: value
                for key, value in item.items()
                if key != "evidence_refs"
            }

            canonical_relations[
                field
            ].append(
                canonical_item
            )

    provenance_items = []

    for (
        path,
        _text,
        refs,
        _guard,
    ) in iter_grounded_items(
        package
    ):
        provenance_items.append(
            {
                "path": path,
                "evidence_refs": refs,
            }
        )

    provenance = {
        "version": "1.0",
        "status": "PASS",
        "evidence_id": evidence[
            "id"
        ],
        "items": provenance_items,
    }

    return {
        "concept": canonical_concept,
        "examples": canonical_examples,
        "mistakes": canonical_mistakes,
        "relations": canonical_relations,
        "_provenance": provenance,
    }

def build_prompt(
    record,
    grade,
    evidence=None,
    generation_feedback=None,
):
    """
    Build strict JSON-generation instructions.

    Mathematics examples must include a
    machine-checkable validation block.
    """

    curriculum_json = json.dumps(
        record,
        ensure_ascii=False,
        indent=2,
    )

    if evidence is None:
        grounding_json = (
            "EVIDENCE NOT SUPPLIED TO PROMPT BUILDER"
        )
    else:
        grounding_json = build_grounding_context(
            evidence
        )

    retry_instruction = ""

    if generation_feedback:
        retry_instruction = f"""
ÖNCEKİ DENEME REDDEDİLDİ.

HATA:
{generation_feedback}

Aynı hatayı tekrar etme.
Özellikle:
- Geçerli JSON üret.
- Zorunlu alanları boş bırakma.
- Her factual öğede geçerli evidence_refs kullan.
- Evidence kapsamı dışına çıkma.
""".strip()

    math_validation_instruction = ""

    if normalize(record["subject"]) == normalize("Matematik"):
        math_validation_instruction = """
MATEMATİK ÜRETİM SINIRI:

Bu evidence-grounded factual draft aşamasında
examples.examples TAM OLARAK boş dizi [] olmalıdır.

Matematik örnekleri bu aşamada LLM tarafından üretilmez.
Örnekler ayrı bir machine-checkable example pipeline içinde
üretilip doğrulanacaktır.

Bu ayrımın amacı factual knowledge üretimi ile matematiksel
örnek üretimi/doğrulamasını birbirine karıştırmamaktır.
""".strip()

    return f"""
Sen YKS için eğitim içerik taslağı hazırlayan bir sistemsin.

GÖREV:
Aşağıdaki müfredat kaydı için yapılandırılmış bir KNOWLEDGE DRAFT üret.

Bu içerik otomatik olarak doğrulanmış kabul edilmeyecek.

KURALLAR:

- Aşağıdaki EVIDENCE PACKAGE tek güvenilir factual kaynaktır.
- Model hafızasından yeni tanım, kural, tarih, formül veya factual ayrıntı ekleme.
- Evidence tarafından desteklenmeyen factual içeriği üretme.
- Evidence bir alanı desteklemiyorsa o alanı uydurarak doldurma.
- Evidence bir alanı desteklemiyorsa ilgili diziyi boş bırak; sırf şemayı doldurmak için bilgi üretme.
- coverage.excluded_terms içinde yer alan kavramları hiçbir öğrenci-görünür alanda üretme.
- relations.prerequisites, relations.next_topics ve relations.related_topics bu aşamada TAM OLARAK [] olmalıdır.
- Konu ilişkileri LLM tarafından üretilmez; curriculum/graph katmanından deterministik olarak yönetilir.
- Müfredat kaydını kapsam/kimlik için kullan; factual kaynak olarak kullanma.
- Tartışmalı veya evidence içinde olmayan bilgiyi ekleme.
- Açık, temel ve YKS seviyesinde kal.
- Yalnızca Türkçe kullan.
- Matematiksel hesaplamaları dikkatlice kontrol et.
- Öğrenciye öğretilebilir, kısa ve net içerik üret.
- Sayısal örneklerde sonucu iki kez kontrol et.
- Matematiksel bir sonuç evidence ile desteklenmiyorsa üretme.
- Çıktının her factual parçası evidence claim'leriyle izlenebilir olmalıdır.

{math_validation_instruction}

{retry_instruction}

EVIDENCE PACKAGE:

{grounding_json}

MÜFREDAT KAYDI:

{curriculum_json}

ÖĞRENCİ SINIFI:
{grade}

ÇIKTI KURALI:

SADECE geçerli JSON üret.
Markdown kullanma.
Kod bloğu kullanma.
JSON dışında hiçbir açıklama yazma.

JSON üst yapısı:

ÖNEMLİ PROVENANCE KURALI:

- Aşağıdaki factual öğelerin HER BİRİ "evidence_refs" taşımalıdır.
- "evidence_refs" sadece EVIDENCE PACKAGE içindeki claim id değerlerini içerebilir.
- Bir claim desteklemiyorsa o bilgiyi üretme.
- Claim'de olmayan yeni alan terimleri ekleme.
- Sırf adet tamamlamak için içerik uydurma.
- Aynı claim farklı pedagogik alanlarda kullanılabilir.
- coverage.notes claim değildir; evidence_refs içinde kullanılamaz.

{{
  "concept": {{
    "id": "string",
    "subject": "{record['subject']}",
    "grade": "{grade}",
    "topic": "{record['topic']}",
    "learning_objectives": [
      {{
        "text": "string",
        "evidence_refs": ["C1"]
      }}
    ],
    "prerequisites": [
      {{
        "text": "string",
        "evidence_refs": ["C1"]
      }}
    ],
    "core_concepts": [
      {{
        "text": "string",
        "evidence_refs": ["C1"]
      }}
    ],
    "definitions": [
      {{
        "term": "string",
        "definition": "string",
        "evidence_refs": ["C1"]
      }}
    ],
    "rules": [
      {{
        "text": "string",
        "evidence_refs": ["C1"]
      }}
    ],
    "common_confusions": [
      {{
        "text": "string",
        "evidence_refs": ["C1"]
      }}
    ],
    "teaching_notes": [
      {{
        "text": "string",
        "evidence_refs": ["C1"]
      }}
    ]
  }},
  "examples": {{
    "topic": "{record['topic']}",
    "examples": []
  }},
  "mistakes": {{
    "topic": "{record['topic']}",
    "mistakes": [
      {{
        "id": "string",
        "error": "string",
        "explanation": "string",
        "teacher_action": "string",
        "evidence_refs": ["C1"]
      }}
    ]
  }},
  "relations": {{
    "topic": "{record['topic']}",
    "prerequisites": [],
    "next_topics": [],
    "related_topics": []
  }}
}}

İÇERİK MİKTARI:

- learning_objectives, core_concepts, definitions ve rules için evidence desteklediği kadar üret.
- prerequisites, common_confusions ve teaching_notes evidence desteklemiyorsa boş dizi olabilir.
- relations içindeki üç dizi bu aşamada her zaman [] olmalıdır.
- Matematik konusuysa examples.examples bu aşamada her zaman [] olmalıdır.
- mistake yalnızca evidence ile gerçekten destekleniyorsa üret; desteklenmiyorsa [] bırak.
- Evidence desteklemediği halde sayıyı artırmak YASAKTIR.
""".strip()


def extract_json(text):
    """
    Parse model output defensively.
    """

    if not text:
        raise ValueError(
            "Model returned empty content."
        )

    text = text.strip()

    if text.startswith("```"):

        text = re.sub(
            r"^```(?:json)?\s*",
            "",
            text,
            flags=re.IGNORECASE,
        )

        text = re.sub(
            r"\s*```$",
            "",
            text,
        )

    try:
        return json.loads(
            text
        )

    except json.JSONDecodeError:

        start = text.find("{")
        end = text.rfind("}")

        if (
            start == -1
            or end == -1
            or end <= start
        ):
            raise

        return json.loads(
            text[start:end + 1]
        )


def enforce_identity(
    package,
    record,
    grade,
):
    """
    Never trust the model for canonical identity fields.
    """

    subject = record["subject"]
    topic = record["topic"]

    subject_slug = slugify(
        subject
    )

    topic_slug = slugify(
        topic
    )

    concept = package.setdefault(
        "concept",
        {}
    )

    concept["id"] = (
        f"{subject_slug}."
        f"grade{grade}."
        f"{topic_slug}"
    )

    concept["subject"] = subject
    concept["grade"] = str(grade)
    concept["topic"] = topic

    for section_name in (
        "examples",
        "mistakes",
        "relations",
    ):

        section = package.setdefault(
            section_name,
            {}
        )

        section["topic"] = topic

    return package


def save_draft(
    record,
    grade,
    package,
    evidence=None,
):
    """
    Save generated package as DRAFT.
    """

    draft_path = get_draft_path(
        record["subject"],
        grade,
        record["topic"],
    )

    draft_path.mkdir(
        parents=True,
        exist_ok=True,
    )

    write_json(
        draft_path / "concept.json",
        package["concept"],
    )

    write_json(
        draft_path / "examples.json",
        package["examples"],
    )

    write_json(
        draft_path / "mistakes.json",
        package["mistakes"],
    )

    write_json(
        draft_path / "relations.json",
        package["relations"],
    )

    provenance = package.get(
        "_provenance"
    )

    if provenance:
        write_json(
            draft_path / "provenance.json",
            provenance,
        )

    metadata = {
        "status": "DRAFT",
        "verified": False,
        "generated_by": "local_llm",
        "model": MODEL_NAME,
        "generated_at": (
            datetime.now()
            .astimezone()
            .isoformat()
        ),
        "exam": record.get("exam"),
        "subject": record.get("subject"),
        "topic": record.get("topic"),
        "priority": record.get("priority"),
        "structure_status": None,
        "factual_review_status": None,
        "source_grounded": evidence is not None,
        "evidence_id": (
            evidence.get("id")
            if evidence
            else None
        ),
        "evidence_sources": (
            [
                item.get("source_id")
                for item in evidence.get(
                    "sources",
                    []
                )
            ]
            if evidence
            else []
        ),
        "claim_provenance_status": (
            provenance.get("status")
            if provenance
            else "NOT_RECORDED"
        ),
        "provenance_file": (
            "provenance.json"
            if provenance
            else None
        ),
        "warning": (
            "Claim provenance, structural, or deterministic validation "
            "does not constitute full factual verification."
        ),
    }

    write_json(
        draft_path / "draft_meta.json",
        metadata,
    )

    return draft_path


def update_draft_metadata(
    draft_path,
    structure_status,
    factual_review_status,
):
    """
    Persist automated review results into draft metadata.
    """

    meta_path = (
        draft_path
        / "draft_meta.json"
    )

    metadata = load_json(
        meta_path
    )

    metadata[
        "structure_status"
    ] = structure_status

    metadata[
        "factual_review_status"
    ] = factual_review_status

    metadata[
        "verified"
    ] = False

    write_json(
        meta_path,
        metadata,
    )


def validate_generated_math_package(
    package,
    subject,
):
    """
    Enforce machine-checkable validation blocks
    before a generated Mathematics draft is saved.

    This validates the validation contract itself.

    It does not establish factual correctness.
    """

    if normalize(subject) != normalize("Matematik"):
        return

    examples_section = package.get(
        "examples"
    )

    if not isinstance(
        examples_section,
        dict,
    ):
        raise ValueError(
            "Mathematics draft has no valid examples section."
        )

    examples = examples_section.get(
        "examples"
    )

    if not isinstance(
        examples,
        list,
    ):
        raise ValueError(
            "Mathematics examples must be a list."
        )

    # Phase 3.4.2 boundary:
    # evidence-grounded factual generation is allowed to contain
    # zero Mathematics examples. Math examples are produced in a
    # separate machine-checkable pipeline.
    if not examples:
        return True

    schema_path = (
        PROJECT_ROOT
        / "data"
        / "knowledge"
        / "schemas"
        / "math_example_validation.schema.json"
    )

    schema = load_json(
        schema_path
    )

    validator = Draft202012Validator(
        schema
    )

    for index, example in enumerate(
        examples,
        start=1,
    ):
        if not isinstance(
            example,
            dict,
        ):
            raise ValueError(
                f"Mathematics example {index} is invalid."
            )

        validation = example.get(
            "validation"
        )

        if not isinstance(
            validation,
            dict,
        ):
            raise ValueError(
                f"Mathematics example {index} "
                f"is missing validation."
            )

        errors = sorted(
            validator.iter_errors(
                validation
            ),
            key=lambda error: list(
                error.path
            ),
        )

        if errors:
            first = errors[0]

            location = ".".join(
                str(item)
                for item in first.path
            )

            if location:
                location = (
                    f" at '{location}'"
                )

            raise ValueError(
                f"Mathematics example {index} "
                f"validation contract failed"
                f"{location}: "
                f"{first.message}"
            )



def build_structured_response_format(
    record=None,
):
    """
    LM Studio/OpenAI-compatible structured output contract.

    Phase 3.4.2 generation boundaries:
    - topic relations are not generated by the LLM;
    - Mathematics examples are not generated in the factual pass.

    The static schema remains reusable, while these dynamic maxItems=0
    constraints make the boundary enforceable at generation time.
    """

    schema = load_json(
        GROUNDING_SCHEMA_PATH
    )

    # Deep copy because nested generation constraints are modified below.
    schema = json.loads(
        json.dumps(
            schema,
            ensure_ascii=False,
        )
    )

    relations_properties = (
        schema
        .get("properties", {})
        .get("relations", {})
        .get("properties", {})
    )

    for field in (
        "prerequisites",
        "next_topics",
        "related_topics",
    ):
        relation_array = (
            relations_properties.get(
                field
            )
        )

        if isinstance(
            relation_array,
            dict,
        ):
            relation_array[
                "maxItems"
            ] = 0

    if (
        record
        and normalize(
            record.get(
                "subject"
            )
        )
        == normalize(
            "Matematik"
        )
    ):
        examples_array = (
            schema
            .get("properties", {})
            .get("examples", {})
            .get("properties", {})
            .get("examples")
        )

        if isinstance(
            examples_array,
            dict,
        ):
            examples_array[
                "maxItems"
            ] = 0

    schema.pop(
        "$schema",
        None,
    )
    schema.pop(
        "$id",
        None,
    )
    schema.pop(
        "title",
        None,
    )

    return {
        "type": "json_schema",
        "json_schema": {
            "name": "knowledge_draft",
            "strict": True,
            "schema": schema,
        },
    }

def generate_one(
    record,
    grade,
    evidence=None,
    generation_feedback=None,
):
    if evidence is None:
        evidence = load_ready_evidence(
            record,
            grade,
        )

    prompt = build_prompt(
        record,
        grade,
        evidence=evidence,
        generation_feedback=generation_feedback,
    )

    response = (
        client
        .chat
        .completions
        .create(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Yalnızca geçerli JSON üret. "
                        "Markdown veya açıklama yazma."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=0.2,
            response_format=(
                build_structured_response_format(
                    record
                )
            ),
        )
    )

    if not response.choices:
        raise RuntimeError(
            "Model returned no choices."
        )

    content = (
        response
        .choices[0]
        .message
        .content
    )

    package = extract_json(
        content
    )

    package = enforce_identity(
        package,
        record,
        grade,
    )

    validate_grounded_generation_schema(
        package
    )

    validate_claim_level_provenance(
        package,
        evidence,
    )

    validate_claim_vocabulary_scope(
        package,
        evidence,
    )

    package = canonicalize_grounded_package(
        package,
        evidence,
    )

    validate_generated_math_package(
        package,
        record["subject"],
    )

    return package


def generate_with_retry(
    record,
    grade,
    max_attempts=3,
    evidence=None,
):
    """
    Generate one package with bounded retries.

    Retries are limited to generation/contract failures
    such as malformed JSON, missing required validation
    fields, unsupported validation contracts, or an empty
    model result. Deterministic factual-review failures are
    intentionally NOT retried here because review happens
    only after a draft has been generated and saved.

    Returns:
        (package, attempts_used)
    """

    if max_attempts < 1:
        raise ValueError(
            "max_attempts must be at least 1."
        )

    topic = record.get(
        "topic",
        "UNKNOWN",
    )

    previous_error = None

    for attempt in range(
        1,
        max_attempts + 1,
    ):
        try:
            if evidence is None:
                package = generate_one(
                    record,
                    grade,
                    generation_feedback=previous_error,
                )
            else:
                package = generate_one(
                    record,
                    grade,
                    evidence=evidence,
                    generation_feedback=previous_error,
                )

            return package, attempt

        except RETRYABLE_GENERATION_ERRORS as exc:
            previous_error = str(
                exc
            )

            if attempt >= max_attempts:
                error = RuntimeError(
                    f"Generation failed after {max_attempts} "
                    f"attempt(s) for '{topic}'. "
                    f"Last error: {exc}"
                )

                error.attempts_used = attempt

                raise error from exc

            print(
                f"RETRY      | {topic} "
                f"| attempt {attempt + 1}/{max_attempts} "
                f"| previous error: {exc}"
            )


def select_records(
    exam,
    subject,
    topic=None,
):
    curriculum = load_curriculum_data()

    selected = []

    for record in curriculum:

        if (
            normalize(
                record.get("exam")
            )
            != normalize(exam)
        ):
            continue

        if (
            normalize(
                record.get("subject")
            )
            != normalize(subject)
        ):
            continue

        if (
            topic
            and normalize(
                record.get("topic")
            )
            != normalize(topic)
        ):
            continue

        selected.append(
            record
        )

    return selected


def run_automated_reviews(
    draft_path,
    subject,
):
    """
    Run structural and deterministic factual checks.

    Returns:
        structure_status
        factual_review_status
    """

    structure_valid = validate_topic(
        draft_path,
        verbose=False,
    )

    structure_status = (
        "PASS"
        if structure_valid
        else "FAIL"
    )

    factual_review_status = (
        "NOT_APPLICABLE"
    )

    if normalize(subject) == normalize(
        "Matematik"
    ):

        factual_report = review_draft(
            draft_path
        )

        factual_review_status = (
            factual_report["status"]
        )

    update_draft_metadata(
        draft_path,
        structure_status,
        factual_review_status,
    )

    return (
        structure_status,
        factual_review_status,
    )


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Generate evidence-grounded local-LLM knowledge drafts "
            "from curriculum records."
        )
    )

    parser.add_argument(
        "--exam",
        required=True,
        help="TYT or AYT",
    )

    parser.add_argument(
        "--subject",
        required=True,
        help="Curriculum subject name",
    )

    parser.add_argument(
        "--grade",
        default="12",
        help="Student release grade. Default: 12",
    )

    parser.add_argument(
        "--topic",
        default=None,
        help="Generate only one exact topic",
    )

    parser.add_argument(
        "--max-topics",
        type=int,
        default=None,
        help="Maximum number of topics to generate",
    )

    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite an existing draft",
    )

    parser.add_argument(
        "--max-attempts",
        type=int,
        default=3,
        help=(
            "Maximum generation attempts per topic. "
            "Default: 3"
        ),
    )

    args = parser.parse_args()

    if args.max_attempts < 1:
        parser.error(
            "--max-attempts must be at least 1"
        )

    connection = check_llm_connection()

    if not connection["connected"]:

        print(
            "ERROR: LM Studio is not available."
        )

        print(
            connection["error"]
        )

        sys.exit(1)

    if MODEL_NAME not in connection["models"]:

        print(
            f"ERROR: Model '{MODEL_NAME}' "
            "is not loaded."
        )

        sys.exit(1)

    records = select_records(
        args.exam,
        args.subject,
        topic=args.topic,
    )

    if not records:

        print(
            "No curriculum records matched."
        )

        sys.exit(1)

    generated = 0
    skipped_units = 0
    skipped_drafts = 0
    skipped_evidence = 0
    failed = 0
    retries_used = 0

    structure_pass = 0
    structure_fail = 0

    factual_pass = 0
    factual_fail = 0
    factual_unverified = 0
    factual_not_applicable = 0

    print(
        "=" * 70
    )

    print(
        "KNOWLEDGE DRAFT BATCH GENERATOR"
    )

    print(
        "=" * 70
    )

    print(
        f"Exam: {args.exam}"
    )

    print(
        f"Subject: {args.subject}"
    )

    print(
        f"Model: {MODEL_NAME}"
    )

    print(
        f"Max attempts per topic: "
        f"{args.max_attempts}"
    )

    print(
        f"Matched curriculum topics: "
        f"{len(records)}"
    )

    print()

    for record in records:

        if (
            args.max_topics is not None
            and generated >= args.max_topics
        ):
            break

        topic = record["topic"]

        existing_unit = find_existing_unit(
            record["subject"],
            topic,
        )

        if existing_unit is not None:

            print(
                f"SKIP UNIT  | {topic}"
            )

            skipped_units += 1
            continue

        try:
            evidence = load_ready_evidence(
                record,
                args.grade,
            )

        except Exception as exc:
            print(
                f"SKIP EVID  | {topic} "
                f"| {exc}"
            )

            skipped_evidence += 1
            continue

        draft_path = get_draft_path(
            record["subject"],
            args.grade,
            topic,
        )

        if (
            draft_path.exists()
            and not args.overwrite
        ):

            print(
                f"SKIP DRAFT | {topic}"
            )

            skipped_drafts += 1
            continue

        removed_old_draft = (
            prepare_draft_for_overwrite(
                draft_path,
                args.overwrite,
            )
        )

        if removed_old_draft:
            print(
                f"REMOVE OLD | {topic}"
            )

        print(
            f"GENERATING | {topic}"
        )

        try:

            (
                package,
                attempts_used,
            ) = generate_with_retry(
                record,
                args.grade,
                max_attempts=args.max_attempts,
                evidence=evidence,
            )

            retries_used += (
                attempts_used - 1
            )

            draft_path = save_draft(
                record,
                args.grade,
                package,
                evidence=evidence,
            )

            (
                structure_status,
                factual_status,
            ) = run_automated_reviews(
                draft_path,
                record["subject"],
            )

            if structure_status == "PASS":

                structure_pass += 1

            else:

                structure_fail += 1

            if factual_status == "FAIL":

                factual_fail += 1

            elif factual_status in (
                "PASS",
                "PASS_WITH_LIMITED_SCOPE",
            ):

                factual_pass += 1

            elif factual_status == "UNVERIFIED":

                factual_unverified += 1

            else:

                factual_not_applicable += 1

            print(
                f"DRAFT      | {topic}"
            )

            print(
                f"  STRUCTURE: "
                f"{structure_status}"
            )

            print(
                f"  FACTUAL  : "
                f"{factual_status}"
            )

            generated += 1

        except Exception as exc:

            attempts_used = getattr(
                exc,
                "attempts_used",
                1,
            )

            retries_used += max(
                0,
                attempts_used - 1,
            )

            print(
                f"FAILED     | {topic} "
                f"| {exc}"
            )

            failed += 1

    print()

    print(
        "=" * 70
    )

    print(
        "BATCH SUMMARY"
    )

    print(
        "=" * 70
    )

    print(
        f"Generated drafts       : {generated}"
    )

    print(
        f"Existing units         : {skipped_units}"
    )

    print(
        f"Existing drafts        : {skipped_drafts}"
    )

    print(
        f"Missing/not-ready evidence: {skipped_evidence}"
    )

    print(
        f"Generation failures    : {failed}"
    )

    print(
        f"Retries used           : {retries_used}"
    )

    print()

    print(
        f"Structure PASS         : {structure_pass}"
    )

    print(
        f"Structure FAIL         : {structure_fail}"
    )

    print()

    print(
        f"Factual PASS           : {factual_pass}"
    )

    print(
        f"Factual FAIL           : {factual_fail}"
    )

    print(
        f"Factual UNVERIFIED     : {factual_unverified}"
    )

    print(
        f"Factual NOT_APPLICABLE : {factual_not_applicable}"
    )

    print()

    print(
        "IMPORTANT:"
    )

    print(
        "Generated files are still DRAFTS."
    )

    print(
        "Automated PASS does NOT mean VERIFIED."
    )

    print(
        "Student access remains disabled until "
        "a draft is explicitly promoted."
    )


if __name__ == "__main__":
    main()
