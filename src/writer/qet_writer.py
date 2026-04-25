"""QET XML Writer -- builds and saves .qet project files."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Callable

from src.element_db.models import ElementRecord

from .models import (
    Conductor,
    DynamicText,
    Folio,
    PlacedElement,
    PlacedTerminal,
    QETProject,
    generate_uuid,
)

ORIENTATION_MAP = {"n": 0, "e": 1, "s": 2, "w": 3}

DEFAULT_FONT = "Liberation Sans,9,-1,5,50,0,0,0,0,0,Regular"


def _extract_prefix(designation: str) -> str:
    """Extract the letter prefix from a designation like 'K1' -> 'K', 'KM1' -> 'KM'."""
    match = re.match(r"^([A-Za-z]+)", designation)
    return match.group(1) if match else ""


def _format_coord(value: float) -> str:
    """Format a coordinate: whole numbers as int, otherwise float."""
    if value == int(value):
        return str(int(value))
    return str(value)


class QETWriter:
    """Builds QET project structures and serialises them to .qet XML."""

    def __init__(
        self,
        element_db: dict[str, ElementRecord] | None = None,
        uuid_factory: Callable[[], str] | None = None,
    ) -> None:
        self._element_db = element_db or {}
        self._uuid = uuid_factory or generate_uuid
        self._terminal_id_counters: dict[int, int] = {}

    def _next_terminal_id(self, folio: Folio) -> int:
        folio_id = id(folio)
        current = self._terminal_id_counters.get(folio_id, 0)
        self._terminal_id_counters[folio_id] = current + 1
        return current

    def create_project(self, title: str, author: str = "") -> QETProject:
        return QETProject(title=title)

    def add_folio(self, project: QETProject, title: str) -> Folio:
        order = len(project.folios) + 1
        folio = Folio(title=title, order=order)
        project.folios.append(folio)
        return folio

    def place_element(
        self,
        folio: Folio,
        elmt_path: str,
        x: float,
        y: float,
        designation: str,
        orientation: int = 0,
    ) -> PlacedElement:
        record = self._element_db[elmt_path]

        placed_terminals = []
        for t in record.terminals:
            pt = PlacedTerminal(
                uuid=self._uuid(),
                name=t.name,
                id=self._next_terminal_id(folio),
                x=t.x,
                y=t.y,
                orientation=ORIENTATION_MAP.get(t.orientation, 0),
            )
            placed_terminals.append(pt)

        element_uuid = self._uuid()
        prefix = _extract_prefix(designation)

        dt = DynamicText(
            uuid=self._uuid(),
            x=25.0,
            y=-9.17,
            z=6.0,
            text=designation,
            text_from="ElementInfo",
            info_name="label",
            font=DEFAULT_FONT,
        )

        pe = PlacedElement(
            uuid=element_uuid,
            elmt_path="common://" + elmt_path,
            x=float(x),
            y=float(y),
            z=10.0,
            orientation=orientation,
            designation=designation,
            prefix=prefix,
            terminals=placed_terminals,
            dynamic_texts=[dt],
            links_uuids=[],
            element_informations={"label": designation},
        )

        folio.elements.append(pe)
        return pe

    def connect(
        self,
        folio: Folio,
        elem1: PlacedElement,
        terminal1_name: str,
        elem2: PlacedElement,
        terminal2_name: str,
        label: str = "",
    ) -> Conductor:
        t1 = self._find_terminal(elem1, terminal1_name)
        t2 = self._find_terminal(elem2, terminal2_name)

        conductor = Conductor(
            terminal1_uuid=t1.uuid,
            terminal2_uuid=t2.uuid,
            element1_uuid=elem1.uuid,
            element2_uuid=elem2.uuid,
            terminal1_id=t1.id,
            terminal2_id=t2.id,
            terminal1_name=t1.name,
            terminal2_name=t2.name,
            element1_label=elem1.designation,
            element2_label=elem2.designation,
            label=label,
        )

        folio.conductors.append(conductor)
        return conductor

    def link_master_slave(self, master: PlacedElement, slave: PlacedElement) -> None:
        master.links_uuids.append(slave.uuid)
        slave.links_uuids.append(master.uuid)

    def save(self, project: QETProject, filepath: str | Path) -> None:
        root = self._build_xml(project)
        tree_str = self._serialize_xml(root)
        Path(filepath).write_text(tree_str, encoding="utf-8")

    # ── XML construction ───────────────────────────────────────────────

    def _build_xml(self, project: QETProject) -> ET.Element:
        root = ET.Element("project", title=project.title, version=project.version)

        ET.SubElement(root, "properties")
        self._build_newdiagrams(root)

        for folio in project.folios:
            self._build_diagram(root, folio)

        ET.SubElement(root, "collection")
        return root

    def _build_newdiagrams(self, root: ET.Element) -> None:
        nd = ET.SubElement(root, "newdiagrams")

        ET.SubElement(nd, "border", cols="17", colsize="60", rows="8", rowsize="80",
                       displaycols="true", displayrows="true")
        ET.SubElement(nd, "inset", displayAt="bottom", title="", author="",
                       folio="%id/%total", date="", filename="", plant="",
                       locmach="", indexrev="", version="")
        ET.SubElement(nd, "conductors", type="multi", condsize="1", num="",
                       formula="", displaytext="1", text_color="#000000",
                       numsize="9", **{"dash-size": "1"}, color2="#000000",
                       horizrotatetext="0", vertirotatetext="0",
                       **{"horizontal-alignment": "AlignBottom",
                          "vertical-alignment": "AlignRight"},
                       onetextperfolio="0", bicolor="false",
                       conductor_color="", cable="", bus="", function="",
                       conductor_section="", tension_protocol="")
        ET.SubElement(nd, "report", label="%f-%l%c")

        xrefs = ET.SubElement(nd, "xrefs")
        for xtype in ("coil", "protection", "commutator"):
            ET.SubElement(xrefs, "xref", type=xtype,
                           master_label="%f-%l%c", slave_label="(%f-%l%c)")

        ET.SubElement(nd, "conductors_autonums", current_autonum="",
                       freeze_new_conductors="false")
        ET.SubElement(nd, "folio_autonums")
        ET.SubElement(nd, "element_autonums", current_autonum="",
                       freeze_new_elements="false")

    def _build_diagram(self, root: ET.Element, folio: Folio) -> None:
        diagram = ET.SubElement(
            root, "diagram",
            title=folio.title, author="", version="0.90",
            order=str(folio.order), date="", folio="%id/%total",
            rows="8", rowsize="80", cols="17", colsize="60",
            displayrows="true", displaycols="true",
            displayAt="bottom", height="660",
            freezeNewElement="false", freezeNewConductor="false",
        )

        ET.SubElement(diagram, "defaultconductor",
                       type="multi", condsize="1", num="", formula="",
                       displaytext="1", text_color="#000000", numsize="9",
                       **{"dash-size": "1"}, color2="#000000",
                       horizrotatetext="0", vertirotatetext="0",
                       **{"horizontal-alignment": "AlignBottom",
                          "vertical-alignment": "AlignRight"},
                       onetextperfolio="0", bicolor="false")

        elements_node = ET.SubElement(diagram, "elements")
        for pe in folio.elements:
            self._build_element(elements_node, pe)

        conductors_node = ET.SubElement(diagram, "conductors")
        for cond in folio.conductors:
            self._build_conductor(conductors_node, cond)

        ET.SubElement(diagram, "inputs")

    def _build_element(self, parent: ET.Element, pe: PlacedElement) -> None:
        elem = ET.SubElement(
            parent, "element",
            type=pe.elmt_path, uuid=pe.uuid,
            x=_format_coord(pe.x), y=_format_coord(pe.y),
            z=_format_coord(pe.z), orientation=str(pe.orientation),
            prefix=pe.prefix, freezeLabel="false",
        )

        terminals_node = ET.SubElement(elem, "terminals")
        for pt in pe.terminals:
            ET.SubElement(
                terminals_node, "terminal",
                x=_format_coord(pt.x), y=_format_coord(pt.y),
                orientation=str(pt.orientation),
                id=str(pt.id), uuid=pt.uuid,
            )

        ET.SubElement(elem, "inputs")

        ei_node = ET.SubElement(elem, "elementInformations")
        for name, value in pe.element_informations.items():
            info_el = ET.SubElement(ei_node, "elementInformation", show="1", name=name)
            info_el.text = value

        dt_node = ET.SubElement(elem, "dynamic_texts")
        for dt in pe.dynamic_texts:
            dyn = ET.SubElement(
                dt_node, "dynamic_elmt_text",
                x=_format_coord(dt.x), y=str(dt.y),
                z=_format_coord(dt.z), rotation="0",
                uuid=dt.uuid, Halignment="AlignLeft", Valignment="AlignTop",
                font=dt.font, text_width="-1", frame="false",
                keep_visual_rotation="false", text_from=dt.text_from,
            )
            text_el = ET.SubElement(dyn, "text")
            text_el.text = dt.text
            info_el = ET.SubElement(dyn, "info_name")
            info_el.text = dt.info_name

        ET.SubElement(elem, "texts_groups")

        if pe.links_uuids:
            links_node = ET.SubElement(elem, "links_uuids")
            for link_uuid in pe.links_uuids:
                ET.SubElement(links_node, "link_uuid", uuid=link_uuid)

    def _build_conductor(self, parent: ET.Element, cond: Conductor) -> None:
        c = ET.SubElement(
            parent, "conductor",
            terminal1=cond.terminal1_uuid, terminal2=cond.terminal2_uuid,
            element1=cond.element1_uuid, element2=cond.element2_uuid,
            element1_label=cond.element1_label,
            element2_label=cond.element2_label,
            element1_name="", element2_name="",
            terminalname1=cond.terminal1_name,
            terminalname2=cond.terminal2_name,
            x="0", y="0",
            type="multi", condsize="1", num="", formula="",
            displaytext="1", text_color="#000000", numsize="9",
            color="#000000", color2="#000000", bicolor="false",
            **{"dash-size": "1"}, freezeLabel="false",
            horizrotatetext="0", vertirotatetext="0",
            **{"horizontal-alignment": "AlignBottom",
               "vertical-alignment": "AlignRight"},
            onetextperfolio="0", cable="", bus="", function="",
            conductor_color="", conductor_section="", tension_protocol="",
        )
        ET.SubElement(c, "sequentialNumbers")

    def _serialize_xml(self, root: ET.Element) -> str:
        ET.indent(root, space="    ")
        raw = ET.tostring(root, encoding="unicode")
        return '<?xml version="1.0" encoding="UTF-8"?>\n' + raw + "\n"

    # ── Helpers ────────────────────────────────────────────────────────

    @staticmethod
    def _find_terminal(element: PlacedElement, name: str) -> PlacedTerminal:
        for t in element.terminals:
            if t.name == name:
                return t
        raise ValueError(
            f"Terminal '{name}' not found on element '{element.designation}'. "
            f"Available: {[t.name for t in element.terminals]}"
        )
