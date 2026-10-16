# Forecast evaluation methods

I keep the target date fixed while moving the model's information cutoff to reflect assumed publication delays. Target-only models and multivariate models therefore forecast different numbers of steps to reach the same year-on-year target. Latest-vintage observations remain distinct from historical information sets.

Evaluation uses expanding training windows, unchanged model settings, common comparison dates, paired loss intervals and DM-HLN tests. German GDP nowcasts are reported both with and without the pandemic quarters; their q/q log-growth target is not annualised.

- [Initial design](DESIGN.md): sources, original monthly target and GDP availability assumptions.
- [Year-on-year target declaration](V2_TARGET.md): target and benchmark definitions.
- [Publication-delay protocol](V3_PROTOCOL.md): information cutoffs, seasonal benchmark and inference rules.
- [Provenance](PROVENANCE.md): final results, inherited estimates and rerun requirements.
- [Technical paper](../report/technical_report.pdf): implementation and results.

The protocols describe successive stages rather than interchangeable specifications. Fixed inference rules and assumed publication masks leave dependence and vintage uncertainty unresolved.
