"""
Database configuration for Django with PgBouncer connection pooling.

Architecture:
    Django App -> PgBouncer (6432) -> PostgreSQL (5432)

Environment Variables:
    USE_PGBOUNCER: Set to 'false' when running migrations
    POSTGRES_HOST: Direct PostgreSQL host
    POSTGRES_PORT: Direct PostgreSQL port (default: 5432)
    PGBOUNCER_HOST: PgBouncer host
    PGBOUNCER_PORT: PgBouncer port (default: 6432)
    POSTGRES_DB: Database name
    POSTGRES_USER: Database user
    POSTGRES_PASSWORD: Database password

Important Notes:
    - Migrations should run directly against PostgreSQL (USE_PGBOUNCER=false)
    - Transaction pooling mode doesn't support:
        * CREATE INDEX CONCURRENTLY
        * Advisory locks (pg_advisory_lock)
        * SET statements that persist across queries
    - For these operations, connect directly to PostgreSQL
"""
# todo - testing

from decouple import config

POSTGRES_DB = config("POSTGRES_DB", default="storefront_catalog")
POSTGRES_USER = config("POSTGRES_USER", default="postgres")
POSTGRES_PASSWORD = config("POSTGRES_PASSWORD", default="postgres")
POSTGRES_HOST = config("POSTGRES_HOST", default="postgres_storefront_catalog_service")
POSTGRES_PORT = config("POSTGRES_PORT", default="5432")

PGBOUNCER_HOST = config("PGBOUNCER_HOST", default="pgbouncer")
PGBOUNCER_PORT = config("PGBOUNCER_PORT", default="6432")

USE_PGBOUNCER = config("USE_PGBOUNCER", default=True, cast=bool)

DB_HOST = PGBOUNCER_HOST if USE_PGBOUNCER else POSTGRES_HOST
DB_PORT = PGBOUNCER_PORT if USE_PGBOUNCER else POSTGRES_PORT

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": POSTGRES_DB,
        "USER": POSTGRES_USER,
        "PASSWORD": POSTGRES_PASSWORD,
        "HOST": DB_HOST,
        "PORT": DB_PORT,
        # Let PgBouncer handle connection pooling (CONN_MAX_AGE=0)
        # For direct PostgreSQL, keep connections alive longer
        "CONN_MAX_AGE": 0 if USE_PGBOUNCER else 600,
        "CONN_HEALTH_CHECKS": True,
        "OPTIONS": {
            "connect_timeout": 10,
        },
    },
    # ========================================================================
    # Direct PostgreSQL connection for operations that don't work with PgBouncer
    # ========================================================================
    # Use this for:
    # - Running migrations
    # - CREATE INDEX CONCURRENTLY
    # - Advisory locks
    # - Any operation requiring session-level state
    # use if needed like MyModel.objects.using("direct").all()
    # or connections["direct"].cursor()
    # or DATABASE=direct python manage.py migrate
    # ========================================================================
    "direct": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": POSTGRES_DB,
        "USER": POSTGRES_USER,
        "PASSWORD": POSTGRES_PASSWORD,
        "HOST": POSTGRES_HOST,
        "PORT": POSTGRES_PORT,
        "CONN_MAX_AGE": 600,
        "CONN_HEALTH_CHECKS": True,
        "OPTIONS": {
            "connect_timeout": 10,
        },
    },
    # ========================================================================
    # CockroachDB — distributed database for the catalog (dishes) only
    # ========================================================================
    # Routed via core.routers.CatalogRouter:
    #   * apps.catalog migrations and queries -> this connection
    #   * everything else -> default (Postgres)
    #
    # Run migrations explicitly:
    #   python manage.py migrate --database=catalog
    #
    # Env vars:
    #   COCKROACH_HOST, COCKROACH_PORT (default 26257)
    #   COCKROACH_DB, COCKROACH_USER, COCKROACH_PASSWORD
    #   COCKROACH_SSLMODE (default 'verify-full' for the secure cluster)
    #   COCKROACH_SSLROOTCERT (path to ca.crt; default '/certs/ca.crt' inside the container)
    #
    # Cluster runs in SECURE mode (TLS): Django verifies the server using
    # ca.crt mounted at /certs/ca.crt, then authenticates with username +
    # password inside the encrypted channel.
    # ========================================================================
    "catalog": {
        # replicas?
        "ENGINE": "django_cockroachdb",
        "NAME": config("COCKROACH_DB", default="catalog"),
        "USER": config("COCKROACH_USER", default="django"),
        "PASSWORD": config("COCKROACH_PASSWORD", default=""),
        "HOST": config("COCKROACH_HOST", default="roach1"),
        "PORT": config("COCKROACH_PORT", default="26257"),
        "CONN_MAX_AGE": 600,
        "CONN_HEALTH_CHECKS": True,
        "OPTIONS": {
            "connect_timeout": 10,
            "sslmode": config("COCKROACH_SSLMODE", default="verify-full"),
            "sslrootcert": config("COCKROACH_SSLROOTCERT", default="/certs/ca.crt"),
        },
    },
}

# Don't phone home from a learning project.
DISABLE_COCKROACHDB_TELEMETRY = True

DATABASE_ROUTERS = ["core.routers.CatalogRouter"]
