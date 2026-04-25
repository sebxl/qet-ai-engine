"""Integration / acceptance tests for the QET XML Writer (QET-2).

Acceptance criteria:
AC-1: create_project + add_folio + place_element + save -> valid .qet XML
AC-2: connect two elements -> conductor with correct UUIDs and legacy IDs
AC-3: link_master_slave -> bidirectional links_uuids in XML
AC-4: Output file opens in QElectroTech without errors (manual, but we verify XML structure)
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from src.element_db.models import ElementRecord, KindInformations, Terminal
from src.writer.qet_writer import QETWriter


class TestAcceptanceCriteria:
    """End-to-end acceptance tests for QET-2."""

    @pytest.fixture(autouse=True)
    def setup(self, fake_element_db, coil_element_record, slave_element_record, tmp_path):
        self.coil_path = coil_element_record.path
        self.slave_path = slave_element_record.path

        counter = iter(range(1000))
        self.writer = QETWriter(
            element_db=fake_element_db,
            uuid_factory=lambda: "{" + f"ac-uuid-{next(counter):04d}" + "}",
        )

        self.project = self.writer.create_project("AC Test Project")
        self.folio = self.writer.add_folio(self.project, "AC Test Folio")

        self.coil = self.writer.place_element(
            self.folio, self.coil_path, 280, 200, "K1",
        )
        self.contact = self.writer.place_element(
            self.folio, self.slave_path, 400, 300, "K1-13",
        )

        self.conductor = self.writer.connect(
            self.folio, self.coil, "A2", self.contact, "", "",
        )
        self.writer.link_master_slave(self.coil, self.contact)

        self.filepath = tmp_path / "acceptance.qet"
        self.writer.save(self.project, self.filepath)
        self.content = self.filepath.read_text(encoding="utf-8")
        xml_body = self.content.split("\n", 1)[1]
        self.root = ET.fromstring(xml_body)

    # ── AC-1: create + place + save -> valid .qet ──────────────────────

    def test_ac1_file_is_valid_xml(self):
        """AC-1: The saved file must be well-formed XML."""
        xml_body = self.content.split("\n", 1)[1]
        ET.fromstring(xml_body)

    def test_ac1_has_xml_declaration(self):
        assert self.content.startswith('<?xml version="1.0" encoding="UTF-8"?>')

    def test_ac1_root_project_element(self):
        assert self.root.tag == "project"
        assert self.root.attrib["title"] == "AC Test Project"
        assert self.root.attrib["version"] == "0.90"

    def test_ac1_structure_properties_newdiagrams_diagram_collection(self):
        children = [child.tag for child in self.root]
        assert "properties" in children
        assert "newdiagrams" in children
        assert "diagram" in children
        assert "collection" in children

    def test_ac1_elements_placed_in_diagram(self):
        elements = self.root.findall("diagram/elements/element")
        assert len(elements) == 2

    def test_ac1_element_paths_use_common(self):
        elements = self.root.findall("diagram/elements/element")
        for elem in elements:
            assert elem.attrib["type"].startswith("common://")

    def test_ac1_element_has_terminals(self):
        elements = self.root.findall("diagram/elements/element")
        for elem in elements:
            terminals = elem.findall("terminals/terminal")
            assert len(terminals) >= 2

    def test_ac1_element_has_element_informations(self):
        elem = self.root.findall("diagram/elements/element")[0]
        label = elem.find("elementInformations/elementInformation[@name='label']")
        assert label is not None
        assert label.text == "K1"

    def test_ac1_element_has_dynamic_text(self):
        elem = self.root.findall("diagram/elements/element")[0]
        dt = elem.find("dynamic_texts/dynamic_elmt_text")
        assert dt is not None
        assert dt.find("text").text == "K1"

    # ── AC-2: connect -> conductor with correct UUIDs and IDs ──────────

    def test_ac2_conductor_in_xml(self):
        conductors = self.root.findall("diagram/conductors/conductor")
        assert len(conductors) == 1

    def test_ac2_conductor_references_correct_elements(self):
        c = self.root.find("diagram/conductors/conductor")
        elements = self.root.findall("diagram/elements/element")
        elem_uuids = {e.attrib["uuid"] for e in elements}
        assert c.attrib["element1"] in elem_uuids
        assert c.attrib["element2"] in elem_uuids

    def test_ac2_conductor_references_correct_terminals(self):
        c = self.root.find("diagram/conductors/conductor")
        all_terminal_uuids = set()
        for elem in self.root.findall("diagram/elements/element"):
            for t in elem.findall("terminals/terminal"):
                all_terminal_uuids.add(t.attrib["uuid"])
        assert c.attrib["terminal1"] in all_terminal_uuids
        assert c.attrib["terminal2"] in all_terminal_uuids

    def test_ac2_conductor_terminal_names(self):
        c = self.root.find("diagram/conductors/conductor")
        assert c.attrib["terminalname1"] == "A2"
        assert c.attrib["terminalname2"] == ""

    def test_ac2_conductor_element_labels(self):
        c = self.root.find("diagram/conductors/conductor")
        assert c.attrib["element1_label"] == "K1"
        assert c.attrib["element2_label"] == "K1-13"

    def test_ac2_conductor_has_sequential_numbers(self):
        c = self.root.find("diagram/conductors/conductor")
        assert c.find("sequentialNumbers") is not None

    # ── AC-3: link_master_slave -> bidirectional links_uuids ───────────

    def test_ac3_master_has_links_uuids(self):
        elements = self.root.findall("diagram/elements/element")
        master_elem = elements[0]
        links = master_elem.findall("links_uuids/link_uuid")
        assert len(links) == 1

    def test_ac3_slave_has_links_uuids(self):
        elements = self.root.findall("diagram/elements/element")
        slave_elem = elements[1]
        links = slave_elem.findall("links_uuids/link_uuid")
        assert len(links) == 1

    def test_ac3_bidirectional(self):
        elements = self.root.findall("diagram/elements/element")
        master_uuid = elements[0].attrib["uuid"]
        slave_uuid = elements[1].attrib["uuid"]
        master_link = elements[0].find("links_uuids/link_uuid").attrib["uuid"]
        slave_link = elements[1].find("links_uuids/link_uuid").attrib["uuid"]
        assert master_link == slave_uuid
        assert slave_link == master_uuid

    # ── AC-4: Output structural validity (proxy for QET opening) ───────

    def test_ac4_diagram_has_correct_dimensions(self):
        d = self.root.find("diagram")
        assert d.attrib["cols"] == "17"
        assert d.attrib["colsize"] == "60"
        assert d.attrib["rows"] == "8"
        assert d.attrib["rowsize"] == "80"
        assert d.attrib["height"] == "660"

    def test_ac4_newdiagrams_has_all_required_children(self):
        nd = self.root.find("newdiagrams")
        required = {"border", "inset", "conductors", "report", "xrefs",
                     "conductors_autonums", "folio_autonums", "element_autonums"}
        children = {child.tag for child in nd}
        assert required.issubset(children)

    def test_ac4_no_embed_paths(self):
        """common:// paths only, no embedded element data."""
        assert "embed://" not in self.content

    def test_ac4_collection_is_empty(self):
        coll = self.root.find("collection")
        assert coll is not None
        assert len(list(coll)) == 0
