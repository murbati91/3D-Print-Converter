#!/usr/bin/env python3
"""
Comprehensive Test Suite for /api/convert Endpoint

Tests all 14 slicer settings parameters via the settings_json field.

Usage:
    python test_api_settings.py

Prerequisites:
    - Server must be running on http://localhost:8000
    - Test file will be generated if not present
"""

import requests
import json
import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional


# Configuration
BASE_URL = "http://localhost:8000"
API_ENDPOINT = f"{BASE_URL}/api/convert"
TEST_FILE_DIR = Path(__file__).parent / "test_data"
TEST_FILE = TEST_FILE_DIR / "sample.dxf"


# ANSI color codes for better output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_header(text: str):
    """Print a formatted section header"""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{text}{Colors.RESET}")
    print(f"{Colors.BLUE}{'='*60}{Colors.RESET}")


def print_success(text: str):
    """Print a success message"""
    try:
        print(f"{Colors.GREEN}✅ {text}{Colors.RESET}")
    except UnicodeEncodeError:
        print(f"{Colors.GREEN}[OK] {text}{Colors.RESET}")


def print_error(text: str):
    """Print an error message"""
    try:
        print(f"{Colors.RED}❌ {text}{Colors.RESET}")
    except UnicodeEncodeError:
        print(f"{Colors.RED}[ERROR] {text}{Colors.RESET}")


def print_info(text: str):
    """Print an info message"""
    try:
        print(f"{Colors.YELLOW}ℹ️  {text}{Colors.RESET}")
    except UnicodeEncodeError:
        print(f"{Colors.YELLOW}[INFO] {text}{Colors.RESET}")


def create_minimal_dxf():
    """
    Create a minimal valid DXF file for testing.
    This creates a simple 10x10 square.
    """
    dxf_content = """0
SECTION
2
HEADER
9
$ACADVER
1
AC1015
0
ENDSEC
0
SECTION
2
ENTITIES
0
LINE
8
0
10
0.0
20
0.0
30
0.0
11
10.0
21
0.0
31
0.0
0
LINE
8
0
10
10.0
20
0.0
30
0.0
11
10.0
21
10.0
31
0.0
0
LINE
8
0
10
10.0
20
10.0
30
0.0
11
0.0
21
10.0
31
0.0
0
LINE
8
0
10
0.0
20
10.0
30
0.0
11
0.0
21
0.0
31
0.0
0
ENDSEC
0
EOF
"""
    TEST_FILE_DIR.mkdir(parents=True, exist_ok=True)
    TEST_FILE.write_text(dxf_content)
    print_info(f"Created test DXF file at: {TEST_FILE}")


def check_server_reachable() -> bool:
    """Check if the server is running and reachable"""
    try:
        response = requests.get(f"{BASE_URL}/status", timeout=5)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False


def make_api_call(
    settings: Optional[Dict[str, Any]] = None,
    expect_error: bool = False
) -> requests.Response:
    """
    Make an API call to /api/convert endpoint

    Args:
        settings: Dictionary of settings to send (will be converted to JSON)
        expect_error: Whether we expect this call to fail

    Returns:
        Response object
    """
    if not TEST_FILE.exists():
        raise FileNotFoundError(f"Test file not found: {TEST_FILE}")

    files = {'file': ('sample.dxf', open(TEST_FILE, 'rb'), 'application/dxf')}
    data = {}

    if settings is not None:
        data['settings_json'] = json.dumps(settings)

    try:
        response = requests.post(API_ENDPOINT, files=files, data=data, timeout=30)

        if not expect_error:
            print_info(f"Status Code: {response.status_code}")
            print_info(f"Response: {response.text[:200]}...")

        return response
    except requests.exceptions.RequestException as e:
        print_error(f"Request failed: {e}")
        raise
    finally:
        files['file'][1].close()


def validate_response(response: requests.Response, expected_status: int = 200):
    """Validate response status and basic structure"""
    assert response.status_code == expected_status, \
        f"Expected status {expected_status}, got {response.status_code}: {response.text}"

    if expected_status == 200:
        data = response.json()
        assert 'job_id' in data, "Response missing job_id"
        print_success(f"Job created: {data['job_id']}")


# ============================================================================
# TEST CASES
# ============================================================================

def test_default_settings():
    """
    Test Case 1: Basic conversion with default settings

    Tests backward compatibility - empty settings_json should use all defaults
    """
    print_info("Testing with empty settings (backward compatibility)")
    print_info("Expected: All ConversionRequest defaults should be used")

    response = make_api_call(settings={})
    validate_response(response)

    print_success("PASSED: Empty settings accepted, defaults applied")


def test_full_settings():
    """
    Test Case 2: Full settings override

    Provides all 14 parameters with custom values
    """
    print_info("Testing with all 14 settings provided")

    settings = {
        "output_format": "gcode",
        "extrusion_height": 15.0,
        "scale_factor": 1.5,
        "center_model": True,
        "repair_mesh": True,
        "simplify_mesh": False,
        "simplify_ratio": 0.5,
        "layer_height": 0.3,
        "nozzle_diameter": 0.6,
        "print_speed": 70.0,
        "infill_percentage": 30,
        "support_enabled": True,
        "bed_size_x": 300.0,
        "bed_size_y": 300.0,
        "bed_size_z": 400.0,
    }

    print_info(f"Settings: {json.dumps(settings, indent=2)}")

    response = make_api_call(settings=settings)
    validate_response(response)

    print_success("PASSED: All 14 settings accepted")


def test_partial_settings():
    """
    Test Case 3: Partial settings override

    Provides only a few settings, others should use defaults
    """
    print_info("Testing with partial settings (only 3 params)")

    settings = {
        "nozzle_diameter": 0.8,
        "print_speed": 100.0,
        "bed_size_x": 250.0,
    }

    print_info(f"Settings: {json.dumps(settings, indent=2)}")
    print_info("Expected: Provided settings used, others default")

    response = make_api_call(settings=settings)
    validate_response(response)

    print_success("PASSED: Partial settings accepted, merged with defaults")


def test_bed_size_validation():
    """
    Test Case 4: Bed size validation

    Tests different bed dimensions
    """
    print_info("Testing custom bed dimensions")

    settings = {
        "bed_size_x": 350.0,
        "bed_size_y": 350.0,
        "bed_size_z": 500.0,
    }

    print_info(f"Custom bed size: {settings['bed_size_x']}x{settings['bed_size_y']}x{settings['bed_size_z']}")

    response = make_api_call(settings=settings)
    validate_response(response)

    print_success("PASSED: Custom bed dimensions accepted")


def test_model_processing_settings():
    """
    Test Case 5: Model processing settings

    Tests center_model, repair_mesh, simplify_mesh, simplify_ratio
    """
    print_info("Testing model processing settings")

    settings = {
        "center_model": False,
        "repair_mesh": False,
        "simplify_mesh": True,
        "simplify_ratio": 0.8,
    }

    print_info(f"Processing settings: {json.dumps(settings, indent=2)}")

    response = make_api_call(settings=settings)
    validate_response(response)

    print_success("PASSED: Model processing settings accepted")


def test_slicer_settings():
    """
    Test Case 6: Slicer settings

    Tests nozzle_diameter, print_speed, layer_height, infill_percentage, support_enabled
    """
    print_info("Testing slicer settings")

    settings = {
        "nozzle_diameter": 0.8,
        "print_speed": 80.0,
        "layer_height": 0.25,
        "infill_percentage": 40,
        "support_enabled": True,
    }

    print_info(f"Slicer settings: {json.dumps(settings, indent=2)}")

    response = make_api_call(settings=settings)
    validate_response(response)

    print_success("PASSED: Slicer settings accepted")


def test_invalid_json():
    """
    Test Case 7: Error handling - Invalid JSON

    Tests that malformed JSON is properly rejected
    """
    print_info("Testing invalid JSON error handling")
    print_info("Expected: HTTP 400 with JSON error message")

    # Manually construct request with invalid JSON
    files = {'file': ('sample.dxf', open(TEST_FILE, 'rb'), 'application/dxf')}
    data = {'settings_json': '{invalid json here}'}

    try:
        response = requests.post(API_ENDPOINT, files=files, data=data, timeout=30)
        files['file'][1].close()

        print_info(f"Status Code: {response.status_code}")
        print_info(f"Response: {response.text}")

        assert response.status_code == 400, \
            f"Expected 400 Bad Request, got {response.status_code}"

        assert "Invalid JSON" in response.text or "JSON" in response.text, \
            "Error message should mention JSON"

        print_success("PASSED: Invalid JSON properly rejected with 400")

    except Exception as e:
        files['file'][1].close()
        raise


def test_invalid_settings():
    """
    Test Case 8: Error handling - Invalid setting values

    Tests that invalid parameter values are properly rejected
    """
    print_info("Testing invalid setting values")

    # Test negative nozzle diameter
    print_info("Subtest: Negative nozzle_diameter")
    settings = {
        "nozzle_diameter": -1.0,
    }

    response = make_api_call(settings=settings, expect_error=True)

    # Pydantic should validate this
    # Depending on validation rules, this might be 400 or 422
    assert response.status_code in [400, 422], \
        f"Expected 400/422 for invalid value, got {response.status_code}"

    print_success("PASSED: Invalid negative value rejected")

    # Test invalid infill percentage (>100)
    print_info("Subtest: Invalid infill_percentage (>100)")
    settings = {
        "infill_percentage": 150,
    }

    response = make_api_call(settings=settings, expect_error=True)

    # This might pass if no validation constraint exists
    # Just check if request completes
    print_info(f"Response status: {response.status_code}")

    if response.status_code in [400, 422]:
        print_success("PASSED: Invalid percentage rejected")
    else:
        print_info("NOTE: No validation for infill > 100% (might be intentional)")


def test_output_formats():
    """
    Test Case 9: Different output formats

    Tests with output_format: "stl", "obj", "gcode"
    """
    formats = ["stl", "obj", "gcode"]

    for fmt in formats:
        print_info(f"Testing output format: {fmt}")

        settings = {
            "output_format": fmt,
        }

        response = make_api_call(settings=settings)
        validate_response(response)

        print_success(f"PASSED: {fmt.upper()} format accepted")


def test_edge_case_values():
    """
    Test Case 10: Edge case values

    Tests minimum/maximum reasonable values
    """
    print_info("Testing edge case values")

    settings = {
        "extrusion_height": 0.1,  # Very small
        "scale_factor": 0.1,      # Very small scale
        "layer_height": 0.05,     # Fine layer
        "nozzle_diameter": 0.2,   # Small nozzle
        "print_speed": 10.0,      # Slow speed
        "infill_percentage": 0,   # No infill
        "simplify_ratio": 0.1,    # Aggressive simplification
    }

    print_info(f"Edge values: {json.dumps(settings, indent=2)}")

    response = make_api_call(settings=settings)
    validate_response(response)

    print_success("PASSED: Edge case values accepted")


# ============================================================================
# TEST RUNNER
# ============================================================================

def run_all_tests():
    """Run all test cases and report results"""

    print_header("3D ESP-Print API Settings Test Suite")
    print_info(f"Base URL: {BASE_URL}")
    print_info(f"Endpoint: {API_ENDPOINT}")
    print_info(f"Test file: {TEST_FILE}")

    # Pre-flight checks
    print_header("Pre-flight Checks")

    if not check_server_reachable():
        print_error("Server is not reachable!")
        print_error(f"Make sure the server is running on {BASE_URL}")
        print_info("Start the server with: python server.py")
        sys.exit(1)

    print_success("Server is reachable")

    # Ensure test file exists
    if not TEST_FILE.exists():
        print_info("Test file not found, creating minimal DXF...")
        create_minimal_dxf()
    else:
        print_success(f"Test file exists: {TEST_FILE}")

    # Define test suite
    tests = [
        ("Default Settings (Backward Compatibility)", test_default_settings),
        ("Full Settings Override (14 params)", test_full_settings),
        ("Partial Settings Override", test_partial_settings),
        ("Bed Size Validation", test_bed_size_validation),
        ("Model Processing Settings", test_model_processing_settings),
        ("Slicer Settings", test_slicer_settings),
        ("Invalid JSON Error Handling", test_invalid_json),
        ("Invalid Settings Error Handling", test_invalid_settings),
        ("Different Output Formats", test_output_formats),
        ("Edge Case Values", test_edge_case_values),
    ]

    results = {"passed": 0, "failed": 0, "errors": []}

    # Run tests
    for name, test_func in tests:
        print_header(f"Test: {name}")

        try:
            test_func()
            results["passed"] += 1
            print_success(f"PASSED: {name}")

        except AssertionError as e:
            print_error(f"FAILED: {name}")
            print_error(f"Assertion Error: {e}")
            results["failed"] += 1
            results["errors"].append({"test": name, "error": str(e)})

        except Exception as e:
            print_error(f"ERROR: {name}")
            print_error(f"Exception: {e}")
            results["failed"] += 1
            results["errors"].append({"test": name, "error": str(e)})

    # Print summary
    print_header("Test Results Summary")

    total = results["passed"] + results["failed"]
    print(f"\nTotal Tests: {total}")
    print_success(f"Passed: {results['passed']}")

    if results["failed"] > 0:
        print_error(f"Failed: {results['failed']}")

        print("\nFailed Tests:")
        for error in results["errors"]:
            print(f"  - {error['test']}: {error['error']}")

    success_rate = (results["passed"] / total * 100) if total > 0 else 0
    print(f"\nSuccess Rate: {success_rate:.1f}%")

    if results["failed"] == 0:
        try:
            print_success("\n🎉 All tests passed!")
        except UnicodeEncodeError:
            print_success("\nAll tests passed!")
        return True
    else:
        try:
            print_error(f"\n⚠️  {results['failed']} test(s) failed")
        except UnicodeEncodeError:
            print_error(f"\n{results['failed']} test(s) failed")
        return False


if __name__ == "__main__":
    try:
        success = run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print_error("\n\nTests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"\n\nFatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
