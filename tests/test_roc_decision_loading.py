"""Loading contracts for ROC decision files and their category declarations."""
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DECISIONS_DIR = ROOT / "common/decisions"
CATEGORIES_DIR = DECISIONS_DIR / "categories"


def roc_decision_files():
    return sorted(DECISIONS_DIR.glob("ROC*.txt"))


def roc_category_files():
    return sorted(CATEGORIES_DIR.glob("ROC*.txt"))


def top_level_block_names(path):
    """Return top-level Clausewitz block names from a decision script."""
    text = path.read_bytes().decode("utf-8")
    # Keep BOM detection as a separate byte-level contract below.
    if text.startswith("\ufeff"):
        text = text[1:]

    names = set()
    depth = 0
    for raw_line in text.splitlines():
        line = raw_line.split("#", 1)[0]
        if depth == 0:
            match = re.match(r"^\s*([A-Za-z0-9_]+)\s*=\s*\{", line)
            if match:
                names.add(match.group(1))
        depth += line.count("{") - line.count("}")
    return names


class RocDecisionLoadingTests(unittest.TestCase):
    def test_roc_decisions_and_categories_have_no_utf8_bom(self):
        files = roc_decision_files() + roc_category_files()
        self.assertTrue(files, "ROC decision files should be present")
        for path in files:
            with self.subTest(path=path.relative_to(ROOT)):
                self.assertFalse(
                    path.read_bytes().startswith(b"\xef\xbb\xbf"),
                    f"{path.relative_to(ROOT)} starts with a UTF-8 BOM",
                )

    def test_every_roc_decision_category_reference_is_declared(self):
        decisions = roc_decision_files()
        categories = roc_category_files()
        declared = set().union(*(top_level_block_names(path) for path in categories))
        referenced = set().union(*(top_level_block_names(path) for path in decisions))

        self.assertTrue(decisions, "ROC decision files should be present")
        self.assertTrue(categories, "ROC decision category files should be present")
        self.assertEqual(
            set(), referenced - declared,
            "ROC decision files reference undeclared categories",
        )


if __name__ == "__main__":
    unittest.main()
