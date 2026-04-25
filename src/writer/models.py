"""Data models for the QET XML Writer."""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4


def generate_uuid() -> str:
    """Generate a QET-style UUID: {xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx}."""
    return "{" + str(uuid4()) + "}"


@dataclass
class PlacedTerminal:
    """A terminal as placed on a folio (with numeric orientation and legacy ID)."""

    uuid: str
    name: str
    id: int
    x: float
    y: float
    orientation: int  # 0=n, 1=e, 2=s, 3=w


@dataclass
class DynamicText:
    """A dynamic text label attached to a placed element."""

    uuid: str
    x: float
    y: float
    z: float
    text: str
    text_from: str
    info_name: str
    font: str


@dataclass
class PlacedElement:
    """An element placed on a folio."""

    uuid: str
    elmt_path: str  # common:// path
    x: float
    y: float
    z: float
    orientation: int
    designation: str
    prefix: str
    terminals: list[PlacedTerminal]
    dynamic_texts: list[DynamicText]
    links_uuids: list[str]
    element_informations: dict[str, str]


@dataclass
class Conductor:
    """A wire connecting two terminals."""

    terminal1_uuid: str
    terminal2_uuid: str
    element1_uuid: str
    element2_uuid: str
    terminal1_id: int
    terminal2_id: int
    terminal1_name: str
    terminal2_name: str
    element1_label: str
    element2_label: str
    label: str


@dataclass
class Folio:
    """A diagram sheet (page) in a QET project."""

    title: str
    order: int
    elements: list[PlacedElement] = field(default_factory=list)
    conductors: list[Conductor] = field(default_factory=list)


@dataclass
class QETProject:
    """Top-level QET project."""

    title: str
    author: str = ""
    version: str = "0.90"
    folios: list[Folio] = field(default_factory=list)
