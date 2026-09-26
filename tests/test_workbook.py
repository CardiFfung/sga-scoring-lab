from pathlib import Path
import xml.etree.ElementTree as E
import zipfile
ROOT=Path(__file__).resolve().parents[1]

def test_tableau_structure_and_package():
    p=ROOT/'tableau/SGA_Scoring_Lab.twbx'
    if not p.exists():return
    with zipfile.ZipFile(p) as z:
        assert z.testzip() is None
        root=E.fromstring(z.read('SGA_Scoring_Lab.twb'))
        assert len(root.findall('./dashboards/dashboard'))==4
        assert len(root.findall('./worksheets/worksheet'))==12
        assert len(root.findall('.//zone[@type-v2="filter"]'))==3
        sheets={x.attrib['name'] for x in root.findall('./worksheets/worksheet')}
        for zone in root.findall('./dashboards/dashboard/zones/zone'):
            if 'name' in zone.attrib:assert zone.attrib['name'] in sheets
        for ds in root.findall('./datasources/datasource'):
            assert 'data/'+ds.attrib['name']+'.csv' in z.namelist()
        assert len(z.read('sga.hyper'))>0

def test_tableau_reported_schema_regressions():
    """Guard the exact schema failures reported by Tableau, beyond well-formed XML."""
    with zipfile.ZipFile(ROOT/'tableau/SGA_Scoring_Lab.twbx') as z:
        root=E.fromstring(z.read('SGA_Scoring_Lab.twb'))
    assert all('user-specific' not in e.attrib for e in root.findall('.//extract'))
    assert root.find('.//format[@attr="gridline-visibility"]') is None
    assert all(len(e.findall('column'))>0 for e in root.findall('.//slices'))
    assert root.find('.//groupfilter[@function="all"]') is None
    assert 'source-width' not in root.find('windows').attrib
    for sheet in root.findall('./worksheets/worksheet'):
        for group in sheet.findall('.//groupfilter[@function="union"]'):
            assert len(group)>0
