# XCorr

XCorr is a research framework for explainable correlation of smart-contract vulnerability findings produced by multiple analysis tools. The project is intended to provide a production-quality, independently testable, and reproducible pipeline that executes heterogeneous analyzers, normalizes their outputs, correlates related findings, explains each correlation decision, and evaluates the resulting methods without obscuring disagreements between tools.

The framework targets Python 3.12 on Ubuntu 24.04 and uses Docker Compose to make analyzer execution and experiments repeatable. Its implementation follows SOLID principles and Clean Architecture: domain logic remains independent of analyzer integrations, infrastructure, persistence, and presentation concerns. Configuration, dataset provenance, random seeds, tool versions, and experiment parameters are externalized and versioned.

> **Project status:** Active development. Research infrastructure is under implementation. No experimental claims or performance conclusions are presented until they are reproduced through the documented evaluation pipeline.

## Research motivation

Smart-contract security analyzers differ in their vulnerability taxonomies, program locations, execution models, reporting formats, and levels of diagnostic detail. Consequently, multiple tools may report the same underlying defect with incompatible labels or locations, while superficially similar reports may describe distinct defects. Simple aggregation can therefore inflate finding counts, hide tool disagreement, and make it difficult for auditors and researchers to understand why reports were grouped.

XCorr addresses this problem as an evidence-based correlation task. It retains each analyzer's original evidence, maps findings into a common representation, combines multiple correlation signals, and exposes the contribution of those signals to every decision. The research emphasis is not merely on merging reports, but on making the merge process measurable, auditable, and reproducible.

## Research objectives

1. Define a tool-independent finding model that preserves analyzer provenance, source locations, vulnerability semantics, execution evidence, and uncertainty.
2. Build isolated adapters for reproducibly executing supported smart-contract analyzers and normalizing their native outputs.
3. Design and compare correlation methods based on taxonomy, source location, program structure, textual evidence, and analyzer metadata.
4. Produce human-readable and machine-readable explanations for correlation and non-correlation decisions.
5. Evaluate correlation quality on versioned, provenance-tracked datasets using a documented annotation protocol and appropriate statistical analysis.
6. Measure robustness, calibration, efficiency, and sensitivity to individual signals, tools, and configuration choices.
7. Release the code, configurations, datasets that may legally be redistributed, experiment manifests, figures, and paper artifacts required to reproduce reported results.

## Research Questions

RQ1. How consistently can heterogeneous smart contract analyzers identify the same underlying vulnerability?

RQ2. Which combination of correlation signals provides the highest agreement with manually verified ground truth?

RQ3. Can explainable correlation reduce duplicate findings while preserving analyzer-specific evidence?

RQ4. What is the computational overhead introduced by the correlation framework?

## Planned novel contributions

The following are research targets, not claims of completed or validated results:

- A canonical finding representation that preserves tool-specific evidence while enabling comparison across heterogeneous analyzer taxonomies.
- A multi-signal correlation approach that represents uncertainty and distinguishes supporting, conflicting, and missing evidence.
- Per-decision explanations that trace correlated findings back to normalized features, rules or model outputs, configuration, and original analyzer reports.
- An evaluation protocol for multi-tool vulnerability correlation, including explicit ground-truth construction, inter-annotator agreement, leakage controls, ablation studies, and uncertainty-aware statistical reporting.
- A reproducible experiment framework that records source revisions, dataset identities, container images, analyzer versions, configurations, seeds, runtime context, and generated artifact checksums.

These contributions are stated as findings only after implementation, execution, and analysis. Any eventual publication claim must be supported by repository evidence and appropriate citations.

## Planned architecture

XCorr separates research-domain policy from external tools and operational infrastructure.

| Area | Responsibility |
| --- | --- |
| `analyzers/` | Analyzer interfaces, container-backed adapters, native-output parsers, and normalization boundaries. |
| `orchestrator/` | Reproducible workflow coordination, run manifests, lifecycle management, and artifact collection. |
| `correlation/` | Canonical finding models, candidate generation, feature extraction, scoring, decision policies, and uncertainty handling. |
| `explainability/` | Explanation models, evidence tracing, decision narratives, and machine-readable explanation exports. |
| `evaluation/` | Ground-truth handling, metrics, validation protocols, error analysis, and evaluation services. |
| `datasets/` | Dataset manifests, provenance, integrity metadata, schemas, and redistribution-safe dataset resources. |
| `experiments/` | Immutable experiment specifications and generated run outputs organized by experiment identity. |
| `statistics/` | Statistical tests, effect sizes, confidence intervals, correction procedures, and analysis utilities. |
| `reports/` and `figures/` | Generated tables, reports, and publication figures derived from recorded experiment artifacts. |
| `configs/` | Externalized application, analyzer, correlation, logging, dataset, and experiment configuration. |
| `docker/` | Container definitions and pinned runtime support used by Docker Compose. |
| `scripts/` | Thin, typed entry points for setup, validation, execution, and artifact generation. |
| `tests/` | Unit, contract, integration, regression, and reproducibility tests. |
| `docs/` | Architecture decisions, schemas, operational guidance, contribution guidance, and dataset documentation. |
| `paper/` | Manuscript sources and publication material generated from verified evidence. |

Dependencies point inward: analyzer and infrastructure adapters may depend on application and domain interfaces, while core correlation and explanation logic does not depend on a particular analyzer, container runtime, database, or reporting format. Components communicate through explicit typed contracts and support dependency injection so each module can be tested independently.

The intended execution flow is:

1. Resolve a versioned dataset and validate its integrity.
2. Materialize a complete run manifest from external configuration.
3. Execute enabled analyzers in pinned, isolated containers.
4. Retain immutable native reports and execution metadata.
5. Normalize reports into the canonical finding model.
6. Generate candidate cross-tool finding pairs or groups.
7. Compute correlation evidence and decisions.
8. Generate explanations linked to the original evidence.
9. Evaluate against an explicitly versioned ground truth.
10. Produce statistics, reports, figures, and checksums from recorded artifacts.

## Reproducibility principles

XCorr applies the following requirements to all publishable experiments:

- **Pinned environments:** Python dependencies, operating-system images, analyzers, and supporting services are pinned to explicit versions or immutable image digests.
- **Configuration as data:** runtime behavior is controlled by validated configuration files and environment variables; research parameters are not hidden in source code.
- **Traceable inputs:** every dataset has a manifest containing its source, license or access constraints, version, selection criteria, preprocessing history, and integrity checksums.
- **Immutable raw evidence:** native analyzer output, standard output, standard error, exit status, timing data, and tool metadata are retained without silent rewriting.
- **Deterministic execution:** seeds, ordering rules, concurrency settings, and nondeterministic dependencies are recorded and controlled where the underlying tools permit it.
- **Complete run manifests:** every run records the source revision, configuration digest, input digests, container identities, tool versions, host context, timestamps, and artifact locations.
- **Separation of generated artifacts:** derived reports, figures, and statistics are generated from preserved machine-readable results and are never treated as primary observations.
- **Fail-closed validation:** schema violations, checksum mismatches, missing provenance, unsupported tool versions, and incomplete runs cause explicit failures rather than partial success.
- **Statistical transparency:** evaluation plans identify metrics, hypotheses, statistical tests, effect sizes, uncertainty intervals, multiple-comparison procedures, exclusions, and missing-data handling before claims are made.
- **Independent verification:** documented commands reconstruct environments, rerun tests and experiments, and verify artifact checksums on Ubuntu 24.04 with Docker Compose.

Secrets and machine-specific paths are not committed. Any dataset or analyzer that cannot legally be redistributed is represented by provenance and acquisition instructions rather than copied into the repository.

## Success Criteria

- Fully reproducible experiments
- Open-source implementation
- Containerized execution
- Automated statistical analysis
- IEEE-quality figures
- Publication-ready datasets
- End-to-end automation

## Development roadmap

The roadmap is ordered so that claims and downstream artifacts depend only on validated upstream components.

### Phase 1 — Foundation

- Establish Python 3.12 packaging, quality gates, structured logging, exception boundaries, and configuration validation.
- Define architectural boundaries, typed interfaces, data schemas, and contribution requirements.
- Create Docker Compose services and reproducible developer/test environments.

### Phase 2 — Analyzer integration

- Define analyzer execution and parsing contracts.
- Implement one adapter at a time with unit fixtures, contract tests, integration tests, and pinned container definitions.
- Preserve native evidence and verify normalization against documented analyzer outputs.

### Phase 3 — Correlation and explainability

- Implement the canonical finding and evidence models.
- Add deterministic candidate generation and configurable correlation signals.
- Implement decision policies, uncertainty representation, explanation generation, and evidence traceability.
- Test invariants, edge cases, malformed reports, and cross-tool disagreement scenarios.

### Phase 4 — Dataset and evaluation protocol

- Define dataset inclusion criteria, provenance schemas, annotation guidance, and quality checks.
- Construct or acquire evaluation data without fabricating labels or redistributing restricted material.
- Version ground truth, quantify annotator agreement where applicable, and freeze evaluation splits before final analysis.

### Phase 5 — Experiments and statistics

- Register experiment configurations and hypotheses before execution.
- Run baselines, comparisons, ablations, sensitivity analyses, robustness checks, and resource measurements.
- Compute metrics and statistical analyses from preserved outputs; investigate failures and document exclusions.

### Phase 6 — Publication and release

- Generate tables and figures directly from verified experiment artifacts.
- Write the manuscript with traceable citations and claims tied to repository evidence.
- Reproduce the complete workflow in a clean environment, archive eligible artifacts, and publish release checksums and documentation.

## Repository structure

```text
XCorr/
├── analyzers/       # Analyzer adapters, parsers, and normalization boundaries
├── orchestrator/    # Workflow execution, manifests, and artifact lifecycle
├── correlation/     # Correlation domain models, signals, and decision logic
├── explainability/  # Evidence tracing and decision explanations
├── evaluation/      # Metrics, validation protocols, and error analysis
├── datasets/        # Dataset manifests, schemas, provenance, and permitted data
├── experiments/     # Experiment specifications and run artifacts
├── reports/         # Generated evaluation reports and tables
├── figures/         # Reproducibly generated publication figures
├── statistics/      # Statistical analysis code and outputs
├── configs/         # Versioned external configuration
├── docker/          # Container definitions and runtime support
├── scripts/         # Typed operational and research entry points
├── tests/           # Unit, contract, integration, and regression tests
├── docs/            # Architecture, protocols, schemas, and user documentation
└── paper/           # Manuscript and publication artifacts
```

Directories are introduced with the files that make their responsibilities executable or documentable; empty scaffolding is intentionally avoided. Generated data is clearly distinguished from source-controlled specifications, fixtures, and small redistribution-safe research assets.

## Research integrity

XCorr does not accept fabricated findings, benchmarks, citations, datasets, annotations, or experimental outcomes. Negative results, analyzer failures, unsupported contracts, and missing observations are retained and reported. Until a result can be reconstructed from versioned inputs and preserved artifacts, it is not a project result.

Every published figure, table, and numerical claim must be generated automatically from recorded experimental artifacts.
