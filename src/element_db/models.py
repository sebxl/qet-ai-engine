"""Data models for QET element database."""

from __future__ import annotations

import math
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Terminal:
    """A connection point on a QET element."""

    uuid: str
    name: str
    x: float
    y: float
    orientation: str  # n, s, e, w
    type: str  # Generic, etc.


@dataclass(frozen=True)
class GraphicPrimitive:
    """A drawing primitive (line, rect, ellipse, etc.) within an element."""

    type: str
    attributes: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class KindInformations:
    """Element kind metadata (coil, protection, simple contact, terminal, etc.)."""

    type: str
    state: str | None = None
    number: int | None = None
    function: str | None = None
    max_slaves: int | None = None


@dataclass
class ElementRecord:
    """A parsed QET element file record."""

    path: str
    uuid: str
    names: dict[str, str]
    width: int
    height: int
    hotspot_x: int
    hotspot_y: int
    link_type: str
    kind_informations: KindInformations | None
    terminals: list[Terminal]
    graphic_primitives: list[GraphicPrimitive]
    informations: str


def terminal_absolute_position(
    terminal: Terminal,
    element_x: float,
    element_y: float,
    orientation: int,
) -> tuple[float, float]:
    """Calculate absolute position of a terminal on a folio.

    Uses the rotation matrix:
        angle = orientation * 90 degrees
        abs_x = element_x + (terminal.x * cos(angle) - terminal.y * sin(angle))
        abs_y = element_y + (terminal.x * sin(angle) + terminal.y * cos(angle))

    Args:
        terminal: The terminal with local x, y coordinates.
        element_x: Element X position on folio.
        element_y: Element Y position on folio.
        orientation: 0=0deg, 1=90deg, 2=180deg, 3=270deg.

    Returns:
        Tuple of (absolute_x, absolute_y).
    """
    angle = math.radians(orientation * 90)
    cos_a = math.cos(angle)
    sin_a = math.sin(angle)
    abs_x = element_x + (terminal.x * cos_a - terminal.y * sin_a)
    abs_y = element_y + (terminal.x * sin_a + terminal.y * cos_a)
    return abs_x, abs_y
