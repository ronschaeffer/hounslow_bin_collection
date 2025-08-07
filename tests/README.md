# Test Suite for Hounslow Bin Collection System

This directory contains comprehensive unit tests for all the new functionality added to the Hounslow bin collection system, with particular focus on format change detection and error handling.

## Test Files Overview

### 1. `test_enhanced_extractor.py`

**Focus:** Core validation and extraction functionality

- Page content validation tests
- Extracted data validation tests
- Format change detection tests
- Error handling for invalid pages
- Integration tests for enhanced extraction

**Key Test Areas:**

- ✅ Valid page content detection
- ✅ Error page detection (404, maintenance, etc.)
- ✅ Data validation with required fields
- ✅ Schedule information validation
- ✅ Exception handling

### 2. `test_cli_and_validation.py`

**Focus:** CLI command functionality and configuration

- CLI command structure validation
- Configuration file handling
- Address normalization testing
- Format validation integration

**Key Test Areas:**

- ✅ CLI commands exist and are structured correctly
- ✅ Config file format validation
- ✅ Address normalization with abbreviations
- ✅ Integration between validation and extraction

### 3. `test_error_handling.py`

**Focus:** Error scenarios and edge cases

- Network failure simulation
- Timeout error handling
- Invalid input handling
- Unicode and edge case testing
- Performance with large datasets

**Key Test Areas:**

- ✅ Network errors (ERR_NAME_NOT_RESOLVED, etc.)
- ✅ JavaScript execution errors
- ✅ Empty/malformed page content
- ✅ Address validation edge cases
- ✅ Large content handling

### 4. `test_cli_integration.py`

**Focus:** End-to-end CLI testing

- Complete CLI workflow testing
- Output formatting validation
- Error message clarity
- Configuration integration

**Key Test Areas:**

- ✅ CLI success scenarios
- ✅ CLI error scenarios
- ✅ Output formatting
- ✅ Error message quality

## Running Tests

### Run All Tests

```bash
python run_tests.py
```

### Run Specific Test Categories

```bash
python run_tests.py validation    # Format detection and validation tests
python run_tests.py error        # Error handling tests
python run_tests.py cli          # CLI integration tests
python run_tests.py browser      # Browser automation tests
python run_tests.py core         # Core functionality tests
```

### Show Test Coverage Summary

```bash
python run_tests.py summary
```

### Run Individual Test Files

```bash
python -m pytest tests/test_enhanced_extractor.py -v
python -m pytest tests/test_cli_and_validation.py -v
python -m pytest tests/test_error_handling.py -v
python -m pytest tests/test_cli_integration.py -v
```

## Test Coverage Areas

### 🔍 Format Change Detection

- **Page Validation:** Detects error pages, maintenance pages, and content that's too short
- **Content Validation:** Ensures required keywords are present (collection, bin/waste, schedule terms)
- **Data Validation:** Validates extracted bin data has required fields and meaningful schedule info
- **Error Detection:** Catches format changes and provides clear error messages

### 🌐 Network & Error Handling

- **Network Failures:** Tests handling of DNS resolution errors, timeouts, connection failures
- **JavaScript Errors:** Tests handling of browser automation errors
- **Invalid Content:** Tests handling of empty pages, malformed HTML, error pages
- **Recovery Scenarios:** Tests fallback mechanisms when primary extraction fails

### 📋 Address Processing

- **Normalization:** Tests address abbreviation expansion (Rd→Road, St→Street, etc.)
- **Variations:** Tests generation of address variations for better matching
- **Edge Cases:** Tests invalid addresses, unicode characters, very long addresses
- **Strict Matching:** Tests exact address matching for --strict mode

### 🖥️ CLI Integration

- **Command Structure:** Tests that CLI commands exist and are properly structured
- **Output Formatting:** Tests that schedule output matches expected format
- **Error Messages:** Tests that error messages are clear and actionable
- **Configuration:** Tests config file loading and default values

### 🛡️ Robustness & Edge Cases

- **Input Validation:** Tests handling of invalid postcodes, addresses, arguments
- **Large Datasets:** Tests performance with many bin types and large content
- **Unicode Support:** Tests handling of international characters in addresses
- **Boundary Conditions:** Tests validation at exact limits (content length, etc.)

## Key Features Tested

### ✅ No Silent Failures

All tests verify that the system:

- Never returns misleading data when website format changes
- Always provides clear error messages when extraction fails
- Handles network issues gracefully with appropriate errors
- Validates data quality before returning results

### ✅ Format Change Detection

Tests verify the system detects:

- Website maintenance pages
- 404 and other error pages
- Missing required content keywords
- Invalid or incomplete data extraction
- JavaScript execution failures

### ✅ Address Matching Robustness

Tests verify address handling:

- Expands common abbreviations automatically
- Generates multiple variations for better matching
- Handles case variations correctly
- Works with house numbers and letters (123a, etc.)
- Removes duplicates from variation lists

### ✅ Error Message Quality

Tests verify error messages:

- Clearly explain what went wrong
- Suggest potential causes (website format change, network issue, etc.)
- Don't expose technical details to end users
- Are consistent across different error scenarios

## Fixtures and Utilities

### Test Fixtures (`conftest.py`)

- `mock_iframe_frame`: Mock browser frame for testing extraction
- `sample_bin_data`: Standard test data for bin collections
- `sample_collection_result`: Complete extraction result for testing
- `project_root`: Path utilities for test files

### Mock Classes

- `MockFrame`: Simulates browser iframe with configurable content
- Various mock collectors and extractors for isolated testing

## Test Data Standards

### Standard Test Address

All tests use `"132 Worple Rd"` as the standard test address to ensure consistency.

### Standard Test Postcode

All tests use `"TW3 3EB"` as the standard test postcode.

### Expected Output Format

Tests verify output matches: `"General Waste: Every 2 weeks on Tuesday (Next: 19/08/2025)"`

## Integration with CI/CD

These tests are designed to:

- Run quickly in automated environments
- Provide clear pass/fail indicators
- Generate detailed error reports
- Work without external network dependencies (using mocks)
- Validate all new functionality without requiring live website access

## Contributing

When adding new functionality:

1. Add corresponding tests in the appropriate test file
2. Update test coverage documentation
3. Ensure tests cover both success and failure scenarios
4. Add edge case testing for new features
5. Update the test runner if new test categories are added
