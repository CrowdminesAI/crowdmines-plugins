# CrowdMines Dev for Codex

Download client bundles from [Releases](https://github.com/CrowdminesAI/crowdmines-plugins/releases).
This repository distributes built packages and installation instructions only.
Development source and build workflows live in the private `CrowdminesAI/crowdmines-mcp`
repository. The files required to run a plugin, including its Python upload script
and skills, remain inspectable inside the downloaded bundle.

The current plugin connects to **https://dev.emthanh.me/mcp**. CrowdMines login and
organization consent are required. Python 3.10+ is required for local uploads; no pip
package installation is needed. Public downloads do not grant account or data access.

## Install version 0.4.2

Download `crowdmines-marketplace-0.4.2.zip` and `SHA256SUMS` from the release page,
verify the checksum, and extract the ZIP into a permanent local directory such as
`crowdmines-marketplace-0.4.2`. It includes catalogs and both client bundles.
Do not remove that directory while using the local marketplace.

Codex:

```sh
codex plugin marketplace add /absolute/path/crowdmines-marketplace-0.4.2
codex plugin add crowdmines-dev@crowdmines
codex --enable mcp_2026_07_28 mcp login crowdmines-dev --oauth-client-registration cimd --scopes datasets:read,datasets:write,analysis:read,analysis:run,offline_access
codex --no-daemon --enable mcp_2026_07_28
```

Claude Code:

```sh
claude plugin marketplace add /absolute/path/crowdmines-marketplace-0.4.2
claude plugin install crowdmines-dev@crowdmines
claude mcp login plugin:crowdmines-dev:crowdmines-dev
claude
```

Complete browser login, MFA if required, and organization consent. Use the plugin or
a manually configured MCP connection, avoiding duplicate tools. The tested Codex
version requires the July protocol flag; plugin installation does not enable it.

## Migrate or update

If you already registered a marketplace named `crowdmines`, remove that source before
adding the extracted new version. This applies to both former Git repository sources
and older downloaded bundles:

```sh
codex plugin marketplace remove crowdmines
# Or for Claude Code:
claude plugin marketplace remove crowdmines
```

Then repeat installation using the new directory, restart your client, and verify
the installed version. Do not disconnect the CrowdMines account solely to update
packages; follow login prompts only if required. Older Git-based marketplace commands
no longer work against this README-only repository. These downloaded bundles do not
automatically update; download and install a new release when needed.

## Uploads

The bundle includes the upload script and skill. File bytes go directly to CrowdMines;
temporary upload-only credentials may enter model context and retained conversations.
The agent must pass the descriptor through a separate stdin channel, never embedding
it in shell commands, logs, or files. Hosts without that channel use website upload
and then access the dataset through MCP. Uploads are limited to 200 MiB.

## Release contents

- `crowdmines-marketplace-VERSION.zip`: both plugins plus local marketplace catalogs.
- `crowdmines-dev-codex-VERSION.zip` and `crowdmines-dev-claude-VERSION.zip`: individual bundles.
- `SHA256SUMS`: checksums for the three ZIP files.

GitHub's automatically generated source-code archives contain only this README, not
the plugins. Download the named release assets above.
