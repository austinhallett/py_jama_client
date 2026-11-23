## 1.0.0

### Breaking changes
- The minimum supported httpx is now 0.26 (was 0.24.1).
- Removed the unused `python-jose` and `anyio` dependencies. `python-jose` (and its `ecdsa`, `rsa` and `six` dependencies) are no longer installed; `anyio` still comes in through httpx. Declare them directly if you import them.
- Removed the unused `requests` dependency, so `requests` and `urllib3` are no longer installed transitively. Declare them directly if you import them.
- API methods no longer accept extra positional arguments, which were silently ignored (for example a `params` dict passed positionally to `TagsAPI.get_tags`). They now raise `TypeError`; pass `params` and other options by keyword.
- Importing `py_jama_client` no longer calls `urllib3.disable_warnings()`, so the process-wide suppression of urllib3's `InsecureRequestWarning` is gone. Code that uses requests/urllib3 with `verify=False` will now see these warnings.

### Added
- New API classes:
  - `CommentsAPI`: list, create, get and replies.
  - `CategoriesAPI`: list (with `category_name`/`project_id` filters), create, visibility, delete, and category path delete, copy and move.
  - `UserGroupsAPI`: groups and their members.
  - `SystemAPI`: CORS domains.
- New methods on existing classes:
  - `ItemsAPI`: `get_item_tag`, `get_item_attachments`, `get_item_location`, `get_item_parent`, `get_item_activities`, `get_item_comments`, `delete_item_tag`, `delete_item_synceditem`, `delete_item_attachment`, `put_item_location`, `put_items_tree_location`, `patch_items`, `post_item_duplicate`, `post_item_workflow_transition`, item link operations (list, get, post, put, delete) and item category operations (list, apply, unapply, baselined, versioned).
  - `TestPlansAPI`: plans, test groups, test group test cases, links, tags, lock, versions, comments, attachments and relationships.
  - `TestCyclesAPI`: test group, versions, patch, put and delete.
  - `TestRunsAPI`: list, get, activities, attachments, comments, links, lock, tags, versions, patch, delete and `updatedtestcase`.
  - `FiltersAPI`: `get_filters`, `get_filter` and `get_filter_count`.
  - `ProjectsAPI`: `get_item_types_in_project`, `get_tags_in_project`, project create/update and item type removal.
  - `AttachmentsAPI`: `get_attachment_comments` and `get_file` (`GET /files?url=`).
  - Item type and item type field creation, pick list create/delete, pick list option add/update, and user custom data get/put.
  - `JamaClient.delete_with_body` for DELETE requests with a JSON body.
- New optional parameters, keyword-only and sent only when given:
  - `include` (links to return as full objects in the linked map) on the GET methods whose operations accept it.
  - Query filters on `UsersAPI.get_users`, `FiltersAPI.get_filters` and `get_filter_results`, `BaselinesAPI.get_baselines` and `get_baseline_versioned_items`, `ItemsAPI.get_items`, `AbstractItemsAPI.get_abstract_items`, `TestPlansAPI.get_test_plans`, `UserGroupsAPI.get_user_groups`, `RelationshipsAPI.get_relationship_type` and `TestRunsAPI.get_test_runs`.
  - `root_comments_only` on the comment listings.
  - `ActivitiesAPI.get_admin_activities`: `object_type` (integer type code) and `object_id`, sent as `objectType`/`objectId`. They must be given together and cannot be combined with `project_id` (`ValueError`).
  - `ItemsAPI.put_item`: `set_global_id_manually` and `global_id`; `ItemsAPI.patch_item`: `return_item`.
  - Request-body fields on `ItemsAPI.post_item_duplicate`, `TestPlansAPI.post_test_plan` and `put_test_plan`, `TestCyclesAPI.put_test_cycle`, and `UsersAPI.post_user` and `put_user`.
  - `ItemsAPI.put_item_lock` now accepts `params` and `**kwargs`.

### Changed
- Requests:
  - Request bodies are sent as JSON (`json=`) instead of `data=json.dumps(...)`, removing httpx's `DeprecationWarning` for `data=` with a string. With httpx 0.28 and later, a NaN or infinite float in a body now raises `ValueError` before the request is sent.
  - `ProjectsAPI.put_project_item_type`, `TestRunsAPI.put_test_run` (string or bytes body) and `ItemsAPI.patch_item` merge their default `Content-Type`/`Accept` with caller `headers` case-insensitively, so a caller's header replaces the default instead of being sent alongside it.
  - `BaselinesAPI.put_baseline`: `baseline_status_pick_list_option` is optional (default `None`, sent as null, which the server accepts).
  - `CommentsAPI.post_comment`: a reply (`in_reply_to`) may pass `location=None` to take its parent comment's location.
  - Ids in request paths are percent-encoded, so a value such as `"1/../users/5"` stays one path segment instead of changing which endpoint is requested.
- Authentication:
  - The OAuth token request uses the client's session (`session_class`), so it shares the session's TLS settings, timeout (previously httpx's 5s default), connection pool, cookies and any custom transport.
  - If fetching the initial OAuth token fails in `JamaClient.__init__`, the session is closed before the exception is raised.
- Errors:
  - Transport failures (timeouts, refused or dropped connections) in `JamaClient.get`, `post`, `put`, `patch`, `delete` and `delete_with_body` are raised as `CoreException`, with the httpx error as its `__cause__`, so API methods raise `APIException` instead of a raw httpx exception.
- Type hints:
  - `ItemsAPI.post_item` `global_id` is `str | None` (Global IDs are strings).
  - `TestRunsAPI.put_test_run` `data` also accepts `str` and `bytes`.
  - `ItemsAPI.patch_item` is overloaded, so `return_item=True` is typed as returning `ClientResponse` and otherwise `int`.
  - The `AbstractItemsAPI.get_abstract_items` filters accept a single value as well as a list.

### Fixed
- Wrong requests:
  - `FiltersAPI.get_filter_results` sent an empty `project=` when no project was given.
  - `AttachmentsAPI.get_attachment_file` requested `files?url=<id>`; it now requests `GET attachments/{id}/file`.
  - `TestRunsAPI.put_test_run` sent its body as form data, which the server rejected. A dict body is now sent as JSON, a JSON string or bytes body is still sent as is, `ValueError` is raised when no body is given, and `params` are passed through.
  - `ActivitiesAPI.get_activities` sent `objectType` for the `event_type` and `item_type` filters and never sent `object_type` on its own. It now sends `eventType`, `objectType` and `itemType`, and sends the delete filter as `deleteEvents`.
  - `JamaClient.get_available_endpoints` sent Basic credentials on an OAuth client; it now sends the bearer token.
- Caller arguments changed or ignored:
  - Methods no longer write into the caller's `params`: `ActivitiesAPI.get_activities` and `get_admin_activities`, `AbstractItemsAPI.get_abstract_items` and `get_abstract_item_versions`, `AttachmentsAPI.get_attachment_file`, `FiltersAPI.get_filter_results`, `ItemsAPI.post_item`, and the `get_relationships`, `get_baselines`, `get_tags`, `get_releases` and `get_items` list methods.
  - `JamaClient` no longer writes the OAuth `Authorization` header into the caller's own `headers` dict, so a reused dict no longer carries the token.
  - Many API methods dropped `**kwargs` (such as `headers` or `timeout`). Fixed in `FiltersAPI.get_filter_results`, `get_items`, `get_item_version`, `get_item_versions`, `get_item_tags`, `delete_item`, `get_relationships` (on every page), `get_releases`, `get_pick_lists` and the single-object GETs for abstract item versions, item types, pick lists and options, relationships, relationship types, releases and tags.
  - `RelationshipsAPI.get_relationship_types` ignored `params`.
  - The `include` helper raised `TypeError` when the caller's `params` already held `include` as `None` or a single value.
  - `ItemsAPI.patch_item` raised `TypeError` when called with `headers=None`.
- Responses and paging:
  - `JamaClient.get_all` dropped a page's data when the response had no `meta.pageInfo`.
  - `JamaClient.get_all` skipped rows when the server returned fewer rows than requested per page; it now advances by the rows returned.
  - `JamaClient.handle_response_status` raised `AttributeError` on a 4xx response whose JSON body had no `meta`; the mapped exception is raised instead.
  - `BaselinesAPI.delete_baseline` returned `None` and ignored error statuses; it now returns the status code and raises on error statuses.

### Tests
- The test suite replays HTTP cassettes stored in `test/cassettes/` and needs no Jama instance or credentials. CI runs it with a 100% coverage gate on `py_jama_client/apis`.

## 0.0.7
Added some helpful documentation to the client class to aleviate UNSAFE LEGACY RENEGOTIATION errors when connecting to Jamacloud instance. For more information, please see [RFC 5746 secure renegotiation](https://www.rfc-editor.org/rfc/rfc5746).

TL;DR
A change in the TLS standard requires support in both the client and server. When using the Jama client to make a request to JamaCloud on a client using OpenSSL v3, if you are attempting to connect to a server which does not support secure renegotation, you will receive the following error:

> UnauthorizedTokenException: Unable to fetch token: [SSL: UNSAFE_LEGACY_RENEGOTIATION_DISABLED] unsafe legacy renegotiation disabled (_ssl.c:1006)

The solution is to provide a new SSLContext which allows for unsafe legacy renegotitation:

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
