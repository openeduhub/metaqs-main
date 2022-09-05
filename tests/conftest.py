import contextlib
import os
from pathlib import Path
from unittest import mock


@contextlib.contextmanager
def elastic_search_mock(resource: str):
    """
    Mock the execute call of the elasticsearch-dsl Search class package.

    Instead of issuing a http request to elastic, the build request will be validated for equality against a checked in
    request, the result of search.execute() will be constructed from the checked in response json file.

    :param resource: The key (filename) that identifies an (optional) request and a response json in the test/resources
                     directory.
    """
    import json

    resource_path = Path(__file__).parent / "resources"

    # request is optional. if no request is provided, the search will simply
    # be mocked to return the respective response.
    if os.path.exists(resource_path / f"{resource}-request.json"):
        with open(resource_path / f"{resource}-request.json", "r") as request:
            request = json.load(request)
    else:
        request = None

    with open(resource_path / f"{resource}-response.json", "r") as response:
        response = json.load(response)

    def execute_mock(self, ignore_cache=False):  # noqa
        assert (
            request is not None and self.to_dict() == request
        ), "Executed request did not match expected request"
        # just use the dictionary deserialized from the resource file and pass it through the original
        # elasticsearch_dsl machinery. I.e. search.execute() should behave __exactly__ as if the result was
        # received via a http call.
        self._response = self._response_class(self, response)
        return self._response

    with mock.patch("elasticsearch_dsl.search.Search.execute", execute_mock):
        yield