import asyncio
import uuid

from src.app.crud.collection import get_child_materials_with_missing_attributes
from src.app.crud.learning_material import MissingAttributeFilter
from src.app.models.learning_material import LearningMaterialAttribute


async def test_get_child_materials_with_missing_attributes():
    dummy_uuid = uuid.uuid4()
    dummy_attribute = MissingAttributeFilter(attr=LearningMaterialAttribute.LICENSES.path)
    result = await get_child_materials_with_missing_attributes(dummy_uuid, dummy_attribute, None)
    print(result)
    assert False


if __name__ == '__main__':
    asyncio.run(test_get_child_materials_with_missing_attributes())
