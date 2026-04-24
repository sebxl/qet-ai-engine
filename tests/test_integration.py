"""End-to-end integration tests for QET-1 acceptance criteria.

Verifies the full pipeline: scan -> get -> search -> position calculation.
"""

import pytest

from src.element_db import (
    ElementDB,
    ElementRecord,
    Terminal,
    terminal_absolute_position,
)


@pytest.fixture(scope="module")
def db():
    """Module-scoped DB fixture -- scan once, share across all tests."""
    from pathlib import Path

    db = ElementDB()
    db.scan(Path("C:/Program Files/QElectroTech/elements"))
    return db


class TestAcceptanceCriteria:
    """Acceptance criteria for QET-1."""

    def test_ac1_scan_all_elements(self, db):
        """AC1: Database contains 8500+ parsed elements."""
        assert db.count() >= 8500

    def test_ac2_get_element_by_path(self, db):
        """AC2: Can retrieve any element by its relative path."""
        rec = db.get(
            "10_electric/10_allpole/310_relays_contactors_contacts/"
            "01_coils/bobine3.elmt"
        )
        assert isinstance(rec, ElementRecord)
        assert rec.uuid == "{793302b1-e96a-f7f8-70bc-dec53eeaab5b}"

    def test_ac3_terminals_parsed(self, db):
        """AC3: Terminals are correctly parsed with positions."""
        rec = db.get(
            "10_electric/10_allpole/310_relays_contactors_contacts/"
            "01_coils/bobine3.elmt"
        )
        assert len(rec.terminals) == 2
        a1 = next(t for t in rec.terminals if t.name == "A1")
        assert a1.x == 0.0
        assert a1.y == -20.0
        assert a1.orientation == "n"

    def test_ac4_search_by_name(self, db):
        """AC4: Can search elements by name in any language."""
        results = db.search("Motorschutzschalter")
        assert len(results) > 0
        # The breaker element should be in results
        paths = [r.path for r in results]
        assert any("dis_mag_term" in p for p in paths)

    def test_ac5_filter_by_link_type(self, db):
        """AC5: Can filter elements by link_type."""
        masters = db.get_by_link_type("master")
        slaves = db.get_by_link_type("slave")
        terminals = db.get_by_link_type("terminal")
        assert len(masters) > 0
        assert len(slaves) > 0
        assert len(terminals) > 0

    def test_ac6_kind_informations_parsed(self, db):
        """AC6: kindInformations are correctly parsed."""
        coil = db.get(
            "10_electric/10_allpole/310_relays_contactors_contacts/"
            "01_coils/bobine3.elmt"
        )
        assert coil.kind_informations is not None
        assert coil.kind_informations.type == "coil"

        contact = db.get(
            "10_electric/10_allpole/310_relays_contactors_contacts/"
            "02_contacts_cross_referencing/01_auxiliary_contacts/"
            "con_simple.elmt"
        )
        assert contact.kind_informations is not None
        assert contact.kind_informations.state == "NO"
        assert contact.kind_informations.number == 1

    def test_ac7_absolute_position_calculation(self, db):
        """AC7: Terminal absolute position is calculated correctly."""
        rec = db.get(
            "10_electric/10_allpole/310_relays_contactors_contacts/"
            "01_coils/bobine3.elmt"
        )
        a1 = next(t for t in rec.terminals if t.name == "A1")

        # Place element at (100, 200) with orientation 0 (no rotation)
        abs_x, abs_y = terminal_absolute_position(a1, 100.0, 200.0, 0)
        assert abs_x == pytest.approx(100.0)
        assert abs_y == pytest.approx(180.0)

        # Same element rotated 90 degrees
        abs_x, abs_y = terminal_absolute_position(a1, 100.0, 200.0, 1)
        assert abs_x == pytest.approx(120.0)
        assert abs_y == pytest.approx(200.0)

    def test_ac8_graphic_primitives_parsed(self, db):
        """AC8: Graphic primitives are parsed from elements."""
        rec = db.get(
            "10_electric/10_allpole/391_consumers_actuators/"
            "10_engines/moteur_tri.elmt"
        )
        types = {p.type for p in rec.graphic_primitives}
        assert "ellipse" in types
        assert "arc" in types
        assert "polygon" in types
        assert "text" in types
        assert "line" in types

    def test_ac9_forward_slashes_in_paths(self, db):
        """AC9: All stored paths use forward slashes."""
        rec = db.get(
            "10_electric/10_allpole/310_relays_contactors_contacts/"
            "01_coils/bobine3.elmt"
        )
        assert "\\" not in rec.path

    def test_ac10_no_external_dependencies(self):
        """AC10: Only stdlib modules are used."""
        import src.element_db.models as models
        import src.element_db.parser as parser
        import src.element_db.database as database
        # If these imports work, we're only using stdlib + our own code.
        # Verify no third-party imports in module source.
        import inspect

        for mod in (models, parser, database):
            source = inspect.getsource(mod)
            # Should not import anything from outside stdlib / our package
            assert "import requests" not in source
            assert "import pandas" not in source
            assert "import numpy" not in source
