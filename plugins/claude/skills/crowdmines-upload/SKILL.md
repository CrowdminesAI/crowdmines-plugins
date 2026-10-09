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
   Alternatively, on POSIX systems create a fresh temporary directory using the
   system temporary-directory facility with mode 0700. Before handling the credential,
   create an empty descriptor file with mode 0600 (for example, `install -m 600
   /dev/null PATH` inside that private directory). Use the harness's file-writing
   facility to write JSON into that already-private file, preserving its mode. Do not
   create a world-readable descriptor and fix its permissions afterward. Invoke
   `upload FILE --server https://dev.emthanh.me --descriptor-file PATH`, passing only
   the path through the shell. The script verifies ownership and permissions, rejects
   links and non-regular files, and deletes the descriptor before reading/transfer.
   Never put the credential in shell code or a heredoc. The file option and
   `--descriptor-stdin` are mutually exclusive. If the harness cannot create a private
   file or supply stdin safely, use website upload; do not weaken permissions checks.
4. Call `complete_upload` with the receipt's upload_id and the user's questionnaire
   decision: without if none, later if it will follow. Poll the returned operation
   using `get_operation`; wait for graph_status=ready before graph-dependent analysis.
   If graph_status=not_applicable, report successful ingestion without graph support;
   do not poll indefinitely or claim graph-dependent tools are ready.
   For a questionnaire, complete the dataset with later and wait for ingestion to
   succeed before creating the questionnaire intent. Then transfer and
   complete a questionnaire intent against that dataset. On cancellation abort the
   unfinished intent with `abort_upload`.

## Credentials and retries

The temporary upload-only credential may appear in the MCP result and model context;
conversation retention may retain it. Do not repeat it in chat, print it, log it, save
it to a file other than the restricted single-use descriptor described above, or
read the client's OAuth store. Only file metadata and safe receipts
belong in user-facing output. File bytes are transferred directly to the server.

The script rejects other origins and redirects. An interrupted transfer restarts
from byte zero against the same intent; it does not resume a byte range. Check status
before retrying. If interrupted before the helper consumes the descriptor, delete
that file and remove its temporary directory. Do not reuse leftover descriptor files.
If the credential expired, repeat upload_dataset with the same
request_id and metadata. Stop on repeated failure and report the safe error.

The organization is fixed at consent; reconnect to change it. AI usage and storage
follow existing organization billing and allowances.
