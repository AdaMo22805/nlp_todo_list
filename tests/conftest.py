import pytest


@pytest.fixture
def todo_file(tmp_path, monkeypatch):
    path = tmp_path / "todo.json"
    monkeypatch.setattr("final_project.storage.STORAGE_PATH", path)
    return path
