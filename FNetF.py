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
import os

import FRTBUtils as FNU

FNetFieldType = {
    'MS_IRDelta' : {
        'RiskGroup'                     : 'str',
        'IRT'                           : 'bool',
        'RiskClass'                     : 'str',
        'Bucket'                        : 'str',
        'CurveType'                     : 'str',
        'Curve'                         : 'str',
        'Tenor'                         : 'str',
        'Sensitivity'                   : 'float64',
    },
    'MS_IRVega' : {
        'RiskGroup'                     : 'str',
        'IRT'                           : 'bool',
        'RiskClass'                     : 'str',
        'Bucket'                        : 'str',
        'CurveType'                     : 'str',
        'OptionMaturity'                : 'str',
        'UnderlyingResidualMaturity'    : 'str',
        'Sensitivity'                   : 'float64',
    },
    'MS_IRCurvature' : {
        'RiskGroup'                     : 'str',
        'IRT'                           : 'bool',
        'RiskClass'                     : 'str',
        'Bucket'                        : 'str',
        'CVR+'                          : 'float64',
        'CVR-'                          : 'float64',
    },
    'MS_CRDelta' : {
        'RiskGroup'                     : 'str',
        'IRT'                           : 'bool',
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
        'IRT'                           : 'bool',
        'RiskClass'                     : 'str',
        'Bucket'                        : 'str',
        'SubBucket'                     : 'str',
        'CreditName'                    : 'str',
        'OptionMaturity'                : 'str',
        'Sensitivity'                   : 'float64',
    },
    'MS_CRCurvature' : {
        'RiskGroup'                     : 'str',
        'IRT'                           : 'bool',
        'RiskClass'                     : 'str',
        'Bucket'                        : 'str',
        'SubBucket'                     : 'str',
        'CreditName'                    : 'str',
        'CVR+'                          : 'float64',
        'CVR-'                          : 'float64',
    },
    'MS_CCDelta' : {
        'RiskGroup'                     : 'str',
        'IRT'                           : 'bool',
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
        'IRT'                           : 'bool',
        'RiskClass'                     : 'str',
        'Bucket'                        : 'str',
        'SubBucket'                     : 'str',
        'Underlier'                     : 'str',
        'OptionMaturity'                : 'str',
        'Sensitivity'                   : 'float64',
    },
    'MS_CCCurvature' : {
        'RiskGroup'                     : 'str',
        'IRT'                           : 'bool',
        'RiskClass'                     : 'str',
        'Bucket'                        : 'str',
        'SubBucket'                     : 'str',
        'Underlier'                     : 'str',
        'CVR+'                          : 'float64',
        'CVR-'                          : 'float64',
    },
    'MS_CSDelta' : {
        'RiskGroup'                     : 'str',
        'IRT'                           : 'bool',
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
        'IRT'                           : 'bool',
        'RiskClass'                     : 'str',
        'Bucket'                        : 'str',
        'SubBucket'                     : 'str',
        'Underlier'                     : 'str',
        'OptionMaturity'                : 'str',
        'Sensitivity'                   : 'float64',
    },
    'MS_CSCurvature' : {
        'RiskGroup'                     : 'str',
        'IRT'                           : 'bool',
        'RiskClass'                     : 'str',
        'Bucket'                        : 'str',
        'SubBucket'                     : 'str',
        'Underlier'                     : 'str',
        'CVR+'                          : 'float64',
        'CVR-'                          : 'float64',
    },
    'MS_EQDelta' : {
        'RiskGroup'                     : 'str',
        'IRT'                           : 'bool',
        'RiskClass'                     : 'str',
        'Bucket'                        : 'str',
        'SubBucket'                     : 'str',
        'EquityName'                    : 'str',
        'SpotRepo'                      : 'str',
        'Sensitivity'                   : 'float64',
    },
    'MS_EQVega' : {
        'RiskGroup'                     : 'str',
        'IRT'                           : 'bool',
        'RiskClass'                     : 'str',
        'Bucket'                        : 'str',
        'SubBucket'                     : 'str',
        'EquityName'                    : 'str',
        'OptionMaturity'                : 'str',
        'Sensitivity'                   : 'float64',
    },
    'MS_EQCurvature' : {
        'RiskGroup'                     : 'str',
        'IRT'                           : 'bool',
        'RiskClass'                     : 'str',
        'Bucket'                        : 'str',
        'SubBucket'                     : 'str',
        'EquityName'                    : 'str',
        'CVR+'                          : 'float64',
        'CVR-'                          : 'float64',
    },
    'MS_CMDelta' : {
        'RiskGroup'                     : 'str',
        'IRT'                           : 'bool',
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
        'IRT'                           : 'bool',
        'RiskClass'                     : 'str',
        'Bucket'                        : 'str',
        'SubBucket'                     : 'str',
        'CommodityName'                 : 'str',
        'OptionMaturity'                : 'str',
        'Sensitivity'                   : 'float64',
    },
    'MS_CMCurvature' : {
        'RiskGroup'                     : 'str',
        'IRT'                           : 'bool',
        'RiskClass'                     : 'str',
        'Bucket'                        : 'str',
        'SubBucket'                     : 'str',
        'CommodityName'                 : 'str',
        'CVR+'                          : 'float64',
        'CVR-'                          : 'float64',
    },
    'MS_FXDelta' : {
        'RiskGroup'                     : 'str',
        'IRT'                           : 'bool',
        'RiskClass'                     : 'str',
        'Bucket'                        : 'str',
        'Sensitivity'                   : 'float64',
    },
    'MS_FXVega' : {
        'RiskGroup'                     : 'str',
        'IRT'                           : 'bool',
        'RiskClass'                     : 'str',
        'Bucket'                        : 'str',
        'OptionMaturity'                : 'str',
        'Sensitivity'                   : 'float64',
    },
    'MS_FXCurvature' : {
        'RiskGroup'                     : 'str',
        'IRT'                           : 'bool',
        'RiskClass'                     : 'str',
        'Bucket'                        : 'str',
        'CVR+'                          : 'float64',
        'CVR-'                          : 'float64',
    },
    'MD_CR_DRC' : {
        'RiskGroup'                     : 'str',
        'IRT'                           : 'bool',
        'RiskClass'                     : 'str',
        'Bucket'                        : 'str',
        'Name'                          : 'str',
        'Seniority'                     : 'str',
        'Rating'                        : 'str',
        'MaturityDate'                  : 'str',
        'JTD'                           : 'float64',
    },
    'MD_CC_DRC' : {
        'RiskGroup'                     : 'str',
        'IRT'                           : 'bool',
        'RiskClass'                     : 'str',
        'Bucket'                        : 'str',
        'Series'                        : 'str',
        'TrancheNames'                  : 'str',
        'Seniority'                     : 'str',
        'Rating'                        : 'str',
        'MaturityDate'                  : 'str',
        'JTD'                           : 'float64',
    },
    'MD_CS_DRC' : {
        'RiskGroup'                     : 'str',
        'IRT'                           : 'bool',
        'RiskClass'                     : 'str',
        'Bucket'                        : 'str',
        'Issuer/Tranche'                : 'str',
        'RiskWeight'                    : 'float64',
        'JTD'                           : 'float64',
    },
    'MR_RRAO' : {
        'RiskGroup'                     : 'str',
        'IRT'                           : 'bool',
        'RiskClass'                     : 'str',
        'Bucket'                        : 'str',
        'NotionalAmount'                : 'float64',
    },

    #
    # CVA RiskClasses
    #
    'CS_IRDelta' : {
        'RiskGroup'                     : 'str',
        'RiskClass'                     : 'str',
        'Bucket'                        : 'str',
        'CurveType'                     : 'str',
        'Tenor'                         : 'str',
        'Sensitivity'                   : 'float64',
        'HedgeSensitivity'              : 'float64',
    },
    'CS_IRVega' : {
        'RiskGroup'                     : 'str',
        'RiskClass'                     : 'str',
        'Bucket'                        : 'str',
        'CurveType'                     : 'str',
        'Sensitivity'                   : 'float64',
        'HedgeSensitivity'              : 'float64',
    },
    'CS_FXDelta' : {
        'RiskGroup'                     : 'str',
        'RiskClass'                     : 'str',
        'Bucket'                        : 'str',
        'Sensitivity'                   : 'float64',
        'HedgeSensitivity'              : 'float64',
    },
    'CS_FXVega' : {
        'RiskGroup'                     : 'str',
        'RiskClass'                     : 'str',
        'Bucket'                        : 'str',
        'Sensitivity'                   : 'float64',
        'HedgeSensitivity'              : 'float64',
    },
    'CS_CCDelta' : {
        'RiskGroup'                     : 'str',
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
        'RiskClass'                     : 'str',
        'Bucket'                        : 'str',
        'SubBucket'                     : 'str',
        'Sensitivity'                   : 'float64',
        'HedgeSensitivity'              : 'float64',
    },
    'CS_CRVega' : {
        'RiskGroup'                     : 'str',
        'RiskClass'                     : 'str',
        'Bucket'                        : 'str',
        'SubBucket'                     : 'str',
        'Sensitivity'                   : 'float64',
        'HedgeSensitivity'              : 'float64',
    },
    'CS_EQDelta' : {
        'RiskGroup'                     : 'str',
        'RiskClass'                     : 'str',
        'Bucket'                        : 'str',
        'SubBucket'                     : 'str',
        'Sensitivity'                   : 'float64',
        'HedgeSensitivity'              : 'float64',
    },
    'CS_EQVega' : {
        'RiskGroup'                     : 'str',
        'RiskClass'                     : 'str',
        'Bucket'                        : 'str',
        'SubBucket'                     : 'str',
        'Sensitivity'                   : 'float64',
        'HedgeSensitivity'              : 'float64',
    },
    'CS_CMDelta' : {
        'RiskGroup'                     : 'str',
        'RiskClass'                     : 'str',
        'Bucket'                        : 'str',
        'SubBucket'                     : 'str',
        'Sensitivity'                   : 'float64',
        'HedgeSensitivity'              : 'float64',
    },
    'CS_CMVega' : {
        'RiskGroup'                     : 'str',
        'RiskClass'                     : 'str',
        'Bucket'                        : 'str',
        'SubBucket'                     : 'str',
        'Sensitivity'                   : 'float64',
        'HedgeSensitivity'              : 'float64',
    },
    'CB_REDUCED' : {
        'RiskGroup'                     : 'str',
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
        self._params = {'FNetFormatVersion' : '1.0'}
        self._sensis = {}
        self._riskGroups = set()
        self._tests = {}

    def load(self, filepath):
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File '{filepath}' not found")
            return None

        if not os.path.isfile(filepath):
            raise ValueError(f"'{filepath}' is not a file")
            return None

        if os.path.getsize(filepath) == 0:
            raise ValueError(f"File '{filepath}' is empty")
            return None

        with  pd.ExcelFile(filepath) as fnf:
            for sheet in fnf.sheet_names:
                if sheet == self.FNF_Params_Tab:
                    df = pd.read_excel(fnf, sheet_name=self.FNF_Params_Tab, header=None)
                    self._params =FNU.extractKeyedData(self.FNF_Params_Tab, df, {})  # empty dataTypes dictionary as all are assumed to be 'str'ings
                elif sheet in self.FNF_Test_Tabs:
                    unitTests = pd.read_excel(fnf, sheet_name=sheet, dtype=str)
                    colNames = [x for x in unitTests.columns if x not in ['Test ID',
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
                            print(f"Required column {col} not found in {sheet}")
                        elif dtype == 'bool':
                            df.loc[:, col] = df[col].apply(lambda x : False if x == 'False' else True)
                            typemap[col] = dtype
                        else:
                            df.loc[:, col] = df[col].fillna(FNU._fillnaMap[dtype])
                            typemap[col] = dtype

                    df = df.astype(typemap)
                    self._sensis[sheet] = df
                    self._riskGroups |= set(df['RiskGroup'].unique())
                elif sheet != self.FNF_Copyright_Tab:
                    print(f"Unknown sheet '{sheet}' in file '{filepath}'")

        self._filename = filepath

        if not self._sensis :
            return None
        else:
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


    def save(self, filename):
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
    path = os.path.join(os.sep, 'Volumes', 'home', 'FRTB', 'Testing', 'UnitTests_BCBS_FNetF_Generated_v0.2.xlsx')
    CS = fnf.load(path)
    print(fnf._params)

    if CS is not None:
        print(CS)

