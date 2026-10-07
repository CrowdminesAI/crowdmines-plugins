---
name: crowdmines-upload
description: Upload a user-selected local survey file or questionnaire to CrowdMines, then check dataset processing.
---

Use the connected CrowdMines dev tools at https://dev.emthanh.me/mcp. If disconnected,
use the client's authentication action. Obtain permission to upload the selected file.
The file must be accessible in this harness; remote MCP does not grant attachment access.

## Bundled script

Run `python3 scripts/transfer.py` relative to this skill's directory (on Windows,
use `py -3`). Resolve the absolute script path from this installed SKILL.md; do not
assume the working directory is the plugin. Python 3.10+ is required, with no pip install.

1. Run `inspect FILE` to get filename, size_bytes, and sha256 without reading bytes
   into context. Maximum size is 200 MiB.
2. Call `upload_dataset` with that metadata and a new UUID request_id. Reuse the same
   ID and metadata on retries. For questionnaires include purpose=questionnaire and dataset_id.
3. Start `upload FILE --server https://dev.emthanh.me` with an input pipe. Send the
   JSON tool result (or its transfer object) through standard input and close input.
   Unwrap the MCP structured result first. Use a separate stdin-write facility;
   never interpolate the descriptor into shell code, command arguments, or a heredoc.
   If the harness cannot send stdin separately, use website upload instead.
4. Call `complete_upload` with the receipt's upload_id and the user's questionnaire
   decision: without if none, later if it will follow. Poll the returned operation
   using `get_operation`; wait for graph_status=ready before graph-dependent analysis.
   If graph_status=not_applicable, report successful ingestion without graph support;
   do not poll indefinitely or claim graph-dependent tools are ready.
   For a questionnaire, complete the dataset with later, then create, transfer and
   complete a questionnaire intent against that dataset. On cancellation abort the
   unfinished intent with `abort_upload`.

## Credentials and retries

The temporary upload-only credential may appear in the MCP result and model context;
conversation retention may retain it. Do not repeat it in chat, print it, log it, save
it to a file, or read the client's OAuth store. Only file metadata and safe receipts
belong in user-facing output. File bytes are transferred directly to the server.

The script rejects other origins and redirects. An interrupted transfer restarts
from byte zero against the same intent; it does not resume a byte range. Check status
before retrying. If the credential expired, repeat upload_dataset with the same
request_id and metadata. Stop on repeated failure and report the safe error.

The organization is fixed at consent; reconnect to change it. AI usage and storage
follow existing organization billing and allowances.
