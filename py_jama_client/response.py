__all__ = ["ClientResponse"]

from dataclasses import dataclass

from httpx import Response


@dataclass
class ClientResponse:
    meta: dict
    links: dict
    linked: dict
    data: list

    @classmethod
    def from_response(cls, response: Response):
        """
        Parse a response from the Jama API into a ClientResponse object.

        Args:
            response (httpx.Response): The response from the Jama API.

        Returns:
            ClientResponse: A ClientResponse object.
        """
        response_json: dict = response.json()

        return ClientResponse(
            meta=response_json.get("meta", {}),
            links=response_json.get("links", {}),
            linked=response_json.get("linked", {}),
            data=response_json.get("data", {}),
        )

    def to_dict(self):
        """
        Convert client response object to dictionary.
        """
        return {
            "meta": self.meta,
            "links": self.links,
            "linked": self.linked,
            "data": self.data,
        }

    def __add__(self, other):
        self.meta.update(other.meta)
        self.links.update(other.links)
        self.linked.update(other.linked)
        self.data += other.data
        return self
