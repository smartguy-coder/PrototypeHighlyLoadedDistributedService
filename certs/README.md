# CockroachDB TLS Certificates

> ⚠️ **DEVELOPMENT-ONLY CERTIFICATES**
>
> The certificates in this directory are intentionally committed to the
> repository for **local development convenience only**. They are
> regenerable junk, not secrets.
>
> **Never** use these certs (or this CA) in staging, production, or any
> environment with real data.

## What's in here

| File | Purpose | Mounted into |
|------|---------|--------------|
| `ca.crt` | CA certificate (trust anchor). Clients verify the server using this. | `roach1`, `roach2`, `roach3`, `roach-init`, `storefront_catalog_service` |
| `node.crt` + `node.key` | Node identity. Each Cockroach node presents this to peers and clients. | `roach1`, `roach2`, `roach3` (read-only) |
| `client.root.crt` + `client.root.key` | Root client cert for admin SQL operations. | `roach-init` (read-only) |

The CA **private key** (`ca.key`) lives in `../certs-ca/` and is **gitignored**.
That's the conventional CockroachDB layout: the CA key is what you'd need to
mint new certs (or impersonate someone), so it's kept apart from the runtime
material.

## How to (re)generate

From the project root:

```bash
make cockroach-certs           # generate (idempotent, skips if certs exist)
make cockroach-certs-clean     # wipe ./certs and ./certs-ca
make cockroach-certs-rotate    # wipe + regenerate (also requires wiping ./data/roach*)
```

The Makefile targets shell out to `cockroach cert` inside a one-shot Docker
container, so you don't need the `cockroach` binary installed locally.

Alternatively, via Docker Compose:

```bash
docker compose --profile bootstrap up cert-generator
```

## Why both a Makefile target and a `cert-generator` service?

- **`make cockroach-certs`** — the idiomatic way. Explicit, fast, easy to debug.
- **`cert-generator` service** — same logic, useful when you want everything
  done through `docker compose` (e.g. CI). Both are idempotent and produce
  identical output.

## Trust model

- The cluster authenticates **server-to-client** with TLS (`sslmode=verify-full`):
  Django checks that the server's `node.crt` was signed by `ca.crt`.
- The cluster authenticates **client-to-server** with **password**, not a
  client cert. Only the `root` user has a client cert; application users
  (`django`) use SQL passwords.
- This is fine because the password travels inside the encrypted TLS channel.

## When to wipe

Regenerate certs whenever:

- You see TLS handshake errors that don't go away after `docker compose down`.
- Certs have expired (default validity: 1 year for client certs, 5 years for CA).
- You added or renamed a Cockroach node (need to re-run `create-node` with the
  new hostname list).

Note that the on-disk Cockroach data (`./data/roach1-3`) is bound to the CA
that signed the cluster. If you rotate the CA, you must also wipe `./data/`,
otherwise the cluster won't start. `make cockroach-certs-rotate` reminds you
of this.
