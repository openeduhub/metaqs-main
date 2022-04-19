from slugify import slugify as python_slugify


def slugify(text, **kwargs):
    return python_slugify(text, **kwargs)
