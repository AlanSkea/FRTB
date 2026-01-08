# FNetF (frtb.net Format) Documentation

**Version:** 3.0
**Copyright:** (C) 2024-2025 frtb.net limited

This document provides comprehensive documentation for the FNetF (frtb.net Format) file format, which is used for storing FRTB (Fundamental Review of the Trading Book) sensitivity data and unit tests. The format supports both Excel (.xlsx) and JSON (.json) representations.

---

## Table of Contents

1. [Overview](#overview)
2. [File Structure](#file-structure)
3. [RiskClass Naming Convention](#riskclass-naming-convention)
4. [Common Fields](#common-fields)
5. [Market Risk - Sensitivities Based Method (MS_*)](#market-risk---sensitivities-based-method-ms_)
6. [Market Risk - Default Risk Charge (MD_*)](#market-risk---default-risk-charge-md_)
7. [Market Risk - Residual Risk Add-On (MR_*)](#market-risk---residual-risk-add-on-mr_)
8. [CVA Risk - Sensitivities Based Method (CS_*)](#cva-risk---sensitivities-based-method-cs_)
9. [CVA Risk - Basic Approach (CB_*)](#cva-risk---basic-approach-cb_)
10. [Unit Test Tabs](#unit-test-tabs)

---

## Overview

FNetF is a standardized format for storing:
- **Sensitivity data** for FRTB capital calculations
- **Unit test definitions** with benchmark results for validation

The format can be stored in two equivalent representations:
- **Excel format** (.xlsx): Each RiskClass is a separate worksheet tab
- **JSON format** (.json): Structured document with equivalent data

---

## File Structure

### Excel Format Structure

| Sheet Name | Description |
|------------|-------------|
| `Copyright` | License and copyright information |
| `Parameters` | Key-value pairs for file metadata |
| `ObligorTests` | Unit tests at obligor level (optional) |
| `FactorTests` | Unit tests at factor level (optional) |
| `BucketTests` | Unit tests at bucket level (optional) |
| `CapitalTests` | Unit tests for capital calculations |
| `<RiskClass>` | One sheet per RiskClass (e.g., `MS_IRDelta`, `MD_CR_DRC`) |

#### Parameters Sheet

The Parameters sheet contains key-value pairs in two columns:

| Parameter | Description | Example |
|-----------|-------------|---------|
| `FNetFormatVersion` | Format version (must be "3.0") | `3.0` |
| `COB Date` | Close of Business date | `2024-04-01` |
| `Regulator` | Regulatory framework | `BCBS`, `EU-EBA`, `UK-PRA` |
| `ReportingCcy` | Reporting currency | `USD` |
| `CalculationCcy` | Calculation currency | `USD` |
| `FNetTestSetVersion` | Test set version | `0.9` |

### JSON Format Structure

```json
{
  "_copyright": {
    "value": ["Copyright text lines..."],
    "type": "text",
    "note": "Copyright and license information"
  },
  "_parameters": {
    "FNetFormatVersion": "3.0",
    "COB Date": "2024-04-01",
    "Regulator": "BCBS",
    "ReportingCcy": "USD",
    "CalculationCcy": "USD"
  },
  "_tests": {
    "CapitalTests": {
      "columns": ["Test ID", "RiskClass", "Description", ...],
      "data": [["MS_IR_000000", "MS_IRDelta", "...", ...], ...]
    }
  },
  "_sensitivities": {
    "MS_IRDelta": {
      "columns": ["Sensitivity ID", "RiskGroup", ...],
      "dtypes": {"Sensitivity ID": "str", "Sensitivity": "float64", ...},
      "data": [["MS_IRD_00000", "UnitTests", ...], ...]
    }
  },
  "_schema": {
    "description": "Field type definitions",
    "risk_classes": {...}
  }
}
```

---

## RiskClass Naming Convention

RiskClasses follow a systematic naming pattern:

```
[Regulation][Method]_[AssetClass][RiskType]
```

### First Character - Regulation Type
| Code | Meaning |
|------|---------|
| `M` | Market Risk |
| `C` | CVA (Credit Valuation Adjustment) |

### Second Character - Calculation Method
| Code | Meaning |
|------|---------|
| `S` | SBM (Sensitivities Based Method) |
| `D` | DRC (Default Risk Charge) |
| `R` | RRAO (Residual Risk Add-On) |
| `B` | BA-CVA (Basic Approach CVA) |

### After Underscore - Asset Class
| Code | Asset Class |
|------|-------------|
| `IR` | Interest Rate |
| `CR` | Credit Spread (Non-Securitisation) |
| `CC` | Credit Spread (Correlation - Securitisation) |
| `CS` | Credit Spread (Securitisation Non-Correlation) |
| `EQ` | Equity |
| `CM` | Commodity |
| `FX` | Foreign Exchange |

### Risk Types (SBM only)
| Suffix | Risk Type |
|--------|-----------|
| `Delta` | Delta sensitivity |
| `Vega` | Vega sensitivity |
| `Curvature` | Curvature risk |

### Examples
- `MS_IRDelta` = Market Risk, SBM, Interest Rate, Delta
- `MD_CR_DRC` = Market Risk, DRC, Credit (Non-Securitisation)
- `CS_CCDelta` = CVA Risk, SBM, Credit Correlation, Delta
- `MR_RRAO` = Market Risk, Residual Risk Add-On

---

## Common Fields

All RiskClass sheets/objects contain these common fields:

| Field | Type | Description |
|-------|------|-------------|
| `Sensitivity ID` | str | Unique identifier for the sensitivity row |
| `RiskGroup` | str | Grouping for portfolio segmentation |
| `RiskSubGroup` | str | Sub-grouping within RiskGroup |
| `RiskClass` | str | The RiskClass name (e.g., `MS_IRDelta`) |

---

## Market Risk - Sensitivities Based Method (MS_*)

### MS_IRDelta - Interest Rate Delta

Delta sensitivities for interest rate risk.

| Field | Type | Description |
|-------|------|-------------|
| `Bucket` | str | Currency (e.g., `EUR`, `USD`, `JPY`) |
| `CurveType` | str | Type of curve: `IR` (yield), `Inflation`, `XCcyBasis` |
| `Curve` | str | Curve identifier (e.g., `IR_Curve_A`) |
| `Tenor` | str | Tenor point: `0.25`, `0.5`, `1`, `2`, `3`, `5`, `10`, `15`, `20`, `30` |
| `Sensitivity` | float64 | Delta sensitivity value |

**Excel Example:**
| Sensitivity ID | RiskGroup | RiskSubGroup | RiskClass | Bucket | CurveType | Curve | Tenor | Sensitivity |
|----------------|-----------|--------------|-----------|--------|-----------|-------|-------|-------------|
| MS_IRD_00000 | UnitTests | Main | MS_IRDelta | EUR | IR | IR_Curve_A | 0.25 | 1000 |

**JSON Example:**
```json
{
  "columns": ["Sensitivity ID", "RiskGroup", "RiskSubGroup", "RiskClass", "Bucket", "CurveType", "Curve", "Tenor", "Sensitivity"],
  "dtypes": {
    "Sensitivity ID": "str",
    "RiskGroup": "str",
    "RiskSubGroup": "str",
    "RiskClass": "str",
    "Bucket": "str",
    "CurveType": "str",
    "Curve": "str",
    "Tenor": "str",
    "Sensitivity": "float64"
  },
  "data": [
    ["MS_IRD_00000", "UnitTests", "Main", "MS_IRDelta", "EUR", "IR", "IR_Curve_A", "0.25", 1000.0]
  ]
}
```

---

### MS_IRVega - Interest Rate Vega

Vega sensitivities for interest rate optionality.

| Field | Type | Description |
|-------|------|-------------|
| `Bucket` | str | Currency |
| `CurveType` | str | Type of curve |
| `Curve` | str | Curve identifier (optional, needed for EU reporting) |
| `OptionMaturity` | str | Option maturity in years |
| `UnderlyingResidualMaturity` | str | Residual maturity of underlying in years |
| `Sensitivity` | float64 | Vega sensitivity value |

**Excel Example:**
| Sensitivity ID | Bucket | CurveType | OptionMaturity | UnderlyingResidualMaturity | Sensitivity |
|----------------|--------|-----------|----------------|---------------------------|-------------|
| MS_IRV_00000 | EUR | IR | 0.5 | 0.5 | 1000 |

---

### MS_IRCurvature - Interest Rate Curvature

Curvature risk for interest rate options.

| Field | Type | Description |
|-------|------|-------------|
| `Bucket` | str | Currency |
| `CVR+` | float64 | Curvature sensitivity value (upward shock) |
| `CVR-` | float64 | Curvature sensitivity value (downward shock) |

**Excel Example:**
| Sensitivity ID | Bucket | CVR+ | CVR- |
|----------------|--------|------|------|
| MS_IRC_00000 | EUR | 1000 | 1000 |

---

### MS_CRDelta - Credit Spread Delta (Non-Securitisation)

Delta sensitivities for credit spread risk.

| Field | Type | Description |
|-------|------|-------------|
| `Bucket` | str | Bucket number (1-18) based on sector/rating |
| `SubBucket` | str | Sub-bucket (if applicable) |
| `CreditName` | str | Name/identifier of the credit entity |
| `CurveType` | str | `BOND` or `CDS` |
| `Rating` | str | Credit rating (e.g., `AAA`, `AA`, `A`, `BBB`) |
| `Tenor` | str | Tenor: `0.5`, `1`, `3`, `5`, `10` |
| `Sensitivity` | float64 | Delta sensitivity value |

**Excel Example:**
| Sensitivity ID | Bucket | CreditName | CurveType | Rating | Tenor | Sensitivity |
|----------------|--------|------------|-----------|--------|-------|-------------|
| MS_CRD_00000 | 1 | Name_B1_N1 | BOND | AAA | 0.5 | 1000 |

---

### MS_CRVega - Credit Spread Vega (Non-Securitisation)

| Field | Type | Description |
|-------|------|-------------|
| `Bucket` | str | Bucket number |
| `SubBucket` | str | Sub-bucket (if applicable) |
| `CreditName` | str | Credit entity identifier |
| `Rating` | str | Credit rating (needed for EU reporting) |
| `OptionMaturity` | str | Option maturity |
| `Sensitivity` | float64 | Vega sensitivity value |

---

### MS_CRCurvature - Credit Spread Curvature (Non-Securitisation)

| Field | Type | Description |
|-------|------|-------------|
| `Bucket` | str | Bucket number |
| `SubBucket` | str | Sub-bucket |
| `CreditName` | str | Credit entity identifier |
| `Rating` | str | Credit rating (needed for EU reporting) |
| `CVR+` | float64 | Curvature sensitivity value (upward) |
| `CVR-` | float64 | Curvature sensitivity valuerisk (downward) |

---

### MS_CCDelta - Credit Spread Delta (Correlation/Securitisation Correlation)

Delta sensitivities for correlation trading portfolio.

| Field | Type | Description |
|-------|------|-------------|
| `Bucket` | str | Bucket number |
| `SubBucket` | str | Sub-bucket |
| `Underlier` | str | Underlying entity identifier |
| `CurveType` | str | `BOND` or `CDS` |
| `Tenor` | str | Tenor point |
| `Sensitivity` | float64 | Delta sensitivity value |

---

### MS_CCVega - Credit Spread Vega (Correlation)

| Field | Type | Description |
|-------|------|-------------|
| `Bucket` | str | Bucket number |
| `SubBucket` | str | Sub-bucket |
| `Underlier` | str | Underlying identifier |
| `OptionMaturity` | str | Option maturity |
| `Sensitivity` | float64 | Vega sensitivity |

---

### MS_CCCurvature - Credit Spread Curvature (Correlation)

| Field | Type | Description |
|-------|------|-------------|
| `Bucket` | str | Bucket number |
| `SubBucket` | str | Sub-bucket |
| `Underlier` | str | Underlying identifier |
| `CVR+` | float64 | Curvature sensitivity value (upward) |
| `CVR-` | float64 | Curvature sensitivity value (downward) |

---

### MS_CSDelta - Credit Spread Delta (Securitisation Non-Correlation)

Delta sensitivities for securitisation positions outside CTP.

| Field | Type | Description |
|-------|------|-------------|
| `Bucket` | str | Bucket number (1-25) |
| `SubBucket` | str | Sub-bucket |
| `Underlier` | str | Underlying identifier |
| `CurveType` | str | `BOND` or `CDS` |
| `Tenor` | str | Tenor point |
| `Sensitivity` | float64 | Delta sensitivity |

---

### MS_CSVega - Credit Spread Vega (Securitisation Non-Correlation)

| Field | Type | Description |
|-------|------|-------------|
| `Bucket` | str | Bucket number |
| `SubBucket` | str | Sub-bucket |
| `Underlier` | str | Underlying identifier |
| `OptionMaturity` | str | Option maturity |
| `Sensitivity` | float64 | Vega sensitivity |

---

### MS_CSCurvature - Credit Spread Curvature (Securitisation Non-Correlation)

| Field | Type | Description |
|-------|------|-------------|
| `Bucket` | str | Bucket number |
| `SubBucket` | str | Sub-bucket |
| `Underlier` | str | Underlying identifier |
| `CVR+` | float64 | Curvature sensitivity value (upward) |
| `CVR-` | float64 | Curvature sensitivity value (downward) |

---

### MS_EQDelta - Equity Delta

Delta sensitivities for equity risk.

| Field | Type | Description |
|-------|------|-------------|
| `Bucket` | str | Bucket number (1-13) based on market cap/economy |
| `SubBucket` | str | Sub-bucket |
| `EquityName` | str | Equity identifier |
| `SpotRepo` | str | `Spot` or `Repo` sensitivity type |
| `Sensitivity` | float64 | Delta sensitivity |

**Excel Example:**
| Sensitivity ID | Bucket | EquityName | SpotRepo | Sensitivity |
|----------------|--------|------------|----------|-------------|
| MS_EQD_00000 | 1 | Name_B1_N1 | Spot | 1000 |
| MS_EQD_00001 | 1 | Name_B1_N1 | Repo | 1000 |

---

### MS_EQVega - Equity Vega

| Field | Type | Description |
|-------|------|-------------|
| `Bucket` | str | Bucket number |
| `SubBucket` | str | Sub-bucket |
| `EquityName` | str | Equity identifier |
| `OptionMaturity` | str | Option maturity |
| `Sensitivity` | float64 | Vega sensitivity |

---

### MS_EQCurvature - Equity Curvature

| Field | Type | Description |
|-------|------|-------------|
| `Bucket` | str | Bucket number |
| `SubBucket` | str | Sub-bucket |
| `EquityName` | str | Equity identifier |
| `CVR+` | float64 | Curvature sensitivity value (upward) |
| `CVR-` | float64 | Curvature sensitivity value (downward) |

---

### MS_CMDelta - Commodity Delta

Delta sensitivities for commodity risk.

| Field | Type | Description |
|-------|------|-------------|
| `Bucket` | str | Bucket number (1-11) based on commodity type |
| `SubBucket` | str | Sub-bucket |
| `CommodityName` | str | Commodity identifier |
| `DeliveryLocation` | str | Delivery location for basis risk |
| `Tenor` | str | Tenor: `0`, `0.25`, `0.5`, `1`, `2`, `3`, `5`, `10`, `15`, `20`, `30` |
| `Sensitivity` | float64 | Delta sensitivity |

**Excel Example:**
| Sensitivity ID | Bucket | CommodityName | DeliveryLocation | Tenor | Sensitivity |
|----------------|--------|---------------|------------------|-------|-------------|
| MS_CMD_00000 | 1 | Name_B1_N1 | Loc_1 | 0.00 | 1000 |

---

### MS_CMVega - Commodity Vega

| Field | Type | Description |
|-------|------|-------------|
| `Bucket` | str | Bucket number |
| `SubBucket` | str | Sub-bucket |
| `CommodityName` | str | Commodity identifier |
| `OptionMaturity` | str | Option maturity |
| `Sensitivity` | float64 | Vega sensitivity |

---

### MS_CMCurvature - Commodity Curvature

| Field | Type | Description |
|-------|------|-------------|
| `Bucket` | str | Bucket number |
| `SubBucket` | str | Sub-bucket |
| `CommodityName` | str | Commodity identifier |
| `CVR+` | float64 | Curvature sensitivity value (upward) |
| `CVR-` | float64 | Curvature sensitivity value (downward) |

---

### MS_FXDelta - FX Delta

Delta sensitivities for foreign exchange risk.

| Field | Type | Description |
|-------|------|-------------|
| `Bucket` | str | Currency code (e.g., `EUR`, `JPY`) - sensitivity vs reporting currency |
| `Sensitivity` | float64 | Delta sensitivity |

**Excel Example:**
| Sensitivity ID | Bucket | Sensitivity |
|----------------|--------|-------------|
| MS_FXD_00000 | EUR | 1000 |
| MS_FXD_00001 | JPY | 1000 |

---

### MS_FXVega - FX Vega

| Field | Type | Description |
|-------|------|-------------|
| `Bucket` | str | Currency pair (e.g., `USDEUR`) |
| `OptionMaturity` | str | Option maturity |
| `Sensitivity` | float64 | Vega sensitivity |

**Excel Example:**
| Sensitivity ID | Bucket | OptionMaturity | Sensitivity |
|----------------|--------|----------------|-------------|
| MS_FXV_00000 | USDEUR | 0.5 | 1000 |

---

### MS_FXCurvature - FX Curvature

| Field | Type | Description |
|-------|------|-------------|
| `Bucket` | str | Currency code |
| `CVR+` | float64 | Curvature sensitivity value (upward) |
| `CVR-` | float64 | Curvature sensitivity value (downward) |

---

## Market Risk - Default Risk Charge (MD_*)

### MD_CR_DRC - Default Risk Charge (Non-Securitisation)

Jump-to-default risk for non-securitisation positions.

| Field | Type | Description |
|-------|------|-------------|
| `Bucket` | str | `Sovereign`, `Corporate`, `LocalGov_PSE` |
| `SubBucket` | str | `Cash` or `Derivative` |
| `Name` | str | Obligor name/identifier |
| `Seniority` | str | `SENIOR`, `SUBORDINATED`, `COVERED`, etc. |
| `Rating` | str | Credit rating |
| `MaturityDate` | str | Maturity date (YYYY-MM-DD format) |
| `JTD` | float64 | Jump-to-Default exposure |

**Excel Example:**
| Sensitivity ID | Bucket | SubBucket | Name | Seniority | Rating | MaturityDate | JTD |
|----------------|--------|-----------|------|-----------|--------|--------------|-----|
| MD_CR__00000 | Sovereign | Cash | Obligor_S_AAA | COVERED | AAA | 2024-05-13 | 1000 |

---

### MD_CC_DRC - Default Risk Charge (Correlation Trading Portfolio)

Jump-to-default risk for correlation trading positions.

| Field | Type | Description |
|-------|------|-------------|
| `Bucket` | str | Index name (e.g., `iTraxx Europe`, `CDX NA IG`) |
| `ExposureType` | str | `CDSIndex`, `CDSIndexTranche`, `SingleNameHedge`, `Bespoke` |
| `Series` | str | Index series number |
| `Tranche` | str | Tranche name (e.g., `[0%-3%[`) or obligor number |
| `MaturityDate` | str | Maturity date |
| `Rating` | object | Credit rating (can be None for index tranches) |
| `RiskWeight` | float64 | Risk weight (optional, for pre-calculated weights) |
| `JTD` | float64 | Jump-to-Default exposure |

**Excel Example:**
| Sensitivity ID | Bucket | ExposureType | Series | Tranche | MaturityDate | Rating | JTD |
|----------------|--------|--------------|--------|---------|--------------|--------|-----|
| MD_CC__00000 | iTraxx Europe | CDSIndexTranche | 33 | [0%-3%[ | 2024-05-13 | | 1000 |

---

### MD_CS_DRC - Default Risk Charge (Securitisation Non-CTP)

Jump-to-default risk for securitisation positions outside CTP.

| Field | Type | Description |
|-------|------|-------------|
| `Bucket` | str | Bucket number |
| `Issuer/Tranche` | str | Issuer or tranche identifier |
| `MaturityDate` | str | Maturity date |
| `Rating` | object | Credit rating (can be None) |
| `RiskWeight` | float64 | Risk weight |
| `JTD` | float64 | Jump-to-Default exposure |

**Excel Example:**
| Sensitivity ID | Bucket | Issuer/Tranche | MaturityDate | RiskWeight | JTD |
|----------------|--------|----------------|--------------|------------|-----|
| MD_CS__00000 | 1 | ISIN_1_AA | 2024-05-13 | 1.45 | 10000 |

---

## Market Risk - Residual Risk Add-On (MR_*)

### MR_RRAO - Residual Risk Add-On

Captures exotic and non-standard risks.

| Field | Type | Description |
|-------|------|-------------|
| `Bucket` | str | `Exotic` or `NonExotic` (instruments bearing Other Residual Risks) |
| `SubBucket` | str | Risk category (e.g., `FutureVol`, `Correlation`) |
| `NotionalAmount` | float64 | Notional amount |
| `NonExoticCategory` | str | Category for non-exotic instruments (optional) |

**Excel Example:**
| Sensitivity ID | Bucket | SubBucket | NotionalAmount | NonExoticCategory |
|----------------|--------|-----------|----------------|-------------------|
| MR_RRA_00000 | Exotic | FutureVol | 10000000 | |

---

## CVA Risk - Sensitivities Based Method (CS_*)

CVA (Credit Valuation Adjustment) risk sensitivities. These are similar to Market Risk sensitivities but include both portfolio sensitivity and hedge sensitivity.

### Common CVA Fields

All CVA sensitivity RiskClasses include:

| Field | Type | Description |
|-------|------|-------------|
| `Sensitivity` | float64 | CVA sensitivity from the portfolio |
| `HedgeSensitivity` | float64 | Sensitivity from eligible CVA hedges |

### CS_IRDelta - CVA Interest Rate Delta

| Field | Type | Description |
|-------|------|-------------|
| `Bucket` | str | Currency |
| `CurveType` | str | Curve type |
| `Tenor` | str | Tenor point |
| `Sensitivity` | float64 | Portfolio sensitivity |
| `HedgeSensitivity` | float64 | Hedge sensitivity |

**Excel Example:**
| Sensitivity ID | Bucket | CurveType | Tenor | Sensitivity | HedgeSensitivity |
|----------------|--------|-----------|-------|-------------|------------------|
| CS_IRD_00000 | SEK | IR | 1 | 1000 | 0 |
| CS_IRD_00001 | SEK | IR | 1 | 1000 | -800 |

---

### CS_IRVega - CVA Interest Rate Vega

| Field | Type | Description |
|-------|------|-------------|
| `Bucket` | str | Currency |
| `CurveType` | str | Curve type |
| `Sensitivity` | float64 | Portfolio sensitivity |
| `HedgeSensitivity` | float64 | Hedge sensitivity |

---

### CS_FXDelta - CVA FX Delta

| Field | Type | Description |
|-------|------|-------------|
| `Bucket` | str | Currency |
| `Sensitivity` | float64 | Portfolio sensitivity |
| `HedgeSensitivity` | float64 | Hedge sensitivity |

---

### CS_FXVega - CVA FX Vega

| Field | Type | Description |
|-------|------|-------------|
| `Bucket` | str | Currency pair |
| `Sensitivity` | float64 | Portfolio sensitivity |
| `HedgeSensitivity` | float64 | Hedge sensitivity |

---

### CS_CCDelta - CVA Counterparty Credit Spread Delta

Credit spread sensitivity to counterparty credit.

| Field | Type | Description |
|-------|------|-------------|
| `Bucket` | str | Sector bucket |
| `SubBucket` | str | Sub-bucket (e.g., `a`, `b`) |
| `CreditName` | str | Counterparty name |
| `ParentName` | str | Ultimate parent of counterparty |
| `IG_HYNR` | str | `IG` (Investment Grade), `HY` (High Yield), or `NR` (Not Rated) |
| `Tenor` | str | Tenor point |
| `Sensitivity` | float64 | Portfolio sensitivity |
| `HedgeSensitivity` | float64 | Hedge sensitivity |

**Excel Example:**
| Sensitivity ID | Bucket | SubBucket | CreditName | ParentName | IG_HYNR | Tenor | Sensitivity | HedgeSensitivity |
|----------------|--------|-----------|------------|------------|---------|-------|-------------|------------------|
| CS_CCD_00000 | 1 | a | Name_B_IG_1a_N1.1 | Parent_B_IG_1a_P1 | IG | 0.5 | 1000 | 0 |

---

### CS_CRDelta - CVA Reference Credit Spread Delta

| Field | Type | Description |
|-------|------|-------------|
| `Bucket` | str | Bucket number |
| `SubBucket` | str | Sub-bucket |
| `Sensitivity` | float64 | Portfolio sensitivity |
| `HedgeSensitivity` | float64 | Hedge sensitivity |

---

### CS_CRVega - CVA Reference Credit Spread Vega

| Field | Type | Description |
|-------|------|-------------|
| `Bucket` | str | Bucket number |
| `SubBucket` | str | Sub-bucket |
| `Sensitivity` | float64 | Portfolio sensitivity |
| `HedgeSensitivity` | float64 | Hedge sensitivity |

---

### CS_EQDelta - CVA Equity Delta

| Field | Type | Description |
|-------|------|-------------|
| `Bucket` | str | Bucket number |
| `SubBucket` | str | Sub-bucket |
| `Sensitivity` | float64 | Portfolio sensitivity |
| `HedgeSensitivity` | float64 | Hedge sensitivity |

---

### CS_EQVega - CVA Equity Vega

| Field | Type | Description |
|-------|------|-------------|
| `Bucket` | str | Bucket number |
| `SubBucket` | str | Sub-bucket |
| `Sensitivity` | float64 | Portfolio sensitivity |
| `HedgeSensitivity` | float64 | Hedge sensitivity |

---

### CS_CMDelta - CVA Commodity Delta

| Field | Type | Description |
|-------|------|-------------|
| `Bucket` | str | Bucket number |
| `SubBucket` | str | Sub-bucket |
| `Sensitivity` | float64 | Portfolio sensitivity |
| `HedgeSensitivity` | float64 | Hedge sensitivity |

---

### CS_CMVega - CVA Commodity Vega

| Field | Type | Description |
|-------|------|-------------|
| `Bucket` | str | Bucket number |
| `SubBucket` | str | Sub-bucket |
| `Sensitivity` | float64 | Portfolio sensitivity |
| `HedgeSensitivity` | float64 | Hedge sensitivity |

---

## CVA Risk - Basic Approach (CB_*)

### CB_REDUCED - Basic Approach CVA (Reduced Version)

Reduced version for banks without eligible hedges.

| Field | Type | Description |
|-------|------|-------------|
| `Sector` | str | Counterparty sector |
| `Region` | str | Counterparty region |
| `PositionType` | str | Always `Exposure` for reduced approach |
| `CreditName` | str | Counterparty name |
| `ParentName` | str | Ultimate parent of counterparty |
| `NettingSetMaturity` | float64 | Effective maturity in years |
| `EAD` | float64 | Exposure at Default |

---

### CB_FULL - Basic Approach CVA (Full Version)

Full version including eligible hedges.

| Field | Type | Description |
|-------|------|-------------|
| `Sector` | str | Counterparty sector |
| `Region` | str | Counterparty region |
| `PositionType` | str | `Exposure`, `Hedge`, or `IndexHedge` |
| `CounterpartyGroup` | str | Grouping for exposures and related hedges |
| `CreditName` | str | Counterparty or hedge underlier name |
| `ParentName` | str | Ultimate parent |
| `NettingSetMaturity` | float64 | Effective maturity in years |
| `EAD` | float64 | Exposure at Default or hedge notional |

---

## Unit Test Tabs

FNetF supports four types of unit test tabs for validation:

### Test Tab Types

| Tab Name | Purpose |
|----------|---------|
| `ObligorTests` | Tests at the obligor/entity level |
| `FactorTests` | Tests at the risk factor level |
| `BucketTests` | Tests at the bucket aggregation level |
| `CapitalTests` | Tests for full capital calculation |

### Common Test Columns

| Column | Type | Description |
|--------|------|-------------|
| `Test ID` | str | Unique test identifier |
| `RiskGroup` | str | Risk group for filtering |
| `RiskSubGroup` | str | Risk sub-group |
| `RiskClass` | str | Target RiskClass being tested |
| `Description` | str | Human-readable test description |
| `Sensitivity IDs` | str | Comma-separated list of sensitivity IDs or prefix patterns |

### Benchmark Columns

After the metadata columns, test tabs contain benchmark result columns:

| Column Pattern | Description |
|----------------|-------------|
| `Benchmark_SbAlt_Medium` | Alternative scenario - medium correlation |
| `Benchmark_SbAlt_Low` | Alternative scenario - low correlation |
| `Benchmark_SbAlt_High` | Alternative scenario - high correlation |
| `Benchmark_SumSb` | Sum of bucket-level results |
| `Benchmark_Medium` | Main result - medium correlation scenario |
| `Benchmark_Low` | Main result - low correlation scenario |
| `Benchmark_High` | Main result - high correlation scenario |

### Sensitivity IDs Syntax

The `Sensitivity IDs` field supports:

1. **Single ID:** `MS_IRD_00000`
2. **Multiple IDs:** `MS_IRD_00000, MS_IRD_00001, MS_IRD_00002`
3. **ALL prefix:** `ALL MS_IRD_` - includes all sensitivities starting with the prefix
4. **Mixed:** `MS_IRD_00000, ALL MS_IRD_001` - explicit IDs followed by prefix patterns

### Test Description Patterns

| Pattern | Description |
|---------|-------------|
| `Factor aggregation and weighting: ...` | Single factor weighting test |
| `Intra-bucket correlations: Bucket=X` | Within-bucket correlation test |
| `Bucket aggregation` | Full bucket aggregation (uses ALL prefix) |

### Excel Example - CapitalTests

| Test ID | RiskClass | Description | Sensitivity IDs | Benchmark_Medium |
|---------|-----------|-------------|-----------------|------------------|
| MS_IR_000000 | MS_IRDelta | Factor aggregation and weighting: Bucket=EUR, Tenor=0.25 | MS_IRD_00000 | 12.020815 |
| MS_IR_000037 | MS_IRDelta | Intra-bucket correlations: Bucket=EUR | MS_IRD_00000, MS_IRD_00001, ... | 156.789 |
| MS_IR_000043 | MS_IRDelta | Bucket aggregation | ALL MS_IRD_ | 1234.567 |

### JSON Example - _tests Structure

```json
{
  "_tests": {
    "CapitalTests": {
      "columns": [
        "Test ID",
        "RiskClass",
        "Description",
        "Sensitivity IDs",
        "RiskGroup",
        "RiskSubGroup",
        "Benchmark_SbAlt_Medium",
        "Benchmark_SbAlt_Low",
        "Benchmark_SbAlt_High",
        "Benchmark_SumSb",
        "Benchmark_Medium",
        "Benchmark_Low",
        "Benchmark_High"
      ],
      "data": [
        [
          "MS_IR_000000",
          "MS_IRDelta",
          "Factor aggregation and weighting: Bucket=EUR, CurveType=IR, Curve=IR_Curve_A, Tenor=0.25",
          "MS_IRD_00000",
          "UnitTests",
          "Main",
          0.0,
          0.0,
          0.0,
          12.020815,
          12.020815,
          12.020815,
          12.020815
        ]
      ]
    }
  }
}
```

---

## Data Type Reference

| Type | Description | JSON Representation |
|------|-------------|---------------------|
| `str` | String/text | `"value"` |
| `float64` | 64-bit floating point | `123.456` or `null` |
| `int64` | 64-bit integer | `123` |
| `bool` | Boolean | `true` or `false` |
| `object` | Nullable string | `"value"` or `null` |

---

## File Conversion

FNetF files can be converted between Excel and JSON using:

```python
from FNetF import FNetF

# Load from Excel
fnf = FNetF()
fnf.load('input.xlsx')

# Save as JSON
fnf.save('output.json')

# Or vice versa
fnf.load('input.json')
fnf.save('output.xlsx')
```

Or using the command-line converter:

```bash
python FNetFConverter.py input.xlsx -o output.json
python FNetFConverter.py input.json -o output.xlsx
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 3.0 | 2024 | Current version with JSON support |

---

*This documentation is part of the frtb.net FRTB calculation framework.*
