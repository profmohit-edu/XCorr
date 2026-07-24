"""Typed contracts for analyzer integrations.

This module defines the persistent records and behavioral ports at XCorr's
analyzer boundary. The records preserve analyzer provenance and native output
without importing correlation, explainability, or evaluation concepts.
Behavioral contracts are expressed as protocols so application services can
depend on capabilities rather than concrete analyzer implementations.

Persisted records are strict, frozen Pydantic v2 models with explicit schema
versions. Generic normalization results use an immutable dataclass because the
canonical finding and normalization-event types belong to an inner domain
layer and are intentionally unknown to this package.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Annotated, BinaryIO, Final, Generic, Protocol, TypeVar, runtime_checkable

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    JsonValue,
    NonNegativeFloat,
    NonNegativeInt,
    PositiveFloat,
    PositiveInt,
    RootModel,
    StringConstraints,
)

CONTRACT_SCHEMA_VERSION: Final[str] = "1.0.0"

SchemaVersion = Annotated[
    str,
    StringConstraints(
        min_length=3,
        max_length=32,
        pattern=r"^[0-9]+\.[0-9]+(?:\.[0-9]+)?$",
    ),
]
ContentDigest = Annotated[
    str,
    StringConstraints(
        min_length=71,
        max_length=71,
        pattern=r"^sha256:[0-9a-f]{64}$",
    ),
]
NonEmptyText = Annotated[str, StringConstraints(min_length=1, max_length=16_384)]
ShortText = Annotated[str, StringConstraints(min_length=1, max_length=512)]
MediaType = Annotated[
    str,
    StringConstraints(
        min_length=3,
        max_length=255,
        pattern=r"^[A-Za-z0-9!#$&^_.+-]+/[A-Za-z0-9!#$&^_.+-]+$",
    ),
]
EnvironmentName = Annotated[
    str,
    StringConstraints(
        min_length=1,
        max_length=255,
        pattern=r"^[A-Za-z_][A-Za-z0-9_]*$",
    ),
]


class AnalyzerId(
    RootModel[
        Annotated[
            str,
            StringConstraints(
                min_length=1,
                max_length=64,
                pattern=r"^[a-z0-9]+(?:[._-][a-z0-9]+)*$",
            ),
        ]
    ]
):
    """Stable lowercase identifier for an analyzer integration.

    The identifier names the integration across configurations, entry points,
    manifests, and artifacts. It is independent of adapter, tool, and image
    versions.
    """

    model_config = ConfigDict(frozen=True, strict=True, validate_default=True)


class AnalyzerVersion(
    RootModel[
        Annotated[
            str,
            StringConstraints(
                min_length=1,
                max_length=128,
                pattern=r"^[A-Za-z0-9][A-Za-z0-9._+~-]*$",
            ),
        ]
    ]
):
    """Opaque, validated version identifier for an adapter or analyzer tool.

    XCorr preserves version strings rather than imposing semantic-version
    ordering on third-party tools. Compatibility decisions belong to the
    analyzer registry and are not inferred from this value object.
    """

    model_config = ConfigDict(frozen=True, strict=True, validate_default=True)


class AnalyzerCapability(StrEnum):
    """Capabilities that an analyzer integration can declare explicitly."""

    SOURCE_CODE = "source_code"
    EVM_BYTECODE = "evm_bytecode"
    PROJECT_ANALYSIS = "project_analysis"
    MULTI_CONTRACT = "multi_contract"
    IMPORT_RESOLUTION = "import_resolution"
    COMPILER_VERSION_SELECTION = "compiler_version_selection"
    STRUCTURED_OUTPUT = "structured_output"
    SOURCE_LOCATIONS = "source_locations"
    SEVERITY = "severity"
    CONFIDENCE = "confidence"
    RULE_METADATA = "rule_metadata"
    DETERMINISTIC_SEED = "deterministic_seed"


class AnalyzerLifecycleStatus(StrEnum):
    """Support state of an analyzer integration within XCorr."""

    EXPERIMENTAL = "experimental"
    SUPPORTED = "supported"
    DEPRECATED = "deprecated"
    REMOVED = "removed"


class AnalyzerHealthStatus(StrEnum):
    """Observed readiness state of an analyzer integration."""

    UNKNOWN = "unknown"
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"
    INCOMPATIBLE = "incompatible"


class AnalyzerExecutionStatus(StrEnum):
    """Terminal status of an analyzer execution attempt.

    A successful status records process execution only. Native report parsing
    and schema validation remain separate stages.
    """

    SUCCEEDED = "succeeded"
    FAILED = "failed"
    TIMED_OUT = "timed_out"
    CANCELLED = "cancelled"
    TERMINATED = "terminated"
    RUNTIME_ERROR = "runtime_error"


class NativeArtifactKind(StrEnum):
    """Role of an immutable artifact emitted during analyzer execution."""

    REPORT = "report"
    STANDARD_OUTPUT = "standard_output"
    STANDARD_ERROR = "standard_error"
    SUPPLEMENTAL = "supplemental"


class DiagnosticSeverity(StrEnum):
    """Severity assigned to a native-report parser diagnostic."""

    INFORMATION = "information"
    WARNING = "warning"
    ERROR = "error"


class MountAccess(StrEnum):
    """Access granted to an analyzer container for a mounted path."""

    READ_ONLY = "read_only"
    READ_WRITE = "read_write"


class MountRole(StrEnum):
    """Purpose of a mount in an analyzer execution request."""

    INPUT = "input"
    OUTPUT = "output"
    TEMPORARY = "temporary"


class _FrozenContractModel(BaseModel):
    """Shared strict configuration for schema-versioned boundary records."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        strict=True,
        validate_default=True,
        revalidate_instances="always",
    )

    schema_version: SchemaVersion = CONTRACT_SCHEMA_VERSION


class AnalyzerDescriptor(_FrozenContractModel):
    """Immutable identity, compatibility, and runtime metadata for an analyzer.

    ``image_reference`` is retained for operator readability, while
    ``image_digest`` is the immutable runtime identity used by publishable
    executions. Supported schema versions describe the integration boundary,
    not vulnerability taxonomy versions.
    """

    analyzer_id: AnalyzerId
    display_name: ShortText
    adapter_version: AnalyzerVersion
    tool_version: AnalyzerVersion
    image_reference: ShortText
    image_digest: ContentDigest
    lifecycle_status: AnalyzerLifecycleStatus
    capabilities: Annotated[frozenset[AnalyzerCapability], Field(min_length=1)]
    supported_input_schema_versions: Annotated[tuple[SchemaVersion, ...], Field(min_length=1)]
    supported_output_schema_versions: Annotated[tuple[SchemaVersion, ...], Field(min_length=1)]
    configuration_schema_version: SchemaVersion
    native_output_media_types: Annotated[tuple[MediaType, ...], Field(min_length=1)]
    deterministic: bool


class ResourceLimits(_FrozenContractModel):
    """Explicit resource boundaries applied to an analyzer container."""

    timeout_seconds: PositiveFloat
    termination_grace_seconds: NonNegativeFloat
    cpu_count: PositiveFloat
    memory_bytes: PositiveInt
    process_count: PositiveInt
    maximum_output_bytes: PositiveInt
    temporary_storage_bytes: PositiveInt


class MountDescriptor(_FrozenContractModel):
    """Explicit host-to-container mount declared for one execution.

    Path containment, symlink rejection, and role/access compatibility are
    validated by the runtime adapter before container creation. Input mounts
    are required to use :attr:`MountAccess.READ_ONLY`.
    """

    role: MountRole
    access: MountAccess
    host_path: NonEmptyText
    container_path: NonEmptyText


class EnvironmentVariable(_FrozenContractModel):
    """Non-secret environment value safe to preserve in an execution request."""

    name: EnvironmentName
    value: str


class SecretReference(_FrozenContractModel):
    """Reference to a runtime secret without persisting its value.

    ``target_name`` is the environment name exposed to the analyzer process;
    ``source_name`` identifies the approved host-side secret channel resolved
    by infrastructure immediately before execution.
    """

    target_name: EnvironmentName
    source_name: EnvironmentName


class ExecutionRequest(_FrozenContractModel):
    """Validated, serializable request for one isolated analyzer execution.

    Commands are represented as argument vectors and are never interpreted by
    a shell. Target identifiers and mounts are explicit, effective tool
    configuration is preserved, and every resource bound is mandatory.
    """

    request_id: ContentDigest
    run_id: ContentDigest
    analyzer: AnalyzerDescriptor
    target_ids: Annotated[tuple[ContentDigest, ...], Field(min_length=1)]
    command: Annotated[tuple[NonEmptyText, ...], Field(min_length=1)]
    working_directory: NonEmptyText
    mounts: Annotated[tuple[MountDescriptor, ...], Field(min_length=1)]
    resource_limits: ResourceLimits
    effective_configuration: Mapping[str, JsonValue] = Field(default_factory=dict)
    environment: tuple[EnvironmentVariable, ...] = ()
    secret_references: tuple[SecretReference, ...] = ()
    network_enabled: bool = False
    random_seed: int | None = None


class NativeArtifact(_FrozenContractModel):
    """Metadata for immutable bytes produced by an analyzer execution.

    Artifact content is stored separately. ``relative_path`` is interpreted
    beneath the validated run root and never as an unrestricted filesystem
    path. ``recorded_at`` is provenance and does not contribute to content
    identity.
    """

    artifact_id: ContentDigest
    content_digest: ContentDigest
    run_id: ContentDigest
    request_id: ContentDigest
    analyzer_id: AnalyzerId
    analyzer_version: AnalyzerVersion
    kind: NativeArtifactKind
    relative_path: NonEmptyText
    media_type: MediaType
    size_bytes: NonNegativeInt
    recorded_at: datetime
    metadata: Mapping[str, JsonValue] = Field(default_factory=dict)


class ResourceUsage(_FrozenContractModel):
    """Resource observations reported by the execution runtime when available."""

    cpu_seconds: NonNegativeFloat | None = None
    peak_memory_bytes: NonNegativeInt | None = None
    output_bytes: NonNegativeInt | None = None
    temporary_storage_bytes: NonNegativeInt | None = None


class ExecutionResult(_FrozenContractModel):
    """Immutable record of one terminal analyzer execution attempt.

    Timestamps must be timezone-aware and ``finished_at`` must not precede
    ``started_at``. Infrastructure records process status independently from
    parser validity, so :attr:`AnalyzerExecutionStatus.SUCCEEDED` does not
    assert that any native report is well formed.
    """

    request_id: ContentDigest
    run_id: ContentDigest
    analyzer_id: AnalyzerId
    adapter_version: AnalyzerVersion
    tool_version: AnalyzerVersion
    image_digest: ContentDigest
    runtime_version: NonEmptyText
    status: AnalyzerExecutionStatus
    started_at: datetime
    finished_at: datetime
    duration_seconds: NonNegativeFloat
    exit_code: int | None
    termination_reason: str | None = None
    failure_code: ShortText | None = None
    failure_message: str | None = None
    stdout_artifact: NativeArtifact | None = None
    stderr_artifact: NativeArtifact | None = None
    native_artifacts: tuple[NativeArtifact, ...] = ()
    resource_usage: ResourceUsage | None = None


class NativeLocation(_FrozenContractModel):
    """Analyzer-native location preserved without canonical interpretation.

    Coordinate bases and end-point inclusivity are recorded because analyzers
    use incompatible conventions. Canonical byte and line projections are
    created by the normalizer, not by this record.
    """

    uri: str | None = None
    file_path: str | None = None
    start_line: NonNegativeInt | None = None
    start_column: NonNegativeInt | None = None
    end_line: NonNegativeInt | None = None
    end_column: NonNegativeInt | None = None
    start_byte: NonNegativeInt | None = None
    end_byte: NonNegativeInt | None = None
    line_base: Annotated[int, Field(ge=0, le=1)] | None = None
    column_base: Annotated[int, Field(ge=0, le=1)] | None = None
    end_inclusive: bool | None = None
    properties: Mapping[str, JsonValue] = Field(default_factory=dict)


class NativeFinding(_FrozenContractModel):
    """Analyzer-native vulnerability finding with retained provenance.

    Native severity, confidence, message, rule identity, locations, and unknown
    attributes remain distinct from canonical vulnerability concepts. The raw
    record digest links this parsed representation to its exact native bytes.
    """

    analyzer_id: AnalyzerId
    analyzer_version: AnalyzerVersion
    parser_version: AnalyzerVersion
    artifact_id: ContentDigest
    target_id: ContentDigest
    record_digest: ContentDigest
    record_index: NonNegativeInt
    native_finding_id: NonEmptyText | None = None
    rule_id: NonEmptyText
    message: str
    severity: str | None = None
    confidence: str | None = None
    locations: tuple[NativeLocation, ...] = ()
    native_attributes: Mapping[str, JsonValue] = Field(default_factory=dict)


class ParserDiagnostic(_FrozenContractModel):
    """Structured, provenance-linked diagnostic emitted while parsing output."""

    analyzer_id: AnalyzerId
    analyzer_version: AnalyzerVersion
    parser_version: AnalyzerVersion
    artifact_id: ContentDigest
    severity: DiagnosticSeverity
    code: ShortText
    message: NonEmptyText
    recoverable: bool
    record_index: NonNegativeInt | None = None
    byte_offset: NonNegativeInt | None = None
    context: Mapping[str, JsonValue] = Field(default_factory=dict)


class ParseResult(_FrozenContractModel):
    """Complete typed output of parsing one bounded native report artifact."""

    analyzer_id: AnalyzerId
    analyzer_version: AnalyzerVersion
    parser_version: AnalyzerVersion
    artifact_id: ContentDigest
    findings: tuple[NativeFinding, ...] = ()
    diagnostics: tuple[ParserDiagnostic, ...] = ()
    complete: bool


class AnalyzerHealth(_FrozenContractModel):
    """Versioned readiness observation for an analyzer integration.

    Health describes runtime availability and compatibility at ``checked_at``;
    it is not an assessment of vulnerability-detection quality.
    """

    analyzer_id: AnalyzerId
    adapter_version: AnalyzerVersion
    expected_tool_version: AnalyzerVersion
    observed_tool_version: AnalyzerVersion | None = None
    image_digest: ContentDigest
    status: AnalyzerHealthStatus
    checked_at: datetime
    runtime_version: str | None = None
    message: str | None = None
    details: Mapping[str, JsonValue] = Field(default_factory=dict)


NormalizedFindingT_co = TypeVar("NormalizedFindingT_co", covariant=True)
NormalizationEventT_co = TypeVar("NormalizationEventT_co", covariant=True)


@dataclass(frozen=True, slots=True)
class NormalizationBatch(Generic[NormalizedFindingT_co, NormalizationEventT_co]):
    """Immutable generic result returned by a finding normalizer.

    Generic parameters keep analyzer contracts independent from the canonical
    finding and normalization-event models owned by the correlation domain.
    """

    findings: tuple[NormalizedFindingT_co, ...]
    events: tuple[NormalizationEventT_co, ...]


@runtime_checkable
class Analyzer(Protocol):
    """Behavioral port for one executable analyzer integration."""

    @property
    def descriptor(self) -> AnalyzerDescriptor:
        """Return the immutable descriptor for this integration."""
        ...

    async def check_health(self) -> AnalyzerHealth:
        """Observe runtime readiness and version compatibility."""
        ...

    async def execute(self, request: ExecutionRequest, /) -> ExecutionResult:
        """Execute one validated request and preserve terminal runtime facts."""
        ...


@runtime_checkable
class NativeReportParser(Protocol):
    """Behavioral port for parsing one bounded native analyzer artifact."""

    @property
    def analyzer_id(self) -> AnalyzerId:
        """Return the analyzer identity accepted by this parser."""
        ...

    @property
    def parser_version(self) -> AnalyzerVersion:
        """Return the version recorded in parser outputs."""
        ...

    @property
    def supported_media_types(self) -> frozenset[str]:
        """Return native report media types accepted by this parser."""
        ...

    def parse(self, artifact: NativeArtifact, content: BinaryIO, /) -> ParseResult:
        """Parse an already bounded stream without closing the supplied stream."""
        ...


@runtime_checkable
class FindingNormalizer(Protocol[NormalizedFindingT_co, NormalizationEventT_co]):
    """Behavioral port for native-to-canonical finding normalization."""

    @property
    def analyzer_id(self) -> AnalyzerId:
        """Return the analyzer identity accepted by this normalizer."""
        ...

    @property
    def normalizer_version(self) -> AnalyzerVersion:
        """Return the version recorded in normalization events."""
        ...

    def normalize(
        self,
        findings: tuple[NativeFinding, ...],
        /,
    ) -> NormalizationBatch[NormalizedFindingT_co, NormalizationEventT_co]:
        """Normalize an immutable batch and return findings with trace events."""
        ...


__all__: Final[tuple[str, ...]] = (
    "CONTRACT_SCHEMA_VERSION",
    "Analyzer",
    "AnalyzerCapability",
    "AnalyzerDescriptor",
    "AnalyzerExecutionStatus",
    "AnalyzerHealth",
    "AnalyzerHealthStatus",
    "AnalyzerId",
    "AnalyzerLifecycleStatus",
    "AnalyzerVersion",
    "ContentDigest",
    "DiagnosticSeverity",
    "EnvironmentVariable",
    "ExecutionRequest",
    "ExecutionResult",
    "FindingNormalizer",
    "MountAccess",
    "MountDescriptor",
    "MountRole",
    "NativeArtifact",
    "NativeArtifactKind",
    "NativeFinding",
    "NativeLocation",
    "NativeReportParser",
    "NormalizationBatch",
    "ParseResult",
    "ParserDiagnostic",
    "ResourceLimits",
    "ResourceUsage",
    "SchemaVersion",
    "SecretReference",
)
