import json
from func import validate_bom

def test_invalid_without_spec_version():
    bom = {"bomFormat": "CycloneDX", "version": 1}
    ok, version, errors = validate_bom(bom)
    assert not ok
    assert version == ""
    assert any("Unsupported" in e or "specVersion" in str(e) for e in errors)

def test_valid_minimal_15():
    bom = {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "version": 1,
        "metadata": {
            "timestamp": "2024-01-01T00:00:00Z",
            "tools": [{"name": "unit-test-tool"}]
        }
    }
    ok, version, errors = validate_bom(bom)
    assert ok, f"Expected valid BOM, got errors: {errors}"
    assert version == "1.5"

def test_valid_minimal_16():
    bom = {
        "bomFormat": "CycloneDX",
        "specVersion": "1.6",
        "version": 1,
        "metadata": {
            "timestamp": "2024-01-01T00:00:00Z",
            "tools": [{"name": "unit-test-tool"}]
        }
    }
    ok, version, errors = validate_bom(bom)
    assert ok, f"Expected valid BOM, got errors: {errors}"
    assert version == "1.6"
    assert len(errors) == 0, f"No validation errors expected, but got: {errors}"

def test_rejects_unsupported_version():
    bom = {"bomFormat": "CycloneDX", "specVersion": "1.7", "version": 1}
    ok, version, errors = validate_bom(bom)
    assert not ok
    assert version == "1.7"
    assert any("Unsupported" in e for e in errors)
    assert len(errors) > 0, "Expected validation errors for unsupported version"
