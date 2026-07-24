from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]


def read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def state_owner(state_id: int) -> str:
    for path in (ROOT / "history" / "states").glob("*.txt"):
        content = path.read_text(encoding="utf-8")
        if re.search(rf"\bid\s*=\s*{state_id}\b", content):
            match = re.search(r"^\s*owner\s*=\s*(\w+)", content, re.MULTILINE)
            return match.group(1) if match else ""
    return ""


class BlrSetupTest(unittest.TestCase):
    def test_blr_tag_has_minimal_country_definition(self):
        tags = read("common/country_tags/00_countries.txt")
        self.assertEqual(1, len(re.findall(r"^BLR\s*=", tags, re.MULTILINE)))
        self.assertIn('BLR = "countries/Belarus.txt"', tags)

        history = read("history/countries/BLR - Belarus-Lithuania Federation.txt")
        self.assertIsNotNone(re.search(r"^capital\s*=\s*206\s*$", history, re.MULTILINE))
        self.assertIn('oob = "BLR_1936"', history)
        self.assertNotIn("recruit_character", history)

    def test_blr_localisation_and_colour_exist(self):
        localisation = read("localisation/simp_chinese/TOD_BLR_l_simp_chinese.yml")
        self.assertIn('BLR:0 "白俄罗斯-立陶宛联邦"', localisation)
        self.assertIn('BLR_DEF:0 "白俄罗斯-立陶宛联邦"', localisation)
        self.assertIn('BLR_ADJ:0 "白俄罗斯-立陶宛"', localisation)
        self.assertTrue(
            (ROOT / "localisation" / "simp_chinese" / "TOD_BLR_l_simp_chinese.yml")
            .read_bytes()
            .startswith(b"\xef\xbb\xbf")
        )
        self.assertTrue(
            (ROOT / "localisation" / "english" / "TOD_BLR_l_english.yml")
            .read_bytes()
            .startswith(b"\xef\xbb\xbf")
        )
        self.assertRegex(read("common/countries/Belarus.txt"), r"(?m)^color\s*=")

    def test_localisation_confirmed_states_are_owned_by_blr(self):
        selected = {11, 188, 189, 194, 204, 206, 207, 241}
        for state_id in selected:
            self.assertEqual("BLR", state_owner(state_id), state_id)
        self.assertEqual("RUS", state_owner(205))

    def test_blr_claimed_states_keep_only_polish_claim(self):
        state_files = {
            784: "history/states/784-Ermland-Masuren.txt",
            96: "history/states/96-Wilejka.txt",
            95: "history/states/95-Nowogrodek.txt",
        }
        for state_id, relative_path in state_files.items():
            content = read(relative_path)
            self.assertRegex(content, r"(?m)^\s*owner\s*=\s*BLR\s*$", state_id)
            self.assertEqual(
                ["POL"],
                re.findall(r"^\s*add_core_of\s*=\s*(\w+)", content, re.MULTILINE),
                state_id,
            )

    def test_descriptor_loads_events_and_country_history(self):
        descriptor = read("descriptor.mod")
        active_lines = [
            line.strip()
            for line in descriptor.splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        ]
        self.assertIn('replace_path="events"', active_lines)
        self.assertIn('replace_path="history/countries"', active_lines)


if __name__ == "__main__":
    unittest.main()
