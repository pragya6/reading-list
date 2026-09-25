from conftest import write_data_file


def test_count_by_status_returns_correct_counts(client, isolated_data_file):
    books = [
        {"id": 1, "title": "A", "author": None, "status": "to-read"},
        {"id": 2, "title": "B", "author": None, "status": "to-read"},
        {"id": 3, "title": "C", "author": None, "status": "reading"},
        {"id": 4, "title": "D", "author": None, "status": "done"},
    ]
    write_data_file(isolated_data_file, books)

    resp = client.get("/count-by-status")

    assert resp.status_code == 200
    assert resp.json() == {"to-read": 2, "reading": 1, "done": 1}


def test_count_by_status_all_zero_when_no_data(client, isolated_data_file):
    write_data_file(isolated_data_file, [])

    resp = client.get("/count-by-status")

    assert resp.status_code == 200
    assert resp.json() == {"to-read": 0, "reading": 0, "done": 0}


def test_count_by_status_updates_after_add_book(client):
    before = client.get("/count-by-status").json()

    client.post("/add-book", json={"title": "New Book", "status": "reading"})

    after = client.get("/count-by-status").json()
    assert after["reading"] == before["reading"] + 1
    assert after["to-read"] == before["to-read"]
    assert after["done"] == before["done"]
