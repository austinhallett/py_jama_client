# Contributors Guide

## Adding New Endpoints

If you would like to contribute additional endpoint please do the following:

1) Write the endpoint code in the appropriate API module (see other endpoint functions for desired syntax).
2) Write a tests to show the endpoint works like expected
3) Submit a pull request

## Running tests

Unit tests are run against a live Jama instance. To authenticate with the
instance, credentials are pulled from the environment.

At a minimum, you must define the following environment variables:

- `HOST`: the host url to a live Jama instance
- `CLIENT_ID`: a username or client_id for a user with API access on the Jama instance
- `CLIENT_SECRET`: the password or client_secret associated with the `CLIENT_ID`
- `OAUTH`: (optional, default False) if `CLIENT_ID` and `CLIENT_SECRET` are for an API key, set oauth to `true`

Optionally, the following environment variables can be defined. For each of the
respective types, if an ID is not specified, all the instances of the item will
be queried and the first one will be used.

- `ABSTRACT_ITEM_ID`
- `ABSTRACT_ITEM_VERSION`
- `BASELINE_ID`
- `ITEM_TYPE_ID`
- `PROJECT_ID`
- `RELATIONSHIP_ID`
- `RELATIONSHIP_TYPE_ID`
- `RELEASE_ID`
- `TAG_ID`

All of these environment variables can be placed in a _`.env`_ file to
be loaded automatically at runtime. This is especially useful for running tests
from an IDE.
