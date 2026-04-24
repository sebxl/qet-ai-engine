"""Tests for the ElementDB database."""

import tempfile
from pathlib import Path

import pytest

from src.element_db.database import ElementDB


class TestElementDBScan:
    """Tests for ElementDB.scan()."""

    def test_scan_populates_db(self, elements_dir):
        db = ElementDB()
        db.scan(elements_dir)
        assert db.count() > 0

    def test_scan_finds_many_elements(self, elements_dir):
        db = ElementDB()
        db.scan(elements_dir)
        assert db.count() >= 8500

    def test_scan_completes_in_time(self, elements_dir):
        """Scan should complete in under 10 seconds."""
        import time

        db = ElementDB()
        start = time.perf_counter()
        db.scan(elements_dir)
        elapsed = time.perf_counter() - start
        assert elapsed < 10.0, f"Scan took {elapsed:.1f}s, expected < 10s"

    def test_scan_bad_dir_raises(self):
        db = ElementDB()
        with pytest.raises(FileNotFoundError):
            db.scan(Path("/nonexistent/path/that/does/not/exist"))

    def test_scan_empty_dir(self, tmp_path):
        db = ElementDB()
        db.scan(tmp_path)
        assert db.count() == 0


class TestElementDBGet:
    """Tests for ElementDB.get()."""

    @pytest.fixture(autouse=True)
    def setup_db(self, elements_dir):
        self.db = ElementDB()
        self.db.scan(elements_dir)

    def test_get_by_relative_path(self, coil_elmt_path):
        rec = self.db.get(coil_elmt_path)
        assert rec.uuid == "{793302b1-e96a-f7f8-70bc-dec53eeaab5b}"
        assert rec.names["de"] == "Spule"

    def test_get_motor(self, motor_tri_elmt_path):
        rec = self.db.get(motor_tri_elmt_path)
        assert len(rec.terminals) == 4

    def test_get_unknown_raises_keyerror(self):
        with pytest.raises(KeyError):
            self.db.get("nonexistent/path.elmt")


class TestElementDBSearch:
    """Tests for ElementDB.search()."""

    @pytest.fixture(autouse=True)
    def setup_db(self, elements_dir):
        self.db = ElementDB()
        self.db.scan(elements_dir)

    def test_search_by_german_name(self):
        results = self.db.search("Spule")
        assert len(results) > 0
        # At least one result should be the bobine3 coil
        paths = [r.path for r in results]
        assert any("bobine3" in p for p in paths)

    def test_search_case_insensitive(self):
        results_lower = self.db.search("spule")
        results_upper = self.db.search("SPULE")
        assert len(results_lower) == len(results_upper)
        assert len(results_lower) > 0

    def test_search_english_name(self):
        results = self.db.search("Coil")
        assert len(results) > 0

    def test_search_no_results(self):
        results = self.db.search("xyznonexistentname123")
        assert len(results) == 0


class TestElementDBGetByLinkType:
    """Tests for ElementDB.get_by_link_type()."""

    @pytest.fixture(autouse=True)
    def setup_db(self, elements_dir):
        self.db = ElementDB()
        self.db.scan(elements_dir)

    def test_get_masters(self):
        masters = self.db.get_by_link_type("master")
        assert len(masters) > 0
        assert all(r.link_type == "master" for r in masters)

    def test_get_slaves(self):
        slaves = self.db.get_by_link_type("slave")
        assert len(slaves) > 0
        assert all(r.link_type == "slave" for r in slaves)

    def test_get_terminals(self):
        terminals = self.db.get_by_link_type("terminal")
        assert len(terminals) > 0
        assert all(r.link_type == "terminal" for r in terminals)

    def test_get_simple(self):
        simple = self.db.get_by_link_type("simple")
        assert len(simple) > 0


class TestElementDBCount:
    """Tests for ElementDB.count()."""

    def test_count_empty(self):
        db = ElementDB()
        assert db.count() == 0

    def test_count_after_scan(self, elements_dir):
        db = ElementDB()
        db.scan(elements_dir)
        assert db.count() >= 8500
