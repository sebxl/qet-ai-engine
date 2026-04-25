"""Tests for the Motor Starter Hauptstromkreis template (QET-4)."""

from __future__ import annotations

import pytest

from src.templates.base import BaseTemplate
from src.templates.motor_starter import MotorStarterTemplate
from src.writer import QETWriter


# ── Helper: deterministic writer factory ─────────────────────────────


def _make_writer(element_db):
    counter = iter(range(1000))
    return QETWriter(
        element_db=element_db,
        uuid_factory=lambda: "{" + f"test-uuid-{next(counter):04d}" + "}",
    )


# ── CYCLE 1: BaseTemplate ABC ───────────────────────────────────────


class TestBaseTemplate:
    """CYCLE 1: BaseTemplate is abstract with generate() method."""

    def test_base_template_is_abstract(self):
        """BaseTemplate cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseTemplate()  # type: ignore[abstract]

    def test_base_template_has_generate_method(self):
        """BaseTemplate defines abstract generate()."""
        assert hasattr(BaseTemplate, "generate")


# ── CYCLE 2: MotorStarterTemplate instantiation + validation ────────


class TestMotorStarterInstantiation:
    """CYCLE 2: Instantiation and parameter validation."""

    def test_is_subclass_of_base_template(self, motor_starter_element_db):
        writer = _make_writer(motor_starter_element_db)
        tmpl = MotorStarterTemplate(writer)
        assert isinstance(tmpl, BaseTemplate)

    def test_instantiation(self, motor_starter_element_db):
        writer = _make_writer(motor_starter_element_db)
        tmpl = MotorStarterTemplate(writer)
        assert tmpl is not None

    def test_validate_params_missing_key_raises(self, motor_starter_element_db):
        writer = _make_writer(motor_starter_element_db)
        tmpl = MotorStarterTemplate(writer)
        with pytest.raises(ValueError, match="motor_power_kw"):
            tmpl.generate({})

    def test_validate_params_accepts_valid(
        self, motor_starter_element_db, valid_motor_starter_params
    ):
        writer = _make_writer(motor_starter_element_db)
        tmpl = MotorStarterTemplate(writer)
        # Should not raise
        project = tmpl.generate(valid_motor_starter_params)
        assert project is not None


# ── CYCLE 3: Project and Folio creation ──────────────────────────────


class TestProjectAndFolio:
    """CYCLE 3: generate() returns QETProject with 1 folio."""

    def test_returns_qet_project(
        self, motor_starter_element_db, valid_motor_starter_params
    ):
        from src.writer.models import QETProject

        writer = _make_writer(motor_starter_element_db)
        tmpl = MotorStarterTemplate(writer)
        project = tmpl.generate(valid_motor_starter_params)
        assert isinstance(project, QETProject)

    def test_project_title_contains_power(
        self, motor_starter_element_db, valid_motor_starter_params
    ):
        writer = _make_writer(motor_starter_element_db)
        tmpl = MotorStarterTemplate(writer)
        project = tmpl.generate(valid_motor_starter_params)
        assert "1.5" in project.title
        assert "kW" in project.title

    def test_one_folio(
        self, motor_starter_element_db, valid_motor_starter_params
    ):
        writer = _make_writer(motor_starter_element_db)
        tmpl = MotorStarterTemplate(writer)
        project = tmpl.generate(valid_motor_starter_params)
        assert len(project.folios) == 1

    def test_folio_title(
        self, motor_starter_element_db, valid_motor_starter_params
    ):
        writer = _make_writer(motor_starter_element_db)
        tmpl = MotorStarterTemplate(writer)
        project = tmpl.generate(valid_motor_starter_params)
        assert project.folios[0].title == "Hauptstromkreis"


# ── CYCLE 4: Element placement ──────────────────────────────────────


class TestElementPlacement:
    """CYCLE 4: 4 elements placed with correct paths and positions."""

    @pytest.fixture
    def folio(self, motor_starter_element_db, valid_motor_starter_params):
        writer = _make_writer(motor_starter_element_db)
        tmpl = MotorStarterTemplate(writer)
        project = tmpl.generate(valid_motor_starter_params)
        return project.folios[0]

    def test_four_elements_placed(self, folio):
        assert len(folio.elements) == 4

    def test_element_designations(self, folio):
        designations = [e.designation for e in folio.elements]
        assert designations == ["F1", "K1", "F2", "M1"]

    def test_element_paths(self, folio):
        paths = [e.elmt_path for e in folio.elements]
        assert paths[0].endswith("dis_mag_term_3f-2.elmt")
        assert paths[1].endswith("com_puiss4.elmt")
        assert paths[2].endswith("relais_therm4.elmt")
        assert paths[3].endswith("moteur_tri.elmt")

    def test_all_paths_start_with_common(self, folio):
        for e in folio.elements:
            assert e.elmt_path.startswith("common://")

    def test_vertical_order(self, folio):
        """Elements must be stacked vertically: F1 < K1 < F2 < M1."""
        ys = [e.y for e in folio.elements]
        assert ys[0] < ys[1] < ys[2] < ys[3]

    def test_positions_on_10px_grid(self, folio):
        """All element positions must be on the 10px grid."""
        for e in folio.elements:
            assert e.x % 10 == 0, f"{e.designation} x={e.x} not on 10px grid"
            assert e.y % 10 == 0, f"{e.designation} y={e.y} not on 10px grid"

    def test_f1_position(self, folio):
        f1 = folio.elements[0]
        assert f1.x == 300
        assert f1.y == 150

    def test_k1_position(self, folio):
        k1 = folio.elements[1]
        assert k1.x == 300
        assert k1.y == 250

    def test_f2_position(self, folio):
        """Thermal relay at x=280 so its x=0 terminal aligns with others at x=300-20."""
        f2 = folio.elements[2]
        assert f2.x == 280
        assert f2.y == 330

    def test_m1_position(self, folio):
        m1 = folio.elements[3]
        assert m1.x == 300
        assert m1.y == 420

    def test_breaker_has_6_terminals(self, folio):
        f1 = folio.elements[0]
        assert len(f1.terminals) == 6

    def test_contactor_has_6_terminals(self, folio):
        k1 = folio.elements[1]
        assert len(k1.terminals) == 6

    def test_thermal_relay_has_6_terminals(self, folio):
        f2 = folio.elements[2]
        assert len(f2.terminals) == 6

    def test_motor_has_4_terminals(self, folio):
        m1 = folio.elements[3]
        assert len(m1.terminals) == 4


# ── CYCLE 5: Connect-by-index helper ────────────────────────────────


class TestConnectByIndex:
    """CYCLE 5: _connect_by_index creates valid Conductor from terminal indices."""

    def test_connect_by_index_creates_conductor(
        self, motor_starter_element_db, valid_motor_starter_params
    ):
        from src.templates.motor_starter import _connect_by_index
        from src.writer.models import Conductor, Folio

        writer = _make_writer(motor_starter_element_db)
        tmpl = MotorStarterTemplate(writer)
        project = tmpl.generate(valid_motor_starter_params)
        folio = project.folios[0]

        # Clear conductors from generate() to test helper in isolation
        original_count = len(folio.conductors)

        # Create a standalone folio with two elements for isolated test
        test_folio = Folio(title="test", order=1)
        k1 = folio.elements[1]  # contactor
        f2 = folio.elements[2]  # thermal relay

        cond = _connect_by_index(test_folio, k1, 1, f2, 0, label="L1")
        assert isinstance(cond, Conductor)
        assert cond.terminal1_uuid == k1.terminals[1].uuid
        assert cond.terminal2_uuid == f2.terminals[0].uuid
        assert cond.element1_uuid == k1.uuid
        assert cond.element2_uuid == f2.uuid
        assert cond.label == "L1"

    def test_connect_by_index_appends_to_folio(
        self, motor_starter_element_db, valid_motor_starter_params
    ):
        from src.templates.motor_starter import _connect_by_index
        from src.writer.models import Folio

        writer = _make_writer(motor_starter_element_db)
        tmpl = MotorStarterTemplate(writer)
        project = tmpl.generate(valid_motor_starter_params)

        test_folio = Folio(title="test", order=1)
        k1 = project.folios[0].elements[1]
        f2 = project.folios[0].elements[2]

        assert len(test_folio.conductors) == 0
        _connect_by_index(test_folio, k1, 1, f2, 0)
        assert len(test_folio.conductors) == 1

    def test_connect_by_index_out_of_range_raises(
        self, motor_starter_element_db, valid_motor_starter_params
    ):
        from src.templates.motor_starter import _connect_by_index
        from src.writer.models import Folio

        writer = _make_writer(motor_starter_element_db)
        tmpl = MotorStarterTemplate(writer)
        project = tmpl.generate(valid_motor_starter_params)

        test_folio = Folio(title="test", order=1)
        k1 = project.folios[0].elements[1]
        f2 = project.folios[0].elements[2]

        with pytest.raises(IndexError):
            _connect_by_index(test_folio, k1, 99, f2, 0)


# ── CYCLE 6: Conductor generation (9 phase connections) ─────────────


class TestConductorGeneration:
    """CYCLE 6: All 9 phase conductors are generated correctly."""

    @pytest.fixture
    def folio(self, motor_starter_element_db, valid_motor_starter_params):
        writer = _make_writer(motor_starter_element_db)
        tmpl = MotorStarterTemplate(writer)
        project = tmpl.generate(valid_motor_starter_params)
        return project.folios[0]

    def test_nine_conductors(self, folio):
        assert len(folio.conductors) == 9

    def test_conductors_reference_valid_elements(self, folio):
        element_uuids = {e.uuid for e in folio.elements}
        for c in folio.conductors:
            assert c.element1_uuid in element_uuids, (
                f"Conductor element1_uuid {c.element1_uuid} not in elements"
            )
            assert c.element2_uuid in element_uuids, (
                f"Conductor element2_uuid {c.element2_uuid} not in elements"
            )

    def test_conductors_reference_valid_terminals(self, folio):
        all_terminal_uuids = set()
        for e in folio.elements:
            for t in e.terminals:
                all_terminal_uuids.add(t.uuid)

        for c in folio.conductors:
            assert c.terminal1_uuid in all_terminal_uuids, (
                f"Conductor terminal1_uuid {c.terminal1_uuid} not found"
            )
            assert c.terminal2_uuid in all_terminal_uuids, (
                f"Conductor terminal2_uuid {c.terminal2_uuid} not found"
            )

    def test_three_conductors_per_segment(self, folio):
        """3 conductors F1->K1, 3 conductors K1->F2, 3 conductors F2->M1."""
        f1, k1, f2, m1 = [e.uuid for e in folio.elements]

        f1_to_k1 = [c for c in folio.conductors
                     if c.element1_uuid == f1 and c.element2_uuid == k1]
        k1_to_f2 = [c for c in folio.conductors
                     if c.element1_uuid == k1 and c.element2_uuid == f2]
        f2_to_m1 = [c for c in folio.conductors
                     if c.element1_uuid == f2 and c.element2_uuid == m1]

        assert len(f1_to_k1) == 3, f"Expected 3 F1->K1 conductors, got {len(f1_to_k1)}"
        assert len(k1_to_f2) == 3, f"Expected 3 K1->F2 conductors, got {len(k1_to_f2)}"
        assert len(f2_to_m1) == 3, f"Expected 3 F2->M1 conductors, got {len(f2_to_m1)}"

    def test_no_duplicate_conductors(self, folio):
        """No two conductors share both terminal UUIDs."""
        seen = set()
        for c in folio.conductors:
            pair = frozenset([c.terminal1_uuid, c.terminal2_uuid])
            assert pair not in seen, f"Duplicate conductor: {pair}"
            seen.add(pair)

    def test_f1_to_k1_terminal_mapping(self, folio):
        """F1 bottom terminals 2,4,6 connect to K1 top terminals idx 0,2,4."""
        f1 = folio.elements[0]
        k1 = folio.elements[1]

        # F1 terminal named "2" -> K1 terminal idx 0
        f1_t2 = next(t for t in f1.terminals if t.name == "2")
        k1_t0 = k1.terminals[0]
        cond_l1 = next(c for c in folio.conductors
                       if c.terminal1_uuid == f1_t2.uuid)
        assert cond_l1.terminal2_uuid == k1_t0.uuid

        # F1 terminal named "4" -> K1 terminal idx 2
        f1_t4 = next(t for t in f1.terminals if t.name == "4")
        k1_t2 = k1.terminals[2]
        cond_l2 = next(c for c in folio.conductors
                       if c.terminal1_uuid == f1_t4.uuid)
        assert cond_l2.terminal2_uuid == k1_t2.uuid

        # F1 terminal named "6" -> K1 terminal idx 4
        f1_t6 = next(t for t in f1.terminals if t.name == "6")
        k1_t4 = k1.terminals[4]
        cond_l3 = next(c for c in folio.conductors
                       if c.terminal1_uuid == f1_t6.uuid)
        assert cond_l3.terminal2_uuid == k1_t4.uuid

    def test_f2_to_m1_terminal_mapping(self, folio):
        """F2 bottom terminals idx 1,3,5 connect to M1 U1,V1,W1."""
        f2 = folio.elements[2]
        m1 = folio.elements[3]

        # F2 idx 1 -> M1 "U1"
        f2_t1 = f2.terminals[1]
        m1_u1 = next(t for t in m1.terminals if t.name == "U1")
        cond = next(c for c in folio.conductors
                    if c.terminal1_uuid == f2_t1.uuid)
        assert cond.terminal2_uuid == m1_u1.uuid

        # F2 idx 3 -> M1 "V1"
        f2_t3 = f2.terminals[3]
        m1_v1 = next(t for t in m1.terminals if t.name == "V1")
        cond = next(c for c in folio.conductors
                    if c.terminal1_uuid == f2_t3.uuid)
        assert cond.terminal2_uuid == m1_v1.uuid

        # F2 idx 5 -> M1 "W1"
        f2_t5 = f2.terminals[5]
        m1_w1 = next(t for t in m1.terminals if t.name == "W1")
        cond = next(c for c in folio.conductors
                    if c.terminal1_uuid == f2_t5.uuid)
        assert cond.terminal2_uuid == m1_w1.uuid


# ── CYCLE 7: Open terminal validation ───────────────────────────────


class TestOpenTerminals:
    """CYCLE 7: F1 top terminals and M1 PE intentionally unconnected."""

    @pytest.fixture
    def folio(self, motor_starter_element_db, valid_motor_starter_params):
        writer = _make_writer(motor_starter_element_db)
        tmpl = MotorStarterTemplate(writer)
        project = tmpl.generate(valid_motor_starter_params)
        return project.folios[0]

    def _connected_terminal_uuids(self, folio):
        connected = set()
        for c in folio.conductors:
            connected.add(c.terminal1_uuid)
            connected.add(c.terminal2_uuid)
        return connected

    def test_f1_top_terminals_unconnected(self, folio):
        """F1 supply-side terminals 1,3,5 are intentionally open."""
        f1 = folio.elements[0]
        connected = self._connected_terminal_uuids(folio)

        f1_t1 = next(t for t in f1.terminals if t.name == "1")
        f1_t3 = next(t for t in f1.terminals if t.name == "3")
        f1_t5 = next(t for t in f1.terminals if t.name == "5")

        assert f1_t1.uuid not in connected
        assert f1_t3.uuid not in connected
        assert f1_t5.uuid not in connected

    def test_m1_pe_terminal_unconnected(self, folio):
        """Motor PE terminal is intentionally open in main circuit."""
        m1 = folio.elements[3]
        connected = self._connected_terminal_uuids(folio)

        m1_pe = next(t for t in m1.terminals if t.name == "PE")
        assert m1_pe.uuid not in connected

    def test_all_internal_terminals_connected(self, folio):
        """All other terminals (internal connections) must be connected."""
        connected = self._connected_terminal_uuids(folio)

        f1 = folio.elements[0]
        k1 = folio.elements[1]
        f2 = folio.elements[2]
        m1 = folio.elements[3]

        # F1 bottom terminals 2,4,6 must be connected
        for name in ("2", "4", "6"):
            t = next(t for t in f1.terminals if t.name == name)
            assert t.uuid in connected, f"F1 terminal '{name}' should be connected"

        # K1 all 6 terminals must be connected
        for i, t in enumerate(k1.terminals):
            assert t.uuid in connected, f"K1 terminal idx {i} should be connected"

        # F2 all 6 terminals must be connected
        for i, t in enumerate(f2.terminals):
            assert t.uuid in connected, f"F2 terminal idx {i} should be connected"

        # M1 U1, V1, W1 must be connected (PE is open)
        for name in ("U1", "V1", "W1"):
            t = next(t for t in m1.terminals if t.name == name)
            assert t.uuid in connected, f"M1 terminal '{name}' should be connected"


# ── CYCLE 8: Full .qet XML generation + validation ──────────────────


class TestQetXmlGeneration:
    """CYCLE 8: save() produces valid XML with correct structure."""

    def test_save_produces_valid_xml(
        self, motor_starter_element_db, valid_motor_starter_params, tmp_path
    ):
        import xml.etree.ElementTree as ET

        writer = _make_writer(motor_starter_element_db)
        tmpl = MotorStarterTemplate(writer)
        project = tmpl.generate(valid_motor_starter_params)

        filepath = tmp_path / "test_motor_starter.qet"
        writer.save(project, filepath)

        assert filepath.exists()

        # Parse the file -- must be valid XML
        tree = ET.parse(filepath)
        root = tree.getroot()
        assert root.tag == "project"

    def test_xml_has_project_attributes(
        self, motor_starter_element_db, valid_motor_starter_params, tmp_path
    ):
        import xml.etree.ElementTree as ET

        writer = _make_writer(motor_starter_element_db)
        tmpl = MotorStarterTemplate(writer)
        project = tmpl.generate(valid_motor_starter_params)

        filepath = tmp_path / "test_motor_starter.qet"
        writer.save(project, filepath)

        tree = ET.parse(filepath)
        root = tree.getroot()
        assert root.attrib["version"] == "0.90"
        assert "1.5" in root.attrib["title"]

    def test_xml_has_one_diagram(
        self, motor_starter_element_db, valid_motor_starter_params, tmp_path
    ):
        import xml.etree.ElementTree as ET

        writer = _make_writer(motor_starter_element_db)
        tmpl = MotorStarterTemplate(writer)
        project = tmpl.generate(valid_motor_starter_params)

        filepath = tmp_path / "test_motor_starter.qet"
        writer.save(project, filepath)

        tree = ET.parse(filepath)
        root = tree.getroot()
        diagrams = root.findall("diagram")
        assert len(diagrams) == 1

    def test_xml_has_four_elements(
        self, motor_starter_element_db, valid_motor_starter_params, tmp_path
    ):
        import xml.etree.ElementTree as ET

        writer = _make_writer(motor_starter_element_db)
        tmpl = MotorStarterTemplate(writer)
        project = tmpl.generate(valid_motor_starter_params)

        filepath = tmp_path / "test_motor_starter.qet"
        writer.save(project, filepath)

        tree = ET.parse(filepath)
        root = tree.getroot()
        diagram = root.find("diagram")
        elements = diagram.find("elements").findall("element")
        assert len(elements) == 4

    def test_xml_has_nine_conductors(
        self, motor_starter_element_db, valid_motor_starter_params, tmp_path
    ):
        import xml.etree.ElementTree as ET

        writer = _make_writer(motor_starter_element_db)
        tmpl = MotorStarterTemplate(writer)
        project = tmpl.generate(valid_motor_starter_params)

        filepath = tmp_path / "test_motor_starter.qet"
        writer.save(project, filepath)

        tree = ET.parse(filepath)
        root = tree.getroot()
        diagram = root.find("diagram")
        conductors = diagram.find("conductors").findall("conductor")
        assert len(conductors) == 9

    def test_xml_element_paths_are_common(
        self, motor_starter_element_db, valid_motor_starter_params, tmp_path
    ):
        import xml.etree.ElementTree as ET

        writer = _make_writer(motor_starter_element_db)
        tmpl = MotorStarterTemplate(writer)
        project = tmpl.generate(valid_motor_starter_params)

        filepath = tmp_path / "test_motor_starter.qet"
        writer.save(project, filepath)

        tree = ET.parse(filepath)
        root = tree.getroot()
        diagram = root.find("diagram")
        elements = diagram.find("elements").findall("element")
        for elem in elements:
            assert elem.attrib["type"].startswith("common://")

    def test_xml_conductor_references_are_valid_uuids(
        self, motor_starter_element_db, valid_motor_starter_params, tmp_path
    ):
        import xml.etree.ElementTree as ET

        writer = _make_writer(motor_starter_element_db)
        tmpl = MotorStarterTemplate(writer)
        project = tmpl.generate(valid_motor_starter_params)

        filepath = tmp_path / "test_motor_starter.qet"
        writer.save(project, filepath)

        tree = ET.parse(filepath)
        root = tree.getroot()
        diagram = root.find("diagram")

        element_uuids = set()
        terminal_uuids = set()
        for elem in diagram.find("elements").findall("element"):
            element_uuids.add(elem.attrib["uuid"])
            for term in elem.find("terminals").findall("terminal"):
                terminal_uuids.add(term.attrib["uuid"])

        for cond in diagram.find("conductors").findall("conductor"):
            assert cond.attrib["terminal1"] in terminal_uuids
            assert cond.attrib["terminal2"] in terminal_uuids
            assert cond.attrib["element1"] in element_uuids
            assert cond.attrib["element2"] in element_uuids


# ══════════════════════════════════════════════════════════════════════
# QET-5: Control Circuit (Steuerstromkreis)
# ══════════════════════════════════════════════════════════════════════


# ── CYCLE 9: Backward compatibility -- with_control_circuit=False ──


class TestControlCircuitBackwardCompat:
    """CYCLE 9: Default behaviour unchanged when control circuit not requested."""

    def test_default_params_produce_one_folio(
        self, motor_starter_element_db, valid_motor_starter_params
    ):
        """Without with_control_circuit, only 1 folio is created."""
        writer = _make_writer(motor_starter_element_db)
        tmpl = MotorStarterTemplate(writer)
        project = tmpl.generate(valid_motor_starter_params)
        assert len(project.folios) == 1

    def test_explicit_false_produces_one_folio(
        self, motor_starter_element_db, valid_motor_starter_params
    ):
        """with_control_circuit=False explicitly still produces 1 folio."""
        params = {**valid_motor_starter_params, "with_control_circuit": False}
        writer = _make_writer(motor_starter_element_db)
        tmpl = MotorStarterTemplate(writer)
        project = tmpl.generate(params)
        assert len(project.folios) == 1


# ── CYCLE 10: Two folios when control circuit enabled ────────────────


class TestControlCircuitFolioCreation:
    """CYCLE 10: with_control_circuit=True creates a second folio."""

    def test_two_folios_created(
        self, control_circuit_element_db, valid_control_circuit_params
    ):
        writer = _make_writer(control_circuit_element_db)
        tmpl = MotorStarterTemplate(writer)
        project = tmpl.generate(valid_control_circuit_params)
        assert len(project.folios) == 2

    def test_folio1_is_hauptstromkreis(
        self, control_circuit_element_db, valid_control_circuit_params
    ):
        writer = _make_writer(control_circuit_element_db)
        tmpl = MotorStarterTemplate(writer)
        project = tmpl.generate(valid_control_circuit_params)
        assert project.folios[0].title == "Hauptstromkreis"

    def test_folio2_is_steuerstromkreis(
        self, control_circuit_element_db, valid_control_circuit_params
    ):
        writer = _make_writer(control_circuit_element_db)
        tmpl = MotorStarterTemplate(writer)
        project = tmpl.generate(valid_control_circuit_params)
        assert project.folios[1].title == "Steuerstromkreis"

    def test_requires_contactor_coil_voltage(
        self, control_circuit_element_db
    ):
        """with_control_circuit=True requires contactor_coil_voltage."""
        params = {
            "motor_power_kw": 1.5,
            "motor_voltage": "400V_3ph",
            "motor_current_a": 3.5,
            "protection_type": "thermal_overload",
            "with_control_circuit": True,
            # Missing contactor_coil_voltage
        }
        writer = _make_writer(control_circuit_element_db)
        tmpl = MotorStarterTemplate(writer)
        with pytest.raises(ValueError, match="contactor_coil_voltage"):
            tmpl.generate(params)


# ── CYCLE 11: Control circuit element placement ──────────────────────


class TestControlCircuitPlacement:
    """CYCLE 11: 6 elements placed on folio 2 with correct designations & positions."""

    @pytest.fixture
    def project(self, control_circuit_element_db, valid_control_circuit_params):
        writer = _make_writer(control_circuit_element_db)
        tmpl = MotorStarterTemplate(writer)
        return tmpl.generate(valid_control_circuit_params)

    @pytest.fixture
    def folio2(self, project):
        return project.folios[1]

    def test_six_elements_on_folio2(self, folio2):
        assert len(folio2.elements) == 6

    def test_element_designations(self, folio2):
        designations = [e.designation for e in folio2.elements]
        assert designations == ["S0", "F2", "S1", "S2", "K1", "K1"]

    def test_element_paths(self, folio2):
        paths = [e.elmt_path for e in folio2.elements]
        assert paths[0].endswith("e_stop_1p.elmt")       # S0
        assert paths[1].endswith("con_simple_nf.elmt")    # F2 aux
        assert paths[2].endswith("poussoir_nf.elmt")      # S1
        assert paths[3].endswith("poussoir.elmt")         # S2
        assert paths[4].endswith("con_simple.elmt")       # K1 self-hold
        assert paths[5].endswith("bobine3.elmt")          # K1 coil

    def test_all_paths_start_with_common(self, folio2):
        for e in folio2.elements:
            assert e.elmt_path.startswith("common://")

    def test_s0_position(self, folio2):
        s0 = folio2.elements[0]
        assert s0.x == 300
        assert s0.y == 150

    def test_f2_aux_position(self, folio2):
        f2 = folio2.elements[1]
        assert f2.x == 300
        assert f2.y == 230

    def test_s1_position(self, folio2):
        s1 = folio2.elements[2]
        assert s1.x == 300
        assert s1.y == 310

    def test_s2_position(self, folio2):
        s2 = folio2.elements[3]
        assert s2.x == 300
        assert s2.y == 390

    def test_k1_self_hold_position(self, folio2):
        """K1 self-hold contact offset to x=380 for parallel branch."""
        k1_self = folio2.elements[4]
        assert k1_self.x == 380
        assert k1_self.y == 390

    def test_k1_coil_position(self, folio2):
        k1_coil = folio2.elements[5]
        assert k1_coil.x == 300
        assert k1_coil.y == 470

    def test_vertical_order_main_path(self, folio2):
        """Main path elements stacked vertically: S0 < F2 < S1 < S2 < K1_coil."""
        s0, f2, s1, s2 = folio2.elements[0:4]
        k1_coil = folio2.elements[5]
        assert s0.y < f2.y < s1.y < s2.y < k1_coil.y

    def test_positions_on_10px_grid(self, folio2):
        for e in folio2.elements:
            assert e.x % 10 == 0, f"{e.designation} x={e.x} not on grid"
            assert e.y % 10 == 0, f"{e.designation} y={e.y} not on grid"

    def test_s0_has_2_terminals(self, folio2):
        assert len(folio2.elements[0].terminals) == 2

    def test_f2_aux_has_2_terminals(self, folio2):
        assert len(folio2.elements[1].terminals) == 2

    def test_s1_has_2_terminals(self, folio2):
        assert len(folio2.elements[2].terminals) == 2

    def test_s2_has_2_terminals(self, folio2):
        assert len(folio2.elements[3].terminals) == 2

    def test_k1_self_has_2_terminals(self, folio2):
        assert len(folio2.elements[4].terminals) == 2

    def test_k1_coil_has_2_terminals(self, folio2):
        assert len(folio2.elements[5].terminals) == 2


# ── CYCLE 12: Control circuit conductors ─────────────────────────────


class TestControlCircuitConductors:
    """CYCLE 12: 6 conductors on folio 2 with correct terminal mapping."""

    @pytest.fixture
    def project(self, control_circuit_element_db, valid_control_circuit_params):
        writer = _make_writer(control_circuit_element_db)
        tmpl = MotorStarterTemplate(writer)
        return tmpl.generate(valid_control_circuit_params)

    @pytest.fixture
    def folio2(self, project):
        return project.folios[1]

    def test_six_conductors(self, folio2):
        assert len(folio2.conductors) == 6

    def test_conductors_reference_valid_elements(self, folio2):
        element_uuids = {e.uuid for e in folio2.elements}
        for c in folio2.conductors:
            assert c.element1_uuid in element_uuids
            assert c.element2_uuid in element_uuids

    def test_conductors_reference_valid_terminals(self, folio2):
        all_terminal_uuids = set()
        for e in folio2.elements:
            for t in e.terminals:
                all_terminal_uuids.add(t.uuid)
        for c in folio2.conductors:
            assert c.terminal1_uuid in all_terminal_uuids
            assert c.terminal2_uuid in all_terminal_uuids

    def test_no_duplicate_conductors(self, folio2):
        """No two conductors share the exact same terminal pair."""
        seen = set()
        for c in folio2.conductors:
            pair = (c.terminal1_uuid, c.terminal2_uuid)
            reverse = (c.terminal2_uuid, c.terminal1_uuid)
            assert pair not in seen and reverse not in seen, (
                f"Duplicate conductor: {pair}"
            )
            seen.add(pair)

    def test_s0_bottom_to_f2aux_top(self, folio2):
        """Conductor 1: S0 idx0 (bottom) -> F2_aux idx0 (top)."""
        s0 = folio2.elements[0]
        f2_aux = folio2.elements[1]
        cond = next(
            c for c in folio2.conductors
            if c.element1_uuid == s0.uuid and c.element2_uuid == f2_aux.uuid
        )
        # S0: idx0 = bottom (south terminal)
        assert cond.terminal1_uuid == s0.terminals[0].uuid
        # F2_aux: idx0 = top (north terminal)
        assert cond.terminal2_uuid == f2_aux.terminals[0].uuid

    def test_f2aux_bottom_to_s1_top(self, folio2):
        """Conductor 2: F2_aux idx1 (bottom) -> S1 idx0 (top)."""
        f2_aux = folio2.elements[1]
        s1 = folio2.elements[2]
        cond = next(
            c for c in folio2.conductors
            if c.element1_uuid == f2_aux.uuid and c.element2_uuid == s1.uuid
        )
        assert cond.terminal1_uuid == f2_aux.terminals[1].uuid
        assert cond.terminal2_uuid == s1.terminals[0].uuid

    def test_s1_bottom_to_s2_top(self, folio2):
        """Conductor 3: S1 idx1 (bottom) -> S2 idx0 (top)."""
        s1 = folio2.elements[2]
        s2 = folio2.elements[3]
        cond = next(
            c for c in folio2.conductors
            if c.element1_uuid == s1.uuid and c.element2_uuid == s2.uuid
        )
        assert cond.terminal1_uuid == s1.terminals[1].uuid
        assert cond.terminal2_uuid == s2.terminals[0].uuid

    def test_s1_bottom_to_k1self_top(self, folio2):
        """Conductor 4: S1 idx1 (bottom) -> K1_self idx0 (top)."""
        s1 = folio2.elements[2]
        k1_self = folio2.elements[4]
        cond = next(
            c for c in folio2.conductors
            if c.element1_uuid == s1.uuid and c.element2_uuid == k1_self.uuid
        )
        assert cond.terminal1_uuid == s1.terminals[1].uuid
        assert cond.terminal2_uuid == k1_self.terminals[0].uuid

    def test_s2_bottom_to_k1coil_a1(self, folio2):
        """Conductor 5: S2 idx1 (bottom) -> K1_coil A1 (named)."""
        s2 = folio2.elements[3]
        k1_coil = folio2.elements[5]
        cond = next(
            c for c in folio2.conductors
            if c.element1_uuid == s2.uuid and c.element2_uuid == k1_coil.uuid
        )
        assert cond.terminal1_uuid == s2.terminals[1].uuid
        # K1_coil A1 is the terminal named "A1"
        a1 = next(t for t in k1_coil.terminals if t.name == "A1")
        assert cond.terminal2_uuid == a1.uuid

    def test_k1self_bottom_to_k1coil_a1(self, folio2):
        """Conductor 6: K1_self idx1 (bottom) -> K1_coil A1 (named)."""
        k1_self = folio2.elements[4]
        k1_coil = folio2.elements[5]
        cond = next(
            c for c in folio2.conductors
            if c.element1_uuid == k1_self.uuid and c.element2_uuid == k1_coil.uuid
        )
        assert cond.terminal1_uuid == k1_self.terminals[1].uuid
        a1 = next(t for t in k1_coil.terminals if t.name == "A1")
        assert cond.terminal2_uuid == a1.uuid

    def test_s1_bottom_shared_by_two_conductors(self, folio2):
        """S1 bottom terminal is shared: connects to both S2 and K1_self."""
        s1 = folio2.elements[2]
        s1_bottom_uuid = s1.terminals[1].uuid
        conductors_from_s1_bottom = [
            c for c in folio2.conductors
            if c.terminal1_uuid == s1_bottom_uuid
        ]
        assert len(conductors_from_s1_bottom) == 2

    def test_k1coil_a1_shared_by_two_conductors(self, folio2):
        """K1_coil A1 terminal is shared: receives from both S2 and K1_self."""
        k1_coil = folio2.elements[5]
        a1 = next(t for t in k1_coil.terminals if t.name == "A1")
        conductors_to_a1 = [
            c for c in folio2.conductors
            if c.terminal2_uuid == a1.uuid
        ]
        assert len(conductors_to_a1) == 2


# ── CYCLE 13: Cross-references (link_master_slave) ──────────────────


class TestCrossReferences:
    """CYCLE 13: K1_coil linked to K1_self and K1_power via links_uuids."""

    @pytest.fixture
    def project(self, control_circuit_element_db, valid_control_circuit_params):
        writer = _make_writer(control_circuit_element_db)
        tmpl = MotorStarterTemplate(writer)
        return tmpl.generate(valid_control_circuit_params)

    def test_k1_coil_links_to_two_slaves(self, project):
        """K1 coil (master) has links_uuids pointing to K1_self and K1_power."""
        k1_coil = project.folios[1].elements[5]  # last element on folio 2
        assert len(k1_coil.links_uuids) == 2

    def test_k1_self_links_to_coil(self, project):
        """K1 self-hold (slave) has link back to coil."""
        k1_self = project.folios[1].elements[4]
        k1_coil = project.folios[1].elements[5]
        assert k1_coil.uuid in k1_self.links_uuids

    def test_k1_power_links_to_coil(self, project):
        """K1 power contact on folio 1 (slave) has link to coil on folio 2."""
        k1_power = project.folios[0].elements[1]  # K1 contactor on folio 1
        k1_coil = project.folios[1].elements[5]
        assert k1_coil.uuid in k1_power.links_uuids

    def test_k1_coil_links_contain_k1_self(self, project):
        k1_self = project.folios[1].elements[4]
        k1_coil = project.folios[1].elements[5]
        assert k1_self.uuid in k1_coil.links_uuids

    def test_k1_coil_links_contain_k1_power(self, project):
        k1_power = project.folios[0].elements[1]
        k1_coil = project.folios[1].elements[5]
        assert k1_power.uuid in k1_coil.links_uuids

    def test_bidirectional_links(self, project):
        """All links are bidirectional."""
        k1_coil = project.folios[1].elements[5]
        k1_self = project.folios[1].elements[4]
        k1_power = project.folios[0].elements[1]
        # coil <-> self
        assert k1_self.uuid in k1_coil.links_uuids
        assert k1_coil.uuid in k1_self.links_uuids
        # coil <-> power
        assert k1_power.uuid in k1_coil.links_uuids
        assert k1_coil.uuid in k1_power.links_uuids


# ── CYCLE 14: Folio 1 unchanged when control circuit added ──────────


class TestFolio1UnchangedWithControlCircuit:
    """CYCLE 14: Power circuit on folio 1 identical with or without control circuit."""

    @pytest.fixture
    def project(self, control_circuit_element_db, valid_control_circuit_params):
        writer = _make_writer(control_circuit_element_db)
        tmpl = MotorStarterTemplate(writer)
        return tmpl.generate(valid_control_circuit_params)

    @pytest.fixture
    def folio1(self, project):
        return project.folios[0]

    def test_folio1_four_elements(self, folio1):
        assert len(folio1.elements) == 4

    def test_folio1_nine_conductors(self, folio1):
        assert len(folio1.conductors) == 9

    def test_folio1_element_designations(self, folio1):
        designations = [e.designation for e in folio1.elements]
        assert designations == ["F1", "K1", "F2", "M1"]

    def test_folio1_title(self, folio1):
        assert folio1.title == "Hauptstromkreis"


# ── CYCLE 15: Full XML generation with control circuit ───────────────


class TestControlCircuitXmlGeneration:
    """CYCLE 15: save() produces valid XML with 2 diagrams."""

    def test_xml_has_two_diagrams(
        self, control_circuit_element_db, valid_control_circuit_params, tmp_path
    ):
        import xml.etree.ElementTree as ET

        writer = _make_writer(control_circuit_element_db)
        tmpl = MotorStarterTemplate(writer)
        project = tmpl.generate(valid_control_circuit_params)

        filepath = tmp_path / "test_control_circuit.qet"
        writer.save(project, filepath)

        tree = ET.parse(filepath)
        root = tree.getroot()
        diagrams = root.findall("diagram")
        assert len(diagrams) == 2

    def test_xml_diagram2_has_six_elements(
        self, control_circuit_element_db, valid_control_circuit_params, tmp_path
    ):
        import xml.etree.ElementTree as ET

        writer = _make_writer(control_circuit_element_db)
        tmpl = MotorStarterTemplate(writer)
        project = tmpl.generate(valid_control_circuit_params)

        filepath = tmp_path / "test_control_circuit.qet"
        writer.save(project, filepath)

        tree = ET.parse(filepath)
        root = tree.getroot()
        diagram2 = root.findall("diagram")[1]
        elements = diagram2.find("elements").findall("element")
        assert len(elements) == 6

    def test_xml_diagram2_has_six_conductors(
        self, control_circuit_element_db, valid_control_circuit_params, tmp_path
    ):
        import xml.etree.ElementTree as ET

        writer = _make_writer(control_circuit_element_db)
        tmpl = MotorStarterTemplate(writer)
        project = tmpl.generate(valid_control_circuit_params)

        filepath = tmp_path / "test_control_circuit.qet"
        writer.save(project, filepath)

        tree = ET.parse(filepath)
        root = tree.getroot()
        diagram2 = root.findall("diagram")[1]
        conductors = diagram2.find("conductors").findall("conductor")
        assert len(conductors) == 6

    def test_xml_links_uuids_present_on_coil(
        self, control_circuit_element_db, valid_control_circuit_params, tmp_path
    ):
        import xml.etree.ElementTree as ET

        writer = _make_writer(control_circuit_element_db)
        tmpl = MotorStarterTemplate(writer)
        project = tmpl.generate(valid_control_circuit_params)

        filepath = tmp_path / "test_control_circuit.qet"
        writer.save(project, filepath)

        tree = ET.parse(filepath)
        root = tree.getroot()
        diagram2 = root.findall("diagram")[1]
        elements = diagram2.find("elements").findall("element")

        # Last element on folio 2 is the coil
        coil_elem = elements[5]
        links = coil_elem.find("links_uuids")
        assert links is not None
        link_uuids = [lu.attrib["uuid"] for lu in links.findall("link_uuid")]
        assert len(link_uuids) == 2

    def test_xml_conductor_references_valid_on_diagram2(
        self, control_circuit_element_db, valid_control_circuit_params, tmp_path
    ):
        import xml.etree.ElementTree as ET

        writer = _make_writer(control_circuit_element_db)
        tmpl = MotorStarterTemplate(writer)
        project = tmpl.generate(valid_control_circuit_params)

        filepath = tmp_path / "test_control_circuit.qet"
        writer.save(project, filepath)

        tree = ET.parse(filepath)
        root = tree.getroot()
        diagram2 = root.findall("diagram")[1]

        element_uuids = set()
        terminal_uuids = set()
        for elem in diagram2.find("elements").findall("element"):
            element_uuids.add(elem.attrib["uuid"])
            for term in elem.find("terminals").findall("terminal"):
                terminal_uuids.add(term.attrib["uuid"])

        for cond in diagram2.find("conductors").findall("conductor"):
            assert cond.attrib["terminal1"] in terminal_uuids
            assert cond.attrib["terminal2"] in terminal_uuids
            assert cond.attrib["element1"] in element_uuids
            assert cond.attrib["element2"] in element_uuids
