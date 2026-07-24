"""Canonical, immutable source-location value models for XCorr.

The models in this module represent locations without reading source files,
consulting clocks, or resolving host paths. Byte offsets use half-open ranges
over exact UTF-8 source bytes. Canonical line projections use one-based lines
and zero-based Unicode code-point columns, while individual coordinates retain
explicit base metadata so native coordinate conventions cannot be mistaken for
canonical coordinates.
"""

from __future__ import annotations

from enum import IntEnum, StrEnum
from pathlib import PurePosixPath
from typing import Final, Literal, Self

from pydantic import (
    BaseModel,
    ConfigDict,
    NonNegativeInt,
    field_validator,
    model_validator,
)

from domain.identifiers import Sha256Identifier

SOURCE_LOCATION_SCHEMA_VERSION: Final[str] = "1.0.0"


class ColumnBase(IntEnum):
    """Numeric origin used by a source coordinate's column component.

    XCorr's canonical projection uses :attr:`ZERO`. :attr:`ONE` exists so an
    integration can represent an external coordinate explicitly before it is
    normalized, without applying an implicit offset.
    """

    ZERO = 0
    ONE = 1


class CoordinateSystem(StrEnum):
    """Coordinate representations carried by a :class:`SourceLocation`.

    ``BYTE_OFFSET_AND_LINE_COLUMN`` records both an authoritative byte range
    and its human-readable line/column projection. Consistency between those
    representations is verified against separately supplied source bytes by a
    higher-level integrity service; this file-independent model records both
    without performing input/output.
    """

    BYTE_OFFSET = "byte_offset"
    BYTE_OFFSET_AND_LINE_COLUMN = "byte_offset_and_line_column"
    LINE_COLUMN = "line_column"


class LineBase(IntEnum):
    """Numeric origin used by a source coordinate's line component.

    XCorr's canonical projection uses :attr:`ONE`. :attr:`ZERO` supports an
    explicit representation of native zero-based coordinates before canonical
    normalization.
    """

    ZERO = 0
    ONE = 1


class _FrozenLocationModel(BaseModel):
    """Strict configuration shared by persisted source-location records."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        strict=True,
        validate_default=True,
        revalidate_instances="always",
    )

    schema_version: Literal["1.0.0"] = SOURCE_LOCATION_SCHEMA_VERSION


class SourceCoordinate(_FrozenLocationModel):
    """One explicit line-and-column coordinate.

    A coordinate includes its line and column bases as data. Values must be at
    least their respective bases: zero is invalid for a one-based component.
    The model does not convert between bases because conversion belongs at the
    analyzer-normalization boundary.
    """

    line: NonNegativeInt
    column: NonNegativeInt
    line_base: LineBase
    column_base: ColumnBase

    @model_validator(mode="after")
    def validate_coordinate_bases(self) -> Self:
        """Reject component values below their explicitly declared bases."""
        if self.line < int(self.line_base):
            message = "line must be greater than or equal to its declared line base"
            raise ValueError(message)
        if self.column < int(self.column_base):
            message = "column must be greater than or equal to its declared column base"
            raise ValueError(message)
        return self


class ByteRange(_FrozenLocationModel):
    """Half-open byte interval over exact UTF-8 source content.

    ``start_byte`` is inclusive and ``end_byte`` is exclusive. Equal endpoints
    represent a valid zero-width point location. Offsets are always zero-based,
    independent of line and column conventions.
    """

    start_byte: NonNegativeInt
    end_byte: NonNegativeInt

    @model_validator(mode="after")
    def validate_byte_order(self) -> Self:
        """Require the exclusive endpoint to follow the inclusive endpoint."""
        if self.end_byte < self.start_byte:
            message = "end_byte must be greater than or equal to start_byte"
            raise ValueError(message)
        return self


class SourceRange(_FrozenLocationModel):
    """Canonical half-open range expressed as line and column coordinates.

    Both endpoints must use XCorr's canonical coordinate convention: one-based
    lines and zero-based Unicode code-point columns. ``start`` is inclusive and
    ``end`` is exclusive. Equal endpoints represent a point location.
    """

    start: SourceCoordinate
    end: SourceCoordinate

    @model_validator(mode="after")
    def validate_canonical_range(self) -> Self:
        """Enforce shared canonical bases and nondecreasing endpoint order."""
        if self.start.line_base is not self.end.line_base:
            message = "source-range endpoints must use the same line base"
            raise ValueError(message)
        if self.start.column_base is not self.end.column_base:
            message = "source-range endpoints must use the same column base"
            raise ValueError(message)
        if self.start.line_base is not LineBase.ONE:
            message = "canonical source ranges require one-based lines"
            raise ValueError(message)
        if self.start.column_base is not ColumnBase.ZERO:
            message = "canonical source ranges require zero-based columns"
            raise ValueError(message)
        if (self.end.line, self.end.column) < (self.start.line, self.start.column):
            message = "source-range end must not precede its start"
            raise ValueError(message)
        return self


class SourceLocation(_FrozenLocationModel):
    """Canonical source identity, relative path, and explicit location ranges.

    ``source_digest`` binds the location to exact source bytes.
    ``repository_relative_path`` is a normalized POSIX path and is never
    resolved against the host filesystem by this model. ``coordinate_system``
    declares which range fields are present, preventing absent byte or
    line/column data from being interpreted implicitly.
    """

    source_digest: Sha256Identifier
    repository_relative_path: str
    coordinate_system: CoordinateSystem
    byte_range: ByteRange | None = None
    source_range: SourceRange | None = None

    @field_validator("repository_relative_path")
    @classmethod
    def validate_repository_relative_path(cls, value: str) -> str:
        """Require a normalized, traversal-free repository-relative POSIX path."""
        if not value:
            message = "repository_relative_path must not be empty"
            raise ValueError(message)
        if "\x00" in value:
            message = "repository_relative_path must not contain a null byte"
            raise ValueError(message)
        if "\\" in value:
            message = "repository_relative_path must use POSIX separators"
            raise ValueError(message)
        if len(value) >= 2 and value[1] == ":":
            message = "repository_relative_path must not be a drive-qualified path"
            raise ValueError(message)

        segments = value.split("/")
        if any(segment in {"", ".", ".."} for segment in segments):
            message = "repository_relative_path must be normalized and traversal-free"
            raise ValueError(message)

        path = PurePosixPath(value)
        if path.is_absolute() or path.as_posix() != value:
            message = "repository_relative_path must be a normalized relative POSIX path"
            raise ValueError(message)
        return value

    @model_validator(mode="after")
    def validate_coordinate_system(self) -> Self:
        """Require range presence to match the declared coordinate system exactly."""
        has_bytes = self.byte_range is not None
        has_lines = self.source_range is not None

        if self.coordinate_system is CoordinateSystem.BYTE_OFFSET:
            if not has_bytes or has_lines:
                message = "byte_offset locations require only byte_range"
                raise ValueError(message)
        elif self.coordinate_system is CoordinateSystem.LINE_COLUMN:
            if has_bytes or not has_lines:
                message = "line_column locations require only source_range"
                raise ValueError(message)
        elif not has_bytes or not has_lines:
            message = (
                "byte_offset_and_line_column locations require both byte_range "
                "and source_range"
            )
            raise ValueError(message)
        return self


__all__: Final[tuple[str, ...]] = (
    "ByteRange",
    "ColumnBase",
    "CoordinateSystem",
    "LineBase",
    "SOURCE_LOCATION_SCHEMA_VERSION",
    "SourceCoordinate",
    "SourceLocation",
    "SourceRange",
)
