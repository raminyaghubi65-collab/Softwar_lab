from __future__ import annotations

import hmac
import json
import os
import re
import sqlite3
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated, Iterator

from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

DATA_DIR = Path(os.environ.get("DATA_DIR", "/data")).resolve()
UPLOAD_DIR = DATA_DIR / "uploads"
DB_PATH = DATA_DIR / "intake.sqlite3"
ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "")
MAX_FILE_BYTES = int(os.environ.get("MAX_FILE_BYTES", str(20 * 1024 * 1024)))
ALLOWED_ORIGINS = [
    item.strip()
    for item in os.environ.get(
        "ALLOWED_ORIGINS",
        "https://raminyaghubi65-collab.github.io",
    ).split(",")
    if item.strip()
]
ALLOWED_EXTENSIONS = {".apk", ".aab", ".zip", ".pdf", ".png", ".jpg", ".jpeg", ".txt", ".json", ".csv"}
RATE_LIMIT = 5
RATE_WINDOW_SECONDS = 3600
_upload_attempts: dict[str, list[float]] = {}

app = FastAPI(title="Software QA Lab private intake", docs_url=None, redoc_url=None)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)


@contextmanager
def database() -> Iterator[sqlite3.Connection]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    try:
        connection.execute(
            """CREATE TABLE IF NOT EXISTS submissions (
                id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                customer_name TEXT NOT NULL,
                email TEXT NOT NULL,
                project_type TEXT NOT NULL,
                description TEXT NOT NULL,
                original_filename TEXT NOT NULL,
                stored_filename TEXT NOT NULL,
                file_size INTEGER NOT NULL
            )"""
        )
        connection.commit()
        yield connection
        connection.commit()
    finally:
        connection.close()


def validate_upload(filename: str, content: bytes) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(415, "File type is not allowed.")
    if not content:
        raise HTTPException(400, "The uploaded file is empty.")
    if len(content) > MAX_FILE_BYTES:
        raise HTTPException(413, "The file exceeds the upload size limit.")
    if suffix in {".apk", ".aab", ".zip"}:
        if not (content.startswith(b"PK\x03\x04") or content.startswith(b"PK\x05\x06") or content.startswith(b"PK\x07\x08")):
            raise HTTPException(415, "The file does not have a valid ZIP/Android package signature.")
    elif suffix == ".pdf" and not content.startswith(b"%PDF-"):
        raise HTTPException(415, "The file does not have a valid PDF signature.")
    elif suffix == ".png" and not content.startswith(b"\x89PNG\r\n\x1a\n"):
        raise HTTPException(415, "The file does not have a valid PNG signature.")
    elif suffix in {".jpg", ".jpeg"} and not content.startswith(b"\xff\xd8\xff"):
        raise HTTPException(415, "The file does not have a valid JPEG signature.")
    elif suffix in {".txt", ".json", ".csv"}:
        if b"\x00" in content:
            raise HTTPException(415, "Text files must not contain binary data.")
        try:
            decoded = content.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise HTTPException(415, "Text files must use UTF-8 encoding.") from exc
        if suffix == ".json":
            try:
                json.loads(decoded)
            except json.JSONDecodeError as exc:
                raise HTTPException(415, "The JSON file is invalid.") from exc
    return suffix


def clean_filename(filename: str) -> str:
    leaf = Path(filename.replace("\\", "/")).name
    leaf = re.sub(r"[^A-Za-z0-9._ -]", "_", leaf).strip(" .")
    return leaf[:120] or "upload"


def enforce_rate_limit(client_ip: str) -> None:
    now = time.monotonic()
    attempts = [stamp for stamp in _upload_attempts.get(client_ip, []) if now - stamp < RATE_WINDOW_SECONDS]
    if len(attempts) >= RATE_LIMIT:
        raise HTTPException(429, "Upload limit reached. Please try again later.")
    attempts.append(now)
    _upload_attempts[client_ip] = attempts


def require_admin(authorization: str | None = Header(default=None)) -> None:
    if not ADMIN_TOKEN:
        raise HTTPException(503, "Private admin access is not configured.")
    supplied = authorization.removeprefix("Bearer ").strip() if authorization else ""
    if not hmac.compare_digest(supplied, ADMIN_TOKEN):
        raise HTTPException(401, "Unauthorized.")


class SubmissionSummary(BaseModel):
    id: str
    created_at: str
    customer_name: str
    email: str
    project_type: str
    description: str
    original_filename: str
    file_size: int


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/intake", status_code=201)
async def create_submission(
    request: Request,
    customer_name: Annotated[str, Form(min_length=2, max_length=80)],
    email: Annotated[str, Form(min_length=5, max_length=254)],
    project_type: Annotated[str, Form(pattern="^(website|android|api|python|other)$")],
    description: Annotated[str, Form(min_length=10, max_length=3000)],
    permission_confirmed: Annotated[bool, Form()],
    uploaded_file: Annotated[UploadFile, File()],
) -> dict[str, str]:
    client_ip = request.client.host if request.client else "unknown"
    enforce_rate_limit(client_ip)
    if not permission_confirmed:
        raise HTTPException(400, "You must confirm that you are authorized to share this file.")
    if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
        raise HTTPException(422, "Enter a valid email address.")
    original_filename = clean_filename(uploaded_file.filename or "upload")
    content = await uploaded_file.read(MAX_FILE_BYTES + 1)
    await uploaded_file.close()
    suffix = validate_upload(original_filename, content)
    submission_id = str(uuid.uuid4())
    stored_filename = f"{submission_id}{suffix}"
    destination = UPLOAD_DIR / stored_filename
    try:
        with destination.open("xb") as output:
            output.write(content)
        created_at = datetime.now(timezone.utc).isoformat()
        with database() as connection:
            connection.execute(
                """INSERT INTO submissions
                (id, created_at, customer_name, email, project_type, description,
                 original_filename, stored_filename, file_size)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    submission_id, created_at, customer_name.strip(), email.strip(),
                    project_type, description.strip(), original_filename, stored_filename, len(content),
                ),
            )
    except Exception:
        destination.unlink(missing_ok=True)
        raise
    return {"id": submission_id, "status": "received", "message": "Your project file was received privately."}


@app.get("/api/admin/submissions", response_model=list[SubmissionSummary], dependencies=[Depends(require_admin)])
def list_submissions() -> list[dict[str, object]]:
    with database() as connection:
        rows = connection.execute(
            """SELECT id, created_at, customer_name, email, project_type, description,
                      original_filename, file_size
               FROM submissions ORDER BY created_at DESC LIMIT 200"""
        ).fetchall()
    return [dict(row) for row in rows]


@app.get("/api/admin/submissions/{submission_id}/file", dependencies=[Depends(require_admin)])
def download_submission(submission_id: str) -> FileResponse:
    try:
        parsed_id = str(uuid.UUID(submission_id))
    except ValueError as exc:
        raise HTTPException(404, "Submission not found.") from exc
    with database() as connection:
        row = connection.execute(
            "SELECT original_filename, stored_filename FROM submissions WHERE id = ?",
            (parsed_id,),
        ).fetchone()
    if row is None:
        raise HTTPException(404, "Submission not found.")
    file_path = (UPLOAD_DIR / row["stored_filename"]).resolve()
    if file_path.parent != UPLOAD_DIR or not file_path.is_file():
        raise HTTPException(404, "Submission file not found.")
    return FileResponse(file_path, filename=row["original_filename"], media_type="application/octet-stream")


@app.delete("/api/admin/submissions/{submission_id}", status_code=204, dependencies=[Depends(require_admin)])
def delete_submission(submission_id: str) -> None:
    try:
        parsed_id = str(uuid.UUID(submission_id))
    except ValueError as exc:
        raise HTTPException(404, "Submission not found.") from exc
    with database() as connection:
        row = connection.execute(
            "SELECT stored_filename FROM submissions WHERE id = ?", (parsed_id,)
        ).fetchone()
        if row is None:
            raise HTTPException(404, "Submission not found.")
        connection.execute("DELETE FROM submissions WHERE id = ?", (parsed_id,))
    (UPLOAD_DIR / row["stored_filename"]).unlink(missing_ok=True)
