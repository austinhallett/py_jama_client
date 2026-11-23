# Contributors Guide

## Adding New Endpoints

If you would like to contribute additional endpoints please do the following:

1) Write the endpoint code in the appropriate API module (see other endpoint functions for desired syntax).
2) Write tests that show the endpoint works as expected, with a cassette for each (see below).
3) Submit a pull request.

## Running tests

```shell
pip install -e ".[test]"
pytest
```

The tests need no Jama instance and no credentials. Every test that uses the
`get_test_jama_client` fixture replays the HTTP exchanges stored in its
cassette, `test/cassettes/<test module>/<test name>.json` (parametrized tests
add `[<parameter id>]`, with characters other than letters, digits, `_`, `.`
and `-` replaced by `_`). A request the cassette does not hold, or a cassette
interaction the test never requests, fails the test. CI runs the suite with a
100% coverage gate on `py_jama_client/apis`.

## Cassettes

A cassette is a JSON file:

- `version`: the cassette format version (1)
- `test`: the test's node id
- `source`: where the exchanges come from: `live` (a Jama instance), `docs`
  (examples in the Jama REST API documentation) or `synthetic` (written by hand)
- `recorded`, `run_id`: when the file was produced
- `interactions`: the exchanges, in order. Each has a `request` (`method`,
  `path`, `query` as a list of `[name, value]` pairs, and a `body` unless it is
  empty) and a `response` (`status`, `headers` as a list of `[name, value]`
  pairs without `content-encoding`, `content-length` or `transfer-encoding`,
  and a `body` unless it is empty). A body is `{"json": ...}`,
  `{"text": ...}`, `{"base64": ...}` or, for uploads, `{"multipart": ...}`.

The test's requests must match the interactions one by one, in order, on
method, path, query (pairs compared sorted by name) and body; the host is
ignored, and the OAuth token request is answered without an entry. Custom
field keys (`name$123`) are dropped from the test's request before matching,
so a cassette request must not contain them. `save_cassette` in
`test/jama_cassette.py` writes the format; pass `source=` explicitly, since it
defaults to `live`. For a new endpoint, write its cassette from the API
documentation (`source: docs`) or by hand (`source: synthetic`), following the
existing files.

Values the tests share (object ids such as the project, items and test plans,
plus the current user) are in `test/cassettes/_fixtures.json` and reach tests
through fixtures such as `real_project`.

`test/test_cassette_hygiene.py` scans every file under `test/` for instance
data: e-mail addresses, hosts outside `example.com` and `.invalid`, custom
field names, bearer tokens and base64 bodies that hide any of these. In `live`
cassettes it also checks that object names, ids and users are generic, except
for the objects named in `_fixtures.json`.
