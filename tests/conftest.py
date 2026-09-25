import json

import pytest
from fastapi.testclient import TestClient

import api


SAMPLE_BOOKS = [
    {"id": 1, "title": "Atomic Habits", "author": "James Clear", "status": "reading"},
    {"id": 2, "title": "The Pragmatic Programmer", "author": "Andrew Hunt", "status": "to-read"},
]


@pytest.fixture(autouse=True)
def isolated_data_file(tmp_path, monkeypatch):
    data_file = tmp_path / "data.json"
    data_file.write_text(json.dumps(SAMPLE_BOOKS))
    monkeypatch.setattr(api, "DATA_FILE", data_file)
    return data_file


@pytest.fixture
def sample_books():
    return [dict(book) for book in SAMPLE_BOOKS]


@pytest.fixture
def client():
    return TestClient(api.app)


def read_data_file(data_file):
    return json.loads(data_file.read_text())


def write_data_file(data_file, books):
    data_file.write_text(json.dumps(books))
