"""
Calculate the Basel III Market Risk Defalt Risk Capital reqirements using the
Standardised Approach within the frtb.net framework

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
import datetime as dt

import FRTBCalculator

class SA_DRC_Calc(FRTBCalculator.FRTBCalculator):
    # This is the primary entry point and computes capital for a single risk class
    # at all the necessary correlation levels.  It returns a list of Dictionaries, each
    # with an entry for RiskClass and an entry for each computed result, such as the capital
    # at each of the correlation levels.  As DRC has only one correlation level, there is
    # just one item in the list but the list is needed so the interface os the same as for
    # the other RiskClasses.  E.g.:
    # [
    #   {
    #       'RiskClass'     : 'MD_CR_DRC',
    #       'Correlation'   : 'Medium',
    #       'Capital'       : 123.45,
    #   }
    # ]
    #
    def calcRiskClassCapital(self, riskClass, df):
        bucketResults = []

        for bucket, bucketSensis in df.groupby('Bucket'):
            bdf = self.prepareData(riskClass, bucketSensis)
            bdf = self.applyRiskWeights(riskClass, bdf)
            bdf = self.collectRiskFactors(riskClass, bdf)  # this ought to be a no-op for DRC
            bucketResults.extend(self.getBucketCalculator(riskClass, bucket)(riskClass, bucket, bdf))

        buckets = pd.DataFrame(bucketResults)
        return self.aggregateDRC(riskClass, buckets)


    def getBucketCalculator(self, riskClass, bucket):
        return self.calcBucketDRC


    def scaleMaturities(self, df):
        ndf = df.copy()

        if 'MaturityDate' in df.columns:  # don't have this for Securitisations non-CTP
            # Scale the sensitivities for short matirities
            ndf.loc[:, 'MaturityScale'] = [min(max((dt.date.fromisoformat(x) - self._cob).days / 365.0, 0.25), 1.0) for x in ndf['MaturityDate']]
            ndf.loc[:, 'ScaledJTD'] = ndf['JTD'] * ndf['MaturityScale']
        else:
            ndf.loc[:, 'ScaledJTD'] = ndf['JTD']

        return ndf


    # Not much to do for securitisations - Non-Securitisations override this method
    #
    def _netByObligor(self, df):
        grossLong = df[df['JTD'] >= 0]['JTD'].sum()
        grossShort = df[df['JTD'] < 0]['JTD'].sum()
        net = df['ScaledJTD'].sum()
        netLong = net if net > 0.0 else 0.0
        netShort = net if net < 0.0 else 0.0
        return pd.Series({
                    'GrossJTDLong'     : grossLong,
                    'GrossJTDShort'    : grossShort,
                    'NetJTDLong'       : netLong,
                    'NetJTDShort'      : netShort
                }
            )


    def getFactorNettingFields(self, riskClass=None):
        return self._factorFields.copy()


    def netByObligor(self, df):
        fields = self.getFactorNettingFields()
        return df.groupby(['RiskGroup', 'RiskSubGroup', 'RiskClass', 'Bucket'] + fields).apply(self._netByObligor).reset_index()        


    def prepareData(self, riskClass, df):
        ddf = self.scaleMaturities(df)
        ddf = self.netByObligor(ddf)
        return ddf


    def collectRiskFactors(self, riskClass, df):
        # df has all the input data for a single Bucket but might be more granular than the
        # bucket risk factors we need.  So here we aggregate all the rows for the same risk
        # factor into a single row.
        #
        factorFields = self.getFactorNettingFields()

        if not 'RiskWeight' in factorFields:
            # Securitisations already have a RiskWeight in the data and as part of the factorFields
            factorFields.append('RiskWeight')

        valueFields = ['GrossJTDLong', 'GrossJTDShort', 'NetJTDLong', 'NetJTDShort', 'WeightedNetJTDLong', 'WeightedNetJTDShort']
        ndf = df[['RiskGroup', 'RiskSubGroup', 'RiskClass', 'Bucket'] + factorFields + valueFields].groupby(['RiskGroup', 'RiskSubGroup', 'RiskClass', 'Bucket'] + factorFields).sum().reset_index()
        return ndf


    # Compute DRC for a single bucket.  In Securitisation (CTP) the HBR and Capital computed
    # here are ignored as the HBR is taken across all buckets and the Capital is then computed
    # using that.
    #
    # TODO : create a method to compute the accurate HBR and Capital for Securitisations (CTP)
    # for intermediate results delivery.  Then maybe the common aggreageDRC method can be used.
    #
    def calcBucketDRC(self, riskClass, bucket, df):
        # Collect net long and net short sensitivities
        grossLong = df['GrossJTDLong'].sum()
        grossShort = df['GrossJTDShort'].sum()
        netLong = df['NetJTDLong'].sum()
        netShort = df['NetJTDShort'].sum()
        weightedNetLong = df['WeightedNetJTDLong'].sum()
        weightedNetShort = df['WeightedNetJTDShort'].sum()

        # compute the hedge benefit ratio and the capital
        hedgeBenefitRatio = netLong / (netLong - netShort)

        bucketCapital = {
                'RiskClass'             : riskClass,
                'Bucket'                : bucket,
                'Correlation'           : 'Medium',
                'GrossJTDLong'          : grossLong,
                'GrossJTDShort'         : grossShort,
                'NetJTDLong'            : netLong,
                'NetJTDShort'           : netShort,
                'WeightedNetJTDLong'    : weightedNetLong,
                'WeightedNetJTDShort'   : weightedNetShort,
                'HedgeBenefitRatio'     : hedgeBenefitRatio,
                'Capital'               : max(weightedNetLong + hedgeBenefitRatio * weightedNetShort, 0)    # EBA varies from this
            }

        return [bucketCapital]


    def aggregateDRC(self, riskClass, buckets):
        # Create capital dictionary
        capital = {}
        capital['RiskClass'] = riskClass
        cap = buckets.loc[buckets['Correlation']=='Medium', 'Capital'].sum()
        capital['Correlation'] = 'Medium'
        capital['Capital'] = cap
        return [ capital ]  # return as a list of capitals to match the interface of the other RiskClasses


#%%################################################
###################################################
#                                                 #
# Market Risk Derived classes for each Risk Class #
#                                                 #
###################################################
###################################################


@FRTBCalculator.registerClass
class MD_CR_SA_DRC(SA_DRC_Calc):
    #
    # Non-Secritisations
    #
    _factorFields = ['Name', 'Rating']

    def applyRiskWeights(self, riskClass, df):
        riskWeight = self.getConfigItem('CQRiskWeight')
        df.loc[:, 'RiskWeight'] = df['Rating'].apply(lambda rating : riskWeight.at[rating])
        df.loc[:, 'WeightedNetJTDLong'] = df['NetJTDLong'] * df['RiskWeight']
        df.loc[:, 'WeightedNetJTDShort'] = df['NetJTDShort'] * df['RiskWeight']
        return df

    # Called with data for just one Obligor, this nets at a seniority level and then allows
    # more senior obligations to offset more junior obligations.
    #
    def _netByObligor(self, df):
        grossLong = df[df['JTD'] >= 0]['JTD'].sum()
        grossShort = df[df['JTD'] < 0]['JTD'].sum()
        netLongEQ = df.loc[(df['ScaledJTD'] > 0) & (df['Seniority'] == 'EQUITY'), 'ScaledJTD'].sum()
        netShortEQ = df.loc[(df['ScaledJTD'] < 0) & (df['Seniority'] == 'EQUITY'), 'ScaledJTD'].sum()
        netLongSub = df.loc[(df['ScaledJTD'] > 0) & (df['Seniority'] == 'NON-SENIOR'), 'ScaledJTD'].sum()
        netShortSub = df.loc[(df['ScaledJTD'] < 0) & (df['Seniority'] == 'NON-SENIOR'), 'ScaledJTD'].sum()
        netLongSenior = df.loc[(df['ScaledJTD'] > 0) & (df['Seniority'] == 'SENIOR'), 'ScaledJTD'].sum()
        netShortSenior = df.loc[(df['ScaledJTD'] < 0) & (df['Seniority'] == 'SENIOR'), 'ScaledJTD'].sum()
        netLongCovered = df.loc[(df['ScaledJTD'] > 0) & (df['Seniority'] == 'COVERED'), 'ScaledJTD'].sum()
        netShortCovered = df.loc[(df['ScaledJTD'] < 0) & (df['Seniority'] == 'COVERED'), 'ScaledJTD'].sum()
        netLong = max(netLongEQ + netShortEQ +
                        max(netLongSub + netShortSub +
                            max(netLongSenior + netShortSenior +
                                max(netLongCovered + netShortCovered, 0),
                                0),
                            0),
                        0)
        netShort = min(netLongCovered + netShortCovered +
                        min(netLongSenior + netShortSenior +
                            min(netLongSub + netShortSub +
                                min(netLongEQ + netShortEQ, 0),
                                0),
                            0),
                        0)
        return pd.Series({
                    'GrossJTDLong'     : grossLong,
                    'GrossJTDShort'    : grossShort,
                    'NetJTDLong'       : netLong,
                    'NetJTDShort'      : netShort
                }
            )


@FRTBCalculator.registerClass
class MD_CS_SA_DRC(SA_DRC_Calc):
    #
    # Securitisations, non Correlation-Trading-Portfolio
    #
    _factorFields = ['Issuer/Tranche', 'RiskWeight']

    def applyRiskWeights(self, riskClass, df):
        df.loc[:, 'WeightedNetJTDLong'] = df['NetJTDLong'] * df['RiskWeight']
        df.loc[:, 'WeightedNetJTDShort'] = df['NetJTDShort'] * df['RiskWeight']
        return df


@FRTBCalculator.registerClass
class MD_CC_SA_DRC(SA_DRC_Calc):
    #
    # Securitisations, Correlation-Trading-Portfolio
    #
    _factorFields = ['TrancheNames', 'Rating']

    def applyRiskWeights(self, riskClass, df):
        riskWeight = self.getConfigItem('CQRiskWeight')
        df.loc[:, 'RiskWeight'] = df['Rating'].apply(lambda rating : riskWeight.at[rating])
        df.loc[:, 'WeightedNetJTDLong'] = df['NetJTDLong'] * df['RiskWeight']
        df.loc[:, 'WeightedNetJTDShort'] = df['NetJTDShort'] * df['RiskWeight']
        return df

    def aggregateDRC(self, riskClass, buckets):
        # Create capital dictionary
        capital = {}
        capital['RiskClass'] = riskClass
        HBR = buckets['NetJTDLong'].sum() / (buckets['NetJTDLong'].sum() - buckets['NetJTDShort'].sum())
        buckets.loc[:, 'DRC'] = buckets['WeightedNetJTDLong'] + HBR * buckets['WeightedNetJTDShort']
        buckets.loc[:, 'Capital'] = buckets['DRC'].apply(lambda x : max(x, 0) + 0.5 * min(x, 0))
        capital['Correlation'] = 'Medium'
        capital['Capital'] = buckets['Capital'].sum()
        return [ capital ]  # return as a list of capitals to match the interface of the other RiskClasses
