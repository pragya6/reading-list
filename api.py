import json
from enum import Enum
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi import Path as PathParam
from pydantic import BaseModel, Field, field_validator

DATA_FILE = Path(__file__).parent / "data" / "data.json"


class Status(str, Enum):
    to_read = "to-read"
    reading = "reading"
    done = "done"


class Book(BaseModel):
    id: int
    title: str
    author: str | None = None
    status: Status


class AddBookRequest(BaseModel):
    title: str = Field(..., min_length=1)
    author: str | None = None
    status: Status

    @field_validator("title")
    @classmethod
    def title_not_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("title must not be blank")
        return v

    @field_validator("author")
    @classmethod
    def strip_author(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip()
        return v or None


class UpdateStatusRequest(BaseModel):
    status: Status


class StatusCounts(BaseModel):
    to_read: int = Field(..., alias="to-read")
    reading: int
    done: int

    model_config = {"populate_by_name": True}


def load_books() -> list[dict]:
    if not DATA_FILE.exists():
        return []
    try:
        data = json.loads(DATA_FILE.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=500, detail="Could not read book data") from exc
    if not isinstance(data, list):
        raise HTTPException(status_code=500, detail="Book data is malformed")
    return data


def save_books(books: list[dict]) -> None:
    try:
        DATA_FILE.write_text(json.dumps(books, indent=2))
    except OSError as exc:
        raise HTTPException(status_code=500, detail="Could not save book data") from exc


app = FastAPI(title="Reading List API")


@app.post("/add-book", response_model=Book)
def add_book(payload: AddBookRequest):
    books = load_books()
    new_id = max((b["id"] for b in books), default=0) + 1
    book = {
        "id": new_id,
        "title": payload.title,
        "author": payload.author,
        "status": payload.status.value,
    }
    books.append(book)
    save_books(books)
    return book


@app.get("/books-list", response_model=list[Book])
def books_list(status: Status | None = None):
    books = load_books()
    if status is not None:
        books = [b for b in books if b["status"] == status.value]
    return books


@app.patch("/update-status/{book_id}", response_model=Book)
def update_status(
    payload: UpdateStatusRequest,
    book_id: int = PathParam(..., gt=0),
):
    books = load_books()
    for book in books:
        if book["id"] == book_id:
            book["status"] = payload.status.value
            save_books(books)
            return book
    raise HTTPException(status_code=404, detail="Book not found")


@app.get("/count-by-status", response_model=StatusCounts)
def count_by_status():
    books = load_books()
    counts = {status.value: 0 for status in Status}
    for book in books:
        counts[book["status"]] = counts.get(book["status"], 0) + 1
    return counts
