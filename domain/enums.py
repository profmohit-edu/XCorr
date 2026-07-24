"""Canonical string enumerations shared throughout the XCorr domain.

The values in this module are persistence contracts. They use
:class:`enum.StrEnum` so machine-readable artifacts contain stable,
language-neutral strings while Python code retains distinct semantic types.
Changing a persisted value requires a schema migration and an explicit
architecture decision.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Final


class AnalyzerType(StrEnum):
    """Primary analysis methodology used by a smart-contract analyzer.

    ``HYBRID`` identifies integrations that deliberately combine multiple
    methodologies and cannot be represented accurately by one other member.
    The value describes technique, not analyzer quality or support status.
    """

    DYNAMIC_ANALYSIS = "dynamic_analysis"
    FORMAL_VERIFICATION = "formal_verification"
    FUZZING = "fuzzing"
    HYBRID = "hybrid"
    STATIC_ANALYSIS = "static_analysis"
    SYMBOLIC_EXECUTION = "symbolic_execution"


class ArtifactFormat(StrEnum):
    """Physical serialization or rendering format of an artifact.

    Format remains separate from :class:`ArtifactType`: the former describes
    encoding, while the latter describes semantic role. ``BINARY`` is reserved
    for preserved tool-native bytes whose specific media type is recorded in
    artifact metadata.
    """

    BINARY = "binary"
    CSV = "csv"
    HTML = "html"
    JSON = "json"
    JSON_LINES = "jsonl"
    LATEX = "latex"
    MARKDOWN = "markdown"
    PDF = "pdf"
    PNG = "png"
    SARIF = "sarif"
    SVG = "svg"
    TEXT = "text"
    TSV = "tsv"
    YAML = "yaml"


class ArtifactType(StrEnum):
    """Semantic role of an immutable artifact in the XCorr data flow.

    Members correspond to the versioned run layout defined by the architecture.
    They distinguish native evidence, derived correlation data, evaluation
    records, publication products, and integrity metadata independently of file
    format.
    """

    ANALYSIS_PLAN = "analysis_plan"
    BLOCKED_MERGES = "blocked_merges"
    CANDIDATE_PAIRS = "candidate_pairs"
    CANONICAL_FINDINGS = "canonical_findings"
    CHECKSUM_MANIFEST = "checksum_manifest"
    CORRELATION_DECISIONS = "correlation_decisions"
    CORRELATION_GROUPS = "correlation_groups"
    DATASET_MANIFEST = "dataset_manifest"
    EFFECTIVE_CONFIGURATION = "effective_configuration"
    EVALUATION_EXCLUSIONS = "evaluation_exclusions"
    EVALUATION_METRICS = "evaluation_metrics"
    EVALUATION_RECORDS = "evaluation_records"
    EXECUTION_RECORD = "execution_record"
    EXPLANATIONS = "explanations"
    FIGURE = "figure"
    GROUND_TRUTH_REFERENCE = "ground_truth_reference"
    NATIVE_REPORT = "native_report"
    NORMALIZATION_EVENTS = "normalization_events"
    PARSED_FINDINGS = "parsed_findings"
    PARSER_DIAGNOSTICS = "parser_diagnostics"
    REPORT = "report"
    RUN_MANIFEST = "run_manifest"
    SIGNAL_OBSERVATIONS = "signal_observations"
    SOURCE_INDEX = "source_index"
    STANDARD_ERROR = "standard_error"
    STANDARD_OUTPUT = "standard_output"
    STATISTICAL_RESULTS = "statistical_results"


class CorrelationDecision(StrEnum):
    """Outcome of a pairwise finding-correlation decision.

    ``ABSTAIN`` is a first-class outcome used when required evidence is missing,
    conflicting, inapplicable, or invalid. It must not be interpreted as either
    a match or a non-match.
    """

    ABSTAIN = "abstain"
    MATCH = "match"
    NON_MATCH = "non_match"


class CorrelationStrength(StrEnum):
    """Qualitative band assigned to valid correlation evidence.

    Numeric boundaries are external, versioned policy configuration rather
    than enum behavior. ``UNDETERMINED`` represents evidence for which no valid
    strength can be assigned and is distinct from ``NONE``.
    """

    MODERATE = "moderate"
    NONE = "none"
    STRONG = "strong"
    UNDETERMINED = "undetermined"
    VERY_STRONG = "very_strong"
    WEAK = "weak"


class EvaluationLevel(StrEnum):
    """Population level at which an evaluation result is calculated."""

    ANALYZER = "analyzer"
    DATASET = "dataset"
    FINDING = "finding"
    GROUP = "group"
    PAIRWISE = "pairwise"
    RUN = "run"
    TARGET = "target"


class EvaluationMetric(StrEnum):
    """Registered metric identity for correlation and systems evaluation.

    Metric implementations, averaging rules, populations, intervals, and
    undefined-value handling are versioned separately. Resource metrics use
    units in their persisted names to prevent ambiguous interpretation.
    """

    ACCURACY = "accuracy"
    ADJUSTED_RAND_INDEX = "adjusted_rand_index"
    B3_F1_SCORE = "b3_f1_score"
    B3_PRECISION = "b3_precision"
    B3_RECALL = "b3_recall"
    BRIER_SCORE = "brier_score"
    COVERAGE = "coverage"
    EXPECTED_CALIBRATION_ERROR = "expected_calibration_error"
    F1_SCORE = "f1_score"
    FALSE_NEGATIVE_RATE = "false_negative_rate"
    FALSE_POSITIVE_RATE = "false_positive_rate"
    LATENCY_SECONDS = "latency_seconds"
    PEAK_MEMORY_BYTES = "peak_memory_bytes"
    PRECISION = "precision"
    RECALL = "recall"
    SPECIFICITY = "specificity"
    THROUGHPUT_TARGETS_PER_SECOND = "throughput_targets_per_second"


class EvidenceType(StrEnum):
    """Canonical evidence category supporting or opposing a decision.

    These categories match the architecture's typed evidence model. A concrete
    evidence record retains its native artifact provenance and structured
    payload in addition to this classification.
    """

    EXECUTION = "execution"
    LOCATION = "location"
    PROVENANCE = "provenance"
    SEMANTIC = "semantic"
    STRUCTURAL = "structural"
    TAXONOMY = "taxonomy"
    TEXTUAL = "textual"


class ExecutionEnvironment(StrEnum):
    """Trusted control or isolated runtime environment for an execution."""

    DOCKER_COMPOSE = "docker_compose"
    HOST = "host"


class ExecutionStatus(StrEnum):
    """Terminal process status of an analyzer execution attempt.

    Process success does not assert that a native report parsed successfully;
    parsing and normalization have their own explicit status records.
    """

    CANCELLED = "cancelled"
    FAILED = "failed"
    RUNTIME_ERROR = "runtime_error"
    SUCCEEDED = "succeeded"
    TERMINATED = "terminated"
    TIMED_OUT = "timed_out"


class FindingConfidence(StrEnum):
    """Canonical confidence band for a normalized vulnerability finding.

    ``UNKNOWN`` preserves unavailable or unmappable native confidence rather
    than silently substituting a numeric or ordinal default.
    """

    CONFIRMED = "confirmed"
    HIGH = "high"
    LOW = "low"
    MEDIUM = "medium"
    UNKNOWN = "unknown"


class FindingSeverity(StrEnum):
    """Canonical impact-severity band for a normalized finding.

    Severity is independent from confidence. ``INFORMATIONAL`` represents a
    deliberate non-impact diagnostic classification; ``UNKNOWN`` represents
    missing or unmappable analyzer severity.
    """

    CRITICAL = "critical"
    HIGH = "high"
    INFORMATIONAL = "informational"
    LOW = "low"
    MEDIUM = "medium"
    UNKNOWN = "unknown"


class FindingSource(StrEnum):
    """Provenance category describing where a finding record originated."""

    ANALYZER = "analyzer"
    IMPORTED_GROUND_TRUTH = "imported_ground_truth"
    MANUAL_ANNOTATION = "manual_annotation"


class FindingStatus(StrEnum):
    """Review and disposition state of a canonical finding.

    Status is annotation metadata and never rewrites analyzer-native evidence.
    ``UNKNOWN`` preserves records whose disposition has not been established.
    """

    CONFIRMED = "confirmed"
    FALSE_POSITIVE = "false_positive"
    MITIGATED = "mitigated"
    OPEN = "open"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"
    UNKNOWN = "unknown"


class NormalizationStatus(StrEnum):
    """Outcome of one explicit native-to-canonical normalization operation.

    ``EXACT`` preserves meaning without loss, ``LOSSY`` records a deliberate
    reduction, ``DEFAULTED`` records an explicit configured default,
    ``UNMAPPED`` retains an unsupported native value, and ``REJECTED`` records
    a value that failed the normalization contract.
    """

    DEFAULTED = "defaulted"
    EXACT = "exact"
    LOSSY = "lossy"
    REJECTED = "rejected"
    UNMAPPED = "unmapped"


class ReportFormat(StrEnum):
    """Supported deterministic rendering format for reports and tables."""

    CSV = "csv"
    HTML = "html"
    JSON = "json"
    LATEX = "latex"
    MARKDOWN = "markdown"
    PDF = "pdf"
    TEXT = "text"


class TargetLanguage(StrEnum):
    """Canonical source or executable language of an analysis target."""

    EVM_BYTECODE = "evm_bytecode"
    SOLIDITY = "solidity"
    VYPER = "vyper"
    YUL = "yul"


__all__: Final[tuple[str, ...]] = (
    "AnalyzerType",
    "ArtifactFormat",
    "ArtifactType",
    "CorrelationDecision",
    "CorrelationStrength",
    "EvaluationLevel",
    "EvaluationMetric",
    "EvidenceType",
    "ExecutionEnvironment",
    "ExecutionStatus",
    "FindingConfidence",
    "FindingSeverity",
    "FindingSource",
    "FindingStatus",
    "NormalizationStatus",
    "ReportFormat",
    "TargetLanguage",
)
