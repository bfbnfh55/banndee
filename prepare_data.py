"""Reproducible data pipeline. Never modifies supplied raw files."""
import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY_DATE = '2026-07-31T06:00:00+07:00'


def read(path):
    with path.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def write(path, rows, fields):
    with path.open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def prepare(root=ROOT):
    raw, gen, out = (root / 'data' / s for s in ('raw', 'generated', 'cleaned'))
    gen.mkdir(parents=True, exist_ok=True)
    out.mkdir(parents=True, exist_ok=True)
    products = read(raw / 'products.csv')
    inventory = read(raw / 'inventory_snapshot.csv')
    # Deterministic synthetic policy, not inferred from sales or supplier records.
    policies = [dict(product_id=p['product_id'], location_id='BKK-DC', min_qty='10',
                     target_qty='30', lead_days='7', updated_at=POLICY_DATE,
                     source='synthetic-policy-v1') for p in products]
    policies[0]['product_id'] = ' sku-0001 '
    policies[1]['min_qty'] = ''
    policies[2]['min_qty'] = '-5'
    policies.append(dict(policies[3]))  # exact duplicate, safe to collapse
    policies.append(dict(policies[4], target_qty='40'))  # conflicting policy; never pick one
    policies.append(dict(policies[6], product_id='SKU-UNKNOWN'))
    fields = list(policies[0])
    write(gen / 'replenishment_policy.csv', policies, fields)
    issues = []

    def issue(source, row, kind, key, before, after, action):
        issues.append(dict(source=source, row=row, issue=kind, key=key,
                           before=before, after=after, action=action))

    # Only case normalization: do not assume that 'Bed room' means 'Bedding'.
    categories = {'kitchen': 'Kitchen', 'bedding': 'Bedding', 'storage': 'Storage'}
    for i, p in enumerate(products, 2):
        old = p['category']
        if old in categories:
            p['category'] = categories[old]
            issue('raw/products.csv', i, 'category_case', p['product_id'], old, p['category'], 'normalize case only')
    product_keys = {p['product_id'] for p in products}
    groups = defaultdict(list)
    for i, p in enumerate(policies, 2):
        p = dict(p)
        old = p['product_id']
        p['product_id'] = old.strip().upper()
        if old != p['product_id']:
            issue('generated/replenishment_policy.csv', i, 'key_format', p['product_id'], old, p['product_id'], 'strip and uppercase SKU')
        groups[(p['product_id'], p['location_id'])].append((i, p))
    clean, quarantine = [], []
    for key, group in groups.items():
        unique = {json.dumps(p, sort_keys=True): (i, p) for i, p in group}
        if len(unique) > 1:
            for i, p in group:
                quarantine.append(dict(p, reason='conflicting_policy'))
                issue('generated/replenishment_policy.csv', i, 'conflicting_policy', '|'.join(key), json.dumps(p), '', 'quarantine all versions')
            continue
        i, p = group[0]
        if len(group) > 1:
            issue('generated/replenishment_policy.csv', group[1][0], 'exact_duplicate', '|'.join(key), str(len(group)), '1', 'collapse identical rows')
        reason = ''
        if p['product_id'] not in product_keys:
            reason = 'unknown_product'
        else:
            try:
                minimum, target, lead = (int(p[k]) for k in ('min_qty', 'target_qty', 'lead_days'))
                if not (0 <= minimum < target <= 10000 and 1 <= lead <= 365):
                    reason = 'invalid_policy_range'
            except ValueError:
                reason = 'missing_or_invalid_number'
        if reason:
            quarantine.append(dict(p, reason=reason))
            issue('generated/replenishment_policy.csv', i, reason, '|'.join(key), json.dumps(p), '', 'quarantine; human review')
        else:
            clean.append(p)
    write(out / 'products.csv', products, list(products[0]))
    write(out / 'inventory.csv', inventory, list(inventory[0]))
    write(out / 'policies.csv', clean, fields)
    write(out / 'quarantine.csv', quarantine, fields + ['reason'])
    write(out / 'correction_log.csv', issues, ['source','row','issue','key','before','after','action'])
    summary = dict(products=len(products), inventory=len(inventory), policy_before=len(policies),
                   policy_after=len(clean), quarantined_rows=len(quarantine),
                   inventory_without_policy=sum((r['product_id'],r['location_id']) not in {(p['product_id'],p['location_id']) for p in clean} for r in inventory),
                   issues_by_type={k:sum(i['issue']==k for i in issues) for k in sorted({i['issue'] for i in issues})},
                   rules='See docs/DATA_RULES.md; generated errors are intentional fixtures, not defects claimed in original inventory.')
    (out / 'quality_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    files = list(raw.glob('*')) + list(gen.glob('*.csv'))
    manifest = {'original_archive':'BaanDee_Class1_Student-20261012T164749Z-1-001.zip',
                'files':{str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
                'generation':'deterministic, no random sampling; scripts/prepare_data.py',
                'synthetic_assumptions':{'min_qty':10,'target_qty':30,'lead_days':7,'max_inventory_age_hours':24,'max_policy_age_days':30}}
    (out / 'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    return summary

if __name__ == '__main__':
    print(json.dumps(prepare(),ensure_ascii=False,indent=2))
