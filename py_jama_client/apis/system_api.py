"""
System API module

Example usage:

    >>> from py_jama_client.client import JamaClient
    >>> client = JamaClient(host=HOST, credentials=(USERNAME, PASSWORD))
    >>> system_api = SystemAPI(client)
    >>> domains = system_api.get_cors_domains().data["domains"]
"""

import logging

from py_jama_client.client import JamaClient
from py_jama_client.exceptions import APIException, CoreException
from py_jama_client.response import ClientResponse

py_jama_client_logger = logging.getLogger("py_jama_client")


class SystemAPI:
    client: JamaClient

    def __init__(self, client: JamaClient):
        self.client = client

    def get_cors_domains(
        self,
        *,
        params: dict | None = None,
        **kwargs,
    ) -> ClientResponse:
        """
        Get the CORS domain whitelist. Admin operation; implemented from the
        REST docs and not exercised against a live instance.

        Args:
            params: optional query parameters

        Returns: the client response, whose data is {"domains": [...]}
        """
        return ClientResponse.from_response(
            self._call(self.client.get, "system/settings/corsdomains", params, **kwargs)
        )

    def post_cors_domains(
        self,
        domains: list[str],
        *,
        params: dict | None = None,
        **kwargs,
    ) -> ClientResponse:
        """
        Update the CORS domain whitelist. Admin operation; implemented from
        the REST docs and not exercised against a live instance. The docs say
        "update" and do not say whether the list replaces or extends the
        current whitelist.

        Args:
            domains: The domains to whitelist
            params: optional query parameters

        Returns: the client response; the docs show only meta in the response
        """
        return ClientResponse.from_response(
            self._call(
                self.client.post,
                "system/settings/corsdomains",
                params,
                json={"domains": domains},
                **kwargs,
            )
        )

    def _call(self, send, *args, **kwargs):
        try:
            response = send(*args, **kwargs)
        except CoreException as err:
            py_jama_client_logger.error(err)
            raise APIException(str(err))
        JamaClient.handle_response_status(response)
        return response
