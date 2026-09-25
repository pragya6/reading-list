import threading
import time

import httpx
import gradio as gr
import uvicorn

from api import app as api_app

BASE_URL = "http://127.0.0.1:8000"

STATUS_OPTIONS = ["To-read", "Reading", "Done"]
FILTER_OPTIONS = ["All"] + STATUS_OPTIONS

STATUS_TO_API = {"To-read": "to-read", "Reading": "reading", "Done": "done"}
API_TO_STATUS = {v: k for k, v in STATUS_TO_API.items()}


def fetch_books(filter_status: str) -> list[dict]:
    params = {}
    if filter_status != "All":
        params["status"] = STATUS_TO_API[filter_status]
    resp = httpx.get(f"{BASE_URL}/books-list", params=params)
    resp.raise_for_status()
    return resp.json()


def fetch_counts() -> dict:
    resp = httpx.get(f"{BASE_URL}/count-by-status")
    resp.raise_for_status()
    return resp.json()


def format_counts(counts: dict) -> str:
    return (
        f"To-read: {counts.get('to-read', 0)} | "
        f"Reading: {counts.get('reading', 0)} | "
        f"Done: {counts.get('done', 0)}"
    )


def add_book_request(title: str, author: str, status: str) -> None:
    payload = {"title": title, "author": author or None, "status": STATUS_TO_API[status]}
    resp = httpx.post(f"{BASE_URL}/add-book", json=payload)
    resp.raise_for_status()


def update_status_request(book_id: int, status: str) -> None:
    resp = httpx.patch(f"{BASE_URL}/update-status/{book_id}", json={"status": STATUS_TO_API[status]})
    resp.raise_for_status()


def make_status_change_handler(book_id: int):
    def handler(new_status: str, trigger: int):
        update_status_request(book_id, new_status)
        return trigger + 1

    return handler


def refresh_footer(trigger: int) -> str:
    return format_counts(fetch_counts())


def open_add_popup():
    return gr.update(visible=True)


def cancel_add_popup():
    return gr.update(visible=False), "", "", "To-read"


def submit_add_book(title: str, author: str, status: str, trigger: int):
    if not title:
        raise gr.Error("Title is required")
    add_book_request(title, author, status)
    return gr.update(visible=False), "", "", "To-read", trigger + 1


with gr.Blocks(title="Reading List") as demo:
    gr.Markdown("<h1 style='text-align: center'>📚 Reading List</h1>")

    refresh_trigger = gr.State(0)

    with gr.Row():
        filter_dropdown = gr.Dropdown(choices=FILTER_OPTIONS, value="All", label="Filter by status")
        add_button = gr.Button("+ Add Book")

    with gr.Group(visible=False) as add_group:
        title_input = gr.Textbox(label="Title *")
        author_input = gr.Textbox(label="Author")
        status_input = gr.Dropdown(choices=STATUS_OPTIONS, value="To-read", label="Status *")
        with gr.Row():
            submit_button = gr.Button("Add", variant="primary")
            cancel_button = gr.Button("Cancel")

    @gr.render(inputs=[filter_dropdown, refresh_trigger])
    def render_books(filter_status, _trigger):
        books = fetch_books(filter_status)
        if not books:
            gr.Markdown("_No books found._")
        for book in books:
            with gr.Row():
                gr.Markdown(f"**{book['title']}**  \n{book.get('author') or '—'}")
                status_dd = gr.Dropdown(
                    choices=STATUS_OPTIONS,
                    value=API_TO_STATUS[book["status"]],
                    show_label=False,
                    container=False,
                    interactive=True,
                )
                status_dd.change(
                    make_status_change_handler(book["id"]),
                    inputs=[status_dd, refresh_trigger],
                    outputs=[refresh_trigger],
                )

    footer = gr.Markdown()

    add_button.click(open_add_popup, outputs=[add_group])
    cancel_button.click(
        cancel_add_popup,
        outputs=[add_group, title_input, author_input, status_input],
    )
    submit_button.click(
        submit_add_book,
        inputs=[title_input, author_input, status_input, refresh_trigger],
        outputs=[add_group, title_input, author_input, status_input, refresh_trigger],
    )

    refresh_trigger.change(refresh_footer, inputs=[refresh_trigger], outputs=[footer])
    demo.load(refresh_footer, inputs=[refresh_trigger], outputs=[footer])


def run_api() -> None:
    uvicorn.run(api_app, host="127.0.0.1", port=8000, log_level="warning")


def wait_for_api(timeout: float = 20.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            httpx.get(f"{BASE_URL}/count-by-status", timeout=1.0)
            return
        except httpx.HTTPError:
            time.sleep(0.2)
    raise RuntimeError("FastAPI backend did not start within the timeout")


if __name__ == "__main__":
    api_thread = threading.Thread(target=run_api, daemon=True)
    api_thread.start()
    wait_for_api()
    demo.launch()
