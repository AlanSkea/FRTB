Vision and Overview
===
Our vision is to create a network of Market Risk and CVA practitioners around a free, open-source implementation of the Standardised Approach Basel III Market Risk Capital rules (aka FRTB).  Our calculators also encompass the Basel III CVA Standardised Approach and the Basel III CVA Basic Approach.  The calculators are flexible and can be configured for a variety of regional variations to the rules.

Based on these core calculators we have also developed some tools for completing regulatory reports, for drill-down and analysis of and explaining the capital charges and a rigorous and comprehensive testing framework.  These are available separately - see below or [contact us](mailto:info@frtb.net).

---
License
===
This program is free software: you can redistribute it and/or modify it under the terms of the GNU Affero General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License along with this program.  If not, see <https://www.gnu.org/licenses/>.
___


Core Calculators
===
The core calculators take as inputs the sensitivities produced by an institution's own pricing and valuation tools and the calculators apply the rules for the relevant jurisdiction to compute the capital requirement.  Sensitivities are expected in an FNet Format file (FNetF).

There is also code to convert ISDA CRIF format files to FNetF files and vice versa.

There are four calculator modules:
* **SA_SBM_Calc.py** : Implements the Market Risk SBM method and the CVA Standardised approach method.  All risk classes are included.
* **SA_DRC_Calc.py** : Implements calculators for the Market Risk Default Risk Charge (for non-securitisations, securitisations not in the correlation trading portfolio and securitisations that are in the correlation trading portfolio)
* **SA_RRAO_Clac.py** : Implements the calculator for the Residual Risk Add-On.
* **BA_CVA_Calc.py** : Implements the CVA Basic Approach calculators.  Either the Reduced or the Full calculation can be used.

Configs
===
Variations between jurisdictions are captured in the configuration spreadsheets in the Configs folder.  A very small amount of code is needed to support more complex regional peculiarities such as the ERM-II currencies in Europe, but mostly the variations are bucketing and correlation differences and are in the configurations.  It should be straightforward to add configurations for new jurisdictions and we welcome contributions.

We currently have configurations for [Basel](https://www.bis.org/basel_framework/standard/MAR), UK-PRA [1](https://www.bankofengland.co.uk/prudential-regulation/publication/2023/december/implementation-of-the-basel-3-1-standards-near-final-policy-statement-part-1), [2](https://www.bankofengland.co.uk/prudential-regulation/publication/2024/september/implementation-of-the-basel-3-1-standards-near-final-policy-statement-part-2) and [EU-EBA](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A02013R0575-20240709) [amended](https://data.consilium.europa.eu/doc/document/ST-15883-2023-INIT/en/pdf) rules.

Examples
===
Some examples of use are in the Examples folder.
* **UnitTests_BCBS_FNetF_v0.3.xlsx** is a spreadsheet in FNetF format containing input sensitivities and resulting capital for a set of portfolios constructed from those sensitivities.
* **RunUnitTests.py** uses the core calculators to compute the capital for each of the test portfolios and compares the result to the benchmark result given in the input spreadsheet.  Given that the input spreadsheet was generated using the same calculators, the results should all match.  This is useful as a regression test when making changes to the core calculators.
* **approach-for-credit-valuation-adjustment-risk-sacva-data-template.xlsx** : this is a spreadsheet downloaded form the PRA website that needs to be completed and submitted as part if any application to use the CVA Standardised Approach.
* **Convert_PRA_CVA_Template.py** : this converts the PRA spreadsheet above into an FNetF format file that can be used by the frtb.net core calculators to compute the requested results.
* **RunPRA_CVA.py** uses the generated FNetF file and the core calculators to compute the results for the data template.

Extensions
===
Available separately and under different license, we can also provide the following:
* **Regulatory report completion** : tools that can fill in the detailed information required on the UK-PRA and EU-EBA report templates for Market Risk Standardised Approach and CVA Standardised and Basic Approaches.
* **Drill-down, analysis and explain** : By examining the top contributors to the capital charge we can drill into the internals of the calculations and explain how these arise, working back to which sensitivity inputs are driving the charges.  This can be done for a single date or to examine the change in capital charge between two dates.
* **Comprehensive testing** : Based on the regional configurations and some additions test configurations we have built a framework that will automatically generate a comprehensive set of unit tests for the capital calculators.  These are useful for regression testing changes to our own calculators and also for helping validate in-house implementations.  We currently generate more than 5000 different tests.  In addition to the basic tests that apply to all jurisdictions, we also include tests selected to exercise the specific variations for regions and check that they are correctly applied in the relevant jurisdiction but not in others.

Contact
===
Contact us at <info@frtb.net> or on +44 20 3422 8888.

---
Copyright © 2024 frtb.net limited

