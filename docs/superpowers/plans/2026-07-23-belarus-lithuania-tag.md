# Belarus-Lithuania Federation Tag Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the existing `BLR` tag into a blank Belarus-Lithuania Federation, assign only the states identified by the mod localisation, and restore the mod's event replacement path.

**Architecture:** Keep the existing `BLT` Baltic Governorate unchanged and reuse the existing `BLR` tag already referenced by state 241. Give `BLR` a minimal country history with no OOB or characters, and transfer only the eight localisation-confirmed states at the start date. Split the malformed descriptor comment so both `events` and `history/countries` are active replacement paths.

**Tech Stack:** Hearts of Iron IV text data files, YAML localisation, Python `unittest` static regression check.

## Global Constraints

- Preserve existing user changes and unrelated content.
- Use `###` to retain replaced historical lines; do not delete them.
- Do not copy vanilla files wholesale.
- Keep `BLT` as the existing Baltic Governorate.
- `events` must be an active `replace_path` in `descriptor.mod`.

---

### Task 1: Add regression checks

**Files:**
- Create: `.qa/test_lbf_setup.py`

- [ ] **Step 1: Write the failing test**

The test checks the existing tag registry entry, blank history, localisation, colour, eight selected state owners, exclusion of localisation state 205, and active descriptor paths.

- [ ] **Step 2: Run the check and confirm it fails because the `BLR` country history and localisation are not yet defined**

Run: `python .qa/test_lbf_setup.py`

Expected: failure identifying the missing `BLR` setup.

---

### Task 2: Add the BLR country definition

**Files:**
- Verify: `common/country_tags/00_countries.txt`
- Verify: `common/countries/Belarus.txt`
- Create: `history/countries/BLR - Belarus-Lithuania Federation.txt`
- Create: `localisation/simp_chinese/TOD_BLR_l_simp_chinese.yml`
- Create: `localisation/english/TOD_BLR_l_english.yml`

- [ ] **Step 1: Reuse the existing `BLR` country-tag and colour entries**
- [ ] **Step 2: Create minimal blank country history with Minsk (state 206) as capital and `oob = "empty"`**
- [ ] **Step 3: Add Simplified Chinese and English country-name keys**
- [ ] **Step 4: Run `python .qa/test_lbf_setup.py` and confirm the country-definition checks pass**

---

### Task 3: Assign localisation-confirmed starting states

**Files:**
- Modify: `history/states/11-Kaunas.txt`
- Modify: `history/states/188-Memel.txt`
- Modify: `history/states/189-Kaunas.txt`
- Modify: `history/states/194-Pinsk Marches.txt`
- Modify: `history/states/204-Brest.txt`
- Modify: `history/states/206-Minsk.txt`
- Modify: `history/states/207-Viciebsk.txt`
- Modify: `history/states/241-Pochep.txt`

- [ ] **Step 1: Preserve each original owner line with `###` and set the start-date owner to `BLR`**
- [ ] **Step 2: Add `add_core_of = BLR` without removing existing cores**
- [ ] **Step 3: Leave state 205 owned by `RUS` because localisation identifies it as Kaluga**
- [ ] **Step 4: Run the static check and verify all eight selected state IDs resolve to `BLR`**

---

### Task 4: Restore events replacement loading

**Files:**
- Modify: `descriptor.mod`

- [ ] **Step 1: Replace the combined `###` line with active `replace_path="events"` and active `replace_path="history/countries"` lines**
- [ ] **Step 2: Run the static check and inspect `git diff --check`**

---

### Task 5: Final verification

**Files:**
- Verify: all files above and `error.log`

- [ ] **Step 1: Run `python .qa/test_lbf_setup.py`**
- [ ] **Step 2: Run `git diff --check`**
- [ ] **Step 3: Run `analyze_errors_by_folder.py` against the latest log if the game has produced a new log**
- [ ] **Step 4: Report changed files, state selection, event loading status, and any remaining game-runtime errors without claiming a full game run unless the normal launcher was actually used**
