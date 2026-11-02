import shutil
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[1]


@pytest.fixture
def repo_copy(tmp_path):
    """A writable copy of the project inputs, so tests can corrupt them."""
    for rel in ("requirements", "configs", "data"):
        shutil.copytree(REPO / rel, tmp_path / rel)
    return tmp_path


def edit_yaml(path: Path, mutate):
    data = yaml.safe_load(path.read_text())
    mutate(data)
    path.write_text(yaml.safe_dump(data, sort_keys=False))
