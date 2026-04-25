"""Abstract base class for all circuit templates."""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.writer.models import QETProject


class BaseTemplate(ABC):
    """Abstract base for circuit templates.

    Every template takes parameters and produces a QETProject.
    """

    @abstractmethod
    def generate(self, params: dict) -> QETProject:
        """Generate a QET project from the given parameters."""
