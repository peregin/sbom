import io
import json
from func import handler

class DummyURL:
    def __init__(self, path="/sbom/validate"):
        self.path = path

class DummyCtx:
    def __init__(self, method="POST", path="/sbom/validate"):
        self._method = method
        self._url = DummyURL(path)
        self.response_headers = {}
        self.response_status_code = 200

    def RequestMethod(self):
        return self._method

    def RequestURL(self):
        return self._url

    def SetResponseHeaders(self, headers, status_code):
        self.response_headers = headers
        self.response_status_code = status_code

def make_data(obj) -> io.BytesIO:
    return io.BytesIO(json.dumps(obj).encode("utf-8"))

def parse_response(resp):
    body_data = getattr(resp, 'body', lambda: None)() or getattr(resp, 'response_data', None)
    if isinstance(body_data, (bytes, bytearray)):
        body_data = body_data.decode()
    return resp.status_code, json.loads(body_data)

def test_handler_valid_bom_15():
    ctx = DummyCtx()
    bom = {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "version": 1,
        "metadata": {
            "timestamp": "2024-01-01T00:00:00Z",
            "tools": [{"name": "unit-test-tool"}]
        }
    }
    resp = handler(ctx, make_data(bom))
    status, body = parse_response(resp)
    assert status == 200
    assert body["valid"] is True
    assert body["specVersion"] == "1.5"

def test_handler_invalid_json():
    ctx = DummyCtx()
    bad_data = io.BytesIO(b"{not-json")
    resp = handler(ctx, bad_data)
    status, body = parse_response(resp)
    assert status == 400
    assert "Invalid JSON" in body["error"]

def test_handler_invalid_bom():
    ctx = DummyCtx()
    invalid_bom = {"bomFormat": "CycloneDX", "specVersion": "1.7", "version": 1}
    resp = handler(ctx, make_data(invalid_bom))
    status, body = parse_response(resp)
    assert status == 400
    assert body["valid"] is False
    assert body["specVersion"] == "1.7"
    assert "errors" in body
    assert len(body["errors"]) > 0, "Expected validation errors in response"

def test_handler_missing_body():
    ctx = DummyCtx()
    resp = handler(ctx, io.BytesIO(b""))
    status, body = parse_response(resp)
    assert status == 400
    assert "Empty request body" in body["error"]
