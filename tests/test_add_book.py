import pytest

from conftest import read_data_file, write_data_file


def test_add_book_increases_count_and_persists(client, isolated_data_file, sample_books):
    resp = client.post(
        "/add-book",
        json={"title": "Deep Work", "author": "Cal Newport", "status": "to-read"},
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["title"] == "Deep Work"
    assert body["author"] == "Cal Newport"
    assert body["status"] == "to-read"
    assert body["id"] == max(b["id"] for b in sample_books) + 1

    stored = read_data_file(isolated_data_file)
    assert len(stored) == len(sample_books) + 1
    assert stored[-1] == body


def test_add_book_author_is_optional(client):
    resp = client.post("/add-book", json={"title": "No Author Book", "status": "reading"})

    assert resp.status_code == 200
    assert resp.json()["author"] is None


def test_add_book_requires_title(client):
    resp = client.post("/add-book", json={"status": "to-read"})

    assert resp.status_code == 422


def test_add_book_rejects_blank_title(client):
    resp = client.post("/add-book", json={"title": "   ", "status": "to-read"})

    assert resp.status_code == 422


def test_add_book_requires_status(client):
    resp = client.post("/add-book", json={"title": "Some Book"})

    assert resp.status_code == 422


def test_add_book_rejects_invalid_status(client):
    resp = client.post("/add-book", json={"title": "Some Book", "status": "archived"})

    assert resp.status_code == 422


@pytest.mark.parametrize("status", ["to-read", "reading", "done"])
def test_add_book_accepts_each_allowed_status(client, status):
    resp = client.post("/add-book", json={"title": f"Book {status}", "status": status})

    assert resp.status_code == 200
    assert resp.json()["status"] == status


def test_add_book_id_starts_at_one_when_data_empty(client, isolated_data_file):
    write_data_file(isolated_data_file, [])

    resp = client.post("/add-book", json={"title": "First Book", "status": "to-read"})

    assert resp.status_code == 200
    assert resp.json()["id"] == 1
