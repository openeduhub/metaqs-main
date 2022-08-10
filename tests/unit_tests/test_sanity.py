"""
Tests only to check, whether everything is alright. If one of these fails, you probably changed a constant or two

"""
import uuid

from app.core.constants import COLLECTION_NAME_TO_ID


def test_COLLECTION_NAME_TO_ID():
    assert len(COLLECTION_NAME_TO_ID.keys()) == 26
    assert all(
        isinstance(uuid.UUID(value), uuid.UUID)
        for value in COLLECTION_NAME_TO_ID.values()
    )
