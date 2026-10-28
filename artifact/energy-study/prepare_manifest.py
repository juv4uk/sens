#!/usr/bin/env python3
"""Package existing ENERGY-06 evidence; never synthesize observations or claim reproduction."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile

from validate_manifest import (
    DIGEST, MAX_BYTES, REQUIRED_FILES, SCHEMA, SHA, InvalidArtifact, demand,
    load_json, verify,
)


def prepare(directory: Path, expected_sha: str) -> dict:
    """Create manifest.json exactly once, but only after full integrity validation."""
    demand(isinstance(expected_sha, str) and SHA.fullmatch(expected_sha) is not None,
           "expected Git SHA must be exactly 40 lowercase hex digits")
    demand(directory.is_dir() and not directory.is_symlink(),
           "evidence directory missing or linked")
    root = directory.resolve()
    destination = root / "manifest.json"
    demand(not os.path.lexists(destination), "manifest already exists; do not overwrite")

    provenance_file = root / REQUIRED_FILES["provenance"]
    demand(provenance_file.is_file() and not provenance_file.is_symlink(),
           "missing or linked provenance")
    provenance = load_json(provenance_file)
    demand(isinstance(provenance, dict) and provenance.get("git_sha") == expected_sha,
           "provenance Git SHA differs from expected source SHA")
    sensor = provenance.get("energy_sensor")
    demand(sensor in ("RAPL_AVAILABLE", "RAPL_UNAVAILABLE", "MULTIPLE_RAPL_PACKAGES"),
           "unrecognized energy sensor provenance")
    status = "MEASURED" if sensor == "RAPL_AVAILABLE" else "ENERGY_NOT_MEASURED"

    files = {}
    for key, filename in REQUIRED_FILES.items():
        path = root / filename
        demand(path.is_file() and not path.is_symlink()
               and path.resolve().parent == root,
               f"missing, linked or escaping evidence {key}")
        size = path.stat().st_size
        demand(0 < size <= MAX_BYTES, f"empty or oversized evidence {key}")
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        files[key] = {"path": filename, "sha256": digest}

    manifest = {
        "schema": SCHEMA,
        "source_sha": expected_sha,
        "energy_status": status,
        "independent_reproduction": "NOT_REPRODUCED",
        "files": files,
    }
    encoded = (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8")

    # Verify in-place using the real validator. If validation fails, do not
    # leave a plausible-looking manifest in the evidence package.
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=root, prefix=".manifest-check-",
                                         suffix=".json", delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(encoded)
        verified = verify(temporary)
        demand(verified["source_sha"] == expected_sha and
               verified["energy_status"] == status,
               "verifier returned inconsistent evidence")
        # An exclusive hard link is atomic and cannot replace another writer's
        # manifest. A filesystem that disallows hard links fails closed.
        os.link(temporary, destination)
        try:
            verify(destination)
        except (InvalidArtifact, OSError):
            destination.unlink()
            raise
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return verified


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("evidence_dir", type=Path)
    parser.add_argument("--expected-sha", required=True,
                        help="40-hex commit SHA recorded before the experiment")
    args = parser.parse_args()
    try:
        result = prepare(args.evidence_dir, args.expected_sha)
    except (InvalidArtifact, OSError) as exc:
        print(f"ARTIFACT_PACKAGING_BLOCKED reason={exc}", file=sys.stderr)
        return 2
    print("ARTIFACT_PACKAGED=PASS "
          f"sha={result['source_sha']} samples={result['raw_samples']} "
          f"energy={result['energy_status']} "
          "independent_reproduction=NOT_REPRODUCED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
