from dataclasses import dataclass


@dataclass
class ClientResponse:
    meta: dict
    links: dict
    linked: dict
    data: list
