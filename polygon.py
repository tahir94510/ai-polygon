"""Architecture-independent, CPU-friendly public benchmark. NOT a sandbox or blind test."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import random
import statistics
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parent
SEEDS = (11, 23, 37, 53, 71)
TRACKS = {
    'regression': {'name': 'Tabular regression', 'suites': ['linear', 'nonlinear', 'shift'],
                   'metric': 'rmse', 'direction': 'min', 'task': 'regression'},
    'classification': {'name': 'Binary classification', 'suites': ['linear', 'xor'],
                       'metric': 'accuracy', 'direction': 'max', 'task': 'classification'},
}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def project_hash(folder):
    h = hashlib.sha256()
    for file in sorted(folder.rglob('*')):
        if file.is_file() and '__pycache__' not in file.parts:
            h.update(file.relative_to(folder).as_posix().encode() + b'\0' + file.read_bytes() + b'\0')
    return h.hexdigest()


def projects():
    found = {}
    for file in sorted((ROOT / 'projects').glob('*/manifest.json')):
        data = json.loads(file.read_text())
        name = file.parent.name
        if data.get('track') not in TRACKS or data.get('origin') not in ('scratch', 'pretrained'):
            raise ValueError(f'Invalid track or origin in {file}')
        if not isinstance(data.get('name'), str) or not data['name'].strip():
            raise ValueError(f'Missing project name in {file}')
        for key in ('train', 'predict'):
            command = data.get(key)
            if not isinstance(command, list) or not command or not all(isinstance(s, str) and s for s in command):
                raise ValueError(f'Invalid {key} command in {file}')
            for part in command:
                import string
                for _, field, _, _ in string.Formatter().parse(part):
                    if field is not None and field not in {'train', 'model', 'input', 'output'}:
                        raise ValueError(f'Unsupported placeholder {field} in {file}')
        found[name] = data
    return found


def data_for(track, suite, seed):
    if track not in TRACKS or suite not in TRACKS[track]['suites']:
        raise ValueError('Unknown benchmark or suite')
    rng = random.Random(seed * (31 if track == 'regression' else 101) +
                        {'linear': 1, 'nonlinear': 2, 'shift': 3, 'xor': 2}[suite])
    dimension = 3 if track == 'regression' else 2
    weights = [rng.uniform(-1.7, 1.7) if dimension == 3 else rng.uniform(0.3, 1.5)
               for _ in range(dimension)]
    bias = rng.uniform(-0.7, 0.7) if dimension == 3 else rng.uniform(-0.25, 0.25)

    def generate(n, prefix):
        result = []
        for i in range(n):
            limit = 2.3 if suite == 'shift' and prefix == 'test' else 1.0
            x = [rng.uniform(-limit, limit) for _ in range(dimension)]
            if track == 'regression':
                y = bias + sum(a * b for a, b in zip(x, weights))
                if suite != 'linear':
                    y += .75 * x[0] * x[1] + .45 * x[2] ** 2
                y += rng.gauss(0, .035)
            else:
                y = int(((x[0] > 0) != (x[1] > 0)) if suite == 'xor'
                        else sum(a * b for a, b in zip(x, weights)) > bias)
            result.append({'id': f'{prefix}-{i}', 'x': x, 'y': y})
        return result
    return generate(240, 'train'), generate(80, 'validation'), generate(120, 'test')


def write_jsonl(path, rows):
    path.write_text(''.join(json.dumps(row, allow_nan=False, separators=(',', ':')) + '\n' for row in rows))


def checked_predictions(path, expected, task):
    if not path.is_file() or path.stat().st_size > 2_000_000:
        raise ValueError('Prediction file missing or too large')
    rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    wanted = {row['id'] for row in expected}
    if len(rows) != len(expected):
        raise ValueError('Prediction count differs from test count')
    got = {}
    for row in rows:
        if not isinstance(row, dict) or set(row) != {'id', 'prediction'}:
            raise ValueError('Each prediction needs exactly id and prediction')
        key, value = row['id'], row['prediction']
        if not isinstance(key, str) or key not in wanted or key in got:
            raise ValueError('Unknown or duplicate prediction ID')
        if type(value) not in (float, int) or not math.isfinite(value):
            raise ValueError('Prediction must be a finite number')
        if task == 'classification' and value not in (0, 1):
            raise ValueError('Classification predictions must be 0 or 1')
        got[key] = float(value)
    if set(got) != wanted:
        raise ValueError('Prediction IDs do not match test IDs')
    return got


def command(args, cwd, paths, timeout):
    import string
    argv = [part.format_map(paths) for part in args]
    if argv[0] in ('python', 'python3'):
        argv[0] = sys.executable
    env = {'PATH': os.environ.get('PATH', ''), 'HOME': os.environ.get('HOME', ''),
           'PYTHONHASHSEED': '0', 'PYTHONDONTWRITEBYTECODE': '1'}
    start = time.perf_counter()
    run = subprocess.run(argv, cwd=cwd, env=env, capture_output=True, text=True,
                         errors='replace', timeout=timeout)
    if run.returncode:
        raise RuntimeError(f'Command exited {run.returncode}: {run.stderr[-500:]}')
    return round(time.perf_counter() - start, 6)


def evaluate(name, suite, seed, timeout=30):
    manifest = projects()[name]
    track = manifest['track']
    train, _, test = data_for(track, suite, seed)
    folder = ROOT / 'projects' / name
    with tempfile.TemporaryDirectory(prefix='polygon-') as tmp:
        paths = {key: str(Path(tmp) / f'{key}.jsonl') for key in ('train', 'input', 'output')}
        paths['model'] = str(Path(tmp) / 'model.json')
        write_jsonl(Path(paths['train']), train)
        write_jsonl(Path(paths['input']), [{'id': r['id'], 'x': r['x']} for r in test])
        train_time = command(manifest['train'], folder, paths, timeout)
        model = Path(paths['model'])
        if not model.is_file() or model.stat().st_size > 2_000_000:
            raise ValueError('Model artifact missing or too large')
        predict_time = command(manifest['predict'], folder, paths, timeout)
        guesses = checked_predictions(Path(paths['output']), test, TRACKS[track]['task'])
        if track == 'regression':
            errors = [guesses[r['id']] - r['y'] for r in test]
            metrics = {'rmse': math.sqrt(statistics.fmean(v*v for v in errors)),
                       'mae': statistics.fmean(abs(v) for v in errors)}
        else:
            metrics = {'accuracy': statistics.fmean(guesses[r['id']] == r['y'] for r in test)}
        return {'project': name, 'track': track, 'suite': suite, 'seed': seed,
                'status': 'completed', 'metrics': metrics,
                'duration_seconds': {'train': train_time, 'predict': predict_time},
                'model_bytes': model.stat().st_size,
                'evidence': {'project_sha256': project_hash(folder),
                             'train_sha256': digest(Path(paths['train']).read_bytes()),
                             'test_inputs_sha256': digest(Path(paths['input']).read_bytes()),
                             'predictions_sha256': digest(Path(paths['output']).read_bytes())}}


def report(seeds=SEEDS, timeout=30):
    records = []
    for name, manifest in projects().items():
        for suite in TRACKS[manifest['track']]['suites']:
            for seed in seeds:
                try:
                    row = evaluate(name, suite, seed, timeout)
                except (Exception, subprocess.TimeoutExpired) as error:
                    row = {'project': name, 'track': manifest['track'], 'suite': suite,
                           'seed': seed, 'status': 'failed', 'error': str(error)[:500]}
                records.append(row)
    groups = {}
    for row in records:
        if row['status'] == 'completed':
            groups.setdefault((row['track'], row['suite'], row['project']), []).append(row)
    summary = []
    for (track, suite, project), rows in sorted(groups.items()):
        metric = TRACKS[track]['metric']
        vals = [row['metrics'][metric] for row in rows]
        summary.append({'track': track, 'suite': suite, 'project': project, 'n': len(rows),
                        'metric': metric, 'mean': statistics.fmean(vals),
                        'min': min(vals), 'max': max(vals)})
    return {'schema': 'polygon-public-demo-v1', 'evaluation': 'public_not_blind',
            'seeds': list(seeds), 'records': records, 'summary': summary}


def main():
    parser = argparse.ArgumentParser(description='AI Polygon public benchmark, not a secure sandbox')
    sub = parser.add_subparsers(dest='action', required=True)
    sub.add_parser('list')
    one = sub.add_parser('evaluate'); one.add_argument('project'); one.add_argument('suite')
    one.add_argument('--seed', type=int, default=11)
    all_ = sub.add_parser('run-all'); all_.add_argument('--output', default='results/local.json')
    args = parser.parse_args()
    if args.action == 'list':
        print(json.dumps({'tracks': TRACKS, 'projects': projects()}, indent=2))
    elif args.action == 'evaluate':
        print(json.dumps(evaluate(args.project, args.suite, args.seed), indent=2))
    else:
        output = ROOT / args.output
        output.parent.mkdir(parents=True, exist_ok=True)
        value = report()
        output.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')
        failed = sum(r['status'] == 'failed' for r in value['records'])
        print(f'{len(value["records"])} trials; {failed} failures; saved {output}')
        return int(failed > 0)
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
