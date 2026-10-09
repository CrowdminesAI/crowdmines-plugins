# CrowdMines client marketplace

Install the CrowdMines Dev plugin in Codex or Claude Code from this public GitHub
marketplace. It includes the MCP connection, upload skill, and standalone Python
upload helper. The current bundle version is **0.5.1**.

The plugin connects to **https://dev.emthanh.me/mcp**. Complete CrowdMines login,
MFA if required, and organization consent. Public installation does not grant access
to account data. Local uploads require Python 3.10+; no separate helper installation
is needed. Use either the plugin or a manual MCP connection, not both: each adds the
same tools under its own name.

## Codex

```sh
codex features enable mcp_2026_07_28
codex plugin marketplace add CrowdminesAI/crowdmines-plugins --ref main
codex plugin add crowdmines-dev@crowdmines
codex mcp login crowdmines-dev
codex
```

The tested Codex 0.160.0 speaks the July 2026 MCP protocol only with the
`mcp_2026_07_28` feature on. The first command saves it in your Codex configuration,
so you run it once; restart any Codex that is already running. Installing the plugin
does not sign in: `codex mcp login crowdmines-dev` opens the browser sign-in. To
update, refresh the marketplace and install its current bundle:

```sh
codex plugin marketplace upgrade crowdmines
codex plugin add crowdmines-dev@crowdmines
```

Restart the client after updating. These are explicit updates; unattended Codex
updates are not promised. See [Codex marketplace documentation](https://developers.openai.com/plugins/build/plugins).

## Claude Code

```sh
claude plugin marketplace add CrowdminesAI/crowdmines-plugins
claude plugin install crowdmines-dev@crowdmines
claude mcp login plugin:crowdmines-dev:crowdmines-dev
claude
```

Complete browser login and consent. The login command needs an interactive terminal;
inside Claude Code, `/mcp` offers the same sign-in. To update explicitly:

```sh
claude plugin marketplace update crowdmines
claude plugin update crowdmines-dev@crowdmines
```

Restart the client after updating. To opt into automatic updates, open `/plugin`,
select **Marketplaces → crowdmines → Enable auto-update**. Third-party marketplaces
do not enable it by default. See [Claude plugin updates](https://code.claude.com/docs/en/discover-plugins#keep-plugins-updated).

## Existing installations

If `crowdmines` already points to an extracted ZIP directory or an older distribution
repository, remove that marketplace and add the GitHub source above. Claude removes
plugins installed from a marketplace when it is removed, so install the plugin again.

```sh
codex plugin marketplace remove crowdmines
# Or:
claude plugin marketplace remove crowdmines
```

If you added the CrowdMines server by hand as `crowdmines`, remove that entry before
using the plugin:

```sh
codex mcp remove crowdmines
# Or:
claude mcp remove crowdmines
```

If you installed an earlier bundle in Codex, run `codex features enable mcp_2026_07_28`
once; plain `codex` and `codex mcp login crowdmines-dev` then need no extra options. Do
not disconnect your CrowdMines grant solely to update packages. Follow any fresh login
prompt the client presents. Normal installations already pointing to this repository
only need the update commands.

## Uploads

The bundled skill inspects a local file, creates an upload intent over MCP, transfers
bytes directly to CrowdMines, completes the upload, and polls its durable operation.
The 200 MiB limit, checksum, destination checks, and retry identifiers are preserved.

Temporary upload-only credentials may enter model context and retained conversations.
The skill passes the descriptor to the helper through a separate stdin channel or, on
POSIX systems, a private single-use file: a new owner-only (0700) temporary directory
holding a file created empty with mode 0600 before the credential arrives, then filled
by the client's file-writing tool. Only the file's path enters the shell, and the
helper deletes the file before transfer. Never put the descriptor in shell commands,
arguments, heredocs or logs. Hosts that can do neither use website upload and then
access the dataset through MCP. The helper never reads client OAuth stores.

## Distribution

This repository contains generated client bundles, both marketplace catalogs, and
installation instructions. Development source, tests, build tooling, and server code
remain in private `CrowdminesAI/crowdmines-mcp`. Generated Python and skill files are
public and inspectable; make changes in the private source and publish a new version.

[Releases](https://github.com/CrowdminesAI/crowdmines-plugins/releases) also provide
individual client ZIPs, a complete marketplace ZIP, and SHA256SUMS. You can still
extract the complete ZIP to a permanent directory and register that local directory;
local ZIP installations require downloading new versions manually. Published assets
are immutable; corrective releases use a new version.
