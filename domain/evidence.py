"""Immutable, provenance-aware evidence models for XCorr.

Evidence is retained as structured data linked to immutable artifacts. A raw
evidence record remains separate from an observation that interprets it as
supporting, contradicting, or neutral for a particular correlation context.
Scores and weights use bounded decimal values so persisted representations do
not depend on binary floating-point behavior.
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
    NonNegativeInt,
    StringConstraints,
    field_validator,
    model_validator,
)

from domain.enums import ArtifactFormat, ArtifactType, EvidenceType
from domain.identifiers import ArtifactId, FindingId, Sha256Identifier, TargetId
from domain.source_location import SourceLocation

EVIDENCE_SCHEMA_VERSION: Final[str] = "1.0.0"

EvidenceDirection = Literal["contradicting", "neutral", "supporting"]
_NonEmptyText = Annotated[str, StringConstraints(min_length=1, max_length=16_384)]
_ShortText = Annotated[str, StringConstraints(min_length=1, max_length=512)]
_UnitInterval = Annotated[
    Decimal,
    Field(
        ge=Decimal("0"),
        le=Decimal("1"),
        allow_inf_nan=False,
    ),
]


class _FrozenEvidenceModel(BaseModel):
    """Strict configuration shared by persisted evidence records."""

    model_config = ConfigDict(
        allow_inf_nan=False,
        extra="forbid",
        frozen=True,
        strict=True,
        validate_default=True,
        revalidate_instances="always",
    )

    schema_version: Literal["1.0.0"] = EVIDENCE_SCHEMA_VERSION


class EvidenceReference(_FrozenEvidenceModel):
    """Immutable pointer from evidence to its exact source artifact.

    ``artifact_id`` is mandatory, so even whole-artifact evidence has durable
    provenance. Optional locators narrow the reference to a record, JSON value,
    finding, target, or canonical source location. ``reference_id`` identifies
    the complete canonical reference rather than only the underlying artifact.
    """

    reference_id: Sha256Identifier
    artifact_id: ArtifactId
    artifact_type: ArtifactType
    artifact_format: ArtifactFormat
    record_digest: Sha256Identifier | None = None
    record_index: NonNegativeInt | None = None
    json_pointer: str | None = None
    finding_id: FindingId | None = None
    target_id: TargetId | None = None
    source_location: SourceLocation | None = None

    @field_validator("json_pointer")
    @classmethod
    def validate_json_pointer(cls, value: str | None) -> str | None:
        """Require a non-empty JSON Pointer to begin with a slash."""
        if value is not None and value != "" and not value.startswith("/"):
            message = "json_pointer must be empty or begin with '/'"
            raise ValueError(message)
        return value


class EvidenceWeight(_FrozenEvidenceModel):
    """Versioned policy weight assigned to one evidence observation.

    ``value`` is a non-negative unit-interval magnitude. Direction is recorded
    by :class:`EvidenceObservation`, never encoded in the sign of a weight.
    Policy identity and version preserve the provenance of the assigned value.
    """

    value: _UnitInterval
    policy_id: _ShortText
    policy_version: _ShortText


class EvidenceScore(_FrozenEvidenceModel):
    """Versioned normalized score measured for an evidence observation.

    ``value`` lies in the closed unit interval. ``scale_id`` and
    ``scale_version`` identify its semantics; equal numeric values from
    different scales are therefore not assumed to be interchangeable.
    ``calibrated`` states whether a registered calibration procedure produced
    the value.
    """

    value: _UnitInterval
    scale_id: _ShortText
    scale_version: _ShortText
    calibrated: bool


class Evidence(_FrozenEvidenceModel):
    """Canonical evidence with mandatory production and artifact provenance.

    The structured payload contains evidence-specific values while
    ``evidence_type`` supplies the stable semantic category. At least one
    artifact reference is required. References and source finding identifiers
    are unique and lexically ordered to preserve canonical serialization.
    """

    evidence_id: Sha256Identifier
    evidence_type: EvidenceType
    summary: _NonEmptyText
    producer_id: _ShortText
    producer_version: _ShortText
    references: Annotated[tuple[EvidenceReference, ...], Field(min_length=1)]
    source_finding_ids: tuple[FindingId, ...] = ()
    payload: Mapping[str, JsonValue] = Field(default_factory=dict)
    reliability: Mapping[str, JsonValue] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_canonical_provenance(self) -> Self:
        """Require unique, canonically ordered references and finding IDs."""
        reference_ids = tuple(reference.reference_id.root for reference in self.references)
        if len(reference_ids) != len(set(reference_ids)):
            message = "evidence references must have unique reference identifiers"
            raise ValueError(message)
        if reference_ids != tuple(sorted(reference_ids)):
            message = "evidence references must be ordered by reference identifier"
            raise ValueError(message)

        finding_ids = tuple(finding_id.root for finding_id in self.source_finding_ids)
        if len(finding_ids) != len(set(finding_ids)):
            message = "source_finding_ids must be unique"
            raise ValueError(message)
        if finding_ids != tuple(sorted(finding_ids)):
            message = "source_finding_ids must be lexically ordered"
            raise ValueError(message)
        return self


class EvidenceObservation(_FrozenEvidenceModel):
    """Versioned interpretation of canonical evidence in one context.

    Direction explicitly distinguishes supporting, contradicting, and neutral
    evidence. Neutral observations carry a zero score so they cannot acquire an
    implicit direction through a nonzero magnitude. The embedded
    :class:`Evidence` retains complete artifact and production provenance;
    observer identity and version preserve the additional interpretation step.
    """

    observation_id: Sha256Identifier
    evidence: Evidence
    direction: EvidenceDirection
    score: EvidenceScore
    weight: EvidenceWeight
    observer_id: _ShortText
    observer_version: _ShortText
    rationale_codes: tuple[_ShortText, ...]
    metadata: Mapping[str, JsonValue] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_observation(self) -> Self:
        """Enforce neutral scoring and canonical rationale-code ordering."""
        if self.direction == "neutral" and self.score.value != Decimal("0"):
            message = "neutral evidence observations require a zero score"
            raise ValueError(message)

        if len(self.rationale_codes) != len(set(self.rationale_codes)):
            message = "rationale_codes must be unique"
            raise ValueError(message)
        if self.rationale_codes != tuple(sorted(self.rationale_codes)):
            message = "rationale_codes must be lexically ordered"
            raise ValueError(message)
        return self


class EvidenceCollection(_FrozenEvidenceModel):
    """Canonical evidence observations associated with one finding context.

    A collection may be empty to preserve an explicit absence of available
    evidence. Its subject finding identifiers and observations are unique and
    lexically ordered. Collection provenance records which component and
    version assembled the immutable view; each contained observation retains
    its own interpretation and source-artifact provenance.
    """

    collection_id: Sha256Identifier
    subject_finding_ids: Annotated[tuple[FindingId, ...], Field(min_length=1)]
    observations: tuple[EvidenceObservation, ...] = ()
    collector_id: _ShortText
    collector_version: _ShortText
    metadata: Mapping[str, JsonValue] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_canonical_collection(self) -> Self:
        """Require canonical subject and observation identity ordering."""
        finding_ids = tuple(finding_id.root for finding_id in self.subject_finding_ids)
        if len(finding_ids) != len(set(finding_ids)):
            message = "subject_finding_ids must be unique"
            raise ValueError(message)
        if finding_ids != tuple(sorted(finding_ids)):
            message = "subject_finding_ids must be lexically ordered"
            raise ValueError(message)

        observation_ids = tuple(
            observation.observation_id.root for observation in self.observations
        )
        if len(observation_ids) != len(set(observation_ids)):
            message = "evidence observations must have unique observation identifiers"
            raise ValueError(message)
        if observation_ids != tuple(sorted(observation_ids)):
            message = "evidence observations must be ordered by observation identifier"
            raise ValueError(message)

        evidence_ids = tuple(
            observation.evidence.evidence_id.root for observation in self.observations
        )
        if len(evidence_ids) != len(set(evidence_ids)):
            message = "an evidence item may occur only once in a collection"
            raise ValueError(message)
        return self


__all__: Final[tuple[str, ...]] = (
    "EVIDENCE_SCHEMA_VERSION",
    "Evidence",
    "EvidenceCollection",
    "EvidenceDirection",
    "EvidenceObservation",
    "EvidenceReference",
    "EvidenceScore",
    "EvidenceWeight",
)
