import csv
import hashlib
import json
import shutil
import sys
import tempfile
import threading
import unittest
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.prepare_data import prepare
from src.core import Store
from src.server import make_server

EVIDENCE=[]

class SystemTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name)
        shutil.copytree(ROOT/'data/raw',self.root/'data/raw')
        shutil.copytree(ROOT/'web',self.root/'web')
        shutil.copytree(ROOT/'docs',self.root/'docs')
        prepare(self.root)
        self.store=Store(self.root)
        self.server=make_server(self.store,0)
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
        self.url=f'http://127.0.0.1:{self.server.server_port}'
    def tearDown(self):
        self.server.shutdown();self.server.server_close();self.thread.join();self.temp.cleanup()
    def call(self,path,method='GET',data=None,origin=None):
        headers={'Content-Type':'application/json'}
        if origin:headers['Origin']=origin
        req=Request(self.url+path,data=json.dumps(data).encode() if data is not None else None,method=method,headers=headers)
        try:
            with urlopen(req,timeout=5) as r:return r.status,json.load(r)
        except HTTPError as e:return e.code,json.load(e)
    def record(self,input_,expected,actual):
        ok=actual==expected
        EVIDENCE.append(dict(test=self.id().split('.')[-1],input=input_,expected=expected,actual=actual,result='PASS' if ok else 'FAIL'))
        self.assertEqual(actual,expected)
    def draft(self):
        return {'product_id':'SKU-0001','quantity':25,'note':'demo','mode':'demo'}
    def test_01_success_rule(self):
        code,r=self.call('/api/risks/SKU-0001?mode=demo')
        self.record('GET SKU-0001 demo', [200,'low',5,25], [code,r['status'],r['available_qty'],r['suggested_qty']])
    def test_02_not_found(self):
        code,_=self.call('/api/risks/DOES-NOT-EXIST')
        self.record('GET absent SKU',404,code)
    def test_03_unavailable(self):
        code,_=self.call('/api/risks?unavailable=1')
        self.record('GET risks unavailable=1',503,code)
    def test_04_ambiguous_policy_blocks_write(self):
        outcomes=[]
        for pid in ['SKU-0002','SKU-0003','SKU-0005']:
            code,r=self.call('/api/risks/'+pid)
            write_code,_=self.call('/api/requests','POST',dict(self.draft(),product_id=pid))
            outcomes.append([r['status'],r['suggested_qty'],write_code])
        self.record('missing / negative / conflicting policies',[['review',None,409]]*3,outcomes)
    def test_05_stale_data_blocks(self):
        # Inject a known old timestamp so this test is stable even on machines with an earlier clock.
        path=self.root/'data/cleaned/inventory.csv'
        path.write_text(path.read_text(encoding='utf-8-sig').replace('2026-07-31','2000-01-01'),encoding='utf-8-sig')
        _,r=self.call('/api/risks/SKU-0001?mode=live')
        code,_=self.call('/api/requests','POST',dict(self.draft(),mode='live'))
        self.record('old snapshot, live mode',['review',409],[r['status'],code])
    def test_06_create_edit_restart_persistence(self):
        code,created=self.call('/api/requests','POST',self.draft())
        update_code,updated=self.call('/api/requests/'+str(created['id']),'PUT',dict(quantity=28,note='edited',version=1,status='draft'))
        self.server.shutdown();self.server.server_close();self.thread.join()
        # Recreate application and SQLite connection from same files.
        self.store=Store(self.root);self.server=make_server(self.store,0)
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
        self.url=f'http://127.0.0.1:{self.server.server_port}'
        _,again=self.call('/api/requests/'+str(created['id']))
        _,history=self.call('/api/requests/'+str(created['id'])+'/history')
        self.record('POST 25; PUT 28; restart; GET',[201,200,28,'edited',2,2],[code,update_code,again['quantity'],again['note'],again['version'],len(history)])
    def test_07_invalid_quantity(self):
        actual=[self.call('/api/requests','POST',dict(self.draft(),quantity=q))[0] for q in [-1,0,1.5,True,10001,'10']]
        self.record('quantities -1,0,1.5,true,10001,string',[422]*6,actual)
    def test_08_duplicate_request(self):
        a,_=self.call('/api/requests','POST',self.draft());b,_=self.call('/api/requests','POST',self.draft())
        self.record('POST same active SKU twice',[201,409],[a,b])
    def test_09_concurrent_edit_version(self):
        _,r=self.call('/api/requests','POST',self.draft())
        path='/api/requests/'+str(r['id'])
        data=dict(quantity=26,note='edit',version=1)
        a,_=self.call(path,'PUT',data);b,_=self.call(path,'PUT',data)
        self.record('two edits use same version=1',[200,409],[a,b])
    def test_10_cancel_retains_audit(self):
        _,r=self.call('/api/requests','POST',self.draft());path='/api/requests/'+str(r['id'])
        a,c=self.call(path,'PUT',dict(quantity=25,note='cancel',version=1,status='cancelled'))
        _,history=self.call(path+'/history')
        b,_=self.call('/api/requests','POST',self.draft())
        self.record('cancel; inspect audit; new request',[200,'cancelled',2,201],[a,c['status'],len(history),b])
    def test_11_cleaning_and_raw_unchanged(self):
        files=list((self.root/'data/raw').glob('*'))
        before=[hashlib.sha256(p.read_bytes()).hexdigest() for p in files]
        result=prepare(self.root)
        after=[hashlib.sha256(p.read_bytes()).hexdigest() for p in files]
        self.record('rerun pipeline; compare SHA256',[85,79,5,3,True],[result['policy_before'],result['policy_after'],result['quarantined_rows'],result['inventory_without_policy'],before==after])
    def test_12_no_many_to_many_join(self):
        _,risks=self.call('/api/risks')
        keys={(r['product_id'],r['location_id']) for r in risks}
        self.record('cleaned joined inventory',[82,82],[len(risks),len(keys)])
    def test_13_cross_origin_write_blocked(self):
        code,_=self.call('/api/requests','POST',self.draft(),origin='https://untrusted.example')
        self.record('POST from unrelated Origin',403,code)
    def test_14_healthy_stock_blocks_request(self):
        code,_=self.call('/api/requests','POST',dict(self.draft(),product_id='SKU-0004'))
        self.record('POST SKU-0004 qty=40 > minimum=10',409,code)
    def test_15_xss_stored_as_text(self):
        payload='<img src=x onerror=alert(1)>'
        code,r=self.call('/api/requests','POST',dict(self.draft(),note=payload))
        self.record('note HTML retained literally; UI uses textContent',[201,payload],[code,r['note']])
    def test_16_unknown_request_and_mode(self):
        a,_=self.call('/api/requests/9999');b,_=self.call('/api/risks?mode=invalid')
        self.record('unknown request; invalid mode',[404,400],[a,b])
    def test_17_runtime_invalid_quantity_stops(self):
        p=self.root/'data/cleaned/inventory.csv'
        p.write_text(p.read_text(encoding='utf-8-sig').replace('SKU-0001,BKK-DC,5,','SKU-0001,BKK-DC,-5,'),encoding='utf-8-sig')
        _,r=self.call('/api/risks/SKU-0001');code,_=self.call('/api/requests','POST',self.draft())
        self.record('negative inventory injected into test copy',['review',None,409],[r['status'],r['suggested_qty'],code])
    def test_18_zero_stock(self):
        code,r=self.call('/api/risks/SKU-BD-220')
        self.record('zero-stock item',[200,'out',30],[code,r['status'],r['suggested_qty']])

    def policy(self, **changes):
        return dict(dict(product_id='SKU-0005',mode='demo',min_qty=10,target_qty=30,lead_days=7,
                         reviewer='Demo reviewer',reason='Team-approved synthetic policy for demonstration',version=0),**changes)

    def test_19_review_resolves_and_persists(self):
        code,r=self.call('/api/policy-reviews','POST',self.policy())
        persisted=Store(self.root).risk('SKU-0005')
        c,_=self.call('/api/requests','POST',dict(self.draft(),product_id='SKU-0005'))
        _,history=self.call('/api/policy-history/SKU-0005')
        self.record('review conflict; reopen Store; create draft',[200,'low',1,201,1],
                    [code,persisted['status'],persisted['policy_version'],c,len(history)])

    def test_20_policy_validation(self):
        codes=[self.call('/api/policy-reviews','POST',self.policy(**d))[0] for d in
               [dict(min_qty=-1),dict(target_qty=10),dict(lead_days=0),dict(min_qty=True),
                dict(reason=''),dict(reviewer=''),dict(version=-1)]]
        self.record('invalid policy bounds/types/reason/reviewer/version',[422]*7,codes)

    def test_21_policy_concurrent_version(self):
        a,_=self.call('/api/policy-reviews','POST',self.policy())
        b,_=self.call('/api/policy-reviews','POST',self.policy(target_qty=40))
        c,r=self.call('/api/policy-reviews','POST',self.policy(target_qty=40,version=1))
        _,h=self.call('/api/policy-history/SKU-0005')
        self.record('version 0; stale 0; current 1',[200,409,200,2,2],[a,b,c,r['policy_version'],len(h)])

    def test_22_review_does_not_refresh_stock(self):
        p=self.root/'data/cleaned/inventory.csv'
        p.write_text(p.read_text(encoding='utf-8-sig').replace('2026-07-31','2000-01-01'),encoding='utf-8-sig')
        _,r=self.call('/api/policy-reviews','POST',self.policy(mode='live'))
        c,_=self.call('/api/requests','POST',dict(self.draft(),product_id='SKU-0005',mode='live'))
        self.record('review policy with stale stock',['review',None,409],[r['status'],r['suggested_qty'],c])

    def test_23_demo_review_isolated_from_live(self):
        self.call('/api/policy-reviews','POST',self.policy())
        _,live=self.call('/api/risks/SKU-0005?mode=live')
        self.record('save demo; read live',[0,None],[live['policy_version'],live['policy_review']])

    def test_24_whatif_no_writes(self):
        before=self.store.risk('SKU-0001')
        code,r=self.call('/api/what-if','POST',self.policy(product_id='SKU-0001',target_qty=50))
        after=self.store.risk('SKU-0001')
        self.record('simulate target 50; compare DB/risk',[200,45,False,True,0,0],
                    [code,r['after']['suggested_qty'],r['saved'],before==after,len(self.store.all_requests()),len(self.store.policy_history('SKU-0001'))])

    def test_25_whatif_blocks_ambiguous(self):
        code,_=self.call('/api/what-if','POST',self.policy())
        self.record('simulate unresolved SKU-0005',409,code)

    def test_26_runtime_invalid_policy(self):
        p=self.root/'data/cleaned/policies.csv'
        p.write_text(p.read_text(encoding='utf-8-sig').replace('SKU-0001,BKK-DC,10,','SKU-0001,BKK-DC,broken,'),encoding='utf-8-sig')
        code,r=self.call('/api/risks/SKU-0001')
        self.record('invalid number in cleaned policy',[200,'review',None],[code,r['status'],r['suggested_qty']])

    def test_27_raw_and_quarantine_preserved(self):
        files=list((self.root/'data/raw').glob('*'))+[self.root/'data/cleaned/quarantine.csv']
        before=[p.read_bytes() for p in files]
        self.call('/api/policy-reviews','POST',self.policy())
        self.record('review policy; compare raw/quarantine',True,before==[p.read_bytes() for p in files])

    def test_28_provenance_hashes(self):
        code,report=self.call('/api/project')
        matches=all(r['matches_teacher'] and r['sha256']==hashlib.sha256((self.root/r['file']).read_bytes()).hexdigest() for r in report['raw_files'])
        self.record('project provenance vs delivered raw',[200,2,True],[code,len(report['raw_files']),matches])

    def test_29_unknown_policy_and_history(self):
        a,_=self.call('/api/policy-reviews','POST',self.policy(product_id='MISSING'))
        b,_=self.call('/api/policy-history/MISSING')
        self.record('unknown product review/history',[404,404],[a,b])

    def test_30_update_audit_evidence(self):
        _,r=self.call('/api/requests','POST',self.draft())
        self.call('/api/policy-reviews','POST',self.policy(product_id='SKU-0001',target_qty=40))
        self.call('/api/requests/'+str(r['id']),'PUT',dict(quantity=35,note='updated policy',version=1))
        _,h=self.call('/api/requests/'+str(r['id'])+'/history')
        evidence=json.loads(h[-1]['payload'])['evaluated_evidence']
        self.record('change policy; update request; inspect audit',[40,1],[evidence['target_qty'],evidence['policy_version']])

if __name__=='__main__':
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(SystemTests)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    out=ROOT/'test_results';out.mkdir(exist_ok=True)
    report={'executed_at':datetime.now(timezone.utc).isoformat(),'python':sys.version,'tests_run':result.testsRun,
            'failures':len(result.failures),'errors':len(result.errors),'cases':EVIDENCE}
    (out/'results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    with (out/'results.csv').open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=['test','input','expected','actual','result']);writer.writeheader()
        for row in EVIDENCE:writer.writerow({k:json.dumps(v,ensure_ascii=False) if isinstance(v,(list,dict)) else v for k,v in row.items()})
    sys.exit(0 if result.wasSuccessful() else 1)
