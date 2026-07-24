"""Immutable canonical vulnerability-finding models for XCorr.

A canonical finding preserves analyzer execution provenance, native identity,
normalization trace, taxonomy mapping, exact source locations, structured
evidence, and explicit relationships. Collections enforce deterministic lexical
ordering so serialization does not depend on parser completion order or runtime
concurrency.
"""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal
from typing import Annotated, Final, Literal, Self

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    JsonValue,
    StringConstraints,
    model_validator,
)

from domain.enums import (
    FindingConfidence,
    FindingSeverity,
    FindingSource,
    FindingStatus,
    NormalizationStatus,
)
from domain.evidence import EvidenceCollection
from domain.identifiers import (
    ArtifactId,
    DatasetId,
    ExecutionRequestId,
    FindingId,
    RunId,
    Sha256Identifier,
    TargetId,
)
from domain.source_location import SourceLocation

FINDING_SCHEMA_VERSION: Final[str] = "1.0.0"

FindingRelationshipType = Literal[
    "causes",
    "duplicate_of",
    "related_to",
    "same_underlying_defect",
    "supersedes",
]
_NonEmptyText = Annotated[str, StringConstraints(min_length=1, max_length=16_384)]
_ShortText = Annotated[str, StringConstraints(min_length=1, max_length=512)]
_MappingConfidence = Annotated[
    Decimal,
    Field(
        ge=Decimal("0"),
        le=Decimal("1"),
        allow_inf_nan=False,
    ),
]


class _FrozenFindingModel(BaseModel):
    """Strict configuration shared by persisted finding records."""

    model_config = ConfigDict(
        allow_inf_nan=False,
        extra="forbid",
        frozen=True,
        strict=True,
        validate_default=True,
        revalidate_instances="always",
    )

    schema_version: Literal["1.0.0"] = FINDING_SCHEMA_VERSION


class FindingIdentity(_FrozenFindingModel):
    """Strongly typed identities that anchor one canonical finding.

    ``finding_id`` identifies the complete canonical finding content.
    ``target_id`` binds it to one verified analysis target, and ``dataset_id``
    binds the target to its immutable dataset manifest.
    """

    finding_id: FindingId
    target_id: TargetId
    dataset_id: DatasetId


class FindingMetadata(_FrozenFindingModel):
    """Analyzer, execution, native-record, and normalization provenance.

    At least one native artifact and normalization event are required. Artifact
    and event identifiers are unique and lexically ordered. Version values are
    preserved exactly as integration metadata and are not interpreted here.
    """

    title: _ShortText
    description: str
    status: FindingStatus
    source: FindingSource
    analyzer_id: _ShortText
    analyzer_descriptor_id: Sha256Identifier
    adapter_version: _ShortText
    tool_version: _ShortText
    parser_version: _ShortText
    normalizer_version: _ShortText
    execution_request_id: ExecutionRequestId
    native_artifact_ids: Annotated[tuple[ArtifactId, ...], Field(min_length=1)]
    native_record_digest: Sha256Identifier
    native_rule_id: _NonEmptyText
    native_finding_id: _NonEmptyText | None = None
    normalization_event_ids: Annotated[
        tuple[Sha256Identifier, ...],
        Field(min_length=1),
    ]
    properties: Mapping[str, JsonValue] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_canonical_provenance(self) -> Self:
        """Require unique and lexically ordered provenance identifiers."""
        artifact_ids = tuple(artifact_id.root for artifact_id in self.native_artifact_ids)
        if len(artifact_ids) != len(set(artifact_ids)):
            message = "native_artifact_ids must be unique"
            raise ValueError(message)
        if artifact_ids != tuple(sorted(artifact_ids)):
            message = "native_artifact_ids must be lexically ordered"
            raise ValueError(message)

        event_ids = tuple(event_id.root for event_id in self.normalization_event_ids)
        if len(event_ids) != len(set(event_ids)):
            message = "normalization_event_ids must be unique"
            raise ValueError(message)
        if event_ids != tuple(sorted(event_ids)):
            message = "normalization_event_ids must be lexically ordered"
            raise ValueError(message)
        return self


class FindingClassification(_FrozenFindingModel):
    """Canonical severity, confidence, and versioned taxonomy mapping.

    Native classification is always retained. A mapped classification requires
    a canonical class identifier and mapping confidence. ``UNMAPPED`` and
    ``REJECTED`` classifications retain the attempted mapping identity but must
    not contain a guessed canonical class or confidence.
    """

    severity: FindingSeverity
    confidence: FindingConfidence
    taxonomy_id: _ShortText
    taxonomy_version: _ShortText
    canonical_class_id: _ShortText | None
    native_class_id: _NonEmptyText
    mapping_id: _ShortText
    mapping_version: _ShortText
    mapping_status: NormalizationStatus
    mapping_confidence: _MappingConfidence | None

    @model_validator(mode="after")
    def validate_taxonomy_mapping(self) -> Self:
        """Keep mapped and unmapped taxonomy states internally consistent."""
        is_unmapped = self.mapping_status in {
            NormalizationStatus.REJECTED,
            NormalizationStatus.UNMAPPED,
        }
        if is_unmapped:
            if self.canonical_class_id is not None or self.mapping_confidence is not None:
                message = (
                    "unmapped or rejected classifications cannot contain a canonical "
                    "class or mapping confidence"
                )
                raise ValueError(message)
        elif self.canonical_class_id is None or self.mapping_confidence is None:
            message = "mapped classifications require a canonical class and confidence"
            raise ValueError(message)
        return self


class FindingRelationship(_FrozenFindingModel):
    """Provenance-linked directed relationship between two findings.

    A relationship is stored on its source finding and points to a distinct
    target finding. At least one canonical evidence identifier supports the
    relationship. Evidence identifiers are unique and lexically ordered.
    """

    relationship_id: Sha256Identifier
    source_finding_id: FindingId
    target_finding_id: FindingId
    relationship_type: FindingRelationshipType
    evidence_ids: Annotated[tuple[Sha256Identifier, ...], Field(min_length=1)]
    producer_id: _ShortText
    producer_version: _ShortText
    properties: Mapping[str, JsonValue] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_relationship(self) -> Self:
        """Reject self-relations and noncanonical evidence identifier lists."""
        if self.source_finding_id == self.target_finding_id:
            message = "a finding relationship must connect two distinct findings"
            raise ValueError(message)

        evidence_ids = tuple(evidence_id.root for evidence_id in self.evidence_ids)
        if len(evidence_ids) != len(set(evidence_ids)):
            message = "relationship evidence_ids must be unique"
            raise ValueError(message)
        if evidence_ids != tuple(sorted(evidence_ids)):
            message = "relationship evidence_ids must be lexically ordered"
            raise ValueError(message)
        return self


class Finding(_FrozenFindingModel):
    """Complete immutable canonical smart-contract vulnerability finding.

    The aggregate embeds its identity, analyzer provenance, classification,
    source locations, evidence collection, and outgoing relationships. Every
    location is bound to exact source bytes. Every relationship references
    evidence present in the finding's own evidence collection.
    """

    identity: FindingIdentity
    metadata: FindingMetadata
    classification: FindingClassification
    locations: Annotated[tuple[SourceLocation, ...], Field(min_length=1)]
    evidence: EvidenceCollection
    relationships: tuple[FindingRelationship, ...] = ()

    @model_validator(mode="after")
    def validate_aggregate(self) -> Self:
        """Enforce evidence ownership, location order, and relationship integrity."""
        finding_id = self.identity.finding_id
        if self.evidence.subject_finding_ids != (finding_id,):
            message = "finding evidence must identify only the owning finding"
            raise ValueError(message)
        if not self.evidence.observations:
            message = "a canonical finding must preserve at least one evidence observation"
            raise ValueError(message)

        location_keys = tuple(self._location_key(location) for location in self.locations)
        if len(location_keys) != len(set(location_keys)):
            message = "finding locations must be unique"
            raise ValueError(message)
        if location_keys != tuple(sorted(location_keys)):
            message = "finding locations must be canonically ordered"
            raise ValueError(message)

        relationship_ids = tuple(
            relationship.relationship_id.root for relationship in self.relationships
        )
        if len(relationship_ids) != len(set(relationship_ids)):
            message = "finding relationships must have unique identifiers"
            raise ValueError(message)
        if relationship_ids != tuple(sorted(relationship_ids)):
            message = "finding relationships must be ordered by relationship identifier"
            raise ValueError(message)

        available_evidence_ids = {
            observation.evidence.evidence_id.root for observation in self.evidence.observations
        }
        for relationship in self.relationships:
            if relationship.source_finding_id != finding_id:
                message = "relationships must be stored on their source finding"
                raise ValueError(message)
            relationship_evidence_ids = {
                evidence_id.root for evidence_id in relationship.evidence_ids
            }
            if not relationship_evidence_ids.issubset(available_evidence_ids):
                message = "relationship evidence must exist in the finding evidence collection"
                raise ValueError(message)
        return self

    @staticmethod
    def _location_key(
        location: SourceLocation,
    ) -> tuple[str, str, int, int, int, int, int, int]:
        """Return a total-order key from already validated location fields."""
        byte_start = location.byte_range.start_byte if location.byte_range is not None else -1
        byte_end = location.byte_range.end_byte if location.byte_range is not None else -1
        line_start = location.source_range.start.line if location.source_range is not None else -1
        column_start = (
            location.source_range.start.column if location.source_range is not None else -1
        )
        line_end = location.source_range.end.line if location.source_range is not None else -1
        column_end = location.source_range.end.column if location.source_range is not None else -1
        return (
            location.repository_relative_path,
            location.source_digest.root,
            byte_start,
            byte_end,
            line_start,
            column_start,
            line_end,
            column_end,
        )


class FindingCollection(_FrozenFindingModel):
    """Deterministically ordered findings produced for one immutable run.

    Empty collections are valid and explicitly represent a run with no
    canonical findings. Nonempty collections require unique, lexically ordered
    finding identifiers, consistent dataset identity, and relationships whose
    endpoints are present in the same collection.
    """

    collection_id: Sha256Identifier
    run_id: RunId
    dataset_id: DatasetId
    producer_id: _ShortText
    producer_version: _ShortText
    findings: tuple[Finding, ...] = ()
    properties: Mapping[str, JsonValue] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_collection(self) -> Self:
        """Enforce canonical ordering and collection-level referential integrity."""
        finding_ids = tuple(finding.identity.finding_id.root for finding in self.findings)
        if len(finding_ids) != len(set(finding_ids)):
            message = "finding collection identifiers must be unique"
            raise ValueError(message)
        if finding_ids != tuple(sorted(finding_ids)):
            message = "findings must be lexically ordered by finding identifier"
            raise ValueError(message)

        available_finding_ids = set(finding_ids)
        for finding in self.findings:
            if finding.identity.dataset_id != self.dataset_id:
                message = "every finding must belong to the collection dataset"
                raise ValueError(message)
            for relationship in finding.relationships:
                if relationship.target_finding_id.root not in available_finding_ids:
                    message = "relationship targets must exist in the finding collection"
                    raise ValueError(message)
        return self


__all__: Final[tuple[str, ...]] = (
    "FINDING_SCHEMA_VERSION",
    "Finding",
    "FindingClassification",
    "FindingCollection",
    "FindingIdentity",
    "FindingMetadata",
    "FindingRelationship",
    "FindingRelationshipType",
)
