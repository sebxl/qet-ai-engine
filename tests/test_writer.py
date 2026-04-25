"""Tests for the QET XML Writer module."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET

import pytest

from src.element_db.models import ElementRecord, KindInformations, Terminal
from src.writer.models import (
    Conductor,
    DynamicText,
    Folio,
    PlacedElement,
    PlacedTerminal,
    QETProject,
    generate_uuid,
)
from src.writer.qet_writer import QETWriter


# ── Phase 1: Data Models ───────────────────────────────────────────────


class TestGenerateUUID:
    """Tests for the generate_uuid helper."""

    def test_returns_string(self):
        assert isinstance(generate_uuid(), str)

    def test_has_curly_braces(self):
        uid = generate_uuid()
        assert uid.startswith("{")
        assert uid.endswith("}")

    def test_matches_qet_uuid_format(self):
        uid = generate_uuid()
        pattern = r"^\{[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\}$"
        assert re.match(pattern, uid), f"UUID {uid} does not match QET format"

    def test_generates_unique_values(self):
        uuids = {generate_uuid() for _ in range(100)}
        assert len(uuids) == 100


class TestQETProject:
    """Tests for the QETProject dataclass."""

    def test_create_with_title(self):
        p = QETProject(title="Test Project")
        assert p.title == "Test Project"
        assert p.version == "0.90"
        assert p.folios == []

    def test_default_version(self):
        p = QETProject(title="X")
        assert p.version == "0.90"

    def test_custom_version(self):
        p = QETProject(title="X", version="0.80")
        assert p.version == "0.80"


class TestFolio:
    """Tests for the Folio dataclass."""

    def test_create_folio(self):
        f = Folio(title="Main", order=1)
        assert f.title == "Main"
        assert f.order == 1
        assert f.elements == []
        assert f.conductors == []


class TestPlacedTerminal:
    """Tests for the PlacedTerminal dataclass."""

    def test_create_placed_terminal(self):
        pt = PlacedTerminal(
            uuid="{abc}", name="A1", id=0, x=0.0, y=-20.0, orientation=0,
        )
        assert pt.uuid == "{abc}"
        assert pt.name == "A1"
        assert pt.id == 0
        assert pt.x == 0.0
        assert pt.y == -20.0
        assert pt.orientation == 0


class TestDynamicText:
    """Tests for the DynamicText dataclass."""

    def test_create_dynamic_text(self):
        dt = DynamicText(
            uuid="{dt-1}", x=25.0, y=-9.17, z=6.0,
            text="K1", text_from="ElementInfo",
            info_name="label", font="Liberation Sans,9,-1,5,50,0,0,0,0,0,Regular",
        )
        assert dt.uuid == "{dt-1}"
        assert dt.text == "K1"
        assert dt.text_from == "ElementInfo"


class TestPlacedElement:
    """Tests for the PlacedElement dataclass."""

    def test_create_placed_element(self):
        pe = PlacedElement(
            uuid="{pe-1}",
            elmt_path="common://10_electric/coils/bobine3.elmt",
            x=280.0, y=200.0, z=10.0, orientation=0,
            designation="K1", prefix="K",
            terminals=[],
            dynamic_texts=[],
            links_uuids=[],
            element_informations={"label": "K1"},
        )
        assert pe.uuid == "{pe-1}"
        assert pe.elmt_path.startswith("common://")
        assert pe.designation == "K1"
        assert pe.z == 10.0
        assert pe.element_informations["label"] == "K1"


class TestConductor:
    """Tests for the Conductor dataclass."""

    def test_create_conductor(self):
        c = Conductor(
            terminal1_uuid="{t1}", terminal2_uuid="{t2}",
            element1_uuid="{e1}", element2_uuid="{e2}",
            terminal1_id=0, terminal2_id=1,
            terminal1_name="A1", terminal2_name="A2",
            element1_label="K1", element2_label="S1",
            label="W1",
        )
        assert c.terminal1_uuid == "{t1}"
        assert c.terminal2_uuid == "{t2}"
        assert c.element1_uuid == "{e1}"
        assert c.element2_uuid == "{e2}"
        assert c.terminal1_id == 0
        assert c.terminal2_id == 1
        assert c.label == "W1"


# ── Phase 2: QETWriter API Basics ──────────────────────────────────────


class TestCreateProject:
    """Tests for QETWriter.create_project()."""

    def test_returns_qet_project(self, fake_element_db):
        w = QETWriter(element_db=fake_element_db)
        p = w.create_project("Motor Control")
        assert isinstance(p, QETProject)

    def test_project_title(self, fake_element_db):
        w = QETWriter(element_db=fake_element_db)
        p = w.create_project("Motor Control")
        assert p.title == "Motor Control"

    def test_project_version_default(self, fake_element_db):
        w = QETWriter(element_db=fake_element_db)
        p = w.create_project("X")
        assert p.version == "0.90"

    def test_project_starts_with_no_folios(self, fake_element_db):
        w = QETWriter(element_db=fake_element_db)
        p = w.create_project("X")
        assert p.folios == []

    def test_project_author(self, fake_element_db):
        w = QETWriter(element_db=fake_element_db)
        p = w.create_project("X", author="Max Mustermann")
        assert p.author == "Max Mustermann"

    def test_project_author_default_empty(self, fake_element_db):
        w = QETWriter(element_db=fake_element_db)
        p = w.create_project("X")
        assert p.author == ""


class TestAddFolio:
    """Tests for QETWriter.add_folio()."""

    def test_returns_folio(self, fake_element_db):
        w = QETWriter(element_db=fake_element_db)
        p = w.create_project("X")
        f = w.add_folio(p, "Page 1")
        assert isinstance(f, Folio)

    def test_folio_title(self, fake_element_db):
        w = QETWriter(element_db=fake_element_db)
        p = w.create_project("X")
        f = w.add_folio(p, "Hauptstromkreis")
        assert f.title == "Hauptstromkreis"

    def test_folio_order_increments(self, fake_element_db):
        w = QETWriter(element_db=fake_element_db)
        p = w.create_project("X")
        f1 = w.add_folio(p, "Page 1")
        f2 = w.add_folio(p, "Page 2")
        assert f1.order == 1
        assert f2.order == 2

    def test_folio_added_to_project(self, fake_element_db):
        w = QETWriter(element_db=fake_element_db)
        p = w.create_project("X")
        f = w.add_folio(p, "Page 1")
        assert f in p.folios
        assert len(p.folios) == 1

    def test_folio_starts_empty(self, fake_element_db):
        w = QETWriter(element_db=fake_element_db)
        p = w.create_project("X")
        f = w.add_folio(p, "Page 1")
        assert f.elements == []
        assert f.conductors == []


# ── Phase 3: Element Placement ─────────────────────────────────────────


class TestPlaceElement:
    """Tests for QETWriter.place_element()."""

    @pytest.fixture(autouse=True)
    def setup(self, fake_element_db, coil_element_record):
        counter = iter(range(1000))
        self.writer = QETWriter(
            element_db=fake_element_db,
            uuid_factory=lambda: "{" + f"test-uuid-{next(counter):04d}" + "}",
        )
        self.project = self.writer.create_project("X")
        self.folio = self.writer.add_folio(self.project, "Page 1")
        self.coil_path = coil_element_record.path

    def test_returns_placed_element(self):
        pe = self.writer.place_element(self.folio, self.coil_path, 280, 200, "K1")
        assert isinstance(pe, PlacedElement)

    def test_element_uuid_generated(self):
        pe = self.writer.place_element(self.folio, self.coil_path, 280, 200, "K1")
        assert pe.uuid.startswith("{")
        assert pe.uuid.endswith("}")

    def test_element_path_has_common_prefix(self):
        pe = self.writer.place_element(self.folio, self.coil_path, 280, 200, "K1")
        assert pe.elmt_path == "common://" + self.coil_path

    def test_element_position(self):
        pe = self.writer.place_element(self.folio, self.coil_path, 280, 200, "K1")
        assert pe.x == 280.0
        assert pe.y == 200.0

    def test_element_z_default(self):
        pe = self.writer.place_element(self.folio, self.coil_path, 280, 200, "K1")
        assert pe.z == 10.0

    def test_element_orientation_default(self):
        pe = self.writer.place_element(self.folio, self.coil_path, 280, 200, "K1")
        assert pe.orientation == 0

    def test_element_orientation_custom(self):
        pe = self.writer.place_element(self.folio, self.coil_path, 280, 200, "K1", orientation=2)
        assert pe.orientation == 2

    def test_element_designation(self):
        pe = self.writer.place_element(self.folio, self.coil_path, 280, 200, "K1")
        assert pe.designation == "K1"

    def test_element_prefix_extracted(self):
        pe = self.writer.place_element(self.folio, self.coil_path, 280, 200, "K1")
        assert pe.prefix == "K"

    def test_element_prefix_multi_char(self):
        pe = self.writer.place_element(self.folio, self.coil_path, 280, 200, "KM1")
        assert pe.prefix == "KM"

    def test_terminals_copied_from_record(self):
        pe = self.writer.place_element(self.folio, self.coil_path, 280, 200, "K1")
        assert len(pe.terminals) == 2

    def test_terminal_names_preserved(self):
        pe = self.writer.place_element(self.folio, self.coil_path, 280, 200, "K1")
        names = {t.name for t in pe.terminals}
        assert "A1" in names
        assert "A2" in names

    def test_terminal_coordinates_preserved(self):
        pe = self.writer.place_element(self.folio, self.coil_path, 280, 200, "K1")
        a1 = next(t for t in pe.terminals if t.name == "A1")
        assert a1.x == 0.0
        assert a1.y == -20.0

    def test_terminal_orientation_mapped(self):
        pe = self.writer.place_element(self.folio, self.coil_path, 280, 200, "K1")
        a1 = next(t for t in pe.terminals if t.name == "A1")
        a2 = next(t for t in pe.terminals if t.name == "A2")
        assert a1.orientation == 0  # n -> 0
        assert a2.orientation == 2  # s -> 2

    def test_terminal_ids_incremental(self):
        pe = self.writer.place_element(self.folio, self.coil_path, 280, 200, "K1")
        ids = [t.id for t in pe.terminals]
        assert ids == [0, 1]

    def test_terminal_ids_continue_across_elements(self, slave_element_record):
        self.writer.place_element(self.folio, self.coil_path, 280, 200, "K1")
        pe2 = self.writer.place_element(
            self.folio, slave_element_record.path, 400, 200, "K1-13",
        )
        ids = [t.id for t in pe2.terminals]
        assert ids == [2, 3]

    def test_terminal_uuids_generated(self):
        pe = self.writer.place_element(self.folio, self.coil_path, 280, 200, "K1")
        for t in pe.terminals:
            assert t.uuid.startswith("{")
            assert t.uuid.endswith("}")

    def test_element_added_to_folio(self):
        pe = self.writer.place_element(self.folio, self.coil_path, 280, 200, "K1")
        assert pe in self.folio.elements
        assert len(self.folio.elements) == 1

    def test_element_informations_label(self):
        pe = self.writer.place_element(self.folio, self.coil_path, 280, 200, "K1")
        assert pe.element_informations["label"] == "K1"

    def test_dynamic_text_created(self):
        pe = self.writer.place_element(self.folio, self.coil_path, 280, 200, "K1")
        assert len(pe.dynamic_texts) == 1
        dt = pe.dynamic_texts[0]
        assert dt.text == "K1"
        assert dt.text_from == "ElementInfo"
        assert dt.info_name == "label"

    def test_links_uuids_initially_empty(self):
        pe = self.writer.place_element(self.folio, self.coil_path, 280, 200, "K1")
        assert pe.links_uuids == []

    def test_unknown_element_raises_key_error(self):
        with pytest.raises(KeyError):
            self.writer.place_element(self.folio, "nonexistent.elmt", 0, 0, "X1")


# ── Phase 4: Conductor Connection ──────────────────────────────────────


class TestConnect:
    """Tests for QETWriter.connect()."""

    @pytest.fixture(autouse=True)
    def setup(self, fake_element_db, coil_element_record, slave_element_record):
        counter = iter(range(1000))
        self.writer = QETWriter(
            element_db=fake_element_db,
            uuid_factory=lambda: "{" + f"test-uuid-{next(counter):04d}" + "}",
        )
        self.project = self.writer.create_project("X")
        self.folio = self.writer.add_folio(self.project, "Page 1")
        self.coil = self.writer.place_element(
            self.folio, coil_element_record.path, 280, 200, "K1",
        )
        self.contact = self.writer.place_element(
            self.folio, slave_element_record.path, 400, 200, "K1-13",
        )

    def test_returns_conductor(self):
        c = self.writer.connect(self.folio, self.coil, "A2", self.contact, "", "")
        assert isinstance(c, Conductor)

    def test_conductor_terminal_uuids(self):
        c = self.writer.connect(self.folio, self.coil, "A2", self.contact, "", "")
        a2 = next(t for t in self.coil.terminals if t.name == "A2")
        contact_top = self.contact.terminals[0]
        assert c.terminal1_uuid == a2.uuid
        assert c.terminal2_uuid == contact_top.uuid

    def test_conductor_element_uuids(self):
        c = self.writer.connect(self.folio, self.coil, "A2", self.contact, "", "")
        assert c.element1_uuid == self.coil.uuid
        assert c.element2_uuid == self.contact.uuid

    def test_conductor_terminal_ids(self):
        c = self.writer.connect(self.folio, self.coil, "A2", self.contact, "", "")
        a2 = next(t for t in self.coil.terminals if t.name == "A2")
        contact_top = self.contact.terminals[0]
        assert c.terminal1_id == a2.id
        assert c.terminal2_id == contact_top.id

    def test_conductor_terminal_names(self):
        c = self.writer.connect(self.folio, self.coil, "A2", self.contact, "", "")
        assert c.terminal1_name == "A2"
        assert c.terminal2_name == ""

    def test_conductor_element_labels(self):
        c = self.writer.connect(self.folio, self.coil, "A2", self.contact, "", "")
        assert c.element1_label == "K1"
        assert c.element2_label == "K1-13"

    def test_conductor_label(self):
        c = self.writer.connect(self.folio, self.coil, "A1", self.contact, "", "W1")
        assert c.label == "W1"

    def test_conductor_added_to_folio(self):
        c = self.writer.connect(self.folio, self.coil, "A2", self.contact, "", "")
        assert c in self.folio.conductors
        assert len(self.folio.conductors) == 1

    def test_invalid_terminal_name_raises(self):
        with pytest.raises(ValueError, match="Terminal.*not found"):
            self.writer.connect(self.folio, self.coil, "BOGUS", self.contact, "", "")

    def test_connect_by_empty_name_uses_first_match(self):
        """When terminal name is '' and element has '' terminals, match by index."""
        c = self.writer.connect(self.folio, self.contact, "", self.coil, "A1", "")
        assert c.terminal1_uuid == self.contact.terminals[0].uuid


# ── Phase 5: Master/Slave Linking ──────────────────────────────────────


class TestLinkMasterSlave:
    """Tests for QETWriter.link_master_slave()."""

    @pytest.fixture(autouse=True)
    def setup(self, fake_element_db, coil_element_record, slave_element_record):
        counter = iter(range(1000))
        self.writer = QETWriter(
            element_db=fake_element_db,
            uuid_factory=lambda: "{" + f"test-uuid-{next(counter):04d}" + "}",
        )
        self.project = self.writer.create_project("X")
        self.folio = self.writer.add_folio(self.project, "Page 1")
        self.master = self.writer.place_element(
            self.folio, coil_element_record.path, 280, 200, "K1",
        )
        self.slave = self.writer.place_element(
            self.folio, slave_element_record.path, 400, 200, "K1-13",
        )

    def test_master_links_to_slave(self):
        self.writer.link_master_slave(self.master, self.slave)
        assert self.slave.uuid in self.master.links_uuids

    def test_slave_links_to_master(self):
        self.writer.link_master_slave(self.master, self.slave)
        assert self.master.uuid in self.slave.links_uuids

    def test_bidirectional_linking(self):
        self.writer.link_master_slave(self.master, self.slave)
        assert len(self.master.links_uuids) == 1
        assert len(self.slave.links_uuids) == 1

    def test_multiple_slaves(self, slave_element_record):
        slave2 = self.writer.place_element(
            self.folio, slave_element_record.path, 500, 200, "K1-14",
        )
        self.writer.link_master_slave(self.master, self.slave)
        self.writer.link_master_slave(self.master, slave2)
        assert len(self.master.links_uuids) == 2
        assert self.slave.uuid in self.master.links_uuids
        assert slave2.uuid in self.master.links_uuids


# ── Phase 6: XML Serialization (save) ─────────────────────────────────


class TestSave:
    """Tests for QETWriter.save() XML output."""

    @pytest.fixture(autouse=True)
    def setup(self, fake_element_db, coil_element_record, slave_element_record, tmp_path):
        counter = iter(range(1000))
        self.writer = QETWriter(
            element_db=fake_element_db,
            uuid_factory=lambda: "{" + f"test-uuid-{next(counter):04d}" + "}",
        )
        self.project = self.writer.create_project("Motor Control")
        self.folio = self.writer.add_folio(self.project, "Hauptstromkreis")
        self.coil = self.writer.place_element(
            self.folio, coil_element_record.path, 280, 200, "K1",
        )
        self.contact = self.writer.place_element(
            self.folio, slave_element_record.path, 400, 200, "K1-13",
        )
        self.writer.connect(self.folio, self.coil, "A2", self.contact, "", "")
        self.writer.link_master_slave(self.coil, self.contact)
        self.filepath = tmp_path / "test_output.qet"
        self.writer.save(self.project, self.filepath)
        self.content = self.filepath.read_text(encoding="utf-8")
        self.root = ET.fromstring(self.content.split("\n", 1)[1])

    def test_file_created(self):
        assert self.filepath.exists()

    def test_xml_declaration(self):
        assert self.content.startswith('<?xml version="1.0" encoding="UTF-8"?>')

    def test_root_is_project(self):
        assert self.root.tag == "project"

    def test_project_title(self):
        assert self.root.attrib["title"] == "Motor Control"

    def test_project_version(self):
        assert self.root.attrib["version"] == "0.90"

    def test_properties_present(self):
        assert self.root.find("properties") is not None

    def test_newdiagrams_present(self):
        nd = self.root.find("newdiagrams")
        assert nd is not None

    def test_newdiagrams_border(self):
        border = self.root.find("newdiagrams/border")
        assert border is not None
        assert border.attrib["cols"] == "17"
        assert border.attrib["colsize"] == "60"
        assert border.attrib["rows"] == "8"
        assert border.attrib["rowsize"] == "80"

    def test_newdiagrams_inset(self):
        inset = self.root.find("newdiagrams/inset")
        assert inset is not None
        assert inset.attrib["folio"] == "%id/%total"

    def test_newdiagrams_conductors(self):
        cond = self.root.find("newdiagrams/conductors")
        assert cond is not None
        assert cond.attrib["type"] == "multi"

    def test_newdiagrams_report(self):
        report = self.root.find("newdiagrams/report")
        assert report is not None
        assert report.attrib["label"] == "%f-%l%c"

    def test_newdiagrams_xrefs(self):
        xrefs = self.root.findall("newdiagrams/xrefs/xref")
        assert len(xrefs) == 3
        types = {x.attrib["type"] for x in xrefs}
        assert types == {"coil", "protection", "commutator"}

    def test_newdiagrams_conductors_autonums(self):
        ca = self.root.find("newdiagrams/conductors_autonums")
        assert ca is not None
        assert ca.attrib["freeze_new_conductors"] == "false"

    def test_newdiagrams_folio_autonums(self):
        assert self.root.find("newdiagrams/folio_autonums") is not None

    def test_newdiagrams_element_autonums(self):
        ea = self.root.find("newdiagrams/element_autonums")
        assert ea is not None
        assert ea.attrib["freeze_new_elements"] == "false"

    def test_diagram_present(self):
        diagrams = self.root.findall("diagram")
        assert len(diagrams) == 1

    def test_diagram_title(self):
        d = self.root.find("diagram")
        assert d.attrib["title"] == "Hauptstromkreis"

    def test_diagram_order(self):
        d = self.root.find("diagram")
        assert d.attrib["order"] == "1"

    def test_diagram_dimensions(self):
        d = self.root.find("diagram")
        assert d.attrib["cols"] == "17"
        assert d.attrib["colsize"] == "60"
        assert d.attrib["rows"] == "8"
        assert d.attrib["rowsize"] == "80"
        assert d.attrib["height"] == "660"

    def test_diagram_default_conductor(self):
        dc = self.root.find("diagram/defaultconductor")
        assert dc is not None
        assert dc.attrib["type"] == "multi"

    def test_elements_present(self):
        elems = self.root.findall("diagram/elements/element")
        assert len(elems) == 2

    def test_element_type_common_prefix(self):
        elems = self.root.findall("diagram/elements/element")
        for e in elems:
            assert e.attrib["type"].startswith("common://")

    def test_element_no_embed_prefix(self):
        elems = self.root.findall("diagram/elements/element")
        for e in elems:
            assert "embed://" not in e.attrib["type"]

    def test_element_attributes(self):
        elem = self.root.findall("diagram/elements/element")[0]
        assert "uuid" in elem.attrib
        assert "x" in elem.attrib
        assert "y" in elem.attrib
        assert "z" in elem.attrib
        assert elem.attrib["z"] == "10"
        assert "orientation" in elem.attrib
        assert elem.attrib["freezeLabel"] == "true"

    def test_element_position_formatting(self):
        elem = self.root.findall("diagram/elements/element")[0]
        assert elem.attrib["x"] == "280"
        assert elem.attrib["y"] == "200"

    def test_element_terminals(self):
        elem = self.root.findall("diagram/elements/element")[0]
        terminals = elem.findall("terminals/terminal")
        assert len(terminals) == 2

    def test_terminal_attributes(self):
        terminal = self.root.find("diagram/elements/element/terminals/terminal")
        assert "x" in terminal.attrib
        assert "y" in terminal.attrib
        assert "orientation" in terminal.attrib
        assert "id" in terminal.attrib
        assert "uuid" in terminal.attrib

    def test_element_inputs(self):
        elem = self.root.findall("diagram/elements/element")[0]
        assert elem.find("inputs") is not None

    def test_element_informations(self):
        elem = self.root.findall("diagram/elements/element")[0]
        ei = elem.find("elementInformations")
        assert ei is not None
        info = ei.find("elementInformation[@name='label']")
        assert info is not None
        assert info.text == "K1"
        assert info.attrib["show"] == "1"

    def test_dynamic_texts(self):
        elem = self.root.findall("diagram/elements/element")[0]
        dts = elem.findall("dynamic_texts/dynamic_elmt_text")
        assert len(dts) == 1
        dt = dts[0]
        assert dt.attrib["text_from"] == "ElementInfo"
        assert dt.attrib["Halignment"] == "AlignLeft"
        assert dt.find("text").text == "K1"
        assert dt.find("info_name").text == "label"

    def test_texts_groups(self):
        elem = self.root.findall("diagram/elements/element")[0]
        assert elem.find("texts_groups") is not None

    def test_links_uuids_present_on_linked_element(self):
        elem = self.root.findall("diagram/elements/element")[0]
        links = elem.findall("links_uuids/link_uuid")
        assert len(links) == 1
        assert "uuid" in links[0].attrib

    def test_links_uuids_bidirectional(self):
        elems = self.root.findall("diagram/elements/element")
        links0 = elems[0].findall("links_uuids/link_uuid")
        links1 = elems[1].findall("links_uuids/link_uuid")
        assert len(links0) == 1
        assert len(links1) == 1
        assert links0[0].attrib["uuid"] == elems[1].attrib["uuid"]
        assert links1[0].attrib["uuid"] == elems[0].attrib["uuid"]

    def test_conductor_present(self):
        conductors = self.root.findall("diagram/conductors/conductor")
        assert len(conductors) == 1

    def test_conductor_attributes(self):
        c = self.root.find("diagram/conductors/conductor")
        assert "terminal1" in c.attrib
        assert "terminal2" in c.attrib
        assert "element1" in c.attrib
        assert "element2" in c.attrib
        assert c.attrib["type"] == "multi"
        assert c.attrib["condsize"] == "1"
        assert c.attrib["bicolor"] == "false"
        assert c.attrib["freezeLabel"] == "false"

    def test_conductor_terminal_names_in_xml(self):
        c = self.root.find("diagram/conductors/conductor")
        assert c.attrib["terminalname1"] == "A2"
        assert c.attrib["terminalname2"] == ""

    def test_conductor_element_labels_in_xml(self):
        c = self.root.find("diagram/conductors/conductor")
        assert c.attrib["element1_label"] == "K1"
        assert c.attrib["element2_label"] == "K1-13"

    def test_conductor_sequential_numbers(self):
        c = self.root.find("diagram/conductors/conductor")
        assert c.find("sequentialNumbers") is not None

    def test_diagram_inputs(self):
        d = self.root.find("diagram")
        assert d.find("inputs") is not None

    def test_collection_present(self):
        assert self.root.find("collection") is not None

    def test_well_formed_xml(self):
        """The full content must be well-formed XML."""
        ET.fromstring(self.content.split("\n", 1)[1])


class TestSaveEmptyProject:
    """Tests for saving a project with no elements."""

    def test_save_empty_folio(self, fake_element_db, tmp_path):
        w = QETWriter(element_db=fake_element_db)
        p = w.create_project("Empty")
        w.add_folio(p, "Blank")
        fp = tmp_path / "empty.qet"
        w.save(p, fp)
        content = fp.read_text(encoding="utf-8")
        root = ET.fromstring(content.split("\n", 1)[1])
        assert root.find("diagram") is not None
        assert root.findall("diagram/elements/element") == []
        assert root.findall("diagram/conductors/conductor") == []

    def test_save_no_folios(self, fake_element_db, tmp_path):
        w = QETWriter(element_db=fake_element_db)
        p = w.create_project("NoPages")
        fp = tmp_path / "nopages.qet"
        w.save(p, fp)
        content = fp.read_text(encoding="utf-8")
        root = ET.fromstring(content.split("\n", 1)[1])
        assert root.findall("diagram") == []


class TestSaveNoLinks:
    """Elements without links should not have links_uuids node."""

    def test_no_links_uuids_when_empty(self, fake_element_db, coil_element_record, tmp_path):
        counter = iter(range(1000))
        w = QETWriter(
            element_db=fake_element_db,
            uuid_factory=lambda: "{" + f"test-uuid-{next(counter):04d}" + "}",
        )
        p = w.create_project("X")
        f = w.add_folio(p, "Page 1")
        w.place_element(f, coil_element_record.path, 280, 200, "K1")
        fp = tmp_path / "nolinks.qet"
        w.save(p, fp)
        content = fp.read_text(encoding="utf-8")
        root = ET.fromstring(content.split("\n", 1)[1])
        elem = root.find("diagram/elements/element")
        assert elem.find("links_uuids") is None


class TestSaveMultipleFolios:
    """Tests for saving a project with multiple folios."""

    def test_multiple_diagrams(self, fake_element_db, tmp_path):
        w = QETWriter(element_db=fake_element_db)
        p = w.create_project("Multi")
        w.add_folio(p, "Page 1")
        w.add_folio(p, "Page 2")
        w.add_folio(p, "Page 3")
        fp = tmp_path / "multi.qet"
        w.save(p, fp)
        content = fp.read_text(encoding="utf-8")
        root = ET.fromstring(content.split("\n", 1)[1])
        diagrams = root.findall("diagram")
        assert len(diagrams) == 3
        assert diagrams[0].attrib["order"] == "1"
        assert diagrams[1].attrib["order"] == "2"
        assert diagrams[2].attrib["order"] == "3"


class TestSaveAuthor:
    """Tests for author propagation into XML."""

    def test_author_in_diagram(self, fake_element_db, tmp_path):
        w = QETWriter(element_db=fake_element_db)
        p = w.create_project("Test", author="Max Mustermann")
        w.add_folio(p, "Folio 1")
        fp = tmp_path / "author.qet"
        w.save(p, fp)
        root = ET.fromstring(fp.read_text(encoding="utf-8").split("\n", 1)[1])
        assert root.find("diagram").attrib["author"] == "Max Mustermann"

    def test_author_in_inset(self, fake_element_db, tmp_path):
        w = QETWriter(element_db=fake_element_db)
        p = w.create_project("Test", author="Max Mustermann")
        w.add_folio(p, "Folio 1")
        fp = tmp_path / "author.qet"
        w.save(p, fp)
        root = ET.fromstring(fp.read_text(encoding="utf-8").split("\n", 1)[1])
        assert root.find("newdiagrams/inset").attrib["author"] == "Max Mustermann"

    def test_empty_author_default(self, fake_element_db, tmp_path):
        w = QETWriter(element_db=fake_element_db)
        p = w.create_project("Test")
        w.add_folio(p, "Folio 1")
        fp = tmp_path / "author.qet"
        w.save(p, fp)
        root = ET.fromstring(fp.read_text(encoding="utf-8").split("\n", 1)[1])
        assert root.find("diagram").attrib["author"] == ""


class TestSaveConductorLabel:
    """Tests for conductor label (num) in XML."""

    def test_conductor_label_in_xml(self, fake_element_db, coil_element_record, tmp_path):
        counter = iter(range(1000))
        w = QETWriter(
            element_db=fake_element_db,
            uuid_factory=lambda: "{" + f"uuid-{next(counter):04d}" + "}",
        )
        p = w.create_project("Test")
        f = w.add_folio(p, "Folio 1")
        e1 = w.place_element(f, coil_element_record.path, 100, 200, "K1")
        e2 = w.place_element(f, coil_element_record.path, 200, 200, "K2")
        w.connect(f, e1, "A2", e2, "A1", label="W1")
        fp = tmp_path / "label.qet"
        w.save(p, fp)
        root = ET.fromstring(fp.read_text(encoding="utf-8").split("\n", 1)[1])
        cond = root.find("diagram/conductors/conductor")
        assert cond.attrib["num"] == "W1"

    def test_conductor_empty_label(self, fake_element_db, coil_element_record, tmp_path):
        counter = iter(range(1000))
        w = QETWriter(
            element_db=fake_element_db,
            uuid_factory=lambda: "{" + f"uuid-{next(counter):04d}" + "}",
        )
        p = w.create_project("Test")
        f = w.add_folio(p, "Folio 1")
        e1 = w.place_element(f, coil_element_record.path, 100, 200, "K1")
        e2 = w.place_element(f, coil_element_record.path, 200, 200, "K2")
        w.connect(f, e1, "A2", e2, "A1")
        fp = tmp_path / "label.qet"
        w.save(p, fp)
        root = ET.fromstring(fp.read_text(encoding="utf-8").split("\n", 1)[1])
        cond = root.find("diagram/conductors/conductor")
        assert cond.attrib["num"] == ""
