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
}
