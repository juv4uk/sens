#!/usr/bin/env python3
"""Доказове представлення STORE -> AIR -> LOAD для #3580/#3595.

Принцип:
- STORE рахує канонічні semantic bits і окремо фізичний byte container;
- AIR рахує carrier bits, не виводить їх автоматично з кількості байтів;
- LOAD-поля присутні в спільній схемі, але лишаються null, доки #3513 не
  надасть фазово ізольовані I-ref виміри.

Парні English/canonical fixtures спочатку мають довести однаковий lowered
semantic trace чинним exact-domain helper-ом. Mechanical fixtures явно
позначені як carrier controls і не претендують на мовну семантичну рівність.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import subprocess
import tempfile
from pathlib import Path

SCHEMA = "sens-store-air-load/v1"
FIXTURE_SCHEMA = "sens-store-air-load-fixtures/v1"
REPO = "juv4uk/sens"
PACKING_EXAMPLE = "store_air_load_repr"
SEMANTIC_EXAMPLE = "current_en_vs_d1d8_cpu"
SHA40_RE = re.compile(r"^[0-9a-f]{40}$")
CONTRACT_RE = re.compile(
    r"\(\(major\s+\.\s+#d(?P<major>[0-9]+)\)\s+\(minor\s+\.\s+(?P<minor>[0-9]+)\)"
)


def run_text(command: list[str], *, cwd: Path | None = None) -> str:
    return subprocess.check_output(
        command, cwd=cwd, text=True, stderr=subprocess.STDOUT
    ).strip()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_kv(stdout: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for raw in stdout.splitlines():
        if "=" not in raw:
            continue
        key, value = raw.split("=", 1)
        fields[key.strip()] = value.strip()
    return fields


def decode_hex(value: str) -> str:
    return bytes.fromhex(value).decode("utf-8")


def git_sha(repo: Path) -> str:
    value = run_text(["git", "rev-parse", "HEAD"], cwd=repo)
    if not SHA40_RE.fullmatch(value):
        raise ValueError(f"invalid git SHA: {value!r}")
    return value


def contract_version(repo: Path) -> str:
    text = (repo / "language-contract.lisp").read_text(encoding="utf-8")
    match = CONTRACT_RE.search(text)
    if match is None:
        raise ValueError("cannot read major/minor from language-contract.lisp")
    return f"{match.group('major')}.{match.group('minor')}"


def helper_path(repo: Path, name: str) -> Path:
    suffix = ".exe" if os.name == "nt" else ""
    return repo / "target" / "release" / "examples" / f"{name}{suffix}"


def build_helpers(repo: Path) -> tuple[Path, Path]:
    subprocess.run(
        [
            "cargo",
            "build",
            "--release",
            "-p",
            "sens",
            "--example",
            PACKING_EXAMPLE,
            "--example",
            SEMANTIC_EXAMPLE,
        ],
        cwd=repo,
        check=True,
    )
    packing = helper_path(repo, PACKING_EXAMPLE)
    semantic = helper_path(repo, SEMANTIC_EXAMPLE)
    if not packing.is_file() or not semantic.is_file():
        raise FileNotFoundError("expected release benchmark helpers were not built")
    return packing, semantic


def load_fixtures(path: Path) -> list[dict[str, object]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema") != FIXTURE_SCHEMA:
        raise ValueError(f"fixture schema must be {FIXTURE_SCHEMA}")
    fixtures = data.get("fixtures")
    if not isinstance(fixtures, list) or not fixtures:
        raise ValueError("fixtures must be a non-empty list")

    seen: set[str] = set()
    for fixture in fixtures:
        if not isinstance(fixture, dict):
            raise ValueError("every fixture must be an object")
        fixture_id = fixture.get("id")
        if not isinstance(fixture_id, str) or not fixture_id:
            raise ValueError("every fixture needs a non-empty id")
        if fixture_id in seen:
            raise ValueError(f"duplicate fixture id: {fixture_id}")
        seen.add(fixture_id)

        kind = fixture.get("kind")
        if kind not in {"mechanical", "paired-program"}:
            raise ValueError(f"{fixture_id}: unknown kind {kind!r}")
        canonical = fixture.get("canonical_source")
        if not isinstance(canonical, str) or not canonical.strip():
            raise ValueError(f"{fixture_id}: canonical_source is required")
        if kind == "paired-program":
            english = fixture.get("english_source")
            if not isinstance(english, str) or not english:
                raise ValueError(f"{fixture_id}: paired fixture needs english_source")

    return fixtures


def normalized_exact_words(source: str) -> str:
    words = source.split()
    if not words:
        raise ValueError("canonical source is empty")
    normalized: list[str] = []
    for word in words:
        if not (1 <= len(word) <= 8) or any(bit not in "01" for bit in word):
            raise ValueError(f"invalid exact-width word: {word!r}")
        normalized.append(f"{len(word)}:{word}")
    return "|".join(normalized)


def write_source(tmp: Path, fixture_id: str, suffix: str, source: str) -> Path:
    path = tmp / f"{fixture_id}.{suffix}.lisp"
    path.write_text(source, encoding="utf-8")
    return path


def packing_facts(
    helper: Path, source_path: Path, framing_bits: int
) -> dict[str, int | float]:
    stdout = run_text([str(helper), str(source_path), str(framing_bits)])
    fields = parse_kv(stdout)
    required = {
        "SEMANTIC_WORD_COUNT",
        "SEMANTIC_PAYLOAD_BITS",
        "FRAMING_BITS",
        "TAIL_UNUSED_BITS",
        "BYTE_CONTAINER_TOTAL_BITS",
        "PHYSICAL_CONTAINER_BYTES",
        "PAYLOAD_UTILIZATION",
    }
    missing = sorted(required - fields.keys())
    if missing:
        raise ValueError(f"packing helper missing fields: {missing}")

    return {
        "semantic_word_count": int(fields["SEMANTIC_WORD_COUNT"]),
        "semantic_payload_bits": int(fields["SEMANTIC_PAYLOAD_BITS"]),
        "framing_bits": int(fields["FRAMING_BITS"]),
        "tail_unused_bits": int(fields["TAIL_UNUSED_BITS"]),
        "byte_container_total_bits": int(fields["BYTE_CONTAINER_TOTAL_BITS"]),
        "physical_container_bytes": int(fields["PHYSICAL_CONTAINER_BYTES"]),
        "payload_utilization": float(fields["PAYLOAD_UTILIZATION"]),
    }


def semantic_preflight(
    helper: Path,
    english_path: Path,
    canonical_path: Path,
    *,
    expected_value: object,
    expected_output: object,
) -> str:
    observed: dict[str, dict[str, str]] = {}
    for candidate, path in (
        ("english-surface", english_path),
        ("canonical-d1d8", canonical_path),
    ):
        stdout = run_text([str(helper), candidate, "preflight", str(path)])
        fields = parse_kv(stdout)
        required = {"TRACE_HEX", "VALUE_HEX", "OUTPUT_HEX"}
        missing = sorted(required - fields.keys())
        if missing:
            raise ValueError(f"semantic helper missing fields: {missing}")
        observed[candidate] = {
            "trace": decode_hex(fields["TRACE_HEX"]),
            "value": decode_hex(fields["VALUE_HEX"]),
            "output": decode_hex(fields["OUTPUT_HEX"]),
        }

    left = observed["english-surface"]
    right = observed["canonical-d1d8"]
    for field in ("trace", "value", "output"):
        if left[field] != right[field]:
            raise ValueError(
                f"paired preflight mismatch for {field}: "
                f"english={left[field]!r} canonical={right[field]!r}"
            )

    if expected_value is not None and left["value"] != expected_value:
        raise ValueError(
            f"expected value mismatch: expected={expected_value!r} got={left['value']!r}"
        )
    if expected_output is not None and left["output"] != expected_output:
        raise ValueError(
            f"expected output mismatch: expected={expected_output!r} got={left['output']!r}"
        )

    return left["trace"]


def nullable_load_metrics() -> dict[str, None]:
    return {
        "decode_i_refs": None,
        "parse_i_refs": None,
        "lower_i_refs": None,
        "ready_i_refs": None,
        "cold_total_i_refs": None,
        "warm_incremental_i_refs": None,
    }


def make_row(
    *,
    fixture_id: str,
    fixture_kind: str,
    representation: str,
    current_git_sha: str,
    current_contract: str,
    semantic_identity_digest: str,
    identity_proof: str,
    semantic_payload_bits: int,
    framing_bits: int,
    tail_unused_bits: int,
    carrier_mode: str,
    carrier_payload_bits: int,
    storage_container_bits: int,
    physical_container_bytes: int,
    text_surface_bytes: int | None,
    packed_vs_text_ratio: float | None,
    bitrate_bps: float,
    provenance: dict[str, object],
) -> dict[str, object]:
    total_wire_bits = carrier_payload_bits + framing_bits
    return {
        "schema": SCHEMA,
        "fixture_id": fixture_id,
        "fixture_kind": fixture_kind,
        "representation": representation,
        "repo": REPO,
        "git_sha": current_git_sha,
        "contract_version": current_contract,
        "semantic_identity_digest": semantic_identity_digest,
        "identity_proof": identity_proof,
        "semantic_payload_bits": semantic_payload_bits,
        "framing_bits": framing_bits,
        "tail_unused_bits": tail_unused_bits,
        "carrier_mode": carrier_mode,
        "carrier_payload_bits": carrier_payload_bits,
        "storage_container_bits": storage_container_bits,
        "total_wire_bits": total_wire_bits,
        "physical_container_bytes": physical_container_bytes,
        "text_surface_bytes": text_surface_bytes,
        "packed_vs_text_ratio": packed_vs_text_ratio,
        "bitrate_bps": bitrate_bps,
        "ideal_airtime_seconds": total_wire_bits / bitrate_bps,
        **nullable_load_metrics(),
        "provenance": provenance,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--fixtures",
        type=Path,
        default=Path(__file__).with_name("fixtures.json"),
    )
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--bitrate-bps", type=float, default=2.0)
    parser.add_argument("--packing-helper", type=Path)
    parser.add_argument("--semantic-helper", type=Path)
    args = parser.parse_args()

    if args.bitrate_bps <= 0:
        raise ValueError("--bitrate-bps must be > 0")

    repo = Path(__file__).resolve().parents[2]
    fixtures = load_fixtures(args.fixtures.resolve())
    current_git_sha = git_sha(repo)
    current_contract = contract_version(repo)

    if args.packing_helper and args.semantic_helper:
        packing_helper = args.packing_helper.resolve()
        semantic_helper = args.semantic_helper.resolve()
    elif args.packing_helper or args.semantic_helper:
        raise ValueError("supply both --packing-helper and --semantic-helper, or neither")
    else:
        packing_helper, semantic_helper = build_helpers(repo)

    for helper in (packing_helper, semantic_helper):
        if not helper.is_file():
            raise FileNotFoundError(helper)

    common_provenance = {
        "runner": "store-air-load/v1",
        "python": platform.python_version(),
        "platform": platform.platform(),
        "packing_helper_sha256": sha256_file(packing_helper),
        "semantic_helper_sha256": sha256_file(semantic_helper),
        "fixtures_sha256": sha256_file(args.fixtures.resolve()),
        "airtime_model": "carrier_payload_bits + framing_bits",
        "load_metrics_status": "deferred-to-#3513",
    }

    rows: list[dict[str, object]] = []
    with tempfile.TemporaryDirectory(prefix="sens-store-air-load-") as tmp_name:
        tmp = Path(tmp_name)
        for fixture in fixtures:
            fixture_id = str(fixture["id"])
            fixture_kind = str(fixture["kind"])
            canonical_source = str(fixture["canonical_source"])
            framing_bits = int(fixture.get("framing_bits", 0))
            if framing_bits < 0:
                raise ValueError(f"{fixture_id}: framing_bits must be >= 0")

            canonical_path = write_source(
                tmp, fixture_id, "canonical", canonical_source
            )
            facts = packing_facts(packing_helper, canonical_path, framing_bits)

            semantic_bits = int(facts["semantic_payload_bits"])
            packed_bytes = int(facts["physical_container_bytes"])
            storage_bits = packed_bytes * 8
            if storage_bits - semantic_bits != int(facts["tail_unused_bits"]):
                raise ValueError(f"{fixture_id}: tail accounting mismatch")
            if storage_bits + framing_bits != int(facts["byte_container_total_bits"]):
                raise ValueError(f"{fixture_id}: byte-container accounting mismatch")

            english_source = fixture.get("english_source")
            if fixture_kind == "paired-program":
                assert isinstance(english_source, str)
                english_path = write_source(
                    tmp, fixture_id, "english", english_source
                )
                trace = semantic_preflight(
                    semantic_helper,
                    english_path,
                    canonical_path,
                    expected_value=fixture.get("expected_value"),
                    expected_output=fixture.get("expected_output"),
                )
                identity_proof = "paired-lowered-trace"
                identity_digest = sha256_bytes(trace.encode("utf-8"))
                text_bytes = len(english_source.encode("utf-8"))
                ratio = text_bytes / packed_bytes
            else:
                identity_proof = "mechanical-exact-word-sequence"
                identity_digest = sha256_bytes(
                    normalized_exact_words(canonical_source).encode("ascii")
                )
                text_bytes = None
                ratio = None

            per_fixture_provenance = {
                **common_provenance,
                "canonical_source_sha256": sha256_bytes(
                    canonical_source.encode("utf-8")
                ),
                "semantic_word_count": int(facts["semantic_word_count"]),
                "byte_container_total_bits": int(facts["byte_container_total_bits"]),
                "byte_container_payload_utilization": float(
                    facts["payload_utilization"]
                ),
            }

            rows.append(
                make_row(
                    fixture_id=fixture_id,
                    fixture_kind=fixture_kind,
                    representation="canonical-packed",
                    current_git_sha=current_git_sha,
                    current_contract=current_contract,
                    semantic_identity_digest=identity_digest,
                    identity_proof=identity_proof,
                    semantic_payload_bits=semantic_bits,
                    framing_bits=framing_bits,
                    tail_unused_bits=int(facts["tail_unused_bits"]),
                    carrier_mode="exact-bitstream",
                    carrier_payload_bits=semantic_bits,
                    storage_container_bits=storage_bits,
                    physical_container_bytes=packed_bytes,
                    text_surface_bytes=text_bytes,
                    packed_vs_text_ratio=ratio,
                    bitrate_bps=args.bitrate_bps,
                    provenance=per_fixture_provenance,
                )
            )

            if text_bytes is not None:
                rows.append(
                    make_row(
                        fixture_id=fixture_id,
                        fixture_kind=fixture_kind,
                        representation="text-surface",
                        current_git_sha=current_git_sha,
                        current_contract=current_contract,
                        semantic_identity_digest=identity_digest,
                        identity_proof=identity_proof,
                        semantic_payload_bits=semantic_bits,
                        framing_bits=0,
                        tail_unused_bits=0,
                        carrier_mode="text-bytes",
                        carrier_payload_bits=text_bytes * 8,
                        storage_container_bits=text_bytes * 8,
                        physical_container_bytes=text_bytes,
                        text_surface_bytes=text_bytes,
                        packed_vs_text_ratio=ratio,
                        bitrate_bps=args.bitrate_bps,
                        provenance=per_fixture_provenance,
                    )
                )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")

    print(
        f"wrote {len(rows)} STORE/AIR rows for {len(fixtures)} fixtures "
        f"at {args.bitrate_bps:g} bit/s -> {args.out}"
    )
    print("LOAD I-ref fields are explicit null until #3513 supplies phase evidence")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as exc:
        print(f"ERROR: {exc}", file=os.sys.stderr)
        raise SystemExit(2)
