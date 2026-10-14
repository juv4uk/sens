#!/usr/bin/env python3
"""CI_GLUE_NO_SEMANTICS: fail-closed SENS publication transaction.

This is NOT a Zig semantic oracle. A pinned Zig-backed CLI owns T5 bytes;
actual SENS execution separately supplies a pinned, expected output receipt.
Era/provenance stays OUTSIDE Zig. Neither physical parity nor a caller-provided
expected hash alone can authenticate a historical migration.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

BACKEND = re.compile(r"\Atransport=zig abi=[1-9][0-9]* semantic_authority=SENS\n?\Z")
HEX256 = re.compile(r"\A[0-9a-f]{64}\Z")


class PublicationRejected(Exception):
    pass


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def require_digest(name: str, value: object) -> str:
    if not isinstance(value, str) or not HEX256.fullmatch(value):
        raise PublicationRejected(f"{name}: expected lowercase 64-hex SHA256")
    return value


def run(executable: Path, *arguments: Path | str, timeout: int = 15) -> bytes:
    try:
        proc = subprocess.run(
            [str(executable), *(str(a) for a in arguments)],
            stdin=subprocess.DEVNULL, capture_output=True, timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise PublicationRejected(f"{executable.name}: unavailable or timeout: {exc}") from exc
    if proc.returncode != 0:
        raise PublicationRejected(
            f"{executable.name}: rejected (exit={proc.returncode}); "
            f"stderr_sha256={sha(proc.stderr)}; stderr={proc.stderr[:240]!r}"
        )
    return proc.stdout


def check_executable(path: Path, pinned: str, name: str) -> str:
    if not path.is_file() or path.is_symlink() or not os.access(path, os.X_OK):
        raise PublicationRejected(f"{name}: regular executable required")
    actual = sha(path.read_bytes())
    if actual != require_digest(name + '_sha256', pinned):
        raise PublicationRejected(f"{name}: executable SHA256 mismatch {actual}")
    return actual


def verify_and_publish(args: argparse.Namespace) -> dict:
    source = args.input.resolve(strict=True)
    original = source.read_bytes()
    if source.suffix != '.sens' or not original:
        raise PublicationRejected('input must be a nonempty physical .sens file')
    # A self-declared era or self-consistent hashes do not authenticate
    # provenance. The SHA approval pin MUST arrive from outside this manifest
    # (e.g. an owner-controlled release decision / protected CI input).
    # This is an integrity trust anchor, NOT signature verification.
    provenance_snapshot = args.provenance.read_bytes()
    approved = require_digest(
        'owner_approved_provenance_sha256',
        getattr(args, 'owner_approved_provenance_sha256', None),
    )
    if sha(provenance_snapshot) != approved:
        raise PublicationRejected('owner approval pin differs from provenance SHA256')
    if provenance_snapshot != getattr(args, '_provenance_snapshot', None):
        raise PublicationRejected('provenance changed since publication request')
    provenance = json.loads(provenance_snapshot)
    if not isinstance(provenance, dict) or provenance.get('schema') != 'sens-publication-provenance/v1':
        raise PublicationRejected('provenance: schema sens-publication-provenance/v1 required')
    if provenance.get('source_era') not in ('current', 'legacy'):
        raise PublicationRejected('provenance: explicit current/legacy era required, never auto')
    source_file = args.source_file.resolve(strict=True)
    source_snapshot = source_file.read_bytes()
    if sha(source_snapshot) != require_digest('source_sha256', provenance.get('source_sha256')):
        raise PublicationRejected('original source differs from provenance SHA256')
    if sha(original) != require_digest('physical_sha256', provenance.get('physical_sha256')):
        raise PublicationRejected('input differs from provenance physical SHA256')

    # Historical translation is permitted ONLY with a separately stored,
    # pinned and content-bound external translation receipt. Neither Zig
    # nor the publisher is allowed to infer an era from equal physical bits.
    translation_path = None
    translation_snapshot = None
    translation = None
    if provenance['source_era'] == 'legacy':
        item = provenance.get('translation_receipt')
        if not isinstance(item, dict) or not isinstance(item.get('path'), str):
            raise PublicationRejected('legacy source requires separate translation receipt')
        translation_path = Path(item['path'])
        if (not translation_path.is_absolute() or translation_path.is_symlink()
                or not translation_path.is_file()):
            raise PublicationRejected('translation receipt must be an absolute regular file')
        if translation_path.stat().st_size > 1024 * 1024:
            raise PublicationRejected('translation receipt too large')
        translation_snapshot = translation_path.read_bytes()
        if sha(translation_snapshot) != require_digest('translation_receipt_sha256', item.get('sha256')):
            raise PublicationRejected('translation receipt SHA256 mismatch')
        translation = json.loads(translation_snapshot)
        if (not isinstance(translation, dict)
                or translation.get('schema') != 'sens-translation-receipt/v1'
                or translation.get('source_era') != 'legacy'
                or translation.get('source_sha256') != provenance['source_sha256']
                or translation.get('physical_sha256') != provenance['physical_sha256']):
            raise PublicationRejected('translation receipt does not bind legacy source and physical candidate')
        require_digest('canonical_source_sha256', translation.get('canonical_source_sha256'))

    runner = args.zig_runner.resolve(strict=True)
    executor = args.sens_executor.resolve(strict=True)
    zig_hash = check_executable(runner, args.zig_runner_sha256, 'zig_runner')
    sens_hash = check_executable(executor, args.sens_executor_sha256, 'sens_executor')
    expected = require_digest('expected_output_sha256', args.expected_output_sha256)
    if not BACKEND.fullmatch(run(runner, 'backend').decode('ascii', errors='replace')):
        raise PublicationRejected('physical runner is not explicitly Zig-backed')

    with tempfile.TemporaryDirectory(prefix='sens-sterile-publication-') as td:
        root = Path(td)
        candidate = root / 'input' / 'candidate.sens'
        candidate.parent.mkdir()
        candidate.write_bytes(original)
        # Zig physical decoding, then SENS-owned D2 canonical admission.
        visible = run(runner, 'open', candidate)
        if not visible or not visible.endswith(b'\n'):
            raise PublicationRejected('Zig physical decode / SENS D2 reader returned no canonical words')
        try:
            canonical = visible.decode('ascii')
        except UnicodeDecodeError as exc:
            raise PublicationRejected('canonical SENS projection was not binary ASCII') from exc
        if not re.fullmatch(r'[01]+(?: [01]+)*\n', canonical):
            raise PublicationRejected('noncanonical visible SENS projection')
        if (translation is not None
                and sha(visible) != translation['canonical_source_sha256']):
            raise PublicationRejected('translation receipt canonical-source SHA256 mismatch')
        witness = root / 'cycle' / 'candidate.lisp'
        witness.parent.mkdir()
        witness.write_bytes(visible)
        # Zig, not Rust, must physically encode the admitted source words.
        run(runner, 'encode', witness)
        replay_path = witness.with_suffix('.sens')
        if not replay_path.is_file():
            raise PublicationRejected('Zig CLI did not create the physical replay')
        replay = replay_path.read_bytes()
        if replay != original:
            first = next((i for i, (x, y) in enumerate(zip(original, replay)) if x != y),
                         min(len(original), len(replay)))
            raise PublicationRejected(
                f'physical roundtrip mismatch first_byte={first} '
                f'input_sha256={sha(original)} replay_sha256={sha(replay)}'
            )
        # Actual SENS execution and pinned owner-approved expected stdout;
        # Python and Zig do NOT decide domain truth/callability.
        output = run(executor, candidate)
        actual_output = sha(output)
        if actual_output != expected:
            raise PublicationRejected(
                f'SENS native verdict mismatch expected_sha256={expected} '
                f'actual_sha256={actual_output}'
            )
        if source_file.read_bytes() != source_snapshot:
            raise PublicationRejected('original source changed during verification')
        if sha(runner.read_bytes()) != zig_hash or sha(executor.read_bytes()) != sens_hash:
            raise PublicationRejected('pinned executable changed during verification')
        if source.read_bytes() != original:
            raise PublicationRejected('source changed during verification')
        if args.provenance.read_bytes() != provenance_snapshot:
            raise PublicationRejected('provenance changed during verification')
        if (translation_path is not None
                and (translation_path.is_symlink()
                     or translation_path.read_bytes() != translation_snapshot)):
            raise PublicationRejected('translation receipt changed during verification')
        if sha(provenance_snapshot) != approved:
            raise PublicationRejected('owner approval pin changed during verification')

    destination = args.out.absolute()
    if destination.suffix != '.sens' or destination == source:
        raise PublicationRejected('publication destination must be a separate .sens file')
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() or destination.is_symlink():
        raise PublicationRejected('publication destination exists, no overwrite')
    fd, staged_name = tempfile.mkstemp(prefix='.sens-sterile-', dir=destination.parent)
    staged = Path(staged_name)
    try:
        with os.fdopen(fd, 'wb') as handle:
            handle.write(original)
            handle.flush()
            os.fsync(handle.fileno())
        # Atomic no-replace publication: all negative cases leave no output.
        os.link(staged, destination)
    finally:
        staged.unlink(missing_ok=True)
    return {
        'schema': 'sens-sterile-publication-receipt/v1',
        'source_era': provenance['source_era'],
        'owner_approved_provenance_sha256': approved,
        'translation_receipt_sha256': sha(translation_snapshot) if translation_snapshot is not None else None,
        'source_sha256': provenance['source_sha256'],
        'physical_sha256': sha(original),
        'replayed_sha256': sha(original),
        'zig_runner_sha256': zig_hash,
        'sens_executor_sha256': sens_hash,
        'sens_output_sha256': actual_output,
        'physical': 'PASS',
        'native_sens_execution': 'PASS',
        'note': 'Pinned executors/output, not cryptographic provenance authentication',
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--input', type=Path, required=True)
    ap.add_argument('--source-file', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--provenance', type=Path, required=True)
    ap.add_argument('--owner-approved-provenance-sha256', required=True,
                    help='independent owner-controlled SHA256 pin for complete provenance JSON')
    ap.add_argument('--zig-runner', type=Path, required=True)
    ap.add_argument('--zig-runner-sha256', required=True)
    ap.add_argument('--sens-executor', type=Path, required=True)
    ap.add_argument('--sens-executor-sha256', required=True)
    ap.add_argument('--expected-output-sha256', required=True)
    ap.add_argument('--receipt', type=Path)
    args = ap.parse_args()
    try:
        args._provenance_snapshot = args.provenance.read_bytes()
        receipt = verify_and_publish(args)
        if args.receipt is not None:
            receipt_created = False
            try:
                args.receipt.parent.mkdir(parents=True, exist_ok=True)
                fd = os.open(args.receipt, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
                receipt_created = True
                with os.fdopen(fd, 'w', encoding='utf-8') as handle:
                    handle.write(json.dumps(receipt, sort_keys=True, indent=2) + '\n')
                    handle.flush()
                    os.fsync(handle.fileno())
            except OSError:
                args.out.unlink(missing_ok=True)
                if receipt_created:
                    args.receipt.unlink(missing_ok=True)
                raise
    except (PublicationRejected, OSError, ValueError, json.JSONDecodeError) as exc:
        print('SENS_STERILE_PUBLICATION_REJECT: ' + str(exc), file=sys.stderr)
        return 1
    print('SENS_STERILE_PUBLICATION_PASS ' + json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
