import io
import json
import os
from typing import Tuple, Any, Dict

from fdk import response
from jsonschema import Draft202012Validator, ValidationError

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCHEMA_DIR = os.path.join(BASE_DIR, "schemas")

SCHEMA_FILES = {
    "1.5": os.path.join(SCHEMA_DIR, "bom-1.5.schema.json"),
    "1.6": os.path.join(SCHEMA_DIR, "bom-1.6.schema.json"),
}


def load_schema(version: str) -> Dict[str, Any]:
    path = SCHEMA_FILES.get(version)
    if not path or not os.path.exists(path):
        raise FileNotFoundError(f"No schema available for specVersion {version}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def detect_version(bom: Dict[str, Any]) -> str:
    v = bom.get("specVersion")
    if isinstance(v, str):
        v = v.strip()
        if v:
            return v
    # fallback
    schema_url = bom.get("$schema")
    if isinstance(schema_url, str):
        if "bom-1.5" in schema_url:
            return "1.5"
        if "bom-1.6" in schema_url:
            return "1.6"

    return ""


def validate_bom(bom: Dict[str, Any]) -> Tuple[bool, str, list]:
    version = detect_version(bom)
    if version not in ("1.5", "1.6"):
        return False, version, [f"Unsupported or missing specVersion; expected 1.5 or 1.6, got '{version or 'none'}'."]

    try:
        schema = load_schema(version)
    except FileNotFoundError as e:
        return False, version, [str(e)]

    try:
        validator = Draft202012Validator(schema)

        errors = []
        for err in sorted(validator.iter_errors(bom), key=lambda e: e.path):
            location = "/" + "/".join([str(p) for p in err.path]) if err.path else "/"
            errors.append({
                "message": err.message,
                "path": location,
                "validator": err.validator,
            })

        return (len(errors) == 0), version, errors
    except Exception as e:
        return False, version, [f"Validation error: {str(e)} - Type: {type(e).__name__}"]


def handler(ctx, data: io.BytesIO):
    try:
        raw = data.read()
        if not raw:
            return response.Response(
                ctx,
                status_code=400,
                response_data=json.dumps({"error": "Empty request body"})
            )

        body = json.loads(raw)

        if isinstance(body, dict) and "sbom" in body:
            bom = body["sbom"]
        else:
            bom = body

        if not isinstance(bom, dict):
            return response.Response(
                ctx,
                status_code=400,
                response_data=json.dumps({"error": "Expected SBOM JSON object"})
            )

        ok, version, errors = validate_bom(bom)

        if ok:
            return response.Response(
                ctx,
                status_code=200,
                response_data=json.dumps({
                    "valid": True,
                    "specVersion": version,
                })
            )
        else:
            return response.Response(
                ctx,
                status_code=400,
                response_data=json.dumps({
                    "valid": False,
                    "specVersion": version or None,
                    "errors": errors[:50]
                })
            )

    except json.JSONDecodeError as e:
        return response.Response(
            ctx,
            status_code=400,
            response_data=json.dumps({"error": f"Invalid JSON: {e}"})
        )
    except Exception as e:
        # last-resort guard to avoid 502
        return response.Response(
            ctx,
            status_code=500,
            response_data=json.dumps({"error": f"Internal error: {str(e)}"})
        )
