"""Development-only validation: python -m pip install jsonschema==4.26.0"""
import copy
import json
from pathlib import Path
from jsonschema import Draft202012Validator, FormatChecker
root = Path(__file__).resolve().parents[1]
results = []
def check(name, condition):
    assert condition, name
    results.append({'name': name, 'status': 'PASS'})
validators = {}
records = {}
for kind, filename in [('product','PF-STD'), ('batch','PF-TEST-001')]:
    schema = json.loads((root / f'site/schemas/{kind}.schema.json').read_text())
    Draft202012Validator.check_schema(schema)
    check(f'{kind} Schema syntax', True)
    validators[kind] = Draft202012Validator(schema, format_checker=FormatChecker())
    folder = 'products' if kind == 'product' else 'batches'
    records[kind] = json.loads((root / f'site/{folder}/{filename}.json').read_text())
    validators[kind].validate(records[kind])
    check(f'{kind} sample', True)
def reject(name,kind,change):
    data = copy.deepcopy(records[kind]); change(data)
    check(name, bool(list(validators[kind].iter_errors(data))))
reject('invalid calendar date','batch',lambda d:d.update(production_date='2026-02-30'))
reject('date naming alias','batch',lambda d:d.update(productionDate='2026-09-07'))
reject('invalid record type','batch',lambda d:d.update(record_type='fake'))
reject('invalid batch status','batch',lambda d:d.update(status='PASS'))
reject('test record requires TEST code','batch',lambda d:d.update(batch='PF-001'))
reject('inspection must be array','batch',lambda d:d.update(inspection={}))
reject('invalid inspection status','batch',lambda d:d['inspection'][0].update(status='OK'))
reject('batch traversal','batch',lambda d:d.update(batch='../test'))
reject('batch trailing newline','batch',lambda d:d.update(batch='PF-TEST-001\n'))
reject('product traversal','product',lambda d:d['identity'].update(product_code='../test'))
reject('missing product identity','product',lambda d:d.pop('identity'))
reject('certifications must be array','product',lambda d:d.update(certifications={}))
reject('invalid certificate date','product',lambda d:d['certifications'][0].update(valid_until='2026-13-01'))
reject('unknown nested field','product',lambda d:d['packaging'].update(packageSize='25kg'))
check('PF-STD process order',records['product']['manufacturing_process']==['Raw Potato Receiving','Washing','Peeling','Cooking','Mashing','Drum Drying','Flaking','Inspection','Packaging'])
check('product batch relation',records['product']['identity']['product_code']==records['batch']['product_code'])
check('no fabricated COA',all(i['result']=='' and i['status']=='NOT_TESTED' for i in records['batch']['inspection']))
(root/'.qa/product-id').mkdir(parents=True,exist_ok=True)
(root/'.qa/product-id/schema-results.json').write_text(json.dumps(results,indent=2)+'\n')
print(f'{len(results)} schema and data checks: PASS')
