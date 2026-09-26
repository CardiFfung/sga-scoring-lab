# Tableau workbook

Open `tableau/SGA_Scoring_Lab.twbx` using Tableau Public or Tableau Desktop. The package contains the workbook, a Hyper extract and its CSV sources; no Python server or account connection is required to inspect local data.

## Four dashboard tabs

1. **01 Regular Season:** scoring source stack, TS trend, shot-zone shares. The season dropdown controls the shot-profile chart only. Hover reveals attempts and accuracy.
2. **02 Playoffs:** scoring by series, postseason scoring source stack, shot-location scatter. The season dropdown controls the shot map only. No postseason in a year means no row, never zero.
3. **03 Compare Phases:** per-season phase comparisons in PPG and TS, and within-season playoff-minus-regular points per 36. Dots do not interpolate missing playoff seasons.
4. **04 Predictions:** final-test model MAE, selected-model forecast vs actual, and game-date errors. The phase dropdown controls the prediction scatter only. Hover for fixture and interval endpoints. Positive residual means actual exceeded forecast.

The workbook also includes 12 native worksheets. Source tables are named clearly and retain their grains. The context table provides season/phase rest and venue analyses for further exploration; it is not a separate headline dashboard in this first release.

## Refresh

Run acquisition only when new raw snapshots are intended. Then run `scripts/run.py`, `scripts/report.py`, and `scripts/build_tableau.py`. Tableau reads precomputed predictions; filtering does not retrain Python models. Save any manual workbook redesign under a different filename before rebuilding, since the builder replaces its generated workbook.

## Verification status

The Hyper build, ZIP integrity, XML references, four dashboard definitions, twelve worksheet definitions and three filter controls are checked programmatically. Five report PNGs were visually inspected.

The corrected workbook has loaded successfully in Tableau. Full visual inspection of all four dashboards and interactive filter behavior remains incomplete. Schema regression checks cover the previously reported extract attributes, formatting values, empty slices and categorical filters.

If the workbook cannot be opened, the validated CSVs remain in `tableau/data`, the Python pipeline is reproducible, and `README.md` and `reports/RESULTS.md` provide the plotted analysis directly on GitHub. The workbook has not been uploaded to Tableau Public.
