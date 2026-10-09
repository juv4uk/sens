"""Adversarial research guard + independent model witnesses.

IMPORTANT: these models do NOT execute any SENS Lisp code. They demonstrate
falsifiable examples for a future actual old/current Lisp runtime oracle.
"""
import copy
from datetime import date,timedelta
import importlib.util
import json
import tempfile
import subprocess
import sys
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'scripts/check_d10_time_law_review_v2.py'
spec=importlib.util.spec_from_file_location('d10time',p)
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
ledger=json.loads((ROOT/'knowledge/d10-time-law-review-v2.json').read_text(encoding='utf-8'))

def model(name,x):
    if name=='CIVIL-FROM-DAYS':
        d=date(1970,1,1)+timedelta(days=x['days']);return [d.year,d.month,d.day]
    if name=='INTERNET-TIME-MODE-VALID?':return int(x['mode'] in (4,5))
    if name=='INTERNET-TIME-STRATUM-VALID?':return int(1<=x['stratum']<=15)
    if name=='INTERNET-TIME-FIELDS->OBSERVATION':
        if x['mode'] not in (4,5) or not(1<=x['stratum']<=15):return ['rejected','invalid-response']
        if x['ntp_seconds']<2208988800:return ['rejected','invalid-epoch']
        return ['accepted',x['host'],x['ntp_seconds']-2208988800,(x['fraction']*1000000000)//4294967296]
    if name=='INTERNET-TIME-RAW->OBSERVATION':
        raw=x['raw'];return model('INTERNET-TIME-FIELDS->OBSERVATION',dict(zip(['host','mode','stratum','ntp_seconds','fraction'],raw[1:]))) if raw[0]=='ntp-fields' else raw
    if name=='INTERNET-TIME-OBSERVATION->UTC':
        raw=x['observation']
        if raw[0]!='accepted':return raw
        secs,nanos=raw[2:];d=date(1970,1,1)+timedelta(days=secs//86400)
        rem=secs%86400
        return ['accepted',raw[1],['utc',d.year,d.month,d.day,rem//3600,(rem%3600)//60,rem%60,nanos]]
    if name=='TIMEZONE-DECLARATIONS->OBSERVATION':
        if isinstance(x['tz'],str) and x['tz']:return ['detected',x['tz'],'TZ']
        if isinstance(x['etc_timezone'],str) and x['etc_timezone']:return ['detected',x['etc_timezone'],'etc-timezone']
        return ['unknown','host-declaration-unavailable']
    if name=='TIMEZONE-RAW->OBSERVATION':
        raw=x['raw'];return model('TIMEZONE-DECLARATIONS->OBSERVATION',{'tz':raw[1],'etc_timezone':raw[2]}) if raw[0]=='timezone-declarations' else ['rejected','invalid-timezone-observation']
    if name=='TIMEZONE-CONFIG':
        if not isinstance(x['name'],str):return ['rejected','invalid-name']
        if not -86400<=x['offset_seconds']<=86400:return ['rejected','invalid-offset']
        return ['accepted',['timezone',x['name'],x['offset_seconds']]]
    raise KeyError(name)

class TimeReview(unittest.TestCase):
    def test_gate(self):
        mod.verify(ledger,ROOT)
    def test_reference_cases_not_runtime_oracle(self):
        for r in ledger['rows']:
            for w in r['witnesses']:
                with self.subTest(name=r['semantic_name'],input=w['input']):
                    self.assertEqual(model(r['semantic_name'],w['input']),w['expect'])
    def test_python_optimized_mode_never_bypasses_assertions(self):
        result=subprocess.run(
            [sys.executable, '-O', str(p)],
            text=True, capture_output=True, cwd=str(ROOT), check=False
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('BLOCK: Python -O disables assertion-based research gates', result.stderr)

    def test_no_fake_ratification(self):
        for field,value in [('coordinate','0000000000'),('ratified_resident',True),('selected_in_canonical_inventory',True),('owner_decision','APPROVED')]:
            with self.subTest(field=field):
                d=copy.deepcopy(ledger);d['rows'][0][field]=value
                with self.assertRaises(AssertionError):mod.verify(d,ROOT)
    def test_no_duplicate_names(self):
        d=copy.deepcopy(ledger);d['rows'][1]['semantic_name']=d['rows'][0]['semantic_name']
        with self.assertRaises(AssertionError):mod.verify(d,ROOT)
    def test_ci_mode_rejects_missing_source(self):
        with tempfile.TemporaryDirectory() as folder:
            self_copy = copy.deepcopy(ledger)
            with self.assertRaisesRegex(AssertionError,'BLOCK: pinned lib/time.lisp missing'):
                mod.verify(self_copy, Path(folder), require_checkout=True)

    def test_ci_mode_rejects_modified_pinned_blob(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            (root/'lib').mkdir()
            (root/'lib/time.lisp').write_text('(00001001 civil-from-days 000)\n',encoding='utf-8')
            with self.assertRaisesRegex(AssertionError,'source moved'):
                mod.verify(copy.deepcopy(ledger),root,require_checkout=True)

    def test_source_optional_mode_is_explicitly_not_admission(self):
        with tempfile.TemporaryDirectory() as folder:
            mod.verify(copy.deepcopy(ledger),Path(folder),require_checkout=False)

    def test_all_pending_independent_oracles(self):
        self.assertTrue(all(r['independent_language_oracle']=='PENDING' for r in ledger['rows']))
        self.assertEqual(ledger['audit']['proposed_selection_effect'],0)

if __name__=='__main__':unittest.main()
