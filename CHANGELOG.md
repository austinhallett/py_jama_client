## 0.0.7
Added some helpful documentation to the client class to aleviate UNSAFE LEGACY RENEGOTIATION errors when connecting to Jamacloud instance. For more information, please see [RFC 5746 secure renegotiation](https://www.rfc-editor.org/rfc/rfc5746).

TL;DR
A change in the TLS standard requires support in both the client and server. When using the Jama client to make a request to JamaCloud on a client using OpenSSL v3, if you are attempting to connect to a server which does not support secure renegotation, you will receive the following error:

> UnauthorizedTokenException: Unable to fetch token: [SSL: UNSAFE_LEGACY_RENEGOTIATION_DISABLED] unsafe legacy renegotiation disabled (_ssl.c:1006)

The solution is to provide a new SSLContext which allows for unsafe legacy renegotitation, as seen in the  `get_test_jama_client` fixture in `./test/conftest.py`

```python
import ssl

def get_jama_client():

    ssl_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
    ssl_context.options |= 0x4  # OP_LEGACY_SERVER_CONNECT
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    client = JamaClient(
        host=os.getenv("HOST"),
        credentials=(os.getenv("CLIENT_ID"), os.getenv("CLIENT_SECRET")),
        verify=ssl_context,
        oauth=True,
    )

    return client
```
