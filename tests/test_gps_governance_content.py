import re
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
FOCUS = ROOT / 'common/national_focus/GPS.txt'
TREE = ROOT / 'common/national_focus/GPS.txt'
LOC = ROOT / 'localisation/simp_chinese/TOD_GPS_l_simp_chinese.yml'
class GovernanceContent(unittest.TestCase):
    def test_batch_one_focuses_and_tree_entry(self):
        self.assertTrue(FOCUS.exists())
        s = FOCUS.read_text(encoding='utf-8-sig')
        for name in ('tang_orders','tang_appointments','tang_register','tang_settlement','committee_table','recovery_desk','repair_roster','workers_record'):
            self.assertIn('id = GPS_gov_' + name, s)
        tree = TREE.read_text(encoding='utf-8-sig')
        for name in ('tang_orders','committee_table','recovery_desk'):
            self.assertIn('shared_focus = GPS_gov_' + name, tree)
    def test_core_narrative_is_localized(self):
        self.assertTrue(LOC.exists())
        s = LOC.read_text(encoding='utf-8-sig')
        for n in (1,2,3,4,5,6,7,8,9,10,20):
            for suffix in ('t','d','a','invalid'):
                self.assertIn(f'GPS_governance.{n}.{suffix}:', s)
    def test_focused_content_is_complete_and_valid_localization(self):
        data = LOC.read_bytes()
        self.assertTrue(data.startswith(b"\xef\xbb\xbf"))
        text = data.decode('utf-8-sig').replace('\r\n', '\n')
        lines = text.splitlines()
        self.assertEqual(lines[0], 'l_simp_chinese:')
        governance_lines = [line for line in lines[1:] if re.match(r'^\s*GPS_(?:gov_|governance\.)', line)]
        for line in governance_lines:
            self.assertRegex(line, r'^ [A-Za-z0-9_.]+:0 "[^"\r\n]*"$')
        entries = dict(re.findall(r'^ ([A-Za-z0-9_.]+):0 "([^"\r\n]*)"$', '\n'.join(governance_lines), re.M))
        self.assertEqual(len(entries), len(governance_lines), 'duplicate or malformed governance keys')
        for n in (1, 3, 5, 7, 9, 10, 20):
            self.assertGreaterEqual(len(entries[f'GPS_governance.{n}.d'].replace(r'\n', '')), 350)
            self.assertLessEqual(len(entries[f'GPS_governance.{n}.d'].replace(r'\n', '')), 650)
        for n in (2, 4, 6, 8):
            for suffix in ('a', 'b', 'c', 'invalid'):
                self.assertIn(f'GPS_governance.{n}.d_{suffix}', entries)
        for name in ('tang_orders','tang_appointments','tang_register','tang_settlement','committee_table','recovery_desk','repair_roster','workers_record'):
            self.assertLessEqual(len(entries['GPS_gov_'+name+'_desc']), 203)
    def test_runtime_public_text_keys_are_translated(self):
        text = LOC.read_text(encoding='utf-8-sig')
        entries = set(re.findall(r'^ ([A-Za-z0-9_.]+):0 ', text, re.M))
        scripts = '\n'.join((ROOT / p).read_text(encoding='utf-8-sig') for p in ('events/GPS.txt', 'common/decisions/GPS.txt', 'common/national_focus/GPS.txt'))
        references = set(re.findall(r'(?:title|desc|text|name)\s*=\s*(GPS_governance\.[\w.]+)', scripts))
        references |= set(re.findall(r'has_country_flag\s*=\s*(GPS_gov_\w+)', scripts))
        references |= set(re.findall(r'custom_effect_tooltip\s*=\s*(GPS_gov_\w+)', scripts))
        self.assertEqual(references - entries, set())
    def test_focus_layout_and_visible_unlock(self):
        text = FOCUS.read_text(encoding='utf-8-sig')
        blocks = re.split(r'(?=shared_focus = \{)', text)
        expected = {'tang_orders': (3, 10), 'tang_appointments': (3, 11), 'tang_register': (3, 12), 'tang_settlement': (3, 13), 'committee_table': (11, 10), 'recovery_desk': (17, 10), 'repair_roster': (17, 11), 'workers_record': (17, 12)}
        for name, xy in expected.items():
            block = next(b for b in blocks if 'id = GPS_gov_'+name+'\n' in b)
            self.assertEqual(tuple(map(int, re.search(r'\bx = (\d+)\s+y = (\d+)', block).groups())), xy)
            self.assertNotIn('completion_reward = {  }', block)
        self.assertIn('custom_effect_tooltip = GPS_gov_recovery_desk_tt', text)
    def test_overview_and_transport_text_exist(self):
        text = LOC.read_text(encoding='utf-8-sig')
        script = (ROOT / 'common/scripted_localisation/GPS_scripted_localisation.txt').read_text(encoding='utf-8-sig')
        for key in ('GetGPSGovMilitary', 'GetGPSGovEconomic', 'GetGPSGovSignature', 'GetGPSGovOrdersPromise', 'GetGPSGovCoalPromise', 'GetGPSGovRestartPromise'):
            self.assertIn(key, script)
            self.assertIn('['+key+']', text)
        for key in ('GPS_governance.3.d_rail','GPS_governance.3.d_road','GPS_governance.12.t','GPS_gov_followup_valid_tt','GPS_gov_followup_invalid_tt'):
            self.assertIn(key+':', text)
    def test_links_move_down_and_coordinates_avoid_reserved_cells(self):
        text = FOCUS.read_text(encoding='utf-8-sig')
        blocks = re.split(r'(?=shared_focus = \{)', text)
        coords = {}
        for b in blocks:
            ident = re.search(r'id = (GPS_gov_\w+)', b)
            if ident:
                coords[ident.group(1)] = tuple(map(int, re.search(r'\bx = (\d+)\s+y = (\d+)', b).groups()))
        self.assertEqual(len(coords), len(set(coords.values())))
        for pre, child in [('tang_orders','tang_appointments'),('tang_appointments','tang_register'),('tang_register','tang_settlement'),('recovery_desk','repair_roster'),('repair_roster','workers_record')]:
            self.assertLess(coords['GPS_gov_'+pre][1], coords['GPS_gov_'+child][1])
        self.assertGreater(coords['GPS_gov_tang_orders'][1], 7)
        self.assertGreater(coords['GPS_gov_committee_table'][1], 5)
        self.assertNotIn((20,10), set(coords.values()))
    def test_committee_batch_two_content_and_layout(self):
        focus = FOCUS.read_text(encoding='utf-8-sig')
        loc = LOC.read_text(encoding='utf-8-sig')
        entries = dict(re.findall(r'^ ([A-Za-z0-9_.]+):0 "([^"\r\n]*)"$', loc, re.M))
        blocks = re.split(r'(?=shared_focus = \{)', focus)
        expected = {'joint_pay':(9,11), 'defence_roster':(13,11), 'joint_appointments':(11,11), 'old_uniforms':(9,12), 'execution_receipts':(13,12), 'committee_settlement':(11,13)}
        coords = {}
        for b in blocks:
            match = re.search(r'id = (GPS_gov_\w+)', b)
            if match:
                coords[match.group(1)] = tuple(map(int, re.search(r'\bx = (\d+)\s+y = (\d+)', b).groups()))
                for parent in re.findall(r'focus = (GPS_gov_\w+)', b):
                    if parent != match.group(1):
                        pass
        self.assertEqual(len(coords), len(set(coords.values())))
        for name, xy in expected.items():
            self.assertEqual(coords['GPS_gov_'+name], xy)
            self.assertLessEqual(len(entries['GPS_gov_'+name+'_desc']), 203)
        for b in blocks:
            match = re.search(r'id = (GPS_gov_\w+)', b)
            if match:
                for parent in re.findall(r'(?<!shared_)focus = (GPS_gov_\w+)', b):
                    if parent in coords:
                        self.assertLess(coords[parent][1], coords[match.group(1)][1])
        for n in range(21,30):
            for suffix in ('t','d','a','invalid'):
                self.assertIn(f'GPS_governance.{n}.{suffix}', entries)
        for n in (21,23,25,27,28,29):
            self.assertGreaterEqual(len(entries[f'GPS_governance.{n}.d'].replace(r'\n', '')), 350)
            self.assertLessEqual(len(entries[f'GPS_governance.{n}.d'].replace(r'\n', '')), 650)
        for n in (22,24,26):
            for suffix in ('a','b','c','invalid'):
                self.assertIn(f'GPS_governance.{n}.d_{suffix}', entries)

    def test_batch_two_event_ids_and_all_scripted_text_references(self):
        events = (ROOT / 'events/GPS.txt').read_text(encoding='utf-8-sig')
        ids = re.findall(r'\bid\s*=\s*(GPS_governance\.\d+)', events)
        # Count definitions only, not queued event references.
        definitions = re.findall(r'country_event\s*=\s*\{\s*id\s*=\s*(GPS_governance\.\d+)\s+title\s*=', events)
        self.assertEqual(len(definitions), len(set(definitions)))
        for n in range(21, 30):
            self.assertIn(f'GPS_governance.{n}', definitions)
        entries = set(re.findall(r'^ ([A-Za-z0-9_.]+):0 ', LOC.read_text(encoding='utf-8-sig'), re.M))
        scripted = (ROOT / 'common/scripted_localisation/GPS_scripted_localisation.txt').read_text(encoding='utf-8-sig')
        refs = set(re.findall(r'localization_key\s*=\s*(GPS_gov_\w+)', scripted))
        self.assertEqual(refs - entries, set())
        for n in (22, 24, 26):
            for suffix in ('a', 'b', 'c', 'invalid'):
                self.assertIn(f'GPS_governance.{n}.d_{suffix}', events)

    def test_committee_receipt_tooltips_disclose_branch_effects_and_cost_priority(self):
        entries = dict(re.findall(r'^ ([A-Za-z0-9_.]+):0 "([^"\r\n]*)"$', LOC.read_text(encoding='utf-8-sig'), re.M))
        for key, parts in {
            'GPS_gov_option_joint_appointment_receipt_tt': ('5政治点', '3指挥点', '2政治点', '稳定度 -0.5%'),
            'GPS_gov_option_joint_pay_receipt_tt': ('2政治点', '3指挥点', '4指挥点', '稳定度 -0.5%'),
            'GPS_gov_option_defence_roster_receipt_tt': ('3陆军经验', '战争支持度 +0.5%', '稳定度 -0.5%'),
            'GPS_gov_option_execution_receipts_a_tt': ('5政治点', '10政治点', '20政治点', '已签承诺未能兑现'),
        }.items():
            for part in parts:
                self.assertIn(part, entries[key])
        self.assertNotIn('任何议题曾失效', entries['GPS_gov_option_execution_receipts_a_tt'])

    def test_batch_three_focus_graph_and_all_descriptions(self):
        focus = FOCUS.read_text(encoding='utf-8-sig')
        entries = dict(re.findall(r'^ ([A-Za-z0-9_.]+):0 "([^"\r\n]*)"$', LOC.read_text(encoding='utf-8-sig'), re.M))
        blocks = re.split(r'(?=shared_focus = \{)', focus)
        nodes = {}
        for b in blocks:
            m = re.search(r'id = (GPS_gov_\w+)', b)
            if m:
                nodes[m.group(1)] = b
        self.assertEqual(len(nodes), 20)
        coords = {k: tuple(map(int, re.search(r'\bx = (\d+)\s+y = (\d+)', v).groups())) for k, v in nodes.items()}
        self.assertEqual(len(set(coords.values())), 20)
        for name, xy in {'rural_supply':(17,13),'national_position':(7,15),'national_army':(5,16),'national_accounts':(7,16),'local_delegation':(9,16),'homeward_station':(7,17)}.items():
            self.assertEqual(coords['GPS_gov_'+name], xy)
        for ident, b in nodes.items():
            self.assertLessEqual(len(entries[ident+'_desc']), 203)
            for parent in re.findall(r'(?<!shared_)focus = (GPS_gov_\w+)', b):
                if parent in coords:
                    self.assertLess(coords[parent][1], coords[ident][1])
        tree = TREE.read_text(encoding='utf-8-sig')
        reached = set(re.findall(r'shared_focus = (GPS_gov_\w+)', tree))
        changed = True
        while changed:
            before = len(reached)
            for ident, b in nodes.items():
                parents = set(re.findall(r'(?<!shared_)focus = (GPS_gov_\w+)', b))
                if parents & reached:
                    reached.add(ident)
            changed = len(reached) != before
        self.assertEqual(set(nodes) - reached, set())
        for n in (40,41,44,45,47,48,49,50,51):
            length = len(entries[f'GPS_governance.{n}.d'].replace(r'\n', ''))
            self.assertTrue(250 <= length <= 420, (n, length))
            self.assertIn(f'GPS_governance.{n}.defer', entries)

    def test_narratives_have_distinct_scenes_and_correct_policy_routes(self):
        text = LOC.read_text(encoding='utf-8-sig')
        entries = dict(re.findall(r'^ ([A-Za-z0-9_.]+):0 "([^"\r\n]*)"$', text, re.M))
        stories = [entries[f'GPS_governance.{n}.d'] for n in (40,41,44,45,47,48,49,50,51)]
        self.assertTrue(all('书记员在纸页末尾留出了' not in story for story in stories))
        self.assertTrue(all('唐玉麟' not in story for story in stories))
        self.assertIn('汤玉麟', text)
        self.assertIn('边境', entries['GPS_governance.54.d'])
        for n in (55,56):
            self.assertIn('港口', entries[f'GPS_governance.{n}.d'])
            self.assertNotIn('朝鲜可由陆路', entries[f'GPS_governance.{n}.d'])

    def test_reviewed_stories_avoid_mechanics_and_repeated_tails(self):
        text = LOC.read_text(encoding='utf-8-sig')
        entries = dict(re.findall(r'^ ([A-Za-z0-9_.]+):0 "([^"\r\n]*)"$', text, re.M))
        domestic = (40, 41, 44, 45, 47, 48, 49, 50, 51)
        foreign = (54, 55, 56)
        forbidden = ('尚未接入', '统一条件', '自有自控', '原目标', '其他国家将领', '触发条件', '政治点', '稳定度', '委员会路线', '汤的路线')
        for n in domestic + foreign:
            value = entries[f'GPS_governance.{n}.d']
            length = len(value.replace(r'\n', ''))
            low, high = (250, 420) if n in domestic else (150, 250)
            self.assertTrue(low <= length <= high, (n, length))
            for word in forbidden:
                self.assertNotIn(word, value, (n, word))
        tails = [entries[f'GPS_governance.{n}.d'][-70:] for n in domestic]
        self.assertEqual(len(tails), len(set(tails)))
        foreign_texts = [entries[f'GPS_governance.{n}.d'] for n in foreign]
        for left in range(3):
            for right in range(left + 1, 3):
                self.assertFalse(any(foreign_texts[left][i:i+30] in foreign_texts[right] for i in range(len(foreign_texts[left])-29)))

    def test_batch_three_branch_descriptions_are_referenced_and_localized(self):
        events = (ROOT / 'events/GPS.txt').read_text(encoding='utf-8-sig')
        entries = dict(re.findall(r'^ ([A-Za-z0-9_.]+):0 "([^"\r\n]*)"$', LOC.read_text(encoding='utf-8-sig'), re.M))
        for n in (42,46,52):
            for suffix in ('a','b','c','invalid'):
                key = f'GPS_governance.{n}.d_{suffix}'
                self.assertIn('text = '+key, events)
                self.assertIn(key, entries)
            self.assertEqual(len({entries[f'GPS_governance.{n}.d_{x}'] for x in ('a','b','c','invalid')}), 4)
        scripts = events + (ROOT / 'common/decisions/GPS.txt').read_text(encoding='utf-8-sig') + FOCUS.read_text(encoding='utf-8-sig') + (ROOT / 'common/scripted_localisation/GPS_scripted_localisation.txt').read_text(encoding='utf-8-sig')
        refs = set(re.findall(r'(?:title|desc|text|name|localization_key|custom_effect_tooltip|tooltip)\s*=\s*(GPS_(?:governance\.[\w.]+|gov_\w+))', scripts))
        self.assertEqual(refs - entries.keys(), set())
        for tag in ('STG','MNG','XBJ','KOR','EZO','WJP'):
            self.assertIn('[GetGPSGovArchiveLine'+tag+']', entries['GPS_gov_category_desc'])
            self.assertIn('[GetGPSGovArchive'+tag+']', entries['GPS_gov_archive_line_'+tag])
        for tag in ('STG','MNG','XBJ'):
            self.assertIn('内部立场', entries['GPS_gov_open_contact_'+tag+'_desc'])
            self.assertNotIn('尚未接入', entries['GPS_gov_open_contact_'+tag+'_desc'])

    def test_batch_three_policy_descriptions_and_costs(self):
        entries = dict(re.findall(r'^ ([A-Za-z0-9_.]+):0 "([^"\r\n]*)"$', LOC.read_text(encoding='utf-8-sig'), re.M))
        for key, parts in {
            'regional_closure_b': ('15政治点','90日','组织度恢复+3%','稳定度系数−1%'),
            'demobilization_b': ('15政治点','基建建造速度+4%','返还3政治点','撤销'),
            'demobilization_c': ('战争支持度−1%','稳定度+1%'),
            'national_army_a': ('组织度+3%','每日政治点−0.03','撤销'),
            'national_army_c': ('180日','训练时间−4%'),
            'national_accounts_b': ('补给消耗−3%','每日政治点−0.02'),
            'local_delegation_c': ('基建建造速度+4%','稳定度系数−1%'),
            'grain_a': ('补给消耗−3%','稳定度系数−2%','撤销'),
            'grain_b': ('补给消耗+2%','稳定度系数+2%'),
            'grain_c': ('每日政治点−0.02','指挥点+3'),
        }.items():
            for part in parts:
                self.assertIn(part, entries['GPS_gov_option_'+key+'_tt'])
        for tag in ('KOR','EZO','WJP'):
            self.assertIn('免费', entries['GPS_gov_option_policy_'+tag+'_c_tt'])
            self.assertIn('无额外收益', entries['GPS_gov_option_policy_'+tag+'_c_tt'])
        ideas = (ROOT / 'common/ideas/GPS_idea.txt').read_text(encoding='utf-8-sig')
        for key in re.findall(r'^\s*(GPS_gov_(?:national_army|national_accounts|local_delegation|regional_closure|demobilization|grain)_\w+_policy)\s*=\s*\{', ideas, re.M):
            self.assertIn(key, entries)
            self.assertIn(key+'_desc', entries)
        for n in (57,58):
            for suffix in ('t','d','a'):
                self.assertIn(f'GPS_governance.{n}.{suffix}', entries)

if __name__ == '__main__': unittest.main()


class GovernanceGrainTextRegression(unittest.TestCase):
    def test_grain_text_matches_wartime_target_conditions(self):
        from test_roc_allied_parties import ROOT
        text=(ROOT/'localisation/simp_chinese/TOD_GPS_l_simp_chinese.yml').read_text(encoding='utf-8-sig')
        keys=['GPS_governance.52.d_a','GPS_governance.52.d_b','GPS_governance.52.d_c','GPS_gov_option_grain_a_tt','GPS_gov_option_grain_b_tt','GPS_gov_option_grain_c_tt','GPS_gov_open_grain_desc','GPS_gov_grain_effort_desc','GPS_gov_overview_grain_failed']
        for key in keys:
            line=next(line for line in text.splitlines() if line.strip().startswith(key+':'))
            self.assertNotIn('和平',line,key)
        self.assertIn('战时',next(line for line in text.splitlines() if line.strip().startswith('GPS_gov_open_grain_desc:')))
