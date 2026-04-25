"""Tests for the SVG renderer (QET-3).

Each test cycle corresponds to a TDD cycle from the implementation plan.
New fixtures with graphic primitives are defined here to avoid modifying
the shared conftest.py used by the writer tests.
"""

from __future__ import annotations

import math
from pathlib import Path

import pytest

from src.element_db.models import (
    ElementRecord,
    GraphicPrimitive,
    KindInformations,
    Terminal,
    terminal_absolute_position,
)
from src.writer.models import (
    Conductor,
    DynamicText,
    Folio,
    PlacedElement,
    PlacedTerminal,
    QETProject,
    generate_uuid,
)

# ---------------------------------------------------------------------------
# Fixtures specific to renderer tests (with graphic primitives)
# ---------------------------------------------------------------------------

@pytest.fixture
def coil_record_with_graphics():
    """Coil ElementRecord WITH graphic primitives for renderer tests."""
    return ElementRecord(
        path="10_electric/10_allpole/310_relays_contactors_contacts/01_coils/bobine3.elmt",
        uuid="{793302b1-e96a-f7f8-70bc-dec53eeaab5b}",
        names={"de": "Spule", "en": "Coil"},
        width=40, height=60, hotspot_x=20, hotspot_y=32,
        link_type="master",
        kind_informations=KindInformations(type="coil"),
        terminals=[
            Terminal(uuid="{8d0fa333-2d98-4a75-8a4e-21c81cce7ec3}", name="A1",
                     x=0.0, y=-20.0, orientation="n", type="Generic"),
            Terminal(uuid="{c5376fd7-bdf1-4c10-985a-0d7d5f52c8f9}", name="A2",
                     x=0.0, y=20.0, orientation="s", type="Generic"),
        ],
        graphic_primitives=[
            GraphicPrimitive(type="line", attributes={
                "x1": "0", "y1": "-20", "x2": "0", "y2": "-8",
                "style": "line-style:normal;line-weight:normal;filling:none;color:black",
                "antialias": "false",
            }),
            GraphicPrimitive(type="rect", attributes={
                "x": "-14", "y": "-8", "width": "28", "height": "16",
                "rx": "0", "ry": "0",
                "style": "line-style:normal;line-weight:normal;filling:none;color:black",
                "antialias": "false",
            }),
            GraphicPrimitive(type="line", attributes={
                "x1": "0", "y1": "8", "x2": "0", "y2": "20",
                "style": "line-style:normal;line-weight:normal;filling:none;color:black",
                "antialias": "false",
            }),
        ],
        informations="",
    )


@pytest.fixture
def motor_record_with_graphics():
    """Motor ElementRecord with a circle and text primitive."""
    return ElementRecord(
        path="10_electric/10_allpole/391_consumers_actuators/10_engines/moteur_tri.elmt",
        uuid="{aabbccdd-1234-5678-abcd-aabbccddeeff}",
        names={"de": "Drehstrommotor", "en": "Three-phase motor"},
        width=60, height=60, hotspot_x=30, hotspot_y=30,
        link_type="simple",
        kind_informations=None,
        terminals=[
            Terminal(uuid="{m-term-u}", name="U", x=-20.0, y=-30.0, orientation="n", type="Generic"),
            Terminal(uuid="{m-term-v}", name="V", x=0.0, y=-30.0, orientation="n", type="Generic"),
            Terminal(uuid="{m-term-w}", name="W", x=20.0, y=-30.0, orientation="n", type="Generic"),
        ],
        graphic_primitives=[
            GraphicPrimitive(type="circle", attributes={
                "x": "-15", "y": "-15", "diameter": "30",
                "style": "line-style:normal;line-weight:normal;filling:none;color:black",
                "antialias": "true",
            }),
            GraphicPrimitive(type="text", attributes={
                "text": "M", "x": "-6", "y": "0", "rotation": "0",
                "font": "Liberation Sans,11,-1,5,50,0,0,0,0,0,Regular",
                "color": "#000000",
            }),
        ],
        informations="",
    )


@pytest.fixture
def renderer_element_db(coil_record_with_graphics, motor_record_with_graphics):
    """Element DB for renderer tests, keyed by path (no common:// prefix)."""
    return {
        coil_record_with_graphics.path: coil_record_with_graphics,
        motor_record_with_graphics.path: motor_record_with_graphics,
    }


@pytest.fixture
def placed_coil(coil_record_with_graphics):
    """A placed coil element on a folio."""
    rec = coil_record_with_graphics
    return PlacedElement(
        uuid="{pe-coil-001}",
        elmt_path="common://" + rec.path,
        x=300.0, y=200.0, z=10.0,
        orientation=0,
        designation="K1",
        prefix="K",
        terminals=[
            PlacedTerminal(uuid="{pt-a1}", name="A1", id=0, x=0.0, y=-20.0, orientation=0),
            PlacedTerminal(uuid="{pt-a2}", name="A2", id=1, x=0.0, y=20.0, orientation=2),
        ],
        dynamic_texts=[
            DynamicText(
                uuid="{dt-k1}", x=25.0, y=-9.17, z=6.0,
                text="K1", text_from="ElementInfo", info_name="label",
                font="Liberation Sans,9,-1,5,50,0,0,0,0,0,Regular",
            ),
        ],
        links_uuids=[],
        element_informations={"label": "K1"},
    )


@pytest.fixture
def placed_motor(motor_record_with_graphics):
    """A placed motor element on a folio."""
    rec = motor_record_with_graphics
    return PlacedElement(
        uuid="{pe-motor-001}",
        elmt_path="common://" + rec.path,
        x=300.0, y=400.0, z=10.0,
        orientation=0,
        designation="M1",
        prefix="M",
        terminals=[
            PlacedTerminal(uuid="{pt-mu}", name="U", id=2, x=-20.0, y=-30.0, orientation=0),
            PlacedTerminal(uuid="{pt-mv}", name="V", id=3, x=0.0, y=-30.0, orientation=0),
            PlacedTerminal(uuid="{pt-mw}", name="W", id=4, x=20.0, y=-30.0, orientation=0),
        ],
        dynamic_texts=[],
        links_uuids=[],
        element_informations={"label": "M1"},
    )


@pytest.fixture
def simple_folio(placed_coil, placed_motor):
    """A folio with a coil and motor, connected by one conductor."""
    conductor = Conductor(
        terminal1_uuid="{pt-a2}",
        terminal2_uuid="{pt-mv}",
        element1_uuid="{pe-coil-001}",
        element2_uuid="{pe-motor-001}",
        terminal1_id=1,
        terminal2_id=3,
        terminal1_name="A2",
        terminal2_name="V",
        element1_label="K1",
        element2_label="M1",
        label="W1",
    )
    return Folio(
        title="Test Folio",
        order=1,
        elements=[placed_coil, placed_motor],
        conductors=[conductor],
    )


@pytest.fixture
def simple_project(simple_folio):
    """A QET project with one folio."""
    return QETProject(
        title="Test Project",
        author="Test Author",
        folios=[simple_folio],
    )


# ===========================================================================
# Cycle 1: Style Parsing Helper
# ===========================================================================

class TestParseStyle:
    """Tests for _parse_style()."""

    def test_normal_style(self):
        from src.renderer.svg_renderer import _parse_style

        result = _parse_style(
            "line-style:normal;line-weight:normal;filling:none;color:black"
        )
        assert result["stroke"] == "black"
        assert result["stroke-width"] == "1"
        assert result["fill"] == "none"
        assert "stroke-dasharray" not in result

    def test_dashed_style(self):
        from src.renderer.svg_renderer import _parse_style

        result = _parse_style(
            "line-style:dashed;line-weight:thin;filling:white;color:red"
        )
        assert result["stroke"] == "red"
        assert result["stroke-width"] == "0.5"
        assert result["fill"] == "white"
        assert result["stroke-dasharray"] == "6,3"

    def test_dotted_style(self):
        from src.renderer.svg_renderer import _parse_style

        result = _parse_style("line-style:dotted;line-weight:hight;filling:black;color:blue")
        assert result["stroke-dasharray"] == "2,2"
        assert result["stroke-width"] == "2"

    def test_dashdotted_style(self):
        from src.renderer.svg_renderer import _parse_style

        result = _parse_style("line-style:dashdotted;line-weight:eleve;filling:green;color:black")
        assert result["stroke-dasharray"] == "6,3,2,3"
        assert result["stroke-width"] == "3"

    def test_weight_none(self):
        from src.renderer.svg_renderer import _parse_style

        result = _parse_style("line-style:normal;line-weight:none;filling:none;color:black")
        assert result["stroke-width"] == "0"

    def test_empty_string(self):
        from src.renderer.svg_renderer import _parse_style

        result = _parse_style("")
        assert result["stroke"] == "black"
        assert result["fill"] == "none"


# ===========================================================================
# Cycle 2: Line Primitive
# ===========================================================================

class TestRenderLine:
    """Tests for _render_line()."""

    def test_basic_line(self):
        from src.renderer.svg_renderer import _render_line

        prim = GraphicPrimitive(type="line", attributes={
            "x1": "0", "y1": "-20", "x2": "0", "y2": "-8",
            "style": "line-style:normal;line-weight:normal;filling:none;color:black",
        })
        svg = _render_line(prim)
        assert "<line" in svg
        assert 'x1="0"' in svg
        assert 'y1="-20"' in svg
        assert 'x2="0"' in svg
        assert 'y2="-8"' in svg
        assert 'stroke="black"' in svg

    def test_dashed_line(self):
        from src.renderer.svg_renderer import _render_line

        prim = GraphicPrimitive(type="line", attributes={
            "x1": "10", "y1": "10", "x2": "50", "y2": "50",
            "style": "line-style:dashed;line-weight:thin;filling:none;color:red",
        })
        svg = _render_line(prim)
        assert 'stroke-dasharray="6,3"' in svg
        assert 'stroke="red"' in svg


# ===========================================================================
# Cycle 3: Rect Primitive
# ===========================================================================

class TestRenderRect:
    """Tests for _render_rect()."""

    def test_basic_rect(self):
        from src.renderer.svg_renderer import _render_rect

        prim = GraphicPrimitive(type="rect", attributes={
            "x": "-14", "y": "-8", "width": "28", "height": "16",
            "rx": "0", "ry": "0",
            "style": "line-style:normal;line-weight:normal;filling:none;color:black",
        })
        svg = _render_rect(prim)
        assert "<rect" in svg
        assert 'x="-14"' in svg
        assert 'width="28"' in svg
        assert 'height="16"' in svg

    def test_rounded_rect(self):
        from src.renderer.svg_renderer import _render_rect

        prim = GraphicPrimitive(type="rect", attributes={
            "x": "0", "y": "0", "width": "40", "height": "30",
            "rx": "5", "ry": "5",
            "style": "line-style:normal;line-weight:normal;filling:white;color:black",
        })
        svg = _render_rect(prim)
        assert 'rx="5"' in svg
        assert 'ry="5"' in svg
        assert 'fill="white"' in svg


# ===========================================================================
# Cycle 4: Ellipse Primitive
# ===========================================================================

class TestRenderEllipse:
    """Tests for _render_ellipse() -- bounding box to center+radii."""

    def test_basic_ellipse(self):
        from src.renderer.svg_renderer import _render_ellipse

        prim = GraphicPrimitive(type="ellipse", attributes={
            "x": "-15", "y": "-15", "width": "30", "height": "30",
            "style": "line-style:normal;line-weight:normal;filling:none;color:black",
        })
        svg = _render_ellipse(prim)
        assert "<ellipse" in svg
        # cx = -15 + 30/2 = 0, cy = -15 + 30/2 = 0
        assert 'cx="0.0"' in svg
        assert 'cy="0.0"' in svg
        assert 'rx="15.0"' in svg
        assert 'ry="15.0"' in svg

    def test_non_square_ellipse(self):
        from src.renderer.svg_renderer import _render_ellipse

        prim = GraphicPrimitive(type="ellipse", attributes={
            "x": "10", "y": "20", "width": "40", "height": "20",
            "style": "line-style:normal;line-weight:normal;filling:none;color:black",
        })
        svg = _render_ellipse(prim)
        # cx = 10 + 40/2 = 30, cy = 20 + 20/2 = 30
        assert 'cx="30.0"' in svg
        assert 'cy="30.0"' in svg
        assert 'rx="20.0"' in svg
        assert 'ry="10.0"' in svg


# ===========================================================================
# Cycle 5: Circle Primitive
# ===========================================================================

class TestRenderCircle:
    """Tests for _render_circle()."""

    def test_basic_circle(self):
        from src.renderer.svg_renderer import _render_circle

        prim = GraphicPrimitive(type="circle", attributes={
            "x": "-15", "y": "-15", "diameter": "30",
            "style": "line-style:normal;line-weight:normal;filling:none;color:black",
        })
        svg = _render_circle(prim)
        assert "<circle" in svg
        # cx = -15 + 30/2 = 0, cy = -15 + 30/2 = 0, r = 15
        assert 'cx="0.0"' in svg
        assert 'cy="0.0"' in svg
        assert 'r="15.0"' in svg


# ===========================================================================
# Cycle 6: Arc Primitive
# ===========================================================================

class TestRenderArc:
    """Tests for _render_arc() -- QET Qt-convention to SVG path arc."""

    def test_semicircle_arc(self):
        from src.renderer.svg_renderer import _render_arc

        prim = GraphicPrimitive(type="arc", attributes={
            "x": "-10", "y": "-10", "width": "20", "height": "20",
            "start": "0", "angle": "180",
            "style": "line-style:normal;line-weight:normal;filling:none;color:black",
        })
        svg = _render_arc(prim)
        assert "<path" in svg
        assert 'd="M' in svg
        # Start at angle 0 (east): sx = 0 + 10*cos(0) = 10, sy = 0 - 10*sin(0) = 0
        # End at angle 180 (west): ex = 0 + 10*cos(pi) = -10, ey = 0 - 10*sin(pi) ~ 0
        # large-arc-flag = 0 (180 is not > 180), sweep-flag = 0 (positive angle => CCW in screen coords)
        assert "A 10.0 10.0" in svg

    def test_full_arc_large(self):
        from src.renderer.svg_renderer import _render_arc

        prim = GraphicPrimitive(type="arc", attributes={
            "x": "-14.5", "y": "-15.5", "width": "32", "height": "32",
            "start": "300", "angle": "80",
            "style": "line-style:normal;line-weight:normal;filling:none;color:black",
        })
        svg = _render_arc(prim)
        assert "<path" in svg
        # angle = 80 < 180, so large-arc-flag = 0
        assert " 0 0 " in svg  # large-arc=0, sweep=0

    def test_negative_angle_arc(self):
        from src.renderer.svg_renderer import _render_arc

        prim = GraphicPrimitive(type="arc", attributes={
            "x": "-10", "y": "-10", "width": "20", "height": "20",
            "start": "90", "angle": "-90",
            "style": "line-style:normal;line-weight:normal;filling:none;color:black",
        })
        svg = _render_arc(prim)
        assert "<path" in svg
        # negative angle => sweep-flag = 1
        assert " 0 1 " in svg

    def test_large_arc_flag(self):
        from src.renderer.svg_renderer import _render_arc

        prim = GraphicPrimitive(type="arc", attributes={
            "x": "-10", "y": "-10", "width": "20", "height": "20",
            "start": "0", "angle": "270",
            "style": "line-style:normal;line-weight:normal;filling:none;color:black",
        })
        svg = _render_arc(prim)
        # |angle| > 180 => large-arc-flag = 1
        assert " 1 0 " in svg


# ===========================================================================
# Cycle 7: Polygon Primitive
# ===========================================================================

class TestRenderPolygon:
    """Tests for _render_polygon()."""

    def test_closed_polygon(self):
        from src.renderer.svg_renderer import _render_polygon

        prim = GraphicPrimitive(type="polygon", attributes={
            "x1": "-20", "y1": "-30", "x2": "-20", "y2": "-20",
            "x3": "-11", "y3": "-11", "closed": "true",
            "style": "line-style:normal;line-weight:normal;filling:none;color:black",
        })
        svg = _render_polygon(prim)
        assert "<polygon" in svg
        assert 'points="-20,-30 -20,-20 -11,-11"' in svg

    def test_open_polyline(self):
        from src.renderer.svg_renderer import _render_polygon

        prim = GraphicPrimitive(type="polygon", attributes={
            "x1": "0", "y1": "0", "x2": "10", "y2": "10",
            "x3": "20", "y3": "0", "closed": "false",
            "style": "line-style:normal;line-weight:normal;filling:none;color:black",
        })
        svg = _render_polygon(prim)
        assert "<polyline" in svg
        assert 'points="0,0 10,10 20,0"' in svg

    def test_many_points(self):
        from src.renderer.svg_renderer import _render_polygon

        prim = GraphicPrimitive(type="polygon", attributes={
            "x1": "0", "y1": "0", "x2": "10", "y2": "0",
            "x3": "10", "y3": "10", "x4": "0", "y4": "10",
            "closed": "true",
            "style": "line-style:normal;line-weight:normal;filling:none;color:black",
        })
        svg = _render_polygon(prim)
        assert "<polygon" in svg
        assert 'points="0,0 10,0 10,10 0,10"' in svg


# ===========================================================================
# Cycle 8: Text Primitive
# ===========================================================================

class TestRenderText:
    """Tests for _render_text()."""

    def test_basic_text(self):
        from src.renderer.svg_renderer import _render_text

        prim = GraphicPrimitive(type="text", attributes={
            "text": "M", "x": "-6", "y": "0", "rotation": "0",
            "font": "Liberation Sans,11,-1,5,50,0,0,0,0,0,Regular",
            "color": "#000000",
        })
        svg = _render_text(prim)
        assert "<text" in svg
        assert 'x="-6"' in svg
        assert 'y="0"' in svg
        assert "M</text>" in svg or ">M<" in svg
        assert 'fill="#000000"' in svg
        assert 'font-family="Liberation Sans"' in svg
        assert 'font-size="11"' in svg

    def test_text_with_rotation(self):
        from src.renderer.svg_renderer import _render_text

        prim = GraphicPrimitive(type="text", attributes={
            "text": "L1", "x": "5", "y": "10", "rotation": "90",
            "font": "Sans Serif,9,-1,5,50,0,0,0,0,0,Regular",
            "color": "#ff0000",
        })
        svg = _render_text(prim)
        assert 'transform="rotate(90' in svg

    def test_multiline_text(self):
        from src.renderer.svg_renderer import _render_text

        prim = GraphicPrimitive(type="text", attributes={
            "text": "Line1&#10;Line2", "x": "0", "y": "0", "rotation": "0",
            "font": "Liberation Sans,10,-1,5,50,0,0,0,0,0,Regular",
            "color": "#000000",
        })
        svg = _render_text(prim)
        assert "<tspan" in svg
        assert "Line1" in svg
        assert "Line2" in svg


# ===========================================================================
# Cycle 9: Primitive Dispatcher
# ===========================================================================

class TestRenderPrimitive:
    """Tests for _render_primitive() dispatcher."""

    def test_dispatches_line(self):
        from src.renderer.svg_renderer import _render_primitive

        prim = GraphicPrimitive(type="line", attributes={
            "x1": "0", "y1": "0", "x2": "10", "y2": "10",
            "style": "line-style:normal;line-weight:normal;filling:none;color:black",
        })
        svg = _render_primitive(prim)
        assert "<line" in svg

    def test_dispatches_rect(self):
        from src.renderer.svg_renderer import _render_primitive

        prim = GraphicPrimitive(type="rect", attributes={
            "x": "0", "y": "0", "width": "10", "height": "10",
            "rx": "0", "ry": "0",
            "style": "line-style:normal;line-weight:normal;filling:none;color:black",
        })
        svg = _render_primitive(prim)
        assert "<rect" in svg

    def test_dispatches_ellipse(self):
        from src.renderer.svg_renderer import _render_primitive

        prim = GraphicPrimitive(type="ellipse", attributes={
            "x": "0", "y": "0", "width": "20", "height": "10",
            "style": "line-style:normal;line-weight:normal;filling:none;color:black",
        })
        svg = _render_primitive(prim)
        assert "<ellipse" in svg

    def test_dispatches_circle(self):
        from src.renderer.svg_renderer import _render_primitive

        prim = GraphicPrimitive(type="circle", attributes={
            "x": "0", "y": "0", "diameter": "20",
            "style": "line-style:normal;line-weight:normal;filling:none;color:black",
        })
        svg = _render_primitive(prim)
        assert "<circle" in svg

    def test_dispatches_arc(self):
        from src.renderer.svg_renderer import _render_primitive

        prim = GraphicPrimitive(type="arc", attributes={
            "x": "0", "y": "0", "width": "20", "height": "20",
            "start": "0", "angle": "90",
            "style": "line-style:normal;line-weight:normal;filling:none;color:black",
        })
        svg = _render_primitive(prim)
        assert "<path" in svg

    def test_dispatches_polygon(self):
        from src.renderer.svg_renderer import _render_primitive

        prim = GraphicPrimitive(type="polygon", attributes={
            "x1": "0", "y1": "0", "x2": "10", "y2": "10",
            "closed": "true",
            "style": "line-style:normal;line-weight:normal;filling:none;color:black",
        })
        svg = _render_primitive(prim)
        assert "<polygon" in svg

    def test_dispatches_text(self):
        from src.renderer.svg_renderer import _render_primitive

        prim = GraphicPrimitive(type="text", attributes={
            "text": "X", "x": "0", "y": "0", "rotation": "0",
            "font": "Liberation Sans,10,-1,5,50,0,0,0,0,0,Regular",
            "color": "#000000",
        })
        svg = _render_primitive(prim)
        assert "<text" in svg

    def test_unknown_type_returns_comment(self):
        from src.renderer.svg_renderer import _render_primitive

        prim = GraphicPrimitive(type="unknown_widget", attributes={"foo": "bar"})
        svg = _render_primitive(prim)
        assert "<!--" in svg
        assert "unknown_widget" in svg


# ===========================================================================
# Cycle 10: Render Single Element (with transform)
# ===========================================================================

class TestRenderElement:
    """Tests for _render_element()."""

    def test_element_wrapped_in_group(self, placed_coil, coil_record_with_graphics):
        from src.renderer.svg_renderer import _render_element

        svg = _render_element(placed_coil, coil_record_with_graphics)
        assert "<g " in svg
        assert 'translate(300' in svg
        assert "</g>" in svg

    def test_element_contains_primitives(self, placed_coil, coil_record_with_graphics):
        from src.renderer.svg_renderer import _render_element

        svg = _render_element(placed_coil, coil_record_with_graphics)
        # Should contain the line and rect primitives
        assert "<line" in svg
        assert "<rect" in svg

    def test_element_orientation_90(self, coil_record_with_graphics):
        from src.renderer.svg_renderer import _render_element

        pe = PlacedElement(
            uuid="{pe-rotated}", elmt_path="common://test.elmt",
            x=100.0, y=200.0, z=10.0, orientation=1,
            designation="K2", prefix="K",
            terminals=[], dynamic_texts=[], links_uuids=[],
            element_informations={},
        )
        svg = _render_element(pe, coil_record_with_graphics)
        assert "rotate(90)" in svg

    def test_element_orientation_0_no_rotate(self, placed_coil, coil_record_with_graphics):
        from src.renderer.svg_renderer import _render_element

        svg = _render_element(placed_coil, coil_record_with_graphics)
        # Orientation 0 means no rotation, should not have rotate in transform
        assert "rotate(" not in svg or "rotate(0)" not in svg

    def test_element_designation_label(self, placed_coil, coil_record_with_graphics):
        from src.renderer.svg_renderer import _render_element

        svg = _render_element(placed_coil, coil_record_with_graphics)
        assert "K1" in svg


# ===========================================================================
# Cycle 11: Terminal Markers
# ===========================================================================

class TestRenderTerminalMarkers:
    """Tests for _render_terminal_markers()."""

    def test_markers_for_coil(self, placed_coil, coil_record_with_graphics):
        from src.renderer.svg_renderer import _render_terminal_markers

        svg = _render_terminal_markers(placed_coil, coil_record_with_graphics)
        # Should contain two circle markers (A1, A2)
        assert svg.count("<circle") == 2

    def test_marker_positions(self, placed_coil, coil_record_with_graphics):
        from src.renderer.svg_renderer import _render_terminal_markers

        svg = _render_terminal_markers(placed_coil, coil_record_with_graphics)
        # Element at (300, 200), orientation 0
        # A1: local (0, -20) => absolute (300, 180)
        # A2: local (0, 20) => absolute (300, 220)
        assert 'cx="300.0"' in svg
        assert 'cy="180.0"' in svg
        assert 'cy="220.0"' in svg

    def test_markers_with_rotation(self, coil_record_with_graphics):
        from src.renderer.svg_renderer import _render_terminal_markers

        pe = PlacedElement(
            uuid="{pe-rot}", elmt_path="common://test.elmt",
            x=100.0, y=100.0, z=10.0, orientation=1,
            designation="K3", prefix="K",
            terminals=[
                PlacedTerminal(uuid="{pt-r1}", name="A1", id=0, x=0.0, y=-20.0, orientation=0),
            ],
            dynamic_texts=[], links_uuids=[], element_informations={},
        )
        svg = _render_terminal_markers(pe, coil_record_with_graphics)
        # orientation=1 => 90 degrees
        # (0, -20) rotated 90 degrees: x' = 0*cos90 - (-20)*sin90 = 20, y' = 0*sin90 + (-20)*cos90 = 0
        # absolute: (100+20, 100+0) = (120, 100)
        assert 'cx="120.0"' in svg
        assert 'cy="100.0"' in svg


# ===========================================================================
# Cycle 12: Render Conductor
# ===========================================================================

class TestRenderConductor:
    """Tests for _render_conductor()."""

    def test_conductor_as_line(self):
        from src.renderer.svg_renderer import _render_conductor

        cond = Conductor(
            terminal1_uuid="{t1}", terminal2_uuid="{t2}",
            element1_uuid="{e1}", element2_uuid="{e2}",
            terminal1_id=0, terminal2_id=1,
            terminal1_name="A1", terminal2_name="A2",
            element1_label="K1", element2_label="K2",
            label="W1",
        )
        term_pos = {"{t1}": (100.0, 200.0), "{t2}": (100.0, 400.0)}
        svg = _render_conductor(cond, term_pos)
        assert "<line" in svg or "<path" in svg
        assert "100" in svg
        assert "200" in svg
        assert "400" in svg

    def test_conductor_missing_terminal_skipped(self):
        from src.renderer.svg_renderer import _render_conductor

        cond = Conductor(
            terminal1_uuid="{missing1}", terminal2_uuid="{missing2}",
            element1_uuid="{e1}", element2_uuid="{e2}",
            terminal1_id=0, terminal2_id=1,
            terminal1_name="A1", terminal2_name="A2",
            element1_label="K1", element2_label="K2",
            label="",
        )
        svg = _render_conductor(cond, {})
        # Should return a comment or empty string, not crash
        assert "<!--" in svg or svg == ""

    def test_conductor_label(self):
        from src.renderer.svg_renderer import _render_conductor

        cond = Conductor(
            terminal1_uuid="{t1}", terminal2_uuid="{t2}",
            element1_uuid="{e1}", element2_uuid="{e2}",
            terminal1_id=0, terminal2_id=1,
            terminal1_name="A1", terminal2_name="A2",
            element1_label="K1", element2_label="K2",
            label="L1",
        )
        term_pos = {"{t1}": (100.0, 200.0), "{t2}": (100.0, 400.0)}
        svg = _render_conductor(cond, term_pos)
        assert "L1" in svg


# ===========================================================================
# Cycle 13: Build Terminal Position Map
# ===========================================================================

class TestBuildTerminalPositions:
    """Tests for _build_terminal_positions()."""

    def test_positions_computed(self, simple_folio, renderer_element_db):
        from src.renderer.svg_renderer import _build_terminal_positions

        pos_map = _build_terminal_positions(simple_folio, renderer_element_db)
        # Coil at (300, 200), orientation 0
        # A1: (0, -20) => (300, 180)
        # A2: (0, 20) => (300, 220)
        assert pos_map["{pt-a1}"] == pytest.approx((300.0, 180.0))
        assert pos_map["{pt-a2}"] == pytest.approx((300.0, 220.0))

    def test_all_terminals_present(self, simple_folio, renderer_element_db):
        from src.renderer.svg_renderer import _build_terminal_positions

        pos_map = _build_terminal_positions(simple_folio, renderer_element_db)
        # 2 coil terminals + 3 motor terminals = 5
        assert len(pos_map) == 5

    def test_motor_terminals(self, simple_folio, renderer_element_db):
        from src.renderer.svg_renderer import _build_terminal_positions

        pos_map = _build_terminal_positions(simple_folio, renderer_element_db)
        # Motor at (300, 400), orientation 0
        # U: (-20, -30) => (280, 370)
        # V: (0, -30) => (300, 370)
        # W: (20, -30) => (320, 370)
        assert pos_map["{pt-mu}"] == pytest.approx((280.0, 370.0))
        assert pos_map["{pt-mv}"] == pytest.approx((300.0, 370.0))
        assert pos_map["{pt-mw}"] == pytest.approx((320.0, 370.0))

    def test_strips_common_prefix(self, simple_folio, renderer_element_db):
        """Ensures common:// prefix is stripped for element_db lookup."""
        from src.renderer.svg_renderer import _build_terminal_positions

        # This should not raise a KeyError
        pos_map = _build_terminal_positions(simple_folio, renderer_element_db)
        assert len(pos_map) > 0


# ===========================================================================
# Cycle 14: Title Block
# ===========================================================================

class TestRenderTitleBlock:
    """Tests for _render_title_block()."""

    def test_title_block_comment(self):
        from src.renderer.svg_renderer import _render_title_block

        folio = Folio(title="Main Circuit", order=1)
        project = QETProject(title="Motor Starter", author="Engineer")
        svg = _render_title_block(folio, project, 1020, 640)
        assert "<!-- titleblock -->" in svg

    def test_title_block_contains_title(self):
        from src.renderer.svg_renderer import _render_title_block

        folio = Folio(title="Main Circuit", order=1)
        project = QETProject(title="Motor Starter", author="Engineer")
        svg = _render_title_block(folio, project, 1020, 640)
        assert "Main Circuit" in svg

    def test_title_block_contains_author(self):
        from src.renderer.svg_renderer import _render_title_block

        folio = Folio(title="Main Circuit", order=1)
        project = QETProject(title="Motor Starter", author="Engineer")
        svg = _render_title_block(folio, project, 1020, 640)
        assert "Engineer" in svg

    def test_title_block_rect(self):
        from src.renderer.svg_renderer import _render_title_block

        folio = Folio(title="X", order=1)
        project = QETProject(title="Y", author="Z")
        svg = _render_title_block(folio, project, 1020, 640)
        assert "<rect" in svg


# ===========================================================================
# Cycle 15: Grid Lines
# ===========================================================================

class TestRenderGrid:
    """Tests for _render_grid()."""

    def test_grid_lines_present(self):
        from src.renderer.svg_renderer import _render_grid

        svg = _render_grid(100, 80, spacing=10)
        # Should contain vertical and horizontal lines
        assert "<line" in svg

    def test_grid_line_count(self):
        from src.renderer.svg_renderer import _render_grid

        svg = _render_grid(100, 80, spacing=10)
        # Vertical lines: at 0, 10, 20, ..., 100 => 11 lines
        # Horizontal lines: at 0, 10, 20, ..., 80 => 9 lines
        # Total: 20 lines
        line_count = svg.count("<line")
        assert line_count == 20

    def test_grid_custom_spacing(self):
        from src.renderer.svg_renderer import _render_grid

        svg = _render_grid(100, 100, spacing=50)
        # Vertical: 0, 50, 100 => 3 lines
        # Horizontal: 0, 50, 100 => 3 lines
        # Total: 6
        line_count = svg.count("<line")
        assert line_count == 6


# ===========================================================================
# Cycle 16: Full Folio Render -- SVGRenderer.render()
# ===========================================================================

class TestSVGRendererRender:
    """Tests for SVGRenderer.render()."""

    def test_render_returns_valid_svg(self, renderer_element_db, simple_project):
        from src.renderer.svg_renderer import SVGRenderer

        renderer = SVGRenderer(renderer_element_db)
        svg = renderer.render(simple_project, folio_index=0)
        assert svg.startswith("<svg")
        assert "</svg>" in svg

    def test_render_contains_viewbox(self, renderer_element_db, simple_project):
        from src.renderer.svg_renderer import SVGRenderer

        renderer = SVGRenderer(renderer_element_db)
        svg = renderer.render(simple_project, folio_index=0)
        assert "viewBox" in svg

    def test_render_contains_elements(self, renderer_element_db, simple_project):
        from src.renderer.svg_renderer import SVGRenderer

        renderer = SVGRenderer(renderer_element_db)
        svg = renderer.render(simple_project, folio_index=0)
        # Should contain element groups and primitives
        assert "<g " in svg
        assert "<line" in svg or "<rect" in svg or "<circle" in svg

    def test_render_contains_conductors(self, renderer_element_db, simple_project):
        from src.renderer.svg_renderer import SVGRenderer

        renderer = SVGRenderer(renderer_element_db)
        svg = renderer.render(simple_project, folio_index=0)
        # Our simple project has one conductor
        assert "conductor" in svg.lower() or "W1" in svg

    def test_render_contains_titleblock(self, renderer_element_db, simple_project):
        from src.renderer.svg_renderer import SVGRenderer

        renderer = SVGRenderer(renderer_element_db)
        svg = renderer.render(simple_project, folio_index=0)
        assert "<!-- titleblock -->" in svg

    def test_render_with_grid(self, renderer_element_db, simple_project):
        from src.renderer.svg_renderer import SVGRenderer

        renderer = SVGRenderer(renderer_element_db)
        svg = renderer.render(simple_project, folio_index=0, show_grid=True)
        assert "<!-- grid -->" in svg

    def test_render_without_grid(self, renderer_element_db, simple_project):
        from src.renderer.svg_renderer import SVGRenderer

        renderer = SVGRenderer(renderer_element_db)
        svg = renderer.render(simple_project, folio_index=0, show_grid=False)
        assert "<!-- grid -->" not in svg

    def test_render_invalid_folio_index(self, renderer_element_db, simple_project):
        from src.renderer.svg_renderer import SVGRenderer

        renderer = SVGRenderer(renderer_element_db)
        with pytest.raises(IndexError):
            renderer.render(simple_project, folio_index=99)

    def test_render_terminal_markers(self, renderer_element_db, simple_project):
        from src.renderer.svg_renderer import SVGRenderer

        renderer = SVGRenderer(renderer_element_db)
        svg = renderer.render(simple_project, folio_index=0)
        # Should have terminal markers (circles with class terminal-marker)
        assert "terminal-marker" in svg

    def test_render_column_headers(self, renderer_element_db, simple_project):
        from src.renderer.svg_renderer import SVGRenderer

        renderer = SVGRenderer(renderer_element_db)
        svg = renderer.render(simple_project, folio_index=0)
        # Should have column numbers 1-17
        assert ">1<" in svg
        assert ">17<" in svg

    def test_render_row_headers(self, renderer_element_db, simple_project):
        from src.renderer.svg_renderer import SVGRenderer

        renderer = SVGRenderer(renderer_element_db)
        svg = renderer.render(simple_project, folio_index=0)
        # Should have row letters A-H
        assert ">A<" in svg
        assert ">H<" in svg


# ===========================================================================
# Cycle 17: render_to_file()
# ===========================================================================

class TestRenderToFile:
    """Tests for SVGRenderer.render_to_file()."""

    def test_writes_file(self, renderer_element_db, simple_project, tmp_path):
        from src.renderer.svg_renderer import SVGRenderer

        renderer = SVGRenderer(renderer_element_db)
        out_path = tmp_path / "test_output.svg"
        renderer.render_to_file(simple_project, folio_index=0, filepath=out_path)
        assert out_path.exists()
        content = out_path.read_text(encoding="utf-8")
        assert content.startswith("<svg")

    def test_file_content_matches_render(self, renderer_element_db, simple_project, tmp_path):
        from src.renderer.svg_renderer import SVGRenderer

        renderer = SVGRenderer(renderer_element_db)
        out_path = tmp_path / "test_output2.svg"
        renderer.render_to_file(simple_project, folio_index=0, filepath=out_path)
        expected = renderer.render(simple_project, folio_index=0)
        actual = out_path.read_text(encoding="utf-8")
        assert actual == expected


# ===========================================================================
# Cycle 18: Calibration File Generation
# ===========================================================================

class TestGenerateCalibration:
    """Tests for generate_calibration()."""

    def test_generates_both_files(self, renderer_element_db, tmp_path):
        from src.renderer.svg_renderer import generate_calibration

        qet_path, svg_path = generate_calibration(tmp_path, renderer_element_db)
        assert qet_path.exists()
        assert svg_path.exists()
        assert qet_path.suffix == ".qet"
        assert svg_path.suffix == ".svg"

    def test_qet_file_is_valid_xml(self, renderer_element_db, tmp_path):
        from src.renderer.svg_renderer import generate_calibration
        import xml.etree.ElementTree as ET

        qet_path, _ = generate_calibration(tmp_path, renderer_element_db)
        # Should parse without error
        tree = ET.parse(qet_path)
        root = tree.getroot()
        assert root.tag == "project"

    def test_svg_file_is_valid(self, renderer_element_db, tmp_path):
        from src.renderer.svg_renderer import generate_calibration

        _, svg_path = generate_calibration(tmp_path, renderer_element_db)
        content = svg_path.read_text(encoding="utf-8")
        assert "<svg" in content
        assert "</svg>" in content


# ===========================================================================
# Cycle 19: Integration Tests
# ===========================================================================

class TestIntegration:
    """End-to-end: build project with QETWriter, render with SVGRenderer."""

    def test_writer_then_renderer(self, renderer_element_db, tmp_path):
        from src.writer.qet_writer import QETWriter
        from src.renderer.svg_renderer import SVGRenderer

        # Build project with QETWriter
        writer = QETWriter(element_db=renderer_element_db)
        project = writer.create_project("Integration Test", author="Tester")
        folio = writer.add_folio(project, "Main")

        coil_path = "10_electric/10_allpole/310_relays_contactors_contacts/01_coils/bobine3.elmt"
        motor_path = "10_electric/10_allpole/391_consumers_actuators/10_engines/moteur_tri.elmt"

        k1 = writer.place_element(folio, coil_path, x=300, y=200, designation="K1")
        m1 = writer.place_element(folio, motor_path, x=300, y=400, designation="M1")
        writer.connect(folio, k1, "A2", m1, "V", label="W1")

        # Save .qet
        qet_path = tmp_path / "integration.qet"
        writer.save(project, qet_path)
        assert qet_path.exists()

        # Render SVG
        renderer = SVGRenderer(renderer_element_db)
        svg = renderer.render(project, folio_index=0)
        assert "<svg" in svg
        assert "</svg>" in svg

        # Save SVG
        svg_path = tmp_path / "integration.svg"
        renderer.render_to_file(project, folio_index=0, filepath=svg_path)
        assert svg_path.exists()

    def test_empty_folio_renders(self, renderer_element_db):
        from src.renderer.svg_renderer import SVGRenderer

        project = QETProject(title="Empty", folios=[Folio(title="Empty Sheet", order=1)])
        renderer = SVGRenderer(renderer_element_db)
        svg = renderer.render(project, folio_index=0)
        assert "<svg" in svg
        assert "<!-- titleblock -->" in svg

    def test_rotated_element_renders(self, renderer_element_db):
        from src.renderer.svg_renderer import SVGRenderer

        coil_path = "10_electric/10_allpole/310_relays_contactors_contacts/01_coils/bobine3.elmt"
        pe = PlacedElement(
            uuid="{pe-rot-int}",
            elmt_path="common://" + coil_path,
            x=500.0, y=300.0, z=10.0,
            orientation=2,  # 180 degrees
            designation="K5",
            prefix="K",
            terminals=[
                PlacedTerminal(uuid="{pt-k5-a1}", name="A1", id=0, x=0.0, y=-20.0, orientation=0),
                PlacedTerminal(uuid="{pt-k5-a2}", name="A2", id=1, x=0.0, y=20.0, orientation=2),
            ],
            dynamic_texts=[],
            links_uuids=[],
            element_informations={"label": "K5"},
        )
        folio = Folio(title="Rotated", order=1, elements=[pe])
        project = QETProject(title="Rotation Test", folios=[folio])

        renderer = SVGRenderer(renderer_element_db)
        svg = renderer.render(project, folio_index=0)
        assert "rotate(180)" in svg
        assert "K5" in svg
