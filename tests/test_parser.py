"""Tests for the .elmt file parser."""

import tempfile
from pathlib import Path

import pytest

from src.element_db.parser import parse_elmt_file


class TestParseBobine3:
    """Parse bobine3.elmt (coil, master link_type)."""

    @pytest.fixture(autouse=True)
    def parse(self, elements_dir, coil_elmt_path):
        self.rec = parse_elmt_file(
            elements_dir / coil_elmt_path, relative_path=coil_elmt_path
        )

    def test_uuid(self):
        assert self.rec.uuid == "{793302b1-e96a-f7f8-70bc-dec53eeaab5b}"

    def test_path_stored(self):
        assert self.rec.path == (
            "10_electric/10_allpole/310_relays_contactors_contacts/"
            "01_coils/bobine3.elmt"
        )

    def test_names_de(self):
        assert self.rec.names["de"] == "Spule"

    def test_names_en(self):
        assert self.rec.names["en"] == "Coil"

    def test_dimensions(self):
        assert self.rec.width == 40
        assert self.rec.height == 60

    def test_hotspot(self):
        assert self.rec.hotspot_x == 20
        assert self.rec.hotspot_y == 32

    def test_link_type_master(self):
        assert self.rec.link_type == "master"

    def test_kind_informations_coil(self):
        assert self.rec.kind_informations is not None
        assert self.rec.kind_informations.type == "coil"

    def test_terminal_count(self):
        assert len(self.rec.terminals) == 2

    def test_terminal_a1(self):
        a1 = next(t for t in self.rec.terminals if t.name == "A1")
        assert a1.x == 0.0
        assert a1.y == -20.0
        assert a1.orientation == "n"

    def test_terminal_a2(self):
        a2 = next(t for t in self.rec.terminals if t.name == "A2")
        assert a2.x == 0.0
        assert a2.y == 20.0
        assert a2.orientation == "s"

    def test_graphic_primitives_present(self):
        types = {p.type for p in self.rec.graphic_primitives}
        assert "rect" in types
        assert "line" in types
        assert "dynamic_text" in types

    def test_informations_contains_author(self):
        assert "Author" in self.rec.informations


class TestParseMoteurTri:
    """Parse moteur_tri.elmt (three-phase motor, simple link_type)."""

    @pytest.fixture(autouse=True)
    def parse(self, elements_dir, motor_tri_elmt_path):
        self.rec = parse_elmt_file(
            elements_dir / motor_tri_elmt_path, relative_path=motor_tri_elmt_path
        )

    def test_terminal_count(self):
        assert len(self.rec.terminals) == 4

    def test_terminal_names(self):
        names = {t.name for t in self.rec.terminals}
        assert names == {"U1", "V1", "W1", "PE"}

    def test_link_type_simple(self):
        assert self.rec.link_type == "simple"

    def test_dimensions(self):
        assert self.rec.width == 60
        assert self.rec.height == 60

    def test_no_kind_informations(self):
        # simple link_type without kindInformations element
        assert self.rec.kind_informations is None

    def test_primitives_include_ellipse(self):
        types = {p.type for p in self.rec.graphic_primitives}
        assert "ellipse" in types

    def test_primitives_include_arc(self):
        types = {p.type for p in self.rec.graphic_primitives}
        assert "arc" in types

    def test_primitives_include_polygon(self):
        types = {p.type for p in self.rec.graphic_primitives}
        assert "polygon" in types

    def test_primitives_include_text(self):
        types = {p.type for p in self.rec.graphic_primitives}
        assert "text" in types


class TestParseBreaker3f:
    """Parse dis_mag_term_3f-2.elmt (3-phase breaker, master)."""

    @pytest.fixture(autouse=True)
    def parse(self, elements_dir, breaker_3f_elmt_path):
        self.rec = parse_elmt_file(
            elements_dir / breaker_3f_elmt_path, relative_path=breaker_3f_elmt_path
        )

    def test_terminal_count(self):
        assert len(self.rec.terminals) == 6

    def test_terminal_names(self):
        names = sorted(t.name for t in self.rec.terminals)
        assert names == ["1", "2", "3", "4", "5", "6"]

    def test_link_type_master(self):
        assert self.rec.link_type == "master"

    def test_kind_informations_protection(self):
        assert self.rec.kind_informations is not None
        assert self.rec.kind_informations.type == "protection"


class TestParseConSimple:
    """Parse con_simple.elmt (slave contact)."""

    @pytest.fixture(autouse=True)
    def parse(self, elements_dir, slave_contact_elmt_path):
        self.rec = parse_elmt_file(
            elements_dir / slave_contact_elmt_path,
            relative_path=slave_contact_elmt_path,
        )

    def test_link_type_slave(self):
        assert self.rec.link_type == "slave"

    def test_kind_state_no(self):
        assert self.rec.kind_informations is not None
        assert self.rec.kind_informations.state == "NO"

    def test_kind_number(self):
        assert self.rec.kind_informations.number == 1

    def test_kind_type(self):
        assert self.rec.kind_informations.type == "simple"


class TestParseBorneContinuite:
    """Parse borne_continuite.elmt (terminal block)."""

    @pytest.fixture(autouse=True)
    def parse(self, elements_dir, terminal_block_elmt_path):
        self.rec = parse_elmt_file(
            elements_dir / terminal_block_elmt_path,
            relative_path=terminal_block_elmt_path,
        )

    def test_link_type_terminal(self):
        assert self.rec.link_type == "terminal"

    def test_kind_type_generic(self):
        assert self.rec.kind_informations is not None
        assert self.rec.kind_informations.type == "generic"

    def test_kind_function_generic(self):
        assert self.rec.kind_informations.function == "generic"


class TestParserEdgeCases:
    """Edge cases for the parser."""

    def test_element_with_no_terminals(self, tmp_path):
        elmt = tmp_path / "no_terminals.elmt"
        elmt.write_text(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<definition version="0.90" type="element" width="20" height="20"'
            ' hotspot_x="10" hotspot_y="10">\n'
            '  <uuid uuid="{00000000-0000-0000-0000-000000000000}"/>\n'
            "  <names><name lang=\"en\">Empty</name></names>\n"
            "  <informations></informations>\n"
            "  <description>\n"
            '    <line x1="0" y1="0" x2="10" y2="10"/>\n'
            "  </description>\n"
            "</definition>\n"
        )
        rec = parse_elmt_file(elmt)
        assert len(rec.terminals) == 0
        assert rec.link_type == "simple"

    def test_invalid_xml_raises_error(self, tmp_path):
        bad = tmp_path / "bad.elmt"
        bad.write_text("this is not xml at all")
        with pytest.raises(Exception):
            parse_elmt_file(bad)

    def test_terminals_with_empty_names(self, tmp_path):
        elmt = tmp_path / "empty_names.elmt"
        elmt.write_text(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<definition version="0.90" type="element" width="20" height="40"'
            ' hotspot_x="10" hotspot_y="20">\n'
            '  <uuid uuid="{11111111-1111-1111-1111-111111111111}"/>\n'
            "  <names></names>\n"
            "  <informations></informations>\n"
            "  <description>\n"
            '    <terminal uuid="{a}" name="" x="0" y="-10" orientation="n"'
            ' type="Generic"/>\n'
            "  </description>\n"
            "</definition>\n"
        )
        rec = parse_elmt_file(elmt)
        assert len(rec.terminals) == 1
        assert rec.terminals[0].name == ""

    def test_path_stored_in_record(self, elements_dir, coil_elmt_path):
        rec = parse_elmt_file(
            elements_dir / coil_elmt_path, relative_path=coil_elmt_path
        )
        assert coil_elmt_path in rec.path

    def test_default_relative_path(self, tmp_path):
        elmt = tmp_path / "test.elmt"
        elmt.write_text(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<definition version="0.90" type="element" width="10" height="10"'
            ' hotspot_x="5" hotspot_y="5">\n'
            '  <uuid uuid="{22222222-2222-2222-2222-222222222222}"/>\n'
            "  <names></names>\n"
            "  <informations></informations>\n"
            "  <description></description>\n"
            "</definition>\n"
        )
        rec = parse_elmt_file(elmt)
        assert rec.path == ""
