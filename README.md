# Quality of metadata with MetaQS backend service

The _MetaQS_ service provides an API to calculate different statistics and metrics for the metadata.
It uses Elasticsearch queries to achieve this.

## Feature Documentation

The documentation regarding how quality metrics are determined and the development setup is done can be found
[here](./docs/index.rst).

It can be converted to markdown with the following command:

```bash
sphinx-build -M markdown ./ build_md
```

## Local Setup

MetaQS requires python 3.9 or later and [poetry](https://python-poetry.org/docs/#installation).

Setup details are explained [here](./docs/setup.rst).

## Code Style & Pre-commit hook

The code style is enforced via tools configured in [.pre-commit-config.yaml](./src/.pre-commit-config.yaml) and
[pyproject.toml](./src/pyproject.toml). After setting up the environment (which will install the python
`pre-commit` script) one should install the hook via:

```bash
pre-commit install
```

This will make sure that the commits follow the defined codestyle and the respective CI pipeline step will pass.

## Unit-Tests

Unit-tests are placed [here](./tests).

All tests make use of mocks and static (checked in) resources. Hence, they can run independently of any docker
container or other environment constraints.

## Branching Model

This repository follows the [Git-Flow](https://www.atlassian.com/de/git/tutorials/comparing-workflows/gitflow-workflow) 
branching model.

> - Anything in the main branch is deployable
> - To work on something new, create a descriptively named branch off of dev, ideally add the issue number to the name (
    ie: #3-new-oauth2-scopes)
> - Commit to that branch locally and regularly push your work to the same named branch on the server
> - When you need feedback or help, or you think the branch is ready for merging, open a pull request
> - After someone else has reviewed and signed off on the feature, you can merge it into dev
> - Once it is merged and pushed to `dev`, you can and should deploy immediately to testing
> - Regularly create a pull request from `dev` to `main`
> - Once it is merged and pushed to `main`, you can and should deploy immediately to production

## Definition of Done

- The endpoints work and yield relevant metrics for a correct collection uuid. No additional information is needed. No
  input data is unnecessary.
- The service is resilient against failing code, i.e., the user will never get a "500 Internal Server Error".
  In the worst case, that response is an error message.
- CI Pipeline passes (Unit tests, pre-commit, and build steps)
- Endpoints do not block each other

## CI Pipeline

The pipeline is launched by creating or updating a branch and has to succeed before any pull request can be merged.

It will perform the following steps:

- run pre-commit hooks to validate codestyle and quality
- build python package
- run python unittests
- build docker images
- (on main branch) push docker images to registry.

## Releases & Versioning

- This repository uses [Sem-Ver](https://semver.org/lang/de/).
- New releases are created via the GitHub release interface.
- Release Tags must follow the pattern `v{MAJOR}.{MINOR}.{PATCH}`
- Docker tags will be extracted from the git tags as `{MAJOR}.{MINOR}.{PATCH}`

## Deployment

MetaQS requires nginx and certbot containers. To deploy them together the two docker-compose files
for [dev](./docker-compose.yml) and [prod](./docker-compose.prod.yml) are used. These dockerfiles also
contain the configuration to run MetaQS with a persistent cache via an external postgres container, 
hosted by edu-sharing.

### Nginx Container (optional, official `nginx` image)

Nginx is an HTTP proxy server. The nginx configuration serves FastAPI as a static endpoint, see configuration
[here](./nginx)

### Certbot Container (optional, official `certbot` image)

Certbot takes care of the HTTPS certificate. Using the [certification skript](./init_letsencrypt.sh) you can locally
create the relevant certificate for the domain. You can find more [here](./docs/main.rst).

## Configuration

The application can be configured via environment variables or a `.env` file. See
[`settings.py`](./src/app/.env.example) for the available options.

## Health-Checks

The service provides a `/_ping` endpoint which will respond with a `200 OK` (body: `{"status": "ok"}`) immediately
(within single-digit milliseconds). If the request takes to long, or answers differently, then the service is in an
inconsistent state and should be restarted. This endpoint is also configured in the docker-compose to be used for
health checks of the docker daemon to trigger automated restarts in case of unhealthy containers.

## Testing with `curl`

When the container is running, the endpoints can be tested e.g. with `curl`:

 ```bash
curl --location --request GET 
'https://c106-168.cloud.gwdg.de/api/collections/4940d5da-9b21-4ec0-8824-d16e0409e629/quality-matrix/replication-source'
 ```

See the files [api.py](./src/app/api/api.py) for the API and the response model documentation.
Alternatively visit the [Swagger-UI](http://localhost:8081/docs) of the locally running service.
