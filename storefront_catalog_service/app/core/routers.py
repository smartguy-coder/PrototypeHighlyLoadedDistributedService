"""
Database routers.

Routes the ``apps.catalog`` Django app to a separate CockroachDB
connection (``catalog``); everything else goes to ``default`` (Postgres).

This is a *partial* multi-database setup: only one app lives elsewhere.
Important consequence - Django does not allow ForeignKey relations across
databases, so ``Dish`` cannot have a ``ForeignKey`` to a model in another
DB. Use a plain UUID/Bigint id field and resolve in code if you need a
cross-DB reference.
"""

from typing import Any


class CatalogRouter:
    """Send the ``catalog`` app to CockroachDB; leave everything else alone."""

    catalog_app_label = "catalog"
    catalog_db = "catalog"
    default_db = "default"

    def db_for_read(self, model: Any, **hints: Any) -> str | None:
        if model._meta.app_label == self.catalog_app_label:  # noqa: SLF001
            return self.catalog_db
        return None

    def db_for_write(self, model: Any, **hints: Any) -> str | None:
        if model._meta.app_label == self.catalog_app_label:  # noqa: SLF001
            return self.catalog_db
        return None

    def allow_relation(self, obj1: Any, obj2: Any, **hints: Any) -> bool | None:
        # Allow relations only inside the same logical DB.
        # _meta is the documented Django API for routers.
        labels = {obj1._meta.app_label, obj2._meta.app_label}  # noqa: SLF001
        if labels == {self.catalog_app_label}:
            return True
        if self.catalog_app_label not in labels:
            return None  # let other routers / Django default decide
        return False  # mixed: forbid cross-DB relations

    def allow_migrate(
        self,
        db: str,
        app_label: str,
        model_name: str | None = None,
        **hints: Any,
    ) -> bool | None:
        if app_label == self.catalog_app_label:
            return db == self.catalog_db
        # Every other app must NOT be migrated into the catalog DB.
        if db == self.catalog_db:
            return False
        return None  # let Django default-handle (i.e. migrate to `default`)
