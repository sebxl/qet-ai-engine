"""Parser for QElectroTech .elmt element files."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

from .models import ElementRecord, GraphicPrimitive, KindInformations, Terminal

# Tags that are recognized as graphic primitives in <description>.
_GRAPHIC_TAGS = frozenset({
    "line",
    "rect",
    "ellipse",
    "circle",
    "arc",
    "polygon",
    "text",
    "dynamic_text",
})


def parse_elmt_file(
    filepath: str | Path,
    relative_path: str = "",
) -> ElementRecord:
    """Parse a .elmt element file and return an ElementRecord.

    Args:
        filepath: Absolute or relative path to the .elmt file.
        relative_path: The path to store in the record (forward slashes,
            relative to the elements collection root).

    Returns:
        An ElementRecord with all parsed data.

    Raises:
        ET.ParseError: If the file is not valid XML.
        FileNotFoundError: If the file does not exist.
    """
    filepath = Path(filepath)
    tree = ET.parse(filepath)
    root = tree.getroot()

    # --- <definition> attributes ---
    uuid_elem = root.find("uuid")
    uuid = uuid_elem.get("uuid", "") if uuid_elem is not None else ""

    width = int(root.get("width", "0"))
    height = int(root.get("height", "0"))
    hotspot_x = int(root.get("hotspot_x", "0"))
    hotspot_y = int(root.get("hotspot_y", "0"))
    link_type = root.get("link_type", "simple")

    # --- <names> ---
    names: dict[str, str] = {}
    names_elem = root.find("names")
    if names_elem is not None:
        for name_elem in names_elem.findall("name"):
            lang = name_elem.get("lang", "")
            text = name_elem.text or ""
            if lang:
                names[lang] = text

    # --- <informations> ---
    info_elem = root.find("informations")
    informations = (info_elem.text or "") if info_elem is not None else ""

    # --- <kindInformations> ---
    kind_informations = _parse_kind_informations(root)

    # --- <description> children: terminals and graphic primitives ---
    terminals: list[Terminal] = []
    graphic_primitives: list[GraphicPrimitive] = []

    desc = root.find("description")
    if desc is not None:
        for child in desc:
            tag = child.tag
            if tag == "terminal":
                terminals.append(_parse_terminal(child))
            elif tag in _GRAPHIC_TAGS:
                graphic_primitives.append(
                    GraphicPrimitive(type=tag, attributes=dict(child.attrib))
                )

    return ElementRecord(
        path=relative_path,
        uuid=uuid,
        names=names,
        width=width,
        height=height,
        hotspot_x=hotspot_x,
        hotspot_y=hotspot_y,
        link_type=link_type,
        kind_informations=kind_informations,
        terminals=terminals,
        graphic_primitives=graphic_primitives,
        informations=informations,
    )


def _parse_terminal(elem: ET.Element) -> Terminal:
    """Parse a <terminal> XML element into a Terminal dataclass."""
    return Terminal(
        uuid=elem.get("uuid", ""),
        name=elem.get("name", ""),
        x=float(elem.get("x", "0")),
        y=float(elem.get("y", "0")),
        orientation=elem.get("orientation", "n"),
        type=elem.get("type", "Generic"),
    )


def _parse_kind_informations(root: ET.Element) -> KindInformations | None:
    """Parse <kindInformations> from the definition root."""
    ki_elem = root.find("kindInformations")
    if ki_elem is None:
        return None

    info_map: dict[str, str] = {}
    for ki_child in ki_elem.findall("kindInformation"):
        name = ki_child.get("name", "")
        value = ki_child.text or ""
        if name:
            info_map[name] = value

    if not info_map:
        return None

    ki_type = info_map.get("type", "")
    state = info_map.get("state")
    number_str = info_map.get("number")
    number = int(number_str) if number_str is not None else None
    function = info_map.get("function")
    max_slaves_str = info_map.get("max_slaves")
    max_slaves = int(max_slaves_str) if max_slaves_str is not None else None

    return KindInformations(
        type=ki_type,
        state=state,
        number=number,
        function=function,
        max_slaves=max_slaves,
    )
