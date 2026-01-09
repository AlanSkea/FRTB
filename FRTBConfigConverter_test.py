#!/usr/bin/env python3
"""
Test script for FRTBConfigConverter

Demonstrates usage and validates bidirectional conversion.
"""

import sys
import json
from pathlib import Path
from FRTBConfigConverter import FRTBConfigConverter


def test_excel_to_json_to_excel():
    """Test round-trip conversion: Excel → JSON → Excel"""
    print("=" * 70)
    print("TEST: Excel → JSON → Excel Round-Trip Conversion")
    print("=" * 70)

    converter = FRTBConfigConverter()

    # Use BCBS config for testing
    excel_original = Path('Configs/FRTBConfig_BCBS.xlsx')

    if not excel_original.exists():
        print(f"❌ Test file not found: {excel_original}")
        return False

    try:
        # Step 1: Excel → JSON
        print("\n📄 Step 1: Converting Excel to JSON...")
        json_file = Path('Configs/FRTBConfig_BCBS_test.json')
        config_dict = converter.excel_to_json(
            str(excel_original),
            str(json_file),
            pretty=True,
            indent=2
        )

        # Validate the JSON
        print("\n✓ Validating generated JSON...")
        is_valid, errors = converter.validate_json(str(json_file))
        if not is_valid:
            print("❌ JSON validation failed:")
            for error in errors:
                print(f"  - {error}")
            return False

        print("✓ JSON validation passed")

        # Step 2: JSON → Excel
        print("\n📄 Step 2: Converting JSON back to Excel...")
        excel_recreated = Path('Configs/FRTBConfig_BCBS_test.xlsx')
        converter.json_to_excel(
            str(json_file),
            str(excel_recreated)
        )

        # Validate the Excel
        print("\n✓ Validating generated Excel...")
        is_valid, errors = converter.validate_excel(str(excel_recreated))
        if not is_valid:
            print("❌ Excel validation failed:")
            for error in errors:
                print(f"  - {error}")
            return False

        print("✓ Excel validation passed")

        # Step 3: Compare by converting back to JSON
        print("\n📄 Step 3: Converting recreated Excel to JSON for comparison...")
        json_file2 = Path('Configs/FRTBConfig_BCBS_test2.json')
        config_dict2 = converter.excel_to_json(
            str(excel_recreated),
            str(json_file2),
            pretty=True,
            indent=2
        )

        # Compare the two JSON files (should be identical)
        print("\n✓ Comparing JSON files...")
        differences = compare_configs(config_dict, config_dict2)

        if differences:
            print(f"❌ Found {len(differences)} difference(s):")
            for diff in differences[:10]:  # Show first 10
                print(f"  - {diff}")
            return False

        print("✓ JSON files are identical - round-trip successful!")

        # Cleanup test files
        print("\n🧹 Cleaning up test files...")
        json_file.unlink()
        json_file2.unlink()
        excel_recreated.unlink()

        print("\n" + "=" * 70)
        print("✅ ALL TESTS PASSED")
        print("=" * 70)
        return True

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


def compare_configs(config1, config2, path=""):
    """Recursively compare two config dictionaries."""
    differences = []

    # Check keys (ignore 'name' field as it's optional metadata)
    keys1 = set(config1.keys()) - {'name'}
    keys2 = set(config2.keys()) - {'name'}

    if keys1 != keys2:
        missing_in_2 = keys1 - keys2
        missing_in_1 = keys2 - keys1
        if missing_in_2:
            differences.append(f"{path}: Keys in config1 but not config2: {missing_in_2}")
        if missing_in_1:
            differences.append(f"{path}: Keys in config2 but not config1: {missing_in_1}")
        return differences

    # Compare values
    for key in keys1:
        new_path = f"{path}.{key}" if path else key
        val1 = config1[key]
        val2 = config2[key]

        if isinstance(val1, dict) and isinstance(val2, dict):
            differences.extend(compare_configs(val1, val2, new_path))
        elif isinstance(val1, list) and isinstance(val2, list):
            if len(val1) != len(val2):
                differences.append(f"{new_path}: List length differs ({len(val1)} vs {len(val2)})")
            else:
                for i, (v1, v2) in enumerate(zip(val1, val2)):
                    if v1 != v2:
                        # Allow small floating point differences
                        if isinstance(v1, (int, float)) and isinstance(v2, (int, float)):
                            if abs(v1 - v2) > 1e-10:
                                differences.append(f"{new_path}[{i}]: {v1} != {v2}")
                        else:
                            differences.append(f"{new_path}[{i}]: {v1} != {v2}")
        else:
            if val1 != val2:
                # Allow small floating point differences
                if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
                    if abs(val1 - val2) > 1e-10:
                        differences.append(f"{new_path}: {val1} != {val2}")
                else:
                    differences.append(f"{new_path}: {val1} != {val2}")

    return differences


def show_json_sample():
    """Show a sample of the JSON format."""
    print("\n" + "=" * 70)
    print("JSON Format Sample")
    print("=" * 70)

    converter = FRTBConfigConverter()
    excel_file = Path('Configs/FRTBConfig_BCBS.xlsx')

    if not excel_file.exists():
        print(f"❌ Config file not found: {excel_file}")
        return

    json_file = Path('Configs/FRTBConfig_BCBS_sample.json')
    config = converter.excel_to_json(str(excel_file), str(json_file))

    # Show a sample from MS_FX risk class
    if 'MS_FX' in config:
        print("\n📋 Sample from MS_FX risk class:\n")
        sample = {
            'MS_FX': {
                k: config['MS_FX'][k]
                for k in list(config['MS_FX'].keys())[:3]
            }
        }
        print(json.dumps(sample, indent=2))

    print("\n💡 Key features of the JSON format:")
    print("  • Self-documenting: includes type metadata")
    print("  • Scalars: {value, type: 'scalar', dtype}")
    print("  • Lists: {value: [...], type: 'list', dtype, name}")
    print("  • DataFrames: {value: {...}, type: 'dataframe', columns, dtypes, index}")
    print("  • No need for _riskClassConfigKeyTypes metadata")
    print("  • No need for _riskClassKeyDataType metadata")

    # Cleanup
    json_file.unlink()
    print("\n" + "=" * 70)


def show_usage_examples():
    """Show usage examples."""
    print("\n" + "=" * 70)
    print("Usage Examples")
    print("=" * 70)

    print("\n1️⃣  Convert Excel to JSON:")
    print("   python FRTBConfigConverter.py Configs/FRTBConfig_BCBS.xlsx")
    print("   python FRTBConfigConverter.py Configs/FRTBConfig_BCBS.xlsx -o output.json")

    print("\n2️⃣  Convert JSON to Excel:")
    print("   python FRTBConfigConverter.py FRTBConfig_BCBS.json")
    print("   python FRTBConfigConverter.py FRTBConfig_BCBS.json -o output.xlsx")

    print("\n3️⃣  Validate files:")
    print("   python FRTBConfigConverter.py Configs/FRTBConfig_BCBS.xlsx --validate")
    print("   python FRTBConfigConverter.py config.json --validate")

    print("\n4️⃣  Use in Python code:")
    print("""
    from FRTBConfigConverter import FRTBConfigConverter

    converter = FRTBConfigConverter()

    # Excel → JSON
    config = converter.excel_to_json('config.xlsx', 'config.json')

    # JSON → Excel
    converter.json_to_excel('config.json', 'config.xlsx')

    # Validate
    is_valid, errors = converter.validate_json('config.json')
    """)

    print("\n" + "=" * 70)


def main():
    """Run tests and examples."""
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 20 + "FRTB Config Converter Test" + " " * 22 + "║")
    print("╚" + "═" * 68 + "╝")

    # Show usage examples
    show_usage_examples()

    # Show JSON format sample
    show_json_sample()

    # Run round-trip test
    print("\n")
    success = test_excel_to_json_to_excel()

    if success:
        print("\n✅ Converter is working correctly!")
        return 0
    else:
        print("\n❌ Tests failed - please review errors above")
        return 1


if __name__ == '__main__':
    sys.exit(main())
