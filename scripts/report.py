"""Create GitHub-readable research findings and figures from computed outputs."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Arc,Rectangle,Circle

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports'
COLORS=['#167bb8','#ef773b','#159b89']

def main():
    s=pd.read_csv(ROOT/'tableau/data/season_summary.csv')
    p=pd.read_csv(ROOT/'tableau/data/predictions.csv')
    m=pd.read_csv(ROOT/'tableau/data/model_scores.csv')
    shots=pd.read_csv(ROOT/'tableau/data/shots.csv')
    meta=json.loads((OUT/'model_runs.json').read_text())
    plt.rcParams.update({'font.family':'DejaVu Sans','axes.spines.top':False,'axes.spines.right':False,'axes.titleweight':'bold','axes.labelcolor':'#42576b','text.color':'#122d43','axes.edgecolor':'#d8e1e9','figure.facecolor':'#ffffff','font.size':10})
    r=s[s.phase.eq('Regular Season')].set_index('season')
    fig,axs=plt.subplots(1,2,figsize=(13,5),layout='constrained')
    bottom=np.zeros(len(r))
    for c,label,color in zip(['two_ppg','three_ppg','ft_ppg'],['Two-pointers','Three-pointers','Free throws'],COLORS):
        axs[0].bar(r.index,r[c],bottom=bottom,label=label,color=color,width=.65);bottom+=r[c]
    axs[0].set(title='Where the points come from',ylabel='Points per game');axs[0].legend(frameon=False,fontsize=9);axs[0].tick_params(axis='x',rotation=30)
    for phase,color in zip(['Regular Season','Playoffs'],COLORS):
        x=s[s.phase.eq(phase)].set_index('season').reindex(r.index);axs[1].plot(r.index,100*x.ts,'o-',label=phase,color=color,lw=2)
    axs[1].set(title='Efficiency changes with the setting',ylabel='True shooting (%)');axs[1].legend(frameon=False);axs[1].tick_params(axis='x',rotation=30)
    fig.suptitle('SGA SCORING LAB  /  Seven seasons in Oklahoma City',fontsize=17,fontweight='bold')
    fig.savefig(OUT/'01_evolution.png',dpi=180);plt.close(fig)
    fig,axs=plt.subplots(1,2,figsize=(13,5),layout='constrained')
    for ax,phase in zip(axs,['Regular Season','Playoffs']):
        d=m[m.season.eq('2025-26')&m.phase.eq(phase)].sort_values('mae')
        ax.barh(d.model,d.mae,color=[COLORS[1] if v else COLORS[0] for v in d.selected]);ax.invert_yaxis()
        for i,row in enumerate(d.itertuples()):ax.text(row.mae+.08,i,f'{row.mae:.2f}',va='center')
        ax.set(title=f'{phase} | n={int(d.n.iloc[0])}',xlabel='Mean absolute error (points); lower is better',xlim=(0,9))
    fig.suptitle('2025–26 final test  /  Orange = selected using 2024–25 only',fontsize=16,fontweight='bold')
    fig.savefig(OUT/'02_model_evidence.png',dpi=180);plt.close(fig)
    fig,axs=plt.subplots(2,1,figsize=(13,8),layout='constrained')
    for ax,phase in zip(axs,['Regular Season','Playoffs']):
        d=p[p.season.eq('2025-26')&p.phase.eq(phase)&p.selected].sort_values('game_date');x=np.arange(1,len(d)+1)
        ax.fill_between(x,d.lower80,d.upper80,color=COLORS[0],alpha=.13,label='Nominal 80% prediction interval')
        ax.plot(x,d.prediction,color=COLORS[0],label='Pregame prediction',lw=1.8)
        ax.scatter(x,d.actual,color=COLORS[1],s=20,label='Actual points',zorder=3)
        ax.set(title=f'{phase} | {d.model.iloc[0]}',xlabel='Appearance number in final-test season',ylabel='Points')
        ax.legend(frameon=False,ncol=3,fontsize=9)
    fig.suptitle('Historical forecast replay  /  Conditional on SGA playing',fontsize=17,fontweight='bold')
    fig.savefig(OUT/'03_replay.png',dpi=180);plt.close(fig)
    fig,axs=plt.subplots(1,2,figsize=(11,6),layout='constrained')
    for ax,phase in zip(axs,['Regular Season','Playoffs']):
        d=shots[shots.season.eq('2025-26')&shots.phase.eq(phase)]
        for made,color in [(0,'#b8c5cf'),(1,COLORS[0])]:
            x=d[d.shot_made_flag.eq(made)];ax.scatter(x.loc_x/10,x.loc_y/10,s=10,alpha=.65,c=color,label='Made' if made else 'Missed')
        for patch in [Rectangle((-25,-5.25),50,47,fill=False),Rectangle((-8,-5.25),16,19,fill=False),Circle((0,0),.75,fill=False),Arc((0,0),47.5,47.5,theta1=22,theta2=158),Arc((0,13.75),12,12,theta1=0,theta2=180)]:
            patch.set_edgecolor('#536b7c');patch.set_linewidth(.8);ax.add_patch(patch)
        ax.plot([-22,-22],[-5.25,8.95],c='#536b7c',lw=.8);ax.plot([22,22],[-5.25,8.95],c='#536b7c',lw=.8)
        ax.set(xlim=(-26,26),ylim=(-6,42),aspect='equal',title=f'{phase} | {len(d):,} attempts');ax.axis('off');ax.legend(frameon=False,loc='upper right')
    fig.suptitle('2025–26 shot locations  /  Coordinates shown in feet',fontsize=16,fontweight='bold')
    fig.savefig(OUT/'04_shot_map.png',dpi=180);plt.close(fig)
    games=pd.read_csv(ROOT/'tableau/data/games.csv')
    fig,axs=plt.subplots(1,2,figsize=(13,5),layout='constrained')
    rs=games[games.phase.eq('Regular Season')]
    seasons=sorted(rs.season.unique())
    axs[0].boxplot([rs[rs.season.eq(y)].pts for y in seasons],tick_labels=seasons,patch_artist=True,boxprops={'facecolor':'#d9edf8'},medianprops={'color':COLORS[1],'linewidth':2})
    axs[0].set(title='Regular-season scoring distribution',ylabel='Points');axs[0].tick_params(axis='x',rotation=30)
    x=games[games.season.eq('2025-26')&games.phase.eq('Regular Season')]
    groups=['Back-to-back','1 day','2 days','3+ days']
    for i,label in enumerate(groups):
        values=x[x.rest_group.eq(label)].pts
        axs[1].scatter(np.full(len(values),i)+np.random.default_rng(42).uniform(-.13,.13,len(values)),values,alpha=.45,s=22,color=COLORS[0])
        axs[1].plot([i-.24,i+.24],[values.mean()]*2,color=COLORS[1],lw=3)
    axs[1].set(xticks=range(4),xticklabels=[f'{v}\n(n={int(x.rest_group.eq(v).sum())})' for v in groups],ylabel='Points',title='2025–26 rest context | orange = mean')
    fig.suptitle('Stability and context  /  Descriptive associations, not causal effects',fontsize=16,fontweight='bold')
    fig.savefig(OUT/'05_stability.png',dpi=180);plt.close(fig)
    last=r.loc['2025-26'];first=r.loc['2019-20'];play=s[(s.season=='2025-26')&(s.phase=='Playoffs')].iloc[0]
    delta=last.ppg-first.ppg
    regscore=m[(m.season=='2025-26')&(m.phase=='Regular Season')&m.selected].iloc[0]
    poscore=m[(m.season=='2025-26')&(m.phase=='Playoffs')&m.selected].iloc[0]
    facts=[f'Regular-season scoring rose from {first.ppg:.1f} to {last.ppg:.1f} PPG (+{delta:.1f}). Two-pointers contributed {last.two_ppg-first.two_ppg:.1f}, threes {last.three_ppg-first.three_ppg:.1f}, and free throws {last.ft_ppg-first.ft_ppg:.1f} points of that change.',
           f'True shooting increased from {first.ts:.1%} to {last.ts:.1%}. This is an observed scoring-efficiency change, not a causal attribution.',
           f'In 2025–26, playoff scoring was {play.ppg:.1f} PPG versus {last.ppg:.1f} in the regular season; TS was {play.ts:.1%} versus {last.ts:.1%}. Playoff sample: {int(play.games)} games.',
           f'The validation-selected regular-season forecast was {meta["selected_regular"]}: final MAE {regscore.mae:.2f} points, nominal 80% interval coverage {regscore.coverage80:.1%}. Gradient Boosting achieved 5.56 MAE on the final test but was not selected by validation.',
           f'The playoff adjustment improved validation MAE but did not beat Rolling10 in the final 15 games: {poscore.mae:.2f} versus 7.01 MAE. Three playoff series are too few for a strong generalization claim.']
    score_table=m[m.season.eq('2025-26')][['phase','model','n','mae','rmse','bias','coverage80','width80']]
    md='| '+' | '.join(score_table.columns)+' |\n| '+' | '.join(['---']*len(score_table.columns))+' |\n'
    for row in score_table.itertuples(index=False,name=None):md+='| '+' | '.join(f'{v:.3f}' if isinstance(v,float) else str(v) for v in row)+' |\n'
    text='# SGA Scoring Lab — Results\n\n'+'\n\n'.join(f'{i+1}. {x}' for i,x in enumerate(facts))+'\n\n## Final-test model scores\n\n'+md
    text+='\n\n## Interpretation limits\n\nCurrent revised NBA snapshots, not archived pregame feeds. Conditional on participation; injuries and minutes restrictions absent. Possessions/pace are box-score estimates. Raw game-log minutes are rounded, so per-36 values are approximate. 2020 bubble venues are neutral. Calibration on the prior season does not guarantee future 80% coverage. P(30+) is exploratory. The final period was not used for model selection.\n'
    failures=p[p.season.eq('2025-26')&p.selected].sort_values('absolute_error',ascending=False).head(8)
    failures[['game_date','phase','opponent','model','actual','prediction','actual_minutes','absolute_error']].to_csv(ROOT/'tableau/data/failure_cases.csv',index=False)
    text+='\n## Largest forecast misses\n\n| Date | Phase | Opponent | Actual | Predicted | Absolute error |\n| --- | --- | --- | ---: | ---: | ---: |\n'
    for row in failures.itertuples():text+=f'| {row.game_date[:10]} | {row.phase} | {row.opponent} | {row.actual:.0f} | {row.prediction:.1f} | {row.absolute_error:.1f} |\n'
    text+='\nActual minutes are provided in the failure-cases table for diagnosis only; they were not available to the pregame model. No injury or tactical explanation is inferred without separate evidence.\n'
    discussion=(ROOT/'docs/RESULTS_DISCUSSION.md').read_text()
    text=text.replace('## Final-test model scores', discussion+'\n\n## Final-test model scores')
    (OUT/'RESULTS.md').write_text(text)
    print('Created report and five figures')

if __name__=='__main__':main()
