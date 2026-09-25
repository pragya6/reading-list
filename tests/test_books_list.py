import pytest

from conftest import write_data_file


def test_books_list_returns_all_books(client, sample_books):
    resp = client.get("/books-list")

    assert resp.status_code == 200
    assert resp.json() == sample_books


def test_books_list_returns_empty_when_no_data(client, isolated_data_file):
    write_data_file(isolated_data_file, [])

    resp = client.get("/books-list")

    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.parametrize("status", ["to-read", "reading", "done"])
def test_books_list_filter_by_status_returns_exact_matches(client, isolated_data_file, status):
    books = [
        {"id": 1, "title": "A", "author": None, "status": "to-read"},
        {"id": 2, "title": "B", "author": None, "status": "reading"},
        {"id": 3, "title": "C", "author": None, "status": "done"},
    ]
    write_data_file(isolated_data_file, books)

    resp = client.get("/books-list", params={"status": status})

    assert resp.status_code == 200
    body = resp.json()
    assert all(b["status"] == status for b in body)
    assert len(body) == 1


def test_books_list_rejects_invalid_status_filter(client):
    resp = client.get("/books-list", params={"status": "bogus"})

    assert resp.status_code == 422
