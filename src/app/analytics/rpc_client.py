from functools import partial

import httpx as http
import polling2
from jsonrpcclient import Ok, parse, request_uuid

from app.core.config import DBT_URL
from app.core.logging import logger

_dbt_spellcheck_path = "models/spellcheck"


def run_analytics():
    cli_command = f"run --exclude path:{_dbt_spellcheck_path}"
    return _send_rpc(method="cli_args", params={"cli": cli_command})


def run_spellcheck():
    cli_command = f"run --select path:{_dbt_spellcheck_path}"
    return _send_rpc(method="cli_args", params={"cli": cli_command})


def poll(request_token: str):
    return polling2.poll(
        partial(
            _send_rpc,
            method="poll",
            params={"request_token": request_token, "logs": False},
        ),
        check_success=lambda result: result.get("state") == "success",
        step=30,
        max_tries=10,
    )


def _send_rpc(method: str, params: dict) -> dict:
    response = http.post(DBT_URL, json=request_uuid(method, params=params))
    parsed = parse(response.json())
    if not isinstance(parsed, Ok):
        logger.error(f"Error from dbt server: {parsed.message}")
        raise Exception(f"Error from dbt server: {parsed.message}")

    return parsed.result
