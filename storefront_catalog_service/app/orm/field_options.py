# Reusable field configurations
from typing import TypedDict


class NullableUniqueIndexedOptions(TypedDict):
    unique: bool
    null: bool
    blank: bool
    db_index: bool


class BooleanDefaultFalseOptions(TypedDict):
    default: bool


NULLABLE_UNIQUE_INDEXED: NullableUniqueIndexedOptions = {
    "unique": True,
    "null": True,
    "blank": True,
    "db_index": True,
}

BOOLEAN_DEFAULT_FALSE: BooleanDefaultFalseOptions = {
    "default": False,
}
