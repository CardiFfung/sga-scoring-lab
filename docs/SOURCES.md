# Sources and provenance

Underlying source: NBA Stats. NBA player ID 1628983, team ID 1610612760.

| Data | Endpoint | Coverage / verification |
|---|---|---|
| Player appearances | PlayerGameLog; extracted SGA rows from cached LeagueGameLog for five regular seasons | 448 regular + 55 playoffs; unique game IDs; phase prefixes checked |
| Team games | LeagueGameLog, PlayerOrTeam=T | 17,758 team rows; exactly two teams per game |
| Shot locations | ShotChartDetail, ContextMeasure=FGA | 9,580 attempts; per-game attempts and makes reconcile |

Documentation: [PlayerGameLog](https://github.com/swar/nba_api/blob/master/docs/nba_api/stats/endpoints/playergamelog.md), [LeagueGameLog](https://github.com/swar/nba_api/blob/master/docs/nba_api/stats/endpoints/leaguegamelog.md), [ShotChartDetail](https://github.com/swar/nba_api/blob/master/docs/nba_api/stats/endpoints/shotchartdetail.md), [NBA glossary](https://www.nba.com/stats/help/glossary).

All 42 season/phase/source files are present, including successful empty SGA/shot responses for seasons with no playoff appearances. Five regular-season player/team pairs were imported from a pre-existing local NBA response cache. Their original acquisition dates are recorded as unknown, not invented. Other responses were acquired through NBA endpoints for this project. Every input has a hash and source lineage in `data/raw/manifest.json`; imported player payloads are explicitly filtered to SGA. Only the raw cache was reused; models and SGA analysis were newly created.

`tableau/data/coverage.csv` contains exact per-file row counts. `reports/quality.json` records checks. Underlying official historical statistics may be revised after original publication.

The downloader does not overwrite existing cached files, does not require account credentials, and does not publish data. API availability and access conditions can change. Software licensing for nba_api is separate from NBA data reuse rights. See [NBA terms](https://www.nba.com/termsofuse) before public redistribution; public source packaging excludes data/extracts by default.
