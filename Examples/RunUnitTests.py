"""
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
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import FNetF
import FRTBCalculator as frtb

# while the calcuator classess below are are not directly referenced, they need
# to be imported here so that they can register themselves with the FRTBCaclulator
#
import SA_SBM_Calc
import SA_DRC_Calc
import SA_RRAO_Calc
import BA_CVA_Calc


def summariseCapital(ds):
    df = pd.DataFrame(ds).set_index(['RiskClass', 'Correlation'])
    capdf = df['Capital'].unstack()

    if 'SumSb' in df.columns:
        bitingCorrelation = capdf.idxmax(axis=1).iloc[0]
        capdf.loc[:, 'SumSb'] = df.loc[(slice(None), bitingCorrelation),'SumSb'].iat[0]

    if 'SbAlt' in df.columns:
        altdf = df['SbAlt'].unstack().rename(columns=dict((k, f'SbAlt_{k}') for k in ['Low', 'Medium', 'High']))
        capdf = capdf.merge(altdf, left_index=True, right_index=True)

    dropCols = ['RiskClass']
    return capdf.reset_index().drop(columns=dropCols)


if __name__ == '__main__':
    regulator = 'BCBS'
    testVersion = '0.6'
    path = os.path.dirname(__file__)
    infile = os.path.join(path, f'UnitTests_{regulator}_FNetF_v{testVersion}.xlsx')
    outfile = os.path.join(path, f'UnitTests_{regulator}_FNetF_v{testVersion}_out.xlsx')
    fnf = FNetF.FNetF()
    CS = fnf.load(infile)
    ccy = fnf.getParam('ReportingCcy')
    cob = dt.date.fromisoformat(fnf.getParam('COB Date'))
    testSetResults = {}
    calculators = {}

    grp1 = CS.loc['CapitalTests', :]
    testSetCapital = pd.DataFrame()

    for combo, grp2 in grp1.groupby('Test ID'):
        comboRCcapital = pd.DataFrame()

        for riskClass, grp3 in grp2.groupby('RiskClass'):
            df = fnf.getRiskClassData(riskClass)
            df = df[df['Sensitivity ID'].isin(grp3['Sensitivity ID'])]

            if riskClass in calculators.keys():
                calc = calculators[riskClass]
            else:
                calc = frtb.FRTBCalculator.create(riskClass[:5], regulator, ccy, cob)
                calculators[riskClass] = calc

            capRes = calc.calcRiskClassCapital(riskClass, df)
            cap = summariseCapital(capRes)
            cap.loc[:, 'Test ID'] = combo
            comboRCcapital = pd.concat([comboRCcapital, cap.T], axis=1)

        comboRCcapital = comboRCcapital.T.groupby('Test ID').sum()
        testSetCapital = pd.concat([testSetCapital, comboRCcapital], axis=0)

    testSetBenchmark = fnf.getUnitTests('CapitalTests')
    testSetCapital = testSetBenchmark.merge(testSetCapital, how="right", on='Test ID')
    testSetCapital.loc[:, 'OK'] = (
                (testSetCapital['Benchmark_Low'].isna() | (testSetCapital['Low'] - testSetCapital['Benchmark_Low']).abs().lt(0.01)) &
                (testSetCapital['Benchmark_Medium'].isna() | (testSetCapital['Medium'] - testSetCapital['Benchmark_Medium']).abs().lt(0.01)) &
                (testSetCapital['Benchmark_High'].isna() | (testSetCapital['High'] - testSetCapital['Benchmark_High']).abs().lt(0.01)) &
                (testSetCapital['Benchmark_SbAlt_Low'].isna() | (testSetCapital['SbAlt_Low'] - testSetCapital['Benchmark_SbAlt_Low']).abs().eq(0.0)) &
                (testSetCapital['Benchmark_SbAlt_Medium'].isna() | (testSetCapital['SbAlt_Medium'] - testSetCapital['Benchmark_SbAlt_Medium']).abs().eq(0.0)) &
                (testSetCapital['Benchmark_SbAlt_High'].isna() | (testSetCapital['SbAlt_High'] - testSetCapital['Benchmark_SbAlt_High']).abs().eq(0.0)) &
                (testSetCapital['Benchmark_SumSb'].isna() | (testSetCapital['SumSb'] - testSetCapital['Benchmark_SumSb']).abs().lt(0.01))
            )

    fails = testSetCapital[testSetCapital['OK'] == False]

    if fails.empty:
        print(f'All {testSetCapital.shape[0]} tests passed')
    else:
        print(fails)
        print(f'{fails.shape[0]} out of {testSetCapital.shape[0]} tests failed')

    testSetCapital.to_excel(outfile, sheet_name='CapitalTests', index=False)
