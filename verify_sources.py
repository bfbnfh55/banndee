"""Verify delivered raw hashes; optionally compare against an extracted teacher folder."""
import argparse
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser()
parser.add_argument('--teacher-root',type=Path,help='Extracted BaanDee_Class1_Student directory')
args=parser.parse_args()
report=json.loads((ROOT/'docs/source_comparison.json').read_text(encoding='utf-8'))
passed=True
for row in report['raw_files']:
    actual=hashlib.sha256((ROOT/row['file']).read_bytes()).hexdigest()
    expected=row['teacher_sha256']
    ok=actual==expected
    if args.teacher_root:
        teacher=args.teacher_root/row['file']
        ok=ok and teacher.exists() and hashlib.sha256(teacher.read_bytes()).hexdigest()==actual
    passed=passed and ok
    print(('PASS' if ok else 'FAIL')+' '+row['file']+' '+actual)
raise SystemExit(0 if passed else 1)
