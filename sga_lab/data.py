"""Load immutable source snapshots and construct strictly lagged features."""
from pathlib import Path
import json
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SEASONS = [f'{y}-{str(y+1)[-2:]}' for y in range(2019, 2026)]
FEATURES = ['pts_l5', 'pts_l10', 'pts_sd10', 'min_l10', 'fga_l10', 'fta_l10',
            'ts_l10', 'season_pts_prior', 'home', 'neutral_site', 'rest_days',
            'appearance_gap', 'opp_drtg_prior10', 'opp_pace_prior10', 'okc_ortg_prior10']

def read_response(path):
    d = json.loads(Path(path).read_text())
    r = d['resultSets'][0]
    return pd.DataFrame(r['rowSet'], columns=[c.lower() for c in r['headers']])

def load_data():
    collections = {'sga': [], 'team': [], 'shots': []}
    coverage = []
    for season in SEASONS:
        for suffix, phase in [('regular_season', 'Regular Season'), ('playoffs', 'Playoffs')]:
            for kind in collections:
                path = ROOT/'data/raw'/f'{season}_{kind}_{suffix}.json'
                if not path.exists():
                    raise FileNotFoundError(f'Required official response missing: {path.name}')
                df = read_response(path)
                df['season'] = season
                df['phase'] = phase
                if 'game_date' in df:
                    df['game_date'] = pd.to_datetime(df.game_date.astype(str), format='mixed')
                if 'game_id' in df:
                    df['game_id'] = df.game_id.astype(str).str.zfill(10)
                coverage.append(dict(season=season, phase=phase, source=kind, rows=len(df)))
                collections[kind].append(df)
    games, teams, shots = [pd.concat(collections[k], ignore_index=True) for k in ['sga','team','shots']]
    games = games.sort_values(['game_date','game_id']).reset_index(drop=True)
    teams = teams.sort_values(['game_date','game_id','team_id']).reset_index(drop=True)
    games['opponent'] = games.matchup.str[-3:]
    games['home'] = games.matchup.str.contains('vs. ', regex=False).astype(float)
    games['neutral_site'] = ((games.season == '2019-20') & (games.game_date >= '2020-07-30')).astype(int)
    games.loc[games.neutral_site.eq(1), 'home'] = 0.5
    games['two_pts'] = 2*(games.fgm-games.fg3m)
    games['three_pts'] = 3*games.fg3m
    games['free_throw_pts'] = games.ftm
    games['ts'] = games.pts / (2*(games.fga+.44*games.fta)).replace(0,np.nan)
    games['efg'] = (games.fgm+.5*games.fg3m)/games.fga.replace(0,np.nan)
    games['points_per36'] = 36*games.pts/games['min'].replace(0,np.nan)
    games['venue'] = np.where(games.neutral_site.eq(1),'Neutral', np.where(games.home.eq(1),'Home','Away'))
    games['series_id'] = np.where(games.phase.eq('Playoffs'), games.season+'_'+games.opponent, '')
    playoff = games.phase.eq('Playoffs')
    games['series_game'] = np.nan
    games.loc[playoff,'series_game'] = games[playoff].groupby('series_id').cumcount()+1
    rounds = games[playoff].groupby(['season','series_id']).game_date.min().groupby(level=0).rank().to_dict()
    games['round'] = [int(rounds[(r.season,r.series_id)]) if r.phase=='Playoffs' else 0 for r in games.itertuples()]
    games['round_name'] = games['round'].map({0:'Regular Season',1:'First Round',2:'Conference Semifinals',3:'Conference Finals',4:'NBA Finals'})
    games['series_wins_before'] = np.nan
    games['series_losses_before'] = np.nan
    for _, idx in games[playoff].groupby('series_id').groups.items():
        win = games.loc[idx,'wl'].eq('W').astype(int)
        games.loc[idx,'series_wins_before'] = win.cumsum()-win
        games.loc[idx,'series_losses_before'] = np.arange(len(idx))-(win.cumsum()-win)
    return games, teams, shots, pd.DataFrame(coverage)

def validate(games, teams, shots):
    assert not games.game_id.duplicated().any(), 'Duplicate SGA game'
    assert not teams.duplicated(['game_id','team_id']).any(), 'Duplicate team game'
    assert teams.groupby('game_id').size().eq(2).all(), 'Missing opponent rows'
    assert (games.two_pts+games.three_pts+games.free_throw_pts).eq(games.pts).all()
    assert set(games.player_id.unique()) == {1628983}
    assert games.game_id.str[:3].isin(['002','004']).all(), 'Unexpected competition (e.g. play-in)'
    assert not shots.duplicated(['game_id','game_event_id']).any()
    counts = shots.groupby('game_id').agg(shot_attempts=('shot_attempted_flag','sum'),shot_makes=('shot_made_flag','sum'))
    check = games.merge(counts, on='game_id',how='left',validate='one_to_one')
    assert check.shot_attempts.fillna(0).eq(check.fga).all(), 'Shot attempts do not reconcile'
    assert check.shot_makes.fillna(0).eq(check.fgm).all(), 'Shot makes do not reconcile'
    expected_regular = dict(zip(SEASONS,[70,35,56,68,75,76,68]))
    for season,n in expected_regular.items():
        assert len(games.query('season == @season and phase == "Regular Season"')) == n
    return {'sga_games':len(games),'regular_games':int(games.phase.eq('Regular Season').sum()),
            'playoff_games':int(games.phase.eq('Playoffs').sum()),'team_rows':len(teams),'shot_rows':len(shots),
            'unique_keys':True,'shots_reconcile_to_boxscores':True,'scoring_identity':True}

def build_features(games, teams):
    """Every rolling feature excludes the current row. Date assertions audit joins."""
    g = games.sort_values('game_date').copy()
    t = teams.sort_values(['game_date','game_id']).copy()
    opponent = t[['game_id','team_id','pts','fga','fta','oreb','tov']].rename(columns={c:'opp_'+c for c in ['team_id','pts','fga','fta','oreb','tov']})
    t = t.merge(opponent,on='game_id')
    t = t[t.team_id.ne(t.opp_team_id)].sort_values(['team_id','game_date']).copy()
    t['poss_est'] = .5*((t.fga+.44*t.fta-t.oreb+t.tov)+(t.opp_fga+.44*t.opp_fta-t.opp_oreb+t.opp_tov))
    # Team minutes represent total player minutes (240 regulation); include OT normalization.
    t['pace_est'] = t.poss_est*240/t['min']
    for c in ['pts','opp_pts','poss_est','pace_est']:
        t[c+'_prior10'] = t.groupby('team_id')[c].transform(lambda s:s.shift().rolling(10,min_periods=3).mean())
    t['ortg_prior10'] = 100*t.pts_prior10/t.poss_est_prior10
    t['drtg_prior10'] = 100*t.opp_pts_prior10/t.poss_est_prior10
    t['team_history_date'] = t.groupby('team_id').game_date.shift()
    t['rest_days'] = (t.game_date-t.team_history_date).dt.days.sub(1).clip(0,14)
    own = t[t.team_id.eq(1610612760)][['game_id','ortg_prior10','rest_days','team_history_date','opp_team_id','matchup']].rename(columns={'ortg_prior10':'okc_ortg_prior10','matchup':'team_matchup'})
    g = g.merge(own,on='game_id',how='left',validate='one_to_one')
    opp = t[['game_id','team_id','drtg_prior10','pace_est_prior10','team_history_date']].rename(columns={'team_id':'opp_team_id','drtg_prior10':'opp_drtg_prior10','pace_est_prior10':'opp_pace_prior10','team_history_date':'opponent_history_date'})
    g = g.merge(opp,on=['game_id','opp_team_id'],how='left',validate='one_to_one').sort_values('game_date').reset_index(drop=True)
    g['history_date'] = g.game_date.shift()
    g['history_count'] = np.arange(len(g))
    for c in ['pts','min','fga','fta']:
        g[c+'_l10'] = g[c].shift().rolling(10,min_periods=3).mean()
    g['pts_l5'] = g.pts.shift().rolling(5,min_periods=3).mean()
    g['pts_sd10'] = g.pts.shift().rolling(10,min_periods=3).std()
    g['ts_l10'] = g.pts_l10/(2*(g.fga_l10+.44*g.fta_l10))
    g['season_pts_prior'] = g.groupby('season').pts.transform(lambda s:s.shift().expanding().mean()).fillna(g.pts_l10)
    g['appearance_gap'] = (g.game_date-g.history_date).dt.days.clip(0,60)
    g['rest_group'] = pd.cut(g.rest_days,[-1,0,1,2,100],labels=['Back-to-back','1 day','2 days','3+ days']).astype(str)
    # Conflicting nominal venue labels are excluded from forecasting, retained for audit.
    g['venue_ambiguous'] = g.team_matchup.str.contains('vs. ',regex=False).ne(g.matchup.str.contains('vs. ',regex=False))
    g['model_eligible'] = g.history_count.ge(10)&g.pts_l10.notna()&g.opp_team_id.notna()&~g.venue_ambiguous
    for c in ['history_date','team_history_date','opponent_history_date']:
        assert (g[c].isna() | g[c].lt(g.game_date)).all(), f'Non-past source date: {c}'
    return g
