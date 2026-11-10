from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path


def request(api: str, token: str, path: str, output: Path | None = None, method: str = "GET"):
    req = urllib.request.Request(
        api.rstrip("/") + path,
        headers={"Authorization": "Bearer " + token, "Accept": "application/json"},
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            data = response.read()
            if output is not None:
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_bytes(data)
                return {"saved_to": str(output), "bytes": len(data)}
            return json.loads(data.decode("utf-8")) if data else {}
    except urllib.error.HTTPError as exc:
        detail = exc.read(1000).decode("utf-8", errors="replace")
        raise SystemExit(f"API error {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise SystemExit(f"Could not reach intake API: {exc.reason}") from exc


def main() -> int:
    parser = argparse.ArgumentParser(description="Private Software QA Lab submission manager")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list", help="List customer submissions")
    download = sub.add_parser("download", help="Download one customer file")
    download.add_argument("submission_id")
    download.add_argument("--out", default="customer_uploads")
    delete = sub.add_parser("delete", help="Delete a submission and its stored file")
    delete.add_argument("submission_id")
    args = parser.parse_args()

    api = os.environ.get("INTAKE_API_URL", "").strip()
    token = os.environ.get("ADMIN_TOKEN", "")
    if not api.startswith("https://"):
        parser.error("Set INTAKE_API_URL to the deployed HTTPS API origin.")
    if len(token) < 32:
        parser.error("Set ADMIN_TOKEN to the private admin token (at least 32 characters).")

    if args.command == "list":
        result = request(api, token, "/api/admin/submissions")
        for item in result:
            print(
                f"{item['id']} | {item['created_at']} | {item['project_type']} | "
                f"{item['customer_name']} <{item['email']}> | "
                f"{item['original_filename']} ({item['file_size']} bytes)"
            )
            print("  " + item["description"].replace("\\n", " "))
    elif args.command == "download":
        listing = request(api, token, "/api/admin/submissions")
        item = next((entry for entry in listing if entry["id"] == args.submission_id), None)
        if item is None:
            raise SystemExit("Submission not found.")
        output = Path(args.out) / f"{args.submission_id}_{Path(item['original_filename']).name}"
        result = request(api, token, f"/api/admin/submissions/{args.submission_id}/file", output=output)
        print(f"Downloaded {result['bytes']} bytes to {result['saved_to']}")
    elif args.command == "delete":
        answer = input(f"Delete submission {args.submission_id} and its file permanently? Type DELETE: ")
        if answer != "DELETE":
            print("Cancelled.")
            return 1
        request(api, token, f"/api/admin/submissions/{args.submission_id}", method="DELETE")
        print("Submission and stored file deleted.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
