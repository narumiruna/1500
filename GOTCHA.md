# GOTCHA

- `urllib.request.urlopen` network failures are not consistently wrapped as `URLError`; TLS/transport problems can surface as raw exceptions like `ConnectionResetError`. Catch broad exceptions at the CLI boundary to avoid unhandled tracebacks and ensure deterministic exit codes.
- Before giving runnable commands, re-validate that referenced entrypoints/files still exist in the current workspace state. Do not assume earlier paths remain valid after user-side deletions or refactors.
