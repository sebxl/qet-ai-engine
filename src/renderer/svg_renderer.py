"""SVG Renderer for QET schematics -- visual self-verification (QET-3).

Converts QETProject/Folio data models into SVG strings for visual inspection.
All render functions produce SVG string fragments using string formatting
(not xml.etree) for simplicity.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape

from src.element_db.models import (
    ElementRecord,
    GraphicPrimitive,
    Terminal,
    terminal_absolute_position,
)
from src.writer.models import (
    Conductor,
    Folio,
    PlacedElement,
    PlacedTerminal,
    QETProject,
)


# ── Helpers ───────────────────────────────────────────────────────────────

def _strip_common_prefix(path: str) -> str:
    """Strip the ``common://`` prefix from element paths if present."""
    if path.startswith("common://"):
        return path[len("common://"):]
    return path


# ── Folio constants ───────────────────────────────────────────────────────
FOLIO_COLS = 17
FOLIO_COL_SIZE = 60
FOLIO_ROWS = 8
FOLIO_ROW_SIZE = 80
HEADER_HEIGHT = 20   # column header height
HEADER_WIDTH = 20    # row header width
MARGIN = 5
GRID_SPACING = 10

# Total drawing area (inside headers)
DRAWING_WIDTH = FOLIO_COLS * FOLIO_COL_SIZE   # 1020
DRAWING_HEIGHT = FOLIO_ROWS * FOLIO_ROW_SIZE  # 640

# Full SVG canvas (with headers and margin)
CANVAS_WIDTH = MARGIN + HEADER_WIDTH + DRAWING_WIDTH + MARGIN   # 1050
CANVAS_HEIGHT = MARGIN + HEADER_HEIGHT + DRAWING_HEIGHT + MARGIN  # 670


# ── Style constants ───────────────────────────────────────────────────────
LINE_WEIGHT_MAP: dict[str, str] = {
    "none": "0",
    "thin": "0.5",
    "normal": "1",
    "hight": "2",
    "eleve": "3",
}

LINE_STYLE_MAP: dict[str, str | None] = {
    "normal": None,
    "dashed": "6,3",
    "dotted": "2,2",
    "dashdotted": "6,3,2,3",
}


# ===========================================================================
# Cycle 1: Style Parsing Helper
# ===========================================================================

def _parse_style(style_str: str) -> dict[str, str]:
    """Parse a QET style string into SVG attribute dict.

    Example input: "line-style:normal;line-weight:normal;filling:none;color:black"
    Returns: {"stroke": "black", "stroke-width": "1", "fill": "none"}
    """
    props: dict[str, str] = {}
    if style_str:
        for part in style_str.split(";"):
            part = part.strip()
            if ":" in part:
                key, value = part.split(":", 1)
                props[key.strip()] = value.strip()

    result: dict[str, str] = {}

    # stroke color
    color = props.get("color", "black")
    result["stroke"] = color

    # stroke-width
    weight = props.get("line-weight", "normal")
    result["stroke-width"] = LINE_WEIGHT_MAP.get(weight, "1")

    # fill
    filling = props.get("filling", "none")
    result["fill"] = filling

    # stroke-dasharray
    line_style = props.get("line-style", "normal")
    dasharray = LINE_STYLE_MAP.get(line_style)
    if dasharray is not None:
        result["stroke-dasharray"] = dasharray

    return result


def _style_attrs(style_str: str) -> str:
    """Convert a QET style string into inline SVG attribute string."""
    d = _parse_style(style_str)
    return " ".join(f'{k}="{v}"' for k, v in d.items())


# ===========================================================================
# Cycle 2: Line Primitive
# ===========================================================================

def _render_line(prim: GraphicPrimitive) -> str:
    """Render a QET line primitive to SVG <line>."""
    a = prim.attributes
    style = _style_attrs(a.get("style", ""))
    return (
        f'<line x1="{a["x1"]}" y1="{a["y1"]}" '
        f'x2="{a["x2"]}" y2="{a["y2"]}" {style}/>'
    )


# ===========================================================================
# Cycle 3: Rect Primitive
# ===========================================================================

def _render_rect(prim: GraphicPrimitive) -> str:
    """Render a QET rect primitive to SVG <rect>."""
    a = prim.attributes
    style = _style_attrs(a.get("style", ""))
    rx = a.get("rx", "0")
    ry = a.get("ry", "0")
    return (
        f'<rect x="{a["x"]}" y="{a["y"]}" '
        f'width="{a["width"]}" height="{a["height"]}" '
        f'rx="{rx}" ry="{ry}" {style}/>'
    )


# ===========================================================================
# Cycle 4: Ellipse Primitive
# ===========================================================================

def _render_ellipse(prim: GraphicPrimitive) -> str:
    """Render a QET ellipse primitive to SVG <ellipse>.

    QET specifies bounding box (x, y, width, height).
    SVG needs center + radii.
    """
    a = prim.attributes
    x = float(a["x"])
    y = float(a["y"])
    w = float(a["width"])
    h = float(a["height"])

    cx = x + w / 2
    cy = y + h / 2
    rx = w / 2
    ry = h / 2

    style = _style_attrs(a.get("style", ""))
    return (
        f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" {style}/>'
    )


# ===========================================================================
# Cycle 5: Circle Primitive
# ===========================================================================

def _render_circle(prim: GraphicPrimitive) -> str:
    """Render a QET circle primitive to SVG <circle>.

    QET specifies bounding box corner (x, y) and diameter.
    SVG needs center + radius.
    """
    a = prim.attributes
    x = float(a["x"])
    y = float(a["y"])
    d = float(a["diameter"])

    cx = x + d / 2
    cy = y + d / 2
    r = d / 2

    style = _style_attrs(a.get("style", ""))
    return f'<circle cx="{cx}" cy="{cy}" r="{r}" {style}/>'


# ===========================================================================
# Cycle 6: Arc Primitive
# ===========================================================================

def _render_arc(prim: GraphicPrimitive) -> str:
    """Render a QET arc to SVG <path> with arc command.

    QET uses Qt convention:
    - Bounding box (x, y, width, height) + start angle + sweep angle
    - Angles in degrees, positive = counter-clockwise from east (3 o'clock)
    - In screen coordinates (Y down), CCW in math = CW visually

    SVG arc: M sx,sy A rx,ry x-rotation large-arc-flag sweep-flag ex,ey
    """
    a = prim.attributes
    x = float(a["x"])
    y = float(a["y"])
    w = float(a["width"])
    h = float(a["height"])
    start_deg = float(a["start"])
    angle_deg = float(a["angle"])

    cx = x + w / 2
    cy = y + h / 2
    rx = w / 2
    ry = h / 2

    start_rad = math.radians(start_deg)
    end_rad = math.radians(start_deg + angle_deg)

    # Start point (Y inverted for screen coords)
    sx = cx + rx * math.cos(start_rad)
    sy = cy - ry * math.sin(start_rad)

    # End point
    ex = cx + rx * math.cos(end_rad)
    ey = cy - ry * math.sin(end_rad)

    # large-arc-flag: 1 if |angle| > 180
    large_arc = 1 if abs(angle_deg) > 180 else 0

    # sweep-flag: 0 for positive angle (CCW in math = CW on screen for SVG)
    # 1 for negative angle
    sweep = 0 if angle_deg >= 0 else 1

    style = _style_attrs(a.get("style", ""))

    return (
        f'<path d="M {sx:.2f},{sy:.2f} '
        f'A {rx} {ry} 0 {large_arc} {sweep} {ex:.2f},{ey:.2f}" '
        f'{style}/>'
    )


# ===========================================================================
# Cycle 7: Polygon Primitive
# ===========================================================================

def _render_polygon(prim: GraphicPrimitive) -> str:
    """Render a QET polygon to SVG <polygon> or <polyline>.

    Points are extracted from x1,y1, x2,y2, ... xN,yN attributes.
    If closed="true" -> <polygon>, otherwise <polyline>.
    """
    a = prim.attributes
    points: list[str] = []
    i = 1
    while f"x{i}" in a:
        px = a[f"x{i}"]
        py = a[f"y{i}"]
        points.append(f"{px},{py}")
        i += 1

    points_str = " ".join(points)
    closed = a.get("closed", "true").lower() == "true"

    tag = "polygon" if closed else "polyline"
    style_dict = _parse_style(a.get("style", ""))
    if not closed:
        style_dict["fill"] = "none"
    style_str_out = " ".join(f'{k}="{v}"' for k, v in style_dict.items())
    return f'<{tag} points="{points_str}" {style_str_out}/>'


# ===========================================================================
# Cycle 8: Text Primitive
# ===========================================================================

def _parse_font(font_str: str) -> tuple[str, str]:
    """Parse QET font string to (family, size).

    Format: "Liberation Sans,11,-1,5,50,0,0,0,0,0,Regular"
    """
    parts = font_str.split(",")
    family = parts[0] if parts else "sans-serif"
    size = parts[1] if len(parts) > 1 else "10"
    return family, size


def _render_text(prim: GraphicPrimitive) -> str:
    """Render a QET text primitive to SVG <text>.

    Handles font parsing, color, rotation, and &#10; newlines via <tspan>.
    """
    a = prim.attributes
    x = a.get("x", "0")
    y = a.get("y", "0")
    rotation = a.get("rotation", "0")
    color = a.get("color", "#000000")
    font_str = a.get("font", "sans-serif,10")
    text_content = a.get("text", "")

    family, size = _parse_font(font_str)

    # Build transform if rotated
    transform = ""
    if rotation != "0":
        transform = f' transform="rotate({rotation},{x},{y})"'

    # Handle multiline text (&#10; separator)
    lines = text_content.split("&#10;")

    if len(lines) == 1:
        return (
            f'<text x="{x}" y="{y}" fill="{color}" '
            f'font-family="{family}" font-size="{size}"{transform}>'
            f'{xml_escape(lines[0])}</text>'
        )

    # Multiline: use tspan elements
    tspans = []
    for idx, line in enumerate(lines):
        escaped_line = xml_escape(line)
        if idx == 0:
            tspans.append(f'<tspan x="{x}" dy="0">{escaped_line}</tspan>')
        else:
            tspans.append(f'<tspan x="{x}" dy="{size}">{escaped_line}</tspan>')

    inner = "".join(tspans)
    return (
        f'<text x="{x}" y="{y}" fill="{color}" '
        f'font-family="{family}" font-size="{size}"{transform}>'
        f'{inner}</text>'
    )


# ===========================================================================
# Cycle 9: Primitive Dispatcher
# ===========================================================================

_PRIMITIVE_RENDERERS: dict[str, Callable[[GraphicPrimitive], str]] = {
    "line": _render_line,
    "rect": _render_rect,
    "ellipse": _render_ellipse,
    "circle": _render_circle,
    "arc": _render_arc,
    "polygon": _render_polygon,
    "text": _render_text,
}


def _render_primitive(prim: GraphicPrimitive) -> str:
    """Dispatch a graphic primitive to the correct renderer.

    Unknown types return an SVG comment.
    """
    renderer = _PRIMITIVE_RENDERERS.get(prim.type)
    if renderer is not None:
        return renderer(prim)
    return f"<!-- unknown primitive: {xml_escape(prim.type)} -->"


# ===========================================================================
# Cycle 10: Render Single Element (with transform)
# ===========================================================================

def _render_element(placed: PlacedElement, record: ElementRecord) -> str:
    """Render a placed element as an SVG <g> group with transform.

    Wraps all graphic primitives in a group translated to the element's
    position and rotated by orientation * 90 degrees.
    """
    angle = placed.orientation * 90
    transform_parts = [f"translate({placed.x},{placed.y})"]
    if angle != 0:
        transform_parts.append(f"rotate({angle})")
    transform = " ".join(transform_parts)

    parts: list[str] = []
    escaped_designation = xml_escape(placed.designation, {'"': '&quot;'})
    parts.append(f'<g transform="{transform}" class="element" data-designation="{escaped_designation}">')

    for prim in record.graphic_primitives:
        parts.append(f"  {_render_primitive(prim)}")

    parts.append("</g>")

    # Designation label (placed near the element)
    label_x = placed.x + 25
    label_y = placed.y - 10
    parts.append(
        f'<text x="{label_x}" y="{label_y}" fill="#333333" '
        f'font-family="Liberation Sans" font-size="9" class="designation-label">'
        f'{xml_escape(placed.designation)}</text>'
    )

    return "\n".join(parts)


# ===========================================================================
# Cycle 11: Terminal Markers
# ===========================================================================

def _render_terminal_markers(placed: PlacedElement, record: ElementRecord) -> str:
    """Render colored circle markers at absolute terminal positions.

    Creates a Terminal object from each PlacedTerminal to use the existing
    terminal_absolute_position function.
    """
    parts: list[str] = []
    for pt in placed.terminals:
        # Create a Terminal from PlacedTerminal for position calculation
        temp_terminal = Terminal(
            uuid=pt.uuid,
            name=pt.name,
            x=pt.x,
            y=pt.y,
            orientation="n",  # orientation not used for position calc
            type="Generic",
        )
        abs_x, abs_y = terminal_absolute_position(
            temp_terminal, placed.x, placed.y, placed.orientation
        )
        parts.append(
            f'<circle cx="{abs_x}" cy="{abs_y}" r="3" '
            f'fill="#e74c3c" stroke="#c0392b" stroke-width="0.5" '
            f'class="terminal-marker" data-uuid="{pt.uuid}" data-name="{pt.name}"/>'
        )
    return "\n".join(parts)


# ===========================================================================
# Cycle 12: Render Conductor
# ===========================================================================

def _render_conductor(
    conductor: Conductor,
    terminal_positions_map: dict[str, tuple[float, float]],
) -> str:
    """Render a conductor as an SVG line between two terminal positions.

    If either terminal position is unknown, returns an SVG comment.
    """
    pos1 = terminal_positions_map.get(conductor.terminal1_uuid)
    pos2 = terminal_positions_map.get(conductor.terminal2_uuid)

    if pos1 is None or pos2 is None:
        return f"<!-- conductor skipped: missing terminal position -->"

    x1, y1 = pos1
    x2, y2 = pos2

    parts: list[str] = []
    parts.append(
        f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
        f'stroke="#2980b9" stroke-width="1.5" class="conductor"/>'
    )

    # Label at midpoint if present
    if conductor.label:
        mx = (x1 + x2) / 2
        my = (y1 + y2) / 2
        parts.append(
            f'<text x="{mx}" y="{my - 5}" fill="#2980b9" '
            f'font-family="Liberation Sans" font-size="8" '
            f'text-anchor="middle" class="conductor-label">'
            f'{xml_escape(conductor.label)}</text>'
        )

    return "\n".join(parts)


# ===========================================================================
# Cycle 13: Build Terminal Position Map
# ===========================================================================

def _build_terminal_positions(
    folio: Folio,
    element_db: dict[str, ElementRecord],
) -> dict[str, tuple[float, float]]:
    """Build a map of terminal UUID -> absolute (x, y) position.

    Iterates all placed elements on the folio, looks up their ElementRecord
    (stripping the "common://" prefix), and computes absolute positions.
    """
    positions: dict[str, tuple[float, float]] = {}

    for pe in folio.elements:
        path = _strip_common_prefix(pe.elmt_path)
        record = element_db.get(path)
        if record is None:
            continue

        for pt in pe.terminals:
            temp_terminal = Terminal(
                uuid=pt.uuid,
                name=pt.name,
                x=pt.x,
                y=pt.y,
                orientation="n",
                type="Generic",
            )
            abs_x, abs_y = terminal_absolute_position(
                temp_terminal, pe.x, pe.y, pe.orientation
            )
            positions[pt.uuid] = (abs_x, abs_y)

    return positions


# ===========================================================================
# Cycle 14: Title Block
# ===========================================================================

def _render_title_block(
    folio: Folio,
    project: QETProject,
    width: float,
    height: float,
) -> str:
    """Render a simplified title block at the bottom of the folio."""
    parts: list[str] = []
    parts.append("<!-- titleblock -->")

    # Title block rectangle
    tb_x = MARGIN + HEADER_WIDTH
    tb_y = height - 40
    tb_w = width - 2 * MARGIN - HEADER_WIDTH
    tb_h = 35

    parts.append(
        f'<rect x="{tb_x}" y="{tb_y}" width="{tb_w}" height="{tb_h}" '
        f'fill="none" stroke="#333333" stroke-width="1"/>'
    )

    # Title text
    parts.append(
        f'<text x="{tb_x + 10}" y="{tb_y + 15}" fill="#333333" '
        f'font-family="Liberation Sans" font-size="11" font-weight="bold">'
        f'{xml_escape(folio.title)}</text>'
    )

    # Author and project info
    parts.append(
        f'<text x="{tb_x + 10}" y="{tb_y + 28}" fill="#666666" '
        f'font-family="Liberation Sans" font-size="9">'
        f'{xml_escape(project.title)} | {xml_escape(project.author)} | Folio {folio.order}</text>'
    )

    return "\n".join(parts)


# ===========================================================================
# Cycle 15: Grid Lines
# ===========================================================================

def _render_grid(width: float, height: float, spacing: int = 10) -> str:
    """Render a grid of light-colored lines at the given spacing."""
    parts: list[str] = []

    # Vertical lines
    x = 0
    while x <= width:
        parts.append(
            f'<line x1="{x}" y1="0" x2="{x}" y2="{height}" '
            f'stroke="#e0e0e0" stroke-width="0.25"/>'
        )
        x += spacing

    # Horizontal lines
    y = 0
    while y <= height:
        parts.append(
            f'<line x1="0" y1="{y}" x2="{width}" y2="{y}" '
            f'stroke="#e0e0e0" stroke-width="0.25"/>'
        )
        y += spacing

    return "\n".join(parts)


# ===========================================================================
# Cycle 16: SVGRenderer class
# ===========================================================================

class SVGRenderer:
    """Renders QET projects/folios as SVG for visual verification."""

    def __init__(self, element_db: dict[str, ElementRecord]) -> None:
        self._element_db = element_db

    def render(
        self,
        project: QETProject,
        folio_index: int,
        show_grid: bool = False,
    ) -> str:
        """Render a single folio of a QET project as an SVG string.

        Args:
            project: The QET project.
            folio_index: Zero-based index of the folio to render.
            show_grid: Whether to show the 10x10 grid.

        Returns:
            Complete SVG document as a string.

        Raises:
            IndexError: If folio_index is out of range.
        """
        if folio_index < 0 or folio_index >= len(project.folios):
            raise IndexError(
                f"Folio index {folio_index} out of range "
                f"(project has {len(project.folios)} folios)"
            )

        folio = project.folios[folio_index]
        parts: list[str] = []

        # SVG root
        parts.append(
            f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'width="{CANVAS_WIDTH}" height="{CANVAS_HEIGHT}" '
            f'viewBox="0 0 {CANVAS_WIDTH} {CANVAS_HEIGHT}">'
        )

        # Background
        parts.append(
            f'<rect x="0" y="0" width="{CANVAS_WIDTH}" height="{CANVAS_HEIGHT}" fill="white"/>'
        )

        # Drawing area border
        draw_x = MARGIN + HEADER_WIDTH
        draw_y = MARGIN + HEADER_HEIGHT
        parts.append(
            f'<rect x="{draw_x}" y="{draw_y}" '
            f'width="{DRAWING_WIDTH}" height="{DRAWING_HEIGHT}" '
            f'fill="none" stroke="#333333" stroke-width="0.5"/>'
        )

        # Grid (optional)
        if show_grid:
            parts.append("<!-- grid -->")
            # Offset grid to drawing area
            parts.append(f'<g transform="translate({draw_x},{draw_y})">')
            parts.append(_render_grid(DRAWING_WIDTH, DRAWING_HEIGHT, GRID_SPACING))
            parts.append("</g>")

        # Column headers (1-17)
        parts.append("<!-- column headers -->")
        for col in range(FOLIO_COLS):
            cx = draw_x + col * FOLIO_COL_SIZE + FOLIO_COL_SIZE / 2
            cy = MARGIN + HEADER_HEIGHT / 2 + 4
            parts.append(
                f'<text x="{cx}" y="{cy}" fill="#333333" '
                f'font-family="Liberation Sans" font-size="9" text-anchor="middle">'
                f'{col + 1}</text>'
            )

        # Row headers (A-H)
        parts.append("<!-- row headers -->")
        row_labels = [chr(ord("A") + i) for i in range(FOLIO_ROWS)]
        for row_idx, label in enumerate(row_labels):
            rx = MARGIN + HEADER_WIDTH / 2
            ry = draw_y + row_idx * FOLIO_ROW_SIZE + FOLIO_ROW_SIZE / 2 + 4
            parts.append(
                f'<text x="{rx}" y="{ry}" fill="#333333" '
                f'font-family="Liberation Sans" font-size="9" text-anchor="middle">'
                f'{label}</text>'
            )

        # Build terminal positions for conductors
        term_pos = _build_terminal_positions(folio, self._element_db)

        # Elements
        parts.append("<!-- elements -->")
        for pe in folio.elements:
            path = _strip_common_prefix(pe.elmt_path)
            record = self._element_db.get(path)
            if record is not None:
                parts.append(_render_element(pe, record))
                parts.append(_render_terminal_markers(pe, record))

        # Conductors
        parts.append("<!-- conductors -->")
        for cond in folio.conductors:
            parts.append(_render_conductor(cond, term_pos))

        # Title block
        parts.append(_render_title_block(folio, project, CANVAS_WIDTH, CANVAS_HEIGHT))

        parts.append("</svg>")
        return "\n".join(parts)

    # ===================================================================
    # Cycle 17: render_to_file
    # ===================================================================

    def render_to_file(
        self,
        project: QETProject,
        folio_index: int,
        filepath: str | Path,
        show_grid: bool = False,
    ) -> None:
        """Render a folio and write it to an SVG file.

        Args:
            project: The QET project.
            folio_index: Zero-based index of the folio to render.
            filepath: Output file path.
            show_grid: Whether to show the grid.
        """
        svg_content = self.render(project, folio_index, show_grid=show_grid)
        Path(filepath).write_text(svg_content, encoding="utf-8")


# ===========================================================================
# Cycle 18: Calibration File Generation
# ===========================================================================

def generate_calibration(
    output_dir: str | Path,
    element_db: dict[str, ElementRecord],
) -> tuple[Path, Path]:
    """Generate calibration .qet and .svg files for visual comparison.

    Creates a simple project with elements from the DB (or test records),
    saves it as .qet via QETWriter, and renders it as .svg via SVGRenderer.

    Args:
        output_dir: Directory where files will be written.
        element_db: Element database dict.

    Returns:
        Tuple of (qet_path, svg_path).
    """
    from src.writer.qet_writer import QETWriter

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    writer = QETWriter(element_db=element_db)
    project = writer.create_project("Calibration", author="QET-AI Engine")
    folio = writer.add_folio(project, "Calibration Sheet")

    # Place available elements from the DB
    paths = list(element_db.keys())
    x_pos = 200.0
    placed_elements = []
    for i, path in enumerate(paths[:4]):  # max 4 elements
        designation = f"X{i + 1}"
        pe = writer.place_element(folio, path, x=x_pos, y=250.0, designation=designation)
        placed_elements.append(pe)
        x_pos += 150.0

    # Connect first two elements if we have at least two
    if len(placed_elements) >= 2:
        e1 = placed_elements[0]
        e2 = placed_elements[1]
        if e1.terminals and e2.terminals:
            t1_name = e1.terminals[-1].name  # last terminal of first
            t2_name = e2.terminals[0].name   # first terminal of second
            writer.connect(folio, e1, t1_name, e2, t2_name, label="Cal-W1")

    # Save .qet
    qet_path = output_dir / "calibration.qet"
    writer.save(project, qet_path)

    # Render .svg
    renderer = SVGRenderer(element_db)
    svg_path = output_dir / "calibration.svg"
    renderer.render_to_file(project, folio_index=0, filepath=svg_path)

    return qet_path, svg_path
