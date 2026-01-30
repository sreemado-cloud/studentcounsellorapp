"""
Input validation helpers for security (C4: ObjectId validation).
Raises HTTP 400 on invalid input to prevent NoSQL injection and info leakage.
"""
from bson import ObjectId
from fastapi import HTTPException


def validate_object_id(id_str: str, param_name: str = "id") -> ObjectId:
    """
    Validate and convert a string to ObjectId.
    Raises HTTP 400 if invalid (prevents NoSQL injection, avoids 500 leaks).
    """
    if not id_str or not isinstance(id_str, str):
        raise HTTPException(status_code=400, detail=f"Invalid {param_name}: expected non-empty string")
    id_str = id_str.strip()
    if not ObjectId.is_valid(id_str):
        raise HTTPException(status_code=400, detail=f"Invalid {param_name} format")
    return ObjectId(id_str)
