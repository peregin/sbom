import io
import json
import os
from typing import Tuple, Any, Dict

from fdk import response

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


from functools import lru_cache
from jsonschema import Draft7Validator, Validator, SchemaError, ValidationError

@lru_cache(maxsize=4)
def get_validator(version: str) -> Validator:
    """
    Load and cache the JSON Schema validator for a given CycloneDX version.
    Raises FileNotFoundError if schema is missing.
    """
    schema = load_schema(version)
    try:
        Draft7Validator.check_schema(schema)
    except SchemaError as e:
        # This makes it obvious the schema is broken, not the SBOM
        schema_path = "/" + "/".join(str(p) for p in e.absolute_schema_path) if e.absolute_schema_path else "/"
        error_details = f"message: {e.message}, schema_path: {schema_path}"
        if e.validator:
            error_details += f", validator: {e.validator}"
        raise RuntimeError(f"Invalid schema for specVersion {version} ({error_details})") from e
    return Draft7Validator(schema)


def _format_validation_error(err: ValidationError) -> Dict[str, Any]:
    """
    Turn a jsonschema.ValidationError into a user-friendly, debuggable dict.
    """
    # JSON instance path where it failed
    instance_path = "/" + "/".join(str(p) for p in err.path) if err.path else "/"

    # JSON Schema path (which rule failed)
    schema_path = "/" + "/".join(str(p) for p in err.schema_path) if err.schema_path else "/"

    # Optional nested context (one level for clarity)
    contexts = []
    for ctx in err.context:
        ctx_path = "/" + "/".join(str(p) for p in ctx.path) if ctx.path else "/"
        contexts.append({
            "message": ctx.message,
            "path": ctx_path,
            "schema_path": "/" + "/".join(str(p) for p in ctx.schema_path) if ctx.schema_path else "/",
        })

    return {
        "message": err.message,
        "path": instance_path,
        "schema_path": schema_path,
        "validator": err.validator,
        "validator_value": err.validator_value,
        "context": contexts or None,
    }


def validate_bom(bom: Dict[str, Any]) -> Tuple[bool, str, list]:
    """
    Validate a CycloneDX BOM against the 1.5 / 1.6 schema.

    Returns:
        (is_valid, detected_version, errors[])
        - errors[] is a list of structured error dicts on failure.
    """
    version = detect_version(bom)

    if version not in ("1.5", "1.6"):
        return (
            False,
            version,
            [{
                "message": f"Unsupported or missing specVersion; expected 1.5 or 1.6, got '{version or 'none'}'.",
                "path": "/specVersion",
                "schema_path": None,
                "validator": "specVersion",
                "validator_value": ["1.5", "1.6"],
                "context": None
            }]
        )

    try:
        validator = get_validator(version)
    except FileNotFoundError as e:
        return (
            False,
            version,
            [{
                "message": str(e),
                "path": "/",
                "schema_path": None,
                "validator": None,
                "validator_value": None,
                "context": None
            }]
        )
    except Exception as e:
        # If the schema itself is broken, make that obvious
        return (
            False,
            version,
            [{
                "message": f"Internal schema/validator error: {type(e).__name__}: {str(e)}",
                "path": "/",
                "schema_path": None,
                "validator": None,
                "validator_value": None,
                "context": None
            }]
        )

    # Collect all validation errors, sorted by path for readability
    errors: list[Dict[str, Any]] = []
    try:
        for err in sorted(validator.iter_errors(bom), key=lambda e: list(e.path)):
            errors.append(_format_validation_error(err))
    except Exception as e:
        # Catch any unexpected issues from jsonschema internals cleanly
        return (
            False,
            version,
            [{
                "message": f"Unexpected validation engine error: {type(e).__name__}: {str(e)}",
                "path": "/",
                "schema_path": None,
                "validator": None,
                "validator_value": None,
                "context": None
            }]
        )

    if not errors:
        return True, version, []

    return False, version, errors


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
