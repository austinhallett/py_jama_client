"""Building request paths from caller-supplied ids."""

from urllib.parse import quote


def segment(value) -> str:
    """`value` as one percent-encoded URL path segment, so an id such as
    "1/../users" cannot change which endpoint is requested."""
    return quote(str(value), safe="")
