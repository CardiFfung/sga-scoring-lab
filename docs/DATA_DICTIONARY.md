# Data dictionary

All CSV files are UTF-8. IDs are identifiers, not numeric measures. Date fields are ISO dates. Rates are proportions (0.665 means 66.5%), not percentage points.

| File | Grain | Key fields |
|---|---|---|
| games | One SGA appearance | game_id, game_date, season, phase, opponent, venue, pts, min, fgm/fga, fg3m/fg3a, ftm/fta, series_id, round_name |
| shots | One shot attempt | game_id + game_event_id; loc_x/loc_y in tenths of feet relative to basket; shot_zone_basic, shot_made_flag |
| season_summary | One season × phase | games, ppg, mpg, ts, efg, points_per36, two_ppg, three_ppg, ft_ppg |
| scoring_mix | One season × phase × scoring source | points_per_game; three mutually exclusive scoring components |
| shot_zones | One season × phase × zone | attempts, makes, fg_pct, attempt_share |
| series_summary | One playoff series | season, opponent, round_name, games, ppg, ts |
| phase_comparison | One season × metric | regular, playoffs, difference=playoffs−regular, both sample counts |
| context | One season × phase × dimension × group | dimension=venue/rest_group, games, ppg, efficiency |
| predictions | One game × model | prediction, actual, residual=actual−prediction, absolute_error, train_end, selected, split |
| model_scores | One season × phase × model | n, MAE, RMSE, bias=prediction−actual, coverage80, width80, brier30 |
| model_comparison | One final-test phase × candidate | paired MAE difference vs baseline, CI, block count |
| forecast_replay | One final-test game, validation-selected method | fixture, actual, prediction, lower80, upper80 |

## Model feature allowlist

- pts_l5/pts_l10: average points over previous 5/10 appearances, excluding current.
- pts_sd10: sample standard deviation over previous ten appearances.
- min_l10/fga_l10/fta_l10: previous-ten averages (source minutes rounded).
- ts_l10: ratio calculated from previous-ten totals.
- season_pts_prior: prior appearances this season; fallback pts_l10 on opening night.
- home: nominal home=1, away=0, 2020 bubble neutral=0.5.
- neutral_site: 2020 bubble indicator.
- rest_days: previous team game gap minus one, capped at 14.
- appearance_gap: days since previous SGA appearance, capped at 60.
- opp_drtg_prior10: opponent's previous-ten points allowed per 100 estimated possessions.
- opp_pace_prior10: opponent's previous-ten estimated pace.
- okc_ortg_prior10: OKC's previous-ten points scored per 100 estimated possessions.

`actual_minutes`, `actual`, box-score totals, series result and current-game metrics are descriptive/output fields, never predictors. `lower80/upper80/p30` are populated only for final test; blanks in development/validation mean not estimated, not zero. `calibration_n` records prior-season phase sample size.

Never average pre-aggregated percentages across seasons in Tableau. Default dashboards preserve the original season/phase grain. To pool data, recompute from totals. Series sample counts count SGA appearances, not necessarily every team fixture.
