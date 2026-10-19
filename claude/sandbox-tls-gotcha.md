# Sandbox TLS gotcha on macOS: `gh` vs `git`

With the Claude Code sandbox enabled and
`sandbox.network.allowedDomains` listing GitHub hosts, `git push` /
`git pull` / `git fetch` work sandboxed, but `gh` (and other Go-based
CLIs, e.g. `grpcurl`, `kubectl`) fail with:

```
tls: failed to verify certificate: x509: OSStatus -26276
```

This is not a network allowlist problem — the sandbox opened the
route. It's macOS certificate trust.

## Why

The Claude Code sandbox routes traffic through a localhost HTTP/SOCKS
proxy (`HTTP_PROXY=http://localhost:<port>` etc.) that CONNECT-tunnels
to allowed domains. It is not MITMing TLS — clients talk TLS directly
to the origin over the tunnel.

`git` on macOS uses libcurl, which verifies origin certs against a
PEM bundle on disk (`/etc/ssl/cert.pem`). Reading that file is not
blocked by the sandbox, so `git` is happy.

`gh` is a Go binary built with cgo. Go on macOS with cgo delegates
TLS verification to the Security framework (`SecTrust*` APIs), which
requires Mach IPC to `trustd`. The Claude sandbox blocks that IPC
path, so `SecTrust` returns a generic OSStatus failure (`-26276`) and
the TLS handshake aborts.

## What doesn't help

- `SSL_CERT_FILE=/etc/ssl/cert.pem` — ignored by Go's cgo Darwin
  root loader. (Pure-Go builds and non-Darwin platforms honor it;
  Homebrew `gh` is cgo Darwin.)
- `GODEBUG=x509usefallbackroots=1` — only kicks in when the system
  root pool loads as empty. Here the system path errors out, so
  fallback roots are not consulted.
- Adding GitHub hosts to `sandbox.network.allowedDomains` — needed,
  but solves the network layer only, not cert trust.
- Trusting a custom CA in `/etc/ssl/cert.pem` — the sandbox proxy
  does not MITM, so there is no extra CA to trust.

There is no runtime switch that forces a cgo-built Go binary on
macOS to use a file-based CA bundle.

## Current workaround

Keep `gh` commands on the Claude permission allowlist (see
`claude/settings.json.base`). When `gh` runs sandboxed it fails fast
on the SecTrust error; Claude detects the sandbox-caused failure and
retries with the sandbox disabled, where the allowlist lets it
through without a prompt.

Cost: an extra second or two per `gh` call and a scary-looking TLS
error line in the transcript. Benefit: the sandbox still constrains
novel, non-allowlisted commands and non-GitHub network reach.

## When to revisit

- Claude Code exposes (or documents) a way to allow
  `com.apple.trustd` Mach access in the sandbox profile.
- Go adds a cgo-Darwin path that honors `SSL_CERT_FILE` (tracking
  upstream Go issues around x509 roots on Darwin).
- Switching to a non-cgo build of `gh` (not straightforward via
  Homebrew).
