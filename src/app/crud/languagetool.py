from httpx import AsyncClient

from src.app.core.config import LANGUAGETOOL_ENABLED_CATEGORIES, LANGUAGETOOL_URL


async def check_text(http: AsyncClient, text: str, language: str = "de-DE") -> dict:
    response = await http.post(
        f"{LANGUAGETOOL_URL}/check",
        data={
            "text": text,
            "language": language,
            "enabledCategories": ",".join(LANGUAGETOOL_ENABLED_CATEGORIES),
            "enabledOnly": "true",
        },
    )

    return response.json()


async def list_supported_languages(http: AsyncClient) -> list:
    response = await http.get(f"{LANGUAGETOOL_URL}/languages")

    return response.json()
