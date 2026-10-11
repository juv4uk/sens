#!/usr/bin/env python3
"""Fail-closed D10 three-way intake using separately verified evidence records.

This script does NOT execute donor code, attest to GitHub CI, or ratify D10.
Evidence producers must verify the source and replay witness independently;
unchecked PASS strings or dedup_check=NO-MATCH never count.
"""
import argparse
import csv
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

INPUT = ('candidate_id', 'semantic_name', 'semantic_law', 'donor_provenance',
         'witness_artifact', 'witness_result_ref', 'semantic_equivalence_certificate',
         'semantic_distinctness_certificate', 'requested_coordinate', 'source_refs')
OUTPUT = ('candidate_id', 'semantic_name', 'status', 'reason', 'donor_provenance',
          'witness_result_ref', 'semantic_proof_ref', 'duplicate_of',
          'conflict_target', 'coordinate', 'source_refs')
HEX = re.compile(r'^[0-9a-f]{64}$')
PIN = re.compile(r'@[0-9a-f]{40}(?::|/|$)')


class IntakeError(ValueError):
    pass


def read_json(path):
    value = json.loads(Path(path).read_text(encoding='utf-8'))
    if not isinstance(value, dict):
        raise IntakeError(f'Expected JSON object: {path}')
    return value


def checked_file(root, name, digest):
    if not isinstance(name, str) or not isinstance(digest, str) or not HEX.fullmatch(digest):
        return False
    base = Path(root).resolve()
    target = (base / name).resolve()
    if not target.is_relative_to(base) or not target.is_file():
        return False
    return hashlib.sha256(target.read_bytes()).hexdigest() == digest


def checked_proof(item, root):
    return (isinstance(item, dict) and item.get('verified') is True and
            checked_file(root, item.get('artifact'), item.get('sha256')))


def classify(row, record, root):
    record = record if isinstance(record, dict) else {}
    source = record.get('provenance', {})
    witness = record.get('witness', {})
    semantic = record.get('semantic', {})
    conflict = record.get('conflict', {})
    name = row['candidate_id']
    out = dict.fromkeys(OUTPUT, '')
    out.update(candidate_id=name, semantic_name=row['semantic_name'],
               donor_provenance=row['donor_provenance'],
               witness_result_ref=row['witness_result_ref'],
               coordinate='NONE', source_refs=row['source_refs'])

    def result(status, reason, proof='', duplicate='', target=''):
        out.update(status=status, reason=reason, semantic_proof_ref=proof,
                   duplicate_of=duplicate, conflict_target=target)
        return out

    # F1: a pinned source or immutable page with independently checked contents.
    provenance = row['donor_provenance']
    source_ref = source.get('source_ref') if isinstance(source, dict) else None
    is_pinned = PIN.search(provenance) or ('https://' in provenance and
                                         ('page=' in provenance or 'p=' in provenance))
    if (not is_pinned or not checked_proof(source, root) or
            source_ref != provenance or not source.get('content_sha256')):
        return result('EXCLUDE_NO_PROVENANCE', 'F1: source reference or verified source proof missing')

    # F2: replayed positive, negative and independent-oracle witness.
    if (not checked_proof(witness, root) or witness.get('source_ref') != provenance or
            witness.get('result') != 'PASS' or witness.get('exit_code') != 0 or
            witness.get('positive_pass') is not True or witness.get('negative_pass') is not True or
            witness.get('oracle_pass') is not True or not witness.get('run_url') or
            not witness.get('tool_version') or not witness.get('run_commit') or
            row['witness_result_ref'] != witness.get('artifact')):
        return result('EXCLUDE_NO_WITNESS', 'F2: independently replayed, SHA-pinned witness PASS not verified')

    # F3: a semantic proof, never a string/name match. Unknown is not a duplicate.
    if not checked_proof(semantic, root):
        return result('EXCLUDE_UNPROVEN_DISTINCTNESS', 'F3: semantic certificate not verified')
    proof = semantic['artifact']
    if semantic.get('classification') == 'duplicate':
        if semantic.get('duplicate_of') and semantic.get('bidirectional') is True:
            return result('EXCLUDE_DUP', 'F3: proven semantic duplicate', proof,
                          semantic['duplicate_of'])
        return result('EXCLUDE_UNPROVEN_DISTINCTNESS', 'F3: incomplete duplicate proof', proof)
    if (semantic.get('classification') != 'distinct' or
            semantic.get('counterexample_checked') is not True or
            semantic.get('lower_domain_review') is not True or
            semantic.get('current_d10_review') is not True):
        return result('EXCLUDE_UNPROVEN_DISTINCTNESS', 'F3: no proved independent law', proof)

    # F4: absence of conflict is also attested; arbitrary coordinates are rejected.
    if row['requested_coordinate'].strip().upper() not in ('', 'NONE', 'NULL'):
        return result('ESCALATE_OWNER', 'F4: proposed coordinate requires independent allocation',
                      proof, target=row['requested_coordinate'])
    if not checked_proof(conflict, root):
        return result('ESCALATE_OWNER', 'F4: conflict audit unavailable', proof)
    if conflict.get('status') == 'conflict':
        return result('ESCALATE_OWNER', 'F4: verified semantic/coordinate conflict',
                      proof, target=conflict.get('target', 'UNSPECIFIED'))
    if conflict.get('status') != 'none':
        return result('ESCALATE_OWNER', 'F4: conflict unresolved', proof)
    return result('ACCEPT_PENDING_BULK_APPROVAL', 'F1-F4 passed; not D10 ratification', proof)


def run(input_tsv, evidence_json, census_json, evidence_root, output_dir):
    with open(input_tsv, newline='', encoding='utf-8') as f:
        r = csv.DictReader(f, delimiter='\t', strict=True)
        if tuple(r.fieldnames or ()) != INPUT:
            raise IntakeError('Unexpected all-candidates.tsv columns')
        rows = list(r)
    names = [r['candidate_id'] for r in rows]
    if any(not x or not x.strip() for x in names) or len(names) != len(set(names)):
        raise IntakeError('Blank/duplicate candidate_id in input; refusing silent loss')
    for r in rows:
        if any(v is None for v in r.values()) or None in r:
            raise IntakeError(f'Ragged candidate row: {r.get("candidate_id")}')
    evidence = read_json(evidence_json)
    census = read_json(census_json)
    # Do not claim coverage from an input row count alone.
    coverage = (census.get('coverage_complete') is True and
                census.get('source_manifest_verified') is True and
                census.get('unreadable_sources') == 0 and
                census.get('candidate_count') == len(rows))
    parts = {'accepted-queue.tsv': [], 'rejected.tsv': [], 'escalated.tsv': []}
    for row in sorted(rows, key=lambda x: x['candidate_id']):
        x = classify(row, evidence.get(row['candidate_id']), evidence_root)
        if x['status'].startswith('ACCEPT_'):
            bucket = 'accepted-queue.tsv'
        elif x['status'].startswith('EXCLUDE_'):
            bucket = 'rejected.tsv'
        elif x['status'] == 'ESCALATE_OWNER':
            bucket = 'escalated.tsv'
        else:
            raise IntakeError('Unrecognized status ' + x['status'])
        parts[bucket].append(x)
    if sum(map(len, parts.values())) != len(rows):
        raise IntakeError('Input partition does not conserve rows')
    dest = Path(output_dir)
    dest.mkdir(parents=True, exist_ok=True)
    sha = {}
    for filename, items in parts.items():
        p = dest / filename
        with p.open('w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=OUTPUT, delimiter='\t', lineterminator='\n')
            writer.writeheader()
            writer.writerows(items)
        sha[filename] = hashlib.sha256(p.read_bytes()).hexdigest()
    reasons = dict(sorted(Counter(x['status'] for x in parts['rejected.tsv']).items()))
    summary = {'schema': 'd10-filter-intake/v1', 'coverage_complete': coverage,
               'bulk_ready': False,  # Requires independent replay/attestation outside this script.
               'rows': len(rows), 'accepted': len(parts['accepted-queue.tsv']),
               'rejected': len(parts['rejected.tsv']),
               'escalated': len(parts['escalated.tsv']),
               'rejected_by_reason': reasons,
               'sha256': sha, 'witness_replay_by_this_script': False,
               'note': 'Proof-manifest verifier is external; this partitioner does NOT execute witnesses or certify their origin.'}
    (dest / 'coverage-report.json').write_text(json.dumps(summary, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    return summary


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input', type=Path, required=True)
    p.add_argument('--evidence', type=Path, required=True)
    p.add_argument('--census', type=Path, required=True)
    p.add_argument('--evidence-root', type=Path, required=True)
    p.add_argument('--out-dir', type=Path, required=True)
    args = p.parse_args()
    try:
        report = run(args.input, args.evidence, args.census, args.evidence_root, args.out_dir)
    except (IntakeError, OSError, json.JSONDecodeError, csv.Error) as exc:
        print(f'D10_FILTER_BLOCKED: {exc}', file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0 if report['coverage_complete'] else 3


if __name__ == '__main__':
    sys.exit(main())
