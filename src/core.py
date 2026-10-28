"""Evidence-based stock rules and persistent, versioned draft requests."""
from contextlib import contextmanager
import csv
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEMO_NOW = '2026-07-31T08:00:00+07:00'

class Problem(Exception):
    def __init__(self, status, message):
        self.status, self.message = status, message


def rows(path):
    with path.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def timestamp():
    return datetime.now(timezone.utc).isoformat()


class Store:
    def __init__(self, root=ROOT, db=None):
        self.root = Path(root)
        self.db = Path(db) if db else self.root / 'data/runtime/stockguard.sqlite3'
        self.db.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as con:
            con.executescript('''CREATE TABLE IF NOT EXISTS requests (
              id INTEGER PRIMARY KEY, product_id TEXT NOT NULL, location_id TEXT NOT NULL,
              quantity INTEGER NOT NULL CHECK(quantity>0), note TEXT NOT NULL, status TEXT NOT NULL,
              mode TEXT NOT NULL, version INTEGER NOT NULL, evidence TEXT NOT NULL,
              created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
              CREATE UNIQUE INDEX IF NOT EXISTS one_active_request
              ON requests(product_id, location_id, mode) WHERE status='draft';
              CREATE TABLE IF NOT EXISTS audit (
              id INTEGER PRIMARY KEY, request_id INTEGER NOT NULL, action TEXT NOT NULL,
              payload TEXT NOT NULL, at TEXT NOT NULL);
              CREATE TABLE IF NOT EXISTS policy_reviews (
              product_id TEXT NOT NULL, location_id TEXT NOT NULL, mode TEXT NOT NULL,
              version INTEGER NOT NULL, payload TEXT NOT NULL,
              PRIMARY KEY(product_id, location_id, mode));
              CREATE TABLE IF NOT EXISTS policy_audit (
              id INTEGER PRIMARY KEY, product_id TEXT NOT NULL, location_id TEXT NOT NULL,
              mode TEXT NOT NULL, payload TEXT NOT NULL, at TEXT NOT NULL);''')

    @contextmanager
    def connect(self):
        con = sqlite3.connect(self.db, timeout=10)
        con.row_factory = sqlite3.Row
        try:
            with con:
                yield con
        finally:
            con.close()

    def risks(self, mode='demo'):
        if mode not in ('demo','live'):
            raise Problem(400, 'mode ต้องเป็น demo หรือ live')
        now = datetime.fromisoformat(DEMO_NOW) if mode == 'demo' else datetime.now(timezone.utc)
        base = self.root / 'data/cleaned'
        products = {p['product_id']:p for p in rows(base/'products.csv')}
        policies = {(p['product_id'],p['location_id']):p for p in rows(base/'policies.csv')}
        with self.connect() as con:
            overrides = {(r['product_id'], r['location_id']): json.loads(r['payload'])
                         for r in con.execute('SELECT * FROM policy_reviews WHERE mode=?', (mode,))}
        policies.update(overrides)
        result = []
        for stock in rows(base/'inventory.csv'):
            pid, location = stock['product_id'],stock['location_id']
            product, policy = products.get(pid),policies.get((pid,location))
            reasons = []
            qty, age = None,None
            try:
                qty = int(stock['available_qty'])
                if qty < 0: raise ValueError()
            except (ValueError,TypeError): reasons.append('จำนวนสต็อกไม่ถูกต้อง')
            try:
                dt = datetime.fromisoformat(stock['as_of'])
                if dt.tzinfo is None: raise ValueError()
                age = (now-dt).total_seconds()/3600
                if age < 0 or age > 24: reasons.append('ข้อมูลสต็อกเกิน 24 ชั่วโมงหรือเวลาอยู่ในอนาคต')
            except (ValueError,TypeError): reasons.append('ตรวจสอบเวลาสต็อกไม่ได้')
            if not product: reasons.append('ไม่พบข้อมูลสินค้า')
            if not policy: reasons.append('นโยบายไม่ผ่านการตรวจสอบ ต้องให้เจ้าหน้าที่ทบทวน')
            else:
                try:
                    policy_date = datetime.fromisoformat(policy['updated_at'])
                    policy_age = (now-policy_date).total_seconds()/86400
                    if policy_age < 0 or policy_age > 30: reasons.append('นโยบายเกิน 30 วันหรือเวลาอยู่ในอนาคต')
                except (ValueError,TypeError): reasons.append('ตรวจสอบเวลานโยบายไม่ได้')
            minimum = target = lead = None
            if policy:
                try:
                    minimum, target, lead = (int(policy[k]) for k in ('min_qty','target_qty','lead_days'))
                    if not 0 <= minimum < target <= 10000 or not 1 <= lead <= 365:
                        raise ValueError()
                except (ValueError, TypeError, KeyError):
                    minimum = target = lead = None
                    reasons.append('ค่านโยบายไม่ถูกต้อง ต้องทบทวน')
            status = 'review' if reasons else ('out' if qty == 0 else 'low' if qty <= minimum else 'ok')
            suggested = max(0,target-qty) if status in ('low','out') else 0 if status=='ok' else None
            result.append(dict(product_id=pid,location_id=location,product_name=product['product_name'] if product else pid,
                category=product['category'] if product else '',available_qty=qty,as_of=stock['as_of'],age_hours=round(age,2) if age is not None else None,
                min_qty=minimum,target_qty=target,lead_days=lead,
                policy_updated_at=policy['updated_at'] if policy else None,status=status,suggested_qty=suggested,
                reasons=reasons,mode=mode,evaluated_at=now.isoformat(),
                sources=['data/raw/products.csv','data/raw/inventory_snapshot.csv','data/generated/replenishment_policy.csv'] + (['SQLite: policy_reviews (human review)'] if (pid,location) in overrides else []),
                policy_version=policy.get('version',0) if policy else 0,
                policy_review=policy if (pid,location) in overrides else None,
                policy_assumption='นโยบายสังเคราะห์ ไม่ใช่ยอดขายหรือระยะเวลาจัดหาที่วัดจริง'))
        return result

    def risk(self, pid, location='BKK-DC', mode='demo'):
        for r in self.risks(mode):
            if (r['product_id'],r['location_id']) == (pid,location): return r
        raise Problem(404,'ไม่พบสินค้า/คลังที่ระบุ')

    def quality(self):
        base=self.root/'data/cleaned'
        return dict(summary=json.loads((base/'quality_summary.json').read_text(encoding='utf-8')),
                    log=rows(base/'correction_log.csv'),quarantine=rows(base/'quarantine.csv'))

    def all_requests(self):
        with self.connect() as con:
            return [dict(r) for r in con.execute('SELECT * FROM requests ORDER BY id DESC')]

    def get_request(self, ident):
        with self.connect() as con:
            r=con.execute('SELECT * FROM requests WHERE id=?',(ident,)).fetchone()
            if not r: raise Problem(404,'ไม่พบคำขอ')
            return dict(r)

    def history(self, ident):
        self.get_request(ident)
        with self.connect() as con:
            return [dict(r) for r in con.execute('SELECT * FROM audit WHERE request_id=? ORDER BY id',(ident,))]

    def validate(self, data):
        if type(data.get('quantity')) is not int or not 1 <= data['quantity'] <= 10000:
            raise Problem(422,'จำนวนต้องเป็นจำนวนเต็ม 1–10,000')
        if not isinstance(data.get('note',''),str) or len(data.get('note',''))>500:
            raise Problem(422,'หมายเหตุต้องเป็นข้อความไม่เกิน 500 ตัวอักษร')
        return data['quantity'],data.get('note','').strip()

    def create(self,data):
        quantity,note=self.validate(data)
        mode=data.get('mode','demo')
        evidence=self.risk(data.get('product_id'),data.get('location_id','BKK-DC'),mode)
        if evidence['status'] not in ('low','out'):
            raise Problem(409,'สร้างไม่ได้: ต้องเป็นสต็อกต่ำ/หมดที่มีหลักฐานครบและยังสดใหม่')
        now=timestamp()
        try:
            with self.connect() as con:
                cur=con.execute('INSERT INTO requests(product_id,location_id,quantity,note,status,mode,version,evidence,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?)',
                    (evidence['product_id'],evidence['location_id'],quantity,note,'draft',mode,1,json.dumps(evidence,ensure_ascii=False),now,now))
                ident=cur.lastrowid
                con.execute('INSERT INTO audit(request_id,action,payload,at) VALUES(?,?,?,?)',(ident,'create',json.dumps(data,ensure_ascii=False),now))
        except sqlite3.IntegrityError:
            raise Problem(409,'มีคำขอฉบับร่างสำหรับสินค้านี้อยู่แล้ว กรุณาแก้ไขรายการเดิม')
        return self.get_request(ident)

    def update(self,ident,data):
        quantity,note=self.validate(data)
        if type(data.get('version')) is not int: raise Problem(422,'ต้องระบุ version เป็นจำนวนเต็ม')
        if data.get('status','draft') not in ('draft','cancelled'): raise Problem(422,'สถานะไม่ถูกต้อง')
        current=self.get_request(ident)
        if current['status']=='cancelled': raise Problem(409,'คำขอถูกยกเลิกแล้ว ไม่สามารถแก้ไข')
        status=data.get('status','draft')
        if status=='draft':
            r=self.risk(current['product_id'],current['location_id'],current['mode'])
            if r['status'] not in ('low','out'): raise Problem(409,'หลักฐานปัจจุบันไม่เพียงพอสำหรับแก้ไขคำขอ')
        now=timestamp()
        with self.connect() as con:
            cur=con.execute('UPDATE requests SET quantity=?,note=?,status=?,version=version+1,updated_at=? WHERE id=? AND version=? AND status=?',
                (quantity,note,status,now,ident,data['version'],'draft'))
            if cur.rowcount!=1: raise Problem(409,'ข้อมูลถูกแก้ไขแล้ว กรุณาโหลดรายการใหม่')
            con.execute('INSERT INTO audit(request_id,action,payload,at) VALUES(?,?,?,?)',(ident,'cancel' if status=='cancelled' else 'update',json.dumps(dict(data,evaluated_evidence=r if status=='draft' else None),ensure_ascii=False),now))
        return self.get_request(ident)


    def policy_history(self, pid, location='BKK-DC', mode='demo'):
        self.risk(pid, location, mode)
        with self.connect() as con:
            return [dict(r) for r in con.execute(
                'SELECT * FROM policy_audit WHERE product_id=? AND location_id=? AND mode=? ORDER BY id',
                (pid,location,mode))]

    def policy_values(self, data):
        values = [data.get(k) for k in ('min_qty','target_qty','lead_days')]
        if any(type(v) is not int for v in values):
            raise Problem(422,'นโยบายต้องเป็นจำนวนเต็ม')
        minimum,target,lead=values
        if not 0 <= minimum < target <= 10000 or not 1 <= lead <= 365:
            raise Problem(422,'ต้องมี 0 ≤ ขั้นต่ำ < เป้าหมาย ≤ 10000 และระยะจัดหา 1–365 วัน')
        return dict(zip(('min_qty','target_qty','lead_days'), values))

    def review_policy(self, data):
        values=self.policy_values(data)
        for key in ('reviewer','reason'):
            if not isinstance(data.get(key),str) or not 3 <= len(data[key].strip()) <= 500:
                raise Problem(422,'ต้องระบุผู้ทบทวนและเหตุผล/หลักฐานอย่างน้อย 3 ตัวอักษร ไม่เกิน 500 ตัวอักษร')
        if type(data.get('version')) is not int or data['version'] < 0:
            raise Problem(422,'ต้องระบุ version ปัจจุบัน')
        pid,loc,mode=data.get('product_id'),data.get('location_id','BKK-DC'),data.get('mode','demo')
        before=self.risk(pid,loc,mode)
        saved_at=timestamp()
        payload=dict(values,product_id=pid,location_id=loc,mode=mode,
                     reviewer=data['reviewer'].strip(),reason=data['reason'].strip(),
                     updated_at=DEMO_NOW if mode=='demo' else saved_at,
                     saved_at=saved_at,version=data['version']+1)
        with self.connect() as con:
            con.execute('BEGIN IMMEDIATE')
            current=con.execute('SELECT version,payload FROM policy_reviews WHERE product_id=? AND location_id=? AND mode=?',
                                (pid,loc,mode)).fetchone()
            version=current['version'] if current else 0
            if version!=data['version']:
                raise Problem(409,'นโยบายถูกแก้ไขแล้ว กรุณาเปิดรายการใหม่')
            con.execute('INSERT OR REPLACE INTO policy_reviews VALUES(?,?,?,?,?)',
                        (pid,loc,mode,payload['version'],json.dumps(payload,ensure_ascii=False)))
            con.execute('INSERT INTO policy_audit(product_id,location_id,mode,payload,at) VALUES(?,?,?,?,?)',
                        (pid,loc,mode,json.dumps(dict(before=json.loads(current['payload']) if current else before,
                                                    after=payload),ensure_ascii=False),saved_at))
        return self.risk(pid,loc,mode)

    def what_if(self, data):
        values=self.policy_values(data)
        before=self.risk(data.get('product_id'),data.get('location_id','BKK-DC'),data.get('mode','demo'))
        if before['status']=='review':
            raise Problem(409,'ต้องแก้ข้อมูลที่ต้องทบทวนก่อนจำลอง What-if')
        qty=before['available_qty']
        status='out' if qty==0 else 'low' if qty<=values['min_qty'] else 'ok'
        return dict(before=before,after=dict(values,status=status,
                    suggested_qty=max(0,values['target_qty']-qty) if status in ('out','low') else 0),
                    saved=False,assumption='สถานการณ์สมมติ ไม่บันทึกนโยบายหรือคำขอ')
