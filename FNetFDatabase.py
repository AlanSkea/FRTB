"""
SQLite database support for frtb.net Format (FNetF) files

Copyright (C) 2024-2025 frtb.net limited

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

import sqlite3
import pandas as pd
import os
import json
from contextlib import contextmanager

from FNetF import FNetFieldType, FNetFormatVersion

# Map FNetF types to SQLite types
_SQLITE_TYPE_MAP = {
    'str': 'TEXT',
    'object': 'TEXT',  # nullable string
    'float64': 'REAL',
    'int64': 'INTEGER',
    'bool': 'INTEGER',  # SQLite stores bools as 0/1
}

# Map SQLite types back to pandas types for reading
_PANDAS_TYPE_MAP = {
    'TEXT': 'str',
    'REAL': 'float64',
    'INTEGER': 'int64',
}


class FNetFDatabase:
    """
    SQLite database handler for FNetF data.

    Provides functionality to:
    - Create and write FNetF data to SQLite databases
    - Read FNetF data from SQLite databases
    - Support lazy loading of sensitivity data for memory efficiency

    Database Schema:
    - parameters: Key-value pairs for file metadata
    - risk_groups: Unique (RiskGroup, RiskSubGroup) combinations
    - sensitivities_<RiskClass>: One table per risk class with appropriate columns
    - tests_<TestType>: One table per test type (ObligorTests, FactorTests, etc.)
    - schema_info: Schema version and field type documentation
    """

    def __init__(self, db_path=None):
        """
        Initialize the database handler.

        Args:
            db_path: Path to the SQLite database file. If None, must be set before operations.
        """
        self._db_path = db_path
        self._conn = None
        self._lazy_mode = False
        self._cached_risk_classes = None
        self._cached_params = None

    @contextmanager
    def _get_connection(self):
        """Context manager for database connections."""
        if self._conn is not None:
            # Reuse existing connection (for lazy mode)
            yield self._conn
        else:
            conn = sqlite3.connect(self._db_path)
            conn.row_factory = sqlite3.Row
            try:
                yield conn
            finally:
                conn.close()

    def _open_persistent_connection(self):
        """Open a persistent connection for lazy loading mode."""
        if self._conn is None:
            self._conn = sqlite3.connect(self._db_path)
            self._conn.row_factory = sqlite3.Row
            self._lazy_mode = True

    def _close_persistent_connection(self):
        """Close the persistent connection."""
        if self._conn is not None:
            self._conn.close()
            self._conn = None
            self._lazy_mode = False
            self._cached_risk_classes = None
            self._cached_params = None

    def close(self):
        """Close any open database connection."""
        self._close_persistent_connection()

    def __enter__(self):
        """Support context manager protocol for lazy loading."""
        self._open_persistent_connection()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Close connection when exiting context."""
        self.close()
        return False

    def _get_table_name(self, prefix, name):
        """Generate a valid SQLite table name from prefix and name."""
        # Replace characters that might cause issues in table names
        safe_name = name.replace('-', '_').replace('+', 'plus').replace('/', '_')
        return f"{prefix}_{safe_name}"

    def _get_sensitivity_table_name(self, risk_class):
        """Get the table name for a risk class."""
        return self._get_table_name('sensitivities', risk_class)

    def _get_test_table_name(self, test_type):
        """Get the table name for a test type."""
        return self._get_table_name('tests', test_type)

    def _create_schema(self, conn):
        """Create the database schema."""
        cursor = conn.cursor()

        # Parameters table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS parameters (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')

        # Risk groups table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS risk_groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                risk_group TEXT NOT NULL,
                risk_sub_group TEXT NOT NULL,
                UNIQUE(risk_group, risk_sub_group)
            )
        ''')

        # Schema info table for version and metadata
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS schema_info (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')

        # Risk class registry - tracks which risk class tables exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS risk_class_registry (
                risk_class TEXT PRIMARY KEY,
                row_count INTEGER,
                columns TEXT
            )
        ''')

        # Test registry - tracks which test tables exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS test_registry (
                test_type TEXT PRIMARY KEY,
                row_count INTEGER,
                columns TEXT
            )
        ''')

        # Store schema version
        cursor.execute('''
            INSERT OR REPLACE INTO schema_info (key, value) VALUES (?, ?)
        ''', ('FNetFormatVersion', FNetFormatVersion))

        cursor.execute('''
            INSERT OR REPLACE INTO schema_info (key, value) VALUES (?, ?)
        ''', ('DatabaseSchemaVersion', '1.0'))

        conn.commit()

    def _create_sensitivity_table(self, conn, risk_class, extra_columns=None):
        """
        Create a table for a specific risk class.

        Args:
            conn: Database connection
            risk_class: The risk class name
            extra_columns: Dict of additional column names to types (beyond FNetFieldType)
        """
        table_name = self._get_sensitivity_table_name(risk_class)

        # Build column definitions
        columns = ['id INTEGER PRIMARY KEY AUTOINCREMENT']
        columns.append('sensitivity_id TEXT UNIQUE NOT NULL')

        # Add standard FNetFieldType columns
        if risk_class in FNetFieldType:
            for col_name, col_type in FNetFieldType[risk_class].items():
                sqlite_type = _SQLITE_TYPE_MAP.get(col_type, 'TEXT')
                columns.append(f'"{col_name}" {sqlite_type}')

        # Add any extra columns
        if extra_columns:
            for col_name, col_type in extra_columns.items():
                if col_name not in ['Sensitivity ID'] and col_name not in FNetFieldType.get(risk_class, {}):
                    sqlite_type = _SQLITE_TYPE_MAP.get(col_type, 'TEXT')
                    columns.append(f'"{col_name}" {sqlite_type}')

        cursor = conn.cursor()
        cursor.execute(f'DROP TABLE IF EXISTS "{table_name}"')
        cursor.execute(f'CREATE TABLE "{table_name}" ({", ".join(columns)})')

        # Create indexes for common query patterns
        cursor.execute(f'CREATE INDEX IF NOT EXISTS "idx_{table_name}_risk_group" ON "{table_name}" ("RiskGroup")')
        cursor.execute(f'CREATE INDEX IF NOT EXISTS "idx_{table_name}_risk_sub_group" ON "{table_name}" ("RiskGroup", "RiskSubGroup")')

        conn.commit()

    def _create_test_table(self, conn, test_type, benchmark_columns):
        """
        Create a table for a specific test type.

        Args:
            conn: Database connection
            test_type: The test type name (e.g., 'CapitalTests')
            benchmark_columns: List of benchmark column names
        """
        table_name = self._get_test_table_name(test_type)

        columns = [
            'id INTEGER PRIMARY KEY AUTOINCREMENT',
            'test_id TEXT UNIQUE NOT NULL',
            'risk_group TEXT',
            'risk_sub_group TEXT',
            'risk_class TEXT',
            'description TEXT',
            'sensitivity_ids TEXT',
        ]

        # Add benchmark columns
        for col in benchmark_columns:
            columns.append(f'"{col}" REAL')

        cursor = conn.cursor()
        cursor.execute(f'DROP TABLE IF EXISTS "{table_name}"')
        cursor.execute(f'CREATE TABLE "{table_name}" ({", ".join(columns)})')

        # Create index for common queries
        cursor.execute(f'CREATE INDEX IF NOT EXISTS "idx_{table_name}_risk_class" ON "{table_name}" ("risk_class")')

        conn.commit()

    def create_database(self, db_path=None):
        """
        Create a new empty database with the FNetF schema.

        Args:
            db_path: Path for the new database. Uses instance path if not provided.
        """
        if db_path:
            self._db_path = db_path

        if not self._db_path:
            raise ValueError("Database path not specified")

        # Remove existing database if present
        if os.path.exists(self._db_path):
            os.remove(self._db_path)

        with self._get_connection() as conn:
            self._create_schema(conn)

    def write_from_fnetf(self, fnetf, db_path=None):
        """
        Write FNetF data to a SQLite database.

        Args:
            fnetf: An FNetF instance with loaded data
            db_path: Path for the database. Uses instance path if not provided.
        """
        if db_path:
            self._db_path = db_path

        if not self._db_path:
            raise ValueError("Database path not specified")

        # Create fresh database
        self.create_database()

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Write parameters
            params = fnetf.getParams()
            for key, value in params.items():
                cursor.execute(
                    'INSERT OR REPLACE INTO parameters (key, value) VALUES (?, ?)',
                    (key, str(value) if value is not None else None)
                )

            # Write risk groups
            for risk_group, risk_sub_group in fnetf.getRiskGroups():
                cursor.execute(
                    'INSERT OR IGNORE INTO risk_groups (risk_group, risk_sub_group) VALUES (?, ?)',
                    (risk_group, risk_sub_group)
                )

            # Write sensitivity data for each risk class
            for risk_class in fnetf.getRiskClasses():
                df = fnetf.getRiskClassData(risk_class)
                if df is not None and not df.empty:
                    self._write_sensitivity_data(conn, risk_class, df)

            # Write test data
            for test_type in fnetf.getUnitTestSets():
                df = fnetf.getUnitTests(test_type)
                if df is not None and not df.empty:
                    self._write_test_data(conn, test_type, df)

            conn.commit()

    def _write_sensitivity_data(self, conn, risk_class, df):
        """Write sensitivity data for a risk class to the database."""
        # Determine extra columns beyond standard FNetFieldType
        standard_cols = set(FNetFieldType.get(risk_class, {}).keys()) | {'Sensitivity ID'}
        extra_cols = {col: self._infer_dtype(df[col]) for col in df.columns if col not in standard_cols}

        # Create the table
        self._create_sensitivity_table(conn, risk_class, extra_cols)

        table_name = self._get_sensitivity_table_name(risk_class)

        # Prepare column list (excluding auto-increment id)
        all_cols = ['Sensitivity ID'] + list(FNetFieldType.get(risk_class, {}).keys())
        all_cols.extend(extra_cols.keys())
        existing_cols = [col for col in all_cols if col in df.columns]

        # Map column names to database column names
        db_cols = ['sensitivity_id'] + [col for col in existing_cols if col != 'Sensitivity ID']

        # Prepare insert statement
        placeholders = ', '.join(['?' for _ in db_cols])
        col_names = ', '.join([f'"{col}"' if col != 'sensitivity_id' else col for col in db_cols])
        insert_sql = f'INSERT INTO "{table_name}" ({col_names}) VALUES ({placeholders})'

        # Insert data
        cursor = conn.cursor()
        for _, row in df.iterrows():
            values = [row['Sensitivity ID']]
            for col in existing_cols:
                if col != 'Sensitivity ID':
                    val = row[col]
                    # Convert numpy types to Python types
                    if pd.isna(val):
                        values.append(None)
                    elif hasattr(val, 'item'):
                        values.append(val.item())
                    else:
                        values.append(val)
            cursor.execute(insert_sql, values)

        # Register this risk class
        columns_json = json.dumps(existing_cols)
        cursor.execute(
            'INSERT OR REPLACE INTO risk_class_registry (risk_class, row_count, columns) VALUES (?, ?, ?)',
            (risk_class, len(df), columns_json)
        )

        conn.commit()

    def _write_test_data(self, conn, test_type, df):
        """Write test data for a test type to the database."""
        # Identify benchmark columns
        standard_cols = ['Test ID', 'RiskGroup', 'RiskSubGroup', 'RiskClass', 'Description', 'Sensitivity IDs']
        benchmark_cols = [col for col in df.columns if col not in standard_cols]

        # Create the table
        self._create_test_table(conn, test_type, benchmark_cols)

        table_name = self._get_test_table_name(test_type)

        # Prepare insert statement
        db_cols = ['test_id', 'risk_group', 'risk_sub_group', 'risk_class', 'description', 'sensitivity_ids']
        db_cols.extend([f'"{col}"' for col in benchmark_cols])

        placeholders = ', '.join(['?' for _ in db_cols])
        col_names = ', '.join(db_cols)
        insert_sql = f'INSERT INTO "{table_name}" ({col_names}) VALUES ({placeholders})'

        # Insert data
        cursor = conn.cursor()
        for _, row in df.iterrows():
            values = [
                row.get('Test ID'),
                row.get('RiskGroup'),
                row.get('RiskSubGroup'),
                row.get('RiskClass'),
                row.get('Description'),
                row.get('Sensitivity IDs'),
            ]
            for col in benchmark_cols:
                val = row.get(col)
                if pd.isna(val):
                    values.append(None)
                elif hasattr(val, 'item'):
                    values.append(val.item())
                else:
                    values.append(val)
            cursor.execute(insert_sql, values)

        # Register this test type
        all_cols = standard_cols + benchmark_cols
        existing_cols = [col for col in all_cols if col in df.columns]
        columns_json = json.dumps(existing_cols)
        cursor.execute(
            'INSERT OR REPLACE INTO test_registry (test_type, row_count, columns) VALUES (?, ?, ?)',
            (test_type, len(df), columns_json)
        )

        conn.commit()

    def _infer_dtype(self, series):
        """Infer the FNetF dtype from a pandas Series."""
        dtype = series.dtype
        if dtype == 'object':
            return 'str'
        elif dtype == 'bool':
            return 'bool'
        elif dtype == 'int64':
            return 'int64'
        elif dtype == 'float64':
            return 'float64'
        else:
            return 'str'

    # -------------------------------------------------------------------------
    # Read methods
    # -------------------------------------------------------------------------

    def load_to_fnetf(self, fnetf, db_path=None):
        """
        Load all data from a SQLite database into an FNetF instance.

        Args:
            fnetf: An FNetF instance to load data into
            db_path: Path to the database. Uses instance path if not provided.
        """
        if db_path:
            self._db_path = db_path

        if not self._db_path:
            raise ValueError("Database path not specified")

        if not os.path.exists(self._db_path):
            raise FileNotFoundError(f"Database '{self._db_path}' not found")

        with self._get_connection() as conn:
            # Load parameters
            params = self._read_parameters(conn)
            for key, value in params.items():
                fnetf.setParam(key, value)

            # Load sensitivity data
            risk_classes = self._get_risk_classes(conn)
            for risk_class in risk_classes:
                df = self._read_sensitivity_data(conn, risk_class)
                if df is not None and not df.empty:
                    fnetf.setRiskClassData(risk_class, df)

            # Load test data
            test_types = self._get_test_types(conn)
            for test_type in test_types:
                df = self._read_test_data(conn, test_type)
                if df is not None and not df.empty:
                    fnetf.setUnitTests(test_type, df)

            # Rebuild risk groups
            fnetf._riskGroups = set()
            for risk_class in fnetf.getRiskClasses():
                df = fnetf.getRiskClassData(risk_class)
                if df is not None and not df.empty:
                    for _, r in df[['RiskGroup', 'RiskSubGroup']].drop_duplicates().iterrows():
                        fnetf._riskGroups.add((r['RiskGroup'], r['RiskSubGroup']))

    def _read_parameters(self, conn):
        """Read all parameters from the database."""
        cursor = conn.cursor()
        cursor.execute('SELECT key, value FROM parameters')
        return {row['key']: row['value'] for row in cursor.fetchall()}

    def _get_risk_classes(self, conn):
        """Get list of risk classes stored in the database."""
        cursor = conn.cursor()
        cursor.execute('SELECT risk_class FROM risk_class_registry')
        return [row['risk_class'] for row in cursor.fetchall()]

    def _get_test_types(self, conn):
        """Get list of test types stored in the database."""
        cursor = conn.cursor()
        cursor.execute('SELECT test_type FROM test_registry')
        return [row['test_type'] for row in cursor.fetchall()]

    def _read_sensitivity_data(self, conn, risk_class, where_clause=None, params=None):
        """
        Read sensitivity data for a risk class from the database.

        Args:
            conn: Database connection
            risk_class: The risk class to read
            where_clause: Optional WHERE clause for filtering (without 'WHERE' keyword)
            params: Parameters for the WHERE clause

        Returns:
            DataFrame with the sensitivity data
        """
        table_name = self._get_sensitivity_table_name(risk_class)

        # Get column info
        cursor = conn.cursor()
        cursor.execute('SELECT columns FROM risk_class_registry WHERE risk_class = ?', (risk_class,))
        row = cursor.fetchone()
        if not row:
            return None

        columns = json.loads(row['columns'])

        # Build SELECT statement
        db_cols = ['sensitivity_id AS "Sensitivity ID"']
        for col in columns:
            if col != 'Sensitivity ID':
                db_cols.append(f'"{col}"')

        sql = f'SELECT {", ".join(db_cols)} FROM "{table_name}"'
        if where_clause:
            sql += f' WHERE {where_clause}'

        # Execute query
        df = pd.read_sql_query(sql, conn, params=params)

        # Apply type conversions
        if risk_class in FNetFieldType:
            typemap = {}
            for col, dtype in FNetFieldType[risk_class].items():
                if col in df.columns:
                    if dtype == 'bool':
                        df[col] = df[col].apply(lambda x: bool(x) if x is not None else False)
                    elif dtype != 'object':
                        df[col] = df[col].fillna(0 if dtype in ('int64', 'float64') else '')
                    typemap[col] = dtype
            df = df.astype(typemap)

        return df

    def _read_test_data(self, conn, test_type):
        """Read test data for a test type from the database."""
        table_name = self._get_test_table_name(test_type)

        # Get column info
        cursor = conn.cursor()
        cursor.execute('SELECT columns FROM test_registry WHERE test_type = ?', (test_type,))
        row = cursor.fetchone()
        if not row:
            return None

        columns = json.loads(row['columns'])

        # Build column mapping for SELECT
        col_map = {
            'Test ID': 'test_id AS "Test ID"',
            'RiskGroup': 'risk_group AS "RiskGroup"',
            'RiskSubGroup': 'risk_sub_group AS "RiskSubGroup"',
            'RiskClass': 'risk_class AS "RiskClass"',
            'Description': 'description AS "Description"',
            'Sensitivity IDs': 'sensitivity_ids AS "Sensitivity IDs"',
        }

        db_cols = []
        for col in columns:
            if col in col_map:
                db_cols.append(col_map[col])
            else:
                db_cols.append(f'"{col}"')

        sql = f'SELECT {", ".join(db_cols)} FROM "{table_name}"'
        df = pd.read_sql_query(sql, conn)

        # Convert benchmark columns to float64
        for col in df.columns:
            if col.startswith('Benchmark_'):
                df[col] = df[col].astype('float64')

        return df

    # -------------------------------------------------------------------------
    # Lazy loading methods
    # -------------------------------------------------------------------------

    def get_parameters(self):
        """
        Get parameters from the database (lazy loading compatible).

        Returns:
            Dict of parameter key-value pairs
        """
        if self._cached_params is not None:
            return self._cached_params

        with self._get_connection() as conn:
            params = self._read_parameters(conn)
            if self._lazy_mode:
                self._cached_params = params
            return params

    def get_risk_classes(self):
        """
        Get list of risk classes in the database (lazy loading compatible).

        Returns:
            List of risk class names
        """
        if self._cached_risk_classes is not None:
            return self._cached_risk_classes

        with self._get_connection() as conn:
            risk_classes = self._get_risk_classes(conn)
            if self._lazy_mode:
                self._cached_risk_classes = risk_classes
            return risk_classes

    def get_risk_class_info(self, risk_class):
        """
        Get metadata about a risk class without loading the full data.

        Args:
            risk_class: The risk class name

        Returns:
            Dict with 'row_count' and 'columns' keys
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT row_count, columns FROM risk_class_registry WHERE risk_class = ?',
                (risk_class,)
            )
            row = cursor.fetchone()
            if row:
                return {
                    'row_count': row['row_count'],
                    'columns': json.loads(row['columns'])
                }
            return None

    def get_sensitivity_data(self, risk_class, risk_group=None, risk_sub_group=None,
                            sensitivity_ids=None, limit=None, offset=None):
        """
        Get sensitivity data with optional filtering (lazy loading compatible).

        This method supports lazy loading by allowing filtered queries instead
        of loading all data at once.

        Args:
            risk_class: The risk class to query
            risk_group: Optional filter by RiskGroup
            risk_sub_group: Optional filter by RiskSubGroup (requires risk_group)
            sensitivity_ids: Optional list of specific Sensitivity IDs to fetch
            limit: Optional maximum number of rows to return
            offset: Optional number of rows to skip

        Returns:
            DataFrame with the requested sensitivity data
        """
        where_parts = []
        params = []

        if risk_group is not None:
            where_parts.append('"RiskGroup" = ?')
            params.append(risk_group)

            if risk_sub_group is not None:
                where_parts.append('"RiskSubGroup" = ?')
                params.append(risk_sub_group)

        if sensitivity_ids is not None:
            placeholders = ', '.join(['?' for _ in sensitivity_ids])
            where_parts.append(f'sensitivity_id IN ({placeholders})')
            params.extend(sensitivity_ids)

        where_clause = ' AND '.join(where_parts) if where_parts else None

        # Add LIMIT and OFFSET to query
        suffix = ''
        if limit is not None:
            suffix += f' LIMIT {int(limit)}'
        if offset is not None:
            suffix += f' OFFSET {int(offset)}'

        with self._get_connection() as conn:
            table_name = self._get_sensitivity_table_name(risk_class)

            # Get column info
            cursor = conn.cursor()
            cursor.execute('SELECT columns FROM risk_class_registry WHERE risk_class = ?', (risk_class,))
            row = cursor.fetchone()
            if not row:
                return None

            columns = json.loads(row['columns'])

            # Build SELECT statement
            db_cols = ['sensitivity_id AS "Sensitivity ID"']
            for col in columns:
                if col != 'Sensitivity ID':
                    db_cols.append(f'"{col}"')

            sql = f'SELECT {", ".join(db_cols)} FROM "{table_name}"'
            if where_clause:
                sql += f' WHERE {where_clause}'
            sql += suffix

            # Execute query
            df = pd.read_sql_query(sql, conn, params=params if params else None)

            # Apply type conversions
            if risk_class in FNetFieldType:
                typemap = {}
                for col, dtype in FNetFieldType[risk_class].items():
                    if col in df.columns:
                        if dtype == 'bool':
                            df[col] = df[col].apply(lambda x: bool(x) if x is not None else False)
                        elif dtype != 'object':
                            df[col] = df[col].fillna(0 if dtype in ('int64', 'float64') else '')
                        typemap[col] = dtype
                df = df.astype(typemap)

            return df

    def get_sensitivity_count(self, risk_class, risk_group=None, risk_sub_group=None):
        """
        Get the count of sensitivities matching the filter criteria.

        Args:
            risk_class: The risk class to query
            risk_group: Optional filter by RiskGroup
            risk_sub_group: Optional filter by RiskSubGroup (requires risk_group)

        Returns:
            Integer count of matching rows
        """
        table_name = self._get_sensitivity_table_name(risk_class)

        where_parts = []
        params = []

        if risk_group is not None:
            where_parts.append('"RiskGroup" = ?')
            params.append(risk_group)

            if risk_sub_group is not None:
                where_parts.append('"RiskSubGroup" = ?')
                params.append(risk_sub_group)

        where_clause = ' AND '.join(where_parts) if where_parts else ''

        sql = f'SELECT COUNT(*) as cnt FROM "{table_name}"'
        if where_clause:
            sql += f' WHERE {where_clause}'

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            row = cursor.fetchone()
            return row['cnt'] if row else 0

    def get_risk_groups(self):
        """
        Get all (RiskGroup, RiskSubGroup) pairs from the database.

        Returns:
            List of (risk_group, risk_sub_group) tuples
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT risk_group, risk_sub_group FROM risk_groups')
            return [(row['risk_group'], row['risk_sub_group']) for row in cursor.fetchall()]

    def get_test_types(self):
        """
        Get list of test types in the database.

        Returns:
            List of test type names
        """
        with self._get_connection() as conn:
            return self._get_test_types(conn)

    def get_test_data(self, test_type, test_id=None, risk_class=None):
        """
        Get test data with optional filtering.

        Args:
            test_type: The test type to query
            test_id: Optional specific test ID to fetch
            risk_class: Optional filter by RiskClass

        Returns:
            DataFrame with the requested test data
        """
        table_name = self._get_test_table_name(test_type)

        where_parts = []
        params = []

        if test_id is not None:
            where_parts.append('test_id = ?')
            params.append(test_id)

        if risk_class is not None:
            where_parts.append('risk_class = ?')
            params.append(risk_class)

        where_clause = ' AND '.join(where_parts) if where_parts else None

        with self._get_connection() as conn:
            # Get column info
            cursor = conn.cursor()
            cursor.execute('SELECT columns FROM test_registry WHERE test_type = ?', (test_type,))
            row = cursor.fetchone()
            if not row:
                return None

            columns = json.loads(row['columns'])

            # Build column mapping for SELECT
            col_map = {
                'Test ID': 'test_id AS "Test ID"',
                'RiskGroup': 'risk_group AS "RiskGroup"',
                'RiskSubGroup': 'risk_sub_group AS "RiskSubGroup"',
                'RiskClass': 'risk_class AS "RiskClass"',
                'Description': 'description AS "Description"',
                'Sensitivity IDs': 'sensitivity_ids AS "Sensitivity IDs"',
            }

            db_cols = []
            for col in columns:
                if col in col_map:
                    db_cols.append(col_map[col])
                else:
                    db_cols.append(f'"{col}"')

            sql = f'SELECT {", ".join(db_cols)} FROM "{table_name}"'
            if where_clause:
                sql += f' WHERE {where_clause}'

            df = pd.read_sql_query(sql, conn, params=params if params else None)

            # Convert benchmark columns to float64
            for col in df.columns:
                if col.startswith('Benchmark_'):
                    df[col] = df[col].astype('float64')

            return df


# Convenience functions for common operations

def fnetf_to_sqlite(fnetf, db_path):
    """
    Write an FNetF instance to a SQLite database.

    Args:
        fnetf: An FNetF instance with loaded data
        db_path: Path for the output database file
    """
    db = FNetFDatabase()
    db.write_from_fnetf(fnetf, db_path)


def sqlite_to_fnetf(db_path, fnetf):
    """
    Load a SQLite database into an FNetF instance.

    Args:
        db_path: Path to the input database file
        fnetf: An FNetF instance to load data into
    """
    db = FNetFDatabase()
    db.load_to_fnetf(fnetf, db_path)


if __name__ == '__main__':
    # Example usage and basic test
    import sys

    # Test with an existing FNetF file if provided
    if len(sys.argv) > 1:
        from FNetF import FNetF

        input_file = sys.argv[1]
        db_file = input_file.rsplit('.', 1)[0] + '.db'

        print(f"Loading {input_file}...")
        fnf = FNetF()
        fnf.load(input_file)

        print(f"Writing to {db_file}...")
        fnetf_to_sqlite(fnf, db_file)

        print(f"Reading back from {db_file}...")
        fnf2 = FNetF()
        sqlite_to_fnetf(db_file, fnf2)

        print(f"Parameters match: {fnf.getParams() == fnf2.getParams()}")
        print(f"Risk classes match: {set(fnf.getRiskClasses()) == set(fnf2.getRiskClasses())}")

        # Test lazy loading
        print("\nTesting lazy loading...")
        with FNetFDatabase(db_file) as db:
            print(f"Risk classes: {db.get_risk_classes()}")
            for rc in db.get_risk_classes():
                info = db.get_risk_class_info(rc)
                print(f"  {rc}: {info['row_count']} rows")

                # Get just first 5 rows
                df = db.get_sensitivity_data(rc, limit=5)
                print(f"    First 5 rows: {len(df)} returned")
    else:
        print("Usage: python FNetFDatabase.py <fnetf_file.xlsx|.json>")
        print("\nThis will create a .db file and test round-trip conversion.")
