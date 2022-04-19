"""md
# Overview

!!! note "Postgres connector library"

    This package uses SQLAlchemy exclusively to connect to postgres.

The `app.analytics` package contains all logic/operations related to running analytics in postgres.

The `analytics.run()` function handles import and subsequent analysis of the current state of the elasticsearch index.

The `spellcheck.run()` function implements the spellcheck functionality.

The function iterates over a list of records from a postgres table and sends each record's text to the languagetool API.
If the API returns a match, i.e. a spellcheck error was found, that error is stored in postgres with reference to the related elastic resource.

All communication with the rpc server running inside the dbt container is located in the `rpc_client.py` module.
"""
