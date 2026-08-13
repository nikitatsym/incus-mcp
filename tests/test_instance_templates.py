"""Instance file templates: raw body plus the required `?path=` query param.

`instanceMetadataTemplatesPost` / `...Delete` answer 400 "missing path
argument" without `path`, and the POST copies the request body verbatim into
the template file - a JSON envelope would land inside the template.
"""

from __future__ import annotations

from incus_mcp.tools import delete, write

_TEMPLATE = "{{ container.name }}\n"


def _empty_sync():
    return {"type": "sync", "status": "Success", "status_code": 200, "metadata": {}}


def test_create_template_sends_raw_content_under_path(stub_client, respx_mock):
    route = respx_mock.post("/1.0/instances/i0/metadata/templates").respond(
        200, json=_empty_sync(),
    )
    write.create_instance_template(
        name="i0", template="hostname.tpl", content=_TEMPLATE, project="p",
    )
    request = route.calls[0].request
    assert "path=hostname.tpl" in str(request.url)
    assert "project=p" in str(request.url)
    assert request.content == _TEMPLATE.encode()


def test_delete_template_sends_path(stub_client, respx_mock):
    route = respx_mock.delete("/1.0/instances/i0/metadata/templates").respond(
        200, json=_empty_sync(),
    )
    delete.delete_instance_template(name="i0", template="hostname.tpl")
    assert "path=hostname.tpl" in str(route.calls[0].request.url)
