# PostgreSQL Dump & Restore

How to load a `.dump` file into the project's PostgreSQL container — both in this project (using **databasus** dumps) and in real-world environments at scale.

---

## Table of Contents

1. [Theory](#theory)
2. [What is databasus](#what-is-databasus)
3. [Dump Formats](#dump-formats)
4. [Restoring a Dump in This Project](#restoring-a-dump-in-this-project)
5. [Using DBeaver to Restore](#using-dbeaver-to-restore)
6. [Common Pitfalls](#common-pitfalls)
7. [How It's Done with Large Production Databases](#how-its-done-with-large-production-databases)
8. [Best Practices](#best-practices)

!!! tip "TL;DR — just want to restore a databasus backup?"
    Open [http://localhost:4005](http://localhost:4005) → select the backup → **Restore from backup** → pick the target DB. See [Option 1 below](#option-1-restore-through-the-databasus-ui-easiest) for details. Everything else on this page is for cases where the UI route doesn't fit.

---

## Theory

### What is a database dump?

A **dump** is a serialized snapshot of database content — schema (DDL), data (DML), or both — that can later be replayed to recreate the database elsewhere. PostgreSQL provides two utilities for this:

| Tool | Purpose |
|------|---------|
| `pg_dump` | Creates a dump of a single database |
| `pg_dumpall` | Creates a dump of an entire cluster (all databases + global objects like roles) |
| `pg_restore` | Restores from non-plain (custom/directory/tar) dumps |
| `psql` | Restores from plain SQL dumps |

In this project we use **databasus** to generate dumps from the local PostgreSQL on a schedule, and `pg_restore` (or `psql`, or databasus' own UI) to load them back into `postgres_storefront_catalog_service`.

### Logical vs Physical Backups

```
┌─────────────────────────────────────────────────────────────────┐
│              Logical vs Physical Backups                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   LOGICAL (pg_dump)                                             │
│   ─────────────────                                             │
│   • SQL statements: CREATE TABLE..., COPY..., INSERT...         │
│   • Portable across major versions                              │
│   • Slow on large databases (must replay everything)            │
│   • Good for: dev/staging copies, schema migration              │
│                                                                 │
│   PHYSICAL (pg_basebackup, pgBackRest)                          │
│   ────────────────────────────────────                          │
│   • Copy of data directory + WAL files                          │
│   • Bound to exact PostgreSQL version + arch                    │
│   • Fast — restore = file copy + WAL replay                     │
│   • Supports PITR (Point-in-Time Recovery)                      │
│   • Good for: production backups, DR, replication               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

This page focuses on **logical backups** since that's what databasus produces by default.

---

## What is databasus

[**databasus**](https://databasus.com/) is an open-source (Apache 2.0), self-hosted backup tool for PostgreSQL, MySQL, MariaDB, and MongoDB. In this project it runs as a service in `docker-compose.yml` (UI on port `4005`) and produces the `.dump` files we restore.

Under the hood it's a UI/scheduling/storage layer over standard tooling (`pg_dump`, WAL archiving). What it adds on top of hand-rolled cron + `pg_dump` scripts:

| Feature | What it gives us |
|---------|------------------|
| **Scheduled backups** | Hourly / daily / weekly / monthly / custom cron — configured in the UI, not in shell scripts |
| **Multiple destinations** | Local disk, S3, Google Drive, Dropbox, NAS, SFTP — one backup, many storage targets |
| **Compression** | zstd by default (~4–8× smaller files at ~20% time cost — the reason we hit the [zstd compression pitfall](#pitfall-1-this-build-does-not-support-compression-with-zstd)) |
| **Encryption** | AES-256-GCM per-backup keys, derived from a master key — backups are useless if the storage leaks |
| **Retention policies** | Auto-prune old backups by age, count, size, or GFS (Grandfather-Father-Son) |
| **Health checks** | Pings the database every minute, alerts after N failed attempts |
| **Notifications** | Slack, Telegram, email, webhooks — on success and on failure |
| **Read-only DB user** | Requires only `SELECT` permissions; refuses to start if write privileges are detected |
| **Backup modes** | *Remote* — connects over network, runs logical backup (like `pg_dump`). *Agent* — sidecar process for physical backups + WAL archiving + PITR |

### How it fits into this project

```
┌─────────────────────────────────────────────────────────────────┐
│              databasus in this project                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ┌──────────────────────────┐                                  │
│   │ postgres_storefront_     │                                  │
│   │ catalog_service          │                                  │
│   └────────┬─────────────────┘                                  │
│            │ SELECT-only connection                             │
│            ▼                                                    │
│   ┌──────────────────────────┐                                  │
│   │      databasus           │  scheduled (cron)                │
│   │   (port 4005, UI)        │  ─► dump (zstd-compressed)       │
│   └────────┬─────────────────┘                                  │
│            │                                                    │
│            ▼                                                    │
│   ┌──────────────────────────┐                                  │
│   │ ./data/databasus-data/   │  → optionally also S3/GDrive/etc │
│   │ (host volume)            │                                  │
│   └──────────────────────────┘                                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

From `docker-compose.yml`:

```yaml
databasus:
  container_name: databasus
  image: databasus/databasus:latest
  ports:
    - "4005:4005"
  volumes:
    - ./data/databasus-data:/databasus-data
  restart: unless-stopped
```

UI is at [http://localhost:4005](http://localhost:4005). Schedules, credentials, retention rules, and notification channels are all configured there — no shell scripts, no editing of the compose file.

### Connecting databasus to PostgreSQL (in our docker-compose setup)

When you create a backup job in the databasus UI, it asks for the database connection details. Because both databasus and PostgreSQL run as containers on the same Docker network, **databasus connects via the internal Docker hostname, not via `localhost`**.

Use these values in the databasus "Add database" form:

| Field | Value | Why |
|-------|-------|-----|
| **Host** | `postgres_storefront_catalog_service` | Service name from `docker-compose.yml` — resolves to the container's internal IP via Docker's DNS |
| **Port** | `5432` | PostgreSQL's internal port. **Not** 5555 — that's the host-side mapping (`5555:5432` in compose), only relevant from your laptop |
| **Database** | `storefront_catalog` | From `POSTGRES_DB` in `.env` |
| **User** | `postgres` | From `POSTGRES_USER` in `.env` |
| **Password** | `postgres` | From `POSTGRES_PASSWORD` in `.env` |
| **SSL** | Off (or skip) | Local dev, plaintext network is internal to Docker |

!!! warning "Why not `localhost:5555`?"
    Inside the databasus container, `localhost` means the *databasus container itself*, not your Mac/Linux host. Connecting to `localhost:5555` from databasus would fail — there's nothing listening there inside its container. The `5555:5432` port mapping in `docker-compose.yml` exists for tools running on the host (DBeaver, `psql` from your terminal), not for other containers.

```
FROM the host (your Mac/Linux):

    DBeaver / psql  ─── localhost:5555 ─────────────────►  postgres container
                                                              (mapped: 5555→5432)

FROM another container (databasus, Django, Celery):

    databasus  ─── postgres_storefront_catalog_service:5432 ─►  postgres container
                                                                  (internal port 5432)

Same database, two addresses depending on where you connect *from*.
The 5555:5432 mapping in docker-compose.yml is host-only — other
containers must use the service name + the internal port (5432).
```

This is the same reason the Django service in `docker-compose.yml` uses `POSTGRES_HOST=postgres_storefront_catalog_service` (not `localhost`) in `.env`.

!!! note "What databasus does *not* do"
    databasus is a **backup tool**, not a data anonymization tool. The dumps it produces contain real database content. If you need to share a sanitized copy of production data with developers, you'd combine databasus (for the backup) with a separate anonymization tool such as [pg_anonymize](https://gitlab.com/dalibo/postgresql_anonymizer), [replibyte](https://github.com/Qovery/Replibyte), or a custom transformation step.

### Why it's useful here

For a project like this — multiple stateful services, frequent local environment resets, and the need to reproduce a known-good database state — databasus replaces what would otherwise be a `cron` entry running:

```bash
# What databasus replaces (and improves on)
0 4 * * * pg_dump -Fc -Z zstd -h ... -U ... db | \
  aws s3 cp - s3://backups/db-$(date +\%F).dump.zst || \
  curl -X POST $SLACK_WEBHOOK -d '{"text":"backup failed"}'
```

…with a UI, retries, encryption, history, restore-from-UI, and audit logs. In this project we use it both for **regular scheduled backups** (in case we want to roll back the local DB to yesterday) and for producing the `.dump` files that this guide explains how to restore.

---

## Dump Formats

`pg_dump` supports four output formats. Knowing which one you have determines which tool to use.

| Format | Flag | File extension | Restore tool | Parallel? | Compressed? |
|--------|------|----------------|--------------|-----------|-------------|
| **Plain SQL** | `-Fp` (default) | `.sql` | `psql` | ❌ | Optional (gzip) |
| **Custom** | `-Fc` | `.dump` | `pg_restore` | ✅ Restore only | ✅ Built-in (gzip/zstd) |
| **Directory** | `-Fd` | folder | `pg_restore` | ✅ Both | ✅ Built-in |
| **Tar** | `-Ft` | `.tar` | `pg_restore` | ❌ | ❌ |

### How to identify the format

```bash
file /path/to/file.dump
```

| Output | Format |
|--------|--------|
| `PostgreSQL custom database dump` | Custom (`-Fc`) — use `pg_restore` |
| `ASCII text` / `UTF-8 Unicode text` | Plain SQL — use `psql` |
| `POSIX tar archive` | Tar — use `pg_restore` |

Inspect the table of contents of a custom/directory/tar dump:

```bash
pg_restore -l /path/to/file.dump | head -50
```

This shows every object the dump contains (tables, indexes, sequences, FK constraints, data).

---

## Restoring a Dump in This Project

### Prerequisites

From `.env`:

| Variable | Value |
|----------|-------|
| `POSTGRES_USER` | `postgres` |
| `POSTGRES_PASSWORD` | `postgres` |
| `POSTGRES_DB` | `storefront_catalog` |

PostgreSQL is exposed on the host at port **5555** (`5555:5432` in `docker-compose.yml`).

!!! warning "Don't restore through PgBouncer"
    Always restore directly to PostgreSQL on port **5555**, never through PgBouncer on **6432**. PgBouncer in `transaction` pool mode breaks DDL operations, prepared statements, and session-level state used by `pg_restore`. See [PgBouncer docs](pgbouncer.md#transaction-mode-what-works-and-what-doesnt) for the full list.

### Option 1: Restore through the databasus UI (easiest)

Since databasus is the tool that produced the dump, it's also the simplest way to restore it. No CLI, no DBeaver, no compression-codec issues — databasus runs `pg_restore` inside its own container, which has all the codecs (zstd, lz4, gzip) bundled.

**Steps:**

1. Open the databasus UI: [http://localhost:4005](http://localhost:4005)
2. Find the backup you want to restore (or upload a `.dump` file if it's not already in databasus' history)
3. Click **Restore from backup**
4. Select the target database — in our setup that's the `postgres_storefront_catalog_service` connection → `storefront_catalog`
5. Confirm. databasus streams the dump into the target database and shows progress in the UI

**When to use this:** for the vast majority of cases where you have a databasus-produced backup and want to roll back the local DB or load a recent backup. It Just Works.

**When *not* to use this:**

- The dump came from somewhere else (a colleague sent you a `.dump` file produced by raw `pg_dump`, not by databasus). You can still upload it through databasus, but if it fails for any reason (different format, custom flags), the CLI options below give you more control.
- You need fine-grained `pg_restore` flags (e.g. `--section=data`, `--disable-triggers`, restoring only specific tables). Use the CLI.
- You're debugging why a restore is failing — the CLI's `--exit-on-error -v` output is more diagnostic than UI logs.

!!! tip "Why this works without zstd issues"
    The [zstd compression pitfall](#pitfall-1-this-build-does-not-support-compression-with-zstd) only affects PostgreSQL clients on the host (Homebrew's `libpq`). databasus itself runs in a Docker container with the full PostgreSQL toolchain, so it always supports the compression methods it produced.

### Option 2: Restore inside the Docker container

The simplest CLI approach — copy the dump into the container and run `pg_restore` there. The official `postgres:17` image is built with all compression codecs (gzip, lz4, zstd), so format issues never arise. Use this when you want CLI control without dealing with local client setup.

```bash
# 1. Copy dump into the container
docker cp /path/to/backup.dump \
  postgres_storefront_catalog_service:/tmp/backup.dump

# 2. Restore (4 parallel workers)
docker exec -i postgres_storefront_catalog_service \
  pg_restore \
    -U postgres \
    -d storefront_catalog \
    --clean --if-exists --no-owner --no-privileges \
    -j 4 -v \
    /tmp/backup.dump

# 3. Clean up
docker exec postgres_storefront_catalog_service rm /tmp/backup.dump
```

### Option 3: Restore from host with local `pg_restore`

If your local PostgreSQL client is installed (and built with the right codecs — see [Common Pitfalls](#common-pitfalls)):

```bash
pg_restore \
  -h localhost -p 5555 \
  -U postgres \
  -d storefront_catalog \
  --clean --if-exists --no-owner --no-privileges \
  --exit-on-error \
  -j 4 -v \
  /path/to/backup.dump
```

### Restoring into an empty database

For the cleanest result, drop and recreate the database first (avoids conflicts with existing Django migrations):

```bash
# Stop services that hold connections
docker compose stop storefront_catalog_service celery_worker celery_beat

# Drop and recreate the database
docker exec -i postgres_storefront_catalog_service \
  psql -U postgres -d postgres -c \
    "DROP DATABASE IF EXISTS storefront_catalog;"
docker exec -i postgres_storefront_catalog_service \
  psql -U postgres -d postgres -c \
    "CREATE DATABASE storefront_catalog;"

# Run pg_restore (no need for --clean now)
docker cp /path/to/backup.dump \
  postgres_storefront_catalog_service:/tmp/backup.dump
docker exec -i postgres_storefront_catalog_service \
  pg_restore -U postgres -d storefront_catalog \
    --no-owner --no-privileges -j 4 -v \
    /tmp/backup.dump

# Bring services back
docker compose up -d storefront_catalog_service celery_worker celery_beat
```

### Key `pg_restore` flags

| Flag | Purpose |
|------|---------|
| `-j N` | Parallel restore with N workers (custom/directory format only) |
| `--clean` | Drop existing objects before recreating |
| `--if-exists` | With `--clean`, ignore "object doesn't exist" errors |
| `--no-owner` | Don't try to set object ownership (useful when dump came from a different user) |
| `--no-privileges` | Skip GRANT/REVOKE statements |
| `--exit-on-error` | Stop on first error (default: continue and report at end) |
| `--single-transaction` | Wrap restore in one transaction — atomic, but disables `-j` |
| `--disable-triggers` | For data-only restores, prevents FK/trigger failures |
| `--section=pre-data\|data\|post-data` | Restore only schema, only data, or only indexes/constraints |
| `-v` | Verbose output (shows each object as it's processed) |

---

## Using DBeaver to Restore

DBeaver doesn't restore dumps itself — it invokes a locally installed `pg_restore` binary and streams the file through it.

### Connection settings

| Setting | Value |
|---------|-------|
| Host | `localhost` |
| Port | `5555` |
| Database | `storefront_catalog` |
| User | `postgres` |
| Password | `postgres` |

### Configuring the local client

DBeaver doesn't have its own `pg_restore` — it shells out to a locally installed PostgreSQL client. **The client's major version must be ≥ the server's** (we run PostgreSQL 17, so the client must be 17+).

The local client is configured **inside the Restore dialog itself**, not in global settings:

1. Right-click the database in the Database Navigator → **Tools → Restore**
2. At the bottom of the dialog, find the **Local Client** field
3. Click **Browse** (or the dropdown) and select the directory containing `pg_restore` — for example, `/opt/homebrew/bin` on macOS with Homebrew, or `/opt/homebrew/Cellar/postgresql@17/<version>/bin` for a specific version
4. Important: select the **directory**, not the `pg_restore` binary itself
5. DBeaver remembers this per-connection, so you only need to set it once

If the dropdown is empty or you get "Local client is not specified", DBeaver couldn't auto-detect any client. Use Browse to point it at the right directory manually.

### Performing the restore

With the local client configured, in the same **Tools → Restore** dialog:

Recommended options:

| Option | Value |
|--------|-------|
| Format | Custom |
| Backup file | path to your `.dump` |
| Clean (drop) database objects before recreating | ✓ |
| Do not save the owner of the objects | ✓ |
| Do not output commands to set ownership | ✓ |
| Number of jobs | 4 |

DBeaver shows the generated command at the bottom of the dialog — read it before clicking **Start**, it's literally what will be executed.

---

## Common Pitfalls

### Pitfall 1: "this build does not support compression with zstd"

**Full error:**

```
pg_restore: warning: archive is compressed, but this installation
does not support compression (this build does not support compression
with zstd) -- no data will be available
pg_restore: error: cannot restore from compressed archive
```

**Cause.** Modern dumps (databasus, `pg_dump` 16+) often use **zstd** compression. Some PostgreSQL client builds — notably Homebrew's `libpq` formula on macOS — ship without zstd support, while the full `postgresql@17` formula includes it.

**Diagnosis on macOS:**

```bash
# What does the symlinked client point to?
which pg_restore
ls -l $(which pg_restore)

# Check both Homebrew formulas
brew list libpq && echo "libpq installed"
brew list postgresql@17 && echo "postgresql@17 installed"

# Verify zstd support in postgresql@17
/opt/homebrew/Cellar/postgresql@17/*/bin/pg_config --configure | tr ' ' '\n' | grep -i zstd
# Expected: --with-zstd
```

If `which pg_restore` resolves into `/opt/homebrew/Cellar/libpq/...` — that's the broken client. If `postgresql@17` is installed but not linked, you have the working one — just need to switch.

**Fix — switch Homebrew symlinks (recommended):**

```bash
# Remove libpq's symlinks from /opt/homebrew/bin (package stays installed)
brew unlink libpq

# Link postgresql@17 instead
brew link --force --overwrite postgresql@17

# Verify
which pg_restore
# /opt/homebrew/bin/pg_restore → now points to postgresql@17

pg_restore --version
# pg_restore (PostgreSQL) 17.x
```

After re-linking, the same `/opt/homebrew/bin/pg_restore` path that DBeaver uses will resolve to the zstd-capable binary. **No DBeaver reconfiguration needed.**

**Alternative — point DBeaver explicitly to `postgresql@17`:**

If you'd rather keep `libpq` linked globally (e.g. some other tool depends on its specific version), tell DBeaver to use `postgresql@17` directly in the Restore dialog:

1. Right-click the database → **Tools → Restore**
2. In the **Local Client** field at the bottom of the dialog, click **Browse**
3. Point it to `/opt/homebrew/Cellar/postgresql@17/<version>/bin`
4. The setting is remembered per-connection — you only need to set it once

**Why this happens.** Homebrew's `libpq` formula intentionally builds a minimal client without optional compression backends — it's designed as a lightweight library for applications that link against `libpq.dylib`. The full `postgresql@17` formula links against zstd, lz4, and other codecs because it's meant to run a full PostgreSQL server. Both formulas ship the same binaries (`pg_dump`, `pg_restore`, `psql`), but their build flags differ.

!!! tip "Verifying compression support before restoring"
    `pg_restore` doesn't have a flag to list supported codecs, but you can infer them from the `pg_config` of the matching install:
    ```bash
    /opt/homebrew/opt/postgresql@17/bin/pg_config --configure | tr ' ' '\n' | grep -E 'zstd|lz4|gzip'
    ```

### Pitfall 2: "Local client is not specified for connection"

DBeaver needs a locally installed `pg_restore` to do anything in **Tools → Restore**. If you see this error, either:

1. **No PostgreSQL client is installed.** Install one via `brew install postgresql@17` (recommended over `libpq` — see Pitfall 1).
2. **A client is installed but DBeaver can't find it.** Open the Restore dialog, scroll to the **Local Client** field at the bottom, click Browse, and point it at the directory containing `pg_restore` (e.g. `/opt/homebrew/bin` or `/opt/homebrew/Cellar/postgresql@17/<version>/bin`).

DBeaver does not have a global "PostgreSQL client" setting in Preferences — the client is configured per-connection inside the Restore/Backup dialogs themselves.

### Pitfall 3: Restore "succeeds" but tables aren't created

`pg_restore` continues on errors by default and exits with code 0 even if half the objects failed. To diagnose:

```bash
pg_restore \
  -h localhost -p 5555 -U postgres -d storefront_catalog \
  --clean --if-exists --no-owner --no-privileges \
  --exit-on-error -v \
  /path/to/backup.dump 2>&1 | tee restore.log
```

`--exit-on-error` fails on the first error; `tee` saves the log for review. Then check what's actually in the database:

```sql
-- All schemas (tables may be in a non-public schema!)
\dn

-- All tables across all schemas
\dt *.*

-- Or via SQL
SELECT schemaname, tablename
FROM pg_tables
WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
ORDER BY schemaname, tablename;
```

Common reasons for partial restore: tables in a non-`public` schema, restore targeted at the wrong database, missing PostgreSQL extensions (e.g. `uuid-ossp`, `pgcrypto`), or `--single-transaction` rolling back due to a single error.

### Pitfall 4: Conflict with Django migrations

Our `storefront_catalog_service` runs `manage.py migrate` on startup. If you restore a dump while migrations are running (or after), you get half-applied state. **Always stop the application services before restoring**:

```bash
docker compose stop storefront_catalog_service celery_worker celery_beat
# ... do restore ...
docker compose up -d storefront_catalog_service celery_worker celery_beat
```

If the restored dump's schema is older than current migrations, run `manage.py migrate` after restore to catch up.

### Pitfall 5: "too many connections" mid-restore

Our Postgres has `max_connections=100` and PgBouncer + Django + Celery can consume 30-60 of those. A `pg_restore -j 4` adds 4-5 more. If everything runs simultaneously you may hit `FATAL: too many connections` mid-restore, leaving the database in a partial state. Stop application services first (see Pitfall 4).

### Pitfall 6: After restore, DBeaver can't edit data — "Attribute X was changed but it hasn't associated unique key"

**Symptom.** Restore finished successfully, you open a table in DBeaver and try to change a row in the data grid — e.g. toggle `is_superuser` on a user — and get:

```
Attribute is_superuser was changed but it hasn't associated unique key
```

The SQL editor still works (`UPDATE auth_user SET is_superuser = TRUE WHERE id = 1` runs fine). Only the **grid editor** is broken.

**What it actually means.** DBeaver's grid editor needs to know the row's primary key to build a safe `UPDATE ... WHERE pk = ...`. The error says "I don't see a PK on this table." After a restore, the most common cause is **stale metadata cache**: DBeaver remembers the table from before the restore (when it had no PK, or no rows, or didn't exist) and didn't refresh after the restore replaced it.

**Fix — reconnect (works in 90% of cases):**

1. In Database Navigator, right-click the connection → **Disconnect**
2. Right-click the connection again → **Connect** (or **Invalidate/Reconnect**)
3. Reopen the table grid — editing should work

If reconnect alone doesn't help, also press **F5** on the schema/database to force a metadata refresh, or close and reopen the data tab.

**If reconnect doesn't fix it — the PK is genuinely missing.** Verify in SQL editor:

```sql
-- Does the table have a primary key?
SELECT conname, contype, pg_get_constraintdef(oid)
FROM pg_constraint
WHERE conrelid = 'public.auth_user'::regclass
  AND contype IN ('p', 'u');
```

If this returns nothing, the restore's `post-data` section (which contains PRIMARY KEY, UNIQUE, FOREIGN KEY, indexes) didn't apply. Re-run just that section to see the underlying error:

```bash
docker exec -i postgres_storefront_catalog_service \
  pg_restore -U postgres -d storefront_catalog \
    --section=post-data \
    --no-owner --no-privileges \
    -v \
    /tmp/backup.dump 2>&1 | tee post-data.log
```

Typical underlying cause: duplicate rows in the data prevent the unique index from being built (`ERROR: could not create unique index ... Key (id)=(N) is duplicated`). Usually means the dump was loaded on top of existing data instead of into an empty database — see Pitfall 4 for the clean-restore procedure.

!!! tip "Workaround while you investigate"
    Even when the grid editor refuses to work, the SQL editor always does:
    ```sql
    UPDATE auth_user SET is_superuser = TRUE WHERE username = 'admin';
    ```
    The grid editor's restriction is a UI safety check, not a database-level limitation.

---

## How It's Done with Large Production Databases

`pg_dump`/`pg_restore` is fine up to tens of GB. Beyond that, the toolchain changes. A quick tour of the levels:

### Level 1: Tens of GB — `pg_dump`/`pg_restore` with tuning

Same tools as above, but with thoughtful configuration:

- **Custom (`-Fc`) or directory (`-Fd`) format** — never plain SQL. Only these formats support `-j` (parallel restore).
- **`-j N`** where N ≈ CPU cores on the restore target. Often 5–10× speedup.
- **Sectioned restore** via `--section=pre-data`, `--section=data`, `--section=post-data` — restore schema, then data (fast without indexes), then indexes/FK constraints. 2–3× faster than naive restore.
- **Tune the target during restore**:

  ```sql
  ALTER SYSTEM SET maintenance_work_mem = '2GB';
  ALTER SYSTEM SET max_wal_size = '16GB';
  ALTER SYSTEM SET checkpoint_timeout = '30min';
  ALTER SYSTEM SET synchronous_commit = off;  -- only on dev/empty target
  ALTER SYSTEM SET wal_compression = on;
  SELECT pg_reload_conf();
  ```

  Revert after restore. **Never** turn off `fsync` or `full_page_writes` on a database with real data — a crash will silently corrupt it.

### Level 2: Hundreds of GB — physical backups

`pg_dump` becomes too slow. Production switches to **file-level backups**:

| Tool | Description |
|------|-------------|
| **pgBackRest** | Industry standard. Differential/incremental backups, parallel compression, encryption, S3/GCS/Azure storage |
| **Barman** | Similar feature set, popular in EU/government setups |
| **WAL-G** | Cloud-native, originally from Citus/Yandex |

How they work:

```
┌─────────────────────────────────────────────────────────────────┐
│              Physical Backup + WAL Archiving                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ┌──────────────┐                                              │
│   │  PostgreSQL  │                                              │
│   │  (primary)   │                                              │
│   └──────┬───────┘                                              │
│          │                                                      │
│          ├──► Full base backup (weekly)    ──► S3/storage       │
│          │                                                      │
│          ├──► Incremental backup (daily)   ──► S3/storage       │
│          │                                                      │
│          └──► WAL stream (continuous)      ──► S3/storage       │
│                                                                 │
│   Restore = base backup + replay WAL up to chosen point         │
│   (PITR — Point-in-Time Recovery, second-level granularity)     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

Restore on this scale is **file copy + WAL replay**, not statement-by-statement replay. Orders of magnitude faster than `pg_restore`.

### Level 3: Terabytes + HA — replication-first architecture

Backups are no longer the primary recovery mechanism for availability:

- **Streaming replication** keeps one or more replicas in near-real-time sync. On primary failure, a replica is promoted (orchestrated by **Patroni**, **repmgr**, or **Stolon**).
- **Backups (pgBackRest)** still exist, but for *logical* corruption recovery (someone ran `DELETE FROM users WHERE 1=1`) and disaster recovery to another region.
- **Logical replication** (`pglogical`, native logical replication) is used for cross-version migration, partial database copying, or zero-downtime major upgrades.

### Level 4: Dev/staging copies of prod data

A related but distinct scenario: copying production data into dev/staging *safely*. Two separate problems often confused:

1. **Producing the dump on schedule with reliable storage** — what tools like databasus, pgBackRest, Barman handle.
2. **Sanitizing PII before the dump leaves prod** — what tools like replibyte, pg_anonymize, Percona's pg_dump_anon handle.

```
┌─────────────────────────────────────────────────────────────────┐
│              Sanitized Prod → Dev Pipeline                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   Production DB                                                 │
│        │                                                        │
│        ▼                                                        │
│   ┌──────────────────────┐                                      │
│   │  Anonymization tool  │  • Subset rows (e.g., 1% of users)   │
│   │  (pg_anonymize,      │  • Replace PII with deterministic    │
│   │   replibyte, ...)    │    fakes                             │
│   │                      │  • Preserve referential integrity    │
│   └──────────┬───────────┘                                      │
│              │                                                  │
│              ▼                                                  │
│   ┌──────────────────────┐                                      │
│   │  Backup orchestrator │  • Schedule, compress, encrypt,      │
│   │  (databasus,         │    ship to S3/GDrive/...             │
│   │   pgBackRest, ...)   │  • Notify on success/failure         │
│   └──────────┬───────────┘                                      │
│              │                                                  │
│              ▼                                                  │
│       .dump file (sanitized)                                    │
│              │                                                  │
│              ▼                                                  │
│   Dev / staging DB  (loaded via pg_restore)                     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

In this project, databasus handles step 2 (orchestration) — we don't currently have a sanitization step in front of it, so the local dumps contain the actual database content. The *load* step is the standard `pg_restore` flow described above; what changes between projects is the *generation* pipeline.

### Level 5: Restore automation & monitoring

Production teams don't run `pg_restore` by hand:

- **Automated backup verification** — every night, a job spins up a fresh database, restores yesterday's backup, runs sanity checks. You don't want to discover backup corruption *during* a real incident (Murphy's law).
- **DR drills** — quarterly, the team simulates a disaster and recovers from cold backup against an SLA.
- **Metrics that drive design**: **RPO** (Recovery Point Objective — max acceptable data loss) and **RTO** (Recovery Time Objective — max acceptable downtime). Backup architecture is engineered backwards from these numbers.

---

## Best Practices

### 1. Always know your dump format before restoring

```bash
file backup.dump
pg_restore -l backup.dump | head -20
```

### 2. Use parallel restore for non-trivial dumps

```bash
pg_restore -j $(nproc) ...
```

### 3. Restore directly to PostgreSQL, never through PgBouncer

Port **5555** (direct), not **6432** (PgBouncer).

### 4. Stop application services during restore

Avoids connection limit exhaustion, half-applied migrations, and races.

### 5. Use `--exit-on-error` for the first attempt

Better to fail fast and see the real error than to find out later that half the objects are missing.

### 6. Match client major version to server

Client must be **≥** server version. PostgreSQL 17 server → PostgreSQL 17+ client.

### 7. Verify after restore

```sql
\dn
\dt *.*
SELECT count(*) FROM information_schema.tables
WHERE table_schema NOT IN ('pg_catalog', 'information_schema');
```

### 8. For large dumps, work near the database

Don't `pg_restore` from your laptop over a VPN to a remote production database — every byte streams through your network. Copy the file to the server (or an adjacent jump host) and restore locally.

### 9. Keep `--no-owner --no-privileges` as defaults for cross-environment restores

Production owners and grants rarely match dev/staging. These flags avoid spurious errors.

### 10. Document the dump source

When sharing dumps within a team, record: source database name, anonymization tool + version, date/time, PostgreSQL version, compression method. Saves hours of debugging later.

---

## Related Documentation

- [PgBouncer](pgbouncer.md) — why dumps go to port 5555, not 6432
- [Technologies Overview](index.md)
- [Quick Start Guide](../guides/quickstart.md)
