"""Tests that all public symbols are importable from src.element_db."""

import pytest


def test_import_terminal():
    from src.element_db import Terminal

    assert Terminal is not None


def test_import_graphic_primitive():
    from src.element_db import GraphicPrimitive

    assert GraphicPrimitive is not None


def test_import_kind_informations():
    from src.element_db import KindInformations

    assert KindInformations is not None


def test_import_element_record():
    from src.element_db import ElementRecord

    assert ElementRecord is not None


def test_import_terminal_absolute_position():
    from src.element_db import terminal_absolute_position

    assert callable(terminal_absolute_position)


def test_import_parse_elmt_file():
    from src.element_db import parse_elmt_file

    assert callable(parse_elmt_file)


def test_import_element_db():
    from src.element_db import ElementDB

    assert ElementDB is not None


def test_all_exports():
    import src.element_db as pkg

    expected = {
        "Terminal",
        "GraphicPrimitive",
        "KindInformations",
        "ElementRecord",
        "terminal_absolute_position",
        "parse_elmt_file",
        "ElementDB",
    }
    assert expected.issubset(set(pkg.__all__))
