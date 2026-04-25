"""Tests for element_db data models."""

import math

import pytest

from src.element_db.models import (
    ElementRecord,
    GraphicPrimitive,
    KindInformations,
    Terminal,
    terminal_absolute_position,
)


class TestTerminal:
    """Tests for the Terminal dataclass."""

    def test_create_terminal_with_all_fields(self):
        t = Terminal(
            uuid="{abc-123}",
            name="A1",
            x=0.0,
            y=-20.0,
            orientation="n",
            type="Generic",
        )
        assert t.uuid == "{abc-123}"
        assert t.name == "A1"
        assert t.x == 0.0
        assert t.y == -20.0
        assert t.orientation == "n"
        assert t.type == "Generic"

    def test_terminal_defaults(self):
        t = Terminal(uuid="", name="", x=0.0, y=0.0, orientation="n", type="Generic")
        assert t.uuid == ""
        assert t.name == ""


class TestGraphicPrimitive:
    """Tests for the GraphicPrimitive dataclass."""

    def test_create_graphic_primitive(self):
        gp = GraphicPrimitive(
            type="rect",
            attributes={"x": "-14", "y": "-8", "width": "28", "height": "16"},
        )
        assert gp.type == "rect"
        assert gp.attributes["width"] == "28"

    def test_graphic_primitive_empty_attributes(self):
        gp = GraphicPrimitive(type="line", attributes={})
        assert gp.type == "line"
        assert gp.attributes == {}


class TestKindInformations:
    """Tests for the KindInformations dataclass."""

    def test_coil_kind(self):
        ki = KindInformations(type="coil")
        assert ki.type == "coil"
        assert ki.state is None
        assert ki.number is None
        assert ki.function is None
        assert ki.max_slaves is None

    def test_slave_contact_kind(self):
        ki = KindInformations(type="simple", state="NO", number=1)
        assert ki.type == "simple"
        assert ki.state == "NO"
        assert ki.number == 1

    def test_terminal_kind(self):
        ki = KindInformations(type="generic", function="generic")
        assert ki.type == "generic"
        assert ki.function == "generic"

    def test_protection_kind(self):
        ki = KindInformations(type="protection")
        assert ki.type == "protection"


class TestElementRecord:
    """Tests for the ElementRecord dataclass."""

    def test_create_element_record(self):
        terminals = [
            Terminal(uuid="{a}", name="A1", x=0.0, y=-20.0, orientation="n", type="Generic"),
            Terminal(uuid="{b}", name="A2", x=0.0, y=20.0, orientation="s", type="Generic"),
        ]
        primitives = [GraphicPrimitive(type="rect", attributes={"x": "0"})]
        ki = KindInformations(type="coil")
        rec = ElementRecord(
            path="10_electric/coils/bobine3.elmt",
            uuid="{uuid-123}",
            names={"de": "Spule", "en": "Coil"},
            width=40,
            height=60,
            hotspot_x=20,
            hotspot_y=32,
            link_type="master",
            kind_informations=ki,
            terminals=terminals,
            graphic_primitives=primitives,
            informations="Author: test",
        )
        assert rec.path == "10_electric/coils/bobine3.elmt"
        assert rec.uuid == "{uuid-123}"
        assert rec.names["de"] == "Spule"
        assert rec.width == 40
        assert rec.height == 60
        assert rec.hotspot_x == 20
        assert rec.hotspot_y == 32
        assert rec.link_type == "master"
        assert rec.kind_informations.type == "coil"
        assert len(rec.terminals) == 2
        assert len(rec.graphic_primitives) == 1
        assert "Author" in rec.informations

    def test_element_record_no_kind_informations(self):
        rec = ElementRecord(
            path="test.elmt",
            uuid="{x}",
            names={},
            width=10,
            height=10,
            hotspot_x=5,
            hotspot_y=5,
            link_type="simple",
            kind_informations=None,
            terminals=[],
            graphic_primitives=[],
            informations="",
        )
        assert rec.kind_informations is None
        assert rec.link_type == "simple"


class TestTerminalAbsolutePosition:
    """Tests for the terminal_absolute_position rotation function."""

    def test_orientation_0_no_rotation(self):
        """Orientation 0 = 0 degrees: no rotation."""
        t = Terminal(uuid="", name="A1", x=0.0, y=-20.0, orientation="n", type="Generic")
        abs_x, abs_y = terminal_absolute_position(t, element_x=100.0, element_y=200.0, orientation=0)
        assert abs_x == pytest.approx(100.0)
        assert abs_y == pytest.approx(180.0)

    def test_orientation_1_90_degrees(self):
        """Orientation 1 = 90 degrees clockwise."""
        t = Terminal(uuid="", name="A1", x=0.0, y=-20.0, orientation="n", type="Generic")
        abs_x, abs_y = terminal_absolute_position(t, element_x=100.0, element_y=200.0, orientation=1)
        # cos(90)=0, sin(90)=1
        # abs_x = 100 + (0*0 - (-20)*1) = 100 + 20 = 120
        # abs_y = 200 + (0*1 + (-20)*0) = 200 + 0 = 200
        assert abs_x == pytest.approx(120.0)
        assert abs_y == pytest.approx(200.0)

    def test_orientation_2_180_degrees(self):
        """Orientation 2 = 180 degrees."""
        t = Terminal(uuid="", name="A1", x=0.0, y=-20.0, orientation="n", type="Generic")
        abs_x, abs_y = terminal_absolute_position(t, element_x=100.0, element_y=200.0, orientation=2)
        # cos(180)=-1, sin(180)=0
        # abs_x = 100 + (0*(-1) - (-20)*0) = 100
        # abs_y = 200 + (0*0 + (-20)*(-1)) = 200 + 20 = 220
        assert abs_x == pytest.approx(100.0)
        assert abs_y == pytest.approx(220.0)

    def test_orientation_3_270_degrees(self):
        """Orientation 3 = 270 degrees."""
        t = Terminal(uuid="", name="A1", x=0.0, y=-20.0, orientation="n", type="Generic")
        abs_x, abs_y = terminal_absolute_position(t, element_x=100.0, element_y=200.0, orientation=3)
        # cos(270)=0, sin(270)=-1
        # abs_x = 100 + (0*0 - (-20)*(-1)) = 100 - 20 = 80
        # abs_y = 200 + (0*(-1) + (-20)*0) = 200
        assert abs_x == pytest.approx(80.0)
        assert abs_y == pytest.approx(200.0)

    def test_nonzero_terminal_x_orientation_0(self):
        """Terminal with non-zero x, no rotation."""
        t = Terminal(uuid="", name="U1", x=-20.0, y=-30.0, orientation="n", type="Generic")
        abs_x, abs_y = terminal_absolute_position(t, element_x=100.0, element_y=200.0, orientation=0)
        assert abs_x == pytest.approx(80.0)
        assert abs_y == pytest.approx(170.0)

    def test_nonzero_terminal_x_orientation_1(self):
        """Terminal with non-zero x, 90 degree rotation."""
        t = Terminal(uuid="", name="U1", x=-20.0, y=-30.0, orientation="n", type="Generic")
        abs_x, abs_y = terminal_absolute_position(t, element_x=100.0, element_y=200.0, orientation=1)
        # cos(90)=0, sin(90)=1
        # abs_x = 100 + ((-20)*0 - (-30)*1) = 100 + 30 = 130
        # abs_y = 200 + ((-20)*1 + (-30)*0) = 200 - 20 = 180
        assert abs_x == pytest.approx(130.0)
        assert abs_y == pytest.approx(180.0)

    def test_nonzero_terminal_x_orientation_2(self):
        """Terminal with non-zero x, 180 degree rotation."""
        t = Terminal(uuid="", name="U1", x=-20.0, y=-30.0, orientation="n", type="Generic")
        abs_x, abs_y = terminal_absolute_position(t, element_x=100.0, element_y=200.0, orientation=2)
        # cos(180)=-1, sin(180)=0
        # abs_x = 100 + ((-20)*(-1) - (-30)*0) = 100 + 20 = 120
        # abs_y = 200 + ((-20)*0 + (-30)*(-1)) = 200 + 30 = 230
        assert abs_x == pytest.approx(120.0)
        assert abs_y == pytest.approx(230.0)

    def test_nonzero_terminal_x_orientation_3(self):
        """Terminal with non-zero x, 270 degree rotation."""
        t = Terminal(uuid="", name="U1", x=-20.0, y=-30.0, orientation="n", type="Generic")
        abs_x, abs_y = terminal_absolute_position(t, element_x=100.0, element_y=200.0, orientation=3)
        # cos(270)=0, sin(270)=-1
        # abs_x = 100 + ((-20)*0 - (-30)*(-1)) = 100 - 30 = 70
        # abs_y = 200 + ((-20)*(-1) + (-30)*0) = 200 + 20 = 220
        assert abs_x == pytest.approx(70.0)
        assert abs_y == pytest.approx(220.0)
