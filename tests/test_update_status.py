import pytest

from conftest import read_data_file


def test_update_status_updates_and_persists(client, isolated_data_file, sample_books):
    target = sample_books[0]
    new_status = "done" if target["status"] != "done" else "reading"

    resp = client.patch(f"/update-status/{target['id']}", json={"status": new_status})

    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == target["id"]
    assert body["status"] == new_status

    stored = read_data_file(isolated_data_file)
    updated = next(b for b in stored if b["id"] == target["id"])
    assert updated["status"] == new_status


def test_update_status_unknown_book_returns_404(client):
    resp = client.patch("/update-status/9999", json={"status": "done"})

    assert resp.status_code == 404


def test_update_status_requires_status(client, sample_books):
    resp = client.patch(f"/update-status/{sample_books[0]['id']}", json={})

    assert resp.status_code == 422


def test_update_status_rejects_invalid_status_value(client, sample_books):
    resp = client.patch(f"/update-status/{sample_books[0]['id']}", json={"status": "archived"})

    assert resp.status_code == 422


@pytest.mark.parametrize("book_id", [0, -1])
def test_update_status_rejects_non_positive_book_id(client, book_id):
    resp = client.patch(f"/update-status/{book_id}", json={"status": "done"})

    assert resp.status_code == 422
