"""
Convert the PRA's CVA unit test template into FNetF file format.

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
import sys
import datetime as dt
import numpy as np
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import FNetF


cf = { #  PRA Excel Tab                 : (cols,  FNetFRiskClass,   ISDARiskClass,  SensiComboPrefix)
        'IR'                            : ('A:G', 'CS_IR',          'GIRR',         'PRA_IR'),
        'FX'                            : ('A:E', 'CS_FX',          'FX',           'PRA_FX'),
        'Counterparty_Credit_Spread'    : ('A:J', 'CS_CC',          'CS_CPY',       'PRA_CC'),
        'EQ'                            : ('A:F', 'CS_EQ',          'EQ',           'PRA_EQ'),
        'Reference_Credit_Spread'       : ('A:F', 'CS_CR',          'CS_REF',       'PRA_CR'),
        'COM'                           : ('A:F', 'CS_CM',          'COMM',         'PRA_CM'),
}

ColMap = {
        # PRA Name            : FNetF name
        # 'Item'              : 'Sensitivity ID',
        # 'Qualifier_1'       : '',
        # 'Qualifier_2'       : '',
        # 'Qualifier_3'       : '',
        # 'Qualifier_4'       : '',
        # 'Qualifier_5'       : '',
        # 'Qualifier_6'       : '',
        # 'Risk_Type'         : 'RiskType',
        # 'S_k^{CVA}[USD]'    : 'Sensitivity',
        # 'S_k^{Hdg}[USD]'    : 'HedgeSensitivity',
    'IR' : {
        'Item'              : 'Sensitivity ID',
        'Qualifier_1'       : 'Bucket',
        'Qualifier_2'       : 'CurveType',
        'Qualifier_3'       : 'Tenor',
        'Risk_Type'         : 'RiskType',
        'S_k^{CVA}[USD]'    : 'Sensitivity',
        'S_k^{Hdg}[USD]'    : 'HedgeSensitivity',
    },
    'FX' : {
        'Item'              : 'Sensitivity ID',
        'Qualifier_1'       : 'Bucket',
        'Risk_Type'         : 'RiskType',
        'S_k^{CVA}[USD]'    : 'Sensitivity',
        'S_k^{Hdg}[USD]'    : 'HedgeSensitivity',
    },
    'Counterparty_Credit_Spread' : {
        'Item'              : 'Sensitivity ID',
        'Qualifier_1'       : 'CreditName',
        'Qualifier_2'       : 'Bucket',
        'Qualifier_3'       : 'SubBucket',
        'Qualifier_4'       : 'IG_HYNR',
        'Qualifier_5'       : 'ParentName',
        'Qualifier_6'       : 'Tenor',
        'Risk_Type'         : 'RiskType',
        'S_k^{CVA}[USD]'    : 'Sensitivity',
        'S_k^{Hdg}[USD]'    : 'HedgeSensitivity',
    },
    'EQ' : {
        'Item'              : 'Sensitivity ID',
        'Qualifier_1'       : 'Issuer',
        'Qualifier_2'       : 'Bucket',
        'Risk_Type'         : 'RiskType',
        'S_k^{CVA}[USD]'    : 'Sensitivity',
        'S_k^{Hdg}[USD]'    : 'HedgeSensitivity',
    },
    'Reference_Credit_Spread' : {
        'Item'              : 'Sensitivity ID',
        'Qualifier_1'       : 'CreditName',
        'Qualifier_2'       : 'Bucket',
        'Risk_Type'         : 'RiskType',
        'S_k^{CVA}[USD]'    : 'Sensitivity',
        'S_k^{Hdg}[USD]'    : 'HedgeSensitivity',
    },
    'COM' : {
        'Item'              : 'Sensitivity ID',
        'Qualifier_1'       : 'CommodityName',
        'Qualifier_2'       : 'Bucket',
        'Risk_Type'         : 'RiskType',
        'S_k^{CVA}[USD]'    : 'Sensitivity',
        'S_k^{Hdg}[USD]'    : 'HedgeSensitivity',
    },
}

TenorMap = {
    # '0.25y' : '0.25',
    '0.5y'  : '0.5',
    '1y'    : '1',
    '2y'    : '2',
    '3y'    : '3',
    '5y'    : '5',
    '10y'   : '10',
    # '15y'   : '15',
    # '20y'   : '20',
    '30y'   : '30',
    'ALL'   : '0',
}

PRA_path = os.path.dirname(__file__)
PRA_file = 'approach-for-credit-valuation-adjustment-risk-sacva-data-template.xlsx'
filename_out = 'UnitTests_PRA_CVA_FNetF.xlsx'
regulator = 'UK-PRA'
ccy = 'GBP'
cob = dt.date(2024, 12, 31)           # a refernce date from which maturities are calculated
btests = pd.DataFrame()
ctests = pd.DataFrame()
fnf = FNetF.FNetF()
praf = pd.ExcelFile(os.path.join(PRA_path, PRA_file))

for sheet in praf.sheet_names:
    if sheet not in cf.keys():
        continue

    cols, FNetFRiskClass, ISDARiskClass, ComboPrefix = cf[sheet]
    cmap = ColMap[sheet]
    df = praf.parse(sheet_name=sheet, header=1, usecols=cols, dtype=str).fillna('')
    df.rename(columns=cmap, inplace=True)

    if 'Tenor' in df.columns:
        df['Tenor'] = df['Tenor'].map(TenorMap)

    df.loc[:, 'RiskGroup'] = 'PRA_CVA_UnitTests'
    df.loc[:, 'RiskSubGroup'] = 'PRA_CVA_UnitTests'
    df.loc[:, 'RiskClass'] = FNetFRiskClass + df['RiskType'].str.capitalize()
    df.loc[:, 'Sensitivity ID'] = df.apply(lambda r : f"{ComboPrefix}_{r['RiskType'][0]}_{int(r['Sensitivity ID']):02d}", axis=1)
    df.loc[:, 'Bucket'] = df['Bucket'].str.removeprefix('Bucket_')

    if FNetFRiskClass == 'CS_CC':
        df.loc[:, 'IG_HYNR'] = df['IG_HYNR'].str.replace('HY', 'HY_NR')
    else:
        df.loc[:, 'SubBucket'] = ''

        if FNetFRiskClass == 'CS_IR':
            df.loc[:, 'CurveType'] = df['CurveType'].str.replace('Inflation', 'INFL')

    for rc in df['RiskClass'].unique():
        rcdf = df[df['RiskClass']==rc]
        fnf.setRiskClassData(rc, rcdf.reset_index())

    n = 1

    for ix, grp in df.groupby(['RiskClass', 'RiskType', 'Bucket'], sort=False):
        newBTests = pd.DataFrame({
                'RiskClass'         : ix[0],
                'Description'        : f"{FNetFRiskClass}{ix[1].capitalize()}, Bucket {ix[2]}",
                'Sensitivity IDs'   : ', '.join(grp['Sensitivity ID'].unique()),
                'Sb'                : 0,
                'Kb_M'              : 0,
                # 'Kb_L'              : None,
                # 'Kb_H'              : None,
            }, index=pd.Index([ComboPrefix + '_B_' + f'{n:02d}'], name='Test ID' ))

        n += 1
        btests = pd.concat([btests, newBTests], axis=0)

    # Now add the combinations that collect all the sensitivities for a particular asset class
    newCTests = pd.DataFrame({
            'RiskClass'         : FNetFRiskClass + 'Delta',
            'Description'       : f"ALL {FNetFRiskClass}Delta",
            'Sensitivity IDs'   : f"ALL {ComboPrefix}_D_",
            'SumSb'             : 0,
            'Medium'            : 0,
        }, index=pd.Index([ComboPrefix + '_C_01'], name='Test ID' ))

    ctests = pd.concat([ctests, newCTests], axis=0)

    if FNetFRiskClass != 'CS_CC':
        newCTests = pd.DataFrame({
            'RiskClass'         : FNetFRiskClass + 'Vega',
            'Description'       : f"ALL {FNetFRiskClass}Vega",
            'Sensitivity IDs'   : f"ALL {ComboPrefix}_V_",
            'SumSb'             : 0,
            'Medium'            : 0,
            }, index=pd.Index([ComboPrefix + '_C_02'], name='Test ID' ))

        ctests = pd.concat([ctests, newCTests], axis=0)

fnf.setUnitTests('BucketTests', btests.reset_index())
fnf.setUnitTests('CapitalTests', ctests.reset_index())

# save the generated unit tests
fnf.setParam('COB Date', cob.isoformat())
fnf.setParam('Regulator', regulator)
fnf.setParam('ReportingCcy', ccy)
fnf.setParam('CalculationCcy', ccy)
fnf.save(os.path.join(PRA_path, filename_out))
print(f"PRA CVA Unit tests saved in {filename_out}")
