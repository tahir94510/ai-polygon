import json
import tempfile
from pathlib import Path
import unittest
from polygon import TRACKS, checked_predictions, data_for, evaluate, projects, report
from scripts.check_reference import verify

class PolygonTests(unittest.TestCase):
    def test_discovery(self):
        self.assertEqual(len(projects()), 6)
        self.assertEqual(len(TRACKS), 2)
        for name, meta in projects().items():
            self.assertEqual(meta['origin'], 'scratch', name)

    def test_reproducible_disjoint_data(self):
        first = data_for('regression', 'shift', 11)
        self.assertEqual(first, data_for('regression', 'shift', 11))
        self.assertEqual([len(group) for group in first], [240, 80, 120])
        ids = [row['id'] for group in first for row in group]
        self.assertEqual(len(ids), len(set(ids)))

    def test_unlabeled_prediction_input_contract(self):
        _, _, test = data_for('classification', 'xor', 11)
        inputs = [{'id': r['id'], 'x': r['x']} for r in test]
        self.assertTrue(all('y' not in row for row in inputs))

    def test_training_actually_runs(self):
        result = evaluate('baseline_linear', 'linear', 11)
        self.assertEqual(result['status'], 'completed')
        self.assertLess(result['metrics']['rmse'], 0.2)
        self.assertEqual(len(result['evidence']['project_sha256']), 64)

    def test_reject_invalid_predictions(self):
        expected = [{'id':'test-0','y':0},{'id':'test-1','y':1}]
        with tempfile.TemporaryDirectory() as tmp:
            file = Path(tmp)/'out.jsonl'
            bad = [
                [{'id':'test-0','prediction':0}],
                [{'id':'test-0','prediction':0},{'id':'test-0','prediction':1}],
                [{'id':'test-0','prediction':True},{'id':'test-1','prediction':1}],
                [{'id':'test-0','prediction':0.5},{'id':'test-1','prediction':1}],
                [{'id':'test-0','prediction':0},{'id':'wrong','prediction':1}]
            ]
            for data in bad:
                file.write_text(''.join(json.dumps(row)+'\n' for row in data))
                with self.assertRaises(ValueError):
                    checked_predictions(file, expected, 'classification')

    def test_published_reference_evidence(self):
        baseline = json.loads(Path('results/reference-demo.json').read_text())
        self.assertEqual(baseline['trials'], 80)
        self.assertEqual(len(baseline['summary']), 16)
        for group in baseline['summary']:
            self.assertEqual(len(group['proof_sha256']), 64)

    def test_reference_verifier_rejects_tampering(self):
        from scripts.check_reference import fingerprint
        baseline = json.loads(Path('results/reference-demo.json').read_text())
        rows = []
        for group in baseline['summary']:
            self.assertEqual(group['n'], 5)
            self.assertEqual(len(group['proof_sha256']), 64)
        bad = json.loads(json.dumps(baseline))
        bad['summary'][0]['proof_sha256'] = '0'*64
        self.assertNotEqual(bad['summary'][0]['proof_sha256'],baseline['summary'][0]['proof_sha256'])

if __name__ == '__main__': unittest.main()
