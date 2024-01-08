from dataclasses import dataclass
from httpx import Response


@dataclass
class ClientResponse:
    meta: dict
    links: dict
    linked: dict
    data: list

    @classmethod
    def parse(cls, response: Response):
        response_json: dict = response.json()

        return ClientResponse(
            meta=response_json.get("meta", {}),
            links=response_json.get("links", {}),
            linked=response_json.get("linked", {}),
            data=response_json.get("data", {}),
        )
