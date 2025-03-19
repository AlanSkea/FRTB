"""
Some definitions to help translate between ISDA CRIF and frtb.net file representation.

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

import FRTBConfig as config
import FNetF

variants = {
    'MS_IRDelta'        : None,
    'MS_IRVega'         : 'Variant 1',
    'MS_IRCurvature'    : 'Variant 1a',
    'MS_CRDelta'        : None,
    'MS_CRVega'         : 'Variant 1',
    'MS_CRCurvature'    : 'Variant 1a',
    'MS_CCDelta'        : None,
    'MS_CCVega'         : 'Variant 1',
    'MS_CCCurvature'    : 'Variant 1a',
    'MS_CSDelta'        : None,
    'MS_CSVega'         : 'Variant 1',
    'MS_CSCurvature'    : 'Variant 1a',
    'MS_EQDelta'        : None,
    'MS_EQVega'         : 'Variant 1',
    'MS_EQCurvature'    : 'Variant 1a',
    'MS_CMDelta'        : None,
    'MS_CMVega'         : 'Variant 1',
    'MS_CMCurvature'    : 'Variant 1a',
    'MS_FXDelta'        : None,
    'MS_FXVega'         : 'Variant 1',
    'MS_FXCurvature'    : 'Variant 1a',
    'MD_CR_DRC'         : 'Variant 2',
    'MD_CC_DRC'         : None,
    'MD_CS_DRC'         : 'Variant 2',
    'MR_RRAO'           : None,
    'MR_RRAO'           : None,
    'CS_IRDelta'        : None,
    'CS_IRVega'         : None,
    'CS_FXDelta'        : None,
    'CS_FXVega'         : None,
    'CS_CCDelta'        : None,
    'CS_CRDelta'        : None,
    'CS_CRVega'         : None,
    'CS_EQDelta'        : None,
    'CS_EQVega'         : None,
    'CB_BAExposure'     : None,
    'CB_BAHedge'        : None
}

#
# ISDA CRIF Unit test files can select a regulator but we'd like
# to map these names to our internal regulator names
#
CRIFregulatorMap = {
    "MAR50 (Jan 23)"     : "MAR50",     # CVA Rules
    "d491 (BCBS Dec'19)" : "d491",      # Market Risk Rules
    "UK-PRA"             : "PRA",       # Market Risk & CVA Rules
    "CRR2+DA"            : "EBA",       # Market Risk & CVA Rules
    "US-FED"             : "FED",       # Market Risk & CVA Rules
}

#
# ISDA CRIF RiskClass names to our internal names
# First for Market Risk (MR) then for CVA
#
RiskClass_MR = {
    'GIRR_DELTA'        : 'MS_IRDelta',
    'GIRR_VEGA'         : 'MS_IRVega',
    'GIRR_CURV'         : 'MS_IRCurvature',
    'CSR_NS_DELTA'      : 'MS_CRDelta',
    'CSR_NS_VEGA'       : 'MS_CRVega',
    'CSR_NS_CURV'       : 'MS_CRCurvature',
    'CSR_SNC_DELTA'     : 'MS_CSDelta',
    'CSR_SNC_VEGA'      : 'MS_CSVega',
    'CSR_SNC_CURV'      : 'MS_CSCurvature',
    'CSR_SC_DELTA'      : 'MS_CCDelta',
    'CSR_SC_VEGA'       : 'MS_CCVega',
    'CSR_SC_CURV'       : 'MS_CCCurvature',
    'FX_DELTA'          : 'MS_FXDelta',
    'FX_VEGA'           : 'MS_FXVega',
    'FX_CURV'           : 'MS_FXCurvature',
    'EQ_DELTA'          : 'MS_EQDelta',
    'EQ_VEGA'           : 'MS_EQVega',
    'EQ_CURV'           : 'MS_EQCurvature',
    'COMM_DELTA'        : 'MS_CMDelta',
    'COMM_VEGA'         : 'MS_CMVega',
    'COMM_CURV'         : 'MS_CMCurvature',
    'DRC_NS'            : 'MD_CR_DRC',
    'DRC_SNC'           : 'MD_CS_DRC',
    'DRC_SC'            : 'MD_CC_DRC',
    'RRAO_1_PERCENT'    : 'MR_RRAO',
    'RRAO_01_PERCENT'   : 'MR_RRAO',
}

RiskClass_CVA = {
    'GIRR_DELTA'        : 'CS_IRDelta',
    'GIRR_VEGA'         : 'CS_IRVega',
    'CSR_REF_DELTA'     : 'CS_CRDelta',
    'CSR_REF_VEGA'      : 'CS_CRVega',
    'CSR_CPY_DELTA'     : 'CS_CCDelta',
    'EQ_DELTA'          : 'CS_EQDelta',
    'EQ_VEGA'           : 'CS_EQVega',
    'FX_DELTA'          : 'CS_FXDelta',
    'FX_VEGA'           : 'CS_FXVega',
    'COMM_DELTA'        : 'CS_CMDelta',
    'COMM_VEGA'         : 'CS_CMVega',
    'BA_EXPOSURE'       : 'CB_FULL',
    'BA_HEDGE'          : 'CB_FULL',
}

#
# Default type is 'str' if not specified
#
CRIFMappedFieldType = {
    # 'Portfolio ID'                  : 'str',
    # 'Trade ID'                      : 'str',
    # 'Variant'                       : 'str',
    # 'Sensitivity ID'                : 'str',
    # 'RiskType'                      : 'str',
    'Bucket'                        : 'str',
    'Tenor'                         : 'str',        # These next three are only used to index the correlation matrices
    'OptionMaturity'                : 'str',        # If we don't compute the correlations then leave as 'str'
    'UnderlyingResidualMaturity'    : 'str',
    'RiskWeight'                    : 'float64',
    'JTD'                           : 'float64',
    'DefaultImpact'                 : 'float64',
    'Sensitivity'                   : 'float64',
    'HedgeSensitivity'              : 'float64',
    'NotionalAmount'                : 'float64',
    # 'Notional'                      : 'float64',      # Only in DRC Variant1
    'EAD'                           : 'float64',
    'NettingSetMaturity'            : 'float64',
    'ResidualMaturity'              : 'float64',
    # 'MaturityDate'                  : 'date'          # This doesn't work - leave as 'str'
}

#
# The ISDA CRIF file has these columns for Market Risk Scenarios, in this order
#
CRIFColumns_MR = [
    'Portfolio ID',
    'Trade ID,'
    'Variant',
    'Sensitivity ID',
    'RiskType',
    'Qualifier',
    'Bucket',
    'Label1',
    'Label2',
    'Amount',
    'AmountCurrency',
    'AmountUSD',
    'Label3',
    'EndDate',
    'CreditQuality',
    'LongShortInd',
    'CoveredBondInd',
    'TrancheThickness',
]

#
# For each RiskClass we need to map fromn the overloaded ISDA CRIF columns
# to the internal representation field.
#
CRIFColumnMap_MR = {
    #
    #  ISDA Name            : Internal Name
    #
    # 'Portfolio ID'        : 'PortfolioID',
    # 'Variant'             : 'Variant',
    # 'Sensitivity ID'      : '',
    # 'RiskType'            : 'RiskClass',
    # 'Qualifier'           : 'Bucket',
    # 'Bucket'              : 'Bucket',
    # 'Label1'              : '',
    # 'Label2'              : '',
    # 'Label3'              : '',   # Implied volatiliy for Variant2 Vega
    # 'Amount'              : 'Sensitivity', 'JTD',
    # 'AmountCurrency'      : '',
    # 'Amount'              : '',
    # 'EndDate'             : '',
    # 'CerditQuality'       : '',
    # 'LongShortInd'        : '',
    # 'CoveredBondInd'      : '',
    # 'TrancheThickness'    : '',
    #

    'MS_IRDelta' : {
        'Sensitivity ID'    : 'Sensitivity ID',
        'RiskType'          : 'RiskClass',
        'Qualifier'         : 'Bucket',
        # 'Bucket'            : 'LiquidCurrency',
        'Label1'            : 'Tenor',
        'Label2'            : 'Curve',
        'Amount'            : 'Sensitivity',
    },
    'MS_IRVega' : {
        'Sensitivity ID'    : 'Sensitivity ID',
        'Variant'           : 'Variant',
        'RiskType'          : 'RiskClass',
        'Qualifier'         : 'Bucket',
        'Label1'            : 'OptionMaturity',
        'Label2'            : 'UnderlyingResidualMaturity',
        'Amount'            : 'Sensitivity',
    },
    'MS_IRCurvature' : {
        'Sensitivity ID'    : 'Sensitivity ID',
        'Variant'           : 'Variant',
        'RiskType'          : 'RiskClass',
        'Qualifier'         : 'Bucket',
        'Label1'            : 'RiskWeight',
        'Amount'            : 'Sensitivity',
    },
    'MS_CRDelta' : {
        'Sensitivity ID'    : 'Sensitivity ID',
        'RiskType'          : 'RiskClass',
        'Qualifier'         : 'CreditName',         # Issuer / Index Name
        'Bucket'            : 'Bucket',
        'Label1'            : 'Tenor',
        'Label2'            : 'CurveType',          # BOND / CDS
        'Amount'            : 'Sensitivity',
        'CreditQuality'     : 'Rating',
    },
    'MS_CRVega' : {
        'Sensitivity ID'    : 'Sensitivity ID',
        'Variant'           : 'Variant',
        'RiskType'          : 'RiskClass',
        'Qualifier'         : 'CreditName',
        'Bucket'            : 'Bucket',
        'Label1'            : 'OptionMaturity',
        'Amount'            : 'Sensitivity',
        'CreditQuality'     : 'Rating',
    },
    'MS_CRCurvature' : {
        'Sensitivity ID'    : 'Sensitivity ID',
        'Variant'           : 'Variant',
        'RiskType'          : 'RiskClass',
        'Qualifier'         : 'CreditName',
        'Bucket'            : 'Bucket',
        'Label1'            : 'RiskWeight',
        'Amount'            : 'Sensitivity',
        'CreditQuality'     : 'Rating',
    },
    'MS_CSDelta' : {
        'Sensitivity ID'    : 'Sensitivity ID',
        'RiskType'          : 'RiskClass',
        'Qualifier'         : 'Underlier',          # Issuer / Tranche / Index Name
        'Bucket'            : 'Bucket',
        'Label1'            : 'Tenor',
        'Label2'            : 'CurveType',          # BOND / CDS
        'Amount'            : 'Sensitivity',
    },
    'MS_CSVega' : {
        'Sensitivity ID'    : 'Sensitivity ID',
        'Variant'           : 'Variant',
        'RiskType'          : 'RiskClass',
        'Qualifier'         : 'Underlier',
        'Bucket'            : 'Bucket',
        'Label1'            : 'OptionMaturity',
        'Amount'            : 'Sensitivity',
    },
    'MS_CSCurvature' : {
        'Sensitivity ID'    : 'Sensitivity ID',
        'Variant'           : 'Variant',
        'RiskType'          : 'RiskClass',
        'Qualifier'         : 'Underlier',
        'Bucket'            : 'Bucket',
        'Label1'            : 'RiskWeight',
        'Amount'            : 'Sensitivity',
    },
    'MS_CCDelta' : {
        'Sensitivity ID'    : 'Sensitivity ID',
        'RiskType'          : 'RiskClass',
        'Qualifier'         : 'Underlier',          # Issuer / Tranche / Index Name
        'Bucket'            : 'Bucket',
        'Label1'            : 'Tenor',
        'Label2'            : 'CurveType',          # BOND / CDS
        'Amount'            : 'Sensitivity',
    },
    'MS_CCVega' : {
        'Sensitivity ID'    : 'Sensitivity ID',
        'Variant'           : 'Variant',
        'RiskType'          : 'RiskClass',
        'Qualifier'         : 'Underlier',
        'Bucket'            : 'Bucket',
        'Label1'            : 'OptionMaturity',
        'Amount'            : 'Sensitivity',
    },
    'MS_CCCurvature' : {
        'Sensitivity ID'    : 'Sensitivity ID',
        'Variant'           : 'Variant',
        'RiskType'          : 'RiskClass',
        'Qualifier'         : 'Underlier',          # Issuer / Tranche
        'Bucket'            : 'Bucket',
        'Label1'            : 'RiskWeight',
        'Amount'            : 'Sensitivity',
    },
    'MS_EQDelta' : {
        'Sensitivity ID'    : 'Sensitivity ID',
        'RiskType'          : 'RiskClass',
        'Qualifier'         : 'EquityName',
        'Bucket'            : 'Bucket',
        'Label2'            : 'SpotRepo',
        'Amount'            : 'Sensitivity',
    },
    'MS_EQVega' : {
        'Sensitivity ID'    : 'Sensitivity ID',
        'Variant'           : 'Variant',
        'RiskType'          : 'RiskClass',
        'Qualifier'         : 'EquityName',
        'Bucket'            : 'Bucket',
        'Label1'            : 'OptionMaturity',
        'Amount'            : 'Sensitivity',
    },
    'MS_EQCurvature' : {
        'Sensitivity ID'    : 'Sensitivity ID',
        'Variant'           : 'Variant',
        'RiskType'          : 'RiskClass',
        'Qualifier'         : 'EquityName',
        'Bucket'            : 'Bucket',
        'Label1'            : 'RiskWeight',
        'Amount'            : 'Sensitivity',
    },
    'MS_CMDelta' : {
        'Sensitivity ID'    : 'Sensitivity ID',
        'RiskType'          : 'RiskClass',
        'Qualifier'         : 'CommodityName',
        'Bucket'            : 'Bucket',
        'Label1'            : 'Tenor',
        'Label2'            : 'DeliveryLocation',
        'Amount'            : 'Sensitivity',
    },
    'MS_CMVega' : {
        'Sensitivity ID'    : 'Sensitivity ID',
        'Variant'           : 'Variant',
        'RiskType'          : 'RiskClass',
        'Qualifier'         : 'CommodityName',
        'Bucket'            : 'Bucket',
        'Label1'            : 'OptionMaturity',
        'Amount'            : 'Sensitivity',
    },
    'MS_CMCurvature' : {
        'Sensitivity ID'    : 'Sensitivity ID',
        'Variant'           : 'Variant',
        'RiskType'          : 'RiskClass',
        'Qualifier'         : 'CommodityName',
        'Bucket'            : 'Bucket',
        'Label1'            : 'RiskWeight',
        'Amount'            : 'Sensitivity',
    },
    'MS_FXDelta' : {
        'Sensitivity ID'    : 'Sensitivity ID',
        'RiskType'          : 'RiskClass',
        'Qualifier'         : 'Bucket',
        'Bucket'            : 'LiquidCurrency',     # 1 = Liquid, 2 = Illiquid
        'Amount'            : 'Sensitivity',
    },
    'MS_FXVega' : {
        'Sensitivity ID'    : 'Sensitivity ID',
        'Variant'           : 'Variant',
        'RiskType'          : 'RiskClass',
        'Qualifier'         : 'Bucket',
        'Label1'            : 'OptionMaturity',
        'Amount'            : 'Sensitivity',
    },
    'MS_FXCurvature' : {
        'Sensitivity ID'    : 'Sensitivity ID',
        'Variant'           : 'Variant',
        'RiskType'          : 'RiskClass',
        'Qualifier'         : 'Bucket',
        'Bucket'            : 'LiquidCurrency',     # 1 = Liquid, 2 = Illiquid
        'Label1'            : 'RiskWeight',
        'Amount'            : 'Sensitivity',
    },
    'MD_CR_DRC' : {
        'Sensitivity ID'    : 'Sensitivity ID',
        'Variant'           : 'Variant',
        'RiskType'          : 'RiskClass',
        'Qualifier'         : 'Name',
        'Bucket'            : 'Bucket',
        'Label2'            : 'Seniority',
        'Amount'            : 'JTD',
        # 'Label3'            : 'Notional',          # Only in Variant1
        'EndDate'           : 'MaturityDate',
        'CreditQuality'     : 'Rating',
        'LongShortInd'      : 'LongShortInd',
        'CoveredBondInd'    : 'CoveredBondInd',
    },
    'MD_CS_DRC' : {
        'Sensitivity ID'    : 'Sensitivity ID',
        'Variant'           : 'Variant',
        'RiskType'          : 'RiskClass',
        'Qualifier'         : 'Issuer/Tranche',
        'Bucket'            : 'Bucket',
        # 'Label2'            : 'Seniority',         # Only in deprecated Variant 1
        'Amount'            : 'JTD',
        'EndDate'           : 'MaturityDate',
        'CreditQuality'     : 'RiskWeight'          # Variant 2.  In (deprecated) Variant 1 'Rating' and the TrancheThickness is needed instead
    },
    'MD_CC_DRC' : {
        'Sensitivity ID'    : 'Sensitivity ID',
        'Variant'           : 'Variant',
        'RiskType'          : 'RiskClass',
        'Qualifier'         : 'Series',
        'Bucket'            : 'Bucket',
        'Label1'            : 'Tranche',            # e.g. for ITRAXX Europe it could be 0-3, 22-100.  For a SingleName Hedge, the ObligorName, 
        'Label2'            : 'ExposureType',       # CDSIndex, CDSIndexTranche, SingleNameHedge, Bespoke.
        'Amount'            : 'JTD',
        'EndDate'           : 'MaturityDate',
        'CreditQuality'     : 'Rating',             # Variant 2.  In Variant 1 this is the RiskWeight.  FNetF supports both variants.
        # 'LongShortInd'      : 'LongShortInd',
        # 'TrancheThickness'  : 'TrancheThickness'
    },
    'MR_RRAO' : {                                   # This one needs some code to set the Bucket appropriately (Exotic / Non-Exotic)
        'Sensitivity ID'    : 'Sensitivity ID',
        'RiskType'          : 'RiskClass',
        'Bucket'            : 'Bucket',
        'Amount'            : 'NotionalAmount',
    },
}

#
# The ISDA CRIF file has these columns for CVA Scenarios, in this order
#
CRIFColumns_CVA = [
    'Portfolio ID',
    'Trade ID',
    'Variant',
    'Sensitivity ID',
    'RiskType',
    'Qualifier',
    'Bucket',
    'Label1',
    'Label2',
    'Amount',
    'AmountCurrency',
    'AmountUSD',
    'Label3',
    'EndDate',
    'CreditQuality',
    'UltimateParent',
]

#
# For each RiskClass we need to map fromn the overloaded ISDA CRIF columns
# to the internal representation field.
#
CRIFColumnMap_CVA = {
    #
    #  ISDA Name            : Internal Name
    #
    # 'Portfolio ID'        : 'PortfolioID',
    # 'Variant'             : 'Variant',
    # 'Sensitivity ID'      : '',
    # 'RiskType'            : 'RiskClass',
    # 'Qualifier'           : 'Bucket',
    # 'Bucket'              : 'Bucket',
    # 'Label1'              : '',
    # 'Label2'              : '',
    # 'Label3'              : '', # Implied vol for Variant2 Vega
    # 'Amount'              : 'Amount',
    # 'AmountCurrency'      : 'AmountCurrency',
    # 'Amount'              : 'Sensitivity', 'JTD',
    # 'EndDate'             : '',
    # 'CerditQuality'       : '',
    # 'LongShortInd'        : '',
    # 'CoveredBondInd'      : '',
    # 'TrancheThickness'    : '',
    #

    'CS_IRDelta' : {
        'Sensitivity ID' : 'Sensitivity ID',
        'RiskType'       : 'RiskClass',
        'Qualifier'      : 'Bucket',
        'Bucket'         : 'LiquidCurrency',    # 1 = Liquid, 2 = Illiquid
        'Label1'         : 'Tenor',             # or INFL or XCCY
        'Label2'         : 'C_Hedge',
        'Amount'         : 'Sensitivity',
    },
    'CS_IRVega' : {
        'Sensitivity ID' : 'Sensitivity ID',
        'RiskType'       : 'RiskClass',
        'Qualifier'      : 'Bucket',
        'Label1'         : 'CurveType',         # IR or INFL
        'Label2'         : 'C_Hedge',
        'Amount'         : 'Sensitivity',
    },
    'CS_CRDelta' : {
        'Sensitivity ID' : 'Sensitivity ID',
        'RiskType'       : 'RiskClass',
        'Bucket'         : 'Bucket',
        'Label2'         : 'C_Hedge',
        'Amount'         : 'Sensitivity',
    },
    'CS_CRVega' : {
        'Sensitivity ID' : 'Sensitivity ID',
        'RiskType'       : 'RiskClass',
        'Bucket'         : 'Bucket',
        'Label2'         : 'C_Hedge',
        'Amount'         : 'Sensitivity',
    },
    'CS_CCDelta' : {
        'Sensitivity ID' : 'Sensitivity ID',
        'RiskType'       : 'RiskClass',
        'Bucket'         : 'Bucket',
        'Label1'         : 'Tenor',
        'Label2'         : 'C_Hedge',
        'Lael3'          : 'ParentName',
        'CreditQuality'  : 'IG_HYNR',
        'Amount'         : 'Sensitivity',
        'Qualifier'      : 'CreditName',
    },
    'CS_EQDelta' : {
        'Sensitivity ID' : 'Sensitivity ID',
        'RiskType'       : 'RiskClass',
        'Bucket'         : 'Bucket',
        'Label2'         : 'C_Hedge',
        'Amount'         : 'Sensitivity',
    },
    'CS_EQVega' : {
        'Sensitivity ID' : 'Sensitivity ID',
        'RiskType'       : 'RiskClass',
        'Bucket'         : 'Bucket',
        'Label2'         : 'C_Hedge',
        'Amount'         : 'Sensitivity',
    },
    'CS_FXDelta' : {
        'Sensitivity ID' : 'Sensitivity ID',
        'RiskType'       : 'RiskClass',
        'Qualifier'      : 'Bucket',
        'Bucket'         : 'LiquidCurrency',    # 1 = Liquid, 2 = Illiquid
        'Label2'         : 'C_Hedge',
        'Amount'         : 'Sensitivity',
    },
    'CS_FXVega' : {
        'Sensitivity ID' : 'Sensitivity ID',
        'RiskType'       : 'RiskClass',
        'Qualifier'      : 'Bucket',
        'Bucket'         : 'LiquidCurrency',    # 1 = Liquid, 2 = Illiquid
        'Label2'         : 'C_Hedge',
        'Amount'         : 'Sensitivity',
    },
    'CS_CMDelta' : {
        'Sensitivity ID' : 'Sensitivity ID',
        'RiskType'       : 'RiskClass',
        'Qualifier'      : 'CommodityName',
        'Bucket'         : 'Bucket',
        'Label2'         : 'C_Hedge',
        'Amount'         : 'Sensitivity',
    },
    'CS_CMVega' : {
        'Sensitivity ID' : 'Sensitivity ID',
        'RiskType'       : 'RiskClass',
        'Qualifier'      : 'CommodityName',
        'Bucket'         : 'Bucket',
        'Label2'         : 'C_Hedge',
        'Amount'         : 'Sensitivity',
    },
    'CB_REDUCED' : {                            # This one needs some code to set the PositionType appropriately (Exposure only, never Hedge)
        'Sensitivity ID' : 'Sensitivity ID',
        'RiskType'       : 'RiskClass',
        'Qualifier'      : 'CreditName',
        'Bucket'         : 'Bucket',
        'Label1'         : 'NettingSetMaturity',
        'Label2'         : 'Region',
        'Amount'         : 'EAD',
        'Label3'         : 'CounterpartyGroup',
        'CreditQuality'  : 'IG_HYNR',
        'UltimateParent' : 'ParentName',
    },
    'CB_FULL' : {                               # This one needs some code to set the PositionType appropriately (Exposure / Hedge)
        'Sensitivity ID' : 'Sensitivity ID',
        'RiskType'       : 'RiskClass',
        'Qualifier'      : 'CreditName',
        'Bucket'         : 'Bucket',
        'Label1'         : 'NettingSetMaturity',
        'Label2'         : 'Region',
        'Amount'         : 'EAD',
        'Label3'         : 'CounterpartyGroup',
        'CerditQuality'  : 'IG_HYNR',
        'UltimateParent' : 'ParentName',
    },
}

class CRIF(FNetF.FNetF):
    def __init__(self, regulator, cva, sensis):
        super().__init__()
        self._config = config.FRTBConfig(regulator)
        self._CVA = cva
        self._CRIFsensis = sensis
        self.CRIFtoFNetF()


    def _CRIFtoFNetF(self, riskClass, riskClassColMap, df):         # ISDA CRIF to frtb.net format, just one riskClass at a time
        dropCols = []
        cvrCols = []

        for col in df.columns:
            if col not in riskClassColMap.keys():
                dropCols.append(col)
            else:
                newCol = riskClassColMap[col]

                if newCol not in ['Sensitivity', 'Variant']:
                    cvrCols.append(newCol)

        ndf = df.drop(columns=dropCols).rename(columns=riskClassColMap)

        #
        # Only keep the variants that we will use
        #
        if not variants[riskClass] is None:
            ndf = ndf[ndf['Variant'] == variants[riskClass]].drop(columns=['Variant'])

        # If we have SubBuckets then break them out
        #
        if 'SubBucket' in FNetF.FNetFieldType[riskClass].keys():
            if riskClass[:5] == 'MD_CR':
                ndf.loc[:, 'SubBucket'] = 'Cash'            # This exists only for use in the reg. reporting templates (Cash / Deriv / DerivAlt), CRIF has no info on this.
            elif riskClass[:5] == 'MR_RR':
                ndf.loc[:, 'SubBucket'] = ''                # This exists only for use in the reg. reporting templates, CRIF has no info on this.
            else:
                if riskClass.startswith('MS_CR'):
                    CBBkt = self._config.getConfigItem('MS_CR', 'CoveredBondBucket')
                    HQ = self._config.getConfigItem('MS_CR', 'CoveredBondHighQuality')

                    if riskClass .endswith('Delta'):
                        ndf.loc[(ndf['Bucket']==CBBkt) & (ndf['Rating'].isin(HQ)), ['Bucket']] = CBBkt+'a'
                        ndf.loc[(ndf['Bucket']==CBBkt) & (~ndf['Rating'].isin(HQ)), ['Bucket']] = CBBkt+'b'
                    else:
                        # The SubBucket is only used in MS_CRDelta and so can be anything for the others
                        # as we don't have Rating we just assign arbitrarily
                        ndf.loc[ndf['Bucket']==CBBkt, ['Bucket']] = CBBkt+'b'

                SubBuckets = self._config.getConfigItem(riskClass[:5], 'Bucket')[['Bucket', 'SubBucket']]
                bktMap = dict([(sb['Bucket']+sb['SubBucket'], (sb['Bucket'], sb['SubBucket'])) for _, sb in SubBuckets.iterrows()])
                ndf.loc[:, 'SubBucket'] = ndf['Bucket'].apply(lambda x : bktMap[x][1] if x in bktMap.keys() else x)
                ndf.loc[:, 'Bucket'] = ndf['Bucket'].apply(lambda x : bktMap[x][0] if x in bktMap.keys() else x)

        #
        # Special magic for riskClass specific transformations
        #
        if riskClass == 'MS_IRDelta':
            ndf.loc[:, 'CurveType'] = ndf['Tenor'].apply(lambda x : x if x in ['INFL', 'XCCY'] else 'IR')
            ndf.loc[:, 'Tenor'] = ndf['Tenor'].apply(lambda x : 0.0 if x in ['INFL', 'XCCY'] else x)
            ndf.loc[:, 'Curve'] = ndf['Curve'].fillna("")
        elif riskClass == 'MS_IRVega':
            ndf.loc[:, 'CurveType'] = ndf['UnderlyingResidualMaturity'].apply(lambda x : x if x in ['INFL', 'XCCY'] else 'IR')
            ndf.loc[:, 'UnderlyingResidualMaturity'] = ndf['UnderlyingResidualMaturity'].apply(lambda x : 0.0 if x in ['INFL', 'XCCY'] else x)
            ndf.loc[:, 'OptionMaturity'] = ndf['OptionMaturity'].apply(lambda x : 0.0 if x in ['INFL', 'XCCY'] else x)
        elif riskClass == 'CS_IRDelta':
            ndf.loc[:, 'CurveType'] = ndf['Tenor']
            ndf.loc[:, 'Tenor'] = ndf['Tenor'].apply(lambda x : 0.0 if x in ['INFL', 'IR'] else x)
        elif riskClass == 'MS_EQDelta':
            ndf.loc[:, 'SpotRepo'] = ndf['SpotRepo'].str.capitalize()
        elif riskClass[:5] == 'MD_CR':
            ndf.loc[:, 'Seniority'] = ndf.apply(lambda x : 'COVERED' if x['CoveredBondInd'] == 'Y' else x['Seniority'], axis=1)
        elif riskClass[:5] == 'MD_CC':
            ndf.loc[:, 'RiskWeight'] = pd.to_numeric(ndf['Rating'], errors='coerce')
            ndf.loc[~ndf['RiskWeight'].isnull(), 'Rating'] = None
        elif riskClass[:5] == 'CS_BA':  # BAExposure or BAHedge.  These both become BA_CVA
            ndf.loc[:, 'Bucket'] = ndf['Bucket'].str[:-1]
            ndf.loc[:, 'BA-CVA-Type'] = ndf['RiskClass']
            ndf.loc[:, 'RiskClass'] = ndf['BA_CVA']
            ndf.loc[:, 'NameOrIndex'] = ndf.apply(lambda x : 'Index' if x['BA-CVA-Type']=='BAHedge' and x['CounterpartyGroup'].startswith('INDEX_') else 'Name', axis=1)

        if riskClass[:3] == 'CS_':
            ndf.loc[:, 'HedgeSensitivity'] = ndf.apply(lambda x : x['Sensitivity'] if x['C_Hedge'] == 'HDG' else 0.0, axis=1)
            ndf.loc[:, 'Sensitivity'] = ndf.apply(lambda x : x['Sensitivity'] if x['C_Hedge'] == 'CVA' else 0.0, axis=1)

        # Set the data types
        #
        ndf = ndf.astype(dict((k, CRIFMappedFieldType[k]) for k in ndf.columns if k in CRIFMappedFieldType.keys()))

        # Drop any buckets that we don't recognise
        #
        if not riskClass[:5] in ['MS_IR', 'MS_FX', 'MD_CR', 'MD_CS', 'MD_CC', 'MR_RR', 'CB_BA']:
            dropBuckets = ndf[~ndf['Bucket'].isin(self._config.getBuckets(riskClass[:5]))]

            if not dropBuckets.empty:
                print(f"Warning: Dropping {len(dropBuckets)} rows with unknown Buckets for {riskClass}: Sensitivities {', '.join(dropBuckets['Sensitivity ID'].unique())}")
                ndf = ndf[ndf['Bucket'].isin(self._config.getBuckets(riskClass[:5]))]

        # curvature records come as two rows in CRIF but are a single row in FNetF
        #
        if riskClass[5:] == 'Curvature':
            down = ndf[ndf['RiskWeight'] < 0.0].copy()
            down.loc[:, 'RiskWeight'] = -down['RiskWeight']
            down = down.rename(columns={'Sensitivity' : 'CVR-'})
            up = ndf[ndf['RiskWeight'] > 0.0]
            up = up.rename(columns={'Sensitivity' : 'CVR+'})
            ndf = up.merge(down, on=cvrCols)

        ndf.loc[:, 'RiskGroup'] = 'UnitTests'
        ndf.loc[:, 'RiskSubGroup'] = 'Main'
        ndf.set_index(['RiskGroup', 'RiskSubGroup', 'RiskClass', 'Bucket'], inplace=True)
        return ndf


    def CRIFtoFNetF(self):
        sensis = self._CRIFsensis.copy()

        if self._CVA:
            riskClassMap = RiskClass_CVA
            CRIFColumnMap = CRIFColumnMap_CVA
            sensis.loc[sensis['RiskType']=='BA_Exposure', 'PositionType'] = 'Exposure'
            sensis.loc[sensis['RiskType']=='BA_Hedge', 'PositionType'] = 'Hedge'
            sensis.loc[sensis['RiskType']=='BA_Hedge', 'IndexHedge'] =  True if sensis['CounterpartyGroup'].startswith('INDEX_') else False
        else:
            riskClassMap = RiskClass_MR
            CRIFColumnMap = CRIFColumnMap_MR
            sensis.loc[sensis['RiskType']=='RRAO_1_PERCENT', 'Bucket'] = 'Exotic'
            sensis.loc[sensis['RiskType']=='RRAO_01_PERCENT', 'Bucket'] = 'Non-Exotic'

        sensis.loc[:, 'RiskType'] = sensis['RiskType'].replace(riskClassMap)
        RiskClassSensis = {}

        for rc, rcColMap in CRIFColumnMap.items():
            df = self._CRIFtoFNetF(rc, rcColMap, sensis[sensis['RiskType']==rc])

            if self._CVA and rc[:2] == 'BA':
                classKey = 'BA-CVA'
            else:
                classKey = rc

            if classKey in RiskClassSensis:
                RiskClassSensis[classKey] = pd.concat([RiskClassSensis[classKey], df], axis=0)
            else:
                RiskClassSensis[classKey] = df

        for rc, df in RiskClassSensis.items():
            self.setRiskClassData(rc, df)

        sensiRiskClass = sensis[['Sensitivity ID', 'RiskType']]

        if self._CVA:
            sensiRiskClass.replace(to_replace=['BAExposure', 'BAHedge'], value='BA_CVA', inplace=True)

        self._sensiRiskClassMap = sensiRiskClass.drop_duplicates().set_index('Sensitivity ID')


    def getSensiRiskClassMap(self):
        return self._sensiRiskClassMap


    def FNetFtoCRIF(self, rc, df, extras={}):        # frtb.net format to ISDA CRIF,  just one riskClass at a time
        if rc[1] == 'C':
            isCVA = True
            CRIFcols = CRIFColumns_CVA
            riskClassMap = RiskClass_CVA
            rcolMap = CRIFColumnMap_CVA
        else:
            isCVA = False
            CRIFcols = CRIFColumns_MR
            riskClassMap = RiskClass_MR
            rcolMap = CRIFColumnMap_MR

        rcRevMap = {v : k for k, v in riskClassMap.items()}
        ndf = df.reset_index()
        res = []
        sid = 0

        if 'SubBucket' in ndf.columns and not rc.startswith('MS_CR'):
            ndf.loc[:, 'Bucket'] = ndf['Bucket'] + ndf['SubBucket']

        if rc == 'CS_CCDelta':
            ndf.loc[:, 'IG'] = ndf['IG'].apply(lambda x : 'IG' if x == 'TRUE' else 'HY_NR')

        for r, rs in ndf.iterrows():
            CRIFrow = {}

            for c in CRIFcols:
                if c in rcolMap[rc].keys():
                    if c == "Sensitivity ID" and not rcolMap[rc][c] in ndf.columns:
                        sensiID = f"S_{rc}_{sid:04d}"
                        sid += 1

                        # if 'Trade ID' in extras.keys():
                        #     sensiID += extras['Trade ID'] + "_"

                        CRIFrow[c] = sensiID

                    if c == "RiskType":
                        CRIFrow[c] = rcRevMap[rc]
                    elif c == 'Variant':
                        CRIFrow[c] = variants[rc]
                    elif rcolMap[rc][c] in ndf.columns:
                        CRIFrow[c] = rs[rcolMap[rc][c]]
                elif c in extras.keys():
                    CRIFrow[c] = extras[c]

            if rc == 'CB_BACVA':
                CRIFrow['RiskType'] = 'BA_' + CRIFrow['PositionType']
            elif rc == 'MR_RRAO':
                CRIFrow['RiskType'] = 'RRAO_' + ('1' if CRIFrow['Bucket'].startswith('Exotic') else '01') + '_PERCENT'

            # for risk classes that can treat liquid currencies specially,
            # we need to set the Bucket to reflect the liquidity of the currency
            #       1 = Illiquid, 2 = Liquid
            if rc in ['MS_FXDelta', 'MS_FXCurvature', 'CS_FXDelta',
                      'MS_IRDelta', 'MS_IRCurvature', 'CS_IRDelta']:
                ac = rc[:5]
                BaselCcys = self._config.getConfigItem(ac, 'BaselCcys')

                if rs.at['Bucket'] in BaselCcys:
                    CRIFrow['Bucket'] = '2'
                else:
                    CRIFrow['Bucket'] = '1'

            if rc.endswith('Curvature'):
                CRIFrow['Amount'] = rs.at['CVR+']
                res.append(CRIFrow)
                CRIFrow = CRIFrow.copy()
                CRIFrow['Label1'] = -rs.at['RiskWeight']
                CRIFrow['Amount'] = rs.at['CVR-']
            elif rc[4:6] == 'IR' and rc[6:] != 'Curvature':
                curveType = rs.at['CurveType']

                if rc == 'M_IRVega':
                    CRIFrow['Label2'] = curveType
                elif not (rc[:3] == 'CS_' and curveType == 'IR' and CRIFcols['Bucket'] == '2'):
                    CRIFrow['Label1'] = curveType
            elif rc == 'MS_EQDelta':
                CRIFrow['Label2'] = CRIFrow['Label2'].upper()
            elif rc == 'MD_CR_DRC' and CRIFrow['Label2'] == 'COVERED':
                CRIFrow['Label2'] = 'SENIOR'    # gotta put something - assume SENIOR
                CRIFrow['CoveredBondInd'] = 'Y'

            if isCVA and rs.at['HedgeSensitivity'] != 0.0:
                if rs.at['Sensitivity'] != 0.0:
                    CRIFrow['Label2'] = 'CVA'
                    res.append(CRIFrow)
                    CRIFrow = CRIFrow.copy()

                CRIFrow['Amount'] = rs.at['HedgeSensitivity']
                CRIFrow['Label2'] = 'HDG'

            res.append(CRIFrow)

        outdf = pd.DataFrame(res, columns=CRIFcols).fillna("").astype(str)
        outdf.loc[:, 'AmountUSD'] = outdf['Amount']
        outdf.loc[:, 'AmountCurrency'] = 'USD'
        return outdf


    def elaborateCRIF(self, comboSensis):
        if self._CVA:
            Cdf = pd.DataFrame(columns=CRIFColumns_CVA)
        else:
            Cdf = pd.DataFrame(columns=CRIFColumns_MR)

        for key, grp in comboSensis.groupby(['Combination ID', 'RiskClass']):
            sensiDf = self._CRIFsensis.copy()
            sensiDf = sensiDf[sensiDf['Sensitivity ID'].isin(grp['Sensitivity ID'])]

            if not variants[key[1]] is None:
                sensiDf = sensiDf[sensiDf['Variant'] == variants[key[1]]]

            if not sensiDf.empty:
                sensiDf.loc[:, 'Portfolio ID'] = key[0]
                Cdf = pd.concat([Cdf, sensiDf], axis=0)

        return Cdf


    def elaborateFNetFtoCRIF(self, CS):
        CRIFdfMR = pd.DataFrame()
        CRIFdfCVA = pd.DataFrame()

        for combo, grp1 in CS.groupby(['Combination ID', 'RiskClass']):
            for rc, grp2 in grp1.groupby(['RiskClass']):
                sdf = self.getRiskClassData(rc[0])
                crifFrag = self.FNetFtoCRIF(rc[0], sdf[sdf['Sensitivity ID'].isin(grp2['Sensitivity ID'])])
                crifFrag.loc[:, 'Portfolio ID'] = combo[0]

                if rc[-3:] == 'CVA':
                    CRIFdfCVA = pd.concat([CRIFdfCVA, crifFrag], axis=0)
                else:
                    CRIFdfMR = pd.concat([CRIFdfMR, crifFrag], axis=0)

        return CRIFdfMR, CRIFdfCVA
