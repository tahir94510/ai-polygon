"""Check a fresh full run against a compact, committed 80-trial reference."""
import hashlib
import json
import math
import sys
from pathlib import Path


def fingerprint(rows):
    evidence = [
        {'project':r['project'],'track':r['track'],'suite':r['suite'],
         'seed':r['seed'],'evidence':r['evidence']}
        for r in sorted(rows, key=lambda r:r['seed'])
    ]
    return hashlib.sha256(json.dumps(evidence, sort_keys=True, separators=(',',':')).encode()).hexdigest()


def verify(actual, baseline):
    if (actual['schema'], actual['evaluation'], actual['seeds']) != (baseline['schema'], baseline['evaluation'], baseline['seeds']):
        raise AssertionError('Report schema, protocol or seeds changed')
    rows = actual['records']
    if len(rows) != baseline['trials'] or any(r['status'] != 'completed' for r in rows):
        raise AssertionError('Missing or failed trials')
    keys = {(r['project'],r['track'],r['suite'],r['seed']) for r in rows}
    if len(keys) != len(rows):
        raise AssertionError('Duplicated trial')
    actual_summary = {(r['track'],r['suite'],r['project']):r for r in actual['summary']}
    if set(actual_summary) != {(r['track'],r['suite'],r['project']) for r in baseline['summary']}:
        raise AssertionError('Unexpected or missing project suite')
    for ref in baseline['summary']:
        key = (ref['track'],ref['suite'],ref['project'])
        entry = actual_summary[key]
        group = [row for row in rows if (row['track'],row['suite'],row['project']) == key]
        if entry['n'] != ref['n'] or fingerprint(group) != ref['proof_sha256']:
            raise AssertionError(f'Count or provenance mismatch: {key}')
        for field in ('mean','min','max'):
            if not math.isclose(entry[field],ref[field],rel_tol=1e-9,abs_tol=1e-9):
                raise AssertionError(f'Metric mismatch: {key}, {field}')
    print(f'REPRODUCED {len(rows)} trials: score summaries and provenance fingerprints match.')

if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('Usage: python scripts/check_reference.py results/local-ci.json')
    verify(json.loads(Path(sys.argv[1]).read_text()),json.loads(Path('results/reference-demo.json').read_text()))
