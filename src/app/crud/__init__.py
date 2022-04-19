"""md
# Overview

The `app.crud` package contains all *CRUD* operations in *MetaQS*.

Queries are assembled using the [elasticsearch Query DSL python client library](https://elasticsearch-dsl.readthedocs.io/en/latest/index.html).

Core query building blocks against the elasticsearch index reside in the `elastic.py` module.

These building blocks are used in the `collections.py`, `learning_material.py` and `stats.py` modules to build concrete queries against the elasticsearch index. They are also used in some other places across the application.

The `util.py` module contains few generic helper functions.
"""

from .collection import MissingAttributeFilter as MissingCollectionAttributeFilter
from .collection import MissingCollectionField
from .learning_material import MissingAttributeFilter as MissingMaterialAttributeFilter
from .learning_material import MissingMaterialField
from .util import OrderByDirection, OrderByParams
