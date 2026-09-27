# SGA Scoring Lab

Scoring trends, shot profiles and next-appearance scoring forecasts for Shai Gilgeous-Alexander.

Built to explore how SGA scores and how much recent form tells us about his next appearance. Covers **seven Oklahoma City seasons, 2019–20 to 2025–26**, with separate regular-season and playoff analysis, a Python forecasting pipeline and Tableau dashboards.

**Python · pandas · scikit-learn · Tableau · NBA Stats**

448 regular-season appearances · 55 playoff appearances · 9,580 shot attempts

[Tableau dashboards](#tableau-analysis) · [Analysis results](reports/RESULTS.md) · [Methodology](docs/METHODOLOGY.md)

## Key findings

- **Two-point scoring accounted for the largest share of the scoring increase.** Regular-season points per game rose from 19.0 to 31.1 between the first and last season. Two-pointers contributed approximately +6.9 points, free throws +3.8 and three-pointers +1.3.
- **Efficiency improved alongside volume.** Regular-season true shooting rose from 56.8% to 66.5%.
- **The latest playoff run had a different shot profile.** In 2025–26, midrange attempts made up a larger share of postseason shots, while midrange accuracy and overall scoring efficiency declined.
- **More complex models offered limited gains.** The rolling ten-game average won validation. Gradient Boosting performed slightly better on the final regular-season test, but the improvement was small and uncertain.

## 1. Scoring development

![Scoring components by season and true shooting by competition](reports/01_evolution.png)

The rise in scoring was not driven primarily by three-pointers. Two-point scoring grew by approximately **6.9 points per game**, while free throws added **3.8**.

This is a decomposition of scoring by point source. It does not separately attribute the increase to changes in shot volume and conversion rates.

Regular-season and playoff results retain separate denominators throughout. Seasons without a playoff appearance are missing observations, not zero-point seasons.

## 2. Regular season versus playoffs

![2025–26 regular-season and playoff shot locations](reports/04_shot_map.png)

In 2025–26:

- Midrange attempts accounted for **26.9%** of regular-season shots and **36.1%** of playoff shots.
- Midrange accuracy declined from **54.9% (195/355)** to **46.6% (48/103)**.
- Restricted-area attempts fell from **27.6%** to **20.0%** of all shots.
- Points per game declined from **31.1** to **27.6**, while true shooting declined from **66.5%** to **59.1%**.

The latest playoff shot profile shifted toward midrange attempts while efficiency declined. These are descriptive differences: the data do not isolate opponent defense, injuries or shot difficulty, and 15 playoff appearances do not establish a general playoff effect.

## 3. Next-appearance scoring forecasts

The target is SGA's points in his next appearance, **conditional on playing**.

Inputs include lagged scoring, minutes, attempts, efficiency, rest, venue and estimated team/opponent context. Actual minutes and outcomes from the game being predicted are excluded from prediction inputs.

### Evaluation setup

- **2019–20 to 2023–24 — historical training and development.** Build past-only features, with development evaluations in 2022–23 and 2023–24.
- **2024–25 — validation.** Select models and calibrate prediction intervals.
- **2025–26 — final retrospective test.** Evaluate the frozen selections on a later season.

Learned models are fitted once before each evaluation season using earlier regular-season games. Features update as games finish. Playoffs are evaluated separately, including a shrinkage adjustment estimated from earlier out-of-sample playoff errors.

### Model comparison

![Final-test model errors, with validation-selected models highlighted](reports/02_model_evidence.png)

Final-test mean absolute error (MAE), measured in points:

- **Last ten appearances:** 5.78 in the regular season; 7.01 in the playoffs. Selected on validation for regular-season forecasts.
- **Ridge regression:** 5.77 in the regular season; 6.59 in the playoffs.
- **Gradient Boosting:** 5.56 in the regular season; 6.51 in the playoffs.
- **Playoff transfer adjustment:** 7.06 in the playoffs. Selected on validation for playoff forecasts.

The final test includes 68 regular-season appearances and 15 playoff appearances.

Gradient Boosting improved regular-season test MAE by approximately **0.21 points** relative to the rolling baseline. However, the paired weekly-block bootstrap interval for that difference crossed zero. The result does not justify changing the selected model after seeing the test results.

The selected playoff adjustment failed to improve on the baseline in the final test.

### Forecast uncertainty

![Selected forecasts, observed points and nominal 80 percent intervals](reports/03_replay.png)

The selected regular-season forecast's nominal 80% intervals covered **85.3%** of final-test outcomes, with an average total width of **20.4 points**.

That width and the missed scoring outliers show why a point forecast alone understates game-level uncertainty. MAE describes average absolute error; it is not a guaranteed error bound.

## Tableau analysis

Four dashboards explore scoring development, playoff performance and forecast errors. Python prepares the analytical data and model outputs; Tableau provides visualization, filtering and standard aggregation.

The previews below are captured from the Tableau workbook and cropped to the dashboard area. Interactive filters and tooltips are available in the workbook.

### Regular season

Track points from two-pointers, three-pointers and free throws alongside true shooting percentage across seven Oklahoma City seasons.

A season filter on the shot-profile chart lets you inspect where his attempts came from. The preview shows the 2025–26 shot profile.

In the scoring stack, red represents two-pointers, orange three-pointers and blue free throws.

<img width="2733" height="1726" alt="SGA regular-season scoring dashboard" src="https://github.com/user-attachments/assets/9862f1c1-cf47-43e8-a74b-2fd40f8c5a99" />


### Playoffs

Inspect points per game by season and opponent, postseason scoring composition and shot locations.

The preview includes the 2025–26 playoff shot map. Scoring-source colors match the regular-season dashboard.

<img width="2733" height="1726" alt="SGA playoff scoring dashboard" src="https://github.com/user-attachments/assets/5cbfca44-42b9-4c5e-911e-9932b4830c7b" />

### Regular season vs. playoffs

Compare scoring volume and efficiency within the same season.

Orange represents the regular season; blue represents the playoffs. The lower-right chart shows playoff points per 36 minutes minus regular-season points per 36 minutes. Negative values indicate lower scoring per 36 minutes in the playoffs.

These comparisons describe observed differences rather than isolating the effects of opponents, injuries or shot difficulty.

<img width="2733" height="1726" alt="SGA regular-season versus playoff comparison" src="https://github.com/user-attachments/assets/0f901578-defb-427f-acc9-158d3137cfc8" />


### Predictions

Inspect model MAE, actual versus predicted points and errors over time. A competition filter separates regular-season and playoff results.

In the scatter plots, orange represents regular-season games and blue represents playoff games. Residuals are actual points minus predicted points, so positive values indicate that SGA outscored the forecast.

The workbook's “next game” heading refers to his next appearance, conditional on playing. Results are retrospective evaluations, not live pregame predictions.

<img width="2733" height="1726" alt="SGA scoring forecast evaluation dashboard" src="https://github.com/user-attachments/assets/f5bdd029-b6d5-487e-baf1-d1e692da064e" />

### Workbook details

The generated workbook contains four dashboards, twelve worksheets and an embedded Hyper extract. It includes eleven worksheet filter definitions and three dashboard filter controls, with no custom calculated fields or parameters.

The four analysis figures earlier in this README are generated with Matplotlib in `scripts/report.py`. The Tableau previews come from the workbook produced by `scripts/build_tableau.py`.

The generated workbook and extract are excluded from version control. Follow the reproduction steps below to generate `tableau/SGA_Scoring_Lab.twbx`.

[Workbook guide](docs/TABLEAU.md)

## Implementation notes

- **Data quality:** reconcile each game's shot attempts and makes against box scores; preserve source hashes and acquisition/import provenance.
- **Leakage prevention:** calculate features using strictly earlier dates; test that changing current or future outcomes cannot change forecast inputs.
- **Model selection:** benchmark learned models against recent form and select on validation.
- **Evaluation:** report failed playoff transfer, interval width, large misses and small-sample uncertainty alongside headline metrics.

[Full findings and error analysis](reports/RESULTS.md) · [Methodology](docs/METHODOLOGY.md) · [Model card](docs/MODEL_CARD.md)

## Repository structure

```text
sga_lab/             Data preparation, feature engineering and model evaluation
scripts/             Acquisition, analysis, figure and Tableau builders
reports/             Findings, figures, quality checks and model-run metadata
docs/                Methods, sources, data dictionary and model card
tests/               Temporal integrity and workbook checks
requirements.txt     Pinned Python dependencies
```

## Reproduce the analysis

Use Python 3.12. Run these commands from the repository root:

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python scripts/acquire.py
.venv/bin/python scripts/run.py
.venv/bin/python scripts/report.py
.venv/bin/python scripts/build_tableau.py
.venv/bin/python -m pytest -q
```

Raw responses, row-level datasets and generated Tableau files are excluded from version control. Acquisition requires access to NBA Stats; service availability and subsequent source revisions can affect reproduction. Existing raw files are reused, while derived outputs are rebuilt.

## Data and limitations

Source: NBA Stats player game logs, team game logs and shot charts. Coverage excludes play-in games.

[Source provenance and coverage](docs/SOURCES.md) · [Data dictionary](docs/DATA_DICTIONARY.md)

This is a retrospective evaluation using revised historical data, not a live forecasting service or an archived pregame feed.

Injury announcements, availability and minute restrictions are absent. Team pace and possessions are box-score estimates; per-36 statistics use rounded source minutes. Only three playoff series appear in the final test, and no causal or reliable playoff-improvement claim is made.

Code is MIT licensed; NBA source data have separate rights.
