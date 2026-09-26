"""Acquire official NBA responses with an explicit local-cache provenance trail."""
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import shutil
import time

ROOT = Path(__file__).resolve().parents[1]
SEASONS = [f'{y}-{str(y+1)[-2:]}' for y in range(2019, 2026)]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--offline', action='store_true')
    parser.add_argument('--limit', type=int, default=100)
    args = parser.parse_args()
    raw = ROOT / 'data/raw'
    raw.mkdir(parents=True, exist_ok=True)
    manifest_path = raw / 'manifest.json'
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    attempts = 0
    from nba_api.stats.endpoints import leaguegamelog, playergamelog, shotchartdetail
    for season in SEASONS:
        for phase, api_phase in [('regular_season', 'Regular Season'), ('playoffs', 'Playoffs')]:
            jobs = [('sga', playergamelog.PlayerGameLog, dict(player_id=1628983)),
                    ('team', leaguegamelog.LeagueGameLog, dict(player_or_team_abbreviation='T')),
                    ('shots', shotchartdetail.ShotChartDetail, dict(team_id=0, player_id=1628983, context_measure_simple='FGA'))]
            for kind, endpoint, params in jobs:
                name = f'{season}_{kind}_{phase}.json'
                path = raw/name
                if path.exists():
                    continue
                cached = ROOT.parent/'nba-star-impact-rebuild/data/raw'/f'{season}_{"player" if kind == "sga" else kind}_{phase}.json'
                stamp = dt.datetime.now(dt.timezone.utc).isoformat()
                if kind != 'shots' and cached.exists():
                    payload = json.loads(cached.read_text())
                    if kind == 'sga':
                        result = payload['resultSets'][0]
                        idx = result['headers'].index('PLAYER_ID')
                        result['rowSet'] = [r for r in result['rowSet'] if r[idx] == 1628983]
                    path.write_text(json.dumps(payload))
                    manifest[name] = {'origin': 'local NBA response cache', 'imported_at': stamp,
                        'parent_path': str(cached.relative_to(ROOT.parent)),
                        'parent_sha256': hashlib.sha256(cached.read_bytes()).hexdigest(), 'acquired_at': None,
                        'source': 'https://stats.nba.com/stats/leaguegamelog'}
                elif not args.offline and attempts < args.limit:
                    attempts += 1
                    request = dict(params, season_type_all_star=api_phase, timeout=20)
                    request['season_nullable' if kind == 'shots' else 'season'] = season
                    try:
                        payload = endpoint(**request).get_json()
                        parsed = json.loads(payload)
                        assert 'resultSets' in parsed
                        path.write_text(payload)
                        manifest[name] = {'origin': 'live NBA endpoint', 'acquired_at': stamp,
                            'source': 'https://stats.nba.com/stats/'+endpoint.__name__.lower(), 'parameters': request}
                        print('Downloaded', name, flush=True)
                    except Exception as error:
                        manifest[name] = {'status': 'unavailable', 'attempted_at': stamp, 'error': str(error)[:300]}
                        print('Unavailable', name, str(error)[:100], flush=True)
                    time.sleep(1)
                if path.exists():
                    manifest[name]['sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
                    manifest[name]['status'] = 'available'
                manifest_path.write_text(json.dumps(manifest, indent=2))

if __name__ == '__main__':
    main()
