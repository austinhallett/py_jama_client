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
            response_json.get("meta", {}),
            response_json.get("links", {}),
            response_json.get("linked", {}),
            response_json.get("data", {}),
        )
