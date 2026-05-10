from decimal import Decimal
from typing import ClassVar

from django.core.validators import MinValueValidator
from django.db import models

from orm import CreatedAtUpdatedAtMixin, UUID7PrimaryKeyMixin


class Dish(UUID7PrimaryKeyMixin, CreatedAtUpdatedAtMixin):
    """
    Storefront catalog item — a dish (1:1 with frontend `MenuItem`).

    Distributed-database design (CockroachDB):
        * UUIDv7 PK (provided by ``UUID7PrimaryKeyMixin``) — time-ordered
          enough for natural pagination, but still spread across the keyspace
          (no hot range like BIGSERIAL).
        * `restaurant_id` is a plain UUID, NOT a ForeignKey: Restaurant
          lives in Postgres (`default` DB), and CockroachDB cannot enforce
          cross-cluster FKs. Referential integrity is the application's job.
        * Indexes are deliberately lean — every secondary index is
          replicated and synchronously updated on each write.
    """

    restaurant_id = models.UUIDField("restaurant id", db_index=True)

    name = models.CharField("name", max_length=200)
    description = models.TextField("description", blank=True, default="")

    price = models.DecimalField(
        "price",
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )

    # Free-form per-restaurant category ("Pizza", "Sashimi", "Curry", ...).
    # Not a choices enum — restaurants invent their own labels.
    category = models.CharField("category", max_length=64)

    image_url = models.URLField("image url", max_length=500, blank=True, default="")

    is_available = models.BooleanField("is available", default=True)

    class Meta:
        verbose_name = "dish"
        verbose_name_plural = "dishes"
        # Hottest query: "menu of restaurant X, only available items".
        indexes: ClassVar[list[models.Index]] = [
            models.Index(fields=["restaurant_id", "is_available"]),
        ]
        constraints: ClassVar[list[models.BaseConstraint]] = [
            models.CheckConstraint(
                condition=models.Q(price__gte=0),
                name="dish_price_non_negative",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.name} (${self.price})"
