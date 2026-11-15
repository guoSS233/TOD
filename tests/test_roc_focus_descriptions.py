"""Check ROC focus descriptions against the requested 203-character display budget."""

from pathlib import Path
import re
import unittest

from test_roc_great_practice import MAIN_FOCUS, POSTWAR_FOCUS, focus_blocks, scalar

ROOT = Path(__file__).resolve().parents[1]
LOCALIZATION_DIR = ROOT / "localisation/simp_chinese"
NEW_FOCI = tuple(
    f"ROC_ma_{minister}_{stage}"
    for minister in ("yu", "yan", "ruan", "chen", "xiao")
    for stage in ("1", "step2", "2", "step4", "3")
)
LOC_LINE = re.compile(r'^\s*([^\s:#]+):\s*(?:\d+)?\s+"(.*)"\s*$')


def focus_ids():
    return [scalar(block, "id") for path in (MAIN_FOCUS, POSTWAR_FOCUS)
            for block in focus_blocks(path)]


def localization_values():
    values = {}
    for path in LOCALIZATION_DIR.glob("*.yml"):
        for line in path.read_text(encoding="utf-8-sig").splitlines():
            if match := LOC_LINE.match(line):
                values.setdefault(match.group(1), []).append(match.group(2))
    return values


class RocFocusDescriptionLocalization(unittest.TestCase):
    def test_every_roc_focus_has_one_description_of_at_most_203_characters(self):
        ids = focus_ids()
        values = localization_values()
        self.assertTrue(ids, "ROC focus trees should contain focus IDs")
        self.assertEqual(len(ids), len(set(ids)), "ROC focus IDs must be unique")
        for focus_id in ids + list(NEW_FOCI):
            with self.subTest(focus_id=focus_id):
                descs = values.get(f"{focus_id}_desc", [])
                self.assertEqual(1, len(descs), "description must exist exactly once")
                self.assertLessEqual(len(descs[0]), 203, "description exceeds 203 characters")


if __name__ == "__main__":
    unittest.main()
