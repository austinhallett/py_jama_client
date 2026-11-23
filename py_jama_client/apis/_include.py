"""Helpers that add optional query parameters (such as `include`) to a
caller's params without modifying it."""

from collections.abc import Iterable


def with_include(
    params: dict | None, include: Iterable[str] | str | None
) -> dict | None:
    """`params` with `include` added (links to return as full objects in the
    response's linked map); `params` unchanged when `include` is None. Values
    already in `params["include"]` are kept. The caller's dict is never
    modified."""
    if include is None:
        return params
    params = dict(params or {})
    existing = params.get("include", [])
    params["include"] = _as_list(existing) + _as_list(include)
    return params


def with_query(params: dict | None, **values) -> dict | None:
    """`params` with each of `values` that is not None added under its own
    name; an argument wins over the same key in `params`. `params` unchanged
    when every value is None. The caller's dict is never modified."""
    given = {key: value for key, value in values.items() if value is not None}
    if not given:
        return params
    return {**(params or {}), **given}


def _as_list(value) -> list:
    if value is None:
        return []
    if isinstance(value, str) or not isinstance(value, Iterable):
        return [value]
    return list(value)
