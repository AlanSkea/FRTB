# FRTB Config Converter

A bidirectional converter for FRTB configuration files between Excel (.xlsx) and JSON formats.

## Features

- **Bidirectional conversion**: Excel ↔ JSON
- **Native JSON support**: FRTBConfig.py can load JSON configs directly (preferred over Excel)
- **Self-documenting JSON format**: Type metadata embedded in the data - no external schema required
- **Automatic format detection**: `FRTBConfig` checks for JSON first, falls back to Excel
- **Type preservation**: Automatically detects and preserves data types (int64, float64, str, bool)
- **Structure preservation**: Handles scalars, lists, and DataFrames correctly
- **Command-line interface**: Easy to use from the command line
- **Python API**: Can be used programmatically in Python scripts

## Native JSON Support in FRTBConfig

FRTBConfig.py now natively supports JSON configuration files. When you create an `FRTBConfig` instance, it automatically:

1. Looks for `Configs/FRTBConfig_{regulator}.json` first
2. Falls back to `Configs/FRTBConfig_{regulator}.xlsx` if JSON not found

This means you can use JSON configs directly without any code changes:

```python
from FRTBConfig import FRTBConfig

# This will load JSON if available, otherwise Excel
config = FRTBConfig('BCBS')
```

## JSON Format

The JSON format is self-documenting and stores type metadata alongside the data:

### Copyright/Text
The Copyright sheet is preserved as readable text in the JSON:
```json
{
  "_copyright": {
    "value": [
      "Copyright (C) 2024-2025 frtb.net limited",
      "",
      "Contact us at <info@frtb.net> or via our website at <https://frtb.net>",
      "",
      "This program is free software: you can redistribute it and/or modify",
      "it under the terms of the GNU Affero General Public License as",
      "..."
    ],
    "type": "text",
    "note": "Copyright and license information"
  }
}
```

Empty strings represent blank lines for readability. When converted back to Excel, each line becomes a row in the Copyright sheet.

### Scalars
```json
{
  "DeltaRiskWeight": {
    "value": 0.15,
    "type": "scalar",
    "dtype": "float64"
  }
}
```

### Lists
```json
{
  "BaselCcys": {
    "value": ["USD", "EUR", "JPY", "GBP", "AUD"],
    "type": "list",
    "dtype": "str",
    "name": "BaselCcys"
  }
}
```

Lists can also have custom indices:
```json
{
  "DeltaTenorRiskWeight": {
    "value": [0.017, 0.017, 0.016, 0.013, 0.012, 0.011, 0.011, 0.011, 0.011, 0.011],
    "type": "list",
    "dtype": "float64",
    "name": "DeltaTenorRiskWeight",
    "index": ["0.25", "0.5", "1", "2", "3", "5", "10", "15", "20", "30"]
  }
}
```

### DataFrames
```json
{
  "Bucket": {
    "value": {
      "Bucket": ["1", "2", "3"],
      "SubBucket": ["", "", ""],
      "Description": ["Sovereigns", "Local govt", "Financials"]
    },
    "type": "dataframe",
    "columns": ["Bucket", "SubBucket", "Description"],
    "dtypes": {
      "Bucket": "str",
      "SubBucket": "str",
      "Description": "str"
    },
    "index": ["0", "1", "2"],
    "index_name": "BucketIndex"
  }
}
```

## Usage

### Command Line

#### Convert Excel to JSON
```bash
python FRTBConfigConverter.py Configs/FRTBConfig_BCBS.xlsx

# Specify output file
python FRTBConfigConverter.py Configs/FRTBConfig_BCBS.xlsx -o output.json

# Compact format (no pretty printing)
python FRTBConfigConverter.py Configs/FRTBConfig_BCBS.xlsx --compact
```

#### Convert JSON to Excel
```bash
python FRTBConfigConverter.py Configs/FRTBConfig_BCBS.json

# Specify output file
python FRTBConfigConverter.py Configs/FRTBConfig_BCBS.json -o output.xlsx
```

#### Validate files
```bash
# Validate Excel file
python FRTBConfigConverter.py Configs/FRTBConfig_BCBS.xlsx --validate

# Validate JSON file
python FRTBConfigConverter.py Configs/FRTBConfig_BCBS.json --validate
```

### Python API

#### Using the Converter Class
```python
from FRTBConfigConverter import FRTBConfigConverter

converter = FRTBConfigConverter()

# Excel → JSON
config_dict = converter.excel_to_json(
    'Configs/FRTBConfig_BCBS.xlsx',
    'Configs/FRTBConfig_BCBS.json',
    pretty=True,
    indent=2
)

# JSON → Excel
excel_path = converter.json_to_excel(
    'Configs/FRTBConfig_BCBS.json',
    'output.xlsx'
)

# Validate files
is_valid, errors = converter.validate_json('config.json')
if not is_valid:
    for error in errors:
        print(f"Error: {error}")

is_valid, errors = converter.validate_excel('config.xlsx')
if not is_valid:
    for error in errors:
        print(f"Error: {error}")
```

#### Using FRTBConfig Directly
```python
from FRTBConfig import FRTBConfig

# Class methods for conversion (no instance needed)
FRTBConfig.excelToJSON('Configs/FRTBConfig_BCBS.xlsx', 'config.json')
FRTBConfig.jsonToExcel('config.json', 'config.xlsx')

# Instance method to write current config to JSON
config = FRTBConfig('BCBS')
config.writeConfigToJSON('output.json', pretty=True, indent=2)
```

## Configuration File Location

Configuration files are stored in the `Configs/` directory with the naming convention:
- Excel: `FRTBConfig_{regulator}.xlsx`
- JSON: `FRTBConfig_{regulator}.json`

Supported regulators include:
- `BCBS` - Basel Committee on Banking Supervision
- `EU-EBA` - European Banking Authority
- `UK-PRA` - UK Prudential Regulation Authority
- `SG-MAS` - Monetary Authority of Singapore
- `US-FED` - US Federal Reserve
- `SA-SARB` - South African Reserve Bank

## Testing

Run the included test script to verify the converter is working correctly:

```bash
python FRTBConfigConverter_test.py
```

This will:
1. Convert an Excel config to JSON
2. Convert the JSON back to Excel
3. Convert the recreated Excel back to JSON
4. Compare the two JSON files to ensure they're identical (round-trip test)
5. Show usage examples and JSON format samples

## Advantages of JSON Format

1. **Native support**: FRTBConfig.py loads JSON directly - no converter needed at runtime
2. **Self-documenting**: Type information is embedded in the data
3. **Version control friendly**: Text-based format works well with Git
4. **Easy to edit**: Human-readable and editable in any text editor
5. **No metadata dependencies**: Doesn't require external schema files
6. **Programmatic access**: Easy to parse and manipulate in any programming language
7. **Validation built-in**: Can validate structure without external metadata
8. **Copyright preservation**: Copyright and license text is preserved in readable format

## Excel Format Compatibility

The converter maintains full compatibility with the existing Excel format:
- Reads all existing risk class sheets (MR, MS_IR, MS_CR, MS_CC, MS_CS, MS_EQ, MS_CM, MS_FX, MD_CR, MD_CC, MD_CS, MR_RR, CVA, CS_IR, CS_FX, CS_CC, CS_CR, CS_EQ, CS_CM)
- Preserves all data types and structures
- Handles special cases (Bucket DataFrames, correlation matrices, etc.)
- Maintains compatibility with FRTBConfig class

## Error Handling

The converter includes comprehensive error handling:

### Excel → JSON
- Validates Excel file exists and can be opened
- Checks for corrupted or invalid Excel files
- Validates data structures in each sheet
- Reports specific errors with sheet names and locations

### JSON → Excel
- Validates JSON syntax and structure
- Checks all required fields are present ('type', 'value', etc.)
- Validates data types are correct
- Ensures DataFrame structures are valid

### Validation
- Both formats can be validated without conversion
- Returns detailed error messages with locations
- Helps catch issues before conversion

## Workflow Examples

### Converting existing configs to JSON for version control
```bash
for file in Configs/*.xlsx; do
    python FRTBConfigConverter.py "$file"
done
```

### Editing configs in JSON and converting back
```bash
# Convert to JSON
python FRTBConfigConverter.py Configs/FRTBConfig_BCBS.xlsx

# Edit the JSON file as needed
nano Configs/FRTBConfig_BCBS.json

# Validate changes
python FRTBConfigConverter.py Configs/FRTBConfig_BCBS.json --validate

# Convert back to Excel (if needed for legacy tools)
python FRTBConfigConverter.py Configs/FRTBConfig_BCBS.json -o Configs/FRTBConfig_BCBS.xlsx
```

### Using JSON configs in production
Once you have JSON configs in the `Configs/` directory, FRTBConfig will automatically use them:

```python
from FRTBConfig import FRTBConfig

# Automatically loads Configs/FRTBConfig_BCBS.json if it exists
config = FRTBConfig('BCBS')

# Access config items as usual
buckets = config.getBuckets('MS_CR')
risk_weight = config.getConfigItem('MS_IR', 'DeltaTenorRiskWeight')
```

## Architecture

The conversion functionality is implemented in two places:

1. **FRTBConfig.py** - Contains the core conversion logic:
   - `_readConfigFromJSON()` / `_readConfigFromExcel()` - Reading configs
   - `_configToJSONFormat()` / `_riskClassToJSONFormat()` - Converting to JSON format
   - `excelToJSON()` / `jsonToExcel()` - Class methods for standalone conversion
   - `writeConfigToJSON()` - Instance method to save current config

2. **FRTBConfigConverter.py** - Provides a simplified interface:
   - Wraps FRTBConfig methods for ease of use
   - Adds validation functionality
   - Provides command-line interface

## License

Copyright © 2024-2025 frtb.net limited

Licensed under GNU Affero General Public License v3.0

## Support

For issues or questions:
- Email: <info@frtb.net>
- Website: <https://frtb.net>
