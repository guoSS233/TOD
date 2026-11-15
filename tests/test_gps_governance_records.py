import re
import unittest
from pathlib import Path
from test_gps_governance_runtime import GPSState

ROOT = Path(__file__).resolve().parents[1]
FLAGS = ('wages', 'representatives', 'grievance')

def receipt(choice='b', flags=(), done=True, invalid=False, repeated=False):
    s = GPSState()
    s.effect('GPS_gov_start_demobilization')
    s.option(45, choice)
    s.flags.update('GPS_gov_'+f+'_recorded' for f in flags)
    if done: s.flags.add('GPS_gov_workers_record_done')
    if invalid: s.states[0]['controlled'] = False
    if repeated: s.flags.add('GPS_gov_demobilization_done')
    before = s.pp, s.stability
    s.option(46, 'a', check=False)
    return s.pp-before[0], s.stability-before[1]

class Records(unittest.TestCase):
    def test_record_bonuses_and_baseline(self):
        for flags, expected in [((), (3,0)), (('wages',),(5,0)), (('representatives',),(3,.005)), (('grievance',),(3,.005)), (FLAGS,(5,.01))]:
            with self.subTest(flags=flags):
                actual=receipt(flags=flags)
                for a,b in zip(actual,expected): self.assertAlmostEqual(a,b)
    def test_no_bonus_without_completed_focus_or_for_other_receipts(self):
        self.assertEqual(receipt(flags=FLAGS,done=False),(3,0))
        for choice in ('a','c'):
            pp,st=receipt(choice,FLAGS)
            self.assertAlmostEqual(pp,0); self.assertAlmostEqual(st,.01)
        for kw in ({'invalid':True},{'repeated':True}):
            self.assertEqual(receipt(flags=FLAGS,**kw),(0,0))
    def test_dynamic_texts_exist(self):
        script=(ROOT/'common/scripted_localisation/GPS_scripted_localisation.txt').read_text(encoding='utf-8-sig')
        loc=(ROOT/'localisation/simp_chinese/TOD_GPS_l_simp_chinese.yml').read_text(encoding='utf-8-sig')
        for flag in FLAGS:
            self.assertIn('GPS_gov_'+flag+'_recorded',script)
        refs=set(re.findall(r'localization_key\s*=\s*(GPS_gov_\w+)',script))
        keys=set(re.findall(r'^\s*(GPS_gov_\w+):',loc,re.M))
        self.assertEqual(refs-keys,set())

if __name__ == '__main__': unittest.main()
