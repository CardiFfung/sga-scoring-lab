"""Build four native Tableau dashboards, a Hyper extract, and a portable TWBX.

Data-source XML structure follows the local, previously opened Tableau workbook.
This file contains all construction logic; no sibling project is required to run it.
"""
from pathlib import Path
import copy
import json
import zipfile
import shutil
import xml.etree.ElementTree as E
import pandas as pd
from tableauhyperapi import HyperProcess,Telemetry,Connection,CreateMode,TableDefinition,TableName,SqlType,Inserter

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'tableau'

def sub(parent,tag,text=None,**attrs):
    e=E.SubElement(parent,tag,{k.replace('_','-'):str(v) for k,v in attrs.items()})
    if text is not None:e.text=str(text)
    return e

def build():
    sources={n:pd.read_csv(OUT/'data'/f'{n}.csv') for n in ['season_summary','scoring_mix','shot_zones','series_summary','phase_comparison','model_scores','predictions','context','games']}
    sources['forecast_replay']=sources['predictions'].query('season == "2025-26" and selected').copy()
    sources['forecast_replay']['fixture']=sources['forecast_replay'].game_date.str[:10]+' | '+sources['forecast_replay'].opponent
    sources['forecast_replay'].to_csv(OUT/'data/forecast_replay.csv',index=False)
    shot=pd.read_csv(OUT/'data/shots.csv')
    sources['shot_map']=shot[['season','phase','game_id','game_event_id','shot_zone_basic','loc_x','loc_y','shot_made_flag']].copy()
    sources['shot_map']['result']=sources['shot_map'].shot_made_flag.map({0:'Missed',1:'Made'})
    sources['shot_map']['shot_id']=sources['shot_map'].game_id.astype(str)+'_'+sources['shot_map'].game_event_id.astype(str)
    sources['shot_map'].to_csv(OUT/'data/shot_map.csv',index=False)
    for n in ['season_summary','scoring_mix','shot_zones','series_summary','phase_comparison','model_scores','context']:
        sources[n].to_csv(OUT/'data'/f'{n}.csv',index=False)
    types={};hyper=OUT/'sga.hyper'
    with HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as process:
        with Connection(process.endpoint,str(hyper),CreateMode.CREATE_AND_REPLACE) as conn:
            conn.catalog.create_schema('Extract')
            for name,df in sources.items():
                types[name]={c:'real' if pd.api.types.is_numeric_dtype(df[c]) and c not in ['game_id','player_id','game_event_id','team_id'] else 'string' for c in df}
                table=TableDefinition(TableName('Extract',name),[TableDefinition.Column(c,SqlType.double() if t=='real' else SqlType.text()) for c,t in types[name].items()])
                conn.catalog.create_table(table)
                rows=[[None if pd.isna(v) else float(v) if types[name][c]=='real' else str(v) for c,v in zip(df.columns,r)] for r in df.itertuples(index=False,name=None)]
                with Inserter(conn,table) as ins:ins.add_rows(rows);ins.execute()
    wb=E.Element('workbook',{'original-version':'18.1','source-build':'2024.1.0 (20241.24.0202.1234)','source-platform':'mac','version':'18.1','xmlns:user':'http://www.tableausoftware.com/xml/user'})
    manifest=sub(wb,'document-format-change-manifest')
    for flag in ['ObjectModelEncapsulateLegacy','ObjectModelExtractV2','ObjectModelTableType','SchemaViewerObjectModel']:sub(manifest,flag)
    datasources=sub(wb,'datasources')
    for name,df in sources.items():
        ds=sub(datasources,'datasource',caption=name.replace('_',' ').title(),inline='true',name=name,version='18.1')
        connection=sub(ds,'connection',**{'class':'federated'})
        nc=sub(sub(connection,'named-connections'),'named-connection',caption=name,name='textscan.'+name)
        sub(nc,'connection',**{'class':'textscan','directory':'data','filename':name+'.csv','password':'','server':''})
        relation=sub(connection,'relation',connection='textscan.'+name,name=name+'.csv',table=f'[{name}#csv]',type='table')
        cols=sub(relation,'columns',character_set='UTF-8',header='yes',locale='en_US',separator=',')
        for i,(c,t) in enumerate(types[name].items()):sub(cols,'column',datatype=t,name=c,ordinal=i)
        def metadata(parent,table):
            records=sub(parent,'metadata-records')
            for i,(c,t) in enumerate(types[name].items()):
                rec=sub(records,'metadata-record',**{'class':'column'})
                for tag,value in [('remote-name',c),('remote-type',5 if t=='real' else 129),('local-name',f'[{c}]'),('parent-name',f'[{table}]'),('remote-alias',c),('ordinal',i),('local-type',t),('aggregation','Sum' if t=='real' else 'Count'),('contains-null','true'),('object-id',f'[{name}_table]')]:sub(rec,tag,value)
        metadata(connection,name+'.csv')
        sub(ds,'aliases',enabled='yes')
        for c,t in types[name].items():
            col=sub(ds,'column',caption=c.replace('_',' ').title(),datatype=t,name=f'[{c}]',role='measure' if t=='real' else 'dimension',type='quantitative' if t=='real' else 'nominal')
            if t=='real':col.set('default-format','p0.0%' if c in ['ts','efg','fg_pct','attempt_share','coverage80','p30','fg3_pct','ft_pct'] else 'n0.0')
        ex=sub(ds,'extract',count='-1',enabled='true',object_id='',units='records')
        ec=sub(ex,'connection',**{'class':'hyper','dbname':'sga.hyper','schema':'Extract','tablename':name,'default-settings':'hyper','username':'tableau_internal_user','sslmode':''})
        ec.set('access_mode','readonly')
        er=sub(ec,'relation',name=name,table=f'[Extract].[{name}]',type='table')
        metadata(ec,name)
        objects=sub(sub(ds,'object-graph'),'objects');obj=sub(objects,'object',caption=name+'.csv',id=name+'_table')
        sub(obj,'properties',context='').append(copy.deepcopy(relation));sub(obj,'properties',context='extract').append(copy.deepcopy(er))
    worksheets=sub(wb,'worksheets');sheet_meta={}

    def sheet(name,source,rows,cols,mark='Bar',color=None,detail=(),filters=None):
        filters=filters or {};sheet_meta[name]=(source,filters)
        sh=sub(worksheets,'worksheet',name=name)
        ft=sub(sub(sub(sh,'layout-options'),'title'),'formatted-text');sub(ft,'run',name,fontname='Tableau Book',fontsize='13',bold='true',fontcolor='#122f46')
        table=sub(sh,'table');view=sub(table,'view');sub(sub(view,'datasources'),'datasource',caption=source.replace('_',' ').title(),name=source)
        dep=sub(view,'datasource-dependencies',datasource=source);refs={}
        fields=set(rows+cols+([color] if color else [])+list(detail)+list(filters))
        for c in sorted(fields):
            dtype=types[source][c];num=dtype=='real'
            sub(dep,'column',caption=c.replace('_',' ').title(),datatype=dtype,name=f'[{c}]',role='measure' if num else 'dimension',type='quantitative' if num else 'nominal')
            inst=f'[avg:{c}:qk]' if num else f'[none:{c}:nk]';refs[c]=f'[{source}].{inst}'
            sub(dep,'column-instance',column=f'[{c}]',derivation='Avg' if num else 'None',name=inst,pivot='key',type='quantitative' if num else 'nominal')
        dep[:]=sorted(dep,key=lambda e:0 if e.tag=='column' else 1)
        for c,values in filters.items():
            f=sub(view,'filter',**{'class':'categorical','column':f'[{source}].[{c}]'})
            if values is None:values=sorted(sources[source][c].dropna().astype(str).unique())
            if len(values)==1:sub(f,'groupfilter',function='member',level=f'[{c}]',member='"'+str(values[0])+'"')
            else:
                u=sub(f,'groupfilter',function='union')
                for val in values:sub(u,'groupfilter',function='member',level=f'[{c}]',member='"'+str(val)+'"')
        if filters:
            slices=sub(view,'slices')
            for c in filters:sub(slices,'column',f'[{source}].[{c}]')
        sub(view,'aggregation',value='true')
        sty=sub(table,'style');r=sub(sty,'style-rule',element='worksheet');sub(r,'format',attr='font-family',value='Tableau Book')
        pane=sub(sub(table,'panes'),'pane',selection_relaxation_option='selection-relaxation-allow');sub(sub(pane,'view'),'breakdown',value='auto')
        sub(pane,'mark',**{'class':mark});enc=sub(pane,'encodings')
        if color:sub(enc,'color',column=refs[color])
        for c in detail:sub(enc,'lod',column=refs[c])
        sub(table,'rows',' / '.join(refs[c] for c in rows));sub(table,'cols',' / '.join(refs[c] for c in cols))

    sheet('Scoring sources | points per game','scoring_mix',['points_per_game'],['season'],color='source',filters={'phase':['Regular Season']})
    sheet('Efficiency | true shooting','season_summary',['ts'],['season'],mark='Line',detail=['games','ppg'],filters={'phase':['Regular Season']})
    sheet('Shot profile | share of attempts','shot_zones',['shot_zone_basic'],['attempt_share'],color='shot_zone_basic',detail=['attempts','fg_pct'],filters={'phase':['Regular Season'],'season':['2025-26']})
    sheet('Playoffs | points by series','series_summary',['season','opponent'],['ppg'],color='round_name',detail=['games','ts','mpg'])
    sheet('Playoffs | scoring sources','scoring_mix',['points_per_game'],['season'],color='source',filters={'phase':['Playoffs']})
    sheet('Playoffs | shot map','shot_map',['loc_y'],['loc_x'],mark='Circle',color='result',detail=['shot_id'],filters={'phase':['Playoffs'],'season':['2025-26']})
    sheet('Scoring | regular vs playoffs','season_summary',['ppg'],['season'],mark='Circle',color='phase',detail=['games','mpg'])
    sheet('Efficiency | regular vs playoffs','season_summary',['ts'],['season'],mark='Circle',color='phase',detail=['games','fga_pg','fta_pg'])
    sheet('Within-season change | points per 36','phase_comparison',['season'],['difference'],detail=['regular_n','playoff_n','regular','playoffs'],filters={'metric':['points_per36']})
    sheet('Final test | mean absolute error','model_scores',['phase','model'],['mae'],color='model',detail=['n','bias','coverage80','width80'],filters={'season':['2025-26']})
    sheet('Forecast replay | predicted vs actual','forecast_replay',['actual'],['prediction'],mark='Circle',color='phase',detail=['fixture','lower80','upper80','model','absolute_error'],filters={'phase':None})
    sheet('Forecast replay | errors by date','forecast_replay',['residual'],['game_date'],mark='Circle',color='phase',detail=['fixture','actual','prediction'],filters={'phase':None})
    dashboards=sub(wb,'dashboards')
    plans=[
      ('01 Regular Season',['Scoring sources | points per game','Efficiency | true shooting','Shot profile | share of attempts'],'SGA / THE SCORING EVOLUTION','448 regular-season appearances | 2019–20 to 2025–26 | Source: NBA Stats. Shot-profile season filter applies to that chart only.',('Shot profile | share of attempts','season')),
      ('02 Playoffs',['Playoffs | points by series','Playoffs | scoring sources','Playoffs | shot map'],'SGA / THE PLAYOFF TEST','55 playoff appearances | 4 postseasons | Missing years mean no appearances. Shot-map filter applies to that chart only.',('Playoffs | shot map','season')),
      ('03 Compare Phases',['Scoring | regular vs playoffs','Efficiency | regular vs playoffs','Within-season change | points per 36'],'SGA / SAME PLAYER. DIFFERENT CONTEXT.','Compare within the same season. Unequal samples, opponents and minutes matter. Associations do not establish causes.',None),
      ('04 Predictions',['Final test | mean absolute error','Forecast replay | predicted vs actual','Forecast replay | errors by date'],'SGA / CAN HISTORY PREDICT THE NEXT GAME?','2025–26 held-out replay | Selection fixed on 2024–25. Regular: Rolling10; playoffs: transfer adjustment. Hover for 80% intervals.',('Forecast replay | predicted vs actual','phase'))]
    for name,sheets,title,subtitle,control in plans:
        d=sub(dashboards,'dashboard',name=name);sub(d,'style');sub(d,'size',maxheight='900',maxwidth='1400',minheight='900',minwidth='1400')
        zones=sub(d,'zones')
        for i,y,h,text,size,bg,fg in [(1,0,8000,title,25,'#112d45','#ffffff'),(2,8000,8500,subtitle,11,'#edf3f7','#334d61')]:
            z=sub(zones,'zone',h=h,id=i,type='text',w=100000,x=0,y=y)
            ft=sub(z,'formatted-text');sub(ft,'run',text,fontname='Tableau Book',fontsize=size,fontcolor=fg,bold='true' if i==1 else 'false')
            st=sub(z,'zone-style');sub(st,'format',attr='background-color',value=bg);sub(st,'format',attr='padding',value='14')
        placements=[(3,2000,18500,60000,78000),(4,64000,18500,34000,35000),(5,64000,58000,34000,38500)]
        for (i,x,y,w,h),sn in zip(placements,sheets):
            z=sub(zones,'zone',h=h,id=i,name=sn,show_title='true',w=w,x=x,y=y)
            st=sub(z,'zone-style');sub(st,'format',attr='padding',value=8);sub(st,'format',attr='border-color',value='#dde5ed');sub(st,'format',attr='border-style',value='solid');sub(st,'format',attr='border-width',value=1)
        if control:
            sn,c=control;source=sheet_meta[sn][0]
            z=sub(zones,'zone',h=4200,id=8,name=sn,param=f'[{source}].[none:{c}:nk]',type_v2='filter',mode='checkdropdown',show_title='false',w=34000,x=64000,y=53700)
    windows=sub(wb,'windows',source_height=900)
    for name,(source,filters) in sheet_meta.items():
        w=sub(windows,'window',**{'class':'worksheet','name':name});sub(w,'viewpoints');sub(w,'active',id='-1')
    for name,sheets,*_ in plans:
        w=sub(windows,'window',**{'class':'dashboard','name':name});v=sub(w,'viewpoints')
        for sn in sheets:sub(sub(v,'viewpoint',name=sn),'zoom',type='entire-view')
        sub(w,'active',id='-1')
    E.indent(wb);twb=OUT/'SGA_Scoring_Lab.twb';E.ElementTree(wb).write(twb,encoding='utf-8',xml_declaration=True)
    with zipfile.ZipFile(OUT/'SGA_Scoring_Lab.twbx','w',zipfile.ZIP_DEFLATED) as z:
        z.write(twb,twb.name);z.write(hyper,hyper.name)
        for name in sources:z.write(OUT/'data'/f'{name}.csv','data/'+name+'.csv')
    shutil.copyfile(OUT/'SGA_Scoring_Lab.twbx',OUT/'SGA_Scoring_Lab_Fixed.twbx')
    print('Created',OUT/'SGA_Scoring_Lab.twbx')

if __name__=='__main__':build()
