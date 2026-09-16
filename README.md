# AI Polygon

**Architecture-neutral AI research playground.** Submit a fully independent model, algorithm, training process or non-neural method, run it through a common task contract and inspect reproducible evidence. Open source, MIT licensed, English-only site and documentation. [Open the live deployment after connecting Vercel](https://vercel.com/new).

> **Scope and honesty:** This is a functioning *public synthetic benchmark prototype*, not a blind test, a universal intelligence ranking, a secure arbitrary-code service, or a comparison with today's frontier models. The initial six reference methods are deliberately simple CPU controls. Public benchmark generators can be reverse-engineered; repeated tuning against them invalidates generalization claims. No deployment, security system or software is guaranteed bug-free.

## Try it locally

Requires Python 3.10+ and Node.js 20+. No Python/npm package installation, API key, database or GPU is required for the included examples.

```bash
python3 -m unittest discover -s tests -v
python3 polygon.py list
python3 polygon.py evaluate baseline_linear linear --seed 11
python3 polygon.py run-all --output results/local.json
python3 scripts/check_reference.py results/local.json
npm run build
npm test
```

To preview the generated static site, run `python3 -m http.server 3000 --directory dist` and open http://localhost:3000.

## Deploy on Vercel

1. Import **https://github.com/tahir94510/ai-polygon** into your Vercel account. Select the repository root and framework **Other**.
2. The committed `vercel.json` sets `npm run build` and output folder `dist`. Use the default Node.js runtime (20 or newer). **No environment variables, database, API key or external service are required for the dashboard.**
3. Click **Deploy**. The website reads committed reference results from the repository; it does **not** run Python or train models on Vercel. GitHub Actions separately reruns reference tasks after reviewed changes are pushed to `main`. Inspect its workflow results for cloud verification.

The Vercel Hobby plan has eligibility and usage restrictions, and the public GitHub Actions runner is CPU-only for these purposes. This design does not offer unlimited free compute or online arbitrary-code execution. Connecting Vercel to GitHub requires the repository owner's one-time authorization.

## Run a completely different technology

Each `projects/<name>/` directory is independent. The evaluator does not import its architecture. A manifest defines `track`, `origin`, `train` and `predict` commands. Train on labeled JSONL rows and output a model artifact; predict on a separate unlabeled JSONL file and output one finite prediction per test ID. Your project can use a novel neural net, a statistical algorithm, a program synthesis engine or an external pretrained model (declare `origin: pretrained`). See [CONTRIBUTING.md](CONTRIBUTING.md) for the exact format.

You can create a new benchmark family by extending the versioned task registry in `polygon.py` and the corresponding dashboard track in `scripts/build.mjs`. Keep a task's definition fixed once published; publish a new version when changing its dataset or metric.

## Measurement and security rules

The two initial families are **tabular regression** (RMSE/MAE) and **binary classification** (accuracy). Each task runs five fixed seeds with disjoint train/validation/test rows. The prediction command never receives test labels. The runner rejects missing/duplicate IDs, NaN, infinity, incorrect classification values and missing artifacts; failures are retained. It records wall time, artifact bytes and SHA-256 of project files, train inputs, test inputs and predictions. Hashes establish byte identity, not fairness or proof against cheating. Model size is **not** peak RAM; no energy or FLOP claims are made.

The `results/reference-demo.json` report holds compact summaries and SHA-256 fingerprints for 80 locally observed trials. Full per-trial source/input/prediction hashes are generated in CI artifacts, not embedded in the static website. GitHub Actions independently reruns them and compares hashes and numerical scores (not wall time); CI artifacts are retained for a limited period. The CI workflow does not automatically execute fork pull requests. Maintainers must review code *before* merging to `main`, and the hosted worker is not a secure sandbox. Public generator rules mean these are **not hidden holdouts**. Honest comparisons across pretrained and scratch models require separate tracks and matched resource budgets.

For serious research: register a hypothesis in advance, freeze model changes before an untouched benchmark, report uncertainty from independent runs and disclose hardware, datasets, weights and evaluation costs. Hosted private holdouts and strong adversarial code isolation would require infrastructure beyond a static Vercel site and ordinary public GitHub Actions.

## Project structure

- `polygon.py`: benchmark generator, independent command runner, validation, scoring and provenance.
- `projects/`: six interchangeable standalone baseline implementations, each with its own manifest.
- `results/reference-demo.json`: compact grouped metrics and grouped provenance fingerprints.
- `scripts/`: static build and independent report verification.
- `site/index.html`: black, responsive, framework-free public results dashboard.
- `.github/workflows/verify.yml`: read-only, main-branch CPU verification.
- `tests/`: contract, integrity and deployment smoke tests.

MIT license for platform code. Contributors must have the right to publish all code, model weights and datasets they submit.
