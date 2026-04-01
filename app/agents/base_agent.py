"""Base agent protocol - all agents implement this interface."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date
from typing import Any, Generic, TypeVar

from app.utils.logger import get_logger

InputT = TypeVar("InputT")
OutputT = TypeVar("OutputT")


@dataclass
class AgentInput:
    """Common fields all agent inputs share."""
    roster_type: str                     # "medical" | "it"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentOutput:
    """Common fields all agent outputs share."""
    success: bool = True
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseAgent(ABC, Generic[InputT, OutputT]):
    """Abstract base class for all scheduling agents."""

    def __init__(self, name: str):
        self.name = name
        self.logger = get_logger(f"agents.{name}")

    def run(self, input_data: InputT) -> OutputT:
        """Public entry point: validate → process → return output."""
        self.logger.debug("[%s] Starting with roster_type=%s", self.name, getattr(input_data, "roster_type", "?"))
        self._validate(input_data)
        result = self._process(input_data)
        self.logger.debug("[%s] Completed. success=%s", self.name, getattr(result, "success", "?"))
        return result

    @abstractmethod
    def _validate(self, input_data: InputT) -> None:
        """Raise ValueError on invalid input."""

    @abstractmethod
    def _process(self, input_data: InputT) -> OutputT:
        """Core agent logic. Must return OutputT."""
