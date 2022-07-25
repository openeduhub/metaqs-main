def create_examples(data: dict) -> dict:
    return {key: {"value": value} for key, value in data.items()}
