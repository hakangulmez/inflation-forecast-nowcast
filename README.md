# inflation-forecast-nowcast

Do fixed inflation models improve on simple benchmarks when we respect assumed publication delays, and how sensitive are German GDP nowcasts to pandemic quarters?

![Headline](figures/headline.png)

## Findings

- With publication delays, EA core BVAR/RW RMSE is 1.077 (90% loss interval 0.999, 1.193) and the EA headline ensemble/RW ratio is 1.071 (0.960, 1.167). These results do not support a general accuracy gain over the random walk.
- Türkiye deteriorates at h = 12: BVAR/RW RMSE is 2.389 and AR/RW is 1.950. The 2021-23 inflation surge is consistent with difficult regime adaptation, but this comparison does not identify its separate causal contribution.
- German GDP nowcasts are pandemic-sensitive: month-3 DFM/bridge RMSE is 1.552 (0.778, 1.709) overall and 0.822 (0.702, 0.971) excluding 2020Q1-2021Q2. GDP is q/q log growth, not annualised.

## Method

We forecast fixed year-on-year inflation targets at horizons of 1, 3, 6 and 12 months using expanding training windows and unchanged model settings. We assume final prices are published one month after their reference month and unemployment two months later, and forecast the extra steps from each effective data cutoff to the fixed target. We compare model errors against random-walk and Atkeson-Ohanian-style rules using paired loss intervals and fixed-bandwidth DM-HLN tests. We also compare bridge, MIDAS and factor nowcasts for German GDP under simulated release masks.

## Data sources

Eurostat supplies EA headline/core HICP, unemployment and German GDP/indicators; CBRT/EVDS-TURKSTAT supplies Türkiye prices and unemployment. [DATA.md](DATA.md) lists selectors, transformations and attribution. Scripts acquire observations at runtime; raw series and row-level forecasts are excluded.

## How to reproduce

Requirements: Python 3.11, uv and Tectonic. Dependencies install inside the repository.

```sh
make setup
make test lint quick
make policy-note report
```

The last command rebuilds the notes and working paper from included aggregate results, without data acquisition or model fitting. `make quick` is offline and synthetic. Empirical acquisition/rerun commands, required credentials and source-vintage constraints are documented in [provenance and reproduction](docs/PROVENANCE.md).

## Reports

[Two-page policy note](report/policy_note.pdf) · [Technical working paper](report/technical_report.pdf) · [Detailed results](report/report.md)

## Limitations

- Publication masks on latest-vintage data do not recreate historical vintages.
- The conservative unemployment delay reduces information for models using it.
- Fixed HAC and loss-bootstrap rules may leave dependence unaccounted for.
- Fixed learners and priors may adapt poorly to an inflation regime change.
- GDP rankings are pandemic-sensitive and some factor fits did not converge.

## Licence

Original code: [MIT](LICENSE). Third-party data retain their source terms and are not included.

Hakan Zeki Gülmez · [GitHub](https://github.com/hakangulmez) · [LinkedIn](https://www.linkedin.com/in/hakan-zeki-g%C3%BClmez-088700180/)
