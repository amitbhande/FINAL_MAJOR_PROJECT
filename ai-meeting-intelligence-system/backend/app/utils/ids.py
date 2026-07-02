from __future__ import annotations

from bson import ObjectId


def oid(s: str) -> ObjectId:
    return ObjectId(s)


def oid_str(x: ObjectId | str) -> str:
    return str(x)

