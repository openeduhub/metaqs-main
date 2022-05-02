import json
from typing import Union

from fastapi import APIRouter, Depends, Security
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from glom import glom
from httpx import AsyncClient
from pydantic import BaseModel

import app.crud.languagetool as crud_languagetool
import app.crud.learning_material as crud_material
from app.api.auth import authenticated
from app.core.logging import logger
from app.http_client import get_client
from app.models.learning_material import LearningMaterial, LearningMaterialAttribute

router = APIRouter()

_SWAGGER_SPEC_PATH = "/app/languagetool-swagger.json"
_swagger_spec: Union[dict, None] = None

try:
    with open(_SWAGGER_SPEC_PATH, mode="r") as f:
        _swagger_spec = json.load(f)
except FileNotFoundError:
    logger.error("LanguageTool swagger spec not found.")
    _swagger_spec = None


def swagger_spec(path: str = None):
    if _swagger_spec and path:
        return glom(_swagger_spec, path)
    return _swagger_spec


@router.get(
    "/check/random-material",
    tags=[],
)
async def spellcheck_random_material(*, http: AsyncClient = Depends(get_client)):
    material: LearningMaterial = await crud_material.get_random(
        source_fields={
            LearningMaterialAttribute.NODEREF_ID,
            LearningMaterialAttribute.TITLE,
            LearningMaterialAttribute.DESCRIPTION,
        }
    )

    response = {
        "material": jsonable_encoder(
            material, include={"noderef_id", "title", "description"}
        ),
    }

    if material.title:
        response["spellcheck_title"] = await crud_languagetool.check_text(
            http, text=material.title
        )
    if material.description:
        response["spellcheck_description"] = await crud_languagetool.check_text(
            http, text=material.description
        )

    return response


class CheckTextBody(BaseModel):
    language: str
    text: str

    class Config:
        schema_extra = {
            "example": {
                "language": "de-DE",
                "text": "Egal ob Mailand oder Madrid, Hauptsache Italien.",
            }
        }


@router.post(
    "/check",
    tags=["LanguageTool"],
    openapi_extra={
        "description": swagger_spec("paths./check.post.description"),
        "responses": {
            "200": {
                "description": f"Successful Response: {swagger_spec('paths./check.post.responses.200.description')}",
                "content": {
                    "application/json": {
                        "schema": swagger_spec(
                            "paths./check.post.responses.200.schema"
                        ),
                    },
                },
            },
        },
    },
)
async def check_text(*, body: CheckTextBody, http: AsyncClient = Depends(get_client)):
    response = await crud_languagetool.check_text(http, **body.dict())

    return JSONResponse(content=response)


@router.get(
    "/languages",
    tags=["LanguageTool"],
    openapi_extra={
        "description": swagger_spec("paths./languages.get.summary"),
        "responses": {
            "200": {
                "description": f"Successful Response: {swagger_spec('paths./languages.get.responses.200.description')}",
                "content": {
                    "application/json": {
                        "schema": swagger_spec(
                            "paths./languages.get.responses.200.schema"
                        ),
                    },
                },
            },
        },
    },
)
async def list_supported_languages(*, http: AsyncClient = Depends(get_client)):
    languages = await crud_languagetool.list_supported_languages(http)

    return JSONResponse(content=languages)


@router.get(
    "/words",
    tags=["LanguageTool"],
    openapi_extra={
        "description": swagger_spec("paths./words.get.description"),
        "responses": {
            "200": {
                "description": f"Successful Response: {swagger_spec('paths./words.get.responses.200.description')}",
                "content": {
                    "application/json": {
                        "schema": swagger_spec("paths./words.get.responses.200.schema"),
                    },
                },
            },
        },
    },
)
async def list_words_in_dictionaries(*, http: AsyncClient = Depends(get_client)):
    return {"Sorry": f"Not yet implemented! Using client {http}"}


@router.post(
    "/words/add",
    dependencies=[Security(authenticated)],
    tags=["LanguageTool", "Authenticated"],
    openapi_extra={
        "description": swagger_spec("paths./words/add.post.description"),
        "responses": {
            "200": {
                "description": f"Successful Response: {swagger_spec('paths./words/add.post.responses.200.description')}",
                "content": {
                    "application/json": {
                        "schema": swagger_spec(
                            "paths./words/add.post.responses.200.schema"
                        ),
                    },
                },
            },
        },
    },
)
async def add_word_to_dictionary(*, http: AsyncClient = Depends(get_client)):
    return {"Sorry": f"Not yet implemented! Using client {http}"}


@router.post(
    "/words/delete",
    dependencies=[Security(authenticated)],
    tags=["LanguageTool", "Authenticated"],
    openapi_extra={
        "description": swagger_spec("paths./words/delete.post.description"),
        "responses": {
            "200": {
                "description": f"Successful Response: {swagger_spec('paths./words/delete.post.responses.200.description')}",
                "content": {
                    "application/json": {
                        "schema": swagger_spec(
                            "paths./words/delete.post.responses.200.schema"
                        ),
                    },
                },
            },
        },
    },
)
async def delete_word_from_dictionary(*, http: AsyncClient = Depends(get_client)):
    return {"Sorry": f"Not yet implemented! Using client {http}"}
