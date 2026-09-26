"""Run the complete local analysis after acquisition."""
from pathlib import Path
import sys,json
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from sga_lab.data import ROOT,load_data,validate,build_features
from sga_lab.model import run_models,paired_uncertainty
from sga_lab.research import tables

def main():
    for d in ['reports','data/processed','tableau/data']:(ROOT/d).mkdir(parents=True,exist_ok=True)
    games,teams,shots,coverage=load_data()
    quality=validate(games,teams,shots)
    features=build_features(games,teams)
    output=tables(features,shots)
    pred,scores,meta=run_models(features)
    output.update(predictions=pred,model_scores=scores,model_comparison=paired_uncertainty(pred),coverage=coverage,
                  games=features,shots=shots)
    for name,df in output.items():df.to_csv(ROOT/'tableau/data'/f'{name}.csv',index=False)
    features.to_parquet(ROOT/'data/processed/features.parquet',index=False)
    quality['feature_missingness']=features[__import__('sga_lab.data',fromlist=['FEATURES']).FEATURES].isna().sum().to_dict()
    quality['model_eligible']=int(features.model_eligible.sum())
    (ROOT/'reports/quality.json').write_text(json.dumps(quality,indent=2))
    (ROOT/'reports/model_runs.json').write_text(json.dumps(meta,indent=2))
    print(json.dumps(quality,indent=2))
    print(scores[scores.season.eq('2025-26')].to_string(index=False))

if __name__=='__main__':main()
