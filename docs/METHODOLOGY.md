# Methodology

## Population and competition

SGA (NBA ID 1628983), Oklahoma City, seven seasons 2019–20 through 2025–26. Include only official regular-season game IDs beginning 002 and playoff IDs beginning 004. Exclude play-in, preseason and exhibitions. A missing playoff season means no appearances, not zero performance. The 2020 bubble is coded neutral, with home=0.5.

## Historical research

The unit is one appearance; percentages are ratios of summed numerators and denominators, not averages of game percentages. Points = 2(FGM−3PM)+3(3PM)+FTM. TS = PTS/[2(FGA+0.44FTA)], eFG=(FGM+0.5×3PM)/FGA. Each season/phase retains its sample count. Per-36 statistics use rounded source minutes and are approximate. No hypothesis claims that observed differences are causal. Context tables split by season and phase to avoid confounding early-career and recent games.

Shot data include every recorded attempt. Attempts and makes reconcile to each game box score. Full-court heaves remain in the data. The illustrative half-court plot clips attempts outside its 42-foot extent; zone totals include them. Tableau's coordinate plot contains all selected attempts and is a location scatter, not a heatmap or expected-shot-quality model.

## Team context

Join two team rows per game using stable IDs. Estimated possessions = 0.5×[(FGA+0.44FTA−OREB+TOV) + opponent equivalent]. Estimated pace = possessions×240 / total player minutes; this normalizes overtime. Off/def rating is 100×points / estimated possessions. Pregame last-10 rating is a ratio of last-10 sums, not an unweighted average of per-game ratings. These are project estimates, not official NBA advanced ratings.

## Information cutoff

Only source rows with dates strictly earlier than the target game date enter rolling features. Current-game minutes, attempts, points, result and series outcome never enter the feature allowlist. Assertions track latest player, own-team and opponent history dates. Mutating all same-day/future outcomes leaves earlier and current pregame features unchanged in the test suite.

Rolling player windows use preceding appearances (including earlier playoff appearances); rolling team windows use preceding team games. They carry across offseason and phase boundaries. Current-season prior points reset at the season boundary and fall back to rolling10 on opening night. Appearance gap is capped at 60 days; team rest, defined as days between team games minus one, is capped at 14. Neutral status and nominal venue are known before the game. Historical snapshots can contain subsequent statistical revisions; there is no archival pregame injury feed.

The first ten SGA appearances are descriptive-only warm-up, leaving 438 regular-season feature rows and 55 playoff rows. Opponent context missingness is filled using training-set medians inside the model pipeline; no test-set mean is used. Same-date joins and all target-derived features are prohibited.

## Model protocol

Fixed candidates: last-ten appearance mean; standardized Ridge alpha=100; Gradient Boosting 120 trees, depth=2, min leaf=20, learning rate=.03, Huber loss, seed=42. This deliberately limits complexity for a small single-player sample.

Annual origins: 2022–23 and 2023–24 development; 2024–25 validation; 2025–26 final test. Train each learned model once on earlier regular seasons and hold coefficients fixed through regular season and playoffs. Lagged features still update as games finish. Validation training has 294 appearances after warm-up; final training has 370. Baseline rolling10 does not fit model parameters. No current-season outcomes are used to fit the annual model.

Select the minimum 2024–25 regular-season MAE, including the simple baseline as a valid winner. Regular selection: Rolling10. For playoffs compare that selected base against a pre-specified additive adjustment: sum of earlier seasons' out-of-sample playoff residuals/(n+10). This shrinks the correction toward zero. Select between those two using 2024–25 playoffs; selection is TransferAdjusted. Freeze selections for the final season. The 2023–24 transfer check has no prior eligible playoff residuals, so its correction is zero; the final correction uses only 2023–24 and 2024–25 residuals.

This is annual-origin evaluation, not daily refitting. Final-test outcomes are reported for all candidates as an audit, not used to retrospectively choose the best one. The final-season descriptive outcomes were already known during project planning; this is a held-out retrospective experiment, not a prospective registered trial.

## Uncertainty and 30+ probabilities

For each model and phase, take absolute 2024–25 residuals (76 regular, 23 playoff). The 80% half-width is ordered residual number ceil[0.8(n+1)], clipped to n. Apply that fixed width to 2025–26 point forecasts; lower bounds are truncated at zero. Temporal dependence and distribution shift mean there is no unconditional 80% guarantee. Report achieved coverage and mean width separately by phase.

Exploratory P(30+) uses the empirical signed validation residual distribution with 0.5/1 smoothing. This assumes residual distribution stability and is not a separately optimized classifier. Brier scores are reported; no calibrated-probability claim is made, especially with 23 playoff calibration examples.

Paired MAE differences versus Rolling10 are resampled 2,000 times using weekly blocks for regular season and series blocks for playoffs. Seed=42. Only three final playoff series exist: that interval is exploratory, not strong inferential evidence. No multiple-comparison significance claim is made.

## Scope limits

No injury/availability model, live fixture forecasting, betting returns, causal treatment effects, raw optical tracking, fatigue measurements or defender-distance model. A training/preprocessing replay can reproduce this snapshot; it cannot reconstruct unpublished historical information.
