import json
from func import detect_version

def test_detect_version_15_from_spec():
    bom = {"specVersion": "1.5"}
    assert detect_version(bom) == "1.5"

def test_detect_version_16_from_spec():
    bom = {"specVersion": "1.6"}
    assert detect_version(bom) == "1.6"

def test_detect_version_from_schema_url():
    bom = {"$schema": "https://cyclonedx.org/schema/bom-1.5.schema.json"}
    assert detect_version(bom) == "1.5"

def test_detect_version_unknown():
    bom = {"specVersion": "1.4"}
    assert detect_version(bom) == "1.4"
