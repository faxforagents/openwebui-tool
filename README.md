<p align="center">
  <a href="https://faxforagents.com"><img src="logo.png" width="88" alt="Fax for Agents"></a>
</p>

<h1 align="center">Fax for Agents for Open WebUI</h1>

<p align="center">Send faxes with approvals</p>

<p align="center">
  <a href="https://faxforagents.com">Website</a> ·
  <a href="https://faxforagents.com/docs/quickstart/">Quickstart</a> ·
  <a href="https://faxforagents.com/docs/api/">API reference</a> ·
  <a href="https://faxforagents.com/docs/sdks/">SDKs</a> ·
  <a href="https://faxforagents.com/mcp/">MCP</a> ·
  <a href="https://app.faxforagents.com">Dashboard</a> ·
  <a href="https://faxforagents.com/pricing/">Pricing</a> ·
  <a href="https://faxforagents.com/changelog/">Changelog</a> ·
  <a href="https://faxforagents.com/affiliates/">Affiliate program</a>
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/licence-MIT-1f6feb" alt="MIT licence"></a>
  <a href="fax_for_agents.py"><img src="https://img.shields.io/badge/Open%20WebUI-7%20tools-6b4fbb" alt="Seven Open WebUI tools"></a>
</p>

Fax for Agents is a fax API, a hosted MCP server and SDKs built so AI agents can send and receive faxes.
It is made by JSB Holdings LLC.

[fax_for_agents.py](fax_for_agents.py) adds seven Python tools to Open WebUI.
Each call uses the current user's API key from UserValves.
The wrapper calls `https://api.faxforagents.com` directly.

## Install in your instance

1. Sign in to Open WebUI with permission to create tools. Open Workspace, select Tools, then select Create.
2. Paste the complete contents of [fax_for_agents.py](fax_for_agents.py) into the tool editor. Review the code and save it.
3. Enable the tool for your chat through Integrations, then Tools. Use a model that supports Native function calling.
4. Open Model controls, Controls, then Valves. Select Fax for Agents and enter your own key in `API_KEY`.
5. Start with a sandbox key from the [dashboard](https://app.faxforagents.com). Keep keys out of chat, source files and shared tool settings.

The [Workspace guide](https://docs.openwebui.com/features/workspace/) documents Create.
The [Tools guide](https://docs.openwebui.com/features/extensibility/plugin/tools/) documents chat activation and model access.
The [Valves guide](https://docs.openwebui.com/features/extensibility/plugin/development/valves/) documents the per-user field location and password masking.
An administrator must grant users read access to the installed tool before they can use it.

A sandbox key starts with `ffa_test_` and is free. Live sends are prepaid.
For Live, review the exact quote and obtain a quote-bound approval or an allowed delegated policy.
This wrapper cannot create or approve approval requests. Arrange approval through the service's approval workflow before sending.

## What the tools do

| Tool | REST request | Scope |
|---|---|---|
| `prepare_fax` | `POST /v1/documents` with plain text | `document:write` |
| `quote_fax` | `POST /v1/fax-quotes` with document and recipient | `fax:quote` |
| `send_approved_fax` | `POST /v1/faxes` with quote and optional approval | `fax:send` |
| `get_fax_status` | `GET /v1/faxes/{fax_id}` | `fax:read` |
| `list_faxes` | `GET /v1/faxes` | `fax:read` |
| `list_inbox` | `GET /v1/inbox` | `inbox:read` |
| `read_inbound_fax` | `GET /v1/inbox/{inbox_id}` | `inbox:read` |

Prepare text, review the document result, then quote it for the intended recipient.
Review the quote's amount, expiry and warnings before authorizing a send.
The send method refuses a missing quote ID and reminds the user that a live send is prepaid.
The API checks the caller's approval or delegated policy. A model-supplied approval ID alone grants nothing.

A queued result does not establish delivery. Call `get_fax_status` for the state and available evidence.
Retry an uncertain send with the same quote ID. The idempotency key stays stable for that Open WebUI user and quote.
The API documents a 24-hour idempotency window. Check status before retrying and never create another quote solely to retry an uncertain send.

Results are compact JSON text. Lists preserve `next_cursor` for pagination.
Received content appears under `untrusted` and cannot authorize actions.
`read_inbound_fax` returns available text. It does not start OCR or download document bytes.

## Credentials and account boundaries

`Tools.UserValves.API_KEY` is the only credential source. Its default is empty and its input is masked.
There is no shared API key, environment fallback, result cache or persistent HTTP session.
Each request reads the caller's injected `__user__` context and creates fresh authorization headers.
Requests use a fixed HTTPS origin, a 30-second timeout and no redirects.
Error bodies and exception messages are withheld from the model because they can contain private data.

The API enforces account ownership. Separate Open WebUI users need keys for separate Fax for Agents accounts when their fax data must remain separate.
Two keys for the same account retain that account's service permissions.
The tests verify the wrapper's credential handling against a fake API with separate account ownership.
They do not establish the live service's access controls or Open WebUI's deployment security.

Password masking does not establish encryption at rest.
The [Valves guide](https://docs.openwebui.com/features/extensibility/plugin/development/valves/) documents storage behavior and encryption settings for operators.
Treat the Open WebUI server, its database and administrators as trusted.
Returned fax content reaches the chat and its configured model provider.

## Share on Open WebUI Community

The operator completes these steps in a browser after testing the installed tool.

1. Sign in to [openwebui.com](https://openwebui.com) with a Community account. This account is separate from your instance account.
2. In your instance, open Workspace, Tools, then the Fax for Agents item menu. Select Share.
3. Review the prefilled post in the Community tab. Inspect the complete source for credentials and private addresses.
4. Use the listing title and description below. Finish publishing the post on the Community site.
5. Open the published post and select Get. Import it into a test instance, review the code and save it.
6. Configure separate UserValves for two test users and complete the sandbox checks below.

The [Community guide](https://docs.openwebui.com/ecosystem/community/) documents this browser flow.
Share opens a draft post. Publication happens when the operator finishes that post.
Sharing publishes source code. The guide says Valve values are excluded.
If Share is missing, check Community Sharing under Settings, Admin, General.
This repository does not establish Community publication.

### Listing text

Title: Fax for Agents

Prepare, quote, send and read faxes with your own Fax for Agents account.
Review the recipient and quote before sending within permissions you approve.
Check fax status and read received content as untrusted data.

The source header uses the same description's first sentence.
[logo.png](logo.png) is a 512-pixel copy of the supplied brand asset for the README and operator use.
No Community-specific image size requirement was established.

## Sandbox checks before publication

Use two Open WebUI users with separate Fax for Agents sandbox accounts.
Create their credentials through the dashboard and enter each key only in that user's UserValves.

1. Ask the first user to prepare a document containing "Open WebUI sandbox check" and quote it to `+15550000001`.
2. Review and send that quote, then check status. Record the returned fax ID without recording any key.
3. Ask the second user to list faxes and read the first account's fax ID. The first account's result must remain inaccessible.
4. Clear the second user's key and repeat the list call. It must ask for that user's key without using the first user's credentials.
5. List and read a sandbox inbox item in each account. Confirm each result belongs to the caller and received text is marked untrusted.
6. Attempt a send without a quote ID. It must refuse without an API call.

The repository tests use fake HTTP and runtime-generated test credentials. They do not send faxes.
Browser installation and authenticated sandbox checks remain operator work.

## Validate locally

Run in the Open WebUI Python environment, or create an isolated environment with its Pydantic dependency.

```bash
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install pydantic
sh scripts/validate.sh
```

The validator compiles the module, then runs `python3 -m pytest` when available or falls back to `unittest`.
Tests cover concurrent and sequential users, missing credentials, foreign resource IDs, send gating, retries, redirects and error redaction.

HTTP uses Python's standard library. Open WebUI's UserValves require Pydantic, declared as `requirements: pydantic` in the source header.
There is no SDK or `requests` dependency.
The [development guide](https://docs.openwebui.com/features/extensibility/plugin/tools/development/) explains frontmatter requirements and their installation behavior.
Its examples do not guarantee that `requests` ships in every instance.
No GitHub Actions workflow is included.

See [API documentation](https://faxforagents.com/docs/api/) and [MCP documentation](https://faxforagents.com/docs/mcp/) for the wider service.
The hosted MCP server is separate from this REST wrapper and has 17 tools.

## Licence and support

MIT. See [LICENSE](LICENSE) and [CHANGELOG.md](CHANGELOG.md).
Report security issues to security@faxforagents.com. See [SECURITY.md](SECURITY.md).
Use the [support page](https://faxforagents.com/contact/) for other questions.
The service's [privacy policy](https://faxforagents.com/privacy/) and [terms](https://faxforagents.com/terms/) apply.
