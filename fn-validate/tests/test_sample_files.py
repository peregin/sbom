import json
import os
from func import detect_version

def test_validate_sample_files():
    """Test basic validation of sample CycloneDX BOM files."""
    samples_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'samples')

    # Find all .cdx.json files in the samples directory
    sample_files = [f for f in os.listdir(samples_dir) if f.endswith('.cdx.json')]

    assert len(sample_files) > 0, "No sample files found in samples directory"

    for filename in sample_files:
        filepath = os.path.join(samples_dir, filename)

        # Read and parse the JSON file
        with open(filepath, 'r', encoding='utf-8') as f:
            bom_data = json.load(f)

        # Test version detection
        version = detect_version(bom_data)
        
        # Basic structure validation
        assert isinstance(bom_data, dict), f"BOM should be a dictionary for {filename}"
        assert "bomFormat" in bom_data, f"Missing bomFormat in {filename}"
        assert bom_data["bomFormat"] == "CycloneDX", f"Invalid bomFormat in {filename}"
        assert version in ("1.5", "1.6"), f"Unexpected version {version} for {filename}"
        
        print(f"✓ {filename}: version {version}, valid structure")
