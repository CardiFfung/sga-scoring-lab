"""Descriptive outputs; denominators are recomputed from totals."""
import numpy as np
import pandas as pd

def summarize(df,keys):
    x=df.groupby(keys,observed=True).agg(games=('game_id','size'),points=('pts','sum'),minutes=('min','sum'),
        fgm=('fgm','sum'),fga=('fga','sum'),fg3m=('fg3m','sum'),fg3a=('fg3a','sum'),ftm=('ftm','sum'),fta=('fta','sum'),
        assists=('ast','sum'),rebounds=('reb','sum'),turnovers=('tov','sum'),stdev_points=('pts','std')).reset_index()
    x['ppg']=x.points/x.games;x['mpg']=x.minutes/x.games
    x['ts']=x.points/(2*(x.fga+.44*x.fta));x['efg']=(x.fgm+.5*x.fg3m)/x.fga
    x['points_per36']=36*x.points/x.minutes
    x['two_ppg']=2*(x.fgm-x.fg3m)/x.games;x['three_ppg']=3*x.fg3m/x.games;x['ft_ppg']=x.ftm/x.games
    x['fga_pg']=x.fga/x.games;x['fta_pg']=x.fta/x.games
    x['three_attempt_share']=x.fg3a/x.fga;x['fta_fga']=x.fta/x.fga
    x['fg_pct']=x.fgm/x.fga;x['fg3_pct']=x.fg3m/x.fg3a;x['ft_pct']=x.ftm/x.fta
    x['apg']=x.assists/x.games;x['rpg']=x.rebounds/x.games;x['tov_pg']=x.turnovers/x.games
    return x

def tables(games,shots):
    summary=summarize(games,['season','phase'])
    scoring=summary.melt(id_vars=['season','phase','games'],value_vars=['two_ppg','three_ppg','ft_ppg'],var_name='source',value_name='points_per_game')
    scoring['source']=scoring.source.map({'two_ppg':'Two-pointers','three_ppg':'Three-pointers','ft_ppg':'Free throws'})
    zone=shots.groupby(['season','phase','shot_zone_basic']).agg(attempts=('shot_attempted_flag','sum'),makes=('shot_made_flag','sum')).reset_index()
    zone['fg_pct']=zone.makes/zone.attempts
    zone['attempt_share']=zone.attempts/zone.groupby(['season','phase']).attempts.transform('sum')
    series=summarize(games[games.phase.eq('Playoffs')],['season','series_id','opponent','round_name'])
    regular=summary[summary.phase.eq('Regular Season')].set_index('season')
    playoff=summary[summary.phase.eq('Playoffs')].set_index('season')
    comparison=[]
    for season in playoff.index:
        for metric in ['ppg','mpg','points_per36','ts','fga_pg','fta_pg','apg','tov_pg']:
            comparison.append(dict(season=season,metric=metric,regular=float(regular.loc[season,metric]),playoffs=float(playoff.loc[season,metric]),
                difference=float(playoff.loc[season,metric]-regular.loc[season,metric]),regular_n=int(regular.loc[season,'games']),playoff_n=int(playoff.loc[season,'games'])))
    context=[]
    for dimension in ['venue','rest_group']:
        a=summarize(games,['season','phase',dimension]).rename(columns={dimension:'group'})
        a['dimension']=dimension;context.append(a)
    return {'season_summary':summary,'scoring_mix':scoring,'shot_zones':zone,'series_summary':series,
            'phase_comparison':pd.DataFrame(comparison),'context':pd.concat(context,ignore_index=True)}
