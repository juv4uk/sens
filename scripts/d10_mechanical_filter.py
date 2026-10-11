#!/usr/bin/env python3
"""Fail-closed D10 candidate intake. Does not select, place, or ratify."""
import argparse
import csv
import hashlib
import json
import re
import subprocess
from pathlib import Path

COLUMNS = ("candidate_id", "semantic_name", "semantic_law", "donor_provenance",
           "source_pin", "witness_command", "witness_artifact", "witness_sha",
           "witness_exit_status", "witness_verdict", "semantic_dedup_certificate",
           "duplicate_target", "coordinate", "ratification_state", "decision", "reason")


def git_blob(data):
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def safe_file(root, name):
    if not name or Path(name).is_absolute():
        return None
    target = (root / name).resolve()
    if not target.is_relative_to(root.resolve()) or not target.is_file():
        return None
    return target


def read_donor_provenance(root, locator):
    """Resolve an exact source blob; never substitute working-tree bytes for a pinned commit."""
    pinned = re.fullmatch(
        r"([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)@([0-9a-f]{40}):([^:\t\n]+):([1-9][0-9]*)(?:-([1-9][0-9]*))?",
        locator,
    )
    if pinned:
        repo, commit, path, first, last = pinned.groups()
        # Foreign repositories and primary-source URLs require separately archived proofs.
        if repo != "juv4uk/sens" or path.startswith("/") or "\\" in path or any(
            part in ("", ".", "..") for part in path.split("/")
        ):
            return None
        try:
            verify = subprocess.run(
                ["git", "-C", str(root), "rev-parse", "--verify", f"{commit}^{{commit}}"],
                capture_output=True, check=False, timeout=10,
            )
            if verify.returncode or verify.stdout.decode("ascii", errors="replace").strip() != commit:
                return None
            source = subprocess.run(
                ["git", "-C", str(root), "show", f"{commit}:{path}"],
                capture_output=True, check=False, timeout=10,
            )
            if source.returncode:
                return None
        except (OSError, subprocess.TimeoutExpired):
            return None
        return source.stdout, int(first), int(last or first)
    local = re.fullmatch(r"([^:\t\n]+):([1-9][0-9]*)(?:-([1-9][0-9]*))?", locator)
    if local:
        path = safe_file(root, local.group(1))
        if path is not None:
            return path.read_bytes(), int(local.group(2)), int(local.group(3) or local.group(2))
    return None


def read_json_receipt(root, path, digest):
    p = safe_file(root, path)
    if p is None or not re.fullmatch(r"[0-9a-f]{64}", digest or ""):
        return None
    raw = p.read_bytes()
    if hashlib.sha256(raw).hexdigest() != digest:
        return None
    try:
        return json.loads(raw)
    except (ValueError, UnicodeError):
        return None


def load_baseline(root):
    ptr = json.loads((root / "knowledge/d10-current-inventory.json").read_text())
    cp = ptr["canonical_current"]
    ipath = safe_file(root, cp["path"])
    if ipath is None or git_blob(ipath.read_bytes()) != cp["git_blob"]:
        raise ValueError("CANONICAL_POINTER_SHA_MISMATCH")
    inv = json.loads(ipath.read_text())
    if inv.get("width") != 10 or inv.get("capacity") != 1024:
        raise ValueError("INVALID_D10_CAPACITY")
    coords = {}
    for row in inv["rows"]:
        coord = row.get("coordinate")
        if coord is not None:
            if not re.fullmatch(r"[01]{10}", coord) or coord in coords:
                raise ValueError("INVALID_CANONICAL_COORDINATES")
            coords[coord] = row["stable_id"]
    foundation = (root / "knowledge/d1-d9-foundation.json").read_bytes()
    return cp["git_blob"], git_blob(foundation), coords


def evaluate(row, root, inventory_sha, foundation_sha, occupied):
    out = dict(row)
    name, ident = row["semantic_name"], row["candidate_id"]
    def verdict(decision, reason):
        out.update(decision=decision, reason=reason)
        return out
    # F1: pinned repository source, with a real line locator.
    source = row["donor_provenance"]
    if not name or not ident or not row["semantic_law"] or not source:
        return verdict("rejected", "EXCLUDE_NO_PROVENANCE")
    pinned = read_donor_provenance(root, source)
    if pinned is None:
        # Unsupported but identified historical sources must not disappear as "no provenance".
        if "@" in source or source.startswith(("https://", "http://")) or re.search(r":[1-9][0-9]*(?:-[1-9][0-9]*)?$", source):
            return verdict("escalated", "HOLD_UNVERIFIED_PIN")
        return verdict("rejected", "EXCLUDE_NO_PROVENANCE")
    raw, first, last = pinned
    if (not re.fullmatch(r"[0-9a-f]{40}", row["source_pin"])
            or git_blob(raw) != row["source_pin"]
            or last < first or last > len(raw.splitlines())):
        return verdict("escalated", "HOLD_UNVERIFIED_PIN")
    # F2: recorded command + digest-verified positive/negative oracle run receipt.
    if not row["witness_artifact"]:
        return verdict("rejected", "EXCLUDE_NO_WITNESS")
    receipt = read_json_receipt(root, row["witness_artifact"], row["witness_sha"])
    if receipt is None:
        return verdict("rejected", "HOLD_NOT_RUN")
    if receipt.get("candidate_id") != ident or receipt.get("source_pin") != row["source_pin"] or receipt.get("command") != row["witness_command"]:
        return verdict("rejected", "HOLD_NOT_RUN")
    if receipt.get("exit_code") != 0 or receipt.get("positive") != "PASS" or receipt.get("negative") != "PASS":
        return verdict("rejected", "REJECT_FAILED_WITNESS")
    if row["witness_exit_status"] != "0" or row["witness_verdict"] != "PASS":
        return verdict("rejected", "HOLD_NOT_RUN")
    # F3: an independently reviewable semantic comparison certificate.
    certpath, sep, digest = row["semantic_dedup_certificate"].partition("#sha256=")
    cert = read_json_receipt(root, certpath, digest) if sep else None
    if (not isinstance(cert, dict) or cert.get("candidate_id") != ident
            or cert.get("inventory_sha") != inventory_sha
            or cert.get("foundation_sha") != foundation_sha
            or cert.get("d1_d9_checked") is not True
            or cert.get("selected_d10_checked") is not True
            or not cert.get("comparison_evidence")):
        return verdict("rejected", "HOLD_DEDUP_UNPROVEN")
    if cert.get("outcome") == "DUPLICATE":
        if not row["duplicate_target"] or row["duplicate_target"] != cert.get("duplicate_target"):
            return verdict("rejected", "HOLD_DEDUP_UNPROVEN")
        return verdict("rejected", "EXCLUDE_DUP")
    if cert.get("outcome") != "DISTINCT":
        return verdict("rejected", "HOLD_DEDUP_UNPROVEN")
    # F4: an actual canonical coordinate collision, never a vacant proposal.
    coord = row["coordinate"]
    if coord:
        if not re.fullmatch(r"[01]{10}", coord):
            return verdict("rejected", "HOLD_INVALID_COORDINATE")
        if coord in occupied and occupied[coord] != ident:
            out["duplicate_target"] = occupied[coord]
            return verdict("escalated", "ESCALATE_OWNER_COORDINATE")
    if cert.get("ratified_conflict") is True:
        out["duplicate_target"] = str(cert.get("conflict_target", ""))
        return verdict("escalated", "ESCALATE_OWNER_SEMANTICS")
    return verdict("accepted", "RESEARCH_ACCEPTABLE_OWNER_BULK_REVIEW")


def filter_file(root, incoming, outdir):
    inventory_sha, foundation_sha, occupied = load_baseline(root)
    with incoming.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh, delimiter="\t")
        if tuple(reader.fieldnames or ()) != COLUMNS:
            raise ValueError("INVALID_TSV_SCHEMA")
        items = list(reader)
    if any(None in item or any(v is None for v in item.values()) for item in items):
        raise ValueError("MALFORMED_TSV")
    ids = [r["candidate_id"] for r in items]
    if len(ids) != len(set(ids)) or not all(ids):
        raise ValueError("DUPLICATE_OR_MISSING_CANDIDATE_ID")
    buckets = {"accepted": [], "rejected": [], "escalated": []}
    for row in sorted(items, key=lambda r: r["candidate_id"]):
        result = evaluate(row, root, inventory_sha, foundation_sha, occupied)
        buckets[result["decision"]].append(result)
    outdir.mkdir(parents=True, exist_ok=True)
    for label, fname in (("accepted", "accepted-queue.tsv"), ("rejected", "rejected.tsv"), ("escalated", "escalated.tsv")):
        with (outdir / fname).open("w", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=COLUMNS, delimiter="\t", lineterminator="\n")
            writer.writeheader()
            writer.writerows(buckets[label])
    return {key: len(value) for key, value in buckets.items()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(filter_file(args.root.resolve(), args.input, args.output_dir), sort_keys=True))


if __name__ == "__main__":
    main()
