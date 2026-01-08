"""
Some definitions to help loading and storing frtb.net Format (FNetF) files

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

import pandas as pd
import numpy as np
import os
import json

import FRTBUtils as FNU

FNetFormatVersion = '3.0'


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

FNetFieldType = {
    'MS_IRDelta' : {
        'RiskGroup'                     : 'str',
        'RiskSubGroup'                  : 'str',
        'RiskClass'                     : 'str',
        'Bucket'                        : 'str',
        'CurveType'                     : 'str',
        'Curve'                         : 'str',
        'Tenor'                         : 'str',
        'Sensitivity'                   : 'float64',
    },
    'MS_IRVega' : {
        'RiskGroup'                     : 'str',
        'RiskSubGroup'                  : 'str',
        'RiskClass'                     : 'str',
        'Bucket'                        : 'str',
        'CurveType'                     : 'str',
        'Curve'                         : 'str',            # needed for EU reporting
        'OptionMaturity'                : 'str',
        'UnderlyingResidualMaturity'    : 'str',
        'Sensitivity'                   : 'float64',
    },
    'MS_IRCurvature' : {
        'RiskGroup'                     : 'str',
        'RiskSubGroup'                  : 'str',
        'RiskClass'                     : 'str',
        'Bucket'                        : 'str',
        'CVR+'                          : 'float64',
        'CVR-'                          : 'float64',
    },
    'MS_CRDelta' : {
        'RiskGroup'                     : 'str',
        'RiskSubGroup'                  : 'str',
        'RiskClass'                     : 'str',
        'Bucket'                        : 'str',
        'SubBucket'                     : 'str',
        'CreditName'                    : 'str',
        'CurveType'                     : 'str',
        'Rating'                        : 'str',
        'Tenor'                         : 'str',
        'Sensitivity'                   : 'float64',
    },
    'MS_CRVega': {
        'RiskGroup'                     : 'str',
        'RiskSubGroup'                  : 'str',
        'RiskClass'                     : 'str',
        'Bucket'                        : 'str',
        'SubBucket'                     : 'str',
        'CreditName'                    : 'str',
        'Rating'                        : 'str',            # needed for EU reporting
        'OptionMaturity'                : 'str',
        'Sensitivity'                   : 'float64',
    },
    'MS_CRCurvature' : {
        'RiskGroup'                     : 'str',
        'RiskSubGroup'                  : 'str',
        'RiskClass'                     : 'str',
        'Bucket'                        : 'str',
        'SubBucket'                     : 'str',
        'CreditName'                    : 'str',
        'Rating'                        : 'str',            # needed for EU reporting
        'CVR+'                          : 'float64',
        'CVR-'                          : 'float64',
    },
    'MS_CCDelta' : {
        'RiskGroup'                     : 'str',
        'RiskSubGroup'                  : 'str',
        'RiskClass'                     : 'str',
        'Bucket'                        : 'str',
        'SubBucket'                     : 'str',
        'Underlier'                     : 'str',
        'CurveType'                     : 'str',
        'Tenor'                         : 'str',
        'Sensitivity'                   : 'float64',
    },
    'MS_CCVega' : {
        'RiskGroup'                     : 'str',
        'RiskSubGroup'                  : 'str',
        'RiskClass'                     : 'str',
        'Bucket'                        : 'str',
        'SubBucket'                     : 'str',
        'Underlier'                     : 'str',
        'OptionMaturity'                : 'str',
        'Sensitivity'                   : 'float64',
    },
    'MS_CCCurvature' : {
        'RiskGroup'                     : 'str',
        'RiskSubGroup'                  : 'str',
        'RiskClass'                     : 'str',
        'Bucket'                        : 'str',
        'SubBucket'                     : 'str',
        'Underlier'                     : 'str',
        'CVR+'                          : 'float64',
        'CVR-'                          : 'float64',
    },
    'MS_CSDelta' : {
        'RiskGroup'                     : 'str',
        'RiskSubGroup'                  : 'str',
        'RiskClass'                     : 'str',
        'Bucket'                        : 'str',
        'SubBucket'                     : 'str',
        'Underlier'                     : 'str',
        'CurveType'                     : 'str',
        'Tenor'                         : 'str',
        'Sensitivity'                   : 'float64',
    },
    'MS_CSVega' : {
        'RiskGroup'                     : 'str',
        'RiskSubGroup'                  : 'str',
        'RiskClass'                     : 'str',
        'Bucket'                        : 'str',
        'SubBucket'                     : 'str',
        'Underlier'                     : 'str',
        'OptionMaturity'                : 'str',
        'Sensitivity'                   : 'float64',
    },
    'MS_CSCurvature' : {
        'RiskGroup'                     : 'str',
        'RiskSubGroup'                  : 'str',
        'RiskClass'                     : 'str',
        'Bucket'                        : 'str',
        'SubBucket'                     : 'str',
        'Underlier'                     : 'str',
        'CVR+'                          : 'float64',
        'CVR-'                          : 'float64',
    },
    'MS_EQDelta' : {
        'RiskGroup'                     : 'str',
        'RiskSubGroup'                  : 'str',
        'RiskClass'                     : 'str',
        'Bucket'                        : 'str',
        'SubBucket'                     : 'str',
        'EquityName'                    : 'str',
        'SpotRepo'                      : 'str',
        'Sensitivity'                   : 'float64',
    },
    'MS_EQVega' : {
        'RiskGroup'                     : 'str',
        'RiskSubGroup'                  : 'str',
        'RiskClass'                     : 'str',
        'Bucket'                        : 'str',
        'SubBucket'                     : 'str',
        'EquityName'                    : 'str',
        'OptionMaturity'                : 'str',
        'Sensitivity'                   : 'float64',
    },
    'MS_EQCurvature' : {
        'RiskGroup'                     : 'str',
        'RiskSubGroup'                  : 'str',
        'RiskClass'                     : 'str',
        'Bucket'                        : 'str',
        'SubBucket'                     : 'str',
        'EquityName'                    : 'str',
        'CVR+'                          : 'float64',
        'CVR-'                          : 'float64',
    },
    'MS_CMDelta' : {
        'RiskGroup'                     : 'str',
        'RiskSubGroup'                  : 'str',
        'RiskClass'                     : 'str',
        'Bucket'                        : 'str',
        'SubBucket'                     : 'str',
        'CommodityName'                 : 'str',
        'DeliveryLocation'              : 'str',
        'Tenor'                         : 'str',
        'Sensitivity'                   : 'float64',
    },
    'MS_CMVega' : {
        'RiskGroup'                     : 'str',
        'RiskSubGroup'                  : 'str',
        'RiskClass'                     : 'str',
        'Bucket'                        : 'str',
        'SubBucket'                     : 'str',
        'CommodityName'                 : 'str',
        'OptionMaturity'                : 'str',
        'Sensitivity'                   : 'float64',
    },
    'MS_CMCurvature' : {
        'RiskGroup'                     : 'str',
        'RiskSubGroup'                  : 'str',
        'RiskClass'                     : 'str',
        'Bucket'                        : 'str',
        'SubBucket'                     : 'str',
        'CommodityName'                 : 'str',
        'CVR+'                          : 'float64',
        'CVR-'                          : 'float64',
    },
    'MS_FXDelta' : {
        'RiskGroup'                     : 'str',
        'RiskSubGroup'                  : 'str',
        'RiskClass'                     : 'str',
        'Bucket'                        : 'str',
        'Sensitivity'                   : 'float64',
    },
    'MS_FXVega' : {
        'RiskGroup'                     : 'str',
        'RiskSubGroup'                  : 'str',
        'RiskClass'                     : 'str',
        'Bucket'                        : 'str',
        'OptionMaturity'                : 'str',
        'Sensitivity'                   : 'float64',
    },
    'MS_FXCurvature' : {
        'RiskGroup'                     : 'str',
        'RiskSubGroup'                  : 'str',
        'RiskClass'                     : 'str',
        'Bucket'                        : 'str',
        'CVR+'                          : 'float64',
        'CVR-'                          : 'float64',
    },
    'MD_CR_DRC' : {
        'RiskGroup'                     : 'str',
        'RiskSubGroup'                  : 'str',
        'RiskClass'                     : 'str',
        'Bucket'                        : 'str',
        'SubBucket'                     : 'str',
        'Name'                          : 'str',
        'Seniority'                     : 'str',
        'Rating'                        : 'str',
        'MaturityDate'                  : 'str',
        'JTD'                           : 'float64',
    },
    'MD_CC_DRC' : {
        'RiskGroup'                     : 'str',
        'RiskSubGroup'                  : 'str',
        'RiskClass'                     : 'str',
        'Bucket'                        : 'str',        # This is the index name or an identifier for the correlation instrument
        'ExposureType'                  : 'str',        # CDSIndex, CDSIndexTranche, SingleNameHedge, Bespoke.
        'Series'                        : 'str',
        'Tranche'                       : 'str',        # May be a tranche name, maybe a number for the obligpr in the index
        'MaturityDate'                  : 'str',
        'Rating'                        : 'object',     # Sometimes this is None and needs to be kept as NoneType.  Otherwise it's a 'str' and 'object' is OK for that
        'RiskWeight'                    : 'float64',
        'JTD'                           : 'float64',
    },
    'MD_CS_DRC' : {
        'RiskGroup'                     : 'str',
        'RiskSubGroup'                  : 'str',
        'RiskClass'                     : 'str',
        'Bucket'                        : 'str',
        'Issuer/Tranche'                : 'str',
        'MaturityDate'                  : 'str',
        'Rating'                        : 'object',     # Sometimes this is None and needs to be kept as NoneType.  Otherwise it's a 'str' and 'object' is OK for that
        'RiskWeight'                    : 'float64',
        'JTD'                           : 'float64',
    },
    'MR_RRAO' : {
        'RiskGroup'                     : 'str',
        'RiskSubGroup'                  : 'str',
        'RiskClass'                     : 'str',
        'Bucket'                        : 'str',
        'SubBucket'                     : 'str',
        'NotionalAmount'                : 'float64',
    },

    #
    # CVA RiskClasses
    #
    'CS_IRDelta' : {
        'RiskGroup'                     : 'str',
        'RiskSubGroup'                  : 'str',
        'RiskClass'                     : 'str',
        'Bucket'                        : 'str',
        'CurveType'                     : 'str',
        'Tenor'                         : 'str',
        'Sensitivity'                   : 'float64',
        'HedgeSensitivity'              : 'float64',
    },
    'CS_IRVega' : {
        'RiskGroup'                     : 'str',
        'RiskSubGroup'                  : 'str',
        'RiskClass'                     : 'str',
        'Bucket'                        : 'str',
        'CurveType'                     : 'str',
        'Sensitivity'                   : 'float64',
        'HedgeSensitivity'              : 'float64',
    },
    'CS_FXDelta' : {
        'RiskGroup'                     : 'str',
        'RiskSubGroup'                  : 'str',
        'RiskClass'                     : 'str',
        'Bucket'                        : 'str',
        'Sensitivity'                   : 'float64',
        'HedgeSensitivity'              : 'float64',
    },
    'CS_FXVega' : {
        'RiskGroup'                     : 'str',
        'RiskSubGroup'                  : 'str',
        'RiskClass'                     : 'str',
        'Bucket'                        : 'str',
        'Sensitivity'                   : 'float64',
        'HedgeSensitivity'              : 'float64',
    },
    'CS_CCDelta' : {
        'RiskGroup'                     : 'str',
        'RiskSubGroup'                  : 'str',
        'RiskClass'                     : 'str',
        'Bucket'                        : 'str',
        'SubBucket'                     : 'str',
        'CreditName'                    : 'str',
        'ParentName'                    : 'str',
        'IG_HYNR'                       : 'str',
        'Tenor'                         : 'str',
        'Sensitivity'                   : 'float64',
        'HedgeSensitivity'              : 'float64',
    },
    'CS_CRDelta' : {
        'RiskGroup'                     : 'str',
        'RiskSubGroup'                  : 'str',
        'RiskClass'                     : 'str',
        'Bucket'                        : 'str',
        'SubBucket'                     : 'str',
        'Sensitivity'                   : 'float64',
        'HedgeSensitivity'              : 'float64',
    },
    'CS_CRVega' : {
        'RiskGroup'                     : 'str',
        'RiskSubGroup'                  : 'str',
        'RiskClass'                     : 'str',
        'Bucket'                        : 'str',
        'SubBucket'                     : 'str',
        'Sensitivity'                   : 'float64',
        'HedgeSensitivity'              : 'float64',
    },
    'CS_EQDelta' : {
        'RiskGroup'                     : 'str',
        'RiskSubGroup'                  : 'str',
        'RiskClass'                     : 'str',
        'Bucket'                        : 'str',
        'SubBucket'                     : 'str',
        'Sensitivity'                   : 'float64',
        'HedgeSensitivity'              : 'float64',
    },
    'CS_EQVega' : {
        'RiskGroup'                     : 'str',
        'RiskSubGroup'                  : 'str',
        'RiskClass'                     : 'str',
        'Bucket'                        : 'str',
        'SubBucket'                     : 'str',
        'Sensitivity'                   : 'float64',
        'HedgeSensitivity'              : 'float64',
    },
    'CS_CMDelta' : {
        'RiskGroup'                     : 'str',
        'RiskSubGroup'                  : 'str',
        'RiskClass'                     : 'str',
        'Bucket'                        : 'str',
        'SubBucket'                     : 'str',
        'Sensitivity'                   : 'float64',
        'HedgeSensitivity'              : 'float64',
    },
    'CS_CMVega' : {
        'RiskGroup'                     : 'str',
        'RiskSubGroup'                  : 'str',
        'RiskClass'                     : 'str',
        'Bucket'                        : 'str',
        'SubBucket'                     : 'str',
        'Sensitivity'                   : 'float64',
        'HedgeSensitivity'              : 'float64',
    },
    'CB_REDUCED' : {
        'RiskGroup'                     : 'str',
        'RiskSubGroup'                  : 'str',
        'RiskClass'                     : 'str',
        'Sector'                        : 'str',          # Sector and Region aren't really necessary if we have CounterPartyGroup
        'Region'                        : 'str',          #    - we can assume that the mismatched ParentNames in a CounterpartyGroup are sector/region matches
        'PositionType'                  : 'str',          # Exposure - no other possibility for Reduced BA-CVA
        'CreditName'                    : 'str',          # Counterparty
        'ParentName'                    : 'str',          # Ultimate Parent of CreditName
        'NettingSetMaturity'            : 'float64',      # In years to run
        'EAD'                           : 'float64',
    },
    'CB_FULL' : {
        'RiskGroup'                     : 'str',
        'RiskSubGroup'                  : 'str',
        'RiskClass'                     : 'str',
        'Sector'                        : 'str',          # Sector and Region aren't really necessary if we have CounterPartyGroup
        'Region'                        : 'str',          #    - we can assume that the mismatched ParentNames in a CounterpartyGroup are sector/region matches
        'PositionType'                  : 'str',          # {Exposure, Hedge, IndexHedge}
        'CounterpartyGroup'             : 'str',          # A grouping for exposures and their related hedges
        'CreditName'                    : 'str',          # Counterparty or hedge underlier
        'ParentName'                    : 'str',          # Ultimate Parent of CreditName
        'NettingSetMaturity'            : 'float64',      # In years to run
        'EAD'                           : 'float64',
    },
}


class FNetF():
    def __init__(self):
        self.FNF_Params_Tab = "Parameters"
        self.FNF_Copyright_Tab = "Copyright"
        self.FNF_Test_Tabs = [ "ObligorTests", "FactorTests", "BucketTests", "CapitalTests" ]
        self._params = {'FNetFormatVersion' : FNetFormatVersion}
        self._sensis = {}
        self._riskGroups = set()
        self._tests = {}

    def load(self, filepath):
        """
        Load FNetF data from either Excel (.xlsx) or JSON (.json) file.

        The format is auto-detected based on file extension.
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File '{filepath}' not found")

        if not os.path.isfile(filepath):
            raise ValueError(f"'{filepath}' is not a file")

        if os.path.getsize(filepath) == 0:
            raise ValueError(f"File '{filepath}' is empty")

        # Auto-detect format based on extension
        filepath_lower = filepath.lower()
        if filepath_lower.endswith('.json'):
            return self._load_json(filepath)
        elif filepath_lower.endswith('.xlsx') or filepath_lower.endswith('.xls'):
            return self._load_excel(filepath)
        else:
            raise ValueError(f"Unsupported file format. Use .xlsx or .json")

    def _load_excel(self, filepath):
        """Load FNetF data from Excel file."""
        with pd.ExcelFile(filepath) as fnf:
            for sheet in fnf.sheet_names:
                if sheet == self.FNF_Params_Tab:
                    df = pd.read_excel(fnf, sheet_name=self.FNF_Params_Tab, header=None)
                    self._params =FNU.extractKeyedData(self.FNF_Params_Tab, df, {})  # empty dataTypes dictionary as all are assumed to be 'str'ings

                    if self._params['FNetFormatVersion'] != FNetFormatVersion:
                        print(f"Incompatible FNetFormatVersion: code version = {FNetFormatVersion}, file version = {self._params['FNetFormatVersion']}")
                        return None
                elif sheet in self.FNF_Test_Tabs:
                    unitTests = pd.read_excel(fnf, sheet_name=sheet, dtype=str)
                    colNames = [x for x in unitTests.columns if x not in ['Test ID',
                                                                          'RiskGroup',
                                                                          'RiskSubGroup',
                                                                          'RiskClass',
                                                                          'Description',
                                                                          'Sensitivity IDs']]
                    newColNames = [f"Benchmark_{x}" for x in colNames]
                    colTypeDict = {x : 'float64' for x in newColNames}
                    unitTests = unitTests.rename(columns=dict(zip(colNames, newColNames))).astype(colTypeDict)
                    self._tests[sheet] = unitTests
                elif sheet in FNetFieldType.keys():
                    # default to string and then convert known fields to the correct type
                    df = pd.read_excel(fnf, sheet_name=sheet, dtype=str)
                    typemap = {}

                    for col, dtype in FNetFieldType[sheet].items():
                        # check the columns specified in the type map all exist before we convert
                        if col not in df.columns:
                            print(f"Column {col} not found in {sheet}")
                        elif dtype == 'bool':
                            df.loc[:, col] = df[col].apply(lambda x : False if x == 'False' else True)
                            typemap[col] = dtype
                        elif dtype != 'object':
                            df.loc[:, col] = df[col].fillna(FNU._fillnaMap[dtype])
                            typemap[col] = dtype

                    df = df.astype(typemap)
                    self._sensis[sheet] = df
                    self._riskGroups |= set([(r.at['RiskGroup'], r.at['RiskSubGroup']) for _,r in df[['RiskGroup','RiskSubGroup']].drop_duplicates().iterrows()])
                elif sheet != self.FNF_Copyright_Tab:
                    print(f"Unknown sheet '{sheet}' in file '{filepath}'")


        if not self._sensis :
            return None
        else:
            self._filename = filepath
            self.setParam('FileName', filepath)
            sensis = pd.concat([x[['Sensitivity ID', 'RiskClass']] for x in self._sensis.values()], axis=0).set_index('Sensitivity ID', drop=False)

            # Collect all the sensitivities for each combination
            #
            comboSensis = pd.DataFrame()

            for testSet, testSetData in self._tests.items():
                for combo, cRow in testSetData.set_index('Test ID').iterrows():
                    # if combo in self._CombosToOmit:
                    #     continue

                    getAll = False
                    newRows = []

                    for s in cRow['Sensitivity IDs'].replace(', ', ',').split(','):
                        if s.startswith('ALL '):
                            getAll = True    # we treat all the remaining Sensitivity IDs as prefixes and match against them
                            sensiSubList = sensis[[ss.startswith(s[4:]) # and (
                                                #     s[4:] == ss                 # exact match
                                                #     or
                                                #     ss[len(s)-4:].isdigit()     # all the characters after the matching prefix are digits
                                                #                                 # so "ALL MS_EQV_a" doesn't match "MS_EQV_aa1"
                                                # ) 
                                                for ss in sensis['Sensitivity ID']]
                                            ]['Sensitivity ID'].unique()
                        elif getAll:
                            # same as the above case but we don't have to look past the "ALL " prefix
                            sensiSubList = sensis[[ss.startswith(s) # and (
                                                #     s == ss                     # exact match
                                                #     or
                                                #     ss[len(s):].isdigit()       # all the characters after the matching prefix are digits
                                                #                                 # so "ALL MS_EQV_a" doesn't match "MS_EQV_aa1"
                                                # )
                                                for ss in sensis['Sensitivity ID']]
                                            ]['Sensitivity ID'].unique()
                        else:
                            if s in sensis.index:
                                sensiSubList = [s]
                            else:
                                print(f"Missing Sensitivity ID: {s} in Test {combo}")
                                continue

                        for ss in sensiSubList:
                            newRows.append([testSet, combo, sensis.at[ss, 'RiskClass'], ss])

                    comboSensis = pd.concat([comboSensis, pd.DataFrame(newRows, columns=['Test Set', 'Test ID', 'RiskClass', 'Sensitivity ID'])], axis=0)

            if not comboSensis.empty:
                comboSensis.set_index(['Test Set', 'Test ID'], inplace=True)

            return comboSensis

    def _load_json(self, filepath):
        """Load FNetF data from JSON file."""
        with open(filepath, 'r') as f:
            data = json.load(f)

        # Load copyright (optional)
        if '_copyright' in data:
            self._copyright = data['_copyright']

        # Load parameters
        if '_parameters' in data:
            self._params = data['_parameters']

            if self._params.get('FNetFormatVersion') != FNetFormatVersion:
                print(f"Incompatible FNetFormatVersion: code version = {FNetFormatVersion}, file version = {self._params.get('FNetFormatVersion')}")
                return None

        # Load test data
        if '_tests' in data:
            for testType, testData in data['_tests'].items():
                if testType in self.FNF_Test_Tabs:
                    df = pd.DataFrame(testData['data'], columns=testData['columns'])
                    # Convert benchmark columns to float64
                    for col in df.columns:
                        if col.startswith('Benchmark_'):
                            df[col] = df[col].astype('float64')
                    self._tests[testType] = df

        # Load sensitivity data (risk classes)
        if '_sensitivities' in data:
            for riskClass, rcData in data['_sensitivities'].items():
                if riskClass in FNetFieldType.keys():
                    df = pd.DataFrame(rcData['data'], columns=rcData['columns'])

                    # Apply type conversions for standard FNetFieldType columns
                    typemap = {}
                    for col, dtype in FNetFieldType[riskClass].items():
                        if col in df.columns:
                            if dtype == 'bool':
                                df[col] = df[col].apply(lambda x: False if x == 'False' or x is False else True)
                            elif dtype != 'object':
                                df[col] = df[col].fillna(FNU._fillnaMap.get(dtype, ''))
                            typemap[col] = dtype

                    # Handle additional columns using dtypes from JSON
                    if 'dtypes' in rcData:
                        fnetf_cols = set(FNetFieldType[riskClass].keys()) | {'Sensitivity ID'}
                        for col, dtype in rcData['dtypes'].items():
                            if col not in fnetf_cols and col in df.columns:
                                # Apply type conversion for extra columns
                                if dtype == 'bool':
                                    df[col] = df[col].apply(lambda x: False if x == 'False' or x is False else True)
                                elif dtype in ('int64', 'float64'):
                                    df[col] = df[col].fillna(FNU._fillnaMap.get(dtype, 0))
                                elif dtype == 'str':
                                    df[col] = df[col].fillna('')
                                typemap[col] = dtype

                    df = df.astype(typemap)
                    self._sensis[riskClass] = df
                    self._riskGroups |= set([
                        (r.at['RiskGroup'], r.at['RiskSubGroup'])
                        for _, r in df[['RiskGroup', 'RiskSubGroup']].drop_duplicates().iterrows()
                    ])
                else:
                    print(f"Unknown RiskClass '{riskClass}' in JSON file")

        if not self._sensis:
            return None

        self._filename = filepath
        self.setParam('FileName', filepath)

        # Build comboSensis the same way as Excel loading
        sensis = pd.concat(
            [x[['Sensitivity ID', 'RiskClass']] for x in self._sensis.values()],
            axis=0
        ).set_index('Sensitivity ID', drop=False)

        comboSensis = pd.DataFrame()

        for testSet, testSetData in self._tests.items():
            for combo, cRow in testSetData.set_index('Test ID').iterrows():
                getAll = False
                newRows = []

                for s in cRow['Sensitivity IDs'].replace(', ', ',').split(','):
                    if s.startswith('ALL '):
                        getAll = True
                        sensiSubList = sensis[
                            [ss.startswith(s[4:]) for ss in sensis['Sensitivity ID']]
                        ]['Sensitivity ID'].unique()
                    elif getAll:
                        sensiSubList = sensis[
                            [ss.startswith(s) for ss in sensis['Sensitivity ID']]
                        ]['Sensitivity ID'].unique()
                    else:
                        if s in sensis.index:
                            sensiSubList = [s]
                        else:
                            print(f"Missing Sensitivity ID: {s} in Test {combo}")
                            continue

                    for ss in sensiSubList:
                        newRows.append([testSet, combo, sensis.at[ss, 'RiskClass'], ss])

                comboSensis = pd.concat(
                    [comboSensis, pd.DataFrame(newRows, columns=['Test Set', 'Test ID', 'RiskClass', 'Sensitivity ID'])],
                    axis=0
                )

        if not comboSensis.empty:
            comboSensis.set_index(['Test Set', 'Test ID'], inplace=True)

        return comboSensis

    def getParams(self):
        if not self._params:
            raise ValueError("No params data loaded")
            return None
        
        return self._params


    def getParam(self, param):
        if not self._params:
            raise ValueError("No params data loaded")
            return None

        if param not in self._params.keys():
            raise ValueError(f"Parameter '{param}' not found")
            return None
        else:
            return self._params[param]


    def getRiskClasses(self):
        if self._sensis:
            return list(self._sensis.keys())
        else:
            return []


    def getRiskGroups(self):
        return list(self._riskGroups)


    def getAllRiskClasses(self):
        return list(FNetFieldType.keys())


    def getRiskClassData(self, riskClass):
        if not self._sensis:
            raise ValueError("No sensitivity data loaded")
            return None

        if riskClass not in self._sensis:
            raise ValueError(f"RiskClass '{riskClass}' not found")
            return None
        else:
            return self._sensis[riskClass]


    def getUnitTestSets(self):
        if not self._tests:
            raise ValueError("No test data loaded")
            return None

        return list(self._tests.keys())


    def getUnitTests(self, testSet):
        if not self._tests:
            raise ValueError("No test data loaded")
            return None

        if not testSet in self._tests.keys():
            raise ValueError(f"TestSet '{testSet}' not found")
            return None

        return self._tests[testSet]


    def getUnitTest(self, testSet, testID):
        if not self._tests:
            raise ValueError("No test data loaded")
            return None

        if not testSet in self._tests.keys():
            raise ValueError(f"TestSet '{testSet}' not found")
            return None

        if not testID in self._tests[testSet]['Test ID'].values:
            raise ValueError(f"TestID '{testID}' not found in TestSet '{testSet}'")
            return None

        return self._tests[testSet][self._tests[testSet]['Test ID'] == testID]


    def getUnitTestSensis(self, testSet, testID):
        if not self._tests:
            raise ValueError("No test data loaded")
            return None

        if not testSet in self._tests.keys():
            raise ValueError(f"TestSet '{testSet}' not found")
            return None
        
        if not testID in self._tests[testSet]['Test ID'].values:
            raise ValueError(f"TestID '{testID}' not found in TestSet '{testSet}'")
            return None

        riskClass = self._tests[testSet][self._tests[testSet]['Test ID'] == testID]['RiskClass'].iat[0]
        sensis = self._tests[testSet][self._tests[testSet]['Test ID'] == testID]['Sensitivity IDs'].iat[0].replace(', ', ',').split(',')
        return self._sensis[riskClass][self._sensis[riskClass]['Sensitivity ID'].isin(sensis)]


    def addRiskClassFields(seld, rc, fields):
        for k, v in fields.items():
            if k in FNetFieldType[rc].keys():
                print(f'Warning: spec for RiskClass {rc} alrady contains field {k} - spec unchanged')
            else:
                FNetFieldType[rc][k] = v


    def save(self, filename):
        """
        Save FNetF data to either Excel (.xlsx) or JSON (.json) file.

        The format is auto-detected based on file extension.
        """
        filename_lower = filename.lower()
        if filename_lower.endswith('.json'):
            self._save_json(filename)
        elif filename_lower.endswith('.xlsx') or filename_lower.endswith('.xls'):
            self._save_excel(filename)
        else:
            raise ValueError(f"Unsupported file format. Use .xlsx or .json")

    def _save_excel(self, filename):
        """Save FNetF data to Excel file."""
        # create the ExcelWriter object
        writer = pd.ExcelWriter(filename)
        params = pd.DataFrame(self._params, index=['Params'])
        # TODO maybe: create the inverse of FRTBUtils.extractKeyedData to write the data back to the Excel file
        params.T['Params'].to_excel(writer, sheet_name=self.FNF_Params_Tab, index=True, header=False)

        for testType in self.FNF_Test_Tabs:
            if testType in self._tests and not self._tests[testType].empty:
                keycols = ['Test ID', 'RiskClass', 'Description', 'Sensitivity IDs']
                valcols = [x for x in self._tests[testType].columns if x not in keycols]
                cols = keycols + valcols
                self._tests[testType][cols].to_excel(writer, sheet_name=testType, index=False)

        for riskClass, df in self._sensis.items():
            if not df.empty:
                cols = [x for x in ['Sensitivity ID'] + list(FNetFieldType[riskClass].keys()) if x in df.columns]
                df[cols].to_excel(writer, sheet_name=riskClass, index=False)

        writer.close()

    def _save_json(self, filename, pretty=True, indent=2):
        """
        Save FNetF data to JSON file.

        The JSON format is self-documenting with the following structure:
        {
            "_copyright": { ... },
            "_parameters": { "FNetFormatVersion": "3.0", ... },
            "_tests": {
                "ObligorTests": { "columns": [...], "data": [...] },
                ...
            },
            "_sensitivities": {
                "MS_IRDelta": {
                    "columns": [...],
                    "dtypes": { "RiskGroup": "str", ... },
                    "data": [...]
                },
                ...
            }
        }
        """
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

        # Use stored copyright if available
        if hasattr(self, '_copyright') and self._copyright:
            data['_copyright'] = self._copyright
        else:
            data['_copyright'] = {
                'value': copyright_text,
                'type': 'text',
                'note': 'Copyright and license information'
            }

        # Add parameters
        data['_parameters'] = self._params.copy()

        # Add test data
        if self._tests:
            data['_tests'] = {}
            for testType, testDf in self._tests.items():
                if not testDf.empty:
                    keycols = ['Test ID', 'RiskClass', 'Description', 'Sensitivity IDs']
                    valcols = [x for x in testDf.columns if x not in keycols]
                    cols = keycols + valcols
                    cols = [c for c in cols if c in testDf.columns]

                    data['_tests'][testType] = {
                        'columns': cols,
                        'data': testDf[cols].values.tolist()
                    }

        # Build schema section documenting field types for all risk classes
        schema = {}

        # Add sensitivity data
        if self._sensis:
            data['_sensitivities'] = {}
            for riskClass, df in self._sensis.items():
                if not df.empty:
                    # Get standard FNetFieldType columns first, then any additional columns
                    fnetf_cols = ['Sensitivity ID'] + list(FNetFieldType[riskClass].keys())
                    standard_cols = [x for x in fnetf_cols if x in df.columns]
                    extra_cols = [x for x in df.columns if x not in fnetf_cols]
                    cols = standard_cols + extra_cols

                    # Get dtypes for documentation - include both standard and extra columns
                    dtypes = {}
                    for col in cols:
                        if col in FNetFieldType[riskClass]:
                            dtypes[col] = FNetFieldType[riskClass][col]
                        elif col == 'Sensitivity ID':
                            dtypes[col] = 'str'
                        else:
                            # Infer dtype for extra columns
                            dtype = df[col].dtype
                            if dtype == 'object':
                                dtypes[col] = 'str'
                            elif dtype == 'bool':
                                dtypes[col] = 'bool'
                            elif dtype == 'int64':
                                dtypes[col] = 'int64'
                            elif dtype == 'float64':
                                dtypes[col] = 'float64'
                            else:
                                dtypes[col] = str(dtype)

                    # Build schema entry for this risk class
                    schema[riskClass] = {
                        'standard_fields': {k: v for k, v in dtypes.items() if k in fnetf_cols},
                        'extra_fields': {k: v for k, v in dtypes.items() if k not in fnetf_cols}
                    }

                    # Convert DataFrame to list, handling NaN/None properly
                    df_subset = df[cols].copy()
                    # Replace NaN with None for JSON serialization
                    df_subset = df_subset.where(pd.notnull(df_subset), None)

                    data['_sensitivities'][riskClass] = {
                        'columns': cols,
                        'dtypes': dtypes,
                        'data': df_subset.values.tolist()
                    }

        # Add schema section documenting all field types
        data['_schema'] = {
            'description': 'Field type definitions for risk classes in this file',
            'risk_classes': schema
        }

        # Write JSON file
        with open(filename, 'w') as f:
            if pretty:
                json.dump(data, f, indent=indent, cls=_FNetFJSONEncoder)
            else:
                json.dump(data, f, cls=_FNetFJSONEncoder)


    def setParam(self, param, value):
        self._params[param] = value


    def setRiskClassData(self, riskClass, sensis):
        if not riskClass in FNetFieldType.keys():
            raise ValueError(f"Unknown RiskClass '{riskClass}'")

        sensisTypeMap = {}

        for k, v in FNetFieldType[riskClass].items():
            if k in sensis.columns:
                sensisTypeMap[k] = v

        self._sensis[riskClass] = sensis.astype(sensisTypeMap)


    def setUnitTests(self, testType, tests):
        if testType not in self.FNF_Test_Tabs:
            raise ValueError(f"Unknown testType '{testType}'")
        else:
            self._tests[testType] = tests


if __name__ == '__main__':
    fnf = FNetF()
    path = os.path.join(os.sep, 'Volumes', 'home', 'FRTB', 'Testing', 'UnitTests_BCBS_FNetF_Generated_v0.8.xlsx')
    CS = fnf.load(path)
    print(fnf._params)

    if CS is not None:
        print(CS)

