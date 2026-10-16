# Inflation forecasts with publication delays

Do more elaborate models improve on simple inflation benchmarks once publication delays are respected? I compare forecasts for the euro area and Türkiye and examine how pandemic quarters affect German GDP nowcast rankings.

![Inflation forecast and GDP nowcast comparisons](figures/headline.png)

## The evaluation I designed

I use expanding training windows and fixed model settings to forecast year-on-year inflation at 1, 3, 6 and 12 months. Prices are assumed to become available one month after their reference month and unemployment two months later. Models must forecast the extra steps between their available data and the same target date; changing the cutoff must not silently change the target.

The comparisons include random-walk and Atkeson–Ohanian-style benchmarks, AR, BVAR, Phillips, Lasso and ensemble forecasts. I report paired loss intervals and fixed-bandwidth DM-HLN tests. The German GDP exercise compares bridge, MIDAS and factor nowcasts under simulated release masks, with and without the pandemic quarters.

These are publication-delay simulations using latest-vintage observations. They do not reconstruct historical data releases or revisions.

## Results that changed the interpretation

- More elaborate models do not show a general accuracy gain over the random walk. EA core BVAR/RW RMSE is 1.077 (90% loss interval 0.999, 1.193); the EA headline ensemble/RW ratio is 1.071 (0.960, 1.167).
- At h = 12, Türkiye BVAR/RW RMSE is 2.389 and AR/RW is 1.950. The 2021–23 surge is consistent with difficult regime adaptation, but this comparison does not isolate its causal contribution.
- German month-3 DFM/bridge RMSE is 1.552 (0.778, 1.709) overall and 0.822 (0.702, 0.971) excluding 2020Q1–2021Q2. GDP is q/q log growth, not annualised.

Some factor fits did not converge. Fixed priors and learners can adapt poorly to regime changes, and the fixed loss-inference rules may leave serial dependence unaccounted for.

## Read or reproduce

[Technical working paper](report/technical_report.pdf) · [Policy note](report/policy_note.pdf) · [Detailed results](report/report.md) · [Methods guide](docs/METHODS.md)

Eurostat and CBRT/EVDS–TURKSTAT supply the observations. [DATA.md](DATA.md) lists selectors, transformations and source terms; raw series and row-level forecasts are not included.

For Python 3.11 and uv:

```sh
make setup
make test lint quick
```

The quick run uses synthetic data. [Provenance and reproduction](docs/PROVENANCE.md) covers the saved report inputs, empirical rerun requirements and the report commands that also regenerate presentation files, including this README.

Original code: [MIT](LICENSE). Data retain their source terms.

Hakan Zeki Gülmez · [Portfolio](https://hakangulmez.github.io/) · [GitHub](https://github.com/hakangulmez)
