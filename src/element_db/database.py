"""Searchable database of parsed QET elements."""

from __future__ import annotations

import logging
import os
from pathlib import Path

from .models import ElementRecord
from .parser import parse_elmt_file

logger = logging.getLogger(__name__)


class ElementDB:
    """In-memory database of parsed .elmt element files.

    Elements are keyed by their relative path (forward slashes) from the
    collection root.
    """

    def __init__(self) -> None:
        self._records: dict[str, ElementRecord] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def scan(self, elements_dir: str | Path) -> None:
        """Scan a directory tree for .elmt files and parse them all.

        Args:
            elements_dir: Root directory of the QET element collection.

        Raises:
            FileNotFoundError: If *elements_dir* does not exist.
        """
        elements_dir = Path(elements_dir)
        if not elements_dir.is_dir():
            raise FileNotFoundError(
                f"Elements directory not found: {elements_dir}"
            )

        self._records.clear()

        for dirpath, _dirnames, filenames in os.walk(elements_dir):
            for fname in filenames:
                if not fname.endswith(".elmt"):
                    continue
                full_path = Path(dirpath) / fname
                # Build the relative path with forward slashes.
                try:
                    rel = full_path.relative_to(elements_dir)
                except ValueError:
                    continue
                rel_path = rel.as_posix()

                try:
                    record = parse_elmt_file(full_path, relative_path=rel_path)
                    self._records[rel_path] = record
                except Exception:
                    logger.debug("Failed to parse %s", full_path, exc_info=True)

    def get(self, elmt_path: str) -> ElementRecord:
        """Return the ElementRecord for the given relative path.

        Args:
            elmt_path: Relative path (forward slashes) from collection root.

        Returns:
            The matching ElementRecord.

        Raises:
            KeyError: If the path is not in the database.
        """
        return self._records[elmt_path]

    def search(self, query: str) -> list[ElementRecord]:
        """Case-insensitive search across all element name languages.

        Args:
            query: Search string.

        Returns:
            List of matching ElementRecords.
        """
        q = query.lower()
        results: list[ElementRecord] = []
        for rec in self._records.values():
            for name in rec.names.values():
                if q in name.lower():
                    results.append(rec)
                    break
        return results

    def get_by_link_type(self, link_type: str) -> list[ElementRecord]:
        """Return all elements with the given link_type.

        Args:
            link_type: One of "master", "slave", "simple", "terminal", etc.

        Returns:
            List of matching ElementRecords.
        """
        return [
            rec
            for rec in self._records.values()
            if rec.link_type == link_type
        ]

    def count(self) -> int:
        """Return the number of elements in the database."""
        return len(self._records)
