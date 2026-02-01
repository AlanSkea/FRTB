"""
Calculate the Basel III Standardised Approach Market Risk Sensitivity Based Method
Capital reqirements and the Standardised Approach CVA Capital requirements within
the frtb.net framework

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
import numpy as np
import pandas as pd

import FRTBCalculator

class SA_SBM_Calc(FRTBCalculator.FRTBCalculator):
    # This is the primary entry point and computes capital for a single risk class
    # at all the necessary correlation levels.  It returns a Dictionary with an entry
    # for RiskClass and an entry for each computed result, such as the capital
    # at each of the correlation levels.  E.g.:
    #   {
    #       'RiskClass' : 'MS_IRDelta',
    #       'Low'       : 123.45,
    #       'Medium'    : 234.56,
    #       'High'      : 345.67
    #   }
    #
    def calcRiskClassCapital(self, riskClass, df):
        bucketResults = []

        for bucket, bucketSensis in df.groupby('Bucket'):
            bdf = self.prepareData(riskClass, bucketSensis)
            bdf = self.applyRiskWeights(riskClass, bdf)
            bdf = self.collectRiskFactors(riskClass, bdf)
            bucketResult = self.getBucketCalculator(riskClass, bucket)(riskClass, bucket, bdf)
            bucketResults.extend(bucketResult)

        buckets = pd.DataFrame(bucketResults)
        # TODO : The Multiplier for SA-CVA must be applied somewhere!
        # multiplier = float(self.getConfigItem('CVA', 'SA-CapitalMultiplier')) if self._CVA else 1.0

        # return self.getRiskClassCalculator(riskClass)(riskClass, buckets)
        if riskClass[5:] == 'Curvature':
            return self.calcCurvature(riskClass, buckets)
        else:
            return self.calcDeltaVega(riskClass, buckets)


    # In some RiskClasses this is overridden so that the "Other" bucket uses the "OtherBucket" calculator
    def getBucketCalculator(self, riskClass, bucket):
        if riskClass[5:] == 'Curvature':
            return self.calcCurvatureBucket
        else:
            return self.calcDeltaVegaBucket

    # TODO : If we want to abstract away from the all the method names ...
    #        perhaps we need a call that would return a list of methods
    #        to be called in sequence with each subsequent method using
    #        the results of the previous method.
    #
    # def getRiskClassCalculator(self, riskClass):
    #     if riskClass[5:] == 'Curvature':
    #         return self.calcCurvature
    #     else:
    #         return self.calcDeltaVega


    def calcDeltaVegaBucket(self, riskClass, bucket, rfdf):
        bucketCapitals = []

        if self._CVA:
            WS = rfdf['WeightedSensitivity'] - rfdf['WeightedHedgeSensitivity']
            WHS = rfdf['WeightedHedgeSensitivity']
            hedgeDisallow = (WHS.pow(2)).sum() * self._hedgeDisallowance
        else:
            WS = rfdf['WeightedSensitivity']
            hedgeDisallow = 0.0

        rho = self.getRho(riskClass, bucket, rfdf)

        for corr in self._correlationLevels:
            bucketCapital = {}
            bucketCapital['RiskClass'] = riskClass
            bucketCapital['Bucket'] = bucket
            bucketCapital['Correlation'] = corr
            bucketCapital['SumSensitivity'] = rfdf['Sensitivity'].sum()
            bucketCapital['SumSensitivity+ve'] = rfdf[rfdf['Sensitivity'] >= 0]['Sensitivity'].sum()
            bucketCapital['SumSensitivity-ve'] = rfdf[rfdf['Sensitivity'] < 0]['Sensitivity'].sum()
            scaledRho = self.scaleCorrelation(corr, rho, 1)
            KbC1 = max(np.matmul(np.matmul(WS.values, scaledRho), WS.values), 0.0)
            bucketCapital['Kb'] = (KbC1 + hedgeDisallow) ** 0.5
            bucketCapital['Sb'] = WS.sum()

            if self._CVA:
                bucketCapital['Kb_C1'] = KbC1
                bucketCapital['Kb_C2'] = hedgeDisallow
                bucketCapital['SumHedgeSensitivity'] = rfdf['HedgeSensitivity'].sum()
                bucketCapital['SumHedgeSensitivity+ve'] = rfdf[rfdf['HedgeSensitivity'] >= 0]['HedgeSensitivity'].sum()
                bucketCapital['SumHedgeSensitivity-ve'] = rfdf[rfdf['HedgeSensitivity'] < 0]['HedgeSensitivity'].sum()

            bucketCapitals.append(bucketCapital)

        return bucketCapitals


    def calcDeltaVegaOtherBucket(self, riskClass, bucket, rfdf):
        bucketCapitals = []
        WS = rfdf['WeightedSensitivity']
        Kb = WS.abs().sum()

        for corr in self._correlationLevels:
            bucketCapital = {}
            bucketCapital['RiskClass'] = riskClass
            bucketCapital['Bucket'] = bucket
            bucketCapital['Correlation'] = corr
            bucketCapital['SumSensitivity'] = rfdf['Sensitivity'].sum()
            bucketCapital['SumSensitivity+ve'] = rfdf[rfdf['Sensitivity'] >= 0]['Sensitivity'].sum()
            bucketCapital['SumSensitivity-ve'] = rfdf[rfdf['Sensitivity'] < 0]['Sensitivity'].sum()
            bucketCapital['Kb'] = Kb
            bucketCapital['Sb'] = WS.sum()
            bucketCapitals.append(bucketCapital)

        return bucketCapitals


    def calcDeltaVega(self, riskClass, bdf):
        capitals = []

        # Unit Tests sometimees want the bucket-level Sb for single-bucket tests
        # This delivers that but is a bit meaningless for multi-bucket portfolios
        # For CVA there is just Medium correation and for Market Risk the Sb is the
        # same for all correlation levels so we just calculate it once.
        #
        gamma = self.getGamma(bdf[bdf['Correlation'] == 'Medium'])

        for corr in self._correlationLevels:
            capital = {}
            capital['RiskClass'] = riskClass
            scaledGamma = self.scaleCorrelation(corr, gamma, 0)
            nbdf = bdf[bdf['Correlation'] == corr].set_index('Bucket')
            Kb = nbdf['Kb']
            Kb2 = nbdf['Kb'] ** 2
            Sb = nbdf['Sb']
            SbAlt = np.maximum(np.minimum(Sb, Kb), -Kb)
            capital['SumSb'] = Sb.sum()
            capital['SumSbAlt'] = SbAlt.sum()
            cap = Sb.T @ scaledGamma @ Sb + Kb2.sum()

            if self._CVA or cap < 0:
                cap = SbAlt.T.dot(scaledGamma).dot(SbAlt) + Kb2.sum()
                capital['SbAlt'] = 1
            else:
                capital['SbAlt'] = 0

            capital['Correlation'] = corr
            capital['Capital'] = cap ** 0.5
            capitals.append(capital)

        return capitals


    def calcCurvatureBucket(self, riskClass, bucket, rfdf):
        bucketCapitals = []
        ndf = self.collectRiskFactors(riskClass, rfdf)
        rho = self.getRho(riskClass, bucket, ndf)
        cvrPlus = ndf['CVR+']
        cvrMinus = ndf['CVR-']
        psiPlus = 1 - np.outer(cvrPlus.lt(0), cvrPlus.lt(0))
        psiMinus = 1 - np.outer(cvrMinus.lt(0), cvrMinus.lt(0))
        SbPlus = cvrPlus.sum()
        SbMinus = cvrMinus.sum()

        for corr in self._correlationLevels:
            # scaledRho = self.scaleCorrelation(corr, rho, 1) ** 2
            # Industry consesus is square beofre scaling
            bucketCapital = {}
            bucketCapital['RiskClass'] = riskClass
            bucketCapital['Bucket'] = bucket
            bucketCapital['Correlation'] = corr
            scaledRho = self.scaleCorrelation(corr, rho ** 2, 1)
            bucketKbPlus = max(np.matmul(np.matmul(cvrPlus.values, psiPlus * scaledRho), cvrPlus.values), 0.0) ** 0.5
            bucketKbMinus = max(np.matmul(np.matmul(cvrMinus.values, psiMinus * scaledRho), cvrMinus.values), 0.0) ** 0.5
            bucketCapital['Kb+'] = bucketKbPlus
            bucketCapital['Kb-'] = bucketKbMinus
            bucketCapital['Sb+'] = SbPlus
            bucketCapital['Sb-'] = SbMinus

            if bucketKbPlus > bucketKbMinus or (bucketKbPlus == bucketKbMinus and SbPlus > SbMinus):
                bucketCapital['Direction'] = 'Up'
                bucketCapital['Kb'] = bucketKbPlus
                bucketCapital['Sb'] = SbPlus
            else:
                bucketCapital['Direction'] = 'Down'
                bucketCapital['Kb'] = bucketKbMinus
                bucketCapital['Sb'] = SbMinus

            bucketCapitals.append(bucketCapital)

        return bucketCapitals


    def calcCurvatureOtherBucket(self, riskClass, bucket, rfdf):
        bucketCapitals = []
        ndf = self.collectRiskFactors(riskClass, rfdf)
        KbPlus = np.maximum(ndf['CVR+'].values, 0.0).sum()
        KbMinus = np.maximum(ndf['CVR-'].values, 0.0).sum()
        SbPlus = ndf['CVR+'].sum()
        SbMinus = ndf['CVR-'].sum()

        for corr in self._correlationLevels:
            bucketCapital = {}
            bucketCapital['RiskClass'] = riskClass
            bucketCapital['Bucket'] = bucket
            bucketCapital['Correlation'] = corr
            bucketCapital['Kb+'] = KbPlus
            bucketCapital['Kb-'] = KbMinus
            bucketCapital['Sb+'] = SbPlus
            bucketCapital['Sb-'] = SbMinus

            if KbPlus > KbMinus or (KbPlus == KbMinus and SbPlus > SbMinus):
                bucketCapital['Direction'] = 'Up'
                bucketCapital['Kb'] = KbPlus
                bucketCapital['Sb'] = SbPlus
            else:
                bucketCapital['Direction'] = 'Down'
                bucketCapital['Kb'] = KbMinus
                bucketCapital['Sb'] = SbMinus

            bucketCapitals.append(bucketCapital)

        return bucketCapitals


    def calcCurvature(self, riskClass, bdf):
        capitals = []
        gamma = self.getGamma(bdf[bdf['Correlation'] == 'Medium'])

        for corr in self._correlationLevels:
            capital = {}
            capital['RiskClass'] = riskClass
            # scaledGamma = self.scaleCorrelation(corr, gamma, 0) * 2
            # Industry consesus is square beofre scaling. SA-SARB (1 July 2025) rules are explicit on this.
            scaledGamma = self.scaleCorrelation(corr, gamma ** 2, 0)
            nbdf = bdf[bdf['Correlation'] == corr].set_index('Bucket')
            psi = 1 - np.outer(nbdf['Sb'].lt(0), nbdf['Sb'].lt(0))
            Kb2 = nbdf['Kb'] ** 2
            Sb = nbdf['Sb']
            capital['SumSb'] = Sb.sum()
            capital['Correlation'] = corr
            capital['Capital'] = max(Sb.T.dot(psi * scaledGamma).dot(Sb) + Kb2.sum(), 0.0) ** 0.5
            capitals.append(capital)

        # Unit Tests sometimees want the bucket-level Sb for single-bucket tests.  This delivers
        # that but is a bit meaningless for multi-bucket portfolios. for Market Risk the Sb is the
        # same for all correlation levels so we just calculate it once.
        #
        return capitals


    def getFactorNettingFields(self, riskClass):
        return self._rhoFactorFields[riskClass[5:]].copy()


    def collectRiskFactors(self, riskClass, df):
        # df has all the input data for a single Bucket but might be mre granular than the
        # bucket risk factors we need.  So here we aggregate all the rows for the same risk
        # factor into a single row.
        #
        keyFields = ['RiskGroup', 'RiskSubGroup', 'RiskClass', 'Bucket']
        factorFields = self.getFactorNettingFields(riskClass)

        if self._CVA:
            valueFields = ['Sensitivity', 'WeightedSensitivity', 'HedgeSensitivity', 'WeightedHedgeSensitivity']
            factorFields.append('RiskWeight')
        elif riskClass[5:] == 'Curvature':
            valueFields = ['CVR+', 'CVR-']
        else:
            valueFields = ['Sensitivity', 'WeightedSensitivity']
            factorFields.append('RiskWeight')

        ndf = df[keyFields + factorFields + valueFields].groupby(keyFields + factorFields).sum().reset_index()
        return ndf


    def applyRiskWeights(self, riskClass, df):
        ndf = self.getRiskWeights(riskClass, df.copy())

        if 'RiskWeight' in ndf.columns and 'Sensitivity' in ndf.columns: # Curvature won't have both these
            ndf.loc[:, 'WeightedSensitivity'] = ndf['Sensitivity'] * ndf['RiskWeight']

            if self._CVA:
                ndf.loc[:, 'WeightedHedgeSensitivity'] = ndf['HedgeSensitivity'] * ndf['RiskWeight']

        return ndf


    # This method is potentially overridden in the derived classes as there is
    # some variation in how risk weights are determined.  This is the most
    # common case here.
    #
    def getRiskWeights(self, riskClass, df):
        riskType = riskClass[5:]

        if riskType == 'Delta':
            RWBucket = self.getConfigItem('DeltaBucketRiskWeight')
            df.loc[:, 'RiskWeight'] = df.apply(lambda r : RWBucket.at[r['Bucket']+r['SubBucket']], axis=1)
        elif riskType == 'Vega':
            RWVega = self.getConfigItem('VegaRiskWeight')
            df.loc[:, 'RiskWeight'] = RWVega
        else:
            # Curvature - is there any risk weight for curvature?
            # CVR+ and CVR- are already delta-neutralised so nothing to do.
            # If, instead we want to use Vi+ and Vi- then need to think again,
            # we'd need the Vi0 (PV), the shock size and the corresponding Delta.
            pass

        return df


    @abc.abstractmethod
    def getRho(self, riskClass, bucket, df):
        # rho correlations are different for each risk class as the risk factors in each
        # risk class are created from a viariety of risk class specific attributes.  So we
        # leave all the detail to the instances of this method in each subclass.  Here we provide
        # a simple DataFrae that might be (or might not) be useful for the subclasses.
        #
        # We assume that the data has been consolidated into distinct risk factors by this point.
        #
        return pd.DataFrame(np.zeros((df.shape[0], df.shape[0])))


    def getRhoFactors(self, riskClass, bucket, factor1, factor2):
        """
        Returns a detailed breakdown of the correlation factors between two risk factors.

        This method explains why a particular rho correlation value was computed by
        showing the individual attribute comparisons and their corresponding rho
        components. Subclasses should override this method to provide risk-class
        specific factor breakdowns.

        Args:
            riskClass: The risk class (e.g., 'MS_IR_Delta')
            bucket: The bucket identifier
            factor1: Dict or Series with attributes for the first risk factor
            factor2: Dict or Series with attributes for the second risk factor

        Returns:
            dict: {
                'rho': float,           # Final correlation value
                'factors': [            # List of factor comparisons
                    {
                        'name': str,           # Factor name (e.g., 'TenorRho')
                        'description': str,    # Human-readable description
                        'value1': any,         # Attribute value for factor1
                        'value2': any,         # Attribute value for factor2
                        'rho_component': float,# Rho contribution from this factor
                        'config_item': str     # Config item name used (or None)
                    },
                    ...
                ]
            }
        """
        # Base implementation returns empty factors - subclasses override
        return {
            'rho': 0.0,
            'factors': []
        }


    def getGamma(self, df):
        # gamma correlations come in two flavours, either a full matrix of inter-bucket correlations
        # or a single value to be applied between all bucket pairs.  In either case we want to return
        # a full matrix of gamma values for the buckets that are in the input dataframe.   We don't worry
        # about the diagonal of the matrix here as it will be set when we call scaleCorrelation.
        #
        gamma = self.getConfigItem('Gamma')
        buckets = df['Bucket']

        if isinstance(gamma, pd.DataFrame):
            return gamma.loc[buckets, buckets]
        else:
            return pd.DataFrame(np.full((df.shape[0], df.shape[0]), gamma), index=buckets, columns=buckets)


    def scaleCorrelation(self, level, corr, diag):
        # if called with a DataFrane then set the diagonal of the matrix to <diag> as specified by the caller. In general,
        #   for intra-bucket rho factors, diag = 1
        #   for inter-bucket gamma factors, diag = 0
        #
        if level == 'Low':
            newCorr = np.maximum(corr * 0.75, 2 * corr - 1)
        elif level == 'High':
            newCorr = np.minimum(corr * 1.25, 1.0)
        else:
            newCorr = corr.copy() if isinstance(corr, pd.DataFrame) else corr

        if isinstance(newCorr, pd.DataFrame):       # we might be called with a scalar in which case there is no diagonal
            np.fill_diagonal(newCorr.values, diag)

        return newCorr


#%%################################################
###################################################
#                                                 #
# Market Risk Derived classes for each Risk Class #
#                                                 #
###################################################
###################################################


## IR : Interest Rates / GIRR
#
@FRTBCalculator.registerClass
class MS_IR_SA_SBM_Calc(SA_SBM_Calc):
    _rhoFactorFields = {
        'Delta'     : ['CurveType', 'Curve', 'Tenor'],
        'Vega'      : ['CurveType', 'OptionMaturity', 'UnderlyingResidualMaturity'],
        'Curvature' : []
    }

    def getRiskWeights(self, riskClass, df):
        riskType = riskClass[5:]

        if riskType == 'Delta':
            RWTenor = self.getConfigItem('DeltaTenorRiskWeight')
            RWInfl = self.getConfigItem('DeltaInflationRiskWeight')
            RWXCcy = self.getConfigItem('DeltaXCcyBasisRiskWeight')
            baselCcys = set(self.getConfigItem('BaselCcys'))
            baselCcys.add(self._ownCcy)  # TODO : change name to reportingCcy
            df.loc[df['CurveType']=='IR', 'RiskWeight'] = df[df['CurveType']=='IR'].apply(lambda x: RWTenor[x['Tenor']], axis=1)
            df.loc[df['CurveType']=='INFL', 'RiskWeight'] = df[df['CurveType']=='INFL'].apply(lambda x: RWInfl, axis=1)
            df.loc[df['CurveType']=='XCCY', 'RiskWeight'] = df[df['CurveType']=='XCCY'].apply(lambda x: RWXCcy, axis=1)
            df.loc[df['Bucket'].isin(baselCcys), 'RiskWeight'] = df.loc[df['Bucket'].isin(baselCcys), 'RiskWeight'] / (2.0 ** 0.5)
        elif riskType == 'Vega':
            RWVega = self.getConfigItem('VegaRiskWeight')
            df.loc[:, 'RiskWeight'] = RWVega
        else:
            # Curvature - is there any risk weight for curvature?
            # CVR+ and CVR- are already delta-neutralised so nothing to do.
            # If, instead we want to use Vi+ and Vi- then need to think again,
            # we'd need the Vi0 (PV), the shock size and the corresponding Delta.
            pass

        return df

    def getRho(self, riskClass, bucket, df):
        rho = np.zeros((df.shape[0], df.shape[0]))
        factors = df[self._rhoFactorFields[riskClass[5:]]]
        tenorRho = self.getConfigItem('DeltaTenorRho')
        curveRho = self.getConfigItem('DeltaCurveRho')
        inflRho = self.getConfigItem('DeltaInflationRho')
        xCcyRho = self.getConfigItem('DeltaXCcyBasisRho')
        optionTenorRho = self.getConfigItem('VegaOptionTenorRho')
        underlyingTenorRho = self.getConfigItem('VegaUnderlyingTenorRho')

        for i, r in enumerate(factors.itertuples(index=False)):
            for j, c in enumerate(factors.itertuples(index=False)):
                if i <= j:
                    break

                if riskClass[5:] == 'Delta':
                    if r[0] == 'XCCY' or c[0] == 'XCCY':
                        corr = xCcyRho
                    elif r[0] == 'INFL' or c[0] == 'INFL':
                        if r[0] == c[0]:    # both are INFL
                            corr = 1.0      # different curves are handled below
                        else:
                            corr = inflRho
                    else:
                        corr = tenorRho.at[r[2], c[2]]

                    if r[0] == c[0] and r[1] != c[1]:
                        # Same CurveType, Differnt Curve
                        # i.e. we have two different IR curves
                        #           or two different XCCY curves
                        #           or two different INFL curves
                        corr *= curveRho
                elif riskClass[5:] == 'Vega':
                    if r[0] == 'IR' and c[0] == 'IR':
                        # corr = optionMaturity * underlyingResidualMaturity
                        corr = optionTenorRho.loc[r[1], c[1]] * underlyingTenorRho.loc[r[2], c[2]]
                    elif r[0] == c[0]:
                        # if we get here then both are XCCY or both are INFL
                        # just use the rho for the option maturity
                        corr = optionTenorRho.loc[r[1], c[1]]
                    elif r[0] == 'XCCY' or c[0] == 'XCCY':
                        # just one is XCCY
                        corr = xCcyRho
                    else:
                        # one is INFL and the other is IR
                        corr = inflRho * optionTenorRho.loc[r[1], c[1]]

                    corr = min(corr, 1.0)

                rho[i, j] = rho[j, i] = corr

        return pd.DataFrame(rho, index=df.index, columns=df.index)


    def getGamma(self, df):
        if self._regulator != 'EU-EBA':
            return super().getGamma(df)

        ERMgamma = self.getConfigItem('GammaERMII')
        ERMCcys = self.getConfigItem('ERMIICcys').to_list()
        gamma = self.getConfigItem('Gamma')
        buckets = df['Bucket']
        g = np.zeros((df.shape[0], df.shape[0]))

        for i, rb in enumerate(buckets):
            for j, cb in enumerate(buckets):
                if i <= j:
                    break

                if rb in ERMCcys and cb == 'EUR' or cb in ERMCcys and rb == 'EUR':
                    g[i, j] = g[j, i] = ERMgamma
                else:
                    g[i, j] = g[j, i] = gamma

        return pd.DataFrame(g, index=buckets, columns=buckets)


    def getRhoFactors(self, riskClass, bucket, factor1, factor2):
        riskType = riskClass[5:]
        factors = []
        rho = 1.0

        # Get the attribute values based on risk type
        if riskType == 'Delta':
            # _rhoFactorFields['Delta'] = ['CurveType', 'Curve', 'Tenor']
            ct1, curve1, tenor1 = factor1['CurveType'], factor1['Curve'], factor1['Tenor']
            ct2, curve2, tenor2 = factor2['CurveType'], factor2['Curve'], factor2['Tenor']

            tenorRho = self.getConfigItem('DeltaTenorRho')
            curveRho = self.getConfigItem('DeltaCurveRho')
            inflRho = self.getConfigItem('DeltaInflationRho')
            xCcyRho = self.getConfigItem('DeltaXCcyBasisRho')

            # Determine base correlation based on curve types
            if ct1 == 'XCCY' or ct2 == 'XCCY':
                rho = xCcyRho
                factors.append({
                    'name': 'XCcyBasisRho',
                    'description': 'XCCY basis correlation (one or both factors are XCCY)',
                    'value1': ct1,
                    'value2': ct2,
                    'rho_component': xCcyRho,
                    'config_item': 'DeltaXCcyBasisRho'
                })
            elif ct1 == 'INFL' or ct2 == 'INFL':
                if ct1 == ct2:  # both INFL
                    rho = 1.0
                    factors.append({
                        'name': 'InflationRho',
                        'description': 'Both factors are INFL curves',
                        'value1': ct1,
                        'value2': ct2,
                        'rho_component': 1.0,
                        'config_item': None
                    })
                else:
                    rho = inflRho
                    factors.append({
                        'name': 'InflationRho',
                        'description': 'Inflation vs non-inflation correlation',
                        'value1': ct1,
                        'value2': ct2,
                        'rho_component': inflRho,
                        'config_item': 'DeltaInflationRho'
                    })
            else:
                # Both are IR curves - use tenor correlation
                tenorCorr = tenorRho.at[tenor1, tenor2]
                rho = tenorCorr
                factors.append({
                    'name': 'TenorRho',
                    'description': 'Tenor correlation between IR curves',
                    'value1': tenor1,
                    'value2': tenor2,
                    'rho_component': tenorCorr,
                    'config_item': 'DeltaTenorRho'
                })

            # Apply curve multiplier if same curve type but different curve
            if ct1 == ct2 and curve1 != curve2:
                rho *= curveRho
                factors.append({
                    'name': 'CurveRho',
                    'description': 'Same curve type but different curves',
                    'value1': curve1,
                    'value2': curve2,
                    'rho_component': curveRho,
                    'config_item': 'DeltaCurveRho'
                })

        elif riskType == 'Vega':
            # _rhoFactorFields['Vega'] = ['CurveType', 'OptionMaturity', 'UnderlyingResidualMaturity']
            ct1, optMat1, undMat1 = factor1['CurveType'], factor1['OptionMaturity'], factor1['UnderlyingResidualMaturity']
            ct2, optMat2, undMat2 = factor2['CurveType'], factor2['OptionMaturity'], factor2['UnderlyingResidualMaturity']

            optionTenorRho = self.getConfigItem('VegaOptionTenorRho')
            underlyingTenorRho = self.getConfigItem('VegaUnderlyingTenorRho')
            inflRho = self.getConfigItem('DeltaInflationRho')
            xCcyRho = self.getConfigItem('DeltaXCcyBasisRho')

            if ct1 == 'IR' and ct2 == 'IR':
                optCorr = optionTenorRho.loc[optMat1, optMat2]
                undCorr = underlyingTenorRho.loc[undMat1, undMat2]
                rho = min(optCorr * undCorr, 1.0)
                factors.append({
                    'name': 'OptionTenorRho',
                    'description': 'Option maturity correlation',
                    'value1': optMat1,
                    'value2': optMat2,
                    'rho_component': optCorr,
                    'config_item': 'VegaOptionTenorRho'
                })
                factors.append({
                    'name': 'UnderlyingTenorRho',
                    'description': 'Underlying residual maturity correlation',
                    'value1': undMat1,
                    'value2': undMat2,
                    'rho_component': undCorr,
                    'config_item': 'VegaUnderlyingTenorRho'
                })
            elif ct1 == ct2:
                # Both XCCY or both INFL
                optCorr = optionTenorRho.loc[optMat1, optMat2]
                rho = min(optCorr, 1.0)
                factors.append({
                    'name': 'OptionTenorRho',
                    'description': f'Option maturity correlation (both {ct1})',
                    'value1': optMat1,
                    'value2': optMat2,
                    'rho_component': optCorr,
                    'config_item': 'VegaOptionTenorRho'
                })
            elif ct1 == 'XCCY' or ct2 == 'XCCY':
                rho = xCcyRho
                factors.append({
                    'name': 'XCcyBasisRho',
                    'description': 'XCCY basis correlation (one factor is XCCY)',
                    'value1': ct1,
                    'value2': ct2,
                    'rho_component': xCcyRho,
                    'config_item': 'DeltaXCcyBasisRho'
                })
            else:
                # One INFL, one IR
                optCorr = optionTenorRho.loc[optMat1, optMat2]
                rho = min(inflRho * optCorr, 1.0)
                factors.append({
                    'name': 'InflationRho',
                    'description': 'Inflation vs IR correlation',
                    'value1': ct1,
                    'value2': ct2,
                    'rho_component': inflRho,
                    'config_item': 'DeltaInflationRho'
                })
                factors.append({
                    'name': 'OptionTenorRho',
                    'description': 'Option maturity correlation',
                    'value1': optMat1,
                    'value2': optMat2,
                    'rho_component': optCorr,
                    'config_item': 'VegaOptionTenorRho'
                })

        else:  # Curvature - no intra-bucket correlations in IR
            pass

        return {
            'rho': rho,
            'factors': factors
        }


## CR : Credit Non-Securitisations / CSR_NS
#
@FRTBCalculator.registerClass
class MS_CR_SA_SBM_Calc(SA_SBM_Calc):
    _rhoFactorFields = {
        'Delta'     : ['CreditName', 'CurveType', 'Tenor'],
        'Vega'      : ['CreditName', 'OptionMaturity'],
        'Curvature' : ['CreditName']
    }

    def getRiskWeights(self, riskClass, df):
        if riskClass[5:] != 'Delta':
            return super().getRiskWeights(riskClass, df)

        RWBucket = self.getConfigItem('DeltaBucketRiskWeight')
        # Covered Bonds should already be assigned to the appropriate SubBuckets.
        # CovBondBucket = self.getConfigItem('CoveredBondBucket')
        # CovBondHighQuality = self.getConfigItem('CoveredBondHighQuality')
        ndf = df.reset_index()
        ndf['RiskWeight'] = ndf.apply(lambda r: RWBucket.at[r['Bucket']+r['SubBucket']], axis=1)
        return ndf.set_index(df.index)


    def getRho(self, riskClass, bucket, df):
        rho = np.zeros((df.shape[0], df.shape[0]))
        factors = df[self._rhoFactorFields[riskClass[5:]]]
        indexBuckets = self.getConfigItem('IndexBuckets').to_list()

        if bucket in indexBuckets:
            nameRho = self.getConfigItem('DeltaNameIndexRho')
            tenorRho = self.getConfigItem('DeltaTenorIndexRho')
            basisRho = self.getConfigItem('DeltaBasisIndexRho')
        else:
            nameRho = self.getConfigItem('DeltaNameRho')
            tenorRho = self.getConfigItem('DeltaTenorRho')
            basisRho = self.getConfigItem('DeltaBasisRho')

        for i, r in enumerate(factors.itertuples(index=False)):
            for j, c in enumerate(factors.itertuples(index=False)):
                if i <= j:
                    break

                corr = 1.0

                if r[0] != c[0]:
                    # Different Obligor Names
                    corr *= nameRho

                if riskClass[5:] == 'Delta':
                    if r[1] != c[1]:
                        # Different curve types
                        corr *= basisRho

                    if r[2] != c[2]:
                        # Different tenors
                        corr *= tenorRho
                elif riskClass[5:] == 'Vega':
                    corr = min(corr * self.getConfigItem('VegaOptionTenorRho').at[r[1], c[1]], 1.0)

                rho[i, j] = rho[j, i] = corr

        return pd.DataFrame(rho, index=df.index, columns=df.index)


    def  getBucketCalculator(self, riskClass, bucket):
        otherBucket = self.getConfigItem('OtherBucket')

        if bucket != otherBucket:
            if riskClass[5:] == 'Curvature':
                return self.calcCurvatureBucket
            else:
                return self.calcDeltaVegaBucket
        else:
            if riskClass[5:] == 'Curvature':
                return self.calcCurvatureOtherBucket
            else:
                return self.calcDeltaVegaOtherBucket


    def getRhoFactors(self, riskClass, bucket, factor1, factor2):
        riskType = riskClass[5:]
        factors = []
        rho = 1.0

        indexBuckets = self.getConfigItem('IndexBuckets').to_list()
        isIndex = bucket in indexBuckets
        suffix = 'Index' if isIndex else ''

        if riskType == 'Delta':
            # _rhoFactorFields['Delta'] = ['CreditName', 'CurveType', 'Tenor']
            name1, ct1, tenor1 = factor1['CreditName'], factor1['CurveType'], factor1['Tenor']
            name2, ct2, tenor2 = factor2['CreditName'], factor2['CurveType'], factor2['Tenor']

            nameRho = self.getConfigItem(f'DeltaName{suffix}Rho')
            tenorRho = self.getConfigItem(f'DeltaTenor{suffix}Rho')
            basisRho = self.getConfigItem(f'DeltaBasis{suffix}Rho')

            if name1 != name2:
                rho *= nameRho
                factors.append({
                    'name': 'NameRho',
                    'description': f'Different obligor names ({"index" if isIndex else "non-index"} bucket)',
                    'value1': name1,
                    'value2': name2,
                    'rho_component': nameRho,
                    'config_item': f'DeltaName{suffix}Rho'
                })

            if ct1 != ct2:
                rho *= basisRho
                factors.append({
                    'name': 'BasisRho',
                    'description': f'Different curve types ({"index" if isIndex else "non-index"} bucket)',
                    'value1': ct1,
                    'value2': ct2,
                    'rho_component': basisRho,
                    'config_item': f'DeltaBasis{suffix}Rho'
                })

            if tenor1 != tenor2:
                rho *= tenorRho
                factors.append({
                    'name': 'TenorRho',
                    'description': f'Different tenors ({"index" if isIndex else "non-index"} bucket)',
                    'value1': tenor1,
                    'value2': tenor2,
                    'rho_component': tenorRho,
                    'config_item': f'DeltaTenor{suffix}Rho'
                })

        elif riskType == 'Vega':
            # _rhoFactorFields['Vega'] = ['CreditName', 'OptionMaturity']
            name1, optMat1 = factor1['CreditName'], factor1['OptionMaturity']
            name2, optMat2 = factor2['CreditName'], factor2['OptionMaturity']

            nameRho = self.getConfigItem(f'DeltaName{suffix}Rho')
            optionTenorRho = self.getConfigItem('VegaOptionTenorRho')

            if name1 != name2:
                rho *= nameRho
                factors.append({
                    'name': 'NameRho',
                    'description': f'Different obligor names ({"index" if isIndex else "non-index"} bucket)',
                    'value1': name1,
                    'value2': name2,
                    'rho_component': nameRho,
                    'config_item': f'DeltaName{suffix}Rho'
                })

            optCorr = optionTenorRho.at[optMat1, optMat2]
            rho = min(rho * optCorr, 1.0)
            factors.append({
                'name': 'OptionTenorRho',
                'description': 'Option maturity correlation',
                'value1': optMat1,
                'value2': optMat2,
                'rho_component': optCorr,
                'config_item': 'VegaOptionTenorRho'
            })

        elif riskType == 'Curvature':
            # _rhoFactorFields['Curvature'] = ['CreditName']
            name1 = factor1['CreditName']
            name2 = factor2['CreditName']

            nameRho = self.getConfigItem(f'DeltaName{suffix}Rho')

            if name1 != name2:
                rho *= nameRho
                factors.append({
                    'name': 'NameRho',
                    'description': f'Different obligor names ({"index" if isIndex else "non-index"} bucket)',
                    'value1': name1,
                    'value2': name2,
                    'rho_component': nameRho,
                    'config_item': f'DeltaName{suffix}Rho'
                })

        return {
            'rho': rho,
            'factors': factors
        }


## CC : Credit Securitisations, Correlaion Trading Portfolio (CTP) / CSR_SC
#
@FRTBCalculator.registerClass
class MS_CC_SA_SBM_Calc(SA_SBM_Calc):
    _rhoFactorFields = {
        'Delta' : ['Underlier', 'CurveType', 'Tenor'],
        'Vega' : ['Underlier', 'OptionMaturity'],
        'Curvature' : ['Underlier']
    }

    def getRho(self, riskClass, bucket, df):
        rho = np.zeros((df.shape[0], df.shape[0]))
        factors = df[self._rhoFactorFields[riskClass[5:]]]
        nameRho = self.getConfigItem('DeltaNameRho')
        tenorRho = self.getConfigItem('DeltaTenorRho')
        basisRho = self.getConfigItem('DeltaBasisRho')

        for i, r in enumerate(factors.itertuples(index=False)):
            for j, c in enumerate(factors.itertuples(index=False)):
                if i <= j:
                    break

                corr = 1.0

                if r[0] != c[0]:
                    # Different Obligor Names
                    corr *= nameRho

                if riskClass[5:] == 'Delta':
                    if r[1] != c[1]:
                        # Different curve types
                        corr *= basisRho

                    if r[2] != c[2]:
                        # Different tenors
                        corr *= tenorRho
                elif riskClass[5:] == 'Vega':
                    corr = min(corr * self.getConfigItem('VegaOptionTenorRho').at[r[1], c[1]], 1.0)

                rho[i, j] = rho[j, i] = corr

        return pd.DataFrame(rho, index=df.index, columns=df.index)


    def  getBucketCalculator(self, riskClass, bucket):
        otherBucket = self.getConfigItem('OtherBucket')

        if bucket != otherBucket:
            if riskClass[5:] == 'Curvature':
                return self.calcCurvatureBucket
            else:
                return self.calcDeltaVegaBucket
        else:
            if riskClass[5:] == 'Curvature':
                return self.calcCurvatureOtherBucket
            else:
                return self.calcDeltaVegaOtherBucket


    def getRhoFactors(self, riskClass, bucket, factor1, factor2):
        riskType = riskClass[5:]
        factors = []
        rho = 1.0

        nameRho = self.getConfigItem('DeltaNameRho')
        tenorRho = self.getConfigItem('DeltaTenorRho')
        basisRho = self.getConfigItem('DeltaBasisRho')

        if riskType == 'Delta':
            # _rhoFactorFields['Delta'] = ['Underlier', 'CurveType', 'Tenor']
            name1, ct1, tenor1 = factor1['Underlier'], factor1['CurveType'], factor1['Tenor']
            name2, ct2, tenor2 = factor2['Underlier'], factor2['CurveType'], factor2['Tenor']

            if name1 != name2:
                rho *= nameRho
                factors.append({
                    'name': 'NameRho',
                    'description': 'Different underliers',
                    'value1': name1,
                    'value2': name2,
                    'rho_component': nameRho,
                    'config_item': 'DeltaNameRho'
                })

            if ct1 != ct2:
                rho *= basisRho
                factors.append({
                    'name': 'BasisRho',
                    'description': 'Different curve types',
                    'value1': ct1,
                    'value2': ct2,
                    'rho_component': basisRho,
                    'config_item': 'DeltaBasisRho'
                })

            if tenor1 != tenor2:
                rho *= tenorRho
                factors.append({
                    'name': 'TenorRho',
                    'description': 'Different tenors',
                    'value1': tenor1,
                    'value2': tenor2,
                    'rho_component': tenorRho,
                    'config_item': 'DeltaTenorRho'
                })

        elif riskType == 'Vega':
            # _rhoFactorFields['Vega'] = ['Underlier', 'OptionMaturity']
            name1, optMat1 = factor1['Underlier'], factor1['OptionMaturity']
            name2, optMat2 = factor2['Underlier'], factor2['OptionMaturity']

            optionTenorRho = self.getConfigItem('VegaOptionTenorRho')

            if name1 != name2:
                rho *= nameRho
                factors.append({
                    'name': 'NameRho',
                    'description': 'Different underliers',
                    'value1': name1,
                    'value2': name2,
                    'rho_component': nameRho,
                    'config_item': 'DeltaNameRho'
                })

            optCorr = optionTenorRho.at[optMat1, optMat2]
            rho = min(rho * optCorr, 1.0)
            factors.append({
                'name': 'OptionTenorRho',
                'description': 'Option maturity correlation',
                'value1': optMat1,
                'value2': optMat2,
                'rho_component': optCorr,
                'config_item': 'VegaOptionTenorRho'
            })

        elif riskType == 'Curvature':
            # _rhoFactorFields['Curvature'] = ['Underlier']
            name1 = factor1['Underlier']
            name2 = factor2['Underlier']

            if name1 != name2:
                rho *= nameRho
                factors.append({
                    'name': 'NameRho',
                    'description': 'Different underliers',
                    'value1': name1,
                    'value2': name2,
                    'rho_component': nameRho,
                    'config_item': 'DeltaNameRho'
                })

        return {
            'rho': rho,
            'factors': factors
        }


## CS : Credit Securitisations, non-CTP / CSR_SNC
#
@FRTBCalculator.registerClass
class MS_CS_SA_SBM_Calc(SA_SBM_Calc):
    _rhoFactorFields = {
        'Delta' : ['Underlier', 'CurveType', 'Tenor'],
        'Vega' : ['Underlier', 'OptionMaturity'],
        'Curvature' : ['Underlier']
    }

    def getRho(self, riskClass, bucket, df):
        # won't get called for the "Other" bukcet
        #
        rho = np.zeros((df.shape[0], df.shape[0]))
        factors = df[self._rhoFactorFields[riskClass[5:]]]
        trancheRho = self.getConfigItem('DeltaTrancheRho')
        tenorRho = self.getConfigItem('DeltaTenorRho')
        basisRho = self.getConfigItem('DeltaBasisRho')

        for i, r in enumerate(factors.itertuples(index=False)):
            for j, c in enumerate(factors.itertuples(index=False)):
                if i <= j:
                    break

                corr = 1.0

                if r[0] != c[0]:
                    # Different Issuer / Tranche / Index
                    corr *= trancheRho

                if riskClass[5:] == 'Delta':
                    if r[1] != c[1]:
                        # Different curve types
                        corr *= basisRho

                    if r[2] != c[2]:
                        # Different tenors
                        corr *= tenorRho
                elif riskClass[5:] == 'Vega':
                    corr = min(corr * self.getConfigItem('VegaOptionTenorRho').at[r[1], c[1]], 1.0)

                rho[i, j] = rho[j, i] = corr

        return pd.DataFrame(rho, index=df.index, columns=df.index)


    def  getBucketCalculator(self, riskClass, bucket):
        otherBucket = self.getConfigItem('OtherBucket')

        if bucket != otherBucket:
            if riskClass[5:] == 'Curvature':
                return self.calcCurvatureBucket
            else:
                return self.calcDeltaVegaBucket
        else:
            if riskClass[5:] == 'Curvature':
                return self.calcCurvatureOtherBucket
            else:
                return self.calcDeltaVegaOtherBucket


    # BCBS MAR 21.71 is poorly written and conflates using a gamma factor of 1 with just adding up the bucket-level
    # capitals, which is not the same thing.  It also doesn't mention what happens at different correlation levels.
    # The consesnsus appears to be that the Other bucket capital is treated as a standalaone capital charge and is
    # the same for all levels of correlation.  So we have to separate it out from the other bucket capitals, calculate
    # for them, then add it on at the end.
    #
    # The PRA regs are slightly clearer on this at Article 325ao.
    #
    def calcDeltaVega(self, riskClass, bdf):
        otherBucket = self.getConfigItem('OtherBucket')

        if otherBucket in bdf['Bucket'].values:
            nbdf = bdf[bdf['Bucket'] != otherBucket]
            otherCapital = bdf[bdf['Bucket'] == otherBucket].set_index('Correlation')[['Sb', 'Kb']]
            hasOtherCapital = True
        else:
            nbdf = bdf
            hasOtherCapital = False

        if nbdf.empty:
            newcapitals = []

            for corr in self._correlationLevels:
                capital = {}
                capital['RiskClass'] = riskClass
                capital['Correlation'] = corr
                capital['SbAlt'] = 0
                capital['SumSb'] = otherCapital.at[corr, 'Sb']
                capital['SumSbAlt'] = otherCapital.at[corr, 'Sb']
                capital['Capital'] = otherCapital.at[corr, 'Kb']
                newcapitals.append(capital)
        else:
            capitals = super().calcDeltaVega(riskClass, nbdf)

            if hasOtherCapital:
                newcapitals = []

                for capital in capitals:
                    capital['SumSb'] += otherCapital.at[capital['Correlation'], 'Sb']
                    capital['SumSbAlt'] += otherCapital.at[capital['Correlation'], 'Sb']
                    capital['Capital'] += otherCapital.at[capital['Correlation'], 'Kb']
                    newcapitals.append(capital)
            else:
                newcapitals = capitals

        return newcapitals


    def calcCurvature(self, riskClass, bdf):
        otherBucket = self.getConfigItem('OtherBucket')

        if otherBucket in bdf['Bucket'].values:
            nbdf = bdf[bdf['Bucket'] != otherBucket]
            otherCapital = bdf[bdf['Bucket'] == otherBucket].set_index('Correlation')[['Sb', 'Kb']]
            hasOtherCapital = True
        else:
            nbdf = bdf
            hasOtherCapital = False

        if nbdf.empty:
            newcapitals = []

            for corr in self._correlationLevels:
                capital = {}
                capital['RiskClass'] = riskClass
                capital['Correlation'] = corr
                capital['SumSb'] = otherCapital.at[corr, 'Sb']
                capital['Capital'] = otherCapital.at[corr, 'Kb']
                newcapitals.append(capital)
        else:
            capitals = super().calcCurvature(riskClass, nbdf)

            if hasOtherCapital:
                newcapitals = []

                for capital in capitals:
                    capital['SumSb'] += otherCapital.at[capital['Correlation'], 'Sb']
                    capital['Capital'] += otherCapital.at[capital['Correlation'], 'Kb']
                    newcapitals.append(capital)
            else:
                newcapitals = capitals

        return newcapitals


    def getRhoFactors(self, riskClass, bucket, factor1, factor2):
        riskType = riskClass[5:]
        factors = []
        rho = 1.0

        trancheRho = self.getConfigItem('DeltaTrancheRho')
        tenorRho = self.getConfigItem('DeltaTenorRho')
        basisRho = self.getConfigItem('DeltaBasisRho')

        if riskType == 'Delta':
            # _rhoFactorFields['Delta'] = ['Underlier', 'CurveType', 'Tenor']
            name1, ct1, tenor1 = factor1['Underlier'], factor1['CurveType'], factor1['Tenor']
            name2, ct2, tenor2 = factor2['Underlier'], factor2['CurveType'], factor2['Tenor']

            if name1 != name2:
                rho *= trancheRho
                factors.append({
                    'name': 'TrancheRho',
                    'description': 'Different issuer/tranche/index',
                    'value1': name1,
                    'value2': name2,
                    'rho_component': trancheRho,
                    'config_item': 'DeltaTrancheRho'
                })

            if ct1 != ct2:
                rho *= basisRho
                factors.append({
                    'name': 'BasisRho',
                    'description': 'Different curve types',
                    'value1': ct1,
                    'value2': ct2,
                    'rho_component': basisRho,
                    'config_item': 'DeltaBasisRho'
                })

            if tenor1 != tenor2:
                rho *= tenorRho
                factors.append({
                    'name': 'TenorRho',
                    'description': 'Different tenors',
                    'value1': tenor1,
                    'value2': tenor2,
                    'rho_component': tenorRho,
                    'config_item': 'DeltaTenorRho'
                })

        elif riskType == 'Vega':
            # _rhoFactorFields['Vega'] = ['Underlier', 'OptionMaturity']
            name1, optMat1 = factor1['Underlier'], factor1['OptionMaturity']
            name2, optMat2 = factor2['Underlier'], factor2['OptionMaturity']

            optionTenorRho = self.getConfigItem('VegaOptionTenorRho')

            if name1 != name2:
                rho *= trancheRho
                factors.append({
                    'name': 'TrancheRho',
                    'description': 'Different issuer/tranche/index',
                    'value1': name1,
                    'value2': name2,
                    'rho_component': trancheRho,
                    'config_item': 'DeltaTrancheRho'
                })

            optCorr = optionTenorRho.at[optMat1, optMat2]
            rho = min(rho * optCorr, 1.0)
            factors.append({
                'name': 'OptionTenorRho',
                'description': 'Option maturity correlation',
                'value1': optMat1,
                'value2': optMat2,
                'rho_component': optCorr,
                'config_item': 'VegaOptionTenorRho'
            })

        elif riskType == 'Curvature':
            # _rhoFactorFields['Curvature'] = ['Underlier']
            name1 = factor1['Underlier']
            name2 = factor2['Underlier']

            if name1 != name2:
                rho *= trancheRho
                factors.append({
                    'name': 'TrancheRho',
                    'description': 'Different issuer/tranche/index',
                    'value1': name1,
                    'value2': name2,
                    'rho_component': trancheRho,
                    'config_item': 'DeltaTrancheRho'
                })

        return {
            'rho': rho,
            'factors': factors
        }


## EQ : Equities
#
@FRTBCalculator.registerClass
class MS_EQ_SA_SBM_Calc(SA_SBM_Calc):
    _rhoFactorFields = {
        'Delta'     : ['EquityName', 'SpotRepo'],
        'Vega'      : ['EquityName', 'OptionMaturity'],
        'Curvature' : ['EquityName']
    }

    def getRiskWeights(self, riskClass, df):
        riskType = riskClass[5:]

        if riskType == 'Delta':
            RWBucket = self.getConfigItem('DeltaBucketRiskWeight')
            df.loc[:, 'RiskWeight'] = df.apply(lambda row : RWBucket.at[row['SpotRepo'], row['Bucket']+row['SubBucket']], axis=1)
        elif riskType == 'Vega':
            RWVega = self.getConfigItem('VegaRiskWeight')
            bucketInfo = self.getConfigItem('Bucket').set_index(['Bucket', 'SubBucket'])
            df.loc[:, 'RiskWeight'] = df.apply(lambda r : RWVega.at[bucketInfo.at[(r['Bucket'],r['SubBucket']), 'MarketCap'], 'RiskWeight'], axis=1)
        else:
            # Curvature - is there any risk weight for curvature?
            # CVR+ and CVR- are already delta-neutralised so nothing to do.
            # If, instead we want to use Vi+ and Vi- then need to think again,
            # we'd need the Vi0 (PV), the shock size and the corresponding Delta.
            pass

        return df


    def getRho(self, riskClass, bucket, df):
        rho = np.zeros((df.shape[0], df.shape[0]))
        factors = df[self._rhoFactorFields[riskClass[5:]]]
        nameRho = self.getConfigItem('DeltaNameBucketRho').at[bucket]
        spotRepoRho = self.getConfigItem('DeltaSpotRepoRho')

        for i, r in enumerate(factors.itertuples(index=False)):
            for j, c in enumerate(factors.itertuples(index=False)):
                if i <= j:
                    break

                corr = 1.0

                if r[0] != c[0]:
                    # Different Names
                    corr *= nameRho

                if riskClass[5:] == 'Delta':
                    if r[1] != c[1]:
                        # One spot one repo
                        corr *= spotRepoRho
                elif riskClass[5:] == 'Vega':
                    if r[1] != c[1]:
                        # Different option maturities
                        corr = min(corr * self.getConfigItem('VegaOptionTenorRho').at[r[1], c[1]], 1.0)

                rho[i, j] = rho[j, i] = corr

        return pd.DataFrame(rho, index=df.index, columns=df.index)


    def  getBucketCalculator(self, riskClass, bucket):
        otherBucket = self.getConfigItem('OtherBucket')

        if bucket != otherBucket:
            if riskClass[5:] == 'Curvature':
                return self.calcCurvatureBucket
            else:
                return self.calcDeltaVegaBucket
        else:
            if riskClass[5:] == 'Curvature':
                return self.calcCurvatureOtherBucket
            else:
                return self.calcDeltaVegaOtherBucket


    def getRhoFactors(self, riskClass, bucket, factor1, factor2):
        riskType = riskClass[5:]
        factors = []
        rho = 1.0

        nameRho = self.getConfigItem('DeltaNameBucketRho').at[bucket]
        spotRepoRho = self.getConfigItem('DeltaSpotRepoRho')

        if riskType == 'Delta':
            # _rhoFactorFields['Delta'] = ['EquityName', 'SpotRepo']
            name1, sr1 = factor1['EquityName'], factor1['SpotRepo']
            name2, sr2 = factor2['EquityName'], factor2['SpotRepo']

            if name1 != name2:
                rho *= nameRho
                factors.append({
                    'name': 'NameRho',
                    'description': f'Different equity names (bucket {bucket})',
                    'value1': name1,
                    'value2': name2,
                    'rho_component': nameRho,
                    'config_item': 'DeltaNameBucketRho'
                })

            if sr1 != sr2:
                rho *= spotRepoRho
                factors.append({
                    'name': 'SpotRepoRho',
                    'description': 'One spot, one repo',
                    'value1': sr1,
                    'value2': sr2,
                    'rho_component': spotRepoRho,
                    'config_item': 'DeltaSpotRepoRho'
                })

        elif riskType == 'Vega':
            # _rhoFactorFields['Vega'] = ['EquityName', 'OptionMaturity']
            name1, optMat1 = factor1['EquityName'], factor1['OptionMaturity']
            name2, optMat2 = factor2['EquityName'], factor2['OptionMaturity']

            optionTenorRho = self.getConfigItem('VegaOptionTenorRho')

            if name1 != name2:
                rho *= nameRho
                factors.append({
                    'name': 'NameRho',
                    'description': f'Different equity names (bucket {bucket})',
                    'value1': name1,
                    'value2': name2,
                    'rho_component': nameRho,
                    'config_item': 'DeltaNameBucketRho'
                })

            if optMat1 != optMat2:
                optCorr = optionTenorRho.at[optMat1, optMat2]
                rho = min(rho * optCorr, 1.0)
                factors.append({
                    'name': 'OptionTenorRho',
                    'description': 'Different option maturities',
                    'value1': optMat1,
                    'value2': optMat2,
                    'rho_component': optCorr,
                    'config_item': 'VegaOptionTenorRho'
                })

        elif riskType == 'Curvature':
            # _rhoFactorFields['Curvature'] = ['EquityName']
            name1 = factor1['EquityName']
            name2 = factor2['EquityName']

            if name1 != name2:
                rho *= nameRho
                factors.append({
                    'name': 'NameRho',
                    'description': f'Different equity names (bucket {bucket})',
                    'value1': name1,
                    'value2': name2,
                    'rho_component': nameRho,
                    'config_item': 'DeltaNameBucketRho'
                })

        return {
            'rho': rho,
            'factors': factors
        }


## CM : Commodities / COMM
#
@FRTBCalculator.registerClass
class MS_CM_SA_SBM_Calc(SA_SBM_Calc):
    _rhoFactorFields = {
        'Delta'     : ['CommodityName', 'DeliveryLocation', 'Tenor'],
        'Vega'      : ['CommodityName', 'OptionMaturity'],
        'Curvature' : ['CommodityName']
    }

    def getRho(self, riskClass, bucket, df):
        rho = np.zeros((df.shape[0], df.shape[0]))
        factors = df[self._rhoFactorFields[riskClass[5:]]]
        commodityRho = self.getConfigItem('DeltaCommodityRho').at[bucket]
        deltaTenorRho = self.getConfigItem('DeltaTenorRho')
        basisRho = self.getConfigItem('DeltaBasisRho')

        for i, r in enumerate(factors.itertuples(index=False)):
            for j, c in enumerate(factors.itertuples(index=False)):
                if i <= j:
                    break

                corr = 1.0

                if r[0] != c[0]:
                    # Different Names
                    corr *= commodityRho

                if riskClass[5:] == 'Delta':
                    if r[2] != c[2]:
                        # Different tenors
                        corr *= deltaTenorRho

                    if r[1] != c[1]:
                        # Different delivery locations
                        corr *= basisRho
                elif riskClass[5:] == 'Vega':
                    corr = min(corr * self.getConfigItem('VegaOptionTenorRho').at[r[1], c[1]], 1)

                rho[i, j] = rho[j, i] = corr

        return pd.DataFrame(rho, index=df.index, columns=df.index)


    def getRhoFactors(self, riskClass, bucket, factor1, factor2):
        riskType = riskClass[5:]
        factors = []
        rho = 1.0

        commodityRho = self.getConfigItem('DeltaCommodityRho').at[bucket]
        deltaTenorRho = self.getConfigItem('DeltaTenorRho')
        basisRho = self.getConfigItem('DeltaBasisRho')

        if riskType == 'Delta':
            # _rhoFactorFields['Delta'] = ['CommodityName', 'DeliveryLocation', 'Tenor']
            name1, loc1, tenor1 = factor1['CommodityName'], factor1['DeliveryLocation'], factor1['Tenor']
            name2, loc2, tenor2 = factor2['CommodityName'], factor2['DeliveryLocation'], factor2['Tenor']

            if name1 != name2:
                rho *= commodityRho
                factors.append({
                    'name': 'CommodityRho',
                    'description': f'Different commodity names (bucket {bucket})',
                    'value1': name1,
                    'value2': name2,
                    'rho_component': commodityRho,
                    'config_item': 'DeltaCommodityRho'
                })

            if tenor1 != tenor2:
                rho *= deltaTenorRho
                factors.append({
                    'name': 'TenorRho',
                    'description': 'Different tenors',
                    'value1': tenor1,
                    'value2': tenor2,
                    'rho_component': deltaTenorRho,
                    'config_item': 'DeltaTenorRho'
                })

            if loc1 != loc2:
                rho *= basisRho
                factors.append({
                    'name': 'BasisRho',
                    'description': 'Different delivery locations',
                    'value1': loc1,
                    'value2': loc2,
                    'rho_component': basisRho,
                    'config_item': 'DeltaBasisRho'
                })

        elif riskType == 'Vega':
            # _rhoFactorFields['Vega'] = ['CommodityName', 'OptionMaturity']
            name1, optMat1 = factor1['CommodityName'], factor1['OptionMaturity']
            name2, optMat2 = factor2['CommodityName'], factor2['OptionMaturity']

            optionTenorRho = self.getConfigItem('VegaOptionTenorRho')

            if name1 != name2:
                rho *= commodityRho
                factors.append({
                    'name': 'CommodityRho',
                    'description': f'Different commodity names (bucket {bucket})',
                    'value1': name1,
                    'value2': name2,
                    'rho_component': commodityRho,
                    'config_item': 'DeltaCommodityRho'
                })

            optCorr = optionTenorRho.at[optMat1, optMat2]
            rho = min(rho * optCorr, 1.0)
            factors.append({
                'name': 'OptionTenorRho',
                'description': 'Option maturity correlation',
                'value1': optMat1,
                'value2': optMat2,
                'rho_component': optCorr,
                'config_item': 'VegaOptionTenorRho'
            })

        elif riskType == 'Curvature':
            # _rhoFactorFields['Curvature'] = ['CommodityName']
            name1 = factor1['CommodityName']
            name2 = factor2['CommodityName']

            if name1 != name2:
                rho *= commodityRho
                factors.append({
                    'name': 'CommodityRho',
                    'description': f'Different commodity names (bucket {bucket})',
                    'value1': name1,
                    'value2': name2,
                    'rho_component': commodityRho,
                    'config_item': 'DeltaCommodityRho'
                })

        return {
            'rho': rho,
            'factors': factors
        }


## FX : Foreign Exchange
#
@FRTBCalculator.registerClass
class MS_FX_SA_SBM_Calc(SA_SBM_Calc):
    _rhoFactorFields = {
        'Delta' : [],
        'Vega' : ['OptionMaturity'],
        'Curvature' : []
    }

    def getRiskWeights(self, riskClass, df):
        riskType = riskClass[5:]
        if riskType == 'Delta':
            RW = self.getConfigItem('DeltaRiskWeight')
            baselCcys = self.getConfigItem('BaselCcys').to_list()
            df.loc[:, 'RiskWeight'] = RW

            if self._regulator == 'EU-EBA':
                ERMCcys = self.getConfigItem('ERMIICcys')
                ERMBand = self.getConfigItem('ERMIIBand')
                EURPegCcys = self.getConfigItem('EURPegCcys').to_list()
                df.loc[df['Bucket'].isin(baselCcys), 'RiskWeight'] = RW / (2 ** 0.5)
                df.loc[df['Bucket'].isin(ERMCcys.index), 'RiskWeight'] = df.loc[df['Bucket'].isin(ERMCcys.index), :].apply(
                    lambda x: ERMCcys.at[x['Bucket']] if ERMCcys.at[x['Bucket']] < ERMBand else RW / 3.0
                    , axis=1)
                df.loc[df['Bucket'].isin(EURPegCcys), 'RiskWeight'] = RW / 2.0
            else:
                df.loc[df['Bucket'].isin(baselCcys), 'RiskWeight'] = RW / (2 ** 0.5)
        elif riskType == 'Vega':
            RWVega = self.getConfigItem('VegaRiskWeight')
            df.loc[:, 'RiskWeight'] = RWVega
        else:
            # Curvature - is there any risk weight for curvature?
            # CVR+ and CVR- are already delta-neutralised so nothing to do.
            # If, instead we want to use Vi+ and Vi- then need to think again,
            # we'd need the Vi0 (PV), the shock size and the corresponding Delta.
            pass

        return df

    def getRho(self, riskClass, bucket, df):
        if riskClass[5:] != 'Vega':
            return super().getRho(riskClass, bucket, df)

        rhoTenor = self.getConfigItem('VegaOptionTenorRho')
        tenors = df['OptionMaturity'].to_list()
        return rhoTenor.loc[tenors, tenors]


    def getRhoFactors(self, riskClass, bucket, factor1, factor2):
        riskType = riskClass[5:]
        factors = []
        rho = 1.0

        # FX Delta and Curvature have no intra-bucket correlations (single factor per bucket)
        if riskType == 'Delta' or riskType == 'Curvature':
            # No factors to compare - each bucket has only one risk factor
            return {
                'rho': 1.0,
                'factors': []
            }

        elif riskType == 'Vega':
            # _rhoFactorFields['Vega'] = ['OptionMaturity']
            optMat1 = factor1['OptionMaturity']
            optMat2 = factor2['OptionMaturity']

            rhoTenor = self.getConfigItem('VegaOptionTenorRho')
            optCorr = rhoTenor.at[optMat1, optMat2]
            rho = optCorr

            factors.append({
                'name': 'OptionTenorRho',
                'description': 'Option maturity correlation',
                'value1': optMat1,
                'value2': optMat2,
                'rho_component': optCorr,
                'config_item': 'VegaOptionTenorRho'
            })

        return {
            'rho': rho,
            'factors': factors
        }


#%%################################################
###################################################
#                                                 #
#     CVA Derived classes for each Risk Class     #
#                                                 #
###################################################
###################################################

## IR : Interest Rates / GIRR
#
@FRTBCalculator.registerClass
class CS_IR_SA_SBM_Calc(SA_SBM_Calc):
    _rhoFactorFields = {
        'Delta' : ['CurveType', 'Tenor'],
        'Vega' : ['CurveType']
    }

    def getRiskWeights(self, riskClass, df):
        if riskClass[5:] != 'Delta':
            return super().getRiskWeights(riskClass, df)

        BaselCcys = self.getConfigItem('BaselCcys').to_list()

        if self._regulator == 'EU-EBA':
            BaselCcys.extend(self.getConfigItem('ERMIICcys').to_list())

        tenorRW = self.getConfigItem('DeltaTenorRiskWeight')
        inflationRW = self.getConfigItem('DeltaInflationRiskWeight')
        tenorIlliquidRW = self.getConfigItem('DeltaTenorIlliquidRiskWeight')
        inflationIlliquidRW = self.getConfigItem('DeltaInflationIlliquidRiskWeight')
        df.loc[df['Bucket'].isin(BaselCcys), 'RiskWeight'] = df[df['Bucket'].isin(BaselCcys)].apply(lambda x: tenorRW.at[x['Tenor']] if x['CurveType']=='IR' else inflationRW, axis=1)
        df.loc[~df['Bucket'].isin(BaselCcys), 'RiskWeight'] = df[~df['Bucket'].isin(BaselCcys)].apply(lambda x: tenorIlliquidRW if x['CurveType']=='IR' else inflationIlliquidRW, axis=1)
        return df

    def getRho(self, riskClass, bucket, df):
        rho = np.zeros((df.shape[0], df.shape[0]))
        factors = df[self._rhoFactorFields[riskClass[5:]]]
        BaselCcys = self.getConfigItem('BaselCcys').to_list()

        if self._regulator == 'EU-EBA':
            BaselCcys.extend(self.getConfigItem('ERMIICcys').to_list())

        deltaTenorRho = self.getConfigItem('DeltaTenorRho')
        deltaIlliquidRho = self.getConfigItem('DeltaIlliquidRho')
        deltaInflationRho = self.getConfigItem('DeltaInflationRho')
        vegaRho = self.getConfigItem('VegaRho')

        for i, r in enumerate(factors.itertuples(index=False)):
            for j, c in enumerate(factors.itertuples(index=False)):
                if i <= j:
                    break

                if riskClass[5:] == 'Delta':
                    if r[0] == 'INFL' or c[0] == 'INFL':
                        if r[0] == c[0]:
                            corr = 1.0
                        else:
                            corr = deltaInflationRho
                    elif bucket in BaselCcys:
                        corr = deltaTenorRho.at[r[1], c[1]]
                    else:
                        corr = deltaIlliquidRho
                elif riskClass[5:] == 'Vega':
                    corr = vegaRho

                rho[i, j] = rho[j, i] = corr

        return pd.DataFrame(rho, index=df.index, columns=df.index)


    def getRhoFactors(self, riskClass, bucket, factor1, factor2):
        riskType = riskClass[5:]
        factors = []
        rho = 1.0

        BaselCcys = self.getConfigItem('BaselCcys').to_list()
        if self._regulator == 'EU-EBA':
            BaselCcys.extend(self.getConfigItem('ERMIICcys').to_list())

        if riskType == 'Delta':
            # _rhoFactorFields['Delta'] = ['CurveType', 'Tenor']
            ct1, tenor1 = factor1['CurveType'], factor1['Tenor']
            ct2, tenor2 = factor2['CurveType'], factor2['Tenor']

            deltaInflationRho = self.getConfigItem('DeltaInflationRho')
            deltaTenorRho = self.getConfigItem('DeltaTenorRho')
            deltaIlliquidRho = self.getConfigItem('DeltaIlliquidRho')

            if ct1 == 'INFL' or ct2 == 'INFL':
                if ct1 == ct2:  # both INFL
                    rho = 1.0
                    factors.append({
                        'name': 'InflationRho',
                        'description': 'Both factors are INFL curves',
                        'value1': ct1,
                        'value2': ct2,
                        'rho_component': 1.0,
                        'config_item': None
                    })
                else:
                    rho = deltaInflationRho
                    factors.append({
                        'name': 'InflationRho',
                        'description': 'Inflation vs non-inflation correlation',
                        'value1': ct1,
                        'value2': ct2,
                        'rho_component': deltaInflationRho,
                        'config_item': 'DeltaInflationRho'
                    })
            elif bucket in BaselCcys:
                tenorCorr = deltaTenorRho.at[tenor1, tenor2]
                rho = tenorCorr
                factors.append({
                    'name': 'TenorRho',
                    'description': f'Tenor correlation (Basel currency: {bucket})',
                    'value1': tenor1,
                    'value2': tenor2,
                    'rho_component': tenorCorr,
                    'config_item': 'DeltaTenorRho'
                })
            else:
                rho = deltaIlliquidRho
                factors.append({
                    'name': 'IlliquidRho',
                    'description': f'Illiquid currency correlation (bucket: {bucket})',
                    'value1': tenor1,
                    'value2': tenor2,
                    'rho_component': deltaIlliquidRho,
                    'config_item': 'DeltaIlliquidRho'
                })

        elif riskType == 'Vega':
            # _rhoFactorFields['Vega'] = ['CurveType']
            ct1 = factor1['CurveType']
            ct2 = factor2['CurveType']

            vegaRho = self.getConfigItem('VegaRho')
            rho = vegaRho
            factors.append({
                'name': 'VegaRho',
                'description': 'Vega correlation between curve types',
                'value1': ct1,
                'value2': ct2,
                'rho_component': vegaRho,
                'config_item': 'VegaRho'
            })

        return {
            'rho': rho,
            'factors': factors
        }


# FX : Foreign Exchange
#
@FRTBCalculator.registerClass
class CS_FX_SA_SBM_Calc(SA_SBM_Calc):
    _rhoFactorFields = {
        'Delta' : [],
        'Vega' : []
    }

    def getRiskWeights(self, riskClass, df):
        riskType = riskClass[5:]

        if riskType == 'Delta':
            RW = self.getConfigItem('DeltaRiskWeight')
        elif riskType == 'Vega':
            RW = self.getConfigItem('VegaRiskWeight')

        df.loc[:, 'RiskWeight'] = RW
        return df

    def getRho(self, riskClass, bucket, df):
        return super().getRho(riskClass, bucket, df)


## CC: Counterparty Credit Spread / CSR_CPY
#
@FRTBCalculator.registerClass
class CS_CC_SA_SBM_Calc(SA_SBM_Calc):
    _rhoFactorFields = {
        'Delta' : ['CreditName', 'ParentName', 'IG_HYNR', 'Tenor']
    }

    def getRiskWeights(self, riskClass, df):
        ndf = df.copy()
        RW = self.getConfigItem('DeltaRiskWeight')

        if self._regulator == 'EU-EBA':
            ndf.loc[:, 'RiskWeight'] = ndf.apply(lambda x : RW.iloc[0, :].at[x['Bucket']+x['SubBucket']], axis=1)
        else:
            ndf.loc[:, 'RiskWeight'] = ndf.apply(lambda x : RW.at[x['IG_HYNR'], x['Bucket']+x['SubBucket']], axis=1)

        return ndf

    def getRho(self, riskClass, bucket, df):
        rho = np.zeros((df.shape[0], df.shape[0]))
        factors = df[self._rhoFactorFields[riskClass[5:]]]
        indexBuckets = self.getConfigItem('IndexBuckets').to_list()

        if bucket in indexBuckets:
            nameRelatedRho = self.getConfigItem('DeltaNameRelatedIndexRho')
            nameUnrelatedRho = self.getConfigItem('DeltaNameUnrelatedIndexRho')
            tenorRho = self.getConfigItem('DeltaTenorIndexRho')
            ratingRho = self.getConfigItem('DeltaCreditQualityIndexRho')
        else:
            nameRelatedRho = self.getConfigItem('DeltaNameRelatedRho')
            nameUnrelatedRho = self.getConfigItem('DeltaNameUnrelatedRho')
            tenorRho = self.getConfigItem('DeltaTenorRho')
            ratingRho = self.getConfigItem('DeltaCreditQualityRho')

        for i, r in enumerate(factors.itertuples(index=False)):
            for j, c in enumerate(factors.itertuples(index=False)):
                if i <= j:
                    break

                corr = 1.0

                if r[1] == c[1]:
                    if r[0] != c[0]:
                        corr *= nameRelatedRho
                else:
                    corr *= nameUnrelatedRho

                if r[2] != c[2]:
                    corr *= ratingRho

                if r[3] != c[3]:
                    corr *= tenorRho

                rho[i, j] = rho[j, i] = corr

        return pd.DataFrame(rho, index=df.index, columns=df.index)


    def getRhoFactors(self, riskClass, bucket, factor1, factor2):
        factors = []
        rho = 1.0

        # _rhoFactorFields['Delta'] = ['CreditName', 'ParentName', 'IG_HYNR', 'Tenor']
        name1, parent1, rating1, tenor1 = factor1['CreditName'], factor1['ParentName'], factor1['IG_HYNR'], factor1['Tenor']
        name2, parent2, rating2, tenor2 = factor2['CreditName'], factor2['ParentName'], factor2['IG_HYNR'], factor2['Tenor']

        indexBuckets = self.getConfigItem('IndexBuckets').to_list()
        isIndex = bucket in indexBuckets
        suffix = 'Index' if isIndex else ''

        nameRelatedRho = self.getConfigItem(f'DeltaNameRelated{suffix}Rho')
        nameUnrelatedRho = self.getConfigItem(f'DeltaNameUnrelated{suffix}Rho')
        tenorRho = self.getConfigItem(f'DeltaTenor{suffix}Rho')
        ratingRho = self.getConfigItem(f'DeltaCreditQuality{suffix}Rho')

        # Name/Parent correlation
        if parent1 == parent2:
            if name1 != name2:
                rho *= nameRelatedRho
                factors.append({
                    'name': 'NameRelatedRho',
                    'description': f'Same parent, different names ({"index" if isIndex else "non-index"} bucket)',
                    'value1': f'{name1} (parent: {parent1})',
                    'value2': f'{name2} (parent: {parent2})',
                    'rho_component': nameRelatedRho,
                    'config_item': f'DeltaNameRelated{suffix}Rho'
                })
        else:
            rho *= nameUnrelatedRho
            factors.append({
                'name': 'NameUnrelatedRho',
                'description': f'Different parents ({"index" if isIndex else "non-index"} bucket)',
                'value1': f'{name1} (parent: {parent1})',
                'value2': f'{name2} (parent: {parent2})',
                'rho_component': nameUnrelatedRho,
                'config_item': f'DeltaNameUnrelated{suffix}Rho'
            })

        # Credit quality correlation
        if rating1 != rating2:
            rho *= ratingRho
            factors.append({
                'name': 'CreditQualityRho',
                'description': f'Different credit quality ({"index" if isIndex else "non-index"} bucket)',
                'value1': rating1,
                'value2': rating2,
                'rho_component': ratingRho,
                'config_item': f'DeltaCreditQuality{suffix}Rho'
            })

        # Tenor correlation
        if tenor1 != tenor2:
            rho *= tenorRho
            factors.append({
                'name': 'TenorRho',
                'description': f'Different tenors ({"index" if isIndex else "non-index"} bucket)',
                'value1': tenor1,
                'value2': tenor2,
                'rho_component': tenorRho,
                'config_item': f'DeltaTenor{suffix}Rho'
            })

        return {
            'rho': rho,
            'factors': factors
        }


## CR : Reference Credet Spread / CSR_REF
#
@FRTBCalculator.registerClass
class CS_CR_SA_SBM_Calc(SA_SBM_Calc):
    _rhoFactorFields = {
        'Delta' : [],
        'Vega' : []
    }

    def getRho(self, riskClass, bucket, df):
        return super().getRho(riskClass, bucket, df)


## EQ : Equities
#
@FRTBCalculator.registerClass
class CS_EQ_SA_SBM_Calc(SA_SBM_Calc):
    _rhoFactorFields = {
        'Delta' : [],
        'Vega' : []
    }

    def getRiskWeights(self, riskClass, df):
        riskType = riskClass[5:]

        if riskType == 'Delta':
            RWBucket = self.getConfigItem('DeltaBucketRiskWeight')
        elif riskType == 'Vega':
            RWBucket = self.getConfigItem('VegaBucketRiskWeight')

        df.loc[:, 'RiskWeight'] = df.apply(lambda r : RWBucket.at[r['Bucket']+r['SubBucket']], axis=1)
        return df

    def getRho(self, riskClass, bucket, df):
        return super().getRho(riskClass, bucket, df)


## CM : Commodities / COMM
#
@FRTBCalculator.registerClass
class CS_CM_SA_SBM_Calc(SA_SBM_Calc):
    _rhoFactorFields = {
        'Delta' : [],
        'Vega' : []
    }

    def getRho(self, riskClass, bucket, df):
        return super().getRho(riskClass, bucket, df)
