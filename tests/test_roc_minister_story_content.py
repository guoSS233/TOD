"""Content and localization contracts for the ministerial milestone stories."""

from pathlib import Path
import re
import unittest

from test_roc_allied_parties import one, read_script


ROOT = Path(__file__).resolve().parents[1]
LOCALIZATION = ROOT / 'localisation/simp_chinese/TOD_ROC_l_simp_chinese.yml'
SLUGS = ('yu', 'yan', 'ruan', 'chen', 'xiao')
STAGES = ('1', 'step2', '2', 'step4', '3', 'step6')
EVENTS = tuple(group * 100 + stage for group in range(1, 6) for stage in range(1, 7))
LOC_LINE = re.compile(r'^\s*([\w.\-]+):0\s+"(.*)"\s*$')


def read_localization():
    if not LOCALIZATION.exists():
        return {}, []
    values = {}
    duplicates = []
    for line in LOCALIZATION.read_text(encoding='utf-8-sig').splitlines():
        match = LOC_LINE.match(line)
        if not match:
            continue
        key, value = match.groups()
        if key in values:
            duplicates.append(key)
        values[key] = value
    return values, duplicates


def walk_blocks(entries):
    yield entries
    for _, value in entries:
        if isinstance(value, list):
            yield from walk_blocks(value)


def parse_tooltip(text):
    """Read the player-facing amounts without consulting the draft manifest."""
    plain = re.sub(r'§[A-Za-z!]', '', text)
    cost_section = plain.split('成本：', 1)[1].split('；派系反应：', 1)[0]
    reaction_section = plain.split('派系反应：', 1)[1].split('；', 1)[0].split('。', 1)[0]
    sides = {'左': 'left', '中': 'center', '右': 'right'}

    def amounts(section):
        return {sides[side]: int(number.replace('−', '-'))
                for side, number in re.findall(r'大同党([左中右])派好感([+−]\d+)', section)}

    def number(pattern):
        match = re.search(pattern, plain)
        return int(match.group(1).replace('−', '-')) if match else 0

    return {
        'pp': -number(r'政治点([+−]\d+)'),
        'cost_favor': {key: -value for key, value in amounts(cost_section).items()},
        'favors': amounts(reaction_section),
        'performance': number(r'履职实绩([+−]\d+)'),
        'pressure': number(r'问责压力([+−]\d+)'),
        'advance_days': number(r'施政提前(\d+)日'),
        'delay_days': number(r'施政延后(\d+)日'),
    }


def parse_script_amounts(option):
    """Read resource gates and executed deltas independently from the event script."""
    trigger = one(option, 'trigger')
    costs = {}
    pp_cost = 0
    for key, value in trigger:
        if key == 'NOT':
            for nested_key, nested_value in value:
                if nested_key == 'has_political_power':
                    if nested_value.operator != '<':
                        raise AssertionError('unexpected political power cost comparison')
                    pp_cost = int(nested_value.value)
        elif key == 'check_variable':
            fields = dict(value)
            match = re.fullmatch(r'ROC_ma_(left|center|right)_favor', fields.get('var', ''))
            if match:
                if fields.get('compare') != 'greater_than_or_equals':
                    raise AssertionError('unexpected faction cost comparison')
                costs[match.group(1)] = int(fields['value'])

    conditional = one(one(option, 'hidden_effect'), 'if')
    changes = {'left': 0, 'center': 0, 'right': 0, 'performance': 0, 'pressure': 0}
    actual_pp = 0
    advance = delay = 0
    allowed = {'limit', 'ROC_ma_story_clear', 'ROC_ce_refresh', 'add_political_power',
               'add_to_variable', 'subtract_from_variable', 'set_variable',
               'ROC_ma_advance_days', 'ROC_ma_delay_days'}
    variables = {'ROC_ma_left_favor': 'left', 'ROC_ma_center_favor': 'center',
                 'ROC_ma_right_favor': 'right', 'ROC_ce_actual': 'performance',
                 'ROC_ce_pressure': 'pressure'}
    for key, value in conditional:
        if key not in allowed:
            raise AssertionError(f'unexpected story effect {key}')
        if key == 'add_political_power':
            actual_pp += int(value)
        elif key in ('add_to_variable', 'subtract_from_variable'):
            fields = dict(value)
            if fields['var'] not in variables:
                raise AssertionError(f'unexpected story variable {fields["var"]}')
            sign = 1 if key == 'add_to_variable' else -1
            changes[variables[fields['var']]] += sign * int(fields['value'])
        elif key == 'set_variable':
            fields = dict(value)
            if 'ROC_ma_day_credit' in fields:
                advance = int(fields['ROC_ma_day_credit'])
            elif 'ROC_ma_day_delay' in fields:
                delay = int(fields['ROC_ma_day_delay'])
            else:
                raise AssertionError(f'unexpected story variable assignment {fields}')
    if actual_pp != -pp_cost:
        raise AssertionError(f'political-power gate {pp_cost} does not match spend {actual_pp}')
    if bool(advance) != (('ROC_ma_advance_days', 'yes') in conditional):
        raise AssertionError('advance amount and effect disagree')
    if bool(delay) != (('ROC_ma_delay_days', 'yes') in conditional):
        raise AssertionError('delay amount and effect disagree')
    reactions = {side: changes[side] + costs.get(side, 0) for side in ('left', 'center', 'right')}
    return {
        'pp': pp_cost,
        'cost_favor': costs,
        'favors': {side: amount for side, amount in reactions.items() if amount},
        'performance': changes['performance'],
        'pressure': changes['pressure'],
        'advance_days': advance,
        'delay_days': delay,
    }


class MinisterStoryContent(unittest.TestCase):
    def test_localization_has_exactly_one_utf8_bom(self):
        self.assertTrue(LOCALIZATION.exists(), 'story localization has not been created')
        if LOCALIZATION.exists():
            raw = LOCALIZATION.read_bytes()
            self.assertTrue(raw.startswith(b'\xef\xbb\xbf'))
            self.assertEqual(raw.count(b'\xef\xbb\xbf'), 1)
            self.assertTrue(raw.decode('utf-8-sig').startswith('l_simp_chinese:'))

    def test_all_and_only_expected_story_keys_are_present(self):
        loc, duplicates = read_localization()
        self.assertEqual([key for key in duplicates if key.startswith("ROC_ma_story")], [])
        loc = {key: value for key, value in loc.items() if key.startswith("ROC_ma_story")}
        expected = {'ROC_ma_story_completion_tt', 'ROC_ma_story_archive', 'ROC_ma_story_archive_tt'}
        for event_id in EVENTS:
            base = f'ROC_ma_story.{event_id}'
            expected.update(f'{base}.{suffix}' for suffix in ('t', 'd', 'a', 'b', 'c', 'a_tt', 'b_tt', 'c_tt'))
        self.assertEqual(set(loc), expected)
        self.assertTrue(all(loc.values()), 'empty story translation')

    def test_thirty_stories_have_dialogue_and_sufficient_distinct_content(self):
        loc, _ = read_localization()
        for event_id in EVENTS:
            with self.subTest(event=event_id):
                base = f'ROC_ma_story.{event_id}'
                if f'{base}.d' not in loc:
                    self.fail('story description is missing')
                title = loc[f'{base}.t']
                body = loc[f'{base}.d'].replace('\\n', '\n')
                self.assertLessEqual(len(title), 14)
                self.assertTrue(520 <= len(body) <= 680, f'{len(body)} characters')
                self.assertGreaterEqual(len(body.split('\n\n')), 4)
                self.assertGreaterEqual(body.count('“'), 2)
                self.assertTrue('中央' in body or '大同党' in body)
                choices = [loc[f'{base}.{suffix}'] for suffix in ('a', 'b', 'c')]
                self.assertEqual(len(set(choices)), 3)
                self.assertTrue(all(0 < len(choice) <= 22 for choice in choices))

    def test_each_focus_queues_its_own_unique_story(self):
        script = read_script('common/scripted_effects/ROC_scripted_effects.txt')
        found = []
        for block in walk_blocks(script):
            focus = [value for key, value in block if key == 'complete_national_focus']
            events = [one(value, 'id') for key, value in block
                      if key == 'country_event' and one(value, 'id').startswith('ROC_ma_story.')]
            if focus and events:
                self.assertEqual(len(focus), 1)
                self.assertEqual(len(events), 1)
                found.append((focus[0], events[0]))
        expected = {(f'ROC_ma_{slug}_{suffix}', f'ROC_ma_story.{group * 100 + stage}')
                    for group, slug in enumerate(SLUGS, 1)
                    for stage, suffix in enumerate(STAGES, 1)}
        self.assertEqual(len(found), 30)
        self.assertEqual(set(found), expected)

    def test_tooltips_distinguish_costs_and_faction_reactions(self):
        loc, _ = read_localization()
        for event_id in EVENTS:
            for suffix in ('a', 'b', 'c'):
                with self.subTest(event=event_id, choice=suffix):
                    tooltip = loc.get(f'ROC_ma_story.{event_id}.{suffix}_tt', '')
                    self.assertIn('成本：', tooltip)
                    self.assertIn('派系反应：', tooltip)
                    self.assertEqual(tooltip.count('§!'), len(re.findall(r'§[YGRg]', tooltip)))

    def test_every_tooltip_matches_the_actual_option_cost_and_effects(self):
        loc, _ = read_localization()
        path = ROOT / 'events/ROC_ma_story.txt'
        self.assertTrue(path.exists(), 'story events have not been created')
        if not path.exists():
            return
        event_blocks = [value for key, value in read_script('events/ROC_ma_story.txt')
                        if key == 'country_event']
        self.assertEqual(len(event_blocks), 30)
        by_id = {one(block, 'id'): block for block in event_blocks}
        self.assertEqual(set(by_id), {f'ROC_ma_story.{event_id}' for event_id in EVENTS})
        for event_id in EVENTS:
            event = by_id[f'ROC_ma_story.{event_id}']
            self.assertEqual(one(event, 'title'), f'ROC_ma_story.{event_id}.t')
            self.assertEqual(one(event, 'desc'), f'ROC_ma_story.{event_id}.d')
            options = {one(value, 'name'): value for key, value in event if key == 'option'}
            self.assertEqual(set(options), {f'ROC_ma_story.{event_id}.{key}' for key in ('a', 'b', 'c')}
                             | {'ROC_ma_story_archive'})
            self.assertEqual(one(options['ROC_ma_story_archive'], 'custom_effect_tooltip'),
                             'ROC_ma_story_archive_tt')
            for suffix in ('a', 'b', 'c'):
                with self.subTest(event=event_id, choice=suffix):
                    name = f'ROC_ma_story.{event_id}.{suffix}'
                    option = options[name]
                    self.assertEqual(one(option, 'custom_effect_tooltip'), name + '_tt')
                    effects = parse_script_amounts(option)
                    self.assertEqual(parse_tooltip(loc[name + '_tt']), effects)
                    self.assertIn(effects['pp'], (0, 10, 15, 20))
                    self.assertLessEqual(len(effects['cost_favor']), 1)
                    self.assertTrue(all(v in (5, 10) for v in effects['cost_favor'].values()))
                    self.assertLessEqual(len(effects['favors']), 2)
                    self.assertTrue(all(-8 <= v <= 8 for v in effects['favors'].values()))
                    self.assertTrue(-5 <= effects['performance'] <= 5)
                    self.assertTrue(-6 <= effects['pressure'] <= 6)
                    self.assertIn(effects['advance_days'], (0, 7, 14, 21))
                    self.assertIn(effects['delay_days'], (0, 7, 14, 21))
                    self.assertFalse(effects['advance_days'] and effects['delay_days'])
                    paid = effects['pp'] or bool(effects['cost_favor'])
                    if suffix == 'a':
                        self.assertFalse(paid, 'the default must remain free')
                    else:
                        self.assertTrue(paid, 'a priced alternative needs a resource gate')
                    dimensions = (bool(effects['pp']) + len(effects['cost_favor'])
                                  + len(effects['favors']) + bool(effects['performance'])
                                  + bool(effects['pressure']) + bool(effects['advance_days'])
                                  + bool(effects['delay_days']))
                    self.assertTrue(1 <= dimensions <= 4)
                    benefit = (any(v > 0 for v in effects['favors'].values())
                               or effects['performance'] > 0 or effects['pressure'] < 0
                               or effects['advance_days'] > 0)
                    drawback = (paid or any(v < 0 for v in effects['favors'].values())
                                or effects['performance'] < 0 or effects['pressure'] > 0
                                or effects['delay_days'] > 0)
                    self.assertFalse(benefit and not drawback, 'benefit lacks a tradeoff')


if __name__ == '__main__':
    unittest.main()
