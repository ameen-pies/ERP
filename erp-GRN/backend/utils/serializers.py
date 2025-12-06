from __future__ import annotations

from bson import ObjectId


def serialize_doc(doc: dict) -> dict:
    """Convert ObjectId instances to strings for JSON-friendly output."""
    if not isinstance(doc, dict):
        return doc

    result: dict = {}
    for key, value in doc.items():
        if isinstance(value, ObjectId):
            result[key] = str(value)
        elif isinstance(value, list):
            result[key] = [
                serialize_doc(item) if isinstance(item, dict) else item for item in value
            ]
        elif isinstance(value, dict):
            result[key] = serialize_doc(value)
        else:
            result[key] = value
    return result

