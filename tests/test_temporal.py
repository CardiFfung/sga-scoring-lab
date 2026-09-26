from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pandas as pd
import numpy as np
from sga_lab.data import load_data,build_features,FEATURES,validate,ROOT

def test_same_day_and_future_outcomes_cannot_change_pregame_features():
    g,t,s,_=load_data()
    original=build_features(g,t)
    cutoff=pd.Timestamp('2025-11-15')
    changed_g=g.copy();changed_t=t.copy()
    for col in ['pts','min','fga','fta']:
        changed_g.loc[changed_g.game_date.ge(cutoff),col]=9999
    for col in ['pts','min','fga','fta','oreb','tov']:
        changed_t.loc[changed_t.game_date.ge(cutoff),col]=9999
    changed=build_features(changed_g,changed_t)
    pd.testing.assert_frame_equal(original.loc[original.game_date.le(cutoff),FEATURES],changed.loc[changed.game_date.le(cutoff),FEATURES])

def test_phase_counts_and_shot_reconciliation():
    g,t,s,_=load_data();q=validate(g,t,s)
    assert q['regular_games']==448 and q['playoff_games']==55
    assert not g.query('season in ["2020-21","2021-22","2022-23"] and phase == "Playoffs"').shape[0]
    assert set(g[g.phase.eq('Regular Season')].game_id.str[:3])=={'002'}
    assert set(g[g.phase.eq('Playoffs')].game_id.str[:3])=={'004'}

def test_sources_strictly_precede_game_and_series_score_excludes_current():
    g,t,_,_=load_data();f=build_features(g,t)
    for c in ['history_date','team_history_date','opponent_history_date']:
        assert (f[c].isna()|f[c].lt(f.game_date)).all()
    p=f[f.phase.eq('Playoffs')]
    assert np.allclose(p.series_wins_before+p.series_losses_before,p.series_game-1)

def test_model_selection_uses_validation_not_final():
    p=pd.read_csv(ROOT/'tableau/data/predictions.csv')
    v=p.query('season == "2024-25" and phase == "Regular Season"')
    winner=v.groupby('model').absolute_error.mean().idxmin()
    final=p.query('season == "2025-26" and phase == "Regular Season" and selected')
    assert set(final.model)=={winner}
    assert (pd.to_datetime(p.train_end)<pd.to_datetime(p.game_date)).all()
    assert p[p.lower80.notna()].season.eq('2025-26').all()
    assert p[p.lower80.notna()].calibration_n.isin([76,23]).all()

def test_rates_are_ratios_of_totals():
    g,_,_,_=load_data();s=pd.read_csv(ROOT/'tableau/data/season_summary.csv')
    for row in s.itertuples():
        x=g[g.season.eq(row.season)&g.phase.eq(row.phase)]
        assert np.isclose(row.ts,x.pts.sum()/(2*(x.fga.sum()+.44*x.fta.sum())))
        assert np.isclose(row.two_ppg+row.three_ppg+row.ft_ppg,row.ppg)
