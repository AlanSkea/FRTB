"""
Defines the structure if an frtb.net configuration for a particular regulator,
reads such a configuration file and provides some common functions for retrieving
configuration items.

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
Copyright © 2024 by Alan Skea
"""

import os
import numpy as np
import pandas as pd
import math
import openpyxl as xl

import FRTBUtils as FNU


class FRTBConfig(object):
    # _Regulators = [
    #     'BCBS',
    #     'UK-PRA',
    #     'EU-EBA',
    #     'SG-MAS'`
    # ]

    _configFile = 'FRTBConfig_{}.xlsx'

    #
    # The following describes the shape of the data for each of the keys in the config.  If the
    # config key appears in a list here then it is given the treatment appropriate for that list.
    # Possible list memberships are:
    #   'listKeys'      : This lists the keys that have a python list of values.  They may be laid out
    #                     horizontally or vertically.  Lists may have headers naming the items in either
    #                     the first row or columns depending on the layout of the list.  listKeys are
    #                     read inot pandas.Series objects.
    #   'arrayKeys'     : List of keys that are arrays
    #   'rowHdrKeys'    : List of keys that have row headers
    #   'colHdrKeys'    : List of keys that have column headers
    #   'addIndex'      : Dictionary of keys and expressions to eval to create index labels
    #   'addColumns'    : Dictionary of keys and expressions to eval to creatre column lalels
    #
    # The addIndex and addColumns keys contain special magic.  They are used to set the row and column
    # indices of a DataFrame or the index of a Series and can refer to other elements of the config data
    # for that riskClass.  The strings are evaluated in the context of the dataDict dictionary into which
    # all the config data is being loaded.  The usual use-case is to set an index from the list of buckets,
    # but in the IR risk classes, the index is set from the list of tenors.  The structure of the addIndex
    # and addColumns dictionaries is that the key is the name of the data item to which the row index or
    # column indsex is to be added, and the value is the string to be evaluated to get the index or column values.
    #
    _riskClassCongigKeyTypes = {
            'MR' : {
                'arrayKeys' : ['VegaLiquidityHorizon'],
                'colHdrKeys' : ['VegaLiquidityHorizon']
            },
            'MS_IR' : {
                'listKeys' : ['DeltaTenorRiskWeight', 'BaselCcys', 'DeltaTenors', 'VegaTenors', 'ERMIICcys'],
                'arrayKeys' : ['DeltaTenorRho'],
                'addIndex' : { 'DeltaTenorRiskWeight' : "dataDict['DeltaTenors']", 'DeltaTenorRho' : "dataDict['DeltaTenors']" },
                'addColumns' : { 'DeltaTenorRho' : "dataDict['DeltaTenors']" }
            },
            'MS_CR' : {
                'listKeys' : ['DeltaBucketRiskWeight', 'DeltaTenors', 'VegaTenors', 'CoveredBondHighQuality', 'IndexBuckets'],
                'arrayKeys' : ['Bucket', 'Gamma'],
                'colHdrKeys' : ['Bucket'],
                'addIndex' : { 'DeltaBucketRiskWeight' : "dataDict['Bucket']['Bucket'] + dataDict['Bucket']['SubBucket']",
                               'Gamma' : "dataDict['Bucket']['Bucket'].unique()" },
                'addColumns' : { 'Gamma' : "dataDict['Bucket']['Bucket'].unique()" }
            },
            'MS_CC' : {
                'listKeys' : ['DeltaBucketRiskWeight', 'DeltaTenors', 'VegaTenors'],
                'arrayKeys' : ['Bucket', 'Gamma'],
                'colHdrKeys' : ['Bucket'],
                'addIndex' : { 'DeltaBucketRiskWeight' : "dataDict['Bucket']['Bucket'] + dataDict['Bucket']['SubBucket']",
                               'Gamma' : "dataDict['Bucket']['Bucket'].unique()" },
                'addColumns' : { 'Gamma' : "dataDict['Bucket']['Bucket'].unique()" }
            },
            'MS_CS' : {
                'listKeys' : ['DeltaBucketRiskWeight', 'DeltaTenors', 'VegaTenors'],
                'arrayKeys' : ['Bucket'],
                'colHdrKeys' : ['Bucket'],
                'addIndex' : { 'DeltaBucketRiskWeight' : "dataDict['Bucket']['Bucket'] + dataDict['Bucket']['SubBucket']" }
            },
            'MS_EQ' : {
                'listKeys' : ['DeltaNameBucketRho', 'VegaTenors'],
                'arrayKeys' : ['AdvancedEconomyCountries', 'Bucket', 'DeltaBucketRiskWeight', 'Gamma'],
                'rowHdrKeys' : ['DeltaBucketRiskWeight'],
                'colHdrKeys' : ['Bucket'],
                'addIndex' : { 'DeltaNameBucketRho' : "dataDict['Bucket']['Bucket'].unique()",
                               'Gamma' : "dataDict['Bucket']['Bucket'].unique()" },
                'addColumns' : { 'DeltaBucketRiskWeight' : "dataDict['Bucket']['Bucket'] + dataDict['Bucket']['SubBucket']",
                                 'Gamma' : "dataDict['Bucket']['Bucket'].unique()" }
            },
            'MS_CM' : {
                'listKeys' : ['DeltaBucketRiskWeight', 'DeltaCommodityRho', 'DeltaTenors', 'VegaTenors'],
                'arrayKeys' : ['Bucket', 'Gamma'],
                'colHdrKeys' : ['Bucket'],
                'addIndex' : { 'DeltaBucketRiskWeight' : "dataDict['Bucket']['Bucket'] + dataDict['Bucket']['SubBucket']",
                               'DeltaCommodityRho' : "dataDict['Bucket']['Bucket'].unique()",
                               'Gamma' : "dataDict['Bucket']['Bucket'].unique()"},
                'addColumns' : { 'Gamma' : "dataDict['Bucket']['Bucket'].unique()" }
            },
            'MS_FX' : {
                'listKeys' : ['BaselCcys', 'VegaTenors', 'ERMIICcys', 'EURPegCcys'],
                'rowHdrKeys' : ['ERMIICcys']
            },
            'MD_CR' : {
                'listKeys' : ['Bucket', 'CQRiskWeight'],
                'rowHdrKeys' : ['CQRiskWeight'],
                'colHdrKeys' : ['Bucket']
            },
            'MD_CC' : {
                'listKeys' : ['CQRiskWeight'],
                'rowHdrKeys' : ['CQRiskWeight']
            },
            'MD_CS' : {
                'listKeys' : ['CQRiskWeight'],
                'arrayKeys' : ['Bucket'],
                'rowHdrKeys' : ['CQRiskWeight'],
                'colHdrKeys' : ['Bucket']
            },
            'MR_RR' : {
                'listKeys' : ['RiskWeight'],
                'arrayKeys' : ['Bucket'],
                'rowHdrKeys' : ['RiskWeight'],
                'colHdrKeys' : ['Bucket']
            },
            'CVA' : {
                'arrayKeys' : ['BA-Bucket', 'BA-RiskWeight'],
                'rowHdrKeys' : ['BA-RiskWeight'],
                'colHdrKeys' : ['BA-Bucket'],
                'addColumns' : { 'BA-RiskWeight' : "dataDict['BA-Bucket']['Bucket']" }
            },
            'CS_IR' : {
                'listKeys' : ['BaselCcys', 'DeltaTenorRiskWeight', 'DeltaTenors', 'ERMIICcys'],
                'arrayKeys' : ['DeltaTenorRho'],
                'addIndex' : { 'DeltaTenorRiskWeight' : "dataDict['DeltaTenors']", 'DeltaTenorRho' : "dataDict['DeltaTenors']" },
                'addColumns' : { 'DeltaTenorRho' : "dataDict['DeltaTenors']" }
            },
            'CS_FX' : {
                'listKeys' : ['ERMIICcys', 'EURPegCcys'],
                'rowHdrKeys' : ['ERMIICcys']
            },
            'CS_CC' : {
                'listKeys' : ['DeltaTenors', 'IndexBuckets'],
                'arrayKeys' : ['Bucket', 'Gamma', 'DeltaRiskWeight'],
                'rowHdrKeys' : ['DeltaRiskWeight'],
                'colHdrKeys' : ['Bucket'],
                'addIndex' : { 'Gamma' : "dataDict['Bucket']['Bucket'].unique()" },
                'addColumns' : { 'DeltaRiskWeight' : "dataDict['Bucket']['Bucket'] + dataDict['Bucket']['SubBucket']",
                                 'Gamma' : "dataDict['Bucket']['Bucket'].unique()" },
            },
            'CS_CR' : {
                'listKeys' : ['DeltaBucketRiskWeight'],
                'arrayKeys' : ['Bucket', 'Gamma'],
                'colHdrKeys' : ['Bucket'],
                'addIndex' :  { 'DeltaBucketRiskWeight' : "dataDict['Bucket']['Bucket'] + dataDict['Bucket']['SubBucket']",
                                 'Gamma' : "dataDict['Bucket']['Bucket'].unique()" },
                'addColumns' : { 'Gamma' : "dataDict['Bucket']['Bucket'].unique()" }
            },
            'CS_EQ' : {
                'listKeys' : ['AdvancedEconomyCountries', 'DeltaBucketRiskWeight', 'VegaBucketRiskWeight', 'DeltaBucketRho'],
                'arrayKeys' : ['Bucket', 'Gamma'],
                'colHdrKeys' : ['Bucket'],
                'addIndex' : { 'DeltaBucketRiskWeight' : "dataDict['Bucket']['Bucket'] + dataDict['Bucket']['SubBucket']",
                               'VegaBucketRiskWeight' : "dataDict['Bucket']['Bucket'] + dataDict['Bucket']['SubBucket']",
                               'DeltaBucketRho' : "dataDict['Bucket']['Bucket'].unique()",
                               'Gamma' : "dataDict['Bucket']['Bucket'].unique()",
                             },
                'addColumns' : { 'Gamma' : "dataDict['Bucket']['Bucket'].unique()" }
            },
            'CS_CM' : {
                'listKeys' : ['DeltaBucketRiskWeight'],
                'arrayKeys' : ['Bucket', 'Gamma'],
                'colHdrKeys' : ['Bucket'],
                'addIndex' : { 'DeltaBucketRiskWeight' : "dataDict['Bucket']['Bucket'] + dataDict['Bucket']['SubBucket']",
                               'Gamma' : "dataDict['Bucket']['Bucket'].unique()" },
                'addColumns' : { 'Gamma' : "dataDict['Bucket']['Bucket'].unique()" }
            }
        }

    # Everything not mentioned in these dictionaries are left as the type passed in.
    #
    _riskClassKeyDataType = {
        'MR' : {
            'VegaOptionRhoAlpha' : 'float64',
            'VegaRiskWeightSigma' : 'float64'
        },
        'MS_IR' : {
            'DeltaTenorRiskWeight' : 'float64',
            'DeltaInflationRiskWeight' : 'float64',
            'DeltaXCcyBasisRiskWeight' : 'float64',
            'DeltaTenorRhoTheta' : 'float64',
            'VegaUnderlyingRhoAlpha' : 'float64',
            'DeltaTenorRho' : 'float64',
            'DeltaCurveRho' : 'float64',
            'DeltaInflationRho' : 'float64',
            'DeltaXCcyBasisRho' : 'float64',
            'Gamma' : 'float64'
        },
        'MS_CR' : {
            'Bucket' : 'str',
            'CoveredBondBucket' :  'str',
            'OtherBucket' : 'str',
            'IndexBuckets' : 'str',
            'DeltaBucketRiskWeight' : 'float64',
            'DeltaCovBondAARiskWeight' : 'float64',
            'DeltaNameRho' : 'float64',
            'DeltaTenorRho' : 'float64',
            'DeltaBasisRho' : 'float64',
            'DeltaNameIndexRho' : 'float64',
            'DeltaTenorIndexRho' : 'float64',
            'DeltaBasisIndexRho' : 'float64',
            'Gamma' : 'float64',
        },
        'MS_CC' : {
            'Bucket' : 'str',
            'OtherBucket' : 'str',
            'DeltaBucketRiskWeight' : 'float64',
            'DeltaNameRho' : 'float64',
            'DeltaTenorRho' : 'float64',
            'DeltaBasisRho' : 'float64',
            'Gamma' : 'float64'
        },
        'MS_CS' : {
            'Bucket' : 'str',
            'OtherBucket' : 'str',
            'DeltaBucketRiskWeight' : 'float64',
            'DeltaTrancheRho' : 'float64',
            'DeltaTenorRho' : 'float64',
            'DeltaBasisRho' : 'float64',
            'Gamma' : 'float64'
        },
        'MS_EQ' : {
            'Bucket' : 'str',
            'OtherBucket' : 'str',
            'MarketCapThreshold' : 'int64',
            'DeltaBucketRiskWeight' : 'float64',
            'DeltaNameBucketRho' : 'float64',
            'DeltaSpotRepoRho' : 'float64',
            'Gamma' : 'float64'
        },
        'MS_CM' : {
            'Bucket' : 'str',
            'DeltaBucketRiskWeight' : 'float64',
            'DeltaCommodityRho' : 'float64',
            'DeltaTenorRho' : 'float64',
            'DeltaBasisRho' : 'float64',
            'Gamma' : 'float64',
        },
        'MS_FX' : {
            'DeltaRiskWeight' : 'float64',
            'Gamma' : 'float64',
            'ERMIIBand' : 'float64',
            'ERMIICcys' : 'float64',
        },
        'MD_CR' : {
            'LGDSenior' : 'float64',
            'LGDCovered' : 'float64',
            'CQRiskWeight' : 'float64'
        },
        'MD_CC' : {
            'CQRiskWeight' : 'float64'
        },
        'MD_CS' : {
            'CQRiskWeight' : 'float64'
        },
        'MR_RR' : {
            'RiskWeight' : 'float64'
        },
        'CVA' : {
            'BA-Bucket' : 'str',
            'BA-Rho' : 'float64',
            'BA-DiscountFactor' : 'float64',
            'BA-Alpha' : 'float64',
            'BA-Beta' : 'float64',
            'BA-DiscountScalar' : 'float64',
            'BA-RiskWeight' : 'float64',
            'BA-rDirect' : 'float64',
            'BA-rRelated' : 'float64',
            'BA-rSectorRegion' : 'float64',
            'BA-IndexDiversifictaion' : 'float64',
            'SA-HedgeDisallowance' : 'float64',
            'SA-CapitalMultiplier' : 'float64',
        },
        'CS_IR' : {
            'DeltaTenorRiskWeight' : 'float64',
            'DeltaInflationRiskWeight' : 'float64',
            'DeltaTenorIlliquidRiskWeight' : 'float64',
            'DeltaInflationIlliquidRiskWeight' : 'float64',
            'DeltaTenorRho' : 'float64',
            'DeltaInflationRho' : 'float64',
            'DeltaIlliquidRho' : 'float64',
            'VegaRiskWeight' : 'float64',
            'VegaRho' : 'float64',
            'Gamma' : 'float64',
        },
        'CS_FX' : {
            'DeltaRiskWeight' : 'float64',
            'VegaRiskWeight' : 'float64',
            'Gamma' : 'float64',
            'ERMIIBand' : 'float64',
            'ERMIICcys' : 'float64',
        },
        'CS_CC' : {
            'Bucket' : 'str',
            'CoveredBondBucket' :  'str',
            'IndexBuckets' : 'str',
            'DeltaRiskWeight' : 'float64',
            'DeltaNameRelatedRho' : 'float64',
            'DeltaNameUnrelatedRho' : 'float64',
            'DeltaTenorRho' : 'float64',
            'DeltaCreditQualityRho' : 'float64',
            'DeltaNameRelatedIndexRho' : 'float64',
            'DeltaNameUnrelatedIndexRho' : 'float64',
            'DeltaTenorIndexRho' : 'float64',
            'DeltaCreditQualityIndexRho' : 'float64',
            'Gamma' : 'float64'
        },
        'CS_CR' : {
            'Bucket' : 'str',
            'DeltaBucketRiskWeight' : 'float64',
            'VegaRiskWeight' : 'float64',
            'Gamma' : 'float64'
        },
        'CS_EQ' : {
            'Bucket' : 'str',
            'OtherBucket' : 'str',
            'MarketCapThreshold' : 'int64',
            'DeltaBucketRiskWeight' : 'float64',
            'VegaBucketRiskWeight' : 'float64',
            'DeltaBucketRho' : 'float64',
            'Gamma' : 'float64'
        },
        'CS_CM' : {
            'Bucket' : 'str',
            'DeltaBucketRiskWeight' : 'float64',
            'VegaRiskWeight' : 'float64',
            'Gamma' : 'float64'
        }
    }


    def __init__(self, regulator):
        self._name = type(self).__name__
        self._regulator = regulator
        self._config = self.readConfig()
        self._computeVegaRiskWeights()
        self._computeRho()


    def _computeVegaRiskWeights(self):
        if 'MR' not in self._config.keys():
            return

        cfg = self._config['MR']

        if 'VegaLiquidityHorizon' not in cfg.keys():
            return

        vegaLH = cfg['VegaLiquidityHorizon']
        RWSigma = cfg['VegaRiskWeightSigma']
        sqrtTen = 10 ** 0.5
        vegaLH.loc[:, 'RiskWeight'] = vegaLH['LiquidityHorizon'].astype('float64').apply(lambda x: min(RWSigma * (x ** 0.5) / sqrtTen, 1))
        self._config['MR']['VegaLiquidityHorizon'] = vegaLH

        for key, grp in vegaLH.groupby('AssetClass'):
            if key in self._config.keys():
                if key == 'MS_EQ':
                    grp.drop(columns=['AssetClass', 'LiquidityHorizon'], inplace=True)
                    grp.set_index('MarketCap', inplace=True)
                    self._config[key]['VegaRiskWeight'] = grp
                else:
                    self._config[key]['VegaRiskWeight'] = grp['RiskWeight'].iat[0]

    def __rhoExpr(self, tau, a, b):
        return math.exp(-tau * abs(a - b) / min(a, b))

    def _computeRho(self):
        cfg = self._config['MS_IR']

        if 'DeltaTenorRhoTheta' in cfg.keys() and 'DeltaTenors' in cfg.keys():
            theta = cfg['DeltaTenorRhoTheta']
            rho = np.ones((len(cfg['DeltaTenors']), len(cfg['DeltaTenors'])))

            for i, r in enumerate(cfg['DeltaTenors']):
                for j, c in enumerate(cfg['DeltaTenors']):
                    if j <= i:
                        continue
                    else:
                        rho[i, j] = rho [j, i] = max(self.__rhoExpr(theta, float(r), float(c)), 0.4)

            cfg['DeltaTenorRho'] = pd.DataFrame(rho, index=cfg['DeltaTenors'], columns=cfg['DeltaTenors'])

        if 'VegaTenors' in cfg.keys():
            alpha = cfg['VegaUnderlyingRhoAlpha']
            rho = np.ones((len(cfg['VegaTenors']), len(cfg['VegaTenors'])))

            for i, r in enumerate(cfg['VegaTenors']):
                for j, c in enumerate(cfg['VegaTenors']):
                    if j <= i:
                        continue
                    else:
                        rho[i, j] = rho [j, i] = self.__rhoExpr(alpha, float(r), float(c))

            cfg['VegaUnderlyingTenorRho'] = pd.DataFrame(rho, index=cfg['VegaTenors'], columns=cfg['VegaTenors'])

        self._config['MS_IR'] = cfg
        alpha = self._config['MR']['VegaOptionRhoAlpha']

        for assetClass in ['MS_IR', 'MS_CR', 'MS_CC', 'MS_CS', 'MS_EQ', 'MS_CM', 'MS_FX']:
            cfg = self._config[assetClass]

            if 'VegaTenors' in cfg.keys():
                rho = np.ones((len(cfg['VegaTenors']), len(cfg['VegaTenors'])))

                for i, r in enumerate(cfg['VegaTenors']):
                    for j, c in enumerate(cfg['VegaTenors']):
                        if j <= i:
                            continue
                        else:
                            rho[i, j] = rho [j, i] = self.__rhoExpr(alpha, float(r), float(c))

                cfg['VegaOptionTenorRho'] = pd.DataFrame(rho, index=cfg['VegaTenors'], columns=cfg['VegaTenors'])
                self._config[assetClass] = cfg


    def getCellValues(self, ws):
        for r in ws.iter_rows():
            vals = []
            nulls = 0

            for c in r:
                if c.value is None:
                    nulls += 1
                else:
                    if nulls:
                        vals.extend([''] * nulls)
                        nulls = 0

                    vals.append(str(c.value))

            yield vals


    def readConfig(self):
        cfpath = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'FRTB', 'Configs')
        xlfile = os.path.join(cfpath, self._configFile.format(self._regulator))
        wb = xl.load_workbook(xlfile, read_only=True, data_only=True)
        cfg = {}    

        for i, ws in enumerate(wb.worksheets):
            configClass = wb.sheetnames[i]

            if configClass in self._riskClassKeyDataType.keys():
                cfgdf = pd.DataFrame(self.getCellValues(ws)).fillna('')
                cfg[configClass] = FNU.extractKeyedData(configClass, cfgdf, self._riskClassKeyDataType[configClass], **self._riskClassCongigKeyTypes[configClass])
            elif configClass != 'Copyright':
                print(f"Unknown config sheet : {configClass} in config for {self._regulator} in {xlfile}")

        wb.close()
        return cfg


    def _argCheck(self, riskClass, item=None):
        if not riskClass in self._config.keys():
            raise ValueError(f"{self._name}: no config for riskClass '{riskClass}'")

        if not item is None and not item in self._config[riskClass].keys():
            raise ValueError(f"{self._name}: no config item '{item}' for riskClass '{riskClass}'")


    def getConfigList(self):
        return self._config.keys()

    def getConfig(self, riskClass):
        self._argCheck(riskClass)
        return self._config[riskClass]

    def getConfigItem(self, riskClass, item):
        self._argCheck(riskClass, item)
        return self._config[riskClass][item]

    def getBuckets(self, riskClass, buckets=None):
        if riskClass == 'CVA':
            self._argCheck(riskClass, 'BA-Bucket')
            bdf = self._config[riskClass]['BA-Bucket']
        else:
            self._argCheck(riskClass, 'Bucket')
            bdf = self._config[riskClass]['Bucket']

        if buckets is None:
            if isinstance(bdf, pd.DataFrame):
                return bdf['Bucket'].unique().tolist()
            else:
                return bdf.unique().tolist()
        else:
            if isinstance(bdf, pd.DataFrame()):
                return bdf[bdf['Bucket'].isin(buckets)]['Bucket'].to_list()
            else:
                return bdf[bdf['Bucket'].isin(buckets)].to_list()


if __name__ == '__main__':
    config = FRTBConfig('BCBS')
    # print(config.getConfigItem('MS_CS', 'DeltaBucketRiskWeight'))

    for cfg in config.getConfigList():
        print
        print('=' * len(cfg))
        print(cfg)
        print('=' * len(cfg))
        print(config.getConfig(cfg))

        if not cfg in ['MR', 'MS_IR', 'MS_FX', 'MD_CC', 'CS_IR', 'CS_FX']:
            print(config.getBuckets(cfg))

    print(config.getConfig('MS_FX'))
