"""
The parent of all the frtb.net core calculators.  Defines some common interfaces.

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
import datetime as dt
import FRTBConfig as cf


classDict = {}

def registerClass(cls):
    classDict[cls.__name__[:5]] = cls
    return cls


class FRTBCalculator(object):
    def __init__(self, assetClass, regulator, ccy, cob):
        self._assetClass = assetClass
        self._regulator = regulator
        self._calcCcy = ccy     # calculaion currency - we don't do translation risk at preent.
        self._config = cf.FRTBConfig(regulator)
        self._ownCcy = self._config.getConfigItem('MR', 'ReportingCurrency')
        self._name = self.__class__.__name__

        if isinstance(cob, dt.datetime):
            self._cob = cob.date()
        elif isinstance(cob, dt.date):
            self._cob = cob
        else:
            raise ValueError(f"'{cob}' : Invalid date type: {type(cob)}")

        if assetClass[:2] == 'MS':    # Market Risk SBM
            self._correlationLevels = ['Low', 'Medium', 'High']
            self._CVA = False
        else:                       # BA-CVA, SA-CVA, SA-DRC, SA-RRAO
            self._correlationLevels = ['Medium']
            self._hedgeDisallowance = self._config.getConfigItem('CVA', 'SA-HedgeDisallowance')
            self._CVA = True


    @classmethod
    def create(cls, assetClass, regulator, ccy, cob):
        if assetClass in classDict.keys():
            return classDict[assetClass](assetClass, regulator, ccy, cob)
        else:
            raise ValueError('Invalid type {}'.format(assetClass))


    def prepareData(self, riskClass, df):
        # apply the transforms peculiar to the RiskClass such that
        # the data is ready for the applyRiskWeights method.
        #
        # Override  as appropriate in the derived class
        return df


    def getFactorNettingFields(self, riskClass=None):
        return []


    @abc.abstractmethod
    def calcRiskClassCapital(self, df):
        # This pure virtual method is the primary entry point and computes capital for a
        # single risk class at all the necessary correlation levels.  It returns a list
        # of Dictionaries, one for each correlatiopn level, with an entry for RiskClass
        # and a entries for for the various results at that correlation level.  E.g.:
        #   {
        #       'RiskClass'     : 'MS_IRDelta',
        #       'Correlation'   : 'Low',
        #       'Capital'       : 123.45,
        #       'Sb'            : 234.56,
        #       'SbAlt'         : 345.67
        #   }
        #
        return {}


    def getConfig(self):
        return self._config.getConfig(self._assetClass)


    def getConfigItem(self, item):
        return self._config.getConfigItem(self._assetClass, item)
