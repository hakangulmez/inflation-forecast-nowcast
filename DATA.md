# Data, terms and lineage

Access date: 7 October 2026. Official runtime acquisition; raw observations, response files and row-level forecasts are private and ignored. Code licence does not license third-party data.

Eurostat: free data reuse with source acknowledgement and disclosure of transformations; https://ec.europa.eu/eurostat/help/copyright-notice. CBRT EVDS/TURKSTAT: research use with attribution; raw data are retained privately and not redistributed. Source conditions: https://evds2.tcmb.gov.tr/ and https://www.tcmb.gov.tr/wps/wcm/connect/en/tcmb+en/main+menu/terms+of+use. No FRED data are used in M2.

| Series | First observed | Last observed | Nonmissing |
| --- | --- | --- | --- |
| ea_headline | 1999-12 | 2026-09 | 322 |
| ea_core | 1999-12 | 2026-09 | 322 |
| ea_unemployment | 2000-01 | 2026-08 | 320 |
| de_gdp | 1999Q1 | 2026Q2 | 110 |
| ip | 1999-01 | 2026-07 | 331 |
| retail | 1999-01 | 2026-08 | 332 |
| unemployment | 1999-01 | 2026-08 | 332 |
| esi | 1999-01 | 2026-09 | 333 |
| tr_headline | 2005-01 | 2026-09 | 261 |
| tr_unemployment | 2005-01 | 2026-08 | 260 |

## Exact sources and SHA-256

- ea_headline: https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/prc_hicp_minr?lang=en&freq=M&unit=I25&coicop18=TOTAL&geo=EA21&sinceTimePeriod=1999-01&untilTimePeriod=2026-09 — accessed 2026-10-07; SHA-256 `a204db0502177eca6f892a42431801835fda82bddcedbe7f977f32aae088c822`; 19513 bytes.
- ea_core: https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/prc_hicp_minr?lang=en&freq=M&unit=I25&coicop18=TOT_X_NRG_FOOD&geo=EA21&sinceTimePeriod=1999-01&untilTimePeriod=2026-09 — accessed 2026-10-07; SHA-256 `8e49f519c8ea299c51b91b0f8f59e7c6fff7f78be0513523ccc1f9996c7ea8fb`; 21621 bytes.
- ea_unemployment: https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/une_rt_m?lang=en&freq=M&s_adj=SA&age=TOTAL&unit=PC_ACT&sex=T&geo=EA21&sinceTimePeriod=1999-01&untilTimePeriod=2026-09 — accessed 2026-10-07; SHA-256 `c490df5f56d15a52215849f59b214904216a1a17fbeee51f3c308e4f301b9cab`; 17998 bytes.
- de_gdp: https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/namq_10_gdp?lang=en&freq=Q&unit=CLV_I20&s_adj=SCA&na_item=B1GQ&geo=DE&sinceTimePeriod=1999-Q1&untilTimePeriod=2026-Q2 — accessed 2026-10-07; SHA-256 `b2409ece1a27921a6adb0f8f324d8fb45f168f4bfc61fea1ac2b752dc9b17d90`; 8200 bytes.
- ip: https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/sts_inpr_m?lang=en&freq=M&indic_bt=PRD&nace_r2=B-D&s_adj=SCA&unit=I21&geo=DE&sinceTimePeriod=1999-01&untilTimePeriod=2026-09 — accessed 2026-10-07; SHA-256 `189b25c72718ca545639a0d9354519fc1f18b7cee265207a78a4ddf218a50afa`; 18407 bytes.
- retail: https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/sts_trtu_m?lang=en&freq=M&indic_bt=VOL_SLS&nace_r2=G47&s_adj=SCA&unit=I21&geo=DE&sinceTimePeriod=1999-01&untilTimePeriod=2026-09 — accessed 2026-10-07; SHA-256 `d792b3b1ba3c697c89a15fec7079a898b9e8e1af391d6d779b3016859447bb15`; 21579 bytes.
- unemployment: https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/une_rt_m?lang=en&freq=M&s_adj=SA&age=TOTAL&unit=PC_ACT&sex=T&geo=DE&sinceTimePeriod=1999-01&untilTimePeriod=2026-09 — accessed 2026-10-07; SHA-256 `40ac8b20642c9f37cd2174ed524ad7b11af087938b331b28e0f32b4355a5b283`; 18100 bytes.
- esi: https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/ei_bssi_m_r2?lang=en&freq=M&s_adj=SA&indic=BS-ESI-I&geo=DE&sinceTimePeriod=1999-01&untilTimePeriod=2026-09 — accessed 2026-10-07; SHA-256 `479de0e3bfd8628d6db729041c8dc7a1c51db7a517c21705502f140f4858469f`; 18223 bytes.
- tr_headline: https://evds3.tcmb.gov.tr/igmevdsms-dis/series=TP.TUKFIY2025.GENEL&startDate=01-01-1999&endDate=30-09-2026&type=json — accessed 2026-10-07; SHA-256 `20afb9200c4e1e6b90bbff11d8fd88b8e69bb1366b46269fcddad874bb44cfe3`; 30925 bytes.
- tr_unemployment: https://evds3.tcmb.gov.tr/igmevdsms-dis/series=TP.TIG08&startDate=01-01-1999&endDate=30-09-2026&type=json — accessed 2026-10-07; SHA-256 `85beb3958df14c6acedea2b61e59a2a05b61a2c184172510b42cac4482761ef9`; 27184 bytes.

## Transformations and information

Headline/core prices and monthly IP/retail: 100×log change; quarterly GDP: 100×quarterly log change. EA/TR unemployment enters inflation forecasts in percent levels; DE unemployment enters the nowcast in monthly differences; ESI is a level. Reindex before differencing so missing months are never bridged. Source frequency and selectors are strict. EA21 membership/index base is the current vintage, not a historical fixed-composition reconstruction.

August 2026 DE IP is genuinely missing and stays missing. No interpolation. Fixed release masks and training-design means are estimator assumptions documented in DECISIONS.md; they do not overwrite source data. CPI/base history determines the actual common TR training start; actual coverage above is authoritative. Training and evaluation vintages are revised, not real time.

References verified against publisher/official pages: Harvey–Leybourne–Newbold (1997), https://doi.org/10.1016/S0169-2070(96)00719-4; Litterman (1986), https://doi.org/10.1080/07350015.1986.10509491; Banbura–Modugno (2014), https://doi.org/10.1002/jae.2306. DFM implementation: https://www.statsmodels.org/stable/generated/statsmodels.tsa.statespace.dynamic_factor_mq.DynamicFactorMQ.html.

Phillips-curve forecasting reference: Stock and Watson (1999), Forecasting Inflation, Journal of Monetary Economics 44(2), 293–335, DOI 10.1016/S0304-3932(99)00027-6. Independently verified against the author-hosted published article: https://www.princeton.edu/~mwatson/papers/Stock_Watson_JME_1999.pdf.


## Annual target and benchmark definitions

Primary point y/y target and the monthly Atkeson-Ohanian adaptation are defined exactly in docs/V2_TARGET.md. Source observations, model hyperparameters and nowcasts unchanged; original m/m table retained as secondary. DM-HLN evaluated against both RW and AO for h = 1, 3, 6 and 12. Overlap-induced serial dependence and multiple testing are explicit limitations. GDP units: 100 delta log(real GDP), q/q growth, not annualised. Primary forecast manifest is results/yoy_manifest.json; original results/manifest.json continues to bind secondary m/m and GDP results. Official AO study summary: https://www.minneapolisfed.org/article/2001/the-magics-gone .

Reference verification: Atkeson & Ohanian (2001), DOI: 10.21034/qr.2511, confirmed on the official Minneapolis Fed article page. This historical benchmark comparison is context; our monthly AO adaptation and loss-test limitations remain explicit.
