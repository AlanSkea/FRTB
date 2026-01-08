"""
Converter for FNetF (frtb.net Format) files between Excel and JSON formats.

Provides bidirectional conversion with validation and a command-line interface.

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

import os
import json
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List, Tuple

from FNetF import FNetF, FNetFieldType, FNetFormatVersion


class _FNetFJSONEncoder(json.JSONEncoder):
    """JSON encoder that handles numpy and pandas types."""
    def default(self, obj):
        if isinstance(obj, (np.integer, np.int64)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float64)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, pd.Timestamp):
            return obj.isoformat()
        elif pd.isna(obj):
            return None
        return super().default(obj)


class FNetFConverter:
    """
    Converts FNetF files between Excel and JSON formats.

    The JSON format is self-documenting with the following structure:
    {
        "_copyright": { "value": [...], "type": "text", ... },
        "_parameters": { "FNetFormatVersion": "3.0", ... },
        "_tests": {
            "CapitalTests": { "columns": [...], "data": [...] },
            ...
        },
        "_sensitivities": {
            "MS_IRDelta": { "columns": [...], "dtypes": {...}, "data": [...] },
            ...
        }
    }
    """

    def __init__(self):
        self._name = type(self).__name__

    def excel_to_json(self, excel_path: str, json_path: str = None,
                      pretty: bool = True, indent: int = 2) -> Dict[str, Any]:
        """
        Convert an FNetF Excel file to JSON format.

        Args:
            excel_path: Path to the Excel file
            json_path: Path to save JSON file (optional, defaults to same name with .json)
            pretty: Whether to pretty-print the JSON
            indent: Indentation level for pretty printing

        Returns:
            Dictionary containing the converted data

        Raises:
            FileNotFoundError: If Excel file doesn't exist
            ValueError: If Excel file is invalid
        """
        excel_path = Path(excel_path)
        if not excel_path.exists():
            raise FileNotFoundError(f"Excel file not found: {excel_path}")

        if json_path is None:
            json_path = excel_path.with_suffix('.json')
        else:
            json_path = Path(json_path)

        print(f"Converting Excel → JSON: {excel_path} → {json_path}")

        # Load using FNetF class
        fnf = FNetF()
        try:
            fnf.load(str(excel_path))
        except Exception as e:
            raise ValueError(f"Failed to load Excel file: {e}")

        # Build JSON structure
        data = self._fnf_to_dict(fnf)

        # Save to JSON
        with open(json_path, 'w') as f:
            if pretty:
                json.dump(data, f, indent=indent, cls=_FNetFJSONEncoder)
            else:
                json.dump(data, f, cls=_FNetFJSONEncoder)

        print(f"✓ Conversion complete: {json_path}")
        return data

    def json_to_excel(self, json_path: str, excel_path: str = None) -> str:
        """
        Convert an FNetF JSON file to Excel format.

        Args:
            json_path: Path to the JSON file
            excel_path: Path to save Excel file (optional)

        Returns:
            Path to the created Excel file

        Raises:
            FileNotFoundError: If JSON file doesn't exist
            ValueError: If JSON is invalid
        """
        json_path = Path(json_path)
        if not json_path.exists():
            raise FileNotFoundError(f"JSON file not found: {json_path}")

        if excel_path is None:
            excel_path = json_path.with_suffix('.xlsx')
        else:
            excel_path = Path(excel_path)

        print(f"Converting JSON → Excel: {json_path} → {excel_path}")

        # Load JSON
        try:
            with open(json_path, 'r') as f:
                data = json.load(f)
        except Exception as e:
            raise ValueError(f"Failed to parse JSON file: {e}")

        # Validate structure
        is_valid, errors = self._validate_json_structure(data)
        if not is_valid:
            raise ValueError(f"Invalid JSON structure: {'; '.join(errors[:3])}")

        # Build FNetF object and save
        fnf = self._dict_to_fnf(data)
        fnf.save(str(excel_path))

        print(f"✓ Conversion complete: {excel_path}")
        return str(excel_path)

    def _fnf_to_dict(self, fnf: FNetF) -> Dict[str, Any]:
        """Convert FNetF object to dictionary structure."""
        data = {}

        # Add copyright
        copyright_text = [
            f"frtb.net Format (FNetF) version {FNetFormatVersion}",
            "",
            "Copyright (C) 2024-2025 frtb.net limited",
            "",
            "Contact us at <info@frtb.net> or via our website at <https://frtb.net>",
            "",
            "This program is free software: you can redistribute it and/or modify",
            "it under the terms of the GNU Affero General Public License as",
            "published by the Free Software Foundation, either version 3 of the",
            "License, or (at your option) any later version."
        ]

        if hasattr(fnf, '_copyright') and fnf._copyright:
            data['_copyright'] = fnf._copyright
        else:
            data['_copyright'] = {
                'value': copyright_text,
                'type': 'text',
                'note': 'Copyright and license information'
            }

        # Add parameters
        data['_parameters'] = fnf._params.copy()

        # Add test data
        if fnf._tests:
            data['_tests'] = {}
            for testType, testDf in fnf._tests.items():
                if not testDf.empty:
                    keycols = ['Test ID', 'RiskGroup', 'RiskSubGroup', 'RiskClass', 'Description', 'Sensitivity IDs']
                    valcols = [x for x in testDf.columns if x not in keycols]
                    cols = [c for c in keycols + valcols if c in testDf.columns]

                    data['_tests'][testType] = {
                        'columns': cols,
                        'data': testDf[cols].values.tolist()
                    }

        # Add sensitivity data
        if fnf._sensis:
            data['_sensitivities'] = {}
            for riskClass, df in fnf._sensis.items():
                if not df.empty:
                    cols = [x for x in ['Sensitivity ID'] + list(FNetFieldType.get(riskClass, {}).keys())
                            if x in df.columns]

                    # Get dtypes for documentation
                    dtypes = {'Sensitivity ID': 'str'}
                    for col in cols:
                        if col in FNetFieldType.get(riskClass, {}):
                            dtypes[col] = FNetFieldType[riskClass][col]

                    # Convert DataFrame, handling NaN properly
                    df_subset = df[cols].copy()
                    df_subset = df_subset.where(pd.notnull(df_subset), None)

                    data['_sensitivities'][riskClass] = {
                        'columns': cols,
                        'dtypes': dtypes,
                        'data': df_subset.values.tolist()
                    }

        return data

    def _dict_to_fnf(self, data: Dict[str, Any]) -> FNetF:
        """Convert dictionary structure to FNetF object."""
        fnf = FNetF()

        # Set copyright
        if '_copyright' in data:
            fnf._copyright = data['_copyright']

        # Set parameters
        if '_parameters' in data:
            fnf._params = data['_parameters'].copy()

        # Set test data
        if '_tests' in data:
            for testType, testData in data['_tests'].items():
                if testType in fnf.FNF_Test_Tabs:
                    df = pd.DataFrame(testData['data'], columns=testData['columns'])
                    # Convert benchmark columns to float64
                    for col in df.columns:
                        if col.startswith('Benchmark_'):
                            df[col] = pd.to_numeric(df[col], errors='coerce')
                    fnf._tests[testType] = df

        # Set sensitivity data
        if '_sensitivities' in data:
            for riskClass, rcData in data['_sensitivities'].items():
                df = pd.DataFrame(rcData['data'], columns=rcData['columns'])

                # Apply type conversions if riskClass is known
                if riskClass in FNetFieldType:
                    typemap = {}
                    for col, dtype in FNetFieldType[riskClass].items():
                        if col in df.columns and dtype != 'object':
                            if dtype == 'float64':
                                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
                            elif dtype == 'int64':
                                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype('int64')
                            elif dtype == 'bool':
                                df[col] = df[col].apply(lambda x: x not in [False, 'False', None, ''])
                            typemap[col] = dtype

                    if typemap:
                        df = df.astype(typemap)

                fnf._sensis[riskClass] = df

                # Update risk groups
                if 'RiskGroup' in df.columns and 'RiskSubGroup' in df.columns:
                    fnf._riskGroups |= set([
                        (r.at['RiskGroup'], r.at['RiskSubGroup'])
                        for _, r in df[['RiskGroup', 'RiskSubGroup']].drop_duplicates().iterrows()
                    ])

        return fnf

    def validate_json(self, json_path: str) -> Tuple[bool, List[str]]:
        """
        Validate an FNetF JSON file.

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
                data = json.load(f)
        except Exception as e:
            return False, [f"Invalid JSON: {e}"]

        return self._validate_json_structure(data)

    def _validate_json_structure(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate the structure of FNetF JSON data."""
        errors = []

        if not isinstance(data, dict):
            errors.append("Root element must be a dictionary")
            return False, errors

        # Check for required sections
        if '_parameters' not in data:
            errors.append("Missing '_parameters' section")
        else:
            params = data['_parameters']
            if not isinstance(params, dict):
                errors.append("'_parameters' must be a dictionary")
            elif 'FNetFormatVersion' not in params:
                errors.append("Missing 'FNetFormatVersion' in parameters")
            elif params['FNetFormatVersion'] != FNetFormatVersion:
                errors.append(f"Incompatible FNetFormatVersion: expected {FNetFormatVersion}, got {params['FNetFormatVersion']}")

        # Validate copyright
        if '_copyright' in data:
            copyright = data['_copyright']
            if not isinstance(copyright, dict):
                errors.append("'_copyright' must be a dictionary")
            elif 'type' not in copyright or copyright['type'] != 'text':
                errors.append("'_copyright' must have type='text'")
            elif 'value' not in copyright or not isinstance(copyright['value'], list):
                errors.append("'_copyright.value' must be a list of strings")

        # Validate tests
        if '_tests' in data:
            tests = data['_tests']
            if not isinstance(tests, dict):
                errors.append("'_tests' must be a dictionary")
            else:
                for testType, testData in tests.items():
                    if not isinstance(testData, dict):
                        errors.append(f"'_tests.{testType}' must be a dictionary")
                    elif 'columns' not in testData or 'data' not in testData:
                        errors.append(f"'_tests.{testType}' must have 'columns' and 'data'")

        # Validate sensitivities
        if '_sensitivities' in data:
            sensis = data['_sensitivities']
            if not isinstance(sensis, dict):
                errors.append("'_sensitivities' must be a dictionary")
            else:
                for riskClass, rcData in sensis.items():
                    if not isinstance(rcData, dict):
                        errors.append(f"'_sensitivities.{riskClass}' must be a dictionary")
                    elif 'columns' not in rcData or 'data' not in rcData:
                        errors.append(f"'_sensitivities.{riskClass}' must have 'columns' and 'data'")
                    elif riskClass not in FNetFieldType:
                        errors.append(f"Unknown risk class: {riskClass}")

        return len(errors) == 0, errors

    def validate_excel(self, excel_path: str) -> Tuple[bool, List[str]]:
        """
        Validate an FNetF Excel file.

        Args:
            excel_path: Path to Excel file

        Returns:
            Tuple of (is_valid: bool, errors: List[str])
        """
        excel_path = Path(excel_path)
        errors = []

        if not excel_path.exists():
            return False, [f"File not found: {excel_path}"]

        try:
            fnf = FNetF()
            result = fnf.load(str(excel_path))

            # Check version
            version = fnf._params.get('FNetFormatVersion')
            if version != FNetFormatVersion:
                errors.append(f"Incompatible FNetFormatVersion: expected {FNetFormatVersion}, got {version}")

            # Check for sensitivity data
            if not fnf._sensis:
                errors.append("No sensitivity data found")

        except Exception as e:
            errors.append(f"Failed to load Excel file: {e}")

        return len(errors) == 0, errors

    def compare(self, file1: str, file2: str) -> Tuple[bool, List[str]]:
        """
        Compare two FNetF files (Excel or JSON).

        Args:
            file1: Path to first file
            file2: Path to second file

        Returns:
            Tuple of (are_equal: bool, differences: List[str])
        """
        differences = []

        # Load both files
        fnf1 = FNetF()
        fnf2 = FNetF()

        try:
            fnf1.load(file1)
        except Exception as e:
            return False, [f"Failed to load {file1}: {e}"]

        try:
            fnf2.load(file2)
        except Exception as e:
            return False, [f"Failed to load {file2}: {e}"]

        # Compare parameters (excluding FileName which will differ)
        params1 = {k: v for k, v in fnf1._params.items() if k != 'FileName'}
        params2 = {k: v for k, v in fnf2._params.items() if k != 'FileName'}
        if params1 != params2:
            differences.append(f"Parameters differ: {set(params1.keys()) ^ set(params2.keys())}")

        # Compare risk classes
        rc1 = set(fnf1._sensis.keys())
        rc2 = set(fnf2._sensis.keys())
        if rc1 != rc2:
            differences.append(f"Risk classes differ: missing in file2: {rc1 - rc2}, missing in file1: {rc2 - rc1}")

        # Compare sensitivity data shapes
        for rc in rc1 & rc2:
            df1 = fnf1._sensis[rc]
            df2 = fnf2._sensis[rc]
            if len(df1) != len(df2):
                differences.append(f"{rc}: row count differs ({len(df1)} vs {len(df2)})")
            if set(df1.columns) != set(df2.columns):
                differences.append(f"{rc}: columns differ")

        # Compare tests
        tests1 = set(fnf1._tests.keys())
        tests2 = set(fnf2._tests.keys())
        if tests1 != tests2:
            differences.append(f"Test sets differ: {tests1 ^ tests2}")

        return len(differences) == 0, differences


def main():
    """Command-line interface for the converter."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Convert FNetF files between Excel and JSON formats'
    )
    parser.add_argument('input', help='Input file path')
    parser.add_argument('-o', '--output', help='Output file path (optional)')
    parser.add_argument('-v', '--validate', action='store_true',
                        help='Validate file without converting')
    parser.add_argument('--compare', metavar='FILE2',
                        help='Compare input file with another file')
    parser.add_argument('--compact', action='store_true',
                        help='Use compact JSON format (no pretty printing)')

    args = parser.parse_args()

    converter = FNetFConverter()
    input_path = Path(args.input)

    if not input_path.exists():
        print(f"Error: File not found: {input_path}")
        return 1

    # Compare mode
    if args.compare:
        print(f"Comparing: {args.input} vs {args.compare}")
        are_equal, differences = converter.compare(args.input, args.compare)
        if are_equal:
            print("✓ Files are equivalent")
            return 0
        else:
            print("✗ Files differ:")
            for diff in differences:
                print(f"  - {diff}")
            return 1

    # Determine format from extension
    if input_path.suffix.lower() == '.json':
        # JSON input
        if args.validate:
            is_valid, errors = converter.validate_json(str(input_path))
            if is_valid:
                print(f"✓ Valid FNetF JSON: {input_path}")
                return 0
            else:
                print(f"✗ Invalid FNetF JSON: {input_path}")
                for error in errors:
                    print(f"  - {error}")
                return 1
        else:
            # Convert to Excel
            try:
                converter.json_to_excel(str(input_path), args.output)
                return 0
            except Exception as e:
                print(f"Error: {e}")
                return 1

    elif input_path.suffix.lower() in ('.xlsx', '.xls'):
        # Excel input
        if args.validate:
            is_valid, errors = converter.validate_excel(str(input_path))
            if is_valid:
                print(f"✓ Valid FNetF Excel: {input_path}")
                return 0
            else:
                print(f"✗ Invalid FNetF Excel: {input_path}")
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
