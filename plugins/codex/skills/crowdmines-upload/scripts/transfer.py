"""Portable, standard-library-only binary transfer; no MCP or OAuth store dependency."""

from __future__ import annotations

import argparse
import hashlib
import http.client
import json
import os
import re
import ssl
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

CHUNK = 256 * 1024
MAX_FILE = 200 * 1024 * 1024
MAX_DESCRIPTOR = 16 * 1024


class TransferError(ValueError):
    """A safe error message which never contains an upload credential."""


def _inspect(handle: Any, filename: str) -> dict:
    stat = os.fstat(handle.fileno())
    if stat.st_size <= 0 or stat.st_size > MAX_FILE:
        raise TransferError("File must contain between 1 byte and 200 MiB")
    digest = hashlib.sha256()
    size = 0
    while chunk := handle.read(CHUNK):
        size += len(chunk)
        if size > MAX_FILE:
            raise TransferError("File grew beyond the upload limit")
        digest.update(chunk)
    if size != stat.st_size:
        raise TransferError("File changed while inspecting it")
    handle.seek(0)
    return {"filename": filename, "size_bytes": size, "sha256": digest.hexdigest()}


def inspect_file(path: str | Path) -> dict:
    """Compute tool input metadata without returning the file contents."""
    file = Path(path).expanduser().resolve(strict=True)
    if not file.is_file():
        raise TransferError("Select a regular file")
    with file.open("rb") as handle:
        return _inspect(handle, file.name)


def _origin(value: str) -> tuple[str, str, int]:
    parsed = urlsplit(value)
    if (
        parsed.scheme not in {"https", "http"}
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
    ):
        raise TransferError("Invalid upload origin")
    if parsed.scheme == "http" and parsed.hostname not in {
        "localhost",
        "127.0.0.1",
        "::1",
    }:
        raise TransferError("Upload requires HTTPS except on loopback")
    return (
        parsed.scheme,
        parsed.hostname.lower(),
        parsed.port or (443 if parsed.scheme == "https" else 80),
    )


def upload_file(path: str | Path, descriptor: dict, *, server_origin: str) -> dict:
    """Stream a file to a descriptor from upload_dataset.

    server_origin is trusted configuration, not copied from the descriptor.
    A framework may pass the full tool result or its transfer object. Never
    put the descriptor in command arguments, logs or a persisted config.
    """
    transfer = descriptor.get("transfer", descriptor)
    if not isinstance(transfer, dict):
        raise TransferError("Invalid transfer descriptor")
    url = transfer.get("url", "")
    parsed = urlsplit(url)
    origin = _origin(url)
    if origin != _origin(server_origin):
        raise TransferError(
            "Upload destination does not match the configured CrowdMines server"
        )
    if transfer.get("method") != "PUT" or not re.fullmatch(
        r"/mcp/uploads/[A-Za-z0-9_-]+/content", parsed.path
    ):
        raise TransferError("Descriptor must name a CrowdMines binary upload endpoint")
    headers = transfer.get("headers", {})
    authorization = headers.get("Authorization", "")
    if (
        not isinstance(authorization, str)
        or not authorization.startswith("Bearer ")
        or any(c in authorization for c in "\r\n")
    ):
        raise TransferError("Descriptor is missing its upload credential")
    if headers.get("Content-Type") != "application/octet-stream":
        raise TransferError("Descriptor must request raw binary content")
    file = Path(path).expanduser().resolve(strict=True)
    if not file.is_file():
        raise TransferError("Select a regular file")
    with file.open("rb") as handle:
        metadata = _inspect(handle, file.name)
        if metadata["size_bytes"] != transfer.get("size_bytes") or metadata[
            "sha256"
        ] != transfer.get("sha256"):
            raise TransferError(
                "Selected file differs from the authorized size or checksum"
            )
        connection: http.client.HTTPConnection
        if origin[0] == "https":
            connection = http.client.HTTPSConnection(
                origin[1], origin[2], timeout=60, context=ssl.create_default_context()
            )
        else:
            connection = http.client.HTTPConnection(origin[1], origin[2], timeout=60)
        try:
            connection.putrequest("PUT", parsed.path)
            connection.putheader("Authorization", authorization)
            connection.putheader("Content-Type", "application/octet-stream")
            connection.putheader("Content-Length", str(metadata["size_bytes"]))
            connection.endheaders()
            remaining = metadata["size_bytes"]
            while remaining:
                chunk = handle.read(min(CHUNK, remaining))
                if not chunk:
                    raise TransferError(
                        "File changed while transferring; retry with the same upload intent"
                    )
                connection.send(chunk)
                remaining -= len(chunk)
            response = connection.getresponse()
            # Never follow redirects or print upstream response bodies/headers.
            if response.status < 200 or response.status >= 300:
                raise TransferError(
                    f"Upload refused with HTTP {response.status}; check the intent before retrying"
                )
            response.read(64 * 1024)
        except (OSError, http.client.HTTPException):
            raise TransferError(
                "Transfer interrupted; check the intent and retry the same upload"
            ) from None
        finally:
            connection.close()
    return {
        "status": "uploaded",
        "upload_id": descriptor.get("upload_id") or parsed.path.split("/")[-2],
        **metadata,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Inspect and stream a selected file to CrowdMines without reading OAuth credentials"
    )
    commands = parser.add_subparsers(dest="command", required=True)
    inspect = commands.add_parser("inspect")
    inspect.add_argument("file")
    upload = commands.add_parser("upload")
    upload.add_argument("file")
    upload.add_argument(
        "--server",
        required=True,
        help="Trusted CrowdMines origin, configured independently of the descriptor",
    )
    args = parser.parse_args()
    try:
        if args.command == "inspect":
            result = inspect_file(args.file)
        else:
            raw = sys.stdin.buffer.read(MAX_DESCRIPTOR + 1)
            if len(raw) > MAX_DESCRIPTOR:
                raise TransferError("Transfer descriptor is too large")
            descriptor = json.loads(raw)
            if not isinstance(descriptor, dict):
                raise TransferError("Transfer descriptor must be a JSON object")
            result = upload_file(args.file, descriptor, server_origin=args.server)
        print(json.dumps(result))
    except (OSError, ValueError, TypeError, AttributeError):
        # A path or malformed descriptor may contain credentials; do not echo it.
        print(
            json.dumps(
                {
                    "error": "Transfer failed; verify the selected file, upload descriptor and server origin"
                }
            ),
            file=sys.stderr,
        )
        raise SystemExit(1) from None


__all__ = ["TransferError", "inspect_file", "main", "upload_file"]


if __name__ == "__main__":
    main()
