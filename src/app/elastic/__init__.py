"""md
# Overview

The `app.crud` package contains all *CRUD* operations in *MetaQS*.

Core query building blocks against the elasticsearch index reside in the `.elastic` module.

These building blocks are used in the `collections`, `learning_material` and `stats` modules to build concrete queries against the elasticsearch index. They are also used in some other places across the application.

The `.util` module contains few generic helper functions.
"""

from .dsl import (
    abucketsort,
    acomposite,
    afilter,
    amissing,
    aterms,
    qbool,
    qboolor,
    qexists,
    qmatch,
    qnotexists,
    qsimplequerystring,
    qterm,
    qterms,
    qwildcard,
    script,
)
from .fields import Field, FieldType
from .search import Search
