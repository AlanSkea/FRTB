"""
Config file converter for FRTB configurations between Excel and JSON formats.

This module provides a command-line interface for converting FRTB configuration
files between Excel (.xlsx) and JSON formats. The actual conversion logic is
implemented in FRTBConfig.py.

Copyright © 2024 frtb.net limited

Author: Alan Skea, frtb.net limited

Contact us at <info@frtb.net> or via our website at <https://frtb.net>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import argparse
import json
from pathlib import Path

from FRTBConfig import FRTBConfig


class FRTBConfigConverter:
    """
    Converts FRTB configuration files between Excel and JSON formats.

    This class provides a simplified interface to the conversion functionality
    in FRTBConfig. The JSON format is self-documenting and stores metadata
    alongside data:
    - Scalars: {"value": <scalar>, "type": "scalar", "dtype": "float64"}
    - Lists: {"value": [...], "type": "list", "dtype": "float64", "name": "..."}
    - DataFrames: {"value": {...}, "type": "dataframe", "columns": [...], "dtypes": {...}}
    """

    def __init__(self):
        self._name = type(self).__name__

    def excel_to_json(self, excel_path: str, json_path: str = None,
                      pretty: bool = True, indent: int = 2) -> dict:
        """
        Convert an Excel config file to JSON format.

        Args:
            excel_path: Path to the Excel file
            json_path: Path to save JSON file (optional, defaults to same name with .json)
            pretty: Whether to pretty-print the JSON
            indent: Indentation level for pretty printing

        Returns:
            Dictionary containing the converted configuration
        """
        return FRTBConfig.excelToJSON(excel_path, json_path, pretty, indent)

    def json_to_excel(self, json_path: str, excel_path: str = None) -> str:
        """
        Convert a JSON config file to Excel format.

        Args:
            json_path: Path to the JSON file
            excel_path: Path to save Excel file (optional)

        Returns:
            Path to the created Excel file
        """
        return FRTBConfig.jsonToExcel(json_path, excel_path)

    def validate_json(self, json_path: str) -> tuple:
        """
        Validate a JSON config file.

        Args:
            json_path: Path to JSON file

        Returns:
            Tuple of (is_valid: bool, errors: List[str])
        """
        json_path = Path(json_path)
        errors = []

        if not json_path.exists():
            return False, [f"File not found: {json_path}"]

        try:
            with open(json_path, 'r') as f:
                config = json.load(f)
        except Exception as e:
            return False, [f"Invalid JSON: {e}"]

        if not isinstance(config, dict):
            errors.append("Root element must be a dictionary")
            return False, errors

        # Validate each risk class
        for risk_class, data in config.items():
            if risk_class == '_copyright':
                if not isinstance(data, dict):
                    errors.append("_copyright must be a dictionary")
                    continue
                if 'type' not in data or data['type'] != 'text':
                    errors.append("_copyright must have type='text'")
                if 'value' not in data or not isinstance(data['value'], list):
                    errors.append("_copyright value must be a list of strings")
                continue

            if not isinstance(data, dict):
                errors.append(f"Risk class '{risk_class}' must be a dictionary")
                continue

            for key, item in data.items():
                if not isinstance(item, dict):
                    errors.append(f"{risk_class}.{key}: must be a dictionary")
                    continue

                if 'type' not in item:
                    errors.append(f"{risk_class}.{key}: missing 'type' field")
                    continue

                item_type = item['type']

                if item_type == 'scalar':
                    if 'value' not in item:
                        errors.append(f"{risk_class}.{key}: scalar missing 'value'")
                    if 'dtype' not in item:
                        errors.append(f"{risk_class}.{key}: scalar missing 'dtype'")

                elif item_type == 'list':
                    if 'value' not in item or not isinstance(item['value'], list):
                        errors.append(f"{risk_class}.{key}: list missing or invalid 'value'")
                    if 'dtype' not in item:
                        errors.append(f"{risk_class}.{key}: list missing 'dtype'")

                elif item_type == 'dataframe':
                    if 'value' not in item or not isinstance(item['value'], dict):
                        errors.append(f"{risk_class}.{key}: dataframe missing or invalid 'value'")
                    if 'columns' not in item or not isinstance(item['columns'], list):
                        errors.append(f"{risk_class}.{key}: dataframe missing or invalid 'columns'")
                    if 'dtypes' not in item or not isinstance(item['dtypes'], dict):
                        errors.append(f"{risk_class}.{key}: dataframe missing or invalid 'dtypes'")

                else:
                    errors.append(f"{risk_class}.{key}: unknown type '{item_type}'")

        return len(errors) == 0, errors

    def validate_excel(self, excel_path: str) -> tuple:
        """
        Validate an Excel config file by attempting to load it.

        Args:
            excel_path: Path to Excel file

        Returns:
            Tuple of (is_valid: bool, errors: List[str])
        """
        excel_path = Path(excel_path)

        if not excel_path.exists():
            return False, [f"File not found: {excel_path}"]

        try:
            # Try to convert to JSON - this validates the structure
            FRTBConfig.excelToJSON(str(excel_path), None, pretty=False)
        except Exception as e:
            return False, [f"Error parsing Excel file: {e}"]

        return True, []


def main():
    """Command-line interface for the converter."""
    parser = argparse.ArgumentParser(
        description='Convert FRTB config files between Excel and JSON formats'
    )
    parser.add_argument('input', help='Input file path')
    parser.add_argument('-o', '--output', help='Output file path (optional)')
    parser.add_argument('-v', '--validate', action='store_true',
                       help='Validate file without converting')
    parser.add_argument('--compact', action='store_true',
                       help='Use compact JSON format (no pretty printing)')

    args = parser.parse_args()

    converter = FRTBConfigConverter()
    input_path = Path(args.input)

    if not input_path.exists():
        print(f"Error: File not found: {input_path}")
        return 1

    # Determine format from extension
    if input_path.suffix.lower() == '.json':
        # JSON input
        if args.validate:
            is_valid, errors = converter.validate_json(str(input_path))
            if is_valid:
                print(f"Valid JSON config: {input_path}")
                return 0
            else:
                print(f"Invalid JSON config: {input_path}")
                for error in errors:
                    print(f"  - {error}")
                return 1
        else:
            # Convert to Excel
            try:
                output = converter.json_to_excel(str(input_path), args.output)
                return 0
            except Exception as e:
                print(f"Error: {e}")
                return 1

    elif input_path.suffix.lower() in ('.xlsx', '.xls'):
        # Excel input
        if args.validate:
            is_valid, errors = converter.validate_excel(str(input_path))
            if is_valid:
                print(f"Valid Excel config: {input_path}")
                return 0
            else:
                print(f"Invalid Excel config: {input_path}")
                for error in errors:
                    print(f"  - {error}")
                return 1
        else:
            # Convert to JSON
            try:
                converter.excel_to_json(
                    str(input_path),
                    args.output,
                    pretty=not args.compact
                )
                return 0
            except Exception as e:
                print(f"Error: {e}")
                return 1

    else:
        print(f"Error: Unsupported file format: {input_path.suffix}")
        print("Supported formats: .json, .xlsx, .xls")
        return 1


if __name__ == '__main__':
    import sys
    sys.exit(main())
