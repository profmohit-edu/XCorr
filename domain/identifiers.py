"""Strongly typed content-addressed identifiers for the XCorr domain.

XCorr represents persistent identities as algorithm-qualified lowercase
SHA-256 digests. Distinct root-model subclasses prevent identifiers from being
interchanged accidentally while preserving a canonical JSON string form.
Identifier construction and digest calculation remain responsibilities of the
canonical serialization and hashing adapters; this module only defines strict,
immutable value contracts.
"""

from __future__ import annotations

from typing import Annotated, Final

from pydantic import ConfigDict, RootModel, StringConstraints

_SHA256_IDENTIFIER_LENGTH: Final[int] = 71
_SHA256_IDENTIFIER_PATTERN: Final[str] = r"^sha256:[0-9a-f]{64}$"

_Sha256IdentifierValue = Annotated[
    str,
    StringConstraints(
        min_length=_SHA256_IDENTIFIER_LENGTH,
        max_length=_SHA256_IDENTIFIER_LENGTH,
        pattern=_SHA256_IDENTIFIER_PATTERN,
    ),
]


class Sha256Identifier(RootModel[_Sha256IdentifierValue]):
    """Reusable base for an algorithm-qualified SHA-256 domain identifier.

    Accepted values contain the literal ``sha256:`` prefix followed by exactly
    64 lowercase hexadecimal characters. Strict validation rejects coercion,
    surrounding whitespace, uppercase hexadecimal, bare digests, and values
    produced by another hashing algorithm. The frozen root model is safe to
    share across immutable domain records and serializes as a JSON string.

    The base validates identities but does not calculate them. Producers must
    hash the canonical bytes prescribed for the relevant identifier subtype.
    """

    model_config = ConfigDict(
        frozen=True,
        strict=True,
        validate_default=True,
        revalidate_instances="always",
    )


class ExperimentSpecificationId(Sha256Identifier):
    """Identity of a fully materialized experiment specification.

    The digest input comprises canonical effective configuration, the dataset
    manifest digest, source revision, analyzer descriptors, analyzer image
    digests, and correlation and evaluation policy versions. Ephemeral
    timestamps and host-specific paths are excluded from that input.
    """


class RunId(Sha256Identifier):
    """Identity of one declared replicate of an experiment specification.

    The digest input combines an :class:`ExperimentSpecificationId` with the
    explicit non-negative replicate index. Reusing the same specification and
    replicate index identifies the same immutable run and never authorizes an
    overwrite.
    """


class ArtifactId(Sha256Identifier):
    """Identity of an immutable, schema-versioned research artifact.

    The digest input combines the exact artifact bytes with the identifier of
    the schema governing those bytes. Recorded timestamps, filesystem paths,
    and other execution-local metadata do not affect artifact identity.
    """


class FindingId(Sha256Identifier):
    """Identity of one canonical analyzer finding.

    The digest input comprises analyzer identity, target identity, a stable
    native finding identity when available, canonical source ranges, native
    rule identity, and the native evidence digest. Native and normalized
    attributes remain distinguishable in the records referenced by this ID.
    """


class DecisionId(Sha256Identifier):
    """Identity of an immutable pairwise correlation decision.

    The digest input comprises the two finding identifiers in canonical order,
    the signal-set version, and the decision-policy version. Presentation text,
    completion order, and wall-clock metadata do not affect this identity.
    """


class GroupId(Sha256Identifier):
    """Identity of a deterministic correlation group.

    The digest input comprises lexically sorted member finding identifiers and
    the grouping-policy version. Pair traversal order and runtime concurrency
    are excluded.
    """


class TargetId(Sha256Identifier):
    """Identity of a verified smart-contract analysis target.

    The digest input is the canonical target descriptor, including dataset
    identity, normalized repository-relative source path, contract identity,
    compiler metadata, and the exact source-content digest. Absolute host paths
    and file modification times are excluded.
    """


class DatasetId(Sha256Identifier):
    """Identity of a versioned, provenance-tracked dataset manifest.

    The digest input is the canonical dataset manifest, including declared
    identity, version, source entries, selection criteria, preprocessing
    lineage, access metadata, and file digests. Download locations and local
    cache paths do not affect the identity.
    """


class ExecutionRequestId(Sha256Identifier):
    """Identity of one fully materialized analyzer execution request.

    The digest input comprises the run identity, analyzer descriptor, ordered
    targets, effective non-secret tool configuration, argument vector, mount
    descriptors, and resource policy. Secret values and runtime observations
    are excluded.
    """


__all__: Final[tuple[str, ...]] = (
    "ArtifactId",
    "DatasetId",
    "DecisionId",
    "ExecutionRequestId",
    "ExperimentSpecificationId",
    "FindingId",
    "GroupId",
    "RunId",
    "Sha256Identifier",
    "TargetId",
)
