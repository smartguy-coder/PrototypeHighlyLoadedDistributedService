# Reusable field configurations
from typing import TypedDict


class NullableIndexedOptions(TypedDict):
    null: bool
    blank: bool
    db_index: bool


class NullableUniqueIndexedOptions(NullableIndexedOptions):
    unique: bool


class BooleanDefaultFalseOptions(TypedDict):
    default: bool


NULLABLE_INDEXED: NullableIndexedOptions = {
    "null": True,
    "blank": True,
    "db_index": True,
}

NULLABLE_UNIQUE_INDEXED: NullableUniqueIndexedOptions = {
    "null": True,
    "blank": True,
    "db_index": True,
    "unique": True,
}

BOOLEAN_DEFAULT_FALSE: BooleanDefaultFalseOptions = {
    "default": False,
}
