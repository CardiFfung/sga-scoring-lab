"""Frozen annual-origin models; all inputs are pregame, all fits are past-only."""
import json
import math
import numpy as np
import pandas as pd
from sklearn.pipeline import make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, brier_score_loss
from .data import FEATURES, ROOT

SPECS = {
    'Rolling10': {'type':'last 10 appearances mean'},
    'Ridge': {'alpha':100.0},
    'GradientBoosting': {'n_estimators':120,'max_depth':2,'min_samples_leaf':20,'learning_rate':0.03,'loss':'huber','random_state':42},
}

def estimator(name):
    if name == 'Ridge':
        return make_pipeline(SimpleImputer(strategy='median'),StandardScaler(),Ridge(**SPECS[name]))
    return make_pipeline(SimpleImputer(strategy='median'),GradientBoostingRegressor(**SPECS[name]))

def run_models(features):
    design = {'features':FEATURES,'candidates':SPECS,'validation':'2024-25','test':'2025-26',
              'origin':'one fit before each season; unchanged through that season playoffs',
              'transfer':'previous playoff residual mean shrunk by n/(n+10); no current-season adjustment',
              'selection':'minimum 2024-25 regular-season MAE; baseline eligible',
              'interval':'phase-specific 2024-25 absolute residuals, finite-sample 80% quantile',
              'seed':42}
    # This file is written before any candidate evaluation, and the final test cannot select a model.
    (ROOT/'reports').mkdir(exist_ok=True)
    (ROOT/'reports/design.json').write_text(json.dumps(design,indent=2))
    records=[]; fit_logs=[]
    for season in ['2022-23','2023-24','2024-25','2025-26']:
        train=features[(features.season<season)&features.phase.eq('Regular Season')&features.model_eligible]
        test=features[features.season.eq(season)&features.model_eligible]
        assert train.game_date.max()<test.game_date.min()
        for name in SPECS:
            if name=='Rolling10':
                prediction=test.pts_l10.to_numpy(float)
            else:
                model=estimator(name)
                model.fit(train[FEATURES],train.pts.astype(float))
                prediction=model.predict(test[FEATURES])
            out=test[['game_id','game_date','season','phase','opponent','venue','round_name','series_id','pts','pts_l10','min']].copy()
            out=out.rename(columns={'pts':'actual','min':'actual_minutes'})
            out['model']=name
            out['prediction']=np.maximum(prediction,0)
            out['train_end']=train.game_date.max()
            out['train_n']=len(train)
            out['transfer_offset']=0.0
            records.append(out)
            fit_logs.append({'season':season,'model':name,'n_train':len(train),'train_end':str(train.game_date.max().date()),'test_start':str(test.game_date.min().date())})
    pred=pd.concat(records,ignore_index=True)
    regular_validation=pred.query('season == "2024-25" and phase == "Regular Season"').groupby('model').apply(lambda x:mean_absolute_error(x.actual,x.prediction),include_groups=False)
    selected=regular_validation.idxmin()
    # A pre-specified, deliberately small transfer adjustment; final playoff outcomes never fit it.
    adjusted=[]
    for season in ['2023-24','2024-25','2025-26']:
        historical=pred[(pred.season<season)&pred.phase.eq('Playoffs')&pred.model.eq(selected)]
        offset=float((historical.actual-historical.prediction).sum()/(len(historical)+10))
        current=pred[pred.season.eq(season)&pred.phase.eq('Playoffs')&pred.model.eq(selected)].copy()
        current['model']='TransferAdjusted'
        current['prediction']=(current.prediction+offset).clip(lower=0)
        current['transfer_offset']=offset
        adjusted.append(current)
    pred=pd.concat([pred,*adjusted],ignore_index=True)
    val_po=pred.query('season == "2024-25" and phase == "Playoffs"')
    po_candidates=val_po[val_po.model.isin([selected,'TransferAdjusted'])].groupby('model').apply(lambda x:mean_absolute_error(x.actual,x.prediction),include_groups=False)
    selected_po=po_candidates.idxmin()
    pred['selected']=((pred.phase.eq('Regular Season')&pred.model.eq(selected))|(pred.phase.eq('Playoffs')&pred.model.eq(selected_po)))
    pred['split']=pred.season.map({'2022-23':'Development','2023-24':'Development','2024-25':'Validation','2025-26':'Final test'})
    pred['residual']=pred.actual-pred.prediction
    pred['absolute_error']=pred.residual.abs()
    pred['lower80']=np.nan;pred['upper80']=np.nan;pred['p30']=np.nan
    pred['calibration_n']=0
    calibration=[]
    for (name,phase),idx in pred[pred.season.eq('2025-26')].groupby(['model','phase']).groups.items():
        prior=pred[pred.season.eq('2024-25')&pred.model.eq(name)&pred.phase.eq(phase)].residual.to_numpy(float)
        if not len(prior):continue
        rank=min(len(prior),math.ceil((len(prior)+1)*.8))
        q=float(np.sort(np.abs(prior))[rank-1])
        point=pred.loc[idx,'prediction'].to_numpy(float)
        pred.loc[idx,'lower80']=np.maximum(0,point-q)
        pred.loc[idx,'upper80']=point+q
        pred.loc[idx,'p30']=[(np.sum(prior>=30-p)+.5)/(len(prior)+1) for p in point]
        pred.loc[idx,'calibration_n']=len(prior)
        calibration.append(dict(model=name,phase=phase,n=len(prior),absolute_residual_q80=q))
    scores=[]
    for (season,phase,name),df in pred.groupby(['season','phase','model']):
        interval=df.lower80.notna()
        scores.append(dict(season=season,phase=phase,model=name,n=len(df),
            mae=mean_absolute_error(df.actual,df.prediction),rmse=np.sqrt(mean_squared_error(df.actual,df.prediction)),
            bias=float((df.prediction-df.actual).mean()),selected=bool(df.selected.all()),
            coverage80=float(((df.actual>=df.lower80)&(df.actual<=df.upper80))[interval].mean()) if interval.any() else np.nan,
            width80=float((df.upper80-df.lower80)[interval].mean()) if interval.any() else np.nan,
            brier30=brier_score_loss(df.actual.ge(30),df.p30) if df.p30.notna().all() else np.nan))
    metadata={'selected_regular':selected,'selected_playoffs':selected_po,'validation_regular_mae':regular_validation.to_dict(),
              'validation_playoff_mae':po_candidates.to_dict(),'fits':fit_logs,'calibration':calibration,
              'probability_note':'Exploratory empirical residual probability, not independently tuned classification; playoff calibration n=23.'}
    return pred,pd.DataFrame(scores),metadata

def paired_uncertainty(pred):
    rows=[];rng=np.random.default_rng(42)
    for phase in ['Regular Season','Playoffs']:
        p=pred[pred.season.eq('2025-26')&pred.phase.eq(phase)]
        baseline=p[p.model.eq('Rolling10')].set_index('game_id')
        for name in p.model.unique():
            if name=='Rolling10':continue
            chosen=p[p.model.eq(name)].set_index('game_id').copy()
            chosen['delta']=chosen.absolute_error-baseline.absolute_error
            chosen['block']=chosen.series_id if phase=='Playoffs' else chosen.game_date.dt.to_period('W').astype(str)
            blocks=[v.delta.to_numpy() for _,v in chosen.groupby('block')]
            draws=[np.concatenate([blocks[i] for i in rng.integers(0,len(blocks),len(blocks))]).mean() for _ in range(2000)]
            low,high=np.quantile(draws,[.025,.975])
            rows.append(dict(phase=phase,model=name,selected=bool(chosen.selected.all()),mae_difference=chosen.delta.mean(),ci95_low=low,ci95_high=high,
                             blocks=len(blocks),note='Exploratory: only 3 series blocks' if phase=='Playoffs' else 'Paired weekly block bootstrap'))
    return pd.DataFrame(rows)
