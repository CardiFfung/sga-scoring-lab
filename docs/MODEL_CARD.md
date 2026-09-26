# Model card

**Purpose:** a retrospective analysis of one player's scoring, with conditional pregame point forecasts.

**Target:** points in an appearance. **Population:** SGA at OKC, regular season and playoffs reported separately. **Not covered:** DNP prediction, injuries, live lineups, minute restrictions, real-time scores or betting decisions.

**Selection:** 2024–25 MAE selects Rolling10 for regular season, and a shrunk residual adjustment to that baseline for playoffs. Learned candidates are Ridge and Gradient Boosting; final-test scores do not change the selected methods.

**Final test:** 2025–26, 68 regular appearances and 15 playoff appearances. Selected methods MAE: 5.776 and 7.063 points respectively. Regular interval coverage 85.3% with width 20.4 points; playoff coverage 93.3% with width 26.26 points. These wide intervals are a material uncertainty result, not precise forecasts.

**Limitations:** single-player sample, changing career role, rounded minutes, estimated team possessions, possible retrospective statistical revisions, dependent repeated-opponent playoff observations, no historical availability feed. Only 23 playoff observations calibrate the final prediction interval and exploratory 30+ probability.

**Update policy:** new data may refresh lagged features; new model development requires a new validation period. Do not tune on 2025–26 and continue labeling it an untouched test. The next future season can provide a prospective evaluation after freezing the whole pipeline.
