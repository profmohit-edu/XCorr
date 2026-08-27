# XCorr

XCorr is an independently identifiable cross-analyzer vulnerability correlation prototype for Ethereum smart contracts, created by Mohit Tiwari, Department of Computer Science and Engineering, Bharati Vidyapeeth's College of Engineering, New Delhi.

## Implemented pipeline

Analyzer JSON → adapter-based normalization → canonical vulnerability taxonomy → contract/file and line-tolerance grouping → tool consensus and confidence → JSON/CSV correlated output.

Supported import shapes include XCorr's generic schema plus representative Slither, Mythril and Solhint JSON. Unknown or malformed findings are reported without silently fabricating results.

Correlation is deterministic. Two findings correlate when their normalized file, canonical vulnerability and source lines match within the configured tolerance. Confidence combines independent-tool agreement and severity; it is not a claim that a vulnerability is certainly exploitable.

## Run

```bash
python3 -m http.server 8000
```

Open `http://localhost:8000`, load the reproducible sample or import analyzer JSON files.

## Reproduce CLI sample and tests

```bash
node cli.js samples/slither.json samples/mythril.json samples/solhint.json > samples/correlated-output.json
node --test tests/core.test.js
```

Version 1.0.0, completed 27 August 2026. MIT licensed.
