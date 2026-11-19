"""In-memory stand-in for the parts of the Drive API v3 the client uses.

Served through ``httpx.MockTransport`` so the real client code (pagination, headers, error
mapping, retries) runs unchanged without network access.
"""

import re
from dataclasses import dataclass

import httpx

FOLDER = "application/vnd.google-apps.folder"
SHORTCUT = "application/vnd.google-apps.shortcut"
API_KEY = "test-api-key"


@dataclass
class Item:
    id: str
    name: str
    mime_type: str
    parent: str | None
    content: bytes = b""
    report_size: bool = True
    shortcut_target: tuple[str, str] | None = None
    trashed: bool = False


def drive_error(status: int, reason: str, headers: dict[str, str] | None = None) -> httpx.Response:
    body = {"error": {"code": status, "message": reason, "errors": [{"reason": reason}]}}
    return httpx.Response(status, json=body, headers=headers)


class FakeDrive:
    def __init__(self) -> None:
        self.items: dict[str, Item] = {}
        self.requests: list[httpx.Request] = []
        self._scripted: list[httpx.Response | Exception] = []

    # --- arranging ---------------------------------------------------------------------

    def add_folder(self, id: str, name: str, parent: str | None = None) -> None:
        self.items[id] = Item(id, name, FOLDER, parent)

    def add_file(
        self,
        id: str,
        name: str,
        mime_type: str,
        parent: str,
        content: bytes = b"content",
        *,
        report_size: bool = True,
    ) -> None:
        self.items[id] = Item(id, name, mime_type, parent, content, report_size)

    def add_shortcut(
        self, id: str, name: str, parent: str, target_id: str, target_mime: str
    ) -> None:
        self.items[id] = Item(id, name, SHORTCUT, parent, shortcut_target=(target_id, target_mime))

    def then_respond(self, *responses: httpx.Response | Exception) -> None:
        """Serve these responses (or raise these errors) before behaving normally again."""
        self._scripted.extend(responses)

    def client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(transport=httpx.MockTransport(self._handle))

    # --- serving -----------------------------------------------------------------------

    def _handle(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        if self._scripted:
            scripted = self._scripted.pop(0)
            if isinstance(scripted, Exception):
                raise scripted
            return scripted
        if request.headers.get("X-Goog-Api-Key") != API_KEY:
            return drive_error(400, "API_KEY_INVALID")
        if request.url.path == "/drive/v3/files":
            return self._list(request)
        match = re.fullmatch(r"/drive/v3/files/([^/]+)", request.url.path)
        item = self.items.get(match.group(1)) if match else None
        if item is None:
            return drive_error(404, "notFound")
        if request.url.params.get("alt") == "media":
            return httpx.Response(200, content=item.content)
        return httpx.Response(200, json=self._resource(item))

    def _list(self, request: httpx.Request) -> httpx.Response:
        match = re.match(r"'([^']+)' in parents", request.url.params["q"])
        assert match, "the client must always filter by parent"
        children = sorted(
            (item for item in self.items.values() if item.parent == match.group(1)),
            key=lambda item: (item.mime_type != FOLDER, item.name),
        )
        size = int(request.url.params["pageSize"])
        start = int(request.url.params.get("pageToken", "0"))
        body: dict[str, object] = {
            "files": [self._resource(i) for i in children[start : start + size]]
        }
        if start + size < len(children):
            body["nextPageToken"] = str(start + size)
        return httpx.Response(200, json=body)

    @staticmethod
    def _resource(item: Item) -> dict[str, object]:
        resource: dict[str, object] = {
            "id": item.id,
            "name": item.name,
            "mimeType": item.mime_type,
            "modifiedTime": "2026-11-01T10:00:00.000Z",
        }
        if item.mime_type not in {FOLDER, SHORTCUT} and item.report_size:
            resource["size"] = str(len(item.content))
        if item.trashed:
            resource["trashed"] = True
        if item.shortcut_target:
            target_id, target_mime = item.shortcut_target
            resource["shortcutDetails"] = {"targetId": target_id, "targetMimeType": target_mime}
        return resource
