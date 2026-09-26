# SGA Scoring Lab — Results

1. Regular-season scoring rose from 19.0 to 31.1 PPG (+12.1). Two-pointers contributed 6.9, threes 1.3, and free throws 3.8 points of that change.

2. True shooting increased from 56.8% to 66.5%. This is an observed scoring-efficiency change, not a causal attribution.

3. In 2025–26, playoff scoring was 27.6 PPG versus 31.1 in the regular season; TS was 59.1% versus 66.5%. Playoff sample: 15 games.

4. The validation-selected regular-season forecast was Rolling10: final MAE 5.78 points, nominal 80% interval coverage 85.3%. Gradient Boosting achieved 5.56 MAE on the final test but was not selected by validation.

5. The playoff adjustment improved validation MAE but did not beat Rolling10 in the final 15 games: 7.06 versus 7.01 MAE. Three playoff series are too few for a strong generalization claim.

## How to interpret the findings

### Scoring growth: components and efficiency

![Scoring development](../reports/01_evolution.png)

The first and last regular seasons differ by about 12.1 points per appearance. Two-pointers account for approximately 6.9 of that increase, free throws 3.8 and three-pointers 1.3; rounded components need not sum exactly to the rounded total. This identifies where additional points were recorded. It does not establish whether development, usage, teammates or coaching caused the change.

True shooting combines field-goal scoring and free throws using PTS / [2 × (FGA + 0.44 × FTA)]. Its increase from 56.8% to 66.5% means scoring efficiency improved alongside scoring volume between these endpoints. It does not mean every intervening season improved monotonically.

### Playoff differences: a change in shot profile

| 2025–26 measure | Regular season | Playoffs |
| --- | ---: | ---: |
| Appearances | 68 | 15 |
| Points per game | 31.1 | 27.6 |
| True shooting | 66.5% | 59.1% |
| Midrange share of attempts | 26.9% | 36.1% |
| Midrange makes / attempts | 195 / 355 | 48 / 103 |
| Midrange accuracy | 54.9% | 46.6% |
| Restricted-area share of attempts | 27.6% | 20.0% |

The postseason sample contains a larger midrange share and a smaller restricted-area share. Midrange conversion also declined. Together these describe a different scoring environment, but do not show that playoff defense caused the decline: opponent mix, shot difficulty and availability are not controlled here. The comparison covers one postseason and should not be generalized to all playoff years.

### Forecasting: selection versus retrospective ranking

![Final-test model comparison](../reports/02_model_evidence.png)

The 2024–25 validation season selected the last-ten-appearance mean for regular-season forecasting. The learned models did not beat that baseline on the selection criterion. In the later 2025–26 test, Gradient Boosting achieved a lower MAE, but switching to it based on that result would use the test set for selection.

The regular-season Gradient Boosting-minus-baseline MAE difference was approximately −0.21 points. A paired weekly-block bootstrap interval was approximately [−0.58, +0.15], crossing zero. This experiment therefore does not establish a dependable improvement from the more complex model. It also does not prove that additional pregame information can never help.

The playoff adjustment was selected on earlier validation outcomes, but its final MAE was 7.06 versus 7.01 for the unadjusted baseline. Transfer did not improve this test. With only 15 games across three series, the sample cannot support strong claims about future playoff performance.

### Uncertainty and failure cases

![Historical prediction replay](../reports/03_replay.png)

Regular-season baseline intervals covered 85.3% of test observations against a nominal 80% target. Their average total width was 20.4 points, so useful evaluation must consider width as well as coverage. Coverage in this historical season is not a guarantee for future games.

The largest selected-model miss was 55 actual points against a prediction of 32.1. Recent-form forecasts remain near a player's typical production and can miss exceptional scoring nights. The table below identifies cases for diagnosis; without separate evidence, it cannot attribute misses to injuries, tactical changes or unexpected playing time.

### What the evidence supports next

A follow-up experiment could add genuinely archived pregame availability and expected-minute inputs, then compare them against the same baseline on a new time period. That would test an information improvement rather than simply increasing model complexity. The current project has not performed that experiment.


## Final-test model scores

| phase | model | n | mae | rmse | bias | coverage80 | width80 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Playoffs | GradientBoosting | 15 | 6.511 | 7.260 | 1.491 | 1.000 | 24.103 |
| Playoffs | Ridge | 15 | 6.587 | 7.451 | 1.554 | 0.933 | 25.238 |
| Playoffs | Rolling10 | 15 | 7.007 | 7.990 | 0.313 | 0.800 | 21.800 |
| Playoffs | TransferAdjusted | 15 | 7.063 | 8.068 | 1.164 | 0.933 | 26.260 |
| Regular Season | GradientBoosting | 68 | 5.562 | 7.290 | 0.258 | 0.794 | 18.513 |
| Regular Season | Ridge | 68 | 5.767 | 7.404 | 0.688 | 0.794 | 18.991 |
| Regular Season | Rolling10 | 68 | 5.776 | 7.383 | 0.203 | 0.853 | 20.400 |


## Interpretation limits

Current revised NBA snapshots, not archived pregame feeds. Conditional on participation; injuries and minutes restrictions absent. Possessions/pace are box-score estimates. Raw game-log minutes are rounded, so per-36 values are approximate. 2020 bubble venues are neutral. Calibration on the prior season does not guarantee future 80% coverage. P(30+) is exploratory. The final period was not used for model selection.

## Largest forecast misses

| Date | Phase | Opponent | Actual | Predicted | Absolute error |
| --- | --- | --- | ---: | ---: | ---: |
| 2025-10-23 | Regular Season | IND | 55 | 32.1 | 22.9 |
| 2026-03-30 | Regular Season | DET | 47 | 30.0 | 17.0 |
| 2026-01-07 | Regular Season | UTA | 46 | 29.3 | 16.7 |
| 2026-01-23 | Regular Season | IND | 47 | 31.4 | 15.6 |
| 2026-05-05 | Playoffs | LAL | 18 | 31.4 | 13.4 |
| 2026-02-03 | Regular Season | ORL | 20 | 32.7 | 12.7 |
| 2026-04-25 | Playoffs | PHX | 42 | 29.9 | 12.1 |
| 2026-05-28 | Playoffs | SAS | 15 | 26.9 | 11.9 |

Actual minutes are provided in the failure-cases table for diagnosis only; they were not available to the pregame model. No injury or tactical explanation is inferred without separate evidence.
