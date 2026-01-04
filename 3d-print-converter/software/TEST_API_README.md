# API Settings Test Suite

Comprehensive test suite for the `/api/convert` endpoint that validates all 14 slicer settings parameters.

## Quick Start

### Prerequisites

1. **Start the server:**
   ```bash
   python server.py
   ```
   The server must be running on `http://localhost:8000`

2. **Run the tests:**
   ```bash
   python test_api_settings.py
   ```

### What Gets Tested

The test suite automatically creates a minimal test DXF file and validates:

1. **Backward Compatibility**: Empty settings use defaults
2. **Full Settings**: All 14 parameters provided
3. **Partial Settings**: Mix of custom and default values
4. **Bed Dimensions**: Custom bed sizes (bed_size_x/y/z)
5. **Model Processing**: center_model, repair_mesh, simplify_mesh, simplify_ratio
6. **Slicer Settings**: nozzle_diameter, print_speed, layer_height, infill_percentage, support_enabled
7. **Error Handling**: Invalid JSON and invalid parameter values
8. **Output Formats**: STL, OBJ, GCODE
9. **Edge Cases**: Minimum/maximum reasonable values

## Test Coverage

### All 14 Settings Parameters

| Parameter | Type | Default | Tested Values |
|-----------|------|---------|---------------|
| `output_format` | string | "stl" | "stl", "obj", "gcode" |
| `extrusion_height` | float | 10.0 | 0.1, 15.0 |
| `scale_factor` | float | 1.0 | 0.1, 1.5 |
| `center_model` | bool | True | True, False |
| `repair_mesh` | bool | True | True, False |
| `simplify_mesh` | bool | False | True, False |
| `simplify_ratio` | float | 0.5 | 0.1, 0.5, 0.8 |
| `layer_height` | float | 0.2 | 0.05, 0.2, 0.25, 0.3 |
| `nozzle_diameter` | float | 0.4 | 0.2, 0.4, 0.6, 0.8 |
| `print_speed` | float | 50.0 | 10.0, 50.0, 70.0, 80.0, 100.0 |
| `infill_percentage` | int | 20 | 0, 20, 30, 40 |
| `support_enabled` | bool | False | True, False |
| `bed_size_x` | float | 220.0 | 220.0, 250.0, 300.0, 350.0 |
| `bed_size_y` | float | 220.0 | 220.0, 300.0, 350.0 |
| `bed_size_z` | float | 250.0 | 250.0, 400.0, 500.0 |

## Example Test Output

```
============================================================
3D ESP-Print API Settings Test Suite
============================================================
ℹ️  Base URL: http://localhost:8000
ℹ️  Endpoint: http://localhost:8000/api/convert
ℹ️  Test file: C:\...\test_data\sample.dxf

============================================================
Pre-flight Checks
============================================================
✅ Server is reachable
✅ Test file exists: C:\...\test_data\sample.dxf

============================================================
Test: Default Settings (Backward Compatibility)
============================================================
ℹ️  Testing with empty settings (backward compatibility)
ℹ️  Expected: All ConversionRequest defaults should be used
ℹ️  Status Code: 200
ℹ️  Response: {"job_id":"abc12345",...}
✅ Job created: abc12345
✅ PASSED: Empty settings accepted, defaults applied
✅ ✅ PASSED: Default Settings (Backward Compatibility)

...

============================================================
Test Results Summary
============================================================

Total Tests: 10
✅ Passed: 10

Success Rate: 100.0%

🎉 All tests passed!
```

## Test Details

### Test 1: Default Settings
- **Purpose**: Verify backward compatibility
- **Input**: Empty `settings_json` or `{}`
- **Expected**: All defaults from `ConversionRequest` model used

### Test 2: Full Settings Override
- **Purpose**: Validate all 14 parameters can be customized
- **Input**: JSON with all 14 fields
- **Expected**: Request accepted, job created

### Test 3: Partial Settings
- **Purpose**: Verify defaults merge with custom values
- **Input**: Only 3 settings (nozzle_diameter, print_speed, bed_size_x)
- **Expected**: Provided values used, others default

### Test 4: Bed Size Validation
- **Purpose**: Test custom printer dimensions
- **Input**: bed_size_x=350, bed_size_y=350, bed_size_z=500
- **Expected**: Custom dimensions accepted

### Test 5: Model Processing Settings
- **Purpose**: Validate mesh processing flags
- **Input**: center_model, repair_mesh, simplify_mesh, simplify_ratio
- **Expected**: Boolean and ratio values accepted

### Test 6: Slicer Settings
- **Purpose**: Test print quality parameters
- **Input**: nozzle_diameter, print_speed, layer_height, infill, supports
- **Expected**: All slicer params accepted

### Test 7: Invalid JSON
- **Purpose**: Error handling for malformed JSON
- **Input**: `{invalid json here}`
- **Expected**: HTTP 400 with JSON error message

### Test 8: Invalid Settings
- **Purpose**: Validation of parameter values
- **Input**: nozzle_diameter=-1.0, infill_percentage=150
- **Expected**: HTTP 400/422 for invalid values

### Test 9: Output Formats
- **Purpose**: Test all supported formats
- **Input**: output_format = "stl", "obj", "gcode"
- **Expected**: Each format accepted

### Test 10: Edge Cases
- **Purpose**: Test minimum/maximum values
- **Input**: Very small/large values within reason
- **Expected**: Edge values accepted

## API Usage Examples

### Minimal Request (Default Settings)
```python
files = {'file': open('model.dxf', 'rb')}
data = {'settings_json': '{}'}
response = requests.post('http://localhost:8000/api/convert', files=files, data=data)
```

### Full Custom Settings
```python
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

files = {'file': open('model.dxf', 'rb')}
data = {'settings_json': json.dumps(settings)}
response = requests.post('http://localhost:8000/api/convert', files=files, data=data)
```

### Partial Settings (Only Override What You Need)
```python
settings = {
    "nozzle_diameter": 0.8,
    "print_speed": 100.0,
    "support_enabled": True,
}

files = {'file': open('model.dxf', 'rb')}
data = {'settings_json': json.dumps(settings)}
response = requests.post('http://localhost:8000/api/convert', files=files, data=data)
```

## Troubleshooting

### Server Not Reachable
```
❌ Server is not reachable!
```
**Solution**: Start the server with `python server.py`

### Test File Issues
The test suite automatically creates a minimal DXF file if missing.
Location: `test_data/sample.dxf`

### Failed Tests
Check the detailed error output for each failed test. Common issues:
- Server validation rules changed
- Missing dependencies
- Network/timeout issues

## Exit Codes

- `0`: All tests passed
- `1`: One or more tests failed or error occurred

## Running Specific Tests

To run individual test functions, modify the `tests` list in `run_all_tests()`:

```python
tests = [
    ("Full Settings Override", test_full_settings),
    ("Slicer Settings", test_slicer_settings),
]
```

## Adding New Tests

1. Create a new test function following the pattern:
   ```python
   def test_my_feature():
       print_info("Testing my feature")
       settings = {...}
       response = make_api_call(settings=settings)
       validate_response(response)
       print_success("PASSED: My feature works")
   ```

2. Add to the `tests` list in `run_all_tests()`

3. Run the full suite to verify

## CI/CD Integration

Use in automated testing:

```bash
# Exit code 0 = success, 1 = failure
python test_api_settings.py
if [ $? -eq 0 ]; then
    echo "API tests passed"
else
    echo "API tests failed"
    exit 1
fi
```
