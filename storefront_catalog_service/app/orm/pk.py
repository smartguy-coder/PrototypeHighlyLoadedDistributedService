import uuid

from django.db import models

import uuid_utils


def uuid7() -> uuid.UUID:
    """
    UUIDv7 (time-ordered) returned as a stdlib ``uuid.UUID``.

    ``uuid_utils.uuid7()`` returns a Rust-backed ``uuid_utils.UUID`` whose
    string repr trips Django admin's UUID validation (smart-quote-looking
    characters surrounding the value reach ``UUIDField.to_python`` and the
    parse fails). Round-tripping via the integer representation gives us
    the same 128 bits in a class everyone — admin, DRF, forms — understands.
    """
    return uuid.UUID(int=uuid_utils.uuid7().int)


class UUID7PrimaryKeyMixin(models.Model):
    """
    Abstract mixin providing a UUIDv7 primary key.

    Distributed-database design (CockroachDB):
        * UUIDv7 PK — time-ordered enough for natural pagination, but still
          spread across the keyspace (no hot range like BIGSERIAL).

    MRO note: place this mixin first in the inheritance list so its ``id``
    field wins over any other abstract base that might declare its own PK.
    """

    id = models.UUIDField(primary_key=True, default=uuid7, editable=False)

    class Meta:
        abstract = True
