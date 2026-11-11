"""Shared Rule 1 digest, assessment, and capability-versus-authorization checks.

These checks apply to knowledge records and tool records. They enforce the
declared invariant and the companion working principle on recorded artifacts.
They do not prove that a tool can never cause harm.
"""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

START = "<!-- RULE-1-CANONICAL-START -->"
END = "<!-- RULE-1-CANONICAL-END -->"

PROTECTION_IDS = ("P1", "P2", "P3", "P4", "P5", "P6")
PROTECTION_TITLES = {
    "P1": "Protect life",
    "P2": "Protect existence",
    "P3": "Respect rights and dignity",
    "P4": "Prevent uncontrolled consequences",
    "P5": "Preserve accountability",
    "P6": "Stop when safety cannot be established",
}
ADDRESSED = "addressed"
NA = "not-applicable-with-reason"
OPEN = "open"
ALLOWED_STATUSES = {ADDRESSED, NA, OPEN}
AUTH_RANK = {"NOT_AUTHORIZED": 0, "AUTHORIZED": 1}
HUMAN_DECISION_KINDS = {"human_decision", "human_authorization"}
FORBIDDEN_INTERPRETATION_KINDS = {"tablet_text", "source_text", "verbatim_source"}
COMPANION_SENTENCE = (
    "Ascendence without responsibility becomes uncontrolled power"
)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def extract_canonical_text(markdown: str) -> str:
    if START in markdown and END in markdown:
        start = markdown.index(START) + len(START)
        end = markdown.index(END)
        body = markdown[start:end]
        if body.startswith("\n"):
            body = body[1:]
        if body.endswith("\n"):
            body = body[:-1]
        return body
    if markdown.endswith("\n"):
        return markdown[:-1]
    return markdown


def foundation_dir(repo_root: Path) -> Path:
    return Path(repo_root) / "foundation"


def rule_1_markdown_path(repo_root: Path) -> Path:
    return foundation_dir(repo_root) / "RULE_1.md"


def rule_1_machine_path(repo_root: Path) -> Path:
    return foundation_dir(repo_root) / "rule_1.json"


def canonical_rule_1_text(repo_root: Path) -> str:
    return extract_canonical_text(rule_1_markdown_path(repo_root).read_text(encoding="utf-8"))


def canonical_rule_1_digest(repo_root: Path) -> str:
    return sha256_text(canonical_rule_1_text(repo_root))


def load_rule_1_machine(repo_root: Path) -> dict[str, Any]:
    return json.loads(rule_1_machine_path(repo_root).read_text(encoding="utf-8"))


def check_rule_1_document(repo_root: Path) -> list[str]:
    errors: list[str] = []
    md_path = rule_1_markdown_path(repo_root)
    machine_path = rule_1_machine_path(repo_root)
    if not md_path.is_file():
        return [f"missing {md_path.as_posix()}"]
    if not machine_path.is_file():
        return [f"missing {machine_path.as_posix()}"]
    markdown = md_path.read_text(encoding="utf-8")
    if START not in markdown or END not in markdown:
        errors.append("RULE_1.md is missing canonical start or end markers")
    digest = canonical_rule_1_digest(repo_root)
    machine = load_rule_1_machine(repo_root)
    if machine.get("id") != "RULE-1":
        errors.append("foundation/rule_1.json id must be RULE-1")
    if machine.get("canonical_sha256") != digest:
        errors.append(
            "foundation/rule_1.json canonical_sha256 does not match RULE_1.md canonical text"
        )
    related = machine.get("related_working_principles") or []
    for item in related:
        if not isinstance(item, dict):
            errors.append("related working principle entry is not an object")
            continue
        if item.get("part_of_canonical_text") is True:
            errors.append(
                "related working principles must not be marked as part of the canonical text"
            )
        if item.get("plan_amendment") is True:
            errors.append("related working principles must not be marked as a Plan amendment")
        path = item.get("path")
        if path and not (Path(repo_root) / path).is_file():
            errors.append(f"related working principle file missing: {path}")
    canonical = canonical_rule_1_text(repo_root)
    companion = foundation_dir(repo_root) / "ASCENDENCE_RESPONSIBILITY.md"
    if COMPANION_SENTENCE in canonical:
        errors.append("RULE-1 canonical text must not include the companion working principle")
    if companion.is_file():
        companion_text = companion.read_text(encoding="utf-8")
        if COMPANION_SENTENCE not in companion_text:
            errors.append("companion working principle file is missing the required sentence")
        if (
            "You don't transcend responsibility; you transcend the limitations that prevent you from fulfilling responsibility better."
            not in companion_text
        ):
            errors.append("companion working principle file is missing the second required sentence")
    elif related:
        errors.append("companion working principle file foundation/ASCENDENCE_RESPONSIBILITY.md is missing")
    return errors


def check_rule_1_reference(record: dict[str, Any], repo_root: Path, *, label: str) -> list[str]:
    errors: list[str] = []
    ref = record.get("rule_1")
    if not isinstance(ref, dict):
        return [f"{label}: missing rule_1 reference"]
    if ref.get("id") != "RULE-1":
        errors.append(f"{label}: rule_1.id must be RULE-1")
    expected = canonical_rule_1_digest(repo_root)
    if ref.get("digest") != expected:
        errors.append(f"{label}: rule_1.digest does not match the current RULE-1 canonical digest")
    return errors


def locator_exists(locator: dict[str, Any], repo_root: Path) -> list[str]:
    if not isinstance(locator, dict):
        return ["evidence locator is not an object"]
    if locator.get("repository"):
        return []
    path = locator.get("path")
    if not path:
        return ["evidence locator is missing a path"]
    candidate = Path(repo_root) / path
    if not candidate.exists():
        return [f"evidence locator path does not exist: {path}"]
    return []



NA_MIN_REASON_LENGTH = 40
NA_PLACEHOLDERS = frozenset(
    {
        "n/a",
        "na",
        "n.a",
        "n.a.",
        "none",
        "tbd",
        "todo",
        "unknown",
        "-",
        "--",
        "---",
        ".",
        "null",
        "nil",
        "not applicable",
        "not-applicable",
        "pending",
        "placeholder",
        "idk",
        "same",
        "see above",
        "as above",
        "n/a.",
        "none.",
    }
)
REASON_REF_KINDS = frozenset({"evidence", "human_decision"})


def normalize_reason_text(text: str) -> str:
    return " ".join(text.strip().lower().split())


def is_placeholder_reason(text: str) -> bool:
    norm = normalize_reason_text(text)
    if norm in NA_PLACEHOLDERS:
        return True
    alnum = "".join(ch if ch.isalnum() or ch.isspace() else " " for ch in norm)
    alnum = " ".join(alnum.split())
    return alnum in {
        "na",
        "none",
        "tbd",
        "todo",
        "unknown",
        "null",
        "nil",
        "pending",
        "placeholder",
        "not applicable",
    }


def evidence_record_exists(repo_root: Path, evidence_id: str) -> bool:
    if not isinstance(evidence_id, str):
        return False
    ident = evidence_id.strip()
    if not ident or "/" in ident or "\\" in ident or ident.startswith(".") or ".." in ident:
        return False
    return (Path(repo_root) / "registry" / "evidence" / f"{ident}.json").is_file()


def collect_decision_ids(repo_root: Path, record: dict[str, Any]) -> set[str]:
    ids: set[str] = set()
    dec = record.get("decision_record")
    if isinstance(dec, dict):
        ident = dec.get("id")
        if isinstance(ident, str) and ident.strip():
            ids.add(ident.strip())
    for folder in (
        Path(repo_root) / "registry" / "tools",
        Path(repo_root) / "registry" / "evidence",
        Path(repo_root) / "registry" / "decisions",
        Path(repo_root) / "knowledge" / "records",
    ):
        if not folder.is_dir():
            continue
        for path in folder.glob("*.json"):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if isinstance(payload, dict):
                item = payload.get("decision_record")
                if isinstance(item, dict):
                    ident = item.get("id")
                    if isinstance(ident, str) and ident.strip():
                        ids.add(ident.strip())
    return ids


def own_identifiers(record: dict[str, Any]) -> set[str]:
    ids: set[str] = set()
    for key in ("id", "record_id", "name"):
        value = record.get(key)
        if isinstance(value, str) and value.strip():
            ids.add(value.strip())
    return ids


def is_self_authorization(record: dict[str, Any]) -> bool:
    dec = record.get("decision_record")
    if not isinstance(dec, dict):
        return False
    ident = dec.get("id")
    if not isinstance(ident, str) or not ident.strip():
        return False
    return ident.strip() in own_identifiers(record)


def check_not_applicable_reason(
    item: dict[str, Any],
    pid: str,
    label: str,
    record: dict[str, Any],
    repo_root: Path,
    seen_reasons: set[str],
) -> list[str]:
    """Structural checks only. This does not judge whether a reason is true."""

    errors: list[str] = []
    reason = item.get("reason")
    if not isinstance(reason, str) or not reason.strip():
        errors.append(f"{label}: {pid} not-applicable-with-reason requires a reason")
        return errors
    stripped = reason.strip()
    if is_placeholder_reason(stripped):
        errors.append(
            f"{label}: {pid} not-applicable-with-reason rejects placeholder reason {stripped!r}"
        )
    if len(stripped) < NA_MIN_REASON_LENGTH:
        errors.append(
            f"{label}: {pid} not-applicable-with-reason is shorter than {NA_MIN_REASON_LENGTH} characters"
        )
    key = normalize_reason_text(stripped)
    if key in seen_reasons:
        errors.append(
            f"{label}: {pid} not-applicable-with-reason duplicates another protection's reason"
        )
    else:
        seen_reasons.add(key)
    ref = item.get("reason_ref")
    if not isinstance(ref, dict):
        errors.append(
            f"{label}: {pid} not-applicable-with-reason requires reason_ref "
            "citing an evidence id or a human decision id that exists in the registry"
        )
        return errors
    kind = ref.get("kind")
    ident = ref.get("id")
    if kind not in REASON_REF_KINDS or not isinstance(ident, str) or not ident.strip():
        errors.append(
            f"{label}: {pid} reason_ref must have kind 'evidence' or 'human_decision' and a non-empty id"
        )
        return errors
    ident = ident.strip()
    if ident not in stripped:
        errors.append(f"{label}: {pid} reason must reference reason_ref id {ident!r}")
    if kind == "evidence":
        if not evidence_record_exists(repo_root, ident):
            errors.append(
                f"{label}: {pid} reason_ref evidence id {ident!r} was not found in the registry"
            )
    else:
        known = collect_decision_ids(repo_root, record)
        if ident not in known:
            errors.append(
                f"{label}: {pid} reason_ref human decision id {ident!r} was not found "
                "on this record or in the registry"
            )
    return errors


def check_rule_1_assessment(
    record: dict[str, Any],
    repo_root: Path,
    *,
    label: str,
    require_local_evidence: bool = True,
) -> list[str]:
    errors: list[str] = []
    block = record.get("rule_1_assessment")
    if not isinstance(block, dict):
        return [f"{label}: missing rule_1_assessment"]
    protections = block.get("protections")
    if not isinstance(protections, list):
        return [f"{label}: rule_1_assessment.protections must be an array"]
    seen: list[str] = []
    seen_reasons: set[str] = set()
    for item in protections:
        if not isinstance(item, dict):
            errors.append(f"{label}: protection entry is not an object")
            continue
        pid = item.get("id")
        seen.append(pid if isinstance(pid, str) else "")
        if pid not in PROTECTION_IDS:
            errors.append(f"{label}: unknown protection id {pid!r}")
            continue
        if item.get("title") != PROTECTION_TITLES[pid]:
            errors.append(f"{label}: {pid} title must be {PROTECTION_TITLES[pid]!r}")
        status = item.get("status")
        if status not in ALLOWED_STATUSES:
            errors.append(f"{label}: {pid} has invalid status {status!r}")
            continue
        if status == OPEN:
            errors.append(f"{label}: {pid} is open, which is treated as unaddressed")
        elif status == NA:
            errors.extend(
                check_not_applicable_reason(item, pid, label, record, repo_root, seen_reasons)
            )
        elif status == ADDRESSED:
            locators = item.get("evidence_locators")
            if not isinstance(locators, list) or not locators:
                errors.append(f"{label}: {pid} addressed requires evidence_locators")
            elif require_local_evidence:
                for loc in locators:
                    for err in locator_exists(loc, repo_root):
                        errors.append(f"{label}: {pid}: {err}")
    missing = [pid for pid in PROTECTION_IDS if pid not in seen]
    if missing:
        errors.append(f"{label}: rule_1_assessment is missing protections: {', '.join(missing)}")
    nonempty = [pid for pid in seen if pid]
    if len(nonempty) != len(set(nonempty)):
        errors.append(f"{label}: rule_1_assessment has duplicate protection ids")
    return errors


def capabilities_of(record: dict[str, Any]) -> set[str]:
    caps = record.get("capabilities") or []
    return {item for item in caps if isinstance(item, str)} if isinstance(caps, list) else set()


def permissions_of(record: dict[str, Any]) -> set[str]:
    perms = record.get("permissions") or []
    return {item for item in perms if isinstance(item, str)} if isinstance(perms, list) else set()


def authorization_status(record: dict[str, Any]) -> str:
    auth = record.get("authorization")
    if isinstance(auth, dict):
        return str(auth.get("status") or "NOT_AUTHORIZED")
    return "NOT_AUTHORIZED"


def capability_set_grew(current: dict[str, Any], proposed: dict[str, Any]) -> bool:
    return bool(capabilities_of(proposed) - capabilities_of(current))


def authorization_or_permissions_grew(current: dict[str, Any], proposed: dict[str, Any]) -> bool:
    old_rank = AUTH_RANK.get(authorization_status(current), 0)
    new_rank = AUTH_RANK.get(authorization_status(proposed), 0)
    if new_rank > old_rank:
        return True
    return bool(permissions_of(proposed) - permissions_of(current))


def has_human_decision(record: dict[str, Any]) -> bool:
    """Structural citation check only.

    This does not verify a signature, identity document, or that the cited
    decision-maker had authority to authorize the change.
    """
    dec = record.get("decision_record")
    if not isinstance(dec, dict):
        return False
    if dec.get("kind") not in HUMAN_DECISION_KINDS:
        return False
    ident = dec.get("id")
    if not isinstance(ident, str) or not ident.strip():
        return False
    if ident.strip() in own_identifiers(record):
        return False
    return True


def assessment_redone(current: dict[str, Any], proposed: dict[str, Any]) -> bool:
    old = current.get("rule_1_assessment") if isinstance(current.get("rule_1_assessment"), dict) else {}
    new = proposed.get("rule_1_assessment") if isinstance(proposed.get("rule_1_assessment"), dict) else {}
    old_rev = old.get("revision", 0)
    new_rev = new.get("revision", 0)
    if not isinstance(new_rev, int) or isinstance(new_rev, bool):
        return False
    if not isinstance(old_rev, int) or isinstance(old_rev, bool):
        old_rev = 0
    if new_rev <= old_rev:
        return False
    token = new.get("reassessed_for")
    if not isinstance(token, str) or not token.strip():
        return False
    added = sorted(capabilities_of(proposed) - capabilities_of(current))
    if added and not all(cap in token for cap in added):
        return False
    added_perms = sorted(permissions_of(proposed) - permissions_of(current))
    if added_perms and not all(perm in token for perm in added_perms):
        return False
    return True


def check_capability_authorization_growth(
    current: dict[str, Any],
    proposed: dict[str, Any],
    *,
    label: str,
) -> list[str]:
    """Authorization or permission growth requires a human decision and reassessment.

    This applies whether or not the capability set also grew. A capability
    increase alone never raises authorization. The human-decision check is
    structural only: it does not verify signatures or authority.
    """
    if not authorization_or_permissions_grew(current, proposed):
        return []
    grew_caps = capability_set_grew(current, proposed)
    if grew_caps:
        need = "capability growth that raises authorization or permissions"
        decision_msg = (
            f"{label}: capability growth must not raise authorization or permissions "
            "without a cited human decision record"
        )
        reassessment_msg = (
            f"{label}: capability growth that raises authorization or permissions "
            "requires a re-done rule_1 assessment (higher revision and reassessed_for "
            "citing the added capabilities)"
        )
    else:
        need = "authorization or permission increase"
        decision_msg = (
            f"{label}: authorization or permission increase requires a cited "
            "human decision record"
        )
        reassessment_msg = (
            f"{label}: authorization or permission increase requires a re-done "
            "rule_1 assessment (higher revision and reassessed_for citing the "
            "added permissions or authorization change)"
        )
    errors: list[str] = []
    if is_self_authorization(proposed):
        errors.append(
            f"{label}: {need} must not cite the record's own id as a human decision "
            "(self-authorization)"
        )
    elif not has_human_decision(proposed):
        errors.append(decision_msg)
    if not assessment_redone(current, proposed):
        errors.append(reassessment_msg)
    return errors


def proposal_touches_rule_1(current: dict[str, Any], proposed: dict[str, Any]) -> bool:
    old_ref = current.get("rule_1") if isinstance(current.get("rule_1"), dict) else {}
    new_ref = proposed.get("rule_1") if isinstance(proposed.get("rule_1"), dict) else {}
    if new_ref.get("id") != old_ref.get("id"):
        return True
    if new_ref.get("digest") != old_ref.get("digest"):
        return True
    for key in ("rule_1_canonical_text", "canonical_sha256", "rule_1_text"):
        if key in proposed and proposed.get(key) != current.get(key):
            return True
    return False


def apply_proposed_update(
    current: dict[str, Any],
    proposed: dict[str, Any],
    repo_root: Path,
    *,
    label: str,
) -> tuple[dict[str, Any] | None, list[str]]:
    """Bounded recursion: keep K_n unless the proposed update is approved.

    Mutations of RULE-1 text or digest are never approved by this path.
    """
    if proposal_touches_rule_1(current, proposed):
        return None, [
            f"{label}: proposed change that touches RULE-1 text or digest is rejected; K_n is unchanged"
        ]
    errors: list[str] = []
    errors.extend(check_rule_1_reference(proposed, repo_root, label=label))
    errors.extend(check_rule_1_assessment(proposed, repo_root, label=label))
    errors.extend(check_capability_authorization_growth(current, proposed, label=label))
    if errors:
        return None, errors
    return deepcopy(proposed), []
