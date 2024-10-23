"""
Calculate the Basel III CVA capital requirement using the Basic Approach within the frtb.net framework.

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

import abc
import pandas as pd
import math

import FRTBCalculator


class CB_BA_BA_CVA(FRTBCalculator.FRTBCalculator):
    def __init__(self, assetClass, regulator, ccy, cob):
        super().__init__(assetClass, regulator, ccy, cob)
        self._DS = self.getConfigItem('BA-DiscountScalar')
        self._rho = self.getConfigItem('BA-Rho')


    def getConfigItem(self, item):
        return self._config.getConfigItem('CVA', item)


    # This is the primary entry point and computes capital for a single risk class
    # at all the necessary correlation levels.  It returns a Dictionary with an entry
    # for RiskClass and an entry for each computed result, such as the capital
    # at each of the correlation levels.  E.g.:
    #   {
    #       'RiskClass' : 'CB_BACVA',
    #       'Medium'    : 123.45,
    #   }
    #
    @abc.abstractmethod
    def calcRiskClassCapital(self, riskClass, df):
        pass

    def calcSCVA(self, df):
        alpha = self.getConfigItem('BA_Alpha')
        RW = self.getConfigItem('BA_RiskWeight')
        df.loc[:, 'RW'] = df.apply(lambda r : RW.at[r['IG_HYNR', r['Bucket']]], axis=1)
        df.loc[:, 'DiscountFactor'] = df.apply(lambda r : ((1 - math.exp(-0.05 * r['NettingSetMatiurity'])) / (0.05 * r['NettingSetMaturity'])), axis=1)
        df.loc[:, 'SCVA'] = df['RW'] * df['NettingSetMaturity'] * df['EAD'] * df['DiscountFactor']
        df.loc[df['PositiionType']=='Exposure', 'SCVA'] = df.loc[df['PositiionType']=='Exposure', 'SCVA'] / alpha
        return df

    def _reducedBACVA(self, riskClass, df):
        if df.empty:
            return 0.0
        else:
            rBACVA = df['CreditName', 'SCVA'].goupby('CreditName').sum()   # .reset_index() ?
            return (((self._rho  * rBACVA.sum()) ** 2 + ((1 - self._rho ** 2) * rBACVA.pow(2).sum())) ** 0.5)


@FRTBCalculator.registerClass
class CB_RE_BACVA_Reduced(CB_BA_BA_CVA):
    def calcRiskClassCapital(self, riskClass, df):
        df = self.calcSCVA(df)
        BACVA = {}
        BACVA['RiskClass'] = riskClass
        BACVA['Correlation'] = 'Medium'
        BACVA['DiscountScalar'] = self._DS
        BACVA['K_Reduced'] = self._reducedBACVA(riskClass, df)
        BACVA['Capital'] = self._DS * BACVA['K_Reduced']
        return [ BACVA ]


@FRTBCalculator.registerClass
class CB_FU_BACVA_Full(CB_BA_BA_CVA):
    def __init__(self, assetClass, regulator, ccy, cob, **kwargs):
        super().__init__(assetClass, regulator, ccy, cob, **kwargs)
        self._rDirect = self.getConfigItem('BA-rDirect')
        self._rRelated = self.getConfigItem('BA-rRelated')
        self._rSectorRegion = self.getConfigItem('BA-rSectorRegion')


    def calcRiskClassCapital(self, riskClass, df):
        df = self.calcSCVA(df)
        BACVA = {}
        BACVA['RiskClass'] = riskClass
        BACVA['Correlation'] = 'Medium'
        BACVA['DiscountScalar'] = self._DS
        BACVA['Beta'] = beta = self.getConfigItem('BA_Beta')
        BACVA['K_Reduced'] = self._reducedBACVA(riskClass, df)
        BACVA['K_Hedged'] = self._hedgedBACVA(riskClass, df)
        BACVA['K_Full'] = (beta * BACVA['K_Reduced'] + (1 - beta) * BACVA['K_Hedged'])
        BACVA['Capital'] = self._DS * BACVA['K_Full']
        return [ BACVA ]

    # Calculate the Hedged BA CVA for all exposures and their hedges
    #
    def _hedgedBACVA(self, riskClass, df):
        # Compute SNH(c) for each counterparty group
        SNHedge = df.groupby('CounterpartyGroup').apply(self._CounterpartyGroupHedgedBACVA)
        IHedge = df[(df['PositionType'] == 'IndexHedge')]

        if IHedge.empty:
            IH = 0.0
        else:
            IH = IHedge['SCVA'].sum() * self.getConfigItem('BA-IndexDiversification')

        SCVA = df[df['PositionType'] == 'Exposure', ['CounterpartyGroup', 'SCVA']].groupby(['CounterpartyGroup', 'ParentName', 'CreditName']).sum().reset_index()
        Kh_parts = SCVA.merge(SNHedge, left_index=True, right_index=True, how='outer').fillna(0.0)
        K_Hedged = (self._rho * (Kh_parts['SCVA'].minus(df['SNH'].sum())) ** 2 +
                     ((1 - self._rho ** 2) * df['SCVA'].minus(df['SNH'].pow(2).sum())) +
                       df['HMA'].sum()) ** 0.5
        return K_Hedged

    # Calculate the Hedged BA CVA for a single exposure and its hedges
    #
    def _CounterpartyGroupHedgedBACVA(self, riskClass, df):
        expDf = df[df['PositionType'] == 'Exposure']
        name = expDf.at['CreditName']
        parent = expDf.at['ParentName']
        group = expDf.at['CounterpartyGroup']
        SCVA = expDf['SCVA'].sum()
        SNhedgeDf = df[df['PositionType'] == 'Hedge']

        if SNhedgeDf.empty:
            return(pd.Series({'SNH' : 0.0, 'HMA' : 0.0}))
        else:
            SNhedgeDf = SNhedgeDf[['CounterpartyGroup', 'ParentName', 'CreditName', 'SCVA']].groupby(['CounterpartyGroup', 'ParentName', 'CreditName']).sum().reset_index()
            SNhedgeDf.loc[:, 'rhc'] = SNhedgeDf.apply(lambda r : self._rDirect if r.at['CreditName'] == name else
                                                                 self._rRelated if r.at['ParentName'] == parent else
                                                                 self._rSectorRegion if r.at['CounterpartyGroup'] == group else
                                                                 0.0 # this should never happen
                                                            , axis=1)
            SNhedgeDf.loc[:, 'SNH'] = SNhedgeDf['SCVA'] * SNhedgeDf['rhc']
            SNhedgeDf.loc[:, 'HMA'] = SNhedgeDf['SCVA'].pow(2) * (1 - (SNhedgeDf['rhc'].pow(2)))
            return SNhedgeDf[['SNH', 'HMA']].sum()
