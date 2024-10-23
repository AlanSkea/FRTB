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
    dropCols = ['RiskClass']
    return capdf.reset_index().drop(columns=dropCols)


def summariseBucket(ds):
    df = pd.DataFrame(ds).set_index(['RiskClass', 'Bucket', 'Correlation'])
    ndf = df['Kb'].unstack().merge(df.loc[(slice(None), slice(None), 'Medium'), ['Sb']].droplevel(level=2), left_index=True, right_index=True).rename(columns=dict((k, f'Kb_{k[0]}') for k in ['Low', 'Medium', 'High']))
    dropCols = ['RiskClass', 'Bucket']
    return ndf.reset_index().drop(columns=dropCols)


if __name__ == '__main__':
    regulator = 'UK-PRA'
    path = os.path.dirname(__file__)
    infile = os.path.join(path, 'UnitTests_PRA_CVA_FNetF.xlsx')
    outfile = os.path.join(path, 'UnitTests_PRA_CVA_FNetF_out.xlsx')
    fnf = FNetF.FNetF()
    CS = fnf.load(infile)
    ccy = fnf.getParam('ReportingCcy')
    cob = dt.date.fromisoformat(fnf.getParam('COB Date'))

    with pd.ExcelWriter(outfile) as writer:
        for testSet in ['BucketTests', 'CapitalTests']:
            grp1 = CS.loc[testSet, :]
            testSetCapital = pd.DataFrame()

            for combo, grp2 in grp1.groupby('Test ID'):
                comboRCcapital = pd.DataFrame()

                for riskClass, grp3 in grp2.groupby('RiskClass'):
                    df = fnf.getRiskClassData(riskClass)
                    df = df[df['Sensitivity ID'].isin(grp3['Sensitivity ID'])]
                    calc = frtb.FRTBCalculator.create(riskClass[:5], regulator, ccy, cob)

                    if testSet == 'CapitalTests':
                        capRes = calc.calcRiskClassCapital(riskClass, df)
                        cap = summariseCapital(capRes)
                    elif testSet == 'BucketTests':
                        bucketRes = []

                        for bucket, grp4 in df.groupby('Bucket'):
                            rfdf = calc.prepareData(riskClass, grp4)
                            rfdf = calc.applyRiskWeights(riskClass, rfdf)
                            rfdf = calc.collectRiskFactors(riskClass, rfdf)
                            BC = calc.getBucketCalculator(riskClass, bucket)
                            bucketRes.extend(BC(riskClass, bucket, rfdf))

                        cap = summariseBucket(bucketRes)

                    cap.loc[:, 'Test ID'] = combo
                    comboRCcapital = pd.concat([comboRCcapital, cap.T], axis=1)

                comboRCcapital = comboRCcapital.T.groupby('Test ID').sum()
                testSetCapital = pd.concat([testSetCapital, comboRCcapital], axis=0)

            print(f'{testSetCapital.shape[0]} {testSet} results computed')
            testSetCapital.to_excel(writer, sheet_name=testSet)#, index=False)

    print(f'Results created in {outfile}')
