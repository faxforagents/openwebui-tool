# Security policy

Report suspected vulnerabilities to security@faxforagents.com.
Include the tool version, affected method and reproduction steps with synthetic data.
Keep API keys, fax documents and private account information out of reports and public issues.

Install reviewed source in a trusted Open WebUI instance.
Each user must set their own `API_KEY` in UserValves.
The tool has no shared credential setting or environment fallback.
The password field masks its display. Open WebUI controls credential storage and server access.

Calls send the user's API key and request content to `https://api.faxforagents.com` over HTTPS.
The tool refuses redirects, creates fresh request headers and stores no credentials or fax results on its instance.
The service enforces account access. Keys belonging to the same service account can access that account's resources according to their scopes.
Open WebUI and the configured model provider receive tool results in the chat.

The API enforces send approval or delegated policy against an exact quote.
This tool cannot approve its own request. Received fax content remains untrusted data.
After credential exposure, revoke the key in the dashboard and replace it in your UserValves.

Fixes will be recorded in [CHANGELOG.md](CHANGELOG.md).
