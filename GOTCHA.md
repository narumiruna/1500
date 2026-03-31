# GOTCHA

- `urllib.request.urlopen` network failures are not consistently wrapped as `URLError`; TLS/transport problems can surface as raw exceptions like `ConnectionResetError`. Catch broad exceptions at the CLI boundary to avoid unhandled tracebacks and ensure deterministic exit codes.
