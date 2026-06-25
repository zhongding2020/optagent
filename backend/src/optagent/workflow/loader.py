from pathlib import Path
from typing import Any

import yaml

from .types import WorkflowDefinition


class WorkflowLoader:
    """Loads and lists workflow definitions from a YAML directory."""

    def __init__(self, directory: str = "./workflows"):
        self.directory = Path(directory)

    def list(self) -> list[str]:
        if not self.directory.exists():
            return []
        return sorted([f.stem for f in self.directory.glob("*.yaml")])

    def load(self, name: str) -> WorkflowDefinition:
        path = self.directory / f"{name}.yaml"
        if not path.exists():
            raise FileNotFoundError(f"Workflow '{name}' not found at {path}")
        with open(path) as f:
            data = yaml.safe_load(f)
        return WorkflowDefinition(**data)
