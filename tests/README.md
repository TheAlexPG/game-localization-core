# Test Suite

Comprehensive test suite for the Game Translation System.

## Structure

```
tests/
├── __init__.py              # Test package init
├── run_tests.py            # Main test runner
├── README.md               # This file
│
├── providers/              # AI Provider tests
│   ├── __init__.py
│   ├── test_openai.py      # OpenAI provider tests
│   ├── test_local.py       # Local model tests
│   └── test_structured_output.py  # Structured output tests
│
├── validation/             # Validation system tests
│   ├── __init__.py
│   ├── test_core_validation.py     # Core validation features
│   ├── test_game_validation.py     # Real game data tests
│   ├── test_custom_patterns.py     # Custom pattern tests
│   ├── test_custom_simple.py       # Simple custom pattern test
│   ├── test_flexible_variables.py  # Variable pattern tests
│   ├── test_validation.py          # Full validation suite
│   └── test_validation_simplified.py  # Simplified tests
│
├── examples/               # Example and demo tests
│   └── __init__.py
│
├── test_basic.py          # Basic system functionality
└── test_translation.py    # Translation pipeline tests
```

## Running Tests

### Run All Tests
```bash
python tests/run_tests.py
```

### Run Specific Categories

#### Provider Tests
```bash
python tests/providers/test_openai.py
python tests/providers/test_local.py
python tests/providers/test_structured_output.py
```

#### Validation Tests
```bash
python tests/validation/test_core_validation.py
python tests/validation/test_game_validation.py
python tests/validation/test_custom_patterns.py
```

#### Basic Tests
```bash
python tests/test_basic.py
python tests/test_translation.py
```

## Test Categories

### 1. Provider Tests (`providers/`)
Test AI translation providers and their functionality:
- **OpenAI Provider**: API integration, structured output
- **Local Provider**: LM Studio/Ollama integration
- **Structured Output**: JSON schema validation

### 2. Validation Tests (`validation/`)
Test translation validation and quality control:
- **Core Validation**: Basic placeholder and tag validation
- **Game Data**: Real game examples (Silksong, X4)
- **Custom Patterns**: User-defined validation rules
- **Flexible Variables**: System variable handling

### 3. Basic Tests
Test core system functionality:
- **Basic**: Core models and utilities
- **Translation**: End-to-end translation pipeline

## Requirements

### Required for All Tests
- Python 3.8+
- Core project dependencies

### Optional (some tests may be skipped)
- **OpenAI API Key**: For OpenAI provider tests
- **LM Studio**: For local model tests
- **openpyxl**: For Excel-related tests

## Test Data

Tests use various types of data:
- **Synthetic examples**: Generated test cases
- **Real game data**: Actual localization files
- **Unicode text**: Multi-language content
- **Complex markup**: Mixed pattern types

## Output Files

Some tests generate output files:
- `validation_test_results.txt`
- `core_validation_demo.txt`
- `game_validation_results.txt`
- `ValidationPatterns_Template.xlsx`

These files are created in the project root during testing.

## Environment Setup

### Set Environment Variables (Optional)
```bash
export OPENAI_API_KEY="your-openai-key"
export LOCAL_API_URL="http://localhost:1234/v1/chat/completions"
```

### Install Test Dependencies
```bash
pip install openpyxl  # For Excel tests
```

## Troubleshooting

### Common Issues

**Unicode Encoding Errors**
- Tests save results to files instead of console output
- Check generated `.txt` files for full results

**Missing API Keys**
- Provider tests will skip if credentials not available
- Tests will show "SKIP" messages

**Import Errors**
- Make sure to run tests from project root
- Check that `game_translator` package is importable

### Test Failures

Most test failures are expected in certain scenarios:
- Missing API credentials
- Unavailable local models
- Network connectivity issues

Check individual test output for specific error details.

## Adding New Tests

### Create New Test File
```python
#!/usr/bin/env python3
"""Description of test"""

def test_functionality():
    \"\"\"Test specific functionality\"\"\"
    # Test implementation
    pass

def main():
    \"\"\"Main test function\"\"\"
    test_functionality()
    print("Test completed")

if __name__ == "__main__":
    main()
```

### Add to Test Runner
Edit `run_tests.py` to include new test in appropriate category.

### Follow Naming Convention
- File names: `test_feature.py`
- Function names: `test_specific_case()`
- Main function: `main()`